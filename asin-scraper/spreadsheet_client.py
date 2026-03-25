import gspread
from google.oauth2.service_account import Credentials
import config

class SpreadsheetClient:
    def __init__(self, credentials_path=config.CREDENTIALS_FILE, spreadsheet_id=config.SPREADSHEET_ID):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        
        try:
            self.client = self._authenticate()
            self.sheet = self.client.open_by_key(self.spreadsheet_id).worksheet(config.SHEET_NAME)
        except Exception as e:
            print(f"Error: スプレッドシートの初期設定に失敗しました: {e}")
            raise

    def _authenticate(self):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes)
            return gspread.authorize(credentials)
        except FileNotFoundError:
            print(f"Warning: 認証ファイル '{self.credentials_path}' が見つかりません。")
            raise

    def get_all_records(self):
        """シート全体のデータを取得する(セルの位置情報とセットで扱うため、get_all_values を使用)"""
        return self.sheet.get_all_values()

    def update_cells(self, updates):
        """
        updates: list of dict 
        形式: [{'range': 'Sheet1!A1:B2', 'values': [['A1', 'B1'], ['A2', 'B2']]}]
        バッチ更新を行う
        """
        if not updates:
            return
        
        self.sheet.batch_update(updates)
