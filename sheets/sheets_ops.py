"""
Google Sheets API CLI

使い方:
  python sheets_ops.py info
  python sheets_ops.py read --range "日報提出!A1:Q5"
  python sheets_ops.py write --range "Settings!B2" --value "2026/01/01"
  python sheets_ops.py formula --range "月次ランキング_表示!A6" --formula "=LET(...)"
  python sheets_ops.py batch --data '[{"range":"Settings!B2","values":[["2026/01/01"]]}]'
  python sheets_ops.py append --sheet "日報提出" --values '[["2026/03/22","池戸 琉登"]]'
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
from config import SPREADSHEET_ID


def get_service():
    return build_service("sheets", "v4")


def cmd_info(args):
    """シート一覧・基本情報を表示"""
    service = get_service()
    result = service.spreadsheets().get(
        spreadsheetId=args.spreadsheet_id,
        fields="spreadsheetId,properties.title,sheets.properties"
    ).execute()

    output = {
        "spreadsheetId": result["spreadsheetId"],
        "title": result["properties"]["title"],
        "sheets": [
            {
                "sheetId": s["properties"]["sheetId"],
                "title": s["properties"]["title"],
                "index": s["properties"]["index"],
                "hidden": s["properties"].get("hidden", False),
            }
            for s in result["sheets"]
        ]
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_read(args):
    """セル範囲の値を読み取る"""
    service = get_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=args.spreadsheet_id,
        range=args.range,
        valueRenderOption="FORMATTED_VALUE",
    ).execute()

    output = {
        "range": result.get("range"),
        "values": result.get("values", []),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_write(args):
    """セルに値を書き込む（RAW = 数式以外）"""
    service = get_service()
    body = {
        "values": [[args.value]]
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=args.spreadsheet_id,
        range=args.range,
        valueInputOption="RAW",
        body=body,
    ).execute()

    print(json.dumps({
        "updatedRange": result.get("updatedRange"),
        "updatedCells": result.get("updatedCells"),
    }, ensure_ascii=False, indent=2))


def cmd_formula(args):
    """数式をセルに書き込む（USER_ENTERED = 数式として解釈）"""
    service = get_service()
    body = {
        "values": [[args.formula]]
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=args.spreadsheet_id,
        range=args.range,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()

    print(json.dumps({
        "updatedRange": result.get("updatedRange"),
        "updatedCells": result.get("updatedCells"),
    }, ensure_ascii=False, indent=2))


def cmd_batch(args):
    """複数セルを一括更新"""
    service = get_service()
    data = json.loads(args.data)
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": data,
    }
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=args.spreadsheet_id,
        body=body,
    ).execute()

    print(json.dumps({
        "totalUpdatedCells": result.get("totalUpdatedCells"),
        "responses": [
            {"updatedRange": r.get("updatedRange"), "updatedCells": r.get("updatedCells")}
            for r in result.get("responses", [])
        ],
    }, ensure_ascii=False, indent=2))


def cmd_append(args):
    """シートの末尾に行を追加"""
    service = get_service()
    values = json.loads(args.values)
    body = {"values": values}
    result = service.spreadsheets().values().append(
        spreadsheetId=args.spreadsheet_id,
        range=f"{args.sheet}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()

    updates = result.get("updates", {})
    print(json.dumps({
        "updatedRange": updates.get("updatedRange"),
        "updatedRows": updates.get("updatedRows"),
        "updatedCells": updates.get("updatedCells"),
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Google Sheets API CLI")
    parser.add_argument(
        "--spreadsheet-id",
        default=SPREADSHEET_ID,
        help=f"スプレッドシートID（デフォルト: {SPREADSHEET_ID}）",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # info
    subparsers.add_parser("info", help="シート一覧・基本情報を表示")

    # read
    p_read = subparsers.add_parser("read", help="セル範囲の値を読み取る")
    p_read.add_argument("--range", required=True, help='例: "日報提出!A1:Q5"')

    # write
    p_write = subparsers.add_parser("write", help="セルに値を書き込む")
    p_write.add_argument("--range", required=True, help='例: "Settings!B2"')
    p_write.add_argument("--value", required=True, help="書き込む値")

    # formula
    p_formula = subparsers.add_parser("formula", help="セルに数式を書き込む")
    p_formula.add_argument("--range", required=True, help='例: "月次ランキング_表示!A6"')
    p_formula.add_argument("--formula", required=True, help='例: "=LET(...)"')

    # batch
    p_batch = subparsers.add_parser("batch", help="複数セルを一括更新")
    p_batch.add_argument(
        "--data",
        required=True,
        help='JSON形式: \'[{"range":"A1","values":[["v1"]]}]\'',
    )

    # append
    p_append = subparsers.add_parser("append", help="シートの末尾に行を追加")
    p_append.add_argument("--sheet", required=True, help='シート名（例: "日報提出"）')
    p_append.add_argument(
        "--values",
        required=True,
        help='JSON形式の2次元配列: \'[["2026/03/22","氏名",...]]\'',
    )

    args = parser.parse_args()

    try:
        commands = {
            "info": cmd_info,
            "read": cmd_read,
            "write": cmd_write,
            "formula": cmd_formula,
            "batch": cmd_batch,
            "append": cmd_append,
        }
        commands[args.command](args)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
