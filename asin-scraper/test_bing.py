import primp
from bs4 import BeautifulSoup
import urllib.parse
import re

def test_bing(query):
    # Bingの検索URLを作成
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    
    try:
        client = primp.Client(impersonate="chrome_120")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        res = client.get(url, headers=headers, timeout=15)
        
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Bingの検索結果リンク要素 (b_algo クラス内の h2 > a)
            results = soup.select('.b_algo h2 a')
            
            for a in results[:3]:
                href = a.get('href')
                print(f"URL: {href}")
        else:
             print("Block detected.")
            
    except Exception as e:
        print(f"Error: {e}")

test_bing('BenQ GL2580HM 取扱説明書 filetype:pdf')
