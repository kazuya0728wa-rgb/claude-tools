"""Scan tools/ directory and detect new/updated tools for daily digest."""

import os
from datetime import datetime, timezone, timedelta

from config import TOOLS_DIR

JST = timezone(timedelta(hours=9))

# Directories to skip
SKIP_DIRS = {"__pycache__", "node_modules", ".next", ".git", "未分類", "system"}


def _get_tool_description(tool_dir: str) -> str:
    """Extract tool description from README.md or main Python file."""
    readme = os.path.join(tool_dir, "README.md")
    if os.path.isfile(readme):
        with open(readme, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for line in lines:
            stripped = line.strip()
            # Skip title lines and empty lines
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                return stripped[:100]

    # Fallback: look for docstring in main .py file
    for fname in ("main.py", "bot.py", "app.py", "send.py", "classify.py"):
        fpath = os.path.join(tool_dir, fname)
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(500)
            if '"""' in content:
                start = content.index('"""') + 3
                end = content.index('"""', start) if '"""' in content[start:] else start + 80
                return content[start:end].strip().split("\n")[0][:100]

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
