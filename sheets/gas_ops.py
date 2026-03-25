"""
Google Apps Script API CLI

使い方:
  python gas_ops.py get --script-id {SCRIPT_ID}
  python gas_ops.py update --script-id {SCRIPT_ID} --file "コード" --code "function onEdit(e)..."
  python gas_ops.py push --script-id {SCRIPT_ID} --json path/to/content.json

スクリプトIDの取得方法:
  1. スプレッドシートを開く
  2. 「拡張機能」→「Apps Script」
  3. URLから取得: https://script.google.com/home/projects/{SCRIPT_ID}/edit

注意:
  - Apps Script API はユーザー設定でも有効化が必要
    https://script.google.com/home/usersettings
  - updateContent は全ファイルを一括送信する必要があります（部分更新不可）
"""

import argparse
import io
import json
import os
import sys

# Windows での日本語文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from auth import build_service
from config import GAS_SCRIPT_ID


def get_service():
    return build_service("script", "v1")


def cmd_get(args):
    """GASプロジェクトの全ファイルのコードを取得"""
    service = get_service()
    result = service.projects().getContent(scriptId=args.script_id).execute()

    output = {
        "scriptId": args.script_id,
        "files": [
            {
                "name": f.get("name"),
                "type": f.get("type"),
                "source": f.get("source", ""),
            }
            for f in result.get("files", [])
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_update(args):
    """特定ファイルのコードを更新（他ファイルは保持）"""
    service = get_service()

    # 1. 現在の全コンテンツを取得
    current = service.projects().getContent(scriptId=args.script_id).execute()
    files = current.get("files", [])

    # 2. 対象ファイルを探して更新
    updated = False
    for f in files:
        if f.get("name") == args.file:
            f["source"] = args.code
            updated = True
            break

    if not updated:
        # ファイルが存在しない場合は新規追加
        files.append({
            "name": args.file,
            "type": "SERVER_JS",
            "source": args.code,
        })
        print(f"[INFO] 新規ファイル '{args.file}' を追加します", file=sys.stderr)

    # 3. 全コンテンツを一括送信（Apps Script APIは部分更新不可）
    result = service.projects().updateContent(
        scriptId=args.script_id,
        body={"files": files},
    ).execute()

    print(json.dumps({
        "scriptId": result.get("scriptId"),
        "updatedFile": args.file,
        "fileCount": len(files),
    }, ensure_ascii=False, indent=2))


def cmd_push(args):
    """JSONファイルから全コンテンツを一括プッシュ"""
    service = get_service()

    with open(args.json, "r", encoding="utf-8") as f:
        content = json.load(f)

    result = service.projects().updateContent(
        scriptId=args.script_id,
        body=content,
    ).execute()

    print(json.dumps({
        "scriptId": result.get("scriptId"),
        "fileCount": len(content.get("files", [])),
    }, ensure_ascii=False, indent=2))


def cmd_deploy(args):
    """新バージョンを作成してWebAppを再デプロイ"""
    service = get_service()

    # 1. 新しいバージョンを作成
    version_body = {"description": args.description or ""}
    version = service.projects().versions().create(
        scriptId=args.script_id,
        body=version_body,
    ).execute()
    version_number = version.get("versionNumber")
    print(f"[OK] バージョン {version_number} を作成しました", file=sys.stderr)

    # 2. 既存デプロイメントを取得
    deployments = service.projects().deployments().list(
        scriptId=args.script_id,
    ).execute()

    # WebApp デプロイメント（@HEAD以外、最新のもの）を探す
    webapp_deploy_id = None
    best_update_time = ""
    for d in deployments.get("deployments", []):
        config = d.get("deploymentConfig", {})
        # @HEAD デプロイメントはスキップ（versionNumber が無い）
        if not config.get("versionNumber"):
            continue
        entry_points = d.get("entryPoints", [])
        for ep in entry_points:
            if ep.get("entryPointType") == "WEB_APP":
                update_time = d.get("updateTime", "")
                if update_time > best_update_time:
                    best_update_time = update_time
                    webapp_deploy_id = d.get("deploymentId", "")
                break

    if webapp_deploy_id:
        # 3. 既存WebAppデプロイメントを新バージョンに更新
        update_body = {
            "deploymentConfig": {
                "scriptId": args.script_id,
                "versionNumber": version_number,
                "description": args.description or f"v{version_number}",
            }
        }
        result = service.projects().deployments().update(
            scriptId=args.script_id,
            deploymentId=webapp_deploy_id,
            body=update_body,
        ).execute()

        # WebApp URLを取得
        webapp_url = ""
        for ep in result.get("entryPoints", []):
            if ep.get("entryPointType") == "WEB_APP":
                webapp_url = ep.get("webApp", {}).get("url", "")
                break

        print(json.dumps({
            "scriptId": args.script_id,
            "deploymentId": webapp_deploy_id,
            "versionNumber": version_number,
            "action": "updated",
            "webAppUrl": webapp_url,
        }, ensure_ascii=False, indent=2))
    else:
        # WebAppデプロイメントが見つからない場合は表示のみ
        print(json.dumps({
            "scriptId": args.script_id,
            "versionNumber": version_number,
            "action": "version_created_only",
            "message": "WebAppデプロイメントが見つかりません。GASエディタから手動でデプロイしてください。",
        }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Google Apps Script API CLI")
    default_id = GAS_SCRIPT_ID or "(config.py の GAS_SCRIPT_ID に記入してください)"
    parser.add_argument(
        "--script-id",
        default=GAS_SCRIPT_ID if GAS_SCRIPT_ID else None,
        help=f"GASスクリプトID（デフォルト: {default_id}）",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    subparsers.add_parser("get", help="全GASファイルのコードを取得")

    # update
    p_update = subparsers.add_parser("update", help="特定ファイルのコードを更新")
    p_update.add_argument("--file", required=True, help='ファイル名（例: "コード"）')
    p_update.add_argument("--code", required=True, help="新しいコード（文字列）")

    # push
    p_push = subparsers.add_parser("push", help="JSONファイルから全コンテンツを一括プッシュ")
    p_push.add_argument("--json", required=True, help="コンテンツJSONファイルのパス")

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="新バージョンを作成してWebAppを再デプロイ")
    p_deploy.add_argument("--description", default="", help="バージョンの説明（任意）")

    args = parser.parse_args()

    if not args.script_id:
        print("[ERROR] --script-id が指定されていません。", file=sys.stderr)
        print("  config.py の GAS_SCRIPT_ID に記入するか、--script-id オプションで指定してください。", file=sys.stderr)
        print("  スクリプトID取得: 拡張機能→Apps Script → URLの /projects/{ID}/edit の {ID} 部分", file=sys.stderr)
        sys.exit(1)

    try:
        commands = {
            "get": cmd_get,
            "update": cmd_update,
            "push": cmd_push,
            "deploy": cmd_deploy,
        }
        commands[args.command](args)
    except Exception as e:
        error_msg = str(e)
        print(json.dumps({"error": error_msg}, ensure_ascii=False), file=sys.stderr)

        # よくあるエラーへのヒント
        if "insufficientPermissions" in error_msg or "403" in error_msg:
            print("[ヒント] Apps Script API のユーザー設定を確認してください:", file=sys.stderr)
            print("  https://script.google.com/home/usersettings", file=sys.stderr)
        elif "scriptId" in error_msg or "404" in error_msg:
            print("[ヒント] スクリプトIDが正しいか確認してください。", file=sys.stderr)
            print("  拡張機能→Apps Script → URLの /projects/{ID}/edit の {ID} 部分", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()
