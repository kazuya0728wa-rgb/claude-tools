"""Claude Code Discord Monitor - Main bot + HTTP server."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

import discord
from aiohttp import web
from discord import app_commands, ui
from discord.ext import tasks

from config import (
    AI_DIGEST_CHANNEL_ID,
    APPROVAL_TIMEOUT_SECONDS,
    DAILY_DIGEST_HOUR,
    DAILY_DIGEST_MINUTE,
    DISCORD_CHANNEL_ID,
    DISCORD_GUILD_ID,
    DISCORD_TOKEN,
    GITHUB_REPO_URL,
    HTTP_HOST,
    HTTP_PORT,
    LOG_FILE,
    READ_ONLY_TOOLS,
    TOOL_SHARE_CHANNEL_ID,
    USER_DISPLAY_NAME,
)
from formatter import (
    build_ai_detail_embed,
    build_ai_digest_embed,
    build_all_tools_embed,
    build_catalog_summary_embed,
    build_code_error_embed,
    build_code_shared_embed,
    build_daily_digest_embed,
    build_post_tool_embed,
    build_pre_tool_embed,
    build_stop_embed,
    build_tool_card_embed,
    build_waiting_embed,
)
from github_pusher import get_tool_github_url, is_tool_shared, push_tool
from tool_tracker import get_all_tools, get_shareable_tools, scan_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("claude-monitor")

JST = timezone(timedelta(hours=9))


# ---------------------------------------------------------------------------
# Approval Queue
# ---------------------------------------------------------------------------

class ApprovalQueue:
    """Manages pending approval requests and instruction buffer."""

    def __init__(self):
        self._pending: dict[str, asyncio.Future] = {}
        self._messages: dict[str, discord.Message] = {}
        self._instruction_buffer: list[str] = []
        self._lock = asyncio.Lock()

    async def create_request(self, request_id: str) -> asyncio.Future:
        future = asyncio.get_event_loop().create_future()
        async with self._lock:
            self._pending[request_id] = future
        return future

    async def set_message(self, request_id: str, message: discord.Message):
        async with self._lock:
            self._messages[request_id] = message

    async def resolve(self, request_id: str, approved: bool, reason: str = ""):
        async with self._lock:
            future = self._pending.pop(request_id, None)
            msg = self._messages.pop(request_id, None)
        if future and not future.done():
            future.set_result({"approved": approved, "reason": reason})
        if msg:
            try:
                embed = msg.embeds[0] if msg.embeds else None
                if embed:
                    if approved:
                        embed.color = 0x57F287
                        embed.set_footer(text=f"承認済み | {request_id[:8]}")
                    else:
                        embed.color = 0xED4245
                        embed.set_footer(text=f"拒否 | {request_id[:8]}")
                await msg.edit(embed=embed, view=None)
            except Exception:
                pass

    async def add_instruction(self, text: str):
        async with self._lock:
            self._instruction_buffer.append(text)

    async def pop_instruction(self) -> str | None:
        async with self._lock:
            if self._instruction_buffer:
                return self._instruction_buffer.pop(0)
            return None

    @property
    async def pending_count(self) -> int:
        async with self._lock:
            return len(self._pending)

    @property
    async def instruction_count(self) -> int:
        async with self._lock:
            return len(self._instruction_buffer)

    async def approve_all(self):
        async with self._lock:
            for rid, future in self._pending.items():
                if not future.done():
                    future.set_result({"approved": True, "reason": "一括承認"})
            self._pending.clear()


# ---------------------------------------------------------------------------
# Discord UI Components
# ---------------------------------------------------------------------------

class InstructionModal(ui.Modal, title="指示を送る"):
    """Modal for deny + instruct or standalone instruction."""

    instruction = ui.TextInput(
        label="Claude Code への指示",
        style=discord.TextStyle.paragraph,
        placeholder="例: そのファイルではなく config.py を編集して",
        max_length=500,
    )

    def __init__(self, queue: ApprovalQueue, request_id: str | None = None):
        super().__init__()
        self.request_id = request_id
        self.queue = queue

    async def on_submit(self, interaction: discord.Interaction):
        if self.request_id:
            reason = f"[スマホからの指示] {self.instruction.value}"
            await self.queue.resolve(self.request_id, False, reason)
        else:
            await self.queue.add_instruction(self.instruction.value)
        await interaction.response.send_message(
            f"\U0001f4dd 指示を送信しました: {self.instruction.value}", ephemeral=True
        )


class ApprovalView(ui.View):
    """Approve / Deny / Deny+Instruct buttons."""

    def __init__(self, request_id: str, queue: ApprovalQueue):
        super().__init__(timeout=APPROVAL_TIMEOUT_SECONDS)
        self.request_id = request_id
        self.queue = queue

    @ui.button(label="許可する", style=discord.ButtonStyle.green, emoji="\u2705")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        await self.queue.resolve(self.request_id, True)
        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            embed.color = 0x57F287
            embed.set_footer(text=f"承認済み | {self.request_id[:8]}")
        await interaction.response.edit_message(embed=embed, view=None)

    @ui.button(label="拒否する", style=discord.ButtonStyle.red, emoji="\u274c")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        await self.queue.resolve(self.request_id, False, "ユーザーが拒否しました")
        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            embed.color = 0xED4245
            embed.set_footer(text=f"拒否 | {self.request_id[:8]}")
        await interaction.response.edit_message(embed=embed, view=None)

    @ui.button(label="拒否 + 指示", style=discord.ButtonStyle.blurple, emoji="\U0001f4dd")
    async def deny_instruct(self, interaction: discord.Interaction, button: ui.Button):
        modal = InstructionModal(self.queue, request_id=self.request_id)
        await interaction.response.send_modal(modal)

    async def on_timeout(self):
        await self.queue.resolve(self.request_id, True, "タイムアウト自動承認")


class WaitingView(ui.View):
    """Button to send instruction when Claude Code is waiting."""

    def __init__(self, queue: ApprovalQueue):
        super().__init__(timeout=None)
        self.queue = queue

    @ui.button(label="指示を送る", style=discord.ButtonStyle.blurple, emoji="\U0001f4dd")
    async def send_instruction(self, interaction: discord.Interaction, button: ui.Button):
        modal = InstructionModal(self.queue)
        await interaction.response.send_modal(modal)


# ---------------------------------------------------------------------------
# AI Digest UI Components
# ---------------------------------------------------------------------------

class DigestCategoryButton(ui.Button):
    """Button for a single AI digest category — shows detail on click."""

    def __init__(self, category: dict):
        emoji = category.get("emoji", "\U0001f4e6")
        name = category.get("name", "")
        item_count = len(category.get("items", []))
        super().__init__(
            label=f"{name} ({item_count})",
            style=discord.ButtonStyle.secondary,
            emoji=emoji,
        )
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        embed = build_ai_detail_embed(self.category)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DigestDetailView(ui.View):
    """View with category buttons for AI digest — up to 5 buttons."""

    def __init__(self, categories: list[dict]):
        super().__init__(timeout=None)  # Persistent buttons
        for cat in categories[:5]:  # Discord allows max 5 buttons per row
            if cat.get("items"):
                self.add_item(DigestCategoryButton(cat))


# ---------------------------------------------------------------------------
# Tool Catalog UI Components
# ---------------------------------------------------------------------------

class ToolCardView(ui.View):
    """Persistent view with 'コードが欲しい' button for a single tool."""

    def __init__(self, tool_key: str):
        super().__init__(timeout=None)
        self.tool_key = tool_key
        # Set custom_id for persistence across bot restarts
        self.request_btn.custom_id = f"tool_request:{tool_key}"

    @ui.button(label="コードが欲しい", style=discord.ButtonStyle.green, emoji="\U0001f4e5")
    async def request_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if already shared
        existing_url = get_tool_github_url(self.tool_key)
        if existing_url:
            embed = build_code_shared_embed(self.tool_key, existing_url)
            embed.title = f"\U0001f4e4 {self.tool_key} は既にGitHubで公開中です"
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Push to GitHub
        success, result = await push_tool(self.tool_key)
        if success:
            embed = build_code_shared_embed(self.tool_key, result)
            # Also post publicly so others can see
            await interaction.followup.send(embed=embed)
        else:
            embed = build_code_error_embed(self.tool_key, result)
            await interaction.followup.send(embed=embed, ephemeral=True)


# ---------------------------------------------------------------------------
# Discord Bot
# ---------------------------------------------------------------------------

class MonitorBot(discord.Client):
    def __init__(self, queue: ApprovalQueue):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.queue = queue
        self.tree = app_commands.CommandTree(self)
        self.start_time = datetime.now(timezone.utc)
        self._channel: discord.TextChannel | None = None
        self._share_channel: discord.TextChannel | None = None

    async def setup_hook(self):
        self._register_commands()

        # Register persistent views for tool card buttons
        shareable = get_shareable_tools()
        for tool in shareable:
            self.add_view(ToolCardView(tool["key"]))

        if DISCORD_GUILD_ID:
            guild = discord.Object(id=DISCORD_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

        # Start daily digest scheduler
        if not self.daily_digest_loop.is_running():
            self.daily_digest_loop.start()

    def _register_commands(self):
        @self.tree.command(name="status", description="モニターの状態を表示")
        async def status_cmd(interaction: discord.Interaction):
            pending = await self.queue.pending_count
            instructions = await self.queue.instruction_count
            uptime = datetime.now(timezone.utc) - self.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)

            embed = discord.Embed(title="\U0001f4ca モニター状態", color=0x5865F2)
            embed.add_field(name="承認待ち", value=str(pending), inline=True)
            embed.add_field(name="指示キュー", value=str(instructions), inline=True)
            embed.add_field(
                name="稼働時間", value=f"{hours}時間{minutes}分{seconds}秒", inline=True
            )
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="approve_all", description="すべての承認待ちを一括許可")
        async def approve_all_cmd(interaction: discord.Interaction):
            await self.queue.approve_all()
            await interaction.response.send_message("\u2705 すべて承認しました")

        @self.tree.command(name="timeout", description="自動承認のタイムアウトを変更（秒）")
        @app_commands.describe(seconds="秒数")
        async def timeout_cmd(interaction: discord.Interaction, seconds: int):
            import config
            config.APPROVAL_TIMEOUT_SECONDS = seconds
            await interaction.response.send_message(
                f"\u23f1\ufe0f タイムアウトを{seconds}秒に変更しました"
            )

        @self.tree.command(name="tools", description="全ツール一覧を表示")
        async def tools_cmd(interaction: discord.Interaction):
            all_tools = get_all_tools()
            embed = build_all_tools_embed(USER_DISPLAY_NAME, all_tools)
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="digest", description="今日のツール活動レポートを手動送信")
        async def digest_cmd(interaction: discord.Interaction):
            tools = scan_tools()
            embed = build_daily_digest_embed(USER_DISPLAY_NAME, tools)
            await interaction.response.send_message(embed=embed)
            # Send individual tool cards with buttons
            for tool in tools:
                catalog = tool.get("catalog")
                if catalog:
                    card_data = dict(catalog)
                    card_data["key"] = tool["name"]
                    card_data["shared"] = is_tool_shared(tool["name"])
                    card_data["github_url"] = get_tool_github_url(tool["name"]) or ""
                    card_embed = build_tool_card_embed(card_data)
                    if catalog.get("shareable", False):
                        view = ToolCardView(tool["name"])
                        await interaction.channel.send(embed=card_embed, view=view)
                    else:
                        await interaction.channel.send(embed=card_embed)

        @self.tree.command(name="catalog", description="共有可能なツールカタログを表示")
        async def catalog_cmd(interaction: discord.Interaction):
            shareable = get_shareable_tools()
            if not shareable:
                await interaction.response.send_message("共有可能なツールがありません。")
                return

            summary = build_catalog_summary_embed(
                USER_DISPLAY_NAME, len(shareable), len(shareable)
            )
            await interaction.response.send_message(embed=summary)

            for tool in shareable:
                tool["shared"] = is_tool_shared(tool["key"])
                tool["github_url"] = get_tool_github_url(tool["key"]) or ""
                card_embed = build_tool_card_embed(tool)
                view = ToolCardView(tool["key"])
                await interaction.channel.send(embed=card_embed, view=view)

    @tasks.loop(minutes=1)
    async def daily_digest_loop(self):
        """Check every minute if it's time to send the daily digest."""
        now = datetime.now(JST)
        if now.hour == DAILY_DIGEST_HOUR and now.minute == DAILY_DIGEST_MINUTE:
            await self._send_daily_digest()

    @daily_digest_loop.before_loop
    async def before_daily_digest(self):
        await self.wait_until_ready()
        log.info(f"Daily digest scheduler started (JST {DAILY_DIGEST_HOUR:02d}:{DAILY_DIGEST_MINUTE:02d})")

    async def _send_daily_digest(self):
        """Send the daily tool digest to the share channel with card embeds."""
        channel = await self.get_share_channel_safe()
        if not channel:
            log.warning("Tool share channel not found, skipping digest")
            return

        tools = scan_tools()
        # Summary embed
        embed = build_daily_digest_embed(USER_DISPLAY_NAME, tools)
        await channel.send(embed=embed)

        # Individual tool cards with buttons
        for tool in tools:
            catalog = tool.get("catalog")
            if catalog:
                card_data = dict(catalog)
                card_data["key"] = tool["name"]
                card_data["shared"] = is_tool_shared(tool["name"])
                card_data["github_url"] = get_tool_github_url(tool["name"]) or ""
                card_embed = build_tool_card_embed(card_data)
                if catalog.get("shareable", False):
                    view = ToolCardView(tool["name"])
                    await channel.send(embed=card_embed, view=view)
                else:
                    await channel.send(embed=card_embed)

        log.info(f"Daily digest sent: {len(tools)} tools reported")

    async def on_ready(self):
        log.info(f"Bot ready: {self.user} (guild={DISCORD_GUILD_ID}, channel={DISCORD_CHANNEL_ID})")
        self._channel = self.get_channel(DISCORD_CHANNEL_ID)
        if self._channel:
            await self._channel.send(
                embed=discord.Embed(
                    title="\U0001f7e2 Claude Monitor 起動",
                    description="Claude Code の監視を開始しました。\nツール実行を通知し、変更系は承認を求めます。",
                    color=0x57F287,
                )
            )

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id != DISCORD_CHANNEL_ID:
            return

        if message.content.startswith("!instruct "):
            text = message.content[len("!instruct "):]
            await self.queue.add_instruction(text)
            await message.add_reaction("\U0001f4e8")
            log.info(f"Instruction queued: {text}")

    async def get_channel_safe(self) -> discord.TextChannel | None:
        if self._channel is None:
            self._channel = self.get_channel(DISCORD_CHANNEL_ID)
        return self._channel

    async def get_share_channel_safe(self) -> discord.TextChannel | None:
        if self._share_channel is None and TOOL_SHARE_CHANNEL_ID:
            self._share_channel = self.get_channel(TOOL_SHARE_CHANNEL_ID)
        return self._share_channel

    async def get_digest_channel_safe(self) -> discord.TextChannel | None:
        """Get channel for AI digest. Falls back to main channel."""
        if AI_DIGEST_CHANNEL_ID:
            ch = self.get_channel(AI_DIGEST_CHANNEL_ID)
            if ch:
                return ch
        return await self.get_channel_safe()


# ---------------------------------------------------------------------------
# HTTP Handler (receives requests from hook scripts)
# ---------------------------------------------------------------------------

class HookHandler:
    def __init__(self, bot: MonitorBot, queue: ApprovalQueue):
        self.bot = bot
        self.queue = queue

    async def handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "running"})

    async def handle_pre_tool(self, request: web.Request) -> web.Response:
        data = await request.json()
        tool_name = data.get("tool_name", "unknown")
        tool_input = data.get("tool_input", {})
        project_dir = data.get("project_dir", "")
        request_id = str(uuid.uuid4())

        log.info(f"PreToolUse: {tool_name} [{request_id[:8]}]")

        # Check for pending instructions
        instruction = await self.queue.pop_instruction()
        if instruction:
            log.info(f"Delivering instruction: {instruction}")
            return web.json_response({
                "approved": False,
                "reason": instruction,
            })

        # Auto-approve read-only tools
        if tool_name in READ_ONLY_TOOLS:
            return web.json_response({"approved": True, "reason": ""})

        # Send approval request to Discord
        channel = await self.bot.get_channel_safe()
        if not channel:
            log.warning("Channel not found, auto-approving")
            return web.json_response({"approved": True, "reason": ""})

        future = await self.queue.create_request(request_id)
        embed = build_pre_tool_embed(
            tool_name, tool_input, request_id, project_dir=project_dir
        )
        view = ApprovalView(request_id, self.queue)
        msg = await channel.send(embed=embed, view=view)
        await self.queue.set_message(request_id, msg)

        try:
            result = await asyncio.wait_for(future, timeout=APPROVAL_TIMEOUT_SECONDS)
            log.info(f"Resolved [{request_id[:8]}]: {result}")
            return web.json_response(result)
        except asyncio.TimeoutError:
            await self.queue.resolve(request_id, True, "タイムアウト自動承認")
            log.info(f"Timeout [{request_id[:8]}]: auto-approved")
            return web.json_response({"approved": True, "reason": ""})

    async def handle_post_tool(self, request: web.Request) -> web.Response:
        data = await request.json()
        tool_name = data.get("tool_name", "unknown")

        log.info(f"PostToolUse: {tool_name}")
        return web.json_response({"status": "ok"})

    async def handle_ai_digest(self, request: web.Request) -> web.Response:
        """Receive AI news digest and post to Discord with category buttons."""
        data = await request.json()
        categories = data.get("categories", [])
        log.info(f"AI Digest received: {len(categories)} categories")

        channel = await self.bot.get_digest_channel_safe()
        if not channel:
            log.warning("Digest channel not found")
            return web.json_response({"status": "error", "reason": "channel not found"})

        embed = build_ai_digest_embed(data)
        view = DigestDetailView(categories)
        await channel.send(embed=embed, view=view)

        log.info("AI Digest sent to Discord")
        return web.json_response({"status": "ok"})

    async def handle_stop(self, request: web.Request) -> web.Response:
        data = await request.json()
        project_dir = data.get("project_dir", "")
        last_message = data.get("last_assistant_message", "")

        log.info("Session stopped — waiting for next instruction")

        channel = await self.bot.get_channel_safe()
        if channel:
            embed = build_waiting_embed(project_dir, last_message)
            view = WaitingView(self.queue)
            asyncio.create_task(channel.send(embed=embed, view=view))

        return web.json_response({"status": "ok"})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    queue = ApprovalQueue()
    bot = MonitorBot(queue)
    handler = HookHandler(bot, queue)

    app = web.Application()
    app.router.add_get("/health", handler.handle_health)
    app.router.add_post("/pre_tool", handler.handle_pre_tool)
    app.router.add_post("/post_tool", handler.handle_post_tool)
    app.router.add_post("/stop", handler.handle_stop)
    app.router.add_post("/ai-digest", handler.handle_ai_digest)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HTTP_HOST, HTTP_PORT)
    await site.start()
    log.info(f"HTTP server listening on {HTTP_HOST}:{HTTP_PORT}")

    try:
        await bot.start(DISCORD_TOKEN)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
