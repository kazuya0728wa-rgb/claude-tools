# ツール共有セットアップガイド（友達用）

## このシステムでできること
- 自分が作ったツールを **カード形式** で Discord に紹介
- 「📥 コードが欲しい」ボタンで **リクエストされた時だけ** GitHub に公開
- 毎朝8時に新しいツールを自動通知（通知済みは再通知しない）

---

## 1. 前提条件
- Python 3.11以上
- Discordアカウント（共有サーバーに参加済み）
- GitHubアカウント
- 自分のツールを入れるディレクトリ（例: `C:/Users/あなた/.claude/tools/`）

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

## 4. 自分のツールカタログを作成
`tool_catalog.yaml` を編集して、自分のツール情報を追加:

```yaml
tools:
  my-tool-name:
    name: "ツールの表示名"
    summary: "1行の概要"
    detail: |
      2-3行の詳細説明。
      何ができるか、どう使えるか。
    features:
      - "機能1"
      - "機能2"
      - "機能3"
    tech: "Python / Flask / etc"
    shareable: true
```

**ポイント:**
- `shareable: true` → 「コードが欲しい」ボタンが付く
- `shareable: false` → カード表示のみ（個人用ツール向け）
- `features` は3〜5個がベスト

## 5. GitHubリポジトリを準備
```bash
# 自分のGitHubにリポを作成してリモート設定
git remote set-url origin https://github.com/あなた/あなたのリポ.git
git push -u origin master
```

`.gitignore` でツールはデフォルト非公開になっています。
「コードが欲しい」ボタンが押された時だけ、そのツールが `git add -f` で個別pushされます。

## 6. start.bat を作成
`claude-monitor/start.bat` を以下の内容で作成:

```bat
@echo off
chcp 65001 >nul

rem === Discord Bot Settings ===
set CLAUDE_MONITOR_DISCORD_TOKEN=ここに自分のBotトークン
set CLAUDE_MONITOR_CHANNEL_ID=自分のモニタリング用チャンネルID
set CLAUDE_MONITOR_GUILD_ID=共有サーバーのID

rem === Tool Share Settings ===
set TOOL_SHARE_CHANNEL_ID=1486204546370899978
set TOOL_SHARE_USER_NAME=ここに自分の名前
set TOOL_SHARE_GITHUB_URL=https://github.com/あなた/あなたのリポ

cd /d "%~dp0"
python bot.py
pause
```

> ⚠️ `start.bat` は `.gitignore` に入っているのでGitHubには公開されません

## 7. 起動 & 動作確認
```bash
start.bat
```

Discordで以下のコマンドが使えます:

| コマンド | 説明 |
|---|---|
| `/catalog` | 自分の共有可能ツールをカード一覧で表示 |
| `/digest` | 今日の活動レポート（未通知のツールのみ） |
| `/tools` | 全ツール一覧（簡易表示） |

## 8. ツールの追加・更新

### 新しいツールを追加した時
1. `tool_catalog.yaml` にエントリを追加
2. 次回の `/digest` や毎朝のダイジェストで自動通知される

### 既存ツールに大きな機能を追加した時
1. `tool_catalog.yaml` の `features` や `detail` を更新
2. 内容の変更を自動検知して 🆙 バッジ付きで再通知される

### 手動で今すぐ送信したい時
```bash
python send_catalog.py        # 未通知分だけ送信
python send_catalog.py --all  # 全ツールを強制送信
```

---

## トラブルシューティング

### 「インタラクションに失敗しました」と出る
→ Botが起動していません。`start.bat` を実行してください

### ボタンを押してもGitHubにpushされない
→ `TOOL_SHARE_GITHUB_URL` が正しく設定されているか確認
→ `git remote -v` でリモートURLを確認

### 通知済みツールをリセットしたい
→ `notified_tools.json` を削除すると全ツールが「未通知」に戻ります
