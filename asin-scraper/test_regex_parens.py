import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def clean_accessories(text: str) -> str:
    # カッコとその中身を削除（長さなどの説明を除外）
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'（[^）]*）', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'【[^】]*】', '', text)
    
    # 簡易的にHTMLタグを改行に置換
    text = re.sub(r'<[^>]+>', '\n', text)
    
    # 付属品・同梱物・同梱品・セット内容 に続く文字列を抽出する正規表現
    pattern = r"(?:付属品|同梱品|同梱物|セット内容|パッケージ内容)[\s\-:：『「]*([^\n。]*)"
    match = re.search(pattern, text)
    
    if match:
        items_str = match.group(1).strip()
    else:
        # 見つからない場合は全体の文字列をカンマ区切り候補としてみる
        items_str = text.strip()
        
    # 第一段階: 明らかな文章を除外する処理
    items_str = re.split(r'[。※\n]', items_str)[0]
    
    # PDF特有のノイズ（著作権表示等）が混ざった場合の強制カット
    if "Copyright" in items_str or "著作権" in items_str:
         items_str = re.split(r'Copyright|著作権', items_str)[0]
         
    # コロン等で区切られている場合の右側を取る (例: 付属品: ケーブル)
    if ":" in items_str:
        items_str = items_str.split(":", 1)[1]
    elif "：" in items_str:
        items_str = items_str.split("：", 1)[1]
    
    # 特殊な区切り文字で配列化
    items = re.split(r'[,、・/／+＋]+', items_str)
    
    result_items = []
    
    # 除外キーワード（これらを含む項目はスキップ）
    exclude_keywords = [
        "別売", "推奨", "対応", "確認", "含ま", "保証", "ご覧", 
        "お客様", "購入", "弊社", "場合", "注意", "仕様", "変更",
        "写真", "画像", "一部", "予告", "なく", "実際", "異な", "梱包", 
        "付属", "無い", "ない", "可能", "領収", "発行", "発送", "専用", "担当",
        "販売", "稼働", "倉庫", "自社", "配送", "時間", "到着", "消毒", "気軽", "動作", 
        "中古", "状態", "美品", "目立つ", "日焼け", "キズ", "汚れ", "ランク", "テスト"
    ]
    
    # 許可するキーワード（これらが含まれていたら絶対にアイテムとして扱う）
    allow_keywords = ["ケーブル", "コード", "アダプタ", "アダプター", "本体", "スタンド", "CD", "説明書", "マニュアル", "ガイド", "ネジ", "シール", "リモコン", "電池", "ベース", "カバー", "クィック", "クイック"]
    
    for item in items:
        # 余分な記号を削除
        item = item.strip(' 』」】\t\r*＊:： ')
        if not item or len(item) < 2: 
            continue
            
        # 長すぎる要素の中に不要な文章が含まれている場合は文末をカット
        item = re.sub(r'(が|は|を|も|に|で|へ|と|から).*(ます|です|ください|可能|する|した|なる|おり).*$', '', item)
        item = item.strip()
            
        # 30文字以上ある場合はいくら何でも長すぎるとみなして除外 (緩和)
        if len(item) > 30 and not any(allow in item for allow in allow_keywords):
             continue
             
        # 除外キーワードチェック
        if any(exclude in item for exclude in exclude_keywords):
            # ただし、本体やケーブル自体は除外しない
            if not any(allow == item for allow in ["ACアダプタ", "電源", "本体", "ケーブル", "コード"]):
                 continue
            
        result_items.append(item)
        
    if result_items:
        # 重複・空文字を除外
        seen = set()
        unique_items = []
        for x in result_items: # 順序保持
            if x not in seen and x:
                seen.add(x)
                unique_items.append(x)
        return ",".join(unique_items)
    return ""

test_cases = [
    "ドライバーCD(マニュアル,クイックスタートガイド含む),電源ケーブル(1.5m),HDMIケーブル(1.5m)",
    "D-subケーブル(1.5m)、DVIケーブル(1.5m)、オーディオケーブル(1.5m)",
    "電源コード 【配送】 365日稼働の自社倉庫",
    "DisplayPortケーブル(1.8m),電源コード(1.8m),ネジ(4個),シール",
    "付属品:電源ケーブル、D-SUBケーブル、オーディオケーブル、クイックスタートガイド、ドライバーCD、保証書",
    "付属品 本体、ACアダプター、電源コード",
]

for t in test_cases:
    print(f"Original: {t}")
    print(f"Cleaned : {clean_accessories(t)}")
    print("-" * 40)
