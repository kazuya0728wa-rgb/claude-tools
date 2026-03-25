import os
import fitz  # PyMuPDF
from google import genai
from google.genai import types

# ユーザーから提供されたAPIキーを使用
GEMINI_API_KEY = "AIzaSyD7I46uEPn3gZGIQACn69N-YabtL-KcpE8"

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDFからテキストを抽出する"""
    text = ""
    try:
        # PDFを開く
        doc = fitz.open(pdf_path)
        # 取説の付属品は最初の5ページ以内にあることが多い
        for page_num in range(min(5, len(doc))): 
            page = doc.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        print(f"PDF読み込みエラー: {e}")
        return ""

def extract_accessories_with_gemini(text: str) -> list[str]:
    """Gemini APIを使ってテキストから付属品リストを抽出する"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = """
    以下の取扱説明書のテキストから、「付属品」「同梱品」「パッケージ内容」などを探し出し、
    含まれているアイテムのリストを抽出してください。
    出力は以下のJSONの配列形式のみとしてください。Markdown記号（```json など）は不要です。
    例: ["ACアダプター", "USBケーブル", "取扱説明書", "保証書"]
    付属品の記載がない場合や不明な場合は空の配列 [] を返してください。

    【取扱説明書テキスト】
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
    sample_pdf = "sample_manual.pdf"
    
    if not os.path.exists(sample_pdf):
        print(f"エラー: テスト用のPDF '{sample_pdf}' が見つかりません。")
    else:
        print(f"PDF '{sample_pdf}' のテキストを読み込んでいます...")
        pdf_text = extract_text_from_pdf(sample_pdf)
        
        if pdf_text.strip():
            print(f"テキスト抽出完了（文字数: {len(pdf_text)}）。AIで付属品を抽出します...")
            extracted_items = extract_accessories_with_gemini(pdf_text)
            
            print("\n=== 抽出結果 ===")
            print(f"見つかった付属品 ({len(extracted_items)}個):")
            for item in extracted_items:
                print(f"- {item}")
        else:
            print("PDFからテキストを抽出できませんでした（画像のみのPDFの可能性があります）。")
