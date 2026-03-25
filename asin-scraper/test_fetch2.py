import primp

def fetch_amazon_title(asin):
    url = f"https://www.amazon.co.jp/dp/{asin}"
    client = primp.Client(impersonate="chrome_120")
    try:
        res = client.get(url, timeout=10)
        with open("dump.html", "w", encoding="utf-8") as f:
            f.write(res.text)
    except Exception as e:
        print(f"Error: {e}")

fetch_amazon_title('B00DCGO2PS')
