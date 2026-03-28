"""Selective GitHub push for individual tools."""

import asyncio
import json
import logging
import os

from config import GITHUB_REPO_URL, TOOLS_DIR

log = logging.getLogger("claude-monitor")

# Track which tools have been shared
SHARED_TOOLS_FILE = os.path.join(os.path.dirname(__file__), "shared_tools.json")


def _load_shared() -> dict[str, str]:
    """Load shared tools registry: {tool_name: github_url}."""
    if os.path.exists(SHARED_TOOLS_FILE):
        try:
            with open(SHARED_TOOLS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_shared(data: dict[str, str]) -> None:
    with open(SHARED_TOOLS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def _run_git(*args: str) -> tuple[int, str]:
    """Run a git command in the tools directory."""
    proc = await asyncio.create_subprocess_exec(
        "git", *args,
        cwd=TOOLS_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = (stdout or b"").decode("utf-8", errors="replace")
    if proc.returncode != 0:
        err = (stderr or b"").decode("utf-8", errors="replace")
        output = f"{output}\n{err}".strip()
    return proc.returncode, output


def get_tool_github_url(tool_name: str) -> str | None:
    """Get GitHub URL for a tool if already shared."""
    shared = _load_shared()
    return shared.get(tool_name)


def is_tool_shared(tool_name: str) -> bool:
    """Check if a tool is already on GitHub."""
    return tool_name in _load_shared()


async def push_tool(tool_name: str) -> tuple[bool, str]:
    """Push a specific tool to GitHub.

    Returns:
        (success, message) — message is the GitHub URL on success,
        or an error description on failure.
    """
    tool_dir = os.path.join(TOOLS_DIR, tool_name)
    if not os.path.isdir(tool_dir):
        return False, f"ツール '{tool_name}' が見つかりません"

    # Already shared? Return existing URL
    shared = _load_shared()
    if tool_name in shared:
        return True, shared[tool_name]

    if not GITHUB_REPO_URL:
        return False, "GITHUB_REPO_URL が設定されていません"

    log.info(f"Pushing tool to GitHub: {tool_name}")

    # Stage the tool directory (force-add despite .gitignore)
    rc, out = await _run_git("add", "-f", f"{tool_name}/")
    if rc != 0:
        log.error(f"git add failed: {out}")
        return False, f"git add 失敗: {out}"

    # Commit
    rc, out = await _run_git("commit", "-m", f"Share: {tool_name}")
    if rc != 0:
        # Nothing to commit means already tracked — still OK
        if "nothing to commit" in out:
            log.info(f"Tool already committed: {tool_name}")
        else:
            log.error(f"git commit failed: {out}")
            return False, f"git commit 失敗: {out}"

    # Push
    rc, out = await _run_git("push", "origin", "master")
    if rc != 0:
        log.error(f"git push failed: {out}")
        return False, f"git push 失敗: {out}"

    # Build URL
    # Remove trailing .git if present
    base_url = GITHUB_REPO_URL.rstrip("/")
    if base_url.endswith(".git"):
        base_url = base_url[:-4]
    github_url = f"{base_url}/tree/master/{tool_name}"

    # Record as shared
    shared[tool_name] = github_url
    _save_shared(shared)

    log.info(f"Tool shared: {tool_name} -> {github_url}")
    return True, github_url
