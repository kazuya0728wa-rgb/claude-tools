import primp
from bs4 import BeautifulSoup
import urllib.parse
import time

def test_ddg(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
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
            results = soup.find_all('a', class_='result__url', limit=3)
            
            for a in results:
                href = a.get('href')
                print(f"URL: {href}")
                # HTML版DDGのリダイレクトURLをクリーンアップしたいが、まずはそのまま検証
        else:
             print("Block detected.")
            
    except Exception as e:
        print(f"Error: {e}")

test_ddg('BenQ GL2580HM 取扱説明書 filetype:pdf')
