"""
株式会社スリーンク 統合管理ツール
新スプレッドシートのセットアップスクリプト

実行すると:
  1. 新しいスプレッドシートを作成
  2. 全シートを追加（ヘッダー・ドロップダウン設定込み）
  3. スプレッドシートIDを出力

使い方:
  python setup_spreadsheet.py
"""

import sys
import os
import json

sys.path.insert(0, r"C:\Users\kazuy\.claude\tools\sheets")
from auth import build_service

SHEETS_SERVICE = None


def get_service():
    global SHEETS_SERVICE
    if SHEETS_SERVICE is None:
        SHEETS_SERVICE = build_service("sheets", "v4")
    return SHEETS_SERVICE


# =====================================================
# シート定義
# =====================================================

SHEET_DEFS = [
    {
        "name": "依頼者マスター",
        "headers": ["依頼者番号", "依頼者LINE名", "種別", "時給", "プルダウン用", "状態", "銀行情報", "備考"],
        "frozen_rows": 1,
    },
    {
        "name": "顧客マスター",
        "headers": ["顧客番号", "顧客名", "プルダウン用", "請求書送付先", "備考"],
        "frozen_rows": 1,
    },
    {
        "name": "ジャンルマスター",
        "headers": ["ジャンル番号", "ジャンル名"],
        "frozen_rows": 1,
    },
    {
        "name": "案件テーブル",
        "headers": [
            "案件番号", "依頼者番号", "依頼者LINE名", "顧客番号", "顧客名",
            "ジャンル番号", "ジャンル名", "案件詳細", "発注日", "納品希望日",
            "予想費用", "状態", "LINE文章", "成果物URL", "登録日時"
        ],
        "frozen_rows": 1,
    },
    {
        "name": "成果物テーブル",
        "headers": ["記録ID", "案件番号", "提出日時", "依頼者番号", "依頼者LINE名", "納品物URL", "コメント"],
        "frozen_rows": 1,
    },
    {
        "name": "依頼者請求テーブル",
        "headers": ["記録ID", "案件番号", "依頼者番号", "依頼者LINE名", "請求年月", "請求金額", "請求書URL", "支払期限", "支払済み"],
        "frozen_rows": 1,
    },
    {
        "name": "クライアント請求テーブル",
        "headers": ["請求ID", "顧客番号", "顧客名", "請求年月", "ジャンル番号", "ジャンル名", "原価合計", "請求額", "消費税区分", "請求書URL", "振込期限", "入金済み"],
        "frozen_rows": 1,
    },
    {
        "name": "稼働記録テーブル",
        "headers": ["記録ID", "年月", "日付", "依頼者番号", "依頼者LINE名", "顧客番号", "顧客名", "開始時刻", "終了時刻", "稼働時間", "時給", "支払額", "作業内容", "備考"],
        "frozen_rows": 1,
    },
    {
        "name": "固定費テーブル",
        "headers": ["固定費ID", "品目", "顧客番号", "顧客名", "月額", "消費税区分", "適用開始月", "適用終了月", "備考"],
        "frozen_rows": 1,
    },
    {
        "name": "収支ダッシュボード",
        "headers": [],
        "frozen_rows": 0,
    },
    {
        "name": "確定申告用シート",
        "headers": [],
        "frozen_rows": 0,
    },
    {
        "name": "依頼者別確認",
        "headers": [],
        "frozen_rows": 0,
    },
]

# 案件テーブルの「状態」列のドロップダウン値
CASE_STATUS_VALUES = [
    "発注中", "納品待ち", "承認待ち", "請求待ち", "支払待ち", "支払済み"
]

# 依頼者マスターの「種別」列のドロップダウン値
PERSON_TYPE_VALUES = ["業務委託", "秘書"]

# 依頼者マスターの「状態」列のドロップダウン値
PERSON_STATUS_VALUES = ["稼働", "停止"]

# 固定費/クライアント請求テーブルの「消費税区分」
TAX_VALUES = ["課税", "非課税"]


def create_spreadsheet(title: str) -> str:
    """スプレッドシートを作成して ID を返す"""
    service = get_service()
    # 最初のシートを「依頼者マスター」として作成
    body = {
        "properties": {"title": title, "locale": "ja_JP"},
        "sheets": [{"properties": {"title": "依頼者マスター"}}],
    }
    result = service.spreadsheets().create(body=body).execute()
    spreadsheet_id = result["spreadsheetId"]
    print(f"[OK] スプレッドシート作成: {title}")
    print(f"     ID: {spreadsheet_id}")
    print(f"     URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    return spreadsheet_id


def add_sheets(spreadsheet_id: str) -> dict[str, int]:
    """シートを追加して {シート名: sheetId} を返す"""
    service = get_service()
    requests = []
    for sheet_def in SHEET_DEFS[1:]:  # 最初は既に作成済み
        requests.append({
            "addSheet": {
                "properties": {"title": sheet_def["name"]}
            }
        })
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()

    # sheetId を取得
    sheet_ids = {}
    for reply in result.get("replies", []):
        if "addSheet" in reply:
            props = reply["addSheet"]["properties"]
            sheet_ids[props["title"]] = props["sheetId"]

    # 最初のシートIDも取得
    meta = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties"
    ).execute()
    for s in meta["sheets"]:
        props = s["properties"]
        sheet_ids[props["title"]] = props["sheetId"]

    print(f"[OK] シート追加完了: {len(SHEET_DEFS)}シート")
    return sheet_ids


def write_headers(spreadsheet_id: str, sheet_ids: dict):
    """全シートにヘッダー行を書き込む"""
    service = get_service()
    data = []
    for sheet_def in SHEET_DEFS:
        if not sheet_def["headers"]:
            continue
        data.append({
            "range": f"'{sheet_def['name']}'!A1",
            "values": [sheet_def["headers"]],
        })
    if data:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "RAW", "data": data},
        ).execute()
    print("[OK] ヘッダー行書き込み完了")


def write_genre_master(spreadsheet_id: str):
    """ジャンルマスターの初期データを書き込む"""
    service = get_service()
    genres = [
        ["1", "YouTube運用代行"],
        ["2", "Instagram"],
        ["3", "デザイン"],
        ["4", "LINE構築"],
        ["5", "ローンチ代行"],
        ["6", "その他"],
    ]
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="ジャンルマスター!A2",
        valueInputOption="RAW",
        body={"values": genres},
    ).execute()
    print("[OK] ジャンルマスター初期データ書き込み完了")


def apply_formatting(spreadsheet_id: str, sheet_ids: dict):
    """ヘッダー行の書式設定・フリーズ・列幅調整"""
    requests = []

    # ヘッダー行が存在するシートの設定
    for sheet_def in SHEET_DEFS:
        if not sheet_def["headers"]:
            continue
        sheet_id = sheet_ids.get(sheet_def["name"])
        if sheet_id is None:
            continue

        n_cols = len(sheet_def["headers"])

        # ヘッダー行: 背景色（濃紺）・文字色（白）・太字
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": n_cols,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.18, "green": 0.31, "blue": 0.31},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True,
                        },
                        "horizontalAlignment": "CENTER",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        })

        # 行フリーズ
        if sheet_def["frozen_rows"] > 0:
            requests.append({
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": sheet_def["frozen_rows"]},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            })

    get_service().spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()
    print("[OK] 書式設定完了")


def apply_validations(spreadsheet_id: str, sheet_ids: dict):
    """ドロップダウンバリデーションを設定する"""
    requests = []

    def dropdown_request(sheet_id, col_index, values, start_row=1):
        return {
            "setDataValidation": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row,
                    "endRowIndex": 1000,
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1,
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": v} for v in values],
                    },
                    "showCustomUi": True,
                    "strict": True,
                },
            }
        }

    # 依頼者マスター: C列=種別(2), F列=状態(5)
    rid = sheet_ids["依頼者マスター"]
    requests.append(dropdown_request(rid, 2, PERSON_TYPE_VALUES))
    requests.append(dropdown_request(rid, 5, PERSON_STATUS_VALUES))

    # 案件テーブル: L列=状態(11)
    aid = sheet_ids["案件テーブル"]
    requests.append(dropdown_request(aid, 11, CASE_STATUS_VALUES))

    # クライアント請求テーブル: I列=消費税区分(8)
    cid = sheet_ids["クライアント請求テーブル"]
    requests.append(dropdown_request(cid, 8, TAX_VALUES))

    # 固定費テーブル: F列=消費税区分(5)
    fid = sheet_ids["固定費テーブル"]
    requests.append(dropdown_request(fid, 5, TAX_VALUES))

    get_service().spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()
    print("[OK] バリデーション設定完了")


def apply_pulldown_formulas(spreadsheet_id: str):
    """プルダウン用の数式を設定"""
    service = get_service()

    # 依頼者マスター E列: =ARRAYFORMULA(IF(A2:A="","",A2:A&" "&B2:B))
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="依頼者マスター!E2",
        valueInputOption="USER_ENTERED",
        body={"values": [['=ARRAYFORMULA(IF(A2:A="","",A2:A&" "&B2:B))']]},
    ).execute()

    # 顧客マスター C列: =ARRAYFORMULA(IF(A2:A="","",A2:A&" "&B2:B))
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="顧客マスター!C2",
        valueInputOption="USER_ENTERED",
        body={"values": [['=ARRAYFORMULA(IF(A2:A="","",A2:A&" "&B2:B))']]},
    ).execute()

    print("[OK] プルダウン用数式設定完了")


def main():
    print("=" * 50)
    print("株式会社スリーンク 統合管理ツール セットアップ")
    print("=" * 50)

    # スプレッドシート作成
    spreadsheet_id = create_spreadsheet("【スリーンク】統合管理ツール")

    # シート追加
    sheet_ids = add_sheets(spreadsheet_id)

    # ヘッダー書き込み
    write_headers(spreadsheet_id, sheet_ids)

    # ジャンルマスター初期データ
    write_genre_master(spreadsheet_id)

    # 書式設定
    apply_formatting(spreadsheet_id, sheet_ids)

    # ドロップダウンバリデーション
    apply_validations(spreadsheet_id, sheet_ids)

    # プルダウン用数式
    apply_pulldown_formulas(spreadsheet_id)

    print()
    print("=" * 50)
    print("[完了] セットアップが完了しました！")
    print(f"スプレッドシートID: {spreadsheet_id}")
    print(f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print()
    print("次のステップ:")
    print("  1. 上記URLを開いてシート構成を確認")
    print("  2. setup_spreadsheet.py と同じフォルダの config_3link.py に")
    print(f"     SPREADSHEET_ID = \"{spreadsheet_id}\"  を記入")
    print("  3. マスターデータ移行スクリプトを実行")
    print("=" * 50)

    # 設定ファイルに自動書き込み
    config_path = os.path.join(os.path.dirname(__file__), "config_3link.py")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(f'SPREADSHEET_ID = "{spreadsheet_id}"\n')
        f.write(f'GAS_SCRIPT_ID = ""  # GAS作成後に記入\n')
    print(f"[OK] config_3link.py を自動生成しました: {config_path}")

    return spreadsheet_id


if __name__ == "__main__":
    main()
