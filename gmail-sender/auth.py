"""Gmail OAuth2 認証モジュール"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

sys.path.insert(0, os.path.dirname(__file__))
from config import CREDENTIALS_FILE, SCOPES, DEFAULT_FROM, get_token_file, TOKENS_DIR


def get_credentials(email: str = DEFAULT_FROM) -> Credentials:
    token_file = get_token_file(email)
    os.makedirs(TOKENS_DIR, exist_ok=True)
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"[ERROR] credentials.json が見つかりません: {CREDENTIALS_FILE}")
                sys.exit(1)

            print(f"[INFO] {email} でログインしてください")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "w") as f:
            f.write(creds.to_json())
        print(f"[OK] 認証完了。トークンを保存しました: {token_file}")

    return creds


def build_gmail_service(email: str = DEFAULT_FROM):
    creds = get_credentials(email)
    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FROM
    print(f"Gmail API 認証を開始します... ({email})")
    creds = get_credentials(email)
    print("[OK] 認証成功！")
    print(f"  有効期限: {creds.expiry}")
