#!/usr/bin/env python
"""PreToolUse hook - sends tool call to Discord monitor, waits for approval."""

import json
import os
import sys

import requests

MONITOR_URL = "http://127.0.0.1:19876"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    try:
        resp = requests.post(
            f"{MONITOR_URL}/pre_tool",
            json={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "project_dir": project_dir,
            },
            timeout=130,
        )
        result = resp.json()
    except requests.ConnectionError:
        sys.exit(0)
    except requests.Timeout:
        sys.exit(0)
    except Exception:
        sys.exit(0)

    if result.get("approved", True):
        sys.exit(0)
    else:
        reason = result.get("reason", "Blocked by Discord monitor")
        print(reason, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
