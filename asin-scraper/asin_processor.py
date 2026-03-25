import re

def is_valid_asin(asin: str) -> bool:
    """ASINが有効な形式（10文字の英数字）か判定する"""
    if not asin or not isinstance(asin, str):
        return False
    # ASINは通常10文字の英数字
    return bool(re.fullmatch(r'^[B0-9][A-Z0-9]{9}$', asin.strip().upper()))

def should_process_row(asin: str, accessory_val: str, url_val: str) -> bool:
    """
    その行が処理対象かどうかを判定する
    - BC列(付属品)が空欄、かつ BD列(根拠URL)が空欄
    - J列(ASIN)が有効な形式であること
    """
    # BC, BDのどちらかに値が存在すれば上書きしないためスキップ
    if accessory_val.strip() or url_val.strip():
        return False
    
    # ASINが有効かチェック (空欄含む不正なものはスキップ)
    if not is_valid_asin(asin):
        return False
        
    return True
