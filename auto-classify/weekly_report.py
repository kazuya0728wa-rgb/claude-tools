"""
週次ファイル分類レポートをメールで送信
毎週月曜 9:05 にタスクスケジューラから実行
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# ==============================
# 設定
# ==============================
GMAIL_ADDRESS    = "kazuya0728wa@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
LOG_PATH    = r"C:\Users\kazuy\Projects\auto-classify\classify.log"
DOWNLOADS   = r"C:\Users\kazuy\Downloads"

CATEGORY_ORDER = ["大学", "物販", "削除予定", "就活", "インターン", "OneDrive\\その他", "その他"]

# ==============================
# ログ解析（過去7日分）
# ==============================
def parse_weekly_log():
    since = datetime.now() - timedelta(days=7)
    sessions = []
    current = None

    try:
        with open(LOG_PATH, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ts = datetime.strptime(line[1:17], "%Y-%m-%d %H:%M")
                except Exception:
                    continue
                if ts < since:
                    continue

                msg = line[20:].strip()

                if "=== 分類開始" in msg:
                    current = {"time": ts, "moves": [], "skipped": 0}
                    try:
                        current["skipped_total"] = int(msg.split("(")[1].split("件")[0])
                    except Exception:
                        pass
                elif msg.startswith("移動:") and current is not None:
                    current["moves"].append(msg[3:].strip())
                elif "=== 完了" in msg and current is not None:
                    try:
                        current["skipped"] = int(msg.split("未分類")[1].strip().split("（")[0].split()[-1].replace("件",""))
                    except Exception:
                        pass
                    sessions.append(current)
                    current = None
    except FileNotFoundError:
        pass

    return sessions

# ==============================
# カテゴリ判定（移動先パスの先頭フォルダ）
# ==============================
def get_category(dest: str) -> str:
    parts = dest.strip().split("\\")
    # "OneDrive\大学\..." → "大学"
    # "Downloads\_削除予定\..." → "削除予定"
    for i, p in enumerate(parts):
        if p in ("OneDrive", "Downloads"):
            if i + 1 < len(parts):
                sub = parts[i + 1]
                return sub.lstrip("_")
        if p.startswith("_"):
            return p.lstrip("_")
    return parts[-1] if parts else "不明"

# ==============================
# Downloadsに残っているファイル一覧
# ==============================
def get_remaining_files():
    dl = Path(DOWNLOADS)
    if not dl.exists():
        return []
    return sorted(
        f.name for f in dl.iterdir()
        if f.is_file() and f.name != "desktop.ini"
    )

# ==============================
# レポート本文を生成
# ==============================
def build_report(sessions):
    now   = datetime.now()
    since = now - timedelta(days=7)

    total_moved   = sum(len(s["moves"]) for s in sessions)
    total_skipped = sum(s.get("skipped", 0) for s in sessions)
    remaining     = get_remaining_files()

    # カテゴリ別集計
    cat_count = defaultdict(int)
    for s in sessions:
        for move in s["moves"]:
            if "→" in move:
                dest = move.split("→")[1].strip()
                cat  = get_category(dest)
                cat_count[cat] += 1

    # 日別集計
    day_count = defaultdict(int)
    for s in sessions:
        key = s["time"].strftime("%m/%d(%a)")
        day_count[key] += len(s["moves"])

    lines = []
    lines.append(f"【週次ファイル分類レポート】")
    lines.append(f"期間: {since.strftime('%Y/%m/%d')} 〜 {now.strftime('%Y/%m/%d')}")
    lines.append("")

    # ── サマリー ──
    lines.append("■ サマリー")
    lines.append(f"  実行: {len(sessions)}回  |  移動: {total_moved}件  |  未分類(残り): {len(remaining)}件")
    lines.append("")

    # ── カテゴリ別 ──
    lines.append("■ カテゴリ別移動件数")
    all_cats = set(cat_count.keys())
    ordered  = [c for c in CATEGORY_ORDER if c in all_cats] + \
               [c for c in all_cats if c not in CATEGORY_ORDER]
    if ordered:
        max_len = max(len(c) for c in ordered)
        for cat in ordered:
            lines.append(f"  {cat:<{max_len}}  {cat_count[cat]:>3}件")
    else:
        lines.append("  (移動なし)")
    lines.append("")

    # ── 要確認 ──
    lines.append("■ 要確認（Downloadsに残っているファイル）")
    if remaining:
        for name in remaining:
            lines.append(f"  ・{name}")
    else:
        lines.append("  なし（すべて分類済み）")
    lines.append("")

    # ── 日別ログ ──
    lines.append("■ 日別ログ")
    if day_count:
        for day, count in sorted(day_count.items()):
            lines.append(f"  {day}  移動 {count}件")
    else:
        lines.append("  (実行なし)")
    lines.append("")

    lines.append("─" * 44)
    lines.append(f"ログ: {LOG_PATH}")

    return "\n".join(lines)

# ==============================
# メール送信
# ==============================
def send_report():
    if not GMAIL_APP_PASSWORD:
        print("ERROR: 環境変数 GMAIL_APP_PASSWORD が未設定です")
        return

    sessions = parse_weekly_log()
    body     = build_report(sessions)
    subject  = f"[自動分類] 週次レポート {datetime.now().strftime('%Y/%m/%d')}"

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = GMAIL_ADDRESS
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f"送信完了: {subject}")
    except Exception as e:
        print(f"送信失敗: {e}")

if __name__ == "__main__":
    send_report()
