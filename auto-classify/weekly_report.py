"""
週次ファイル分類レポートをDiscordに送信
毎週月曜 9:05 にタスクスケジューラから実行
"""
import os
import sys
import time
import socket
import logging
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# ── ログ設定 ─────────────────────────────────────────────────
_LOG_FILE = Path(r"C:\Users\kazuy\.claude\tools\auto-classify\weekly_report.log")
logging.basicConfig(
    filename=str(_LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
_logger = logging.getLogger(__name__)

# ── 設定 ────────────────────────────────────────────────────
LOG_PATH  = r"C:\Users\kazuy\.claude\tools\auto-classify\classify.log"
DOWNLOADS = r"C:\Users\kazuy\Downloads"
CATEGORY_ORDER = ["大学", "物販", "削除予定", "就活", "インターン", "OneDrive\\その他", "その他"]

# Discord は2000文字制限があるため複数メッセージに分割して送る
DISCORD_MAX = 1900


def _get_webhook_url() -> str:
    try:
        creds = json.loads(
            (Path.home() / ".claude/credentials/services/discord.json").read_text()
        )["credentials"]
        return creds.get("TOOL_NOTIFY_WEBHOOK_URL", "")
    except Exception:
        return ""


def _send_discord(content: str):
    url = _get_webhook_url()
    if not url:
        _logger.warning("TOOL_NOTIFY_WEBHOOK_URL が未設定")
        return
    # 2000文字制限で分割
    chunks = [content[i:i+DISCORD_MAX] for i in range(0, len(content), DISCORD_MAX)]
    for chunk in chunks:
        data = json.dumps({"content": chunk, "username": "ツール自動通知"}).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "User-Agent": "DiscordBot"},
            method="POST"
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            _logger.warning(f"Discord通知失敗: {e}")


def _wait_for_network(timeout=60):
    """スリープ解除直後のネットワーク未接続を最大 timeout 秒待機"""
    for _ in range(timeout // 5):
        try:
            socket.setdefaulttimeout(5)
            socket.getaddrinfo("discord.com", 443)
            return True
        except OSError:
            time.sleep(5)
    return False


# ── ログ解析（過去7日分）─────────────────────────────────────
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


def get_category(dest: str) -> str:
    parts = dest.strip().split("\\")
    for i, p in enumerate(parts):
        if p in ("OneDrive", "Downloads"):
            if i + 1 < len(parts):
                return parts[i + 1].lstrip("_")
        if p.startswith("_"):
            return p.lstrip("_")
    return parts[-1] if parts else "不明"


def get_remaining_files():
    dl = Path(DOWNLOADS)
    if not dl.exists():
        return []
    return sorted(f.name for f in dl.iterdir() if f.is_file() and f.name != "desktop.ini")


# ── レポート本文生成（Discord向け）───────────────────────────
def build_report(sessions) -> str:
    now   = datetime.now()
    since = now - timedelta(days=7)

    total_moved = sum(len(s["moves"]) for s in sessions)
    remaining   = get_remaining_files()

    cat_count = defaultdict(int)
    for s in sessions:
        for move in s["moves"]:
            if "→" in move:
                cat_count[get_category(move.split("→")[1].strip())] += 1

    day_moves = defaultdict(list)
    for s in sessions:
        key = s["time"].strftime("%m/%d(%a)")
        day_moves[key].extend(s["moves"])

    lines = []
    if not sessions:
        lines.append("⚠️ **DownloadAutoClassifyが1週間実行されていません**（classify.logに過去7日の実行記録なし）")
        lines.append("")
    lines.append(f"📊 **週次ファイル分類レポート** {now.strftime('%Y/%m/%d')}")
    lines.append(f"期間: {since.strftime('%m/%d')} 〜 {now.strftime('%m/%d')}")
    lines.append("")

    # サマリー
    lines.append("**■ サマリー**")
    lines.append(f"実行 {len(sessions)}回　移動 {total_moved}件　Downloads残り {len(remaining)}件")
    lines.append("")

    # カテゴリ別
    lines.append("**■ カテゴリ別移動**")
    ordered = [c for c in CATEGORY_ORDER if c in cat_count] + \
              [c for c in cat_count if c not in CATEGORY_ORDER]
    if ordered:
        for cat in ordered:
            lines.append(f"　{cat}：{cat_count[cat]}件")
    else:
        lines.append("　移動なし")
    lines.append("")

    # 日別ログ（移動ファイル名を列挙）
    lines.append("**■ 日別ログ**")
    if day_moves:
        for day in sorted(day_moves):
            moves = day_moves[day]
            lines.append(f"　**{day}**　{len(moves)}件")
            for m in moves:
                lines.append(f"　　・{m}")
    else:
        lines.append("　実行なし")
    lines.append("")

    # Downloads残りファイル
    lines.append("**■ Downloads残りファイル**")
    if remaining:
        for name in remaining:
            lines.append(f"　・{name}")
    else:
        lines.append("　なし（すべて分類済み）")

    return "\n".join(lines)


# ── メイン ───────────────────────────────────────────────────
def send_report():
    _logger.info("=== 週次レポート開始 ===")

    if not _wait_for_network():
        _logger.error("ネットワーク接続タイムアウト（60秒）")
        _send_discord("❌ **WeeklyClassifyReport 失敗**：ネットワーク接続タイムアウト")
        sys.exit(1)

    sessions = parse_weekly_log()
    body     = build_report(sessions)

    _send_discord(body)
    _logger.info(f"Discord送信完了 ({len(body)}文字)")
    print(f"送信完了 ({len(body)}文字)")


if __name__ == "__main__":
    send_report()
