"""Gmail送信ツール設定"""

import os

BASE_DIR = os.path.dirname(__file__)
TOKENS_DIR = os.path.join(BASE_DIR, "tokens")

CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")

DEFAULT_FROM = "hemitesuto482@gmail.com"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]


def get_token_file(email: str) -> str:
    name = email.split("@")[0]
    return os.path.join(TOKENS_DIR, f"{name}.json")
