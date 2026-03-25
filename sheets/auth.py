"""
OAuth2 認証モジュール

使い方:
  # 初回認証（ブラウザが起動します）
  python auth.py

  # 他スクリプトからの利用
  from auth import get_credentials, build_service
  service = build_service("sheets", "v4")
"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# パスを通す
sys.path.insert(0, os.path.dirname(__file__))
from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES


def get_credentials() -> Credentials:
    """
    認証情報を取得する。
    - token.json が存在し有効 → そのまま返す
    - 期限切れでリフレッシュトークンあり → サイレントリフレッシュ
    - token.json なし → ブラウザで OAuth フローを起動
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # リフレッシュ失敗 → 再認証
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"[ERROR] credentials.json が見つかりません: {CREDENTIALS_FILE}")
                print()
                print("セットアップ手順:")
                print("1. https://console.cloud.google.com/ でGCPプロジェクトを作成")
                print("2. Google Sheets API と Apps Script API を有効化")
                print("3. OAuth2クライアントID（デスクトップアプリ）を作成してJSONをダウンロード")
                print(f"4. ダウンロードしたファイルを以下に配置: {CREDENTIALS_FILE}")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # token.json に保存
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"[OK] 認証完了。token.json を保存しました: {TOKEN_FILE}")

    return creds


def build_service(api_name: str, version: str):
    """汎用 API サービスビルダー"""
    creds = get_credentials()
    return build(api_name, version, credentials=creds)


if __name__ == "__main__":
    print("Google API 認証を開始します...")
    creds = get_credentials()
    print("[OK] 認証成功！")
    print(f"  有効期限: {creds.expiry}")
