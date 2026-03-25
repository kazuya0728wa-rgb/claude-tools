"""
GASプロジェクト作成・コードデプロイスクリプト

実行すると:
  1. 新しいGASプロジェクトを作成（スプレッドシートにバインド）
  2. コード・HTMLをデプロイ
  3. スクリプトIDを config_3link.py に記録

使い方:
  python deploy_gas.py
"""

import sys
import os
import json

sys.path.insert(0, r"C:\Users\kazuy\.claude\tools\sheets")
from auth import build_service

try:
    from config_3link import SPREADSHEET_ID
except ImportError:
    print("[ERROR] config_3link.py が見つかりません。setup_spreadsheet.py を先に実行してください。")
    sys.exit(1)

GAS_DIR = os.path.join(os.path.dirname(__file__), "gas")


def read_file(filename):
    path = os.path.join(GAS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def create_gas_project():
    """GASプロジェクトを作成してスクリプトIDを返す"""
    service = build_service("script", "v1")

    body = {
        "title": "スリーンク統合管理ツール",
        "parentId": SPREADSHEET_ID,
    }
    result = service.projects().create(body=body).execute()
    script_id = result["scriptId"]
    print(f"[OK] GASプロジェクト作成: スクリプトID = {script_id}")
    return script_id


def push_gas_code(script_id):
    """GASコードをプッシュする"""
    service = build_service("script", "v1")

    files = [
        {
            "name": "appsscript",
            "type": "JSON",
            "source": read_file("appsscript.json"),
        },
        {
            "name": "コード",
            "type": "SERVER_JS",
            "source": read_file("コード.js"),
        },
        {
            "name": "index",
            "type": "HTML",
            "source": read_file("index.html"),
        },
    ]

    result = service.projects().updateContent(
        scriptId=script_id,
        body={"files": files},
    ).execute()

    print(f"[OK] GASコードプッシュ完了: {len(files)}ファイル")
    return result


def save_script_id(script_id):
    """config_3link.py にスクリプトIDを保存"""
    config_path = os.path.join(os.path.dirname(__file__), "config_3link.py")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(f'SPREADSHEET_ID = "{SPREADSHEET_ID}"\n')
        f.write(f'GAS_SCRIPT_ID = "{script_id}"\n')
    print(f"[OK] config_3link.py を更新しました: {config_path}")


def main():
    from config_3link import GAS_SCRIPT_ID
    print("=" * 50)
    print("GASコード 更新デプロイ")
    print(f"  スプレッドシートID: {SPREADSHEET_ID}")

    if GAS_SCRIPT_ID:
        # 既存プロジェクトを更新
        print(f"  スクリプトID: {GAS_SCRIPT_ID} (既存を更新)")
        print("=" * 50)
        script_id = GAS_SCRIPT_ID
        push_gas_code(script_id)
    else:
        # 新規作成
        print("  スクリプトID: 新規作成")
        print("=" * 50)
        script_id = create_gas_project()
        push_gas_code(script_id)
        save_script_id(script_id)

    print()
    print("=" * 50)
    print("[完了] GASプロジェクトの作成・デプロイが完了しました！")
    print()
    print("【重要】次の手順でWebAppをデプロイしてください:")
    print(f"  1. スプレッドシートを開く:")
    print(f"     https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print(f"  2. 「拡張機能」→「Apps Script」を開く")
    print(f"  3. 「デプロイ」→「新しいデプロイ」をクリック")
    print(f"  4. 種類：ウェブアプリ")
    print(f"     実行ユーザー：自分")
    print(f"     アクセス：全員")
    print(f"  5. 「デプロイ」をクリックしてURLを取得")
    print("=" * 50)


if __name__ == "__main__":
    main()
