def fetch_accessory_info(asin: str) -> dict:
    """
    ASINを受け取り、付属品情報を返すモック（ダミー）関数
    戻り値の形式:
      {
          'accessories': str, # カンマ区切りの付属品、または "説明書未検出"
          'urls': str         # 改行区切りの根拠URL、または ""
      }
    """
    asin = asin.strip().upper()
    
    # 動作確認のため、ASINの末尾の文字によって結果を出し分けるダミー実装
    if asin.endswith('1'):
        return {
            'accessories': 'リモコン,単3乾電池×2,取扱説明書',
            'urls': 'https://example.com/manual/1\nhttps://amazon.co.jp/dp/' + asin
        }
    elif asin.endswith('2'):
        # 説明書が見つからない・記載がないパターン
        return {
            'accessories': '説明書未検出',
            'urls': ''
        }
    else:
        return {
            'accessories': 'USBケーブル,ACアダプタ',
            'urls': 'https://example.com/product/' + asin
        }
