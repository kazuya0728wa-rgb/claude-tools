"""
シートデータ整備スクリプト
1. 担当マスター → マトリクス形式に変換（チェックボックス付き）
2. 稼働記録 → 正しい構造に修正（タイトル行1、空行2、ヘッダー行3、データ行4+）
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from auth import build_service
from config import SPREADSHEET_ID

sheets = build_service('sheets', 'v4').spreadsheets()

# ============================================================
# 1. 担当マスター → マトリクス形式
# ============================================================

# クライアント一覧（顧客・秘書マスターと合わせる）
clients = ['田中商事', '山田産業', '鈴木建設', '佐藤物産', '伊藤製造']

# 秘書×クライアント担当マップ
secretary_assignments = {
    '若松和弥':  {'email': 'kazuya0728wa@gmail.com', 'clients': {'田中商事': True,  '山田産業': False, '鈴木建設': False, '佐藤物産': False, '伊藤製造': False}},
    '青山花子':  {'email': 'hanako@example.com',     'clients': {'田中商事': True,  '山田産業': False, '鈴木建設': False, '佐藤物産': True,  '伊藤製造': False}},
    '中村太郎':  {'email': 'taro@example.com',       'clients': {'田中商事': False, '山田産業': True,  '鈴木建設': True,  '佐藤物産': False, '伊藤製造': False}},
    '小林美香':  {'email': 'mika@example.com',       'clients': {'田中商事': False, '山田産業': False, '鈴木建設': False, '佐藤物産': True,  '伊藤製造': True}},
    '加藤健一':  {'email': 'kenichi@example.com',    'clients': {'田中商事': True,  '山田産業': False, '鈴木建設': False, '佐藤物産': False, '伊藤製造': True}},
}

# まずシートIDを取得
sheet_meta = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id_map = {s['properties']['title']: s['properties']['sheetId'] for s in sheet_meta['sheets']}
master_sheet_id = sheet_id_map.get('担当マスター')

if master_sheet_id is None:
    print('[ERROR] 担当マスターシートが見つかりません', file=sys.stderr)
    sys.exit(1)

print(f'担当マスター sheetId: {master_sheet_id}')

# シートをクリア
sheets.values().clear(
    spreadsheetId=SPREADSHEET_ID,
    range='担当マスター!A:Z'
).execute()

# データを書き込む
# 行2: ヘッダー
header_row = ['秘書名', 'メールアドレス'] + clients
# 行3以降: 秘書データ
data_rows = []
for sec_name, info in secretary_assignments.items():
    row = [sec_name, info['email']]
    for cli in clients:
        row.append(info['clients'].get(cli, False))
    data_rows.append(row)

# タイトル（行1）
sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='担当マスター!A1',
    valueInputOption='RAW',
    body={'values': [['【担当マスター】 秘書×クライアント担当表']]}
).execute()

# ヘッダー（行2）
sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='担当マスター!A2',
    valueInputOption='RAW',
    body={'values': [header_row]}
).execute()

# データ（行3〜）
sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='担当マスター!A3',
    valueInputOption='RAW',
    body={'values': data_rows}
).execute()

# チェックボックスのデータバリデーション適用
n_secs = len(secretary_assignments)
n_clis = len(clients)
# C3:G{3+n_secs-1} にBOOLEANバリデーション
checkbox_requests = [{
    'setDataValidation': {
        'range': {
            'sheetId': master_sheet_id,
            'startRowIndex': 2,  # 0-indexed: row 3
            'endRowIndex': 2 + n_secs,
            'startColumnIndex': 2,  # 0-indexed: col C
            'endColumnIndex': 2 + n_clis,
        },
        'rule': {
            'condition': {'type': 'BOOLEAN'},
            'strict': True,
            'showCustomUi': True,
        }
    }
}]

# タイトル行をマージ
merge_request = [{
    'mergeCells': {
        'range': {
            'sheetId': master_sheet_id,
            'startRowIndex': 0,
            'endRowIndex': 1,
            'startColumnIndex': 0,
            'endColumnIndex': 2 + n_clis,
        },
        'mergeType': 'MERGE_ALL',
    }
}]

# 書式設定
format_requests = [
    # タイトル行
    {
        'repeatCell': {
            'range': {
                'sheetId': master_sheet_id,
                'startRowIndex': 0, 'endRowIndex': 1,
                'startColumnIndex': 0, 'endColumnIndex': 2 + n_clis,
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.098, 'green': 0.098, 'blue': 0.224},
                    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 13},
                    'horizontalAlignment': 'CENTER',
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)',
        }
    },
    # ヘッダー行（行2）
    {
        'repeatCell': {
            'range': {
                'sheetId': master_sheet_id,
                'startRowIndex': 1, 'endRowIndex': 2,
                'startColumnIndex': 0, 'endColumnIndex': 2 + n_clis,
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.851, 'green': 0.910, 'blue': 0.984},
                    'textFormat': {'foregroundColor': {'red': 0.102, 'green': 0.137, 'blue': 0.494}, 'bold': True},
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat)',
        }
    },
    # 列幅: A=150, B=230, C以降=100
    {'updateDimensionProperties': {'range': {'sheetId': master_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1}, 'properties': {'pixelSize': 150}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': master_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2}, 'properties': {'pixelSize': 230}, 'fields': 'pixelSize'}},
]
for i in range(n_clis):
    format_requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': master_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 2 + i, 'endIndex': 3 + i},
            'properties': {'pixelSize': 100},
            'fields': 'pixelSize',
        }
    })

sheets.batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': merge_request + checkbox_requests + format_requests}
).execute()

print('✅ 担当マスター をマトリクス形式に変換しました')

# ============================================================
# 2. 稼働記録 → 正しい構造に修正
# ============================================================

record_sheet_id = sheet_id_map.get('稼働記録')
if record_sheet_id is None:
    print('[ERROR] 稼働記録シートが見つかりません', file=sys.stderr)
    sys.exit(1)

# データ行（F列は稼働時間を文字列で保持、後でformula化）
# 日付はすべて文字列、時刻はテキスト形式
record_data = [
    # 日付,        秘書名,     クライアント名, 開始,    終了,    メモ,                   備考,       フラグ
    ['2026/03/22', '青山花子', '田中商事',    '09:00', '12:30', '資料作成・メール対応',  '',         ''],
    ['2026/03/22', '青山花子', '佐藤物産',    '13:00', '15:00', 'スケジュール調整',      '',         ''],
    ['2026/03/23', '青山花子', '田中商事',    '10:00', '13:00', '会議準備・議事録作成',  '',         ''],
    ['2026/03/22', '中村太郎', '山田産業',    '09:30', '12:00', '電話対応・資料整理',    '',         ''],
    ['2026/03/22', '中村太郎', '鈴木建設',    '13:30', '17:30', '契約書確認・書類作成',  '月次報告用', ''],
    ['2026/03/23', '中村太郎', '山田産業',    '09:00', '11:30', 'メール対応・見積もり確認', '',      ''],
    ['2026/03/22', '小林美香', '佐藤物産',    '10:00', '14:00', 'プレゼン資料作成',      '',         ''],
    ['2026/03/22', '小林美香', '伊藤製造',    '14:30', '17:00', '問い合わせ対応',        '',         ''],
    ['2026/03/23', '小林美香', '伊藤製造',    '09:00', '12:00', '月次レポート作成',      '',         ''],
    ['2026/03/22', '加藤健一', '田中商事',    '08:30', '12:30', '営業サポート・資料整理', '',        ''],
    ['2026/03/22', '加藤健一', '伊藤製造',    '13:00', '16:30', '採用関連書類確認',      '',         ''],
    ['2026/03/23', '加藤健一', '田中商事',    '09:00', '14:00', '企画書作成',            '重要案件', ''],
    ['2026/03/22', '若松和弥', '株式会社A',   '23:05', '23:10', 'テスト稼働：メール対応', 'aaa',     ''],
    ['2026/03/22', '若松和弥', '株式会社A',   '23:26', '23:32', 'sagyo',                 'aaa',     ''],
    ['2026/03/22', '若松和弥', '株式会社B',   '23:32', '23:33', 'aaaa',                  'sss',     ''],
    ['2026/03/23', '若松和弥', '株式会社A',   '00:32', '00:37', '',                      '',         ''],
    ['2026/03/23', '若松和弥', '株式会社A',   '00:46', '00:49', 'ああ',                  '',         ''],
    ['2026/03/23', '若松和弥', '株式会社A',   '00:53', '00:58', '',                      '',         ''],
    ['2026/03/23', '若松和弥', '株式会社B',   '00:58', '00:59', 'ｗｗｗ',                '',         ''],
    ['2026/03/23', '若松和弥', '株式会社A',   '01:01', '06:22', 'ああ',                  '',         '手動修正'],
]

# シートをクリア
sheets.values().clear(
    spreadsheetId=SPREADSHEET_ID,
    range='稼働記録!A:Z'
).execute()

# タイトル（行1）
sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='稼働記録!A1',
    valueInputOption='RAW',
    body={'values': [['稼働記録']]}
).execute()

# ヘッダー（行3）
header = [['日付', '秘書名', 'クライアント名', '開始時刻', '終了時刻', '稼働時間', '作業内容', '備考', 'フラグ']]
sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='稼働記録!A3',
    valueInputOption='RAW',
    body={'values': header}
).execute()

# データ（行4〜）: 列A〜E, G〜I を先に書き込む（F列は数式）
data_no_formula = []
for i, row in enumerate(record_data):
    # 日付, 秘書名, クライアント名, 開始, 終了, '', メモ, 備考, フラグ
    data_no_formula.append([row[0], row[1], row[2], row[3], row[4], '', row[5], row[6], row[7]])

sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='稼働記録!A4',
    valueInputOption='USER_ENTERED',
    body={'values': data_no_formula}
).execute()

# F列（稼働時間）に数式を設定
formula_values = []
for i in range(len(record_data)):
    row_num = i + 4
    formula_values.append([f'=IF(AND(D{row_num}<>"",E{row_num}<>""),E{row_num}-D{row_num},"")'])

sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=f'稼働記録!F4:F{3 + len(record_data)}',
    valueInputOption='USER_ENTERED',
    body={'values': formula_values}
).execute()

# 書式設定（稼働記録）
n_rows = len(record_data)
rec_format_requests = [
    # タイトル行
    {
        'repeatCell': {
            'range': {'sheetId': record_sheet_id, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0, 'endColumnIndex': 9},
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.098, 'green': 0.098, 'blue': 0.224},
                    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 13},
                    'horizontalAlignment': 'CENTER',
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)',
        }
    },
    # ヘッダー行（行3）
    {
        'repeatCell': {
            'range': {'sheetId': record_sheet_id, 'startRowIndex': 2, 'endRowIndex': 3, 'startColumnIndex': 0, 'endColumnIndex': 9},
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.851, 'green': 0.910, 'blue': 0.984},
                    'textFormat': {'foregroundColor': {'red': 0.102, 'green': 0.137, 'blue': 0.494}, 'bold': True},
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat)',
        }
    },
    # A列（日付）フォーマット
    {
        'repeatCell': {
            'range': {'sheetId': record_sheet_id, 'startRowIndex': 3, 'endRowIndex': 3 + n_rows, 'startColumnIndex': 0, 'endColumnIndex': 1},
            'cell': {'userEnteredFormat': {'numberFormat': {'type': 'DATE', 'pattern': 'yyyy/MM/dd'}}},
            'fields': 'userEnteredFormat.numberFormat',
        }
    },
    # F列（稼働時間）フォーマット
    {
        'repeatCell': {
            'range': {'sheetId': record_sheet_id, 'startRowIndex': 3, 'endRowIndex': 3 + n_rows, 'startColumnIndex': 5, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {'numberFormat': {'type': 'DATE_TIME', 'pattern': '[h]:mm'}}},
            'fields': 'userEnteredFormat.numberFormat',
        }
    },
    # D, E列（開始・終了）テキスト形式
    {
        'repeatCell': {
            'range': {'sheetId': record_sheet_id, 'startRowIndex': 3, 'endRowIndex': 3 + n_rows, 'startColumnIndex': 3, 'endColumnIndex': 5},
            'cell': {'userEnteredFormat': {'numberFormat': {'type': 'TEXT'}}},
            'fields': 'userEnteredFormat.numberFormat',
        }
    },
    # タイトル行マージ
    {
        'mergeCells': {
            'range': {'sheetId': record_sheet_id, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0, 'endColumnIndex': 9},
            'mergeType': 'MERGE_ALL',
        }
    },
    # 列幅
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1}, 'properties': {'pixelSize': 110}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2}, 'properties': {'pixelSize': 120}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3}, 'properties': {'pixelSize': 130}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 5}, 'properties': {'pixelSize': 80}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 5, 'endIndex': 6}, 'properties': {'pixelSize': 80}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 7}, 'properties': {'pixelSize': 200}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 7, 'endIndex': 8}, 'properties': {'pixelSize': 150}, 'fields': 'pixelSize'}},
    {'updateDimensionProperties': {'range': {'sheetId': record_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 8, 'endIndex': 9}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
]

sheets.batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': rec_format_requests}
).execute()

print('✅ 稼働記録 を正しい構造に修正しました')
print(f'   タイトル: 行1, ヘッダー: 行3, データ: 行4〜{3 + n_rows}')

# ============================================================
# 3. 顧客・秘書マスター に若松和弥を追加（秘書管理表）
# ============================================================

# 若松和弥 を秘書管理表に追加（行9）
sheets.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='顧客・秘書マスター!H9:K9',
    valueInputOption='RAW',
    body={'values': [['若松和弥', 'kazuya0728wa@gmail.com', 2000, '']]}
).execute()

print('✅ 顧客・秘書マスター に若松和弥の秘書情報を追加しました')
print('\n🎉 すべてのデータ整備が完了しました！')
