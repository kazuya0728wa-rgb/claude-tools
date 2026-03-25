import config
from spreadsheet_client import SpreadsheetClient

def test_api():
    print("API接続テストを開始します...")
    try:
        client = SpreadsheetClient()
        range_name = "BC2" 
        print(f"{range_name} に「あ」と書き込みます...")
        
        # BC2セル1つに向けた直接のupdate
        client.sheet.update(range_name=range_name, values=[['あ']])
        print("書き込みが成功しました！ブラウザでスプレッドシートの BC2 セルをご確認ください。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    test_api()
