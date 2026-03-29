# ツール共有システム セットアップ手順（Claude Code 実行用）

> **このファイルは友達のClaude Codeが読んで自動実行するための手順書です。**
> 友達が「このガイドに従ってツール共有をセットアップして」と指示すれば、
> Claude Code がほぼ全自動でセットアップします。

---

## 前提
- Claude Code が動作している
- Python 3.11+、Git がインストール済み
- Discordアカウントがある（共有サーバー: ID `1475066261841903650` に参加済み）
- GitHubアカウントがある
- Playwright MCP が使える（Discord Bot 作成の自動化に必要）

---

## Phase 1: リポのクローン & ファイル配置

```bash
# 1. テンプレートリポをクローン
git clone https://github.com/kazuya0728wa-rgb/claude-tools.git /tmp/claude-tools-template

# 2. tools ディレクトリを作成（なければ）
mkdir -p ~/.claude/tools

# 3. claude-monitor をコピー
cp -r /tmp/claude-tools-template/claude-monitor ~/.claude/tools/claude-monitor

# 4. friend-template の内容で上書き（クリーンなhooks・カタログ雛形）
cp -f ~/.claude/tools/claude-monitor/friend-template/hooks/* ~/.claude/tools/claude-monitor/hooks/
cp -f ~/.claude/tools/claude-monitor/friend-template/tool_catalog.yaml ~/.claude/tools/claude-monitor/tool_catalog.yaml
cp -f ~/.claude/tools/claude-monitor/friend-template/.gitignore ~/.claude/tools/

# 5. 依存インストール
pip install -r ~/.claude/tools/claude-monitor/requirements.txt

# 6. テンプレート削除
rm -rf /tmp/claude-tools-template
```

---

## Phase 2: Discord Bot 作成（Playwright で自動化）

ユーザーに以下を確認:
- 「Discordにブラウザでログインしてください。ログインできたら教えてください。」

ログイン確認後、Playwright で以下を実行:

1. `https://discord.com/developers/applications` に遷移
2. 「New Application」ボタンをクリック
3. 名前に `CC Monitor - {ユーザー名}` を入力して作成
4. 左メニュー「Bot」を開く
5. 「Reset Token」→ トークンをコピーして変数に保存
6. 「MESSAGE CONTENT INTENT」トグルを ON にして Save
7. 左メニュー「OAuth2」→「URL Generator」を開く
8. Scopes: `bot` と `applications.commands` にチェック
9. Bot Permissions: `Send Messages`, `Embed Links`, `Use Slash Commands` にチェック
10. 生成されたURLをコピー
11. そのURLに遷移して、共有サーバー（ID: `1475066261841903650`）にBotを追加

**取得すべき値:**
- `BOT_TOKEN` — Step 5 で取得
- `GUILD_ID` — `1475066261841903650`（共有サーバー、固定）
- `TOOL_SHARE_CHANNEL_ID` — `1486204546370899978`（ツール共有チャンネル、固定）

**ユーザーに確認すべき値:**
- `USER_NAME` — 「Discord上で表示する名前は何にしますか？」
- `MONITOR_CHANNEL_ID` — 「あなた専用のモニターチャンネルを作りますか？それとも既存のチャンネルIDがありますか？」
  - 新規作成の場合: Discord API (`POST /guilds/{guild_id}/channels`) で作成可能

---

## Phase 3: GitHubリポ作成

```bash
cd ~/.claude/tools

# git 初期化
git init
git add .gitignore
git commit -m "Initial commit"
```

ユーザーに確認:
- 「GitHubにツール共有用のリポジトリを作成します。リポジトリ名は何にしますか？（例: my-claude-tools）」

`gh` CLI でリポ作成:
```bash
gh repo create {リポ名} --private --source=. --remote=origin --push
```

取得した値: `GITHUB_URL` — `https://github.com/{ユーザー名}/{リポ名}`

---

## Phase 4: start.bat 生成

Phase 2, 3 で取得した値を使って `start.bat` を生成:

```bat
@echo off
chcp 65001 >nul

set CLAUDE_MONITOR_DISCORD_TOKEN={BOT_TOKEN}
set CLAUDE_MONITOR_CHANNEL_ID={MONITOR_CHANNEL_ID}
set CLAUDE_MONITOR_GUILD_ID=1475066261841903650

set TOOL_SHARE_CHANNEL_ID=1486204546370899978
set TOOL_SHARE_USER_NAME={USER_NAME}
set TOOL_SHARE_GITHUB_URL={GITHUB_URL}

cd /d "%~dp0"
python bot.py
pause
```

保存先: `~/.claude/tools/claude-monitor/start.bat`

---

## Phase 5: Claude Code フック設定

ユーザーの `~/.claude/settings.json` にフックを追加。
**既存の設定がある場合はマージすること（上書き厳禁）。**

追加するフック:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/tools/claude-monitor/hooks/pre_tool.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/tools/claude-monitor/hooks/post_tool.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/tools/claude-monitor/hooks/on_stop.py"
          }
        ]
      }
    ]
  }
}
```

> Windows の場合、パスは `C:/Users/{ユーザー名}/.claude/tools/claude-monitor/hooks/xxx.py` の形式に変換すること。

---

## Phase 6: ツールカタログ作成

ユーザーに確認:
- 「共有したいツールはありますか？ツール名と簡単な説明を教えてください。」
- 回答をもとに `~/.claude/tools/claude-monitor/tool_catalog.yaml` を生成

カタログのフォーマット:
```yaml
tools:
  {tool-dir-name}:
    name: "表示名"
    summary: "1行の概要"
    detail: |
      2-3行の詳細説明。
    features:
      - "機能1"
      - "機能2"
      - "機能3"
    tech: "使用技術"
    shareable: true
```

ツールディレクトリを `.gitignore` にも追加:
```
{tool-dir-name}/
```

---

## Phase 7: 起動 & 動作確認

```bash
cd ~/.claude/tools/claude-monitor
# Windows: start.batを実行
# それ以外:
python bot.py
```

確認事項:
1. `curl http://127.0.0.1:19876/health` が `{"status": "running"}` を返すか
2. Discordで `/catalog` コマンドが動作するか
3. カードが「ツール共有」チャンネルに表示されるか

---

## ユーザーへの最終報告

セットアップ完了後、以下を伝える:

- Bot名: `CC Monitor - {ユーザー名}`
- 使えるコマンド: `/catalog`, `/digest`, `/tools`
- ツール追加方法: `tool_catalog.yaml` を編集 → `/digest` で通知
- Bot起動方法: `start.bat` を実行
- 「コードが欲しい」ボタン: Bot起動中のみ動作
