import os
import re
from bs4 import BeautifulSoup
import primp
from google import genai
from google.genai import types

GEMINI_API_KEY = "AIzaSyD7I46uEPn3gZGIQACn69N-YabtL-KcpE8"

def fetch_amazon_product_text(asin: str) -> str:
    """ASINからAmazon商品ページのテキストを取得する"""
    url = f"https://www.amazon.co.jp/dp/{asin}"
    print(f"[{asin}] Amazonページを取得中: {url}")
    
    try:
        # primpを使用してブロックを回避（Chromeを偽装）
        client = primp.Client(impersonate="chrome_120")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        res = client.get(url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 不要なタグを削除（スクリプトやスタイルなど）
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
                
            # テキストを抽出
            text = soup.get_text(separator=' ', strip=True)
            # 連続する不要な空白や改行を削減
            clean_text = re.sub(r'\s+', ' ', text)
            
            # ページ全体だとトークン数が多すぎるため、「特長」「説明」「同梱」「付属」などの周辺テキストを切り出すか、
            # 最初から中盤あたりを切り出す。今回は全体の最初の20000文字程度に絞る
            print(f"[{asin}] 取得成功 (文字数: {len(clean_text)})")
            return clean_text[:20000]
        else:
            print(f"[{asin}] 取得失敗 (ステータスコード: {res.status_code})")
            return ""
            
    except Exception as e:
        print(f"[{asin}] 取得エラー: {e}")
        return ""

def extract_accessories_with_gemini(text: str) -> list[str]:
    """Gemini APIを使ってウェブページのテキストから付属品リストを抽出する"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = """
    以下のテキストはAmazonなどの商品のウェブページから抽出されたテキストです。
    この商品に含まれる「付属品」「同梱品」「パッケージ内容」などを探し出し、
    含まれているアイテムのリストを抽出してください。
    
    出力は以下のJSONの配列形式のみとしてください。Markdown記号（```json など）は不要です。
    例: ["ACアダプター", "USBケーブル", "取扱説明書", "保証書"]
    付属品の記載がない場合や不明な場合は空の配列 [] を返してください。

    【ウェブページテキスト】
    """ + text

    print("Geminiに解析を依頼中...")
    response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", 
        ),
    )
    
    import json
    try:
        accessories = json.loads(response.text)
        return accessories
    except json.JSONDecodeError:
        print("JSONのパースに失敗しました。AIの生の回答:", response.text)
        return []

if __name__ == "__main__":
    test_asin = "B074WTMCDJ"
    
    print("=" * 40)
    print(f"ウェブページAI抽出テスト (ASIN: {test_asin})")
    print("=" * 40)
    
    page_text = fetch_amazon_product_text(test_asin)
    
    if page_text:
        extracted_items = extract_accessories_with_gemini(page_text)
        
        print("\n=== 抽出結果 ===")
        print(f"見つかった付属品 ({len(extracted_items)}個):")
        if extracted_items:
            for item in extracted_items:
                print(f"- {item}")
        else:
            print("- なし（検出できませんでした）")
    else:
        print("ページのテキストが取得できなかったため終了します。")
