"""
稼働管理表_3Link GAS push スクリプト

使い方:
  python kadou/push.py

kadou/ ディレクトリ内のコード.js・フォーム.html を
稼働管理表の GAS にpushします。
"""

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 共通モジュールのパスを通す
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth import build_service
from kadou.config import PROJECT_NAME, GAS_SCRIPT_ID

DIR = os.path.dirname(__file__)


def main():
    code_path = os.path.join(DIR, "コード.js")
    form_path = os.path.join(DIR, "フォーム.html")

    if not os.path.exists(code_path):
        print(f"[ERROR] {code_path} が見つかりません", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(form_path):
        print(f"[ERROR] {form_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    with open(code_path, "r", encoding="utf-8") as f:
        gas_code = f.read()
    with open(form_path, "r", encoding="utf-8") as f:
        form_html = f.read()

    content = {
        "files": [
            {
                "name": "appsscript",
                "type": "JSON",
                "source": json.dumps(
                    {
                        "timeZone": "Asia/Tokyo",
                        "dependencies": {},
                        "exceptionLogging": "STACKDRIVER",
                        "runtimeVersion": "V8",
                        "webapp": {
                            "executeAs": "USER_ACCESSING",
                            "access": "ANYONE",
                        },
                    }
                ),
            },
            {"name": "コード", "type": "SERVER_JS", "source": gas_code},
            {"name": "フォーム", "type": "HTML", "source": form_html},
        ]
    }

    print(f"[{PROJECT_NAME}] GASにpushします...")
    print(f"  Script ID: {GAS_SCRIPT_ID}")

    service = build_service("script", "v1")
    result = service.projects().updateContent(
        scriptId=GAS_SCRIPT_ID, body=content
    ).execute()

    print(f"[OK] push完了（ファイル数: {len(result.get('files', []))}）")
    for f in result.get("files", []):
        print(f"  - {f['name']} ({f['type']})")

    print()
    print("[注意] Webアプリに反映するには再デプロイが必要です:")
    print("  スプレッドシート → 拡張機能 → Apps Script → デプロイ → デプロイを管理 → 新バージョン")


if __name__ == "__main__":
    main()
