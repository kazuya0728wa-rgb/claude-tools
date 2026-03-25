# 稼働管理システム（稼働管理表_3Link）

秘書×クライアントの多対多に対応した稼働管理 Web アプリ + スプレッドシート構成。

## リンク

| 種別 | URL / ID |
|------|---------|
| スプレッドシート | https://docs.google.com/spreadsheets/d/1G0A5-vW8zpYwzfga6SUgroJYMNCzeQtKwg3dD-wrxVo/edit |
| Web アプリ | https://script.google.com/macros/s/AKfycbwzwxJrOOg81CbHGm8SCMcRfoEvFXGC32SQNBbpoqPa7Q78ojX0AgGKt3m9n1L2yTJCTQ/exec |
| GAS スクリプト ID | `18_S87UdmAsobMfOfcJbZYUdA5KcM4kBv_L0xZiJck5-AGlWW7xw4uxVk` |

---

## ファイル構成

```
gas_upload/
├── コード.js       # GAS サーバーサイドロジック
├── フォーム.html   # Web アプリ UI（HTML + CSS + JS）
├── content.json    # GAS push 用パッケージ（appsscript.json + コード + HTML）
└── README.md       # このファイル
```

---

## シート構成

| シート名 | 役割 |
|---------|------|
| 担当マスター | 秘書↔クライアントの対応表（管理者が直接編集） |
| 稼働記録 | 全稼働ログ（全秘書・全クライアント） |
| 秘書別サマリー | 秘書×月×クライアント集計 |
| クライアント別サマリー | クライアント×月×秘書集計 |

### 担当マスター 列構成（ヘッダー行: 3行目, データ開始: 4行目）

| 列 | 内容 |
|----|------|
| A | 秘書名 |
| B | メールアドレス |
| C | クライアント名 |

1行 = 1対応関係。複数クライアントは複数行で表現。

### 稼働記録 列構成（ヘッダー行: 3行目, データ開始: 4行目）

| 列 | 内容 | 備考 |
|----|------|------|
| A | 日付 | `yyyy/MM/dd` |
| B | 秘書名 | |
| C | クライアント名 | |
| D | 開始時刻 | `HH:mm` テキスト形式 |
| E | 終了時刻 | `HH:mm` テキスト形式 |
| F | 稼働時間 | `=IF(AND(D<>"",E<>""),E-D,"")` `[h]:mm` 表示 |
| G | 作業内容 | 稼働開始時に入力（任意） |
| H | 備考 | 稼働終了時に入力（任意） |

---

## GAS 関数一覧

| 関数名 | 呼び出し元 | 処理内容 |
|--------|----------|---------|
| `doGet()` | Web アクセス | HTML フォームを返す |
| `getMyClients()` | `google.script.run` | ログインユーザーの担当クライアント一覧を返す |
| `getCurrentWorking()` | `google.script.run` | 現在稼働中のレコードを返す（終了時刻が空のもの） |
| `startWork(clientName, memo)` | `google.script.run` | 稼働開始（既存稼働があれば自動終了） |
| `endWork(clientName, note)` | `google.script.run` | 稼働終了 |
| `onOpen()` | スプレッドシート起動時 | カスタムメニュー「管理メニュー」追加 |
| `updateSummaries()` | 管理メニュー | 秘書別・クライアント別サマリーを更新 |
| `formatRecordSheet()` | 管理メニュー | 稼働記録シートの書式を整える |

---

## デプロイ設定（重要）

`content.json` 内 `appsscript.json` の設定：

```json
"executeAs": "USER_ACCESSING",
"access": "ANYONE"
```

**`USER_ACCESSING` が必須。** `USER_DEPLOYING` にすると `Session.getActiveUser().getEmail()` が空文字を返し、全ユーザーに「担当クライアントなし」と表示される。

---

## よくある変更手順

### 秘書・クライアントの担当を追加する

担当マスターシートの4行目以降に1行追加する：
```
A列: 秘書名（例: 田中花子）
B列: メールアドレス（例: hanako@gmail.com）
C列: クライアント名（例: 株式会社D）
```

### GAS コードを更新してデプロイする

1. `コード.js` または `フォーム.html` を編集
2. `content.json` の対応する `source` フィールドを更新
3. プッシュ：
   ```bash
   cd C:\Users\kazuy\.claude\tools\sheets
   python gas_ops.py --script-id 18_S87UdmAsobMfOfcJbZYUdA5KcM4kBv_L0xZiJck5-AGlWW7xw4uxVk push --json gas_upload/content.json
   ```
4. GAS エディタでデプロイ → 新しいバージョンを選択して「デプロイ」

または個別ファイルのみ更新：
```bash
python gas_ops.py update --file "コード" --code "$(cat gas_upload/コード.js)"
python gas_ops.py update --file "フォーム" --code "$(cat gas_upload/フォーム.html)"
```

### サマリーを手動更新する

スプレッドシートのカスタムメニュー「⚙️ 管理メニュー」→「サマリーを更新」

対象月を変更する場合は、各サマリーシートの **B3セル** に `yyyy/MM` 形式で入力（空欄 = 全期間）。

---

## 初回利用時の注意（OAuth 認証）

Web アプリを初めて開いたユーザーは OAuth 認証が必要：
1. アプリを開く
2. 「このアプリは Google によって確認されていません」画面が出る場合、「詳細」→「〜に移動（安全ではないページ）」をクリック
3. 権限を確認して「続行」
4. 以降は認証不要

---

## config.py との関係

`C:\Users\kazuy\.claude\tools\sheets\config.py` のデフォルト値は別の（日報）スプレッドシートを指している。
gas_upload 操作時は `--script-id` を明示するか、config.py の `GAS_SCRIPT_ID` を書き換える。
