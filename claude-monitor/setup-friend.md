# ツール共有セットアップガイド（友達用）

## 1. 前提条件
- Python 3.11以上
- Discordアカウント
- GitHubアカウント

## 2. Discordボットを作成
1. https://discord.com/developers/applications にアクセス
2. 「New Application」→ 名前を入力（例: `CC Monitor - ○○`）
3. 「Bot」→「Reset Token」→ トークンをコピー
4. 「Bot」→「MESSAGE CONTENT INTENT」をON
5. 「OAuth2」→「URL Generator」→ `bot` + `applications.commands` にチェック
6. 権限: `Send Messages`, `Embed Links`, `Use Slash Commands`
7. 生成されたURLをブラウザで開き、共有サーバーに追加

## 3. リポジトリをクローン
```bash
git clone https://github.com/kazuya0728wa-rgb/claude-tools.git
cd claude-tools/claude-monitor
pip install -r requirements.txt
```

## 4. start.bat を作成
`claude-monitor/start.bat` を以下の内容で作成：

```bat
@echo off
chcp 65001 >/dev/null

rem === Discord Bot Settings ===
set CLAUDE_MONITOR_DISCORD_TOKEN=ここに自分のBotトークン
set CLAUDE_MONITOR_CHANNEL_ID=自分のモニタリング用チャンネルID
set CLAUDE_MONITOR_GUILD_ID=共有サーバーのID

rem === Tool Share Settings ===
set TOOL_SHARE_CHANNEL_ID=1486204546370899978
set TOOL_SHARE_USER_NAME=ここに自分の名前
set TOOL_SHARE_GITHUB_URL=ここに自分のGitHubリポジトリURL

cd /d "%~dp0"
python bot.py
pause
```

## 5. tool_tracker.py にツール説明を追加
`tool_tracker.py` の `TOOL_DESCRIPTIONS` に自分のツール情報を追記。

## 6. 起動
```bash
start.bat
```

毎朝8時に「ツール共有」チャンネルに自動で活動レポートが投稿されます。
