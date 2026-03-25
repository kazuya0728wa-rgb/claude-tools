"""
マスターデータ移行スクリプト
会計管理シートの依頼者・顧客データを新スプレッドシートに移行する

使い方:
  python migrate_masters.py
"""

import sys
import json

sys.path.insert(0, r"C:\Users\kazuy\.claude\tools\sheets")
from auth import build_service

# スプレッドシートID
SRC_ID = "1s7-24tDHdXOFb5-AkEZjUdQrFDweWmm6NnNWol3NNAU"  # 会計管理シート

# 新スプレッドシートID（setup_spreadsheet.py で生成）
try:
    from config_3link import SPREADSHEET_ID as DST_ID
except ImportError:
    print("[ERROR] config_3link.py が見つかりません。setup_spreadsheet.py を先に実行してください。")
    sys.exit(1)


def get_service():
    return build_service("sheets", "v4")


def migrate_requester_master():
    """依頼者マスターを移行する"""
    service = get_service()

    # 元データ取得
    result = service.spreadsheets().values().get(
        spreadsheetId=SRC_ID,
        range="依頼者一覧!B2:C30",
        valueRenderOption="FORMATTED_VALUE",
    ).execute()

    rows = result.get("values", [])

    # ヘッダー行をスキップ、有効な行だけ抽出
    people = []
    for row in rows[1:]:  # 最初の行はヘッダー
        if len(row) >= 2 and row[0] and row[1]:
            people.append({
                "番号": row[0],
                "名前": row[1],
            })

    if not people:
        print("[WARN] 依頼者データが見つかりませんでした")
        return

    # 新フォーマットに変換
    # 列: 依頼者番号, 依頼者LINE名, 種別, 時給, プルダウン用(数式), 状態, 銀行情報, 備考
    new_rows = []
    for p in people:
        new_rows.append([
            p["番号"],     # A: 依頼者番号
            p["名前"],     # B: 依頼者LINE名
            "業務委託",    # C: 種別（デフォルト）
            "",            # D: 時給（空）
            "",            # E: プルダウン用（数式で自動生成）
            "稼働",        # F: 状態
            "",            # G: 銀行情報
            "",            # H: 備考
        ])

    # 書き込み
    service.spreadsheets().values().update(
        spreadsheetId=DST_ID,
        range="依頼者マスター!A2",
        valueInputOption="RAW",
        body={"values": new_rows},
    ).execute()

    print(f"[OK] 依頼者マスター移行完了: {len(new_rows)}件")
    for p in people:
        print(f"     {p['番号']}: {p['名前']}")


def migrate_customer_master():
    """顧客マスターを移行する"""
    service = get_service()

    # 元データ取得（ヘッダーは6行目から）
    result = service.spreadsheets().values().get(
        spreadsheetId=SRC_ID,
        range="顧客一覧!B6:E30",
        valueRenderOption="FORMATTED_VALUE",
    ).execute()

    rows = result.get("values", [])

    # ヘッダー行をスキップ、有効な行だけ抽出
    customers = []
    for row in rows[1:]:  # 最初の行はヘッダー
        if len(row) >= 2 and row[0] and row[1]:
            customers.append({
                "番号": row[0],
                "名前": row[1].strip(),
            })

    if not customers:
        print("[WARN] 顧客データが見つかりませんでした")
        return

    # 新フォーマットに変換
    # 列: 顧客番号, 顧客名, プルダウン用(数式), 請求書送付先, 備考
    new_rows = []
    for c in customers:
        new_rows.append([
            c["番号"],     # A: 顧客番号
            c["名前"],     # B: 顧客名
            "",            # C: プルダウン用（数式で自動生成）
            "",            # D: 請求書送付先
            "",            # E: 備考
        ])

    # 書き込み
    service.spreadsheets().values().update(
        spreadsheetId=DST_ID,
        range="顧客マスター!A2",
        valueInputOption="RAW",
        body={"values": new_rows},
    ).execute()

    print(f"[OK] 顧客マスター移行完了: {len(new_rows)}件")
    for c in customers:
        print(f"     {c['番号']}: {c['名前']}")


def verify_genre_master():
    """ジャンルマスターの確認"""
    service = get_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=DST_ID,
        range="ジャンルマスター!A2:B10",
        valueRenderOption="FORMATTED_VALUE",
    ).execute()
    rows = result.get("values", [])
    print(f"[OK] ジャンルマスター確認: {len(rows)}件")
    for r in rows:
        if r:
            print(f"     {r[0]}: {r[1] if len(r) > 1 else ''}")


def main():
    print("=" * 50)
    print("マスターデータ移行")
    print(f"  移行元: {SRC_ID}")
    print(f"  移行先: {DST_ID}")
    print("=" * 50)

    migrate_requester_master()
    print()
    migrate_customer_master()
    print()
    verify_genre_master()

    print()
    print("[完了] マスターデータ移行が完了しました")
    print("次のステップ: GAS実装スクリプトを実行してください")


if __name__ == "__main__":
    main()
