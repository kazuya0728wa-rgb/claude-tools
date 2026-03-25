from duckduckgo_search import DDGS
import time

def test_ddg():
    print("Testing DuckDuckGo Python package...")
    
    try:
        # DDGSを使用した検索
        with DDGS(headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}) as ddgs:
            # 検索ワード: BenQ GL2580HM 取扱説明書 filetype:pdf
            results = list(ddgs.text("BenQ GL2580HM 取扱説明書 filetype:pdf", max_results=3))
            
            for index, result in enumerate(results):
                print(f"[{index+1}] Title: {result.get('title')}")
                print(f"URL: {result.get('href')}")
                
    except Exception as e:
        print(f"Error accessing DDG: {e}")

if __name__ == "__main__":
    test_ddg()
