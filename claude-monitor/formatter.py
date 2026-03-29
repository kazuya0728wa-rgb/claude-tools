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
    """Build summary embed for daily tool digest notification.

    Note: github_url parameter kept for backward compatibility but no longer
    displayed. Code is shared on-demand via tool card buttons instead.
    """
    if not tools:
        embed = discord.Embed(
            title=f"\U0001f6e0\ufe0f {user_name}のツール活動",
            description="昨日は新しいツールの作成・更新はありませんでした。",
            color=0x95A5A6,
            timestamp=datetime.now(timezone.utc),
        )
        return embed

    new_count = sum(1 for t in tools if t["status"] == "新規")
    update_count = sum(1 for t in tools if t["status"] == "更新")

    summary_parts = []
    if new_count:
        summary_parts.append(f"\U0001f195 新規 {new_count}件")
    if update_count:
        summary_parts.append(f"\U0001f504 更新 {update_count}件")
    summary_parts.append("📥 各ツールの「コードが欲しい」ボタンでGitHub共有できます")

    embed = discord.Embed(
        title=f"\U0001f6e0\ufe0f {user_name}のツール活動",
        description="\n".join(summary_parts),
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_footer(text=f"全{len(tools)}件")

    return embed


# ---------------------------------------------------------------------------
# AI Digest Embeds
# ---------------------------------------------------------------------------

IMPORTANCE_EMOJI = {"high": "\u2b50", "medium": "\u2796", "low": "\u25ab"}  # ⭐ ➖ ▫


def build_ai_digest_embed(data: dict) -> discord.Embed:
    """Build summary embed for AI news digest.

    Args:
        data: {digest_id, categories: [{name, emoji, items}], meta: {total_items, new_items, ...}}
    """
    meta = data.get("meta", {})
    total = meta.get("total_items", 0)
    new = meta.get("new_items", 0)
    next_run = meta.get("next_run", "")

    if total == 0:
        embed = discord.Embed(
            title="\U0001f916 AI\u6700\u65b0\u60c5\u5831\u30c0\u30a4\u30b8\u30a7\u30b9\u30c8",
            description="\u76f4\u8fd12\u65e5\u9593\u306e\u65b0\u3057\u3044AI\u30cb\u30e5\u30fc\u30b9\u306f\u3042\u308a\u307e\u305b\u3093\u3067\u3057\u305f\u3002",
            color=0x95A5A6,
            timestamp=datetime.now(timezone.utc),
        )
        if next_run:
            embed.set_footer(text=f"\u6b21\u56de\u53ce\u96c6: {next_run}")
        return embed

    digest_id = data.get("digest_id", "")
    embed = discord.Embed(
        title=f"\U0001f916 AI\u6700\u65b0\u60c5\u5831\u30c0\u30a4\u30b8\u30a7\u30b9\u30c8\uff08{digest_id}\uff09",
        description=f"\u76f4\u8fd12\u65e5\u9593\u306eAI\u95a2\u9023\u30cb\u30e5\u30fc\u30b9 \u5168{total}\u4ef6\uff08\u65b0\u898f{new}\u4ef6\uff09",
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )

    for cat in data.get("categories", []):
        items = cat.get("items", [])
        if not items:
            continue
        emoji = cat.get("emoji", "\U0001f4e6")
        name = cat.get("name", "")

        lines = []
        for item in items[:3]:  # サマリーは最大3件
            imp = IMPORTANCE_EMOJI.get(item.get("importance", "medium"), "\u2796")
            lines.append(f"{imp} {item.get('title', '')}")

        if len(items) > 3:
            lines.append(f"... \u4ed6{len(items) - 3}\u4ef6")

        embed.add_field(
            name=f"{emoji} {name}\uff08{len(items)}\u4ef6\uff09",
            value=truncate("\n".join(lines), MAX_EMBED_FIELD_LENGTH),
            inline=False,
        )

    if next_run:
        embed.set_footer(text=f"\u6b21\u56de\u53ce\u96c6: {next_run}")

    return embed


def build_ai_detail_embed(category: dict) -> discord.Embed:
    """Build detailed embed for a single AI digest category (shown on button click).

    Args:
        category: {name, emoji, items: [{title, summary, source, url, importance}]}
    """
    emoji = category.get("emoji", "\U0001f4e6")
    name = category.get("name", "")
    items = category.get("items", [])

    embed = discord.Embed(
        title=f"{emoji} {name} \u6700\u65b0\u60c5\u5831\uff08{len(items)}\u4ef6\uff09",
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )

    for item in items[:10]:  # Discord embed field上限25だが読みやすさのため10件まで
        imp = IMPORTANCE_EMOJI.get(item.get("importance", "medium"), "\u2796")
        title = item.get("title", "")
        summary = item.get("summary", "")
        source = item.get("source", "")
        url = item.get("url", "")

        value_parts = []
        if summary:
            value_parts.append(summary)
        if source:
            value_parts.append(f"\U0001f4f0 {source}")
        if url:
            value_parts.append(f"\U0001f517 [Link]({url})")

        embed.add_field(
            name=f"{imp} {title}",
            value=truncate("\n".join(value_parts) or "\u2014", MAX_EMBED_FIELD_LENGTH),
            inline=False,
        )

    if len(items) > 10:
        embed.set_footer(text=f"\u4ed6{len(items) - 10}\u4ef6\u306f\u7701\u7565")

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


# ---------------------------------------------------------------------------
# Tool Card Embeds (catalog-style sharing)
# ---------------------------------------------------------------------------

def build_tool_card_embed(tool: dict) -> discord.Embed:
    """Build a rich card embed for a single tool.

    Args:
        tool: dict with keys: name, summary, detail, features, tech,
              shareable, shared (optional), github_url (optional)
    """
    name = tool.get("name", tool.get("key", "不明"))
    summary = tool.get("summary", "")
    detail = tool.get("detail", "").strip()
    features = tool.get("features", [])
    tech = tool.get("tech", "")
    shared = tool.get("shared", False)
    github_url = tool.get("github_url", "")
    notify_reason = tool.get("notify_reason", "")

    # Title with badge
    badge = ""
    if notify_reason == "新規":
        badge = " \U0001f195"
    elif notify_reason == "機能追加":
        badge = " \U0001f199"
    title = f"\U0001f6e0\ufe0f {name}{badge}"

    # Description: summary + detail
    desc_parts = []
    if summary:
        desc_parts.append(f"**{summary}**")
    if detail:
        desc_parts.append(f"\n{detail}")
    description = "\n".join(desc_parts) if desc_parts else "説明なし"

    embed = discord.Embed(
        title=title,
        description=description,
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )

    # Features field
    if features:
        feat_text = "\n".join(f"\u2022 {f}" for f in features[:6])
        embed.add_field(name="\u2728 主要機能", value=feat_text, inline=False)

    # Tech stack field
    if tech:
        embed.add_field(name="\u2699\ufe0f 技術スタック", value=tech, inline=True)

    # Status field
    if shared and github_url:
        embed.add_field(
            name="\U0001f4e4 共有済み",
            value=f"[GitHub]({github_url})",
            inline=True,
        )

    return embed


def build_catalog_summary_embed(
    user_name: str,
    tool_count: int,
    shareable_count: int,
) -> discord.Embed:
    """Build a summary header embed for the tool catalog."""
    embed = discord.Embed(
        title=f"\U0001f4e6 {user_name}のツールカタログ",
        description=(
            f"全 **{tool_count}** 件のツール（共有可能: **{shareable_count}** 件）\n"
            "気になるツールがあれば「📥 コードが欲しい」ボタンを押してください！"
        ),
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )
    return embed


def build_code_shared_embed(tool_name: str, github_url: str) -> discord.Embed:
    """Build embed shown after code is pushed to GitHub."""
    embed = discord.Embed(
        title=f"\u2705 {tool_name} をGitHubに公開しました！",
        description=f"\U0001f517 **[リポジトリを開く]({github_url})**",
        color=0x57F287,
        timestamp=datetime.now(timezone.utc),
    )
    return embed


def build_code_error_embed(tool_name: str, error: str) -> discord.Embed:
    """Build embed shown when GitHub push fails."""
    embed = discord.Embed(
        title=f"\u274c {tool_name} の共有に失敗しました",
        description=truncate(error, MAX_EMBED_FIELD_LENGTH),
        color=0xED4245,
        timestamp=datetime.now(timezone.utc),
    )
    return embed
