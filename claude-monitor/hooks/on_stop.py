#!/usr/bin/env python
"""Stop hook - sends waiting notification to Discord and archives old plans."""

import json
import os
import sys
import shutil
import time

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

    # Plan自動アーカイブ: 7日以上前のプランファイルを移動
    try:
        plans_dir = os.path.join(os.path.expanduser("~"), ".claude", "plans")
        archive_dir = os.path.join(plans_dir, "archive")
        cutoff = time.time() - 7 * 86400  # 7日前
        if os.path.isdir(plans_dir):
            for f in os.listdir(plans_dir):
                fp = os.path.join(plans_dir, f)
                if f.endswith(".md") and os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
                    os.makedirs(archive_dir, exist_ok=True)
                    shutil.move(fp, os.path.join(archive_dir, f))
    except Exception:
        pass

    # Smart Claude: セッション学習・同期
    try:
        smart_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "..", "smart-claude")
        sys.path.insert(0, os.path.abspath(smart_dir))
        from smart_hook import handle_stop
        handle_stop(data)
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
