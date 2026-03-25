"""Scan tools/ directory and detect new/updated tools for daily digest."""

import os
from datetime import datetime, timezone, timedelta

from config import TOOLS_DIR

JST = timezone(timedelta(hours=9))

# Directories to skip
SKIP_DIRS = {"__pycache__", "node_modules", ".next", ".git", "未分類", "system"}


TOOL_DESCRIPTIONS = {
    "3link": "株式会社スリーンクの案件・依頼者・クライアントを一元管理。Google Sheets + GAS WebAppでブラウザから操作できる業務システム",
    "asin-scraper": "Amazon ASINから付属品情報を自動調査してスプレッドシートに追記。EC物販の商品リサーチを効率化",
    "auto-classify": "テキストやデータをAIで自動分類。手作業の仕分け作業を自動化",
    "claude-monitor": "Claude Codeの操作をDiscordにリアルタイム通知＆スマホから承認・指示できるモニタリングBot",
    "flowsync-lp": "FlowSync（業務自動化サービス）のランディングページ",
    "gmail-sender": "PythonからGmail APIで自動メール送信。テンプレートメールの一括送信などに使用",
    "sheets": "Google Sheets APIとGAS（Apps Script）をCLIから操作。シート読み書き・GASコードの取得更新",
    "transcribe-tool": "音声・動画ファイルのURLからテキストを自動文字起こし",
}


def _get_tool_description(tool_dir: str) -> str:
    """Get tool description from manual registry, fallback to README."""
    name = os.path.basename(tool_dir)

    # Use manual description if available
    if name in TOOL_DESCRIPTIONS:
        return TOOL_DESCRIPTIONS[name]

    # Fallback: README title
    readme = os.path.join(tool_dir, "README.md")
    if os.path.isfile(readme):
        with open(readme, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("# ") and not stripped.startswith("##"):
                    return stripped.lstrip("# ").strip()[:120]

    return "説明なし"


def _latest_mtime(tool_dir: str) -> datetime:
    """Get the most recent modification time of files in a tool directory."""
    latest = 0.0
    for root, dirs, files in os.walk(tool_dir):
        # Skip irrelevant directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".tsx", ".bat", ".md", ".json", ".html", ".css")):
                fpath = os.path.join(root, f)
                try:
                    mt = os.path.getmtime(fpath)
                    if mt > latest:
                        latest = mt
                except OSError:
                    pass
    return datetime.fromtimestamp(latest, tz=JST) if latest else datetime.min.replace(tzinfo=JST)


def _creation_date(tool_dir: str) -> datetime:
    """Get the earliest file creation/modification time in a tool directory."""
    earliest = float("inf")
    for root, dirs, files in os.walk(tool_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fpath = os.path.join(root, f)
            try:
                ct = os.path.getctime(fpath)
                if ct < earliest:
                    earliest = ct
            except OSError:
                pass
    return datetime.fromtimestamp(earliest, tz=JST) if earliest != float("inf") else datetime.min.replace(tzinfo=JST)


def scan_tools(since: datetime | None = None) -> list[dict]:
    """Scan tools directory and return info about each tool.

    Args:
        since: If provided, only return tools modified since this time.
               If None, return all tools.

    Returns:
        List of dicts with keys: name, description, status ("新規"/"更新"), last_modified
    """
    if since is None:
        # Default: last 24 hours
        since = datetime.now(JST) - timedelta(hours=24)

    results = []
    if not os.path.isdir(TOOLS_DIR):
        return results

    for entry in sorted(os.listdir(TOOLS_DIR)):
        tool_dir = os.path.join(TOOLS_DIR, entry)
        if not os.path.isdir(tool_dir) or entry in SKIP_DIRS or entry.startswith("."):
            continue

        last_modified = _latest_mtime(tool_dir)
        if last_modified <= since:
            continue

        created = _creation_date(tool_dir)
        # If the tool was created within the scan period, it's "新規"
        is_new = created >= since

        results.append({
            "name": entry,
            "description": _get_tool_description(tool_dir),
            "status": "新規" if is_new else "更新",
            "last_modified": last_modified,
        })

    return results


def get_all_tools() -> list[dict]:
    """Return info about all tools (for full listing)."""
    results = []
    if not os.path.isdir(TOOLS_DIR):
        return results

    for entry in sorted(os.listdir(TOOLS_DIR)):
        tool_dir = os.path.join(TOOLS_DIR, entry)
        if not os.path.isdir(tool_dir) or entry in SKIP_DIRS or entry.startswith("."):
            continue

        results.append({
            "name": entry,
            "description": _get_tool_description(tool_dir),
            "last_modified": _latest_mtime(tool_dir),
        })

    return results
