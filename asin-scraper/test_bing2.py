import primp
from bs4 import BeautifulSoup
import urllib.parse
import re

def search_bing(query, max_results=3):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    results = []
    
    try:
        client = primp.Client(impersonate="chrome_120")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        res = client.get(url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Bingの検索結果は .b_algo クラスを持つ要素内にある
            items = soup.select('.b_algo h2 a')
            
            for a in items[:max_results]:
                href = a.get('href', '')
                title = a.get_text(strip=True)
                
                # BingのリダイレクトURLの解決（BASE64エンコードっぽい u=a1... のデコードが必要だが、
                # 直接的なリンクになっているか確認する）
                
                # u= 引数にエンコードされたURLがある場合の簡易解析 (Base64だがパディング等を考慮する必要がある)
                match = re.search(r'u=a1([A-Za-z0-9\-_]+)', href)
                if match:
                    import base64
                    encoded_url = match.group(1)
                    # paddingの補充
                    encoded_url += '=' * ((4 - len(encoded_url) % 4) % 4)
                    try:
                         # URL Safe base64 のデコード (URLの一部に使われるため - や _ も考慮)
                         decoded_bytes = base64.urlsafe_b64decode(encoded_url)
                         real_url = decoded_bytes.decode('utf-8', errors='ignore')
                         href = real_url
                    except Exception as e:
                         print(f"Decode error: {e}")
                
                if href and not href.startswith('/'): # 相対パス等を除外
                     results.append({'title': title, 'href': href})
                     
    except Exception as e:
        print(f"  [Warn] Bing検索に失敗しました: {e}")
        
    return results

print("=== Bing Search Results ===")
res = search_bing('BenQ GL2580HM 取扱説明書 filetype:pdf')
for r in res:
     print(r)
