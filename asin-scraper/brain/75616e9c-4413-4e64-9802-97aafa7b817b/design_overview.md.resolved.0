# Amazon ASIN 付属品調査ツール 設計概要

## 概要

Googleスプレッドシートに記載されたAmazon商品のASINに対して、
商品ページをスクレイピングし、Gemini AIを使って付属品リストを自動抽出・書き込みするツール。

---

## ファイル構成

```
antigravity/
├── main.py               # エントリーポイント。全体の処理フローを制御
├── config.py             # 設定（列番号・シート名・行範囲など）
├── spreadsheet_client.py # Google Sheetsの認証・読み書きを担当
├── asin_processor.py     # ASINのバリデーションと処理対象判定
├── web_investigator.py   # Amazonページ取得 + Gemini AIによる付属品抽出
├── credentials.json      # Google APIサービスアカウント認証情報
└── requirements.txt      # 依存ライブラリ一覧
```

---

## 処理フロー

```
main.py
  │
  ├─① SpreadsheetClient でシート全行を取得
  │
  └─② 各行をループ
        │
        ├─ asin_processor.should_process_row() で処理要否を判定
        │   ・J列(ASIN)が有効な10文字英数字
        │   ・BC列(付属品)が空欄
        │   ・BD列(URL)が空欄
        │   → どれか1つでも条件を満たさなければスキップ
        │
        ├─ web_investigator.fetch_accessory_info(asin) を呼び出し
        │   ├─① primp でAmazon商品ページのHTMLを取得
        │   ├─② BeautifulSoup で不要タグ除去、プレーンテキスト化（最大20,000文字）
        │   └─③ Gemini API (gemini-2.5-flash) にテキストを投げてJSONで付属品リストを返させる
        │       ・Rate Limit (429) の場合は最大5回まで自動リトライ
        │       ・付属品が見つかれば「ケーブル,アダプター,...」形式で返却
        │       ・見つからなければ「付属品記載なし」を返却
        │
        └─ スプレッドシートのBC列・BD列に結果を書き込み
```

---

## スプレッドシートのデータ構造

| 列 | 内容 | 設定名 |
|---|---|---|
| J列 (10列目) | ASIN | `COL_ASIN = 10` |
| BC列 (55列目) | **付属品（出力先）** | `COL_ACCESSORY = 55` |
| BD列 (56列目) | **根拠URL（出力先）** | `COL_URL = 56` |

- シート名: `商品リスト`
- 処理開始行: 2行目（1行目はヘッダー）
- 処理終了行: `END_ROW = None`（全行）

---

## AIへのプロンプト設計

- モデル: `gemini-2.5-flash`
- 出力形式: JSON配列（`response_mime_type="application/json"`で強制）
- 主な指示:
  - 「付属品」「同梱品」「パッケージ内容」に該当するものを抽出
  - 「別売」「オプション」は含めない
  - **括弧内の情報（長さ・個数・型番）は除外する**
    - 例: `DisplayPortケーブル(1.8m)` → `DisplayPortケーブル`

---

## 現在の既知問題

### ⚠️ APIレートリミット（最重要课题）

`gemini-2.5-flash` の無料枠は **1日あたり20リクエストまで**。

| 総データ行 | 処理済み | 残り |
|---|---|---|
| 約318件 | 約41件 | 約277件 |

20件/日のペースだと全件完了まで約14日かかる。

### 解決策

| 方法 | コスト | 難易度 |
|---|---|---|
| Google AI Studio で課金有効化 | 数十〜100円以下 | ★☆☆ |
| Groq API に切り替え (Llama-3) | 完全無料・14,400回/日 | ★★☆ |

---

## 依存ライブラリ

| ライブラリ | 用途 |
|---|---|
| `gspread` | Google Sheets API |
| `google-auth` | API認証 |
| `primp` | AmazonページのHTMLを取得（ボット対策回避） |
| `beautifulsoup4` | HTML解析・テキスト抽出 |
| `google-genai` | Gemini API（AI抽出） |
| `PyMuPDF` | PDF取説テキスト抽出（現在は未使用） |
