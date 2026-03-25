"""Discord embed formatting for tool calls and results — Japanese UI."""

import json
import os
from datetime import datetime, timezone

import discord

from config import MAX_CODE_BLOCK_LENGTH, MAX_EMBED_FIELD_LENGTH


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 15] + "\n... (省略)"


def _safe_text(text: str) -> str:
    """Remove non-printable / surrogate characters that cause mojibake."""
    try:
        return text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    except Exception:
        return "(表示できないテキスト)"


def _ext_from_path(path: str) -> str:
    if "." in path:
        return path.rsplit(".", 1)[-1]
    return ""


def _project_name(project_dir: str) -> str:
    """Extract a readable project name from the full path."""
    if not project_dir:
        return "Claude Code"
    normalized = project_dir.replace("\\", "/").rstrip("/")
    basename = os.path.basename(normalized)
    if basename.startswith(".") or basename in ("src", "tools", "app"):
        parts = normalized.split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    return basename


def _describe_tool_ja(tool_name: str, tool_input: dict) -> str:
    """Return a plain Japanese description of what this tool call does."""
    if tool_name == "Bash":
        desc = tool_input.get("description", "")
        if desc:
            return f"PCで処理を実行: {desc}"
        return "PCで処理を実行しようとしています"

    if tool_name == "Edit":
        path = tool_input.get("file_path", "")
        fname = os.path.basename(path) if path else "不明"
        return f"**{fname}** を書き換えようとしています"

    if tool_name == "Write":
        path = tool_input.get("file_path", "")
        fname = os.path.basename(path) if path else "不明"
        return f"**{fname}** を作成しようとしています"

    if tool_name == "Read":
        path = tool_input.get("file_path", "")
        fname = os.path.basename(path) if path else "不明"
        return f"**{fname}** を読んでいます"

    if tool_name in ("Glob", "Grep"):
        pattern = tool_input.get("pattern", "")
        return f"`{pattern}` に一致するファイルを探しています"

    if tool_name == "Agent":
        desc = tool_input.get("description", "")
        if desc:
            return f"別の作業を並行で開始: {desc}"
        return "別の作業を並行で開始しようとしています"

    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        if len(parts) >= 3:
            service = parts[1].split("-")[0]
            action = parts[2].replace("_", " ")
            return f"{service} を操作: {action}"
    return f"{tool_name} を実行しようとしています"


def build_pre_tool_embed(
    tool_name: str,
    tool_input: dict,
    request_id: str,
    *,
    auto: bool = False,
    project_dir: str = "",
) -> discord.Embed:
    """Build embed for a PreToolUse notification."""
    project = _project_name(project_dir)
    description = _describe_tool_ja(tool_name, tool_input)

    if auto:
        color = 0x57F287
        title = f"\U0001f4d6 {project}"
    else:
        color = 0xFEE75C
        title = f"\u26a0\ufe0f {project} | 許可が必要です"

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Show file path for file operations (no raw commands)
    if tool_name in ("Write", "Edit"):
        path = tool_input.get("file_path", "")
        embed.add_field(name="対象ファイル", value=f"`{path}`", inline=False)

    if auto:
        embed.set_footer(text=f"自動承認 | {request_id[:8]}")
    else:
        embed.set_footer(text=f"承認待ち | {request_id[:8]}")

    return embed


def build_post_tool_embed(
    tool_name: str, tool_input: dict, output: str, project_dir: str = ""
) -> discord.Embed:
    """Build embed for a PostToolUse result."""
    project = _project_name(project_dir)
    description = _describe_tool_ja(tool_name, tool_input)

    embed = discord.Embed(
        title=f"\u2705 {project} | 完了",
        description=description,
        color=0x57F287,
        timestamp=datetime.now(timezone.utc),
    )

    return embed


def build_stop_embed() -> discord.Embed:
    """Build embed for session end notification."""
    embed = discord.Embed(
        title="\U0001f6d1 Claude Code 終了",
        description="セッションが完全に終了しました。",
        color=0xED4245,
        timestamp=datetime.now(timezone.utc),
    )
    return embed


def build_waiting_embed(project_dir: str = "", last_message: str = "") -> discord.Embed:
    """Build embed for when Claude Code is waiting for user input."""
    project = _project_name(project_dir)
    embed = discord.Embed(
        title=f"\U0001f4ac {project} | 次の指示を待っています",
        description="作業が完了しました。次の指示を入力できます。",
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )

    if last_message:
        safe_msg = _safe_text(last_message)
        # Remove code blocks and keep readable text
        cleaned = safe_msg.strip()
        if cleaned:
            embed.add_field(
                name="直前の返答",
                value=truncate(cleaned, MAX_EMBED_FIELD_LENGTH),
                inline=False,
            )

    return embed


def build_daily_digest_embed(
    user_name: str,
    tools: list[dict],
    github_url: str = "",
) -> discord.Embed:
    """Build embed for daily tool digest notification."""
    if not tools:
        embed = discord.Embed(
            title=f"\U0001f6e0\ufe0f {user_name}のツール活動",
            description="昨日は新しいツールの作成・更新はありませんでした。",
            color=0x95A5A6,
            timestamp=datetime.now(timezone.utc),
        )
        return embed

    lines = []
    new_count = sum(1 for t in tools if t["status"] == "新規")
    update_count = sum(1 for t in tools if t["status"] == "更新")

    for tool in tools:
        status_emoji = "\U0001f195" if tool["status"] == "新規" else "\U0001f504"
        lines.append(f"{status_emoji} **{tool['name']}**（{tool['status']}）")
        lines.append(f"　　→ {tool['description']}")

    embed = discord.Embed(
        title=f"\U0001f6e0\ufe0f {user_name}のツール活動",
        description="\n".join(lines),
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )

    summary_parts = []
    if new_count:
        summary_parts.append(f"新規 {new_count}件")
    if update_count:
        summary_parts.append(f"更新 {update_count}件")
    embed.set_footer(text=" | ".join(summary_parts))

    if github_url:
        embed.add_field(name="\U0001f517 GitHub", value=github_url, inline=False)

    return embed


def build_all_tools_embed(
    user_name: str,
    tools: list[dict],
    github_url: str = "",
) -> discord.Embed:
    """Build embed listing all tools."""
    if not tools:
        embed = discord.Embed(
            title=f"\U0001f4e6 {user_name}のツール一覧",
            description="ツールがまだありません。",
            color=0x95A5A6,
            timestamp=datetime.now(timezone.utc),
        )
        return embed

    lines = []
    for tool in tools:
        lines.append(f"\U0001f4e6 **{tool['name']}**")
        lines.append(f"　　→ {tool['description']}")

    embed = discord.Embed(
        title=f"\U0001f4e6 {user_name}のツール一覧（全{len(tools)}件）",
        description="\n".join(lines),
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )

    if github_url:
        embed.add_field(name="\U0001f517 GitHub", value=github_url, inline=False)

    return embed
