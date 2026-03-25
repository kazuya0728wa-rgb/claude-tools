"""
月次ランキング スナップショット作成

使い方:
  python snapshot.py               # 前月のスナップショットを作成
  python snapshot.py 2026-01       # 指定月のスナップショットを作成
  python snapshot.py --list        # 保存済みスナップショット一覧

動作:
  1. Settings!B2 に対象月をセット
  2. 月次ランキング_表示 の計算結果（値）を読み取り
  3. "2026-02" などの名前で新シートを作成してコピー
  4. Settings!B2 をリセット（空に戻す）
"""

import io
import json
import os
import sys
import time
from datetime import date, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from auth import build_service
from config import SPREADSHEET_ID

RANKING_SHEET_ID = 618096803  # 月次ランキング_表示


def get_prev_month() -> str:
    """前月の1日を "YYYY-MM-DD" 形式で返す"""
    today = date.today()
    first_this_month = today.replace(day=1)
    last_prev = first_this_month - timedelta(days=1)
    return last_prev.replace(day=1).strftime("%Y/%m/%d")


def get_sheet_titles(service) -> dict:
    """シート名 → sheetId のマップを返す"""
    result = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        fields="sheets.properties"
    ).execute()
    return {
        s["properties"]["title"]: s["properties"]["sheetId"]
        for s in result["sheets"]
    }


def create_snapshot(target_month: str = None):
    """
    target_month: "YYYY-MM" 形式（省略時は前月）
    """
    service = build_service("sheets", "v4")

    # 対象月の決定
    if target_month:
        year, month = target_month.split("-")
        month_date_str = f"{year}/{int(month):02d}/01"
        sheet_name = target_month  # 例: "2026-02"
    else:
        prev = get_prev_month()
        year, month, _ = prev.split("/")
        month_date_str = prev
        sheet_name = f"{year}-{month}"

    print(f"対象月: {sheet_name} ({month_date_str})")

    # 既にスナップショットが存在するか確認
    titles = get_sheet_titles(service)
    if sheet_name in titles:
        print(f"[SKIP] シート '{sheet_name}' は既に存在します。上書きする場合は先に削除してください。")
        sys.exit(0)

    # Step 1: Settings!B2 に対象月をセット
    print("Settings!B2 に対象月をセット中...")
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Settings!B2",
        valueInputOption="USER_ENTERED",
        body={"values": [[month_date_str]]},
    ).execute()

    # スピル数式の再計算を待つ
    time.sleep(2)

    # Step 2: 月次ランキング_表示 の値を読み取り（A1から全体）
    print("ランキングデータを読み取り中...")
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="月次ランキング_表示!A1:F50",
        valueRenderOption="FORMATTED_VALUE",
    ).execute()
    values = result.get("values", [])

    if not values:
        print("[ERROR] ランキングデータが空です。日報データを確認してください。")
        _reset_settings(service)
        sys.exit(1)

    print(f"  {len(values)} 行取得")

    # Step 3: 新しいシートを作成
    print(f"シート '{sheet_name}' を作成中...")
    add_sheet_req = {
        "addSheet": {
            "properties": {
                "title": sheet_name,
                "index": 3,  # 月次ランキング_表示の後ろに挿入
            }
        }
    }
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": [add_sheet_req]},
    ).execute()
    new_sheet_id = result["replies"][0]["addSheet"]["properties"]["sheetId"]

    # Step 4: 値をコピー
    print("データをコピー中...")
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{sheet_name}'!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    # Step 5: Settings!B2 をリセット（空に戻す = 前月自動）
    _reset_settings(service)

    print(f"\n[完了] '{sheet_name}' シートにランキングを保存しました。")
    print(f"  保存行数: {len(values)} 行")


def _reset_settings(service):
    """Settings!B2 を空に戻す"""
    print("Settings!B2 をリセット中...")
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range="Settings!B2",
    ).execute()


def list_snapshots():
    """保存済みスナップショット一覧を表示"""
    service = build_service("sheets", "v4")
    titles = get_sheet_titles(service)

    snapshots = sorted([t for t in titles if len(t) == 7 and t[4] == "-"])
    if snapshots:
        print("保存済みスナップショット:")
        for s in snapshots:
            print(f"  {s}")
    else:
        print("スナップショットはまだありません。")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_snapshots()
        return

    target = sys.argv[1] if len(sys.argv) > 1 else None

    # 形式チェック
    if target:
        try:
            year, month = target.split("-")
            assert len(year) == 4 and len(month) == 2
        except Exception:
            print("[ERROR] 月の指定形式が不正です。例: 2026-02")
            sys.exit(1)

    create_snapshot(target)


if __name__ == "__main__":
    main()
