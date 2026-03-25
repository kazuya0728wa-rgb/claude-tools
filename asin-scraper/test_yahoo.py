import primp
from bs4 import BeautifulSoup
import urllib.parse

def search_yahoo(query):
    print("Testing Yahoo Japan Search...")
    url = f"https://search.yahoo.co.jp/search?p={urllib.parse.quote(query)}"
    
    try:
        client = primp.Client(impersonate="chrome_120")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        res = client.get(url, headers=headers, timeout=15)
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Yahoo検索結果の各要素
            links = soup.select('.sw-Card__title a')
            for index, a in enumerate(links[:3]):
                href = a.get('href', '')
                title = a.get_text(strip=True)
                print(f"[{index+1}] {title}")
                print(f"URL: {href}")
                
    except Exception as e:
        print(f"Error accessing Yahoo: {e}")

if __name__ == "__main__":
    search_yahoo("BenQ GL2580HM 取扱説明書 filetype:pdf")
