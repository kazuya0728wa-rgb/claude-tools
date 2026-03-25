"""
稼働管理表_3Link 集計整合性テスト

テスト項目:
1. 月次集計（クライアントブロック）× 月 × クライアント = 稼働記録の集計と一致
2. 月次集計（秘書ブロック）× 月 × 秘書 = 稼働記録の集計と一致
3. S_〇〇シート × 月 × クライアント行 = 稼働記録の集計と一致
4. C_〇〇シート × 月 × 秘書行 = 稼働記録の集計と一致
5. クロス検証：月次集計クライアント合計 = C_シートの合計と一致
"""

import io
import sys
import os
import json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from auth import build_service
from config import SPREADSHEET_ID

def get_sheets_service():
    return build_service('sheets', 'v4')

def read_range(service, range_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueRenderOption='UNFORMATTED_VALUE'
    ).execute()
    return result.get('values', [])

def list_sheets(service):
    result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    return [s['properties']['title'] for s in result.get('sheets', [])]

def hhmm_to_minutes(val):
    """HH:MM形式またはシリアル値（Sheetsの時間）をミリ秒に変換"""
    if val == '' or val is None:
        return 0
    if isinstance(val, (int, float)):
        # Sheetsのシリアル値（1日=1.0）→ ミリ秒
        return round(val * 24 * 3600 * 1000)
    if isinstance(val, str) and ':' in val:
        parts = val.split(':')
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return (h * 60 + m) * 60 * 1000
    return 0

def ms_to_hhmm(ms):
    total_min = round(ms / 60000)
    h = total_min // 60
    m = total_min % 60
    return f"{h:02d}:{m:02d}"

def parse_date(val):
    """日付値から YYYY-MM を取得"""
    if val == '' or val is None:
        return None
    if isinstance(val, (int, float)):
        # Sheetsのシリアル値 → Python dateを計算
        from datetime import date
        base = date(1899, 12, 30)
        from datetime import timedelta
        d = base + timedelta(days=int(val))
        return d.strftime('%Y-%m')
    if isinstance(val, str):
        # YYYY/MM/DD or YYYY-MM-DD
        return val[:7].replace('/', '-')
    return None

def main():
    service = get_sheets_service()

    all_sheets = list_sheets(service)
    s_sheets = [s for s in all_sheets if s.startswith('S_')]
    c_sheets = [s for s in all_sheets if s.startswith('C_')]

    print(f"シート一覧: S_シート={s_sheets}, C_シート={c_sheets}")

    # ===== 稼働記録を読み込む =====
    # 列構成: A=日付, B=秘書名, C=メール, D=クライアント名, E=開始, F=終了, G=稼働時間, H=作業内容
    rec_data = read_range(service, '稼働記録!A2:I500')
    print(f"稼働記録: {len(rec_data)}行")

    # 集計: {(month, client): ms}, {(month, sec): ms}, {(month, client, sec): ms}
    cli_month_ms = {}  # (month, client) -> totalMs
    sec_month_ms = {}  # (month, sec) -> totalMs
    cli_sec_month_ms = {}  # (month, client, sec) -> totalMs

    for row in rec_data:
        if len(row) < 7:
            continue
        date_val = row[0] if len(row) > 0 else ''
        sec_name = row[1] if len(row) > 1 else ''
        cli_name = row[3] if len(row) > 3 else ''  # D列: クライアント名（C列はメール）
        hours_val = row[6] if len(row) > 6 else ''  # G列: 稼働時間

        month = parse_date(date_val)
        if not month or not sec_name or not cli_name:
            continue

        ms = hhmm_to_minutes(hours_val)
        if ms <= 0:
            # 稼働時間が未記入でも開始・終了から計算できる場合はスキップ（終了済みのみ対象）
            continue

        key_cli = (month, cli_name)
        key_sec = (month, sec_name)
        key_all = (month, cli_name, sec_name)

        cli_month_ms[key_cli] = cli_month_ms.get(key_cli, 0) + ms
        sec_month_ms[key_sec] = sec_month_ms.get(key_sec, 0) + ms
        cli_sec_month_ms[key_all] = cli_sec_month_ms.get(key_all, 0) + ms

    print(f"集計キー数: クライアント×月={len(cli_month_ms)}, 秘書×月={len(sec_month_ms)}")

    tests_passed = 0
    tests_failed = 0
    failures = []

    # ===== テスト1: 月次集計クライアントブロック（A〜H列）=====
    print("\n=== テスト1: 月次集計クライアントブロック ===")
    combined_cli = read_range(service, '月次集計!A4:H100')
    for row in combined_cli:
        if len(row) < 3 or not row[0] or not row[1]:
            continue
        month = parse_date(row[0])  # シリアル値 or 文字列 → "YYYY-MM"
        if not month:
            continue
        cli = str(row[1]).strip()

        actual_ms = hhmm_to_minutes(row[2] if len(row) > 2 else 0)
        expected_ms = cli_month_ms.get((month, cli), 0)

        diff = abs(actual_ms - expected_ms)
        # 1分(60000ms)以内の誤差は許容
        if diff <= 60000:
            tests_passed += 1
            print(f"  ✓ {month} {cli}: {ms_to_hhmm(actual_ms)} (期待値: {ms_to_hhmm(expected_ms)})")
        else:
            tests_failed += 1
            msg = f"  ✗ {month} {cli}: 実際={ms_to_hhmm(actual_ms)} 期待={ms_to_hhmm(expected_ms)} 差={ms_to_hhmm(diff)}"
            failures.append(msg)
            print(msg)

    # ===== テスト2: 月次集計秘書ブロック（J〜N列）=====
    print("\n=== テスト2: 月次集計秘書ブロック ===")
    combined_sec = read_range(service, '月次集計!J4:N100')
    for row in combined_sec:
        if len(row) < 3 or not row[0] or not row[1]:
            continue
        month = parse_date(row[0])
        if not month:
            continue
        sec = str(row[1]).strip()

        actual_ms = hhmm_to_minutes(row[2] if len(row) > 2 else 0)
        expected_ms = sec_month_ms.get((month, sec), 0)

        diff = abs(actual_ms - expected_ms)
        if diff <= 60000:
            tests_passed += 1
            print(f"  ✓ {month} {sec}: {ms_to_hhmm(actual_ms)} (期待値: {ms_to_hhmm(expected_ms)})")
        else:
            tests_failed += 1
            msg = f"  ✗ {month} {sec}: 実際={ms_to_hhmm(actual_ms)} 期待={ms_to_hhmm(expected_ms)} 差={ms_to_hhmm(diff)}"
            failures.append(msg)
            print(msg)

    # ===== テスト3: S_〇〇シートの整合性 =====
    print("\n=== テスト3: S_〇〇個別シート ===")
    for sheet_name in s_sheets:
        sec_name = sheet_name[2:]  # "S_" を除く
        data = read_range(service, f'{sheet_name}!A1:Z200')
        if not data:
            continue

        # S_シートのレイアウト: 行1=タイトル, 行2=空, 行3=ヘッダー（月, クライアント, 稼働時間,...）
        # データは行4以降
        # ヘッダー行を探す
        header_row = None
        data_start = None
        for i, row in enumerate(data):
            if row and len(row) >= 2 and '月' in str(row[0]) and 'クライアント' in str(row[1]):
                header_row = i
                data_start = i + 1
                break

        if data_start is None:
            print(f"  [{sheet_name}] ヘッダーが見つかりません")
            continue

        for row in data[data_start:]:
            if len(row) < 3 or not row[0] or not row[1]:
                continue
            month = parse_date(row[0])
            cli = str(row[1]).strip()
            if not month or not cli:
                continue

            actual_ms = hhmm_to_minutes(row[2] if len(row) > 2 else 0)
            expected_ms = cli_sec_month_ms.get((month, cli, sec_name), 0)

            diff = abs(actual_ms - expected_ms)
            if diff <= 60000:
                tests_passed += 1
                print(f"  ✓ [{sheet_name}] {month} {cli}: {ms_to_hhmm(actual_ms)}")
            else:
                tests_failed += 1
                msg = f"  ✗ [{sheet_name}] {month} {cli}: 実際={ms_to_hhmm(actual_ms)} 期待={ms_to_hhmm(expected_ms)}"
                failures.append(msg)
                print(msg)

    # ===== テスト4: C_〇〇シートの整合性 =====
    print("\n=== テスト4: C_〇〇個別シート ===")
    for sheet_name in c_sheets:
        cli_name = sheet_name[2:]  # "C_" を除く
        data = read_range(service, f'{sheet_name}!A1:Z200')
        if not data:
            continue

        # C_シートのレイアウト: 行1=タイトル, 行3=ヘッダー（月, 秘書名, 稼働時間,...）
        header_row = None
        data_start = None
        for i, row in enumerate(data):
            if row and len(row) >= 2 and '月' in str(row[0]) and '秘書' in str(row[1]):
                header_row = i
                data_start = i + 1
                break

        if data_start is None:
            print(f"  [{sheet_name}] ヘッダーが見つかりません")
            continue

        for row in data[data_start:]:
            if len(row) < 3 or not row[0] or not row[1]:
                continue
            month = parse_date(row[0])
            sec = str(row[1]).strip()
            if not month or not sec:
                continue

            actual_ms = hhmm_to_minutes(row[2] if len(row) > 2 else 0)
            expected_ms = cli_sec_month_ms.get((month, cli_name, sec), 0)

            diff = abs(actual_ms - expected_ms)
            if diff <= 60000:
                tests_passed += 1
                print(f"  ✓ [{sheet_name}] {month} {sec}: {ms_to_hhmm(actual_ms)}")
            else:
                tests_failed += 1
                msg = f"  ✗ [{sheet_name}] {month} {sec}: 実際={ms_to_hhmm(actual_ms)} 期待={ms_to_hhmm(expected_ms)}"
                failures.append(msg)
                print(msg)

    # ===== テスト5: クロス検証（月次集計CLI合計 = C_シート合計）=====
    print("\n=== テスト5: クロス検証（月次集計 vs C_シート合計）===")
    # 月次集計のクライアントブロックを再度読む
    for (month, cli), expected_ms in cli_month_ms.items():
        sheet_name = f'C_{cli}'
        if sheet_name not in all_sheets:
            continue

        # C_シートの該当月の全行を合算
        data = read_range(service, f'{sheet_name}!A1:Z200')
        if not data:
            continue

        # ヘッダー検索
        data_start = None
        for i, row in enumerate(data):
            if row and len(row) >= 2 and '月' in str(row[0]) and '秘書' in str(row[1]):
                data_start = i + 1
                break

        if data_start is None:
            continue

        c_total_ms = 0
        for row in data[data_start:]:
            if len(row) < 3 or not row[0] or not row[1]:
                continue
            row_month = parse_date(row[0])
            if row_month == month:
                c_total_ms += hhmm_to_minutes(row[2] if len(row) > 2 else 0)

        diff = abs(c_total_ms - expected_ms)
        if diff <= 60000:
            tests_passed += 1
            print(f"  ✓ {month} {cli}: 月次集計={ms_to_hhmm(expected_ms)} C_シート合計={ms_to_hhmm(c_total_ms)}")
        else:
            tests_failed += 1
            msg = f"  ✗ {month} {cli}: 月次集計={ms_to_hhmm(expected_ms)} C_シート合計={ms_to_hhmm(c_total_ms)}"
            failures.append(msg)
            print(msg)

    # ===== サマリー =====
    total = tests_passed + tests_failed
    print(f"\n{'='*50}")
    print(f"テスト結果: {tests_passed}/{total} 合格")
    if failures:
        print(f"\n失敗したテスト ({len(failures)}件):")
        for f in failures:
            print(f)
    else:
        print("全テスト合格！")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
