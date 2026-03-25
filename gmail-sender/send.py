"""
Gmail送信スクリプト

使い方:
  python send.py --to user@example.com --subject "件名" --body "本文"
  python send.py --from kazuya0728wa@gmail.com --to user@example.com --subject "件名" --body "本文"
"""

import argparse
import base64
import sys
import os
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(__file__))
from config import DEFAULT_FROM
from auth import build_gmail_service


def send_email(from_email: str, to: str, subject: str, body: str) -> dict:
    service = build_gmail_service(from_email)

    message = MIMEText(body, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    return result


def main():
    parser = argparse.ArgumentParser(description="Gmail送信ツール")
    parser.add_argument("--from", dest="from_email", default=DEFAULT_FROM, help="送信元メールアドレス")
    parser.add_argument("--to", required=True, help="宛先メールアドレス")
    parser.add_argument("--subject", required=True, help="件名")
    parser.add_argument("--body", required=True, help="本文")
    args = parser.parse_args()

    result = send_email(args.from_email, args.to, args.subject, args.body)
    print(f"[OK] 送信完了！ ({args.from_email} → {args.to}) Message ID: {result['id']}")


if __name__ == "__main__":
    main()
