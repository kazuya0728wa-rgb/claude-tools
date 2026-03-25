import re

def clean_accessories(text: str) -> str:
    # 簡易的にHTMLタグを改行に置換
    text = re.sub(r'<[^>]+>', '\n', text)
    
    # 付属品・同梱物・同梱品・セット内容 に続く文字列を抽出する正規表現
    pattern = r"(?:付属品|同梱品|同梱物|セット内容|パッケージ内容)[\s\-:：『「【]*([^\n。]*)"
    match = re.search(pattern, text)
    
    if match:
        items_str = match.group(1).strip()
    else:
        # 見つからない場合は全体の文字列をカンマ区切り候補としてみる（Amazonなどの直書きの場合）
        items_str = text.strip()
        
    # 第一段階: 明らかな文章を除外する処理
    # 文の終了や補足説明の開始を示す文字で区切る
    items_str = re.split(r'[。※\n]', items_str)[0]
    
    # 特殊な区切り文字で配列化
    items = re.split(r'[,、・/／+＋]+', items_str)
    
    result_items = []
    
    # 除外キーワード（これらを含む項目はスキップ）
    exclude_keywords = [
        "別売", "推奨", "対応", "確認", "含ま", "保証", "ご覧", 
        "お客様", "購入", "弊社", "場合", "注意", "仕様", "変更",
        "写真", "画像", "一部", "予告", "なく", "実際", "異な", "梱包", 
        "付属", "無い", "ない", "可能", "領収", "発行", "発送", "専用", "担当"
    ]
    
    # 許可するキーワード（これらが含まれていたら絶対にアイテムとして扱う）
    allow_keywords = ["ケーブル", "コード", "アダプタ", "本体", "スタンド", "CD", "説明書", "マニュアル", "ガイド", "ネジ"]
    
    for item in items:
        # 余分な記号を削除（カッコは残すように変更）
        item = item.strip(' 』」】\t\r*＊')
        if not item or len(item) < 2: 
            continue
            
        # 長すぎる要素の中に不要な文章が含まれている場合は文末をカット
        # 例：「HDMIケーブル(1.5m)が入っています」 -> 「HDMIケーブル(1.5m)」
        item = re.sub(r'(が|は|を|も|に|で|へ|と|から).*(ます|です|ください|可能|する|した|なる).*$', '', item)
        item = item.strip()
            
        # 15文字以上ある場合かつ、許可キーワードが含まれていない場合は説明文とみなす
        if len(item) > 15 and not any(allow in item for allow in allow_keywords):
             continue
             
        # 除外キーワードチェック
        if any(exclude in item for exclude in exclude_keywords):
            # ただし、本体やケーブル自体は除外しない
            if not any(allow == item for allow in ["ACアダプター", "電源コード", "本体のみ"]):
                 continue
            
        result_items.append(item)
        
    if result_items:
        return ",".join(result_items)
    return ""

test_cases = [
    "電源コード (約1.5m), 映像ケーブル (約1.5m) ※365日専任の担当者により厳重に梱包されます",
    "ドライバーCD(マニュアル,クイックスタートガイド含む),保証書,電源ケーブル(1.5m),HDMIケーブル(1.5m)",
    "動作確認済み",
    "本体のみ",
    "画像に写っているものが全てです",
    "DisplayPortケーブル (1.8m)",
    "写真をご参照ください 法人のため領収書発行可能です",
    "付属品,または本体のみ",
    "【パッケージ内容】モニター本体、電源ケーブル(約1.5m)、HDMIケーブル(約1.5m)、保証書",
    "電源コード",
    "D-subケーブル(1.5m)、DVIケーブル(1.5m)、オーディオケーブル(1.5m)",
]

for t in test_cases:
    print(f"Original: {t}")
    print(f"Cleaned : {clean_accessories(t)}")
    print("-" * 40)
