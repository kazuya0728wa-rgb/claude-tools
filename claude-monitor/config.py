"""Claude Code Discord Monitor - Configuration"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))

# Discord settings (set via environment variables or start.bat)
DISCORD_TOKEN = os.environ.get("CLAUDE_MONITOR_DISCORD_TOKEN", "")
DISCORD_CHANNEL_ID = int(os.environ.get("CLAUDE_MONITOR_CHANNEL_ID", "0"))
DISCORD_GUILD_ID = int(os.environ.get("CLAUDE_MONITOR_GUILD_ID", "0"))

# Tool share channel (daily digest)
TOOL_SHARE_CHANNEL_ID = int(os.environ.get("TOOL_SHARE_CHANNEL_ID", "0"))

# AI Digest channel (defaults to main channel if not set)
AI_DIGEST_CHANNEL_ID = int(os.environ.get("AI_DIGEST_CHANNEL_ID", "0"))

# Daily digest schedule (JST)
DAILY_DIGEST_HOUR = 8  # 朝8時
DAILY_DIGEST_MINUTE = 0

# User display name for digest
USER_DISPLAY_NAME = os.environ.get("TOOL_SHARE_USER_NAME", "かずや")

# GitHub repo URL
GITHUB_REPO_URL = os.environ.get("TOOL_SHARE_GITHUB_URL", "")

# Internal HTTP API (hook scripts POST here)
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 19876

# Timeouts
APPROVAL_TIMEOUT_SECONDS = 120  # Auto-approve after this
HOOK_HTTP_TIMEOUT_SECONDS = 130  # Hook script timeout (slightly > approval)

# Tools that are auto-approved (log only, no Discord buttons)
READ_ONLY_TOOLS = frozenset({
    "Read", "Glob", "Grep", "WebSearch", "WebFetch",
    "Skill", "TodoWrite", "TodoRead",
    "Agent", "SendMessage",
    "ToolSearch",
})

# Maximum characters for Discord embed fields
MAX_EMBED_FIELD_LENGTH = 1024
MAX_CODE_BLOCK_LENGTH = 900  # Leave room for ```lang\n...\n``` wrapper

# Tool catalog (detailed descriptions for card-style sharing)
TOOL_CATALOG_FILE = os.path.join(BASE_DIR, "tool_catalog.yaml")

# Log file
LOG_FILE = os.path.join(BASE_DIR, "monitor.log")
