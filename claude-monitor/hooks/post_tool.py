#!/usr/bin/env python
"""PostToolUse hook - sends result to Discord (fire-and-forget)."""

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
    output = data.get("output", "")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    if isinstance(output, str) and len(output) > 3000:
        output = output[:3000] + "\n... (truncated)"

    try:
        requests.post(
            f"{MONITOR_URL}/post_tool",
            json={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "output": output,
                "project_dir": project_dir,
            },
            timeout=5,
        )
    except Exception:
        pass

    # Smart Claude: インテリジェンス学習
    try:
        smart_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "..", "smart-claude")
        sys.path.insert(0, os.path.abspath(smart_dir))
        from smart_hook import handle_post_tool
        handle_post_tool(data)
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
