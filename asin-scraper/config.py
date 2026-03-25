import os

# Google Sheets API 設定
CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '1ZUZ-WBD-4XrwKaPgKOTwnIcm4LvUyKjQrkbrvWLNbNE')
SHEET_NAME = '商品リスト'

# 列インデックス (1始まり)
COL_ASIN = 10      # J列
COL_ALT_URL = 54   # BB列（ヨドバシ/ビックカメラURL）
COL_ACCESSORY = 55 # BC列
COL_URL = 56       # BD列（AmazonページURL）
START_ROW = 2      # 2行目以降から処理
END_ROW = 10       # テスト: 10行目まで
