import primp
from bs4 import BeautifulSoup

def fetch_amazon_title(asin):
    url = f"https://www.amazon.co.jp/dp/{asin}"
    try:
        # User-Agentを指定してPC版ページを要求
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        client = primp.Client(impersonate="chrome_120")
        res = client.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # 1. PC版の productTitle を探す
            title_elem = soup.find(id='productTitle')
            if title_elem:
                return title_elem.get_text(strip=True)
            
            # 2. スマホ版などで id="title" となっている場合を探す
            title_elem_mobile = soup.find(id='title')
            if title_elem_mobile:
                return title_elem_mobile.get_text(strip=True)
                
            # 3. どちらもない場合は <title> タグから抽出する
            if soup.title and soup.title.string:
                title_text = soup.title.string.replace('Amazon.co.jp: ', '').replace('Amazon.co.jp： ', '').replace('Amazon | ', '')
                # 末尾のカテゴリー等（「: 家電＆カメラ」など）を削除したいが、単純化のため「 : 」で分割
                title_parts = title_text.split(' : ')
                if title_parts:
                    return title_parts[0].strip()
                    
        print(f"[{asin}] HTTP {res.status_code}")
    except Exception as e:
        print(f"[{asin}] Error: {e}")
    return None

print("B074WTMCDJ:", fetch_amazon_title('B074WTMCDJ'))
print("B00DCGO2PS:", fetch_amazon_title('B00DCGO2PS'))
print("B074WZJ4K2:", fetch_amazon_title('B074WZJ4K2'))
print("B077SHM6W6:", fetch_amazon_title('B077SHM6W6'))
