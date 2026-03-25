#!/usr/bin/env python
"""Stop hook - sends waiting notification to Discord."""

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

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    last_message = data.get("last_assistant_message", "")

    # Sanitize for safe transmission
    if isinstance(last_message, str):
        last_message = last_message.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        if len(last_message) > 1500:
            last_message = last_message[:1500] + "\n... (省略)"

    try:
        requests.post(
            f"{MONITOR_URL}/stop",
            json={
                "project_dir": project_dir,
                "last_assistant_message": last_message,
            },
            timeout=5,
        )
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
