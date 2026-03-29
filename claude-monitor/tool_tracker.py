"""Scan tools/ directory and detect new/updated tools for daily digest."""

import hashlib
import json
import os
from datetime import datetime, timezone, timedelta

from config import TOOL_CATALOG_FILE, TOOLS_DIR

JST = timezone(timedelta(hours=9))

# Directories to skip
SKIP_DIRS = {"__pycache__", "node_modules", ".next", ".git", "未分類", "system"}

# health_config.yaml からツール説明を読み込み（単一正規ソース）
_YAML_DESCRIPTIONS: dict[str, str] | None = None

# tool_catalog.yaml からカタログ情報を読み込み
_CATALOG: dict[str, dict] | None = None


def _load_yaml_descriptions() -> dict[str, str]:
    """health_config.yaml の tools.*.description を読み込む"""
    global _YAML_DESCRIPTIONS
    if _YAML_DESCRIPTIONS is not None:
        return _YAML_DESCRIPTIONS

    _YAML_DESCRIPTIONS = {}
    yaml_path = os.path.join(TOOLS_DIR, "tool-health-monitor", "health_config.yaml")
    if not os.path.exists(yaml_path):
        return _YAML_DESCRIPTIONS

    try:
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        for tool_name, tool_config in config.get("tools", {}).items():
            desc = tool_config.get("description", "")
            if desc:
                _YAML_DESCRIPTIONS[tool_name] = desc
    except Exception:
        pass

    return _YAML_DESCRIPTIONS


def _load_catalog() -> dict[str, dict]:
    """Load tool_catalog.yaml for card-style sharing."""
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG

    _CATALOG = {}
    if not os.path.exists(TOOL_CATALOG_FILE):
        return _CATALOG

    try:
        import yaml
        with open(TOOL_CATALOG_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _CATALOG = data.get("tools", {})
    except Exception:
        pass

    return _CATALOG


def reload_catalog() -> None:
    """Force reload catalog from disk (used after edits)."""
    global _CATALOG
    _CATALOG = None
    _load_catalog()


def get_catalog_entry(tool_name: str) -> dict | None:
    """Get detailed catalog entry for a tool."""
    catalog = _load_catalog()
    return catalog.get(tool_name)


def get_shareable_tools() -> list[dict]:
    """Get all tools marked as shareable in the catalog."""
    catalog = _load_catalog()
    results = []
    for key, entry in catalog.items():
        if entry.get("shareable", False):
            tool = dict(entry)
            tool["key"] = key
            results.append(tool)
    return results


# ---------------------------------------------------------------------------
# Notification History — track what's been notified to avoid duplicates
# ---------------------------------------------------------------------------

NOTIFIED_FILE = os.path.join(os.path.dirname(__file__), "notified_tools.json")


def _catalog_hash(entry: dict) -> str:
    """Hash catalog entry's key fields to detect significant changes."""
    parts = [
        entry.get("summary", ""),
        entry.get("detail", ""),
        "|".join(entry.get("features", [])),
        entry.get("tech", ""),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def _load_notified() -> dict:
    if os.path.exists(NOTIFIED_FILE):
        try:
            with open(NOTIFIED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_notified(data: dict) -> None:
    with open(NOTIFIED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mark_notified(tool_name: str, catalog_entry: dict | None = None) -> None:
    """Record that a tool has been notified."""
    data = _load_notified()
    data[tool_name] = {
        "notified_at": datetime.now(JST).isoformat(),
        "catalog_hash": _catalog_hash(catalog_entry) if catalog_entry else "",
    }
    _save_notified(data)


def should_notify(tool_name: str) -> tuple[bool, str]:
    """Check if a tool should be notified.

    Returns:
        (should_notify, reason) — reason is "新規", "機能追加", or ""
    """
    catalog_entry = get_catalog_entry(tool_name)
    notified = _load_notified()

    if tool_name not in notified:
        return True, "新規"

    # Already notified — check if catalog content changed significantly
    if catalog_entry:
        old_hash = notified[tool_name].get("catalog_hash", "")
        new_hash = _catalog_hash(catalog_entry)
        if old_hash and new_hash != old_hash:
            return True, "機能追加"

    return False, ""


def _get_tool_description(tool_dir: str) -> str:
    """Get tool description from health_config.yaml, fallback to README."""
    name = os.path.basename(tool_dir)

    # health_config.yaml から取得
    descriptions = _load_yaml_descriptions()
    if name in descriptions:
        return descriptions[name]

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

        tool_info = {
            "name": entry,
            "description": _get_tool_description(tool_dir),
            "status": "新規" if is_new else "更新",
            "last_modified": last_modified,
        }
        # Merge catalog data if available
        catalog_entry = get_catalog_entry(entry)
        if catalog_entry:
            tool_info["catalog"] = catalog_entry
        results.append(tool_info)

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

        tool_info = {
            "name": entry,
            "description": _get_tool_description(tool_dir),
            "last_modified": _latest_mtime(tool_dir),
        }
        catalog_entry = get_catalog_entry(entry)
        if catalog_entry:
            tool_info["catalog"] = catalog_entry
        results.append(tool_info)

    return results
