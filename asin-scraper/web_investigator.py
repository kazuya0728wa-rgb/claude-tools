import re
import requests
from bs4 import BeautifulSoup
import time
import primp
import urllib.parse

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
    'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
}

GEMINI_API_KEY = "AIzaSyD7I46uEPn3gZGIQACn69N-YabtL-KcpE8"

# ==================== ヨドバシ検索 ====================

def search_yodobashi_url(product_name: str) -> str:
    """商品名でヨドバシ.comを検索し、最初の商品ページURLを返す"""
    try:
        query = urllib.parse.quote(product_name)
        search_url = f"https://www.yodobashi.com/category/0/0/0/0/?word={query}"

        client = primp.Client(impersonate="chrome_120")
        res = client.get(search_url, headers=HEADERS, timeout=15)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # 商品リンクを探す
            link = soup.select_one('a[href*="/product/"]')
            if link:
                href = link.get('href', '')
                if href.startswith('/'):
                    return f"https://www.yodobashi.com{href}"
                return href
    except Exception as e:
        print(f"  [Warn] ヨドバシ検索失敗: {e}")
    return ""


def search_biccamera_url(product_name: str) -> str:
    """商品名でビックカメラを検索し、最初の商品ページURLを返す"""
    try:
        query = urllib.parse.quote(product_name)
        search_url = f"https://www.biccamera.com/bc/category/?q={query}"

        client = primp.Client(impersonate="chrome_120")
        res = client.get(search_url, headers=HEADERS, timeout=15)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            link = soup.select_one('a[href*="/bc/item/"]')
            if link:
                href = link.get('href', '')
                if href.startswith('/'):
                    return f"https://www.biccamera.com{href}"
                return href
    except Exception as e:
        print(f"  [Warn] ビックカメラ検索失敗: {e}")
    return ""


def find_alt_shop_url(product_name: str, asin: str) -> str:
    """ヨドバシ→ビックカメラの順で検索してURLを返す"""
    print(f"  [{asin}] ヨドバシ/ビックカメラを検索中...")

    url = search_yodobashi_url(product_name)
    if url:
        print(f"  [{asin}] ヨドバシURL発見: {url[:60]}...")
        return url

    url = search_biccamera_url(product_name)
    if url:
        print(f"  [{asin}] ビックカメラURL発見: {url[:60]}...")
        return url

    print(f"  [{asin}] ヨドバシ/ビックカメラでは見つかりませんでした")
    return ""


# ==================== Amazon商品名取得 ====================

def _get_product_title(soup: BeautifulSoup) -> str:
    """BeautifulSoupオブジェクトからAmazon商品のタイトルを取得"""
    title_el = soup.select_one('#productTitle')
    if title_el:
        return title_el.get_text(strip=True)
    return ""


# ==================== AI抽出ロジック ====================

def _extract_accessories_ai(page_text: str, asin: str) -> list[str]:
    """Gemini APIを使ってウェブページテキストから付属品リストを抽出する"""
    from google import genai
    from google.genai import types
    import json

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = """
以下のテキストはAmazonの商品ページから抽出されたテキストです。
この商品に含まれる「付属品」「同梱品」「パッケージ内容」などを探し出し、
含まれているアイテムのリストを抽出してください。

出力はJSONの配列形式のみとしてください。Markdown記号（```json など）は不要です。
例: ["ACアダプター", "USBケーブル", "取扱説明書"]
付属品の記載がない場合や不明な場合は空の配列 [] を返してください。

【注意事項】
- 「別売」「オプション」など、同梱されないものは含めないでください
- 「本体」「商品本体」や商品の製品名・ブランド名は含めないでください
  例: "Bose QuietComfort Ultra Headphones" → 含めない
  例: "モニター本体" → 含めない
- 型番・モデル番号は除外してアイテム種類名のみにしてください
  例: "ACアダプターAC-UB10C/UB10D" → "ACアダプター"
  例: "リチャージャブルバッテリーパックNP-BX1" → "バッテリーパック"
  例: "USBケーブル(Type-C, 1.5m)" → "USBケーブル"
- 括弧内の情報（長さ・個数・型番・規格）は全て除外してください
  例: "DisplayPortケーブル(1.8m)" → "DisplayPortケーブル"
  例: "ネジ(4個)" → "ネジ"
- 元箱・梱包材・パッケージは含めないでください

【ウェブページテキスト】
""" + page_text

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        accessories = json.loads(response.text)
        if isinstance(accessories, list):
            return [str(a).strip() for a in accessories if str(a).strip()]
        return []

    except Exception as e:
        err_str = str(e)
        if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
            print(f"  [{asin}] [Rate Limit] スキップ（次回実行時に再処理）")
            raise
        else:
            print(f"  [{asin}] [Warn] AI抽出中にエラーが発生: {e}")
            return []


# ==================== メイン処理 ====================

def fetch_accessory_info(asin: str) -> dict:
    """ASINに基づいてAmazonページを取得し、Gemini AIで付属品と根拠URL、ヨドバシURLを返す"""
    asin = asin.strip().upper()
    result = {
        'accessories': '付属品記載なし',
        'urls': '',
        'alt_url': ''  # BB列: ヨドバシ/ビックカメラURL
    }

    print(f"  [{asin}] 調査開始（AIモード）...")

    amazon_url = f"https://www.amazon.co.jp/dp/{asin}"

    try:
        client = primp.Client(impersonate="chrome_120")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        res = client.get(amazon_url, headers=headers, timeout=15)

        if res.status_code != 200:
            print(f"  [{asin}] Amazonページの取得に失敗 (status: {res.status_code})")
            return result

        soup = BeautifulSoup(res.text, 'html.parser')

        # 商品タイトルを取得（ヨドバシ検索用）
        product_title = _get_product_title(soup)

        # 不要なタグを削除
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.extract()

        # テキストを取得し、最大20000文字に絞る
        page_text = re.sub(r'\s+', ' ', soup.get_text(separator=' ', strip=True))[:20000]

        print(f"  [{asin}] ページ取得成功（文字数: {len(page_text)}）。Geminiで解析中...")

        items = _extract_accessories_ai(page_text, asin)

        if items:
            acc_str = ",".join(items)
            result['accessories'] = acc_str
            result['urls'] = amazon_url
            print(f"  [{asin}] [AI] 付属品を抽出: {acc_str}")
        else:
            print(f"  [{asin}] AIが付属品を検出できませんでした")

        # ヨドバシ/ビックカメラURLを検索（商品タイトルがある場合）
        if product_title:
            alt_url = find_alt_shop_url(product_title, asin)
            if alt_url:
                result['alt_url'] = alt_url

    except Exception as e:
        err_str = str(e)
        if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
            print(f"  [{asin}] [Rate Limit] この行はスキップ（次回実行で再処理）")
            return None
        print(f"  [{asin}] エラーが発生しました: {e}")

    return result
