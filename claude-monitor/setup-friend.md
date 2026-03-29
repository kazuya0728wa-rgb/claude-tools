# ツール共有セットアップガイド（Claude Code ユーザー向け）

## 概要
このシステムで、自分が作ったツールをDiscordでカード形式で紹介できます。
「📥 コードが欲しい」ボタンでリクエストされた時だけGitHubに公開されます。

**全員がClaude Codeを使う前提の構成です。**

```
あなたのPC
├── .claude/tools/           ← あなたのツール置き場
│   ├── claude-monitor/      ← Discord Bot（ここをセットアップ）
│   │   ├── bot.py           ← メインBot
│   │   ├── hooks/           ← Claude Code フック
│   │   ├── tool_catalog.yaml← あなたのツールカタログ
│   │   └── start.bat        ← 起動用（自分で作る）
│   ├── your-tool-1/         ← あなたのツール
│   └── your-tool-2/
│
└── Discord 共有サーバー
    ├── #ツール共有           ← 全員のカタログが投稿される
    └── #あなた用モニター      ← あなた専用の作業通知
```

---

## Step 1: 前提条件
- Claude Code が使える状態
- Python 3.11+
- Git
- Discordアカウント（共有サーバーに参加済み）
- GitHubアカウント

## Step 2: Discord Bot を作成
1. https://discord.com/developers/applications → 「New Application」
2. 名前: `CC Monitor - あなたの名前`
3. 「Bot」→「Reset Token」→ **トークンをコピー**（後で使う）
4. 「Bot」→「MESSAGE CONTENT INTENT」を **ON**
5. 「OAuth2」→「URL Generator」
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
6. 生成されたURLをブラウザで開き、**共有サーバーに追加**

## Step 3: フォルダ構成を作る

Claude Code に以下を指示してください:

```
かずやの claude-tools リポから claude-monitor をクローンして、
自分の .claude/tools/ にセットアップして。
テンプレートは friend-template/ にある。

リポ: https://github.com/kazuya0728wa-rgb/claude-tools
```

**Claude Code がやってくれること:**
1. リポをクローン
2. `claude-monitor/` を `~/.claude/tools/` にコピー
3. `friend-template/` の内容（クリーンなhooks・カタログ雛形）で上書き
4. `pip install -r requirements.txt`

## Step 4: 自分のGitHubリポを準備

```bash
cd ~/.claude/tools
git init
git remote add origin https://github.com/あなた/あなたのリポ.git
```

`.gitignore` は `friend-template/` に入っているものを使ってください。
自分のツールディレクトリを `.gitignore` に追加:

```gitignore
# 自分のツール（デフォルト非公開）
my-tool-1/
my-tool-2/
```

## Step 5: start.bat を設定

`claude-monitor/start.bat` を編集:

| 変数 | 値 |
|---|---|
| `CLAUDE_MONITOR_DISCORD_TOKEN` | Step 2 でコピーしたBotトークン |
| `CLAUDE_MONITOR_CHANNEL_ID` | あなた専用のモニターチャンネルID |
| `CLAUDE_MONITOR_GUILD_ID` | 共有サーバーのID |
| `TOOL_SHARE_CHANNEL_ID` | `1486204546370899978`（共有チャンネル・全員共通） |
| `TOOL_SHARE_USER_NAME` | あなたの名前 |
| `TOOL_SHARE_GITHUB_URL` | あなたのGitHubリポURL |

> start.bat は .gitignore に入っているのでGitHubに公開されません

## Step 6: Claude Code のフックを設定

Claude Code の設定ファイル `~/.claude/settings.json` に以下を追加:

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

## Step 7: ツールカタログを作成

`claude-monitor/tool_catalog.yaml` を編集して自分のツールを登録:

```yaml
tools:
  my-awesome-tool:
    name: "すごいツール"
    summary: "1行で何ができるか"
    detail: |
      2-3行の詳細。何が便利か、
      どう使うか。
    features:
      - "機能A"
      - "機能B"
      - "機能C"
    tech: "Python / Flask"
    shareable: true
```

## Step 8: 起動 & 確認

```bash
# Bot起動
cd ~/.claude/tools/claude-monitor
start.bat
```

Discordで確認:
- `/catalog` → 自分のツールカタログをカード表示
- `/digest` → 未通知ツールのみ送信
- `/tools` → 全ツール一覧

---

## 日常の使い方

### 新しいツールを作った時
1. `tool_catalog.yaml` にエントリ追加
2. `/digest` で手動送信 or 毎朝8時に自動通知

### ツールに大きな機能追加した時
1. `tool_catalog.yaml` の `features` / `detail` を更新
2. 変更を自動検知 → 🆙 バッジ付きで再通知

### 「コードが欲しい」と言われた時
→ ボタンが自動処理（git add -f → push → GitHubリンク返信）

---

## トラブルシューティング

| 問題 | 対処 |
|---|---|
| 「インタラクションに失敗しました」 | Botが起動していない → `start.bat` を実行 |
| ボタンでpush失敗 | `TOOL_SHARE_GITHUB_URL` を確認 / `git remote -v` を確認 |
| 通知履歴をリセットしたい | `notified_tools.json` を削除 |
| カタログが反映されない | Bot再起動（カタログはキャッシュされる） |
