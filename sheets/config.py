"""
Google Sheets / Apps Script API 設定定数

セットアップ後:
  - GAS_SCRIPT_ID: GASエディタのURLから取得して記入
    例) https://script.google.com/home/projects/{SCRIPT_ID}/edit
"""

# =====================================================
# ★ 稼働管理表_3Link（現在の開発対象）
# =====================================================
SPREADSHEET_ID = "1G0A5-vW8zpYwzfga6SUgroJYMNCzeQtKwg3dD-wrxVo"
GAS_SCRIPT_ID  = "18_S87UdmAsobMfOfcJbZYUdA5KcM4kBv_L0xZiJck5-AGlWW7xw4uxVk"

# =====================================================
# 日報提出&ランキングシート（別プロジェクト）
# =====================================================
# SPREADSHEET_ID = "10yS2-QGAd-tjZEtUdAQM6Fan18sXcsjwin5ujmpskPE"
# GAS_SCRIPT_ID  = "1-IFmw7Q5t2r9Bs5KQ_FdOCgYoqoj1u5eawkEjaV9qQ00bW8BNZd_XOEx"

# =====================================================
# コピーシート（バックアップ用・参照のみ）
# =====================================================
# SPREADSHEET_ID = "1s4nuFj76hkX0Qg16WFSHuBPO_eqdhHOEpJPDk49oM_0"
# GAS_SCRIPT_ID  = "18aqkXKNTT4A47w89o-K5uKQo4MNTBjUYD-Or9JJgDSf9uvpaN2Z_mVzf"

CREDENTIALS_FILE = r"C:\Users\kazuy\.claude\tools\sheets\credentials.json"
TOKEN_FILE = r"C:\Users\kazuy\.claude\tools\sheets\token.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
    "https://www.googleapis.com/auth/drive.readonly",
]
