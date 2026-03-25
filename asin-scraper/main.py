import sys
import config
from spreadsheet_client import SpreadsheetClient
from asin_processor import is_valid_asin, should_process_row
from web_investigator import fetch_accessory_info

def col_num_to_letter(n: int) -> str:
    """1-basedの列番号をアルファベット(A, B... Z, AA...)に変換"""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def main():
    print("--- Amazon ASIN 付属品調査ツール (Mock Version) ---")
    
    try:
        client = SpreadsheetClient()
    except Exception as e:
        print("起動処理を中断します。設定を確認してください。")
        sys.exit(1)

    print("スプレッドシートのデータを取得中...")
    rows = client.get_all_records()
    
    if not rows:
        print("データがありませんでした。")
        return

    updates = []
    
    for i, row in enumerate(rows):
        row_num = i + 1 # スプレッドシートの行番号(1始まり)
        
        # 1行目はヘッダーなどのためスキップ
        if row_num < config.START_ROW:
            continue
            
        # ユーザー要望により指定行までで停止（None の場合は全行処理）
        if config.END_ROW is not None and row_num > config.END_ROW:
            print(f"[{config.END_ROW}行目到達] 処理を終了します。")
            break
            
        # リストの長さが足りていない場合を考慮しつつ値を取得
        # indexは列番号 - 1
        asin = row[config.COL_ASIN - 1] if len(row) >= config.COL_ASIN else ""
        accessory_val = row[config.COL_ACCESSORY - 1] if len(row) >= config.COL_ACCESSORY else ""
        url_val = row[config.COL_URL - 1] if len(row) >= config.COL_URL else ""
        
        if should_process_row(asin, accessory_val, url_val):
            print(f"対象行発見: {row_num}行目 (ASIN: {asin})")
            
            # 調査ロジックの呼び出し
            result = fetch_accessory_info(asin)

            # Rate Limit等でスキップされた場合はNoneが返るので書き込みしない
            if result is None:
                print(f"  [{asin}] スキップ（空欄のまま維持）")
                continue

            try:
                # 1件ごとに更新
                col_bb_letter = col_num_to_letter(config.COL_ALT_URL)
                col_bc_letter = col_num_to_letter(config.COL_ACCESSORY)
                col_bd_letter = col_num_to_letter(config.COL_URL)
                
                # BB列（ヨドバシ/ビックカメラURL）
                if result.get('alt_url'):
                    client.sheet.update(range_name=f"{col_bb_letter}{row_num}", values=[[result['alt_url']]])

                # BC列（付属品）
                client.sheet.update(range_name=f"{col_bc_letter}{row_num}", values=[[result['accessories']]])

                # BD列（AmazonページURL）
                if result['urls']:
                    client.sheet.update(range_name=f"{col_bd_letter}{row_num}", values=[[result['urls']]])
                     
                print(f"  [{asin}] スプレッドシートへ保存完了")
            except Exception as e:
                print(f"  [{asin}] 書き込み中にエラーが発生しました: {e}")

    print("--- 処理が完了しました ---")

if __name__ == "__main__":
    main()
