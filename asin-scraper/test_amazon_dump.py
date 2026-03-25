import primp
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

asins = [
    "B07X3WMRPB", "B074WTMCDJ", "B00DCGO2PS", "B074WZJ4K2", "B077SHM6W6",
    "B01KUW5BC4", "B00PF4UC2M", "B08KGPL974", "B0982VXNXN", "B076LY7BHH"
]

def check_amazon_accessories(asin):
    url = f"https://www.amazon.co.jp/dp/{asin}"
    try:
        client = primp.Client(impersonate="chrome_120")
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = client.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            print(f"\n[{asin}] ---")
            
            # テーブル情報
            for th in soup.find_all(['th', 'td']):
                text = th.get_text(strip=True)
                if '付属' in text or '同梱' in text:
                    sibling = th.find_next_sibling(['td', 'span'])
                    if sibling:
                        print(f"Table/Row: {text} -> {sibling.get_text(strip=True)}")
                        
            # "付属品" という単語を含む全テキスト
            for elem in soup.find_all(string=lambda text: text and '付属品' in text):
                 parent = elem.parent
                 if parent.name not in ['script', 'style']:
                     print(f"Text : {elem.strip()}")
                     
        else:
            print(f"[{asin}] HTTP {res.status_code}")
    except Exception as e:
         pass

for a in asins:
    check_amazon_accessories(a)
