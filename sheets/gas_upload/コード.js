/**
 * 稼働管理システム（秘書×クライアント多対多対応）
 * Spreadsheet: 稼働管理表_3Link
 */

const SHEET = {
  master    : '担当マスター',
  record    : '稼働記録',
  clientSec : '顧客・秘書マスター',
  combined  : '月次集計',
  cliPrefix : 'C_',
  secPrefix : 'S_',
};

const COL = {
  // 担当マスター（行形式: A=秘書名, B=メール, C=クライアント名）
  masterSecName  : 1, // A
  masterEmail    : 2, // B
  masterClient   : 3, // C（行形式）
  // 稼働記録
  recDate    : 1,  // A
  recSecName : 2,  // B
  recEmail   : 3,  // C ← NEW: メールアドレス
  recClient  : 4,  // D
  recStart   : 5,  // E
  recEnd     : 6,  // F
  recHours   : 7,  // G
  recMemo    : 8,  // H
  recNote    : 9,  // I
  recFlag    : 10, // J
  // 顧客・秘書マスター（クライアント A〜F列）
  csCliName  : 1, // A
  csPlan     : 2, // B
  csFee      : 3, // C
  csLimitH   : 4, // D
  csOverRate : 5, // E
  csFrom     : 6, // F
  // 顧客・秘書マスター（秘書 H〜K列）
  csSecName  : 8,  // H
  csSecEmail : 9,  // I
  csSecRate  : 10, // J
  csSecFrom  : 11, // K
};

const HEADER_ROW     = 3;
const DATA_START     = 4;
const SUM_TITLE_ROW  = 1;
const SUM_HEADER_ROW = 3;
const SUM_DATA_START = 4;

// ============================================================
// Web App エントリーポイント
// ============================================================

function doGet() {
  return HtmlService.createHtmlOutputFromFile('フォーム')
    .setTitle('稼働管理')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ============================================================
// クライアント向けAPI（google.script.run から呼び出し）
// ============================================================

/**
 * ログインユーザーの担当クライアント一覧を返す
 * 担当マスターは行形式:
 *   行2=ヘッダー（秘書名|メール|クライアント名）
 *   行3+=データ（田中花子|hanako@...|A社）
 */
function getMyClients() {
  const email = Session.getActiveUser().getEmail();
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET.master);
  const rows  = sheet.getDataRange().getValues();

  const clients = [];
  for (let i = 2; i < rows.length; i++) { // 行3以降（index=2）がデータ
    const rowEmail   = String(rows[i][COL.masterEmail  - 1]).trim();
    const rowSecName = String(rows[i][COL.masterSecName - 1]).trim();
    const rowClient  = String(rows[i][COL.masterClient  - 1]).trim();
    if (rowEmail === email && rowClient) {
      clients.push({ name: rowClient, secName: rowSecName });
    }
  }
  return { email, clients };
}

/** 現在稼働中のレコードを返す（終了時刻が空のもの）
 *  最後500行のみスキャン（パフォーマンス改善）
 */
function getCurrentWorking() {
  const email   = Session.getActiveUser().getEmail();
  const ss      = SpreadsheetApp.getActiveSpreadsheet();
  const sheet   = ss.getSheetByName(SHEET.record);
  const secName = _getSecName(email);
  if (!secName) return null;

  const lastRow = sheet.getLastRow();
  if (lastRow < DATA_START) return null;

  // 最大500行に制限（約2年分に相当）
  const scanRows = Math.min(lastRow - DATA_START + 1, 500);
  const startRow = lastRow - scanRows + 1;
  const data = sheet.getRange(startRow, 1, scanRows, COL.recNote).getValues();

  for (let i = data.length - 1; i >= 0; i--) {
    const rowSec   = String(data[i][COL.recSecName - 1]).trim();
    const rowStart = data[i][COL.recStart - 1];
    const rowEnd   = data[i][COL.recEnd   - 1];
    if (rowSec === secName && rowStart !== '' && rowEnd === '') {
      return {
        client   : String(data[i][COL.recClient - 1]).trim(),
        startTime: _formatTime(rowStart),
        rowIndex : startRow + i,
      };
    }
  }
  return null;
}

/** 稼働開始 */
function startWork(clientName, memo) {
  const email   = Session.getActiveUser().getEmail();
  const secName = _getSecName(email);
  if (!secName) return { ok: false, msg: '担当マスターにメールアドレスが登録されていません。' };

  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET.record);
  const now   = new Date();
  const jst   = _toJST(now);

  // 既存稼働中があれば自動終了
  const current = getCurrentWorking();
  if (current) _setEndTime(sheet, current.rowIndex, jst);

  // 新レコード追加
  const dateStr = Utilities.formatDate(jst, 'Asia/Tokyo', 'yyyy/MM/dd');
  const timeStr = Utilities.formatDate(jst, 'Asia/Tokyo', 'HH:mm');
  const newRow  = sheet.getLastRow() + 1;

  sheet.getRange(newRow, COL.recDate   ).setValue(dateStr).setNumberFormat('yyyy/MM/dd');
  sheet.getRange(newRow, COL.recSecName).setValue(secName);
  sheet.getRange(newRow, COL.recEmail  ).setValue(email);   // メールアドレスも記録
  sheet.getRange(newRow, COL.recClient ).setValue(clientName);
  sheet.getRange(newRow, COL.recStart  ).setValue(jst).setNumberFormat('HH:mm');  // Date型で保存
  sheet.getRange(newRow, COL.recMemo   ).setValue(memo || '');
  sheet.getRange(newRow, COL.recHours  ).setFormula(
    // Date型同士の差分 → 日またぎ対応（全datetime保存なので単純引き算で正しい）
    `=IF(AND(E${newRow}<>"",F${newRow}<>""),F${newRow}-E${newRow},"")`
  ).setNumberFormat('[h]:mm');
  _formatRecordRow(sheet, newRow);

  return {
    ok: true, startTime: timeStr, rowIndex: newRow,
    autoEnded: current ? current.client : null,
    autoEndedRowIndex: current ? current.rowIndex : null,
  };
}

/** 稼働終了 */
function endWork(clientName, memo, note) {
  const email   = Session.getActiveUser().getEmail();
  const secName = _getSecName(email);
  if (!secName) return { ok: false, msg: '担当マスターにメールアドレスが登録されていません。' };

  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET.record);
  const now   = new Date();
  const jst   = _toJST(now);

  const current = getCurrentWorking();
  if (!current || current.client !== clientName) {
    return { ok: false, msg: `${clientName} の稼働記録が見つかりません。` };
  }

  _setEndTime(sheet, current.rowIndex, jst);
  if (memo) sheet.getRange(current.rowIndex, COL.recMemo).setValue(memo);
  if (note) sheet.getRange(current.rowIndex, COL.recNote).setValue(note);

  const timeStr = Utilities.formatDate(jst, 'Asia/Tokyo', 'HH:mm');
  return { ok: true, endTime: timeStr };
}

/** 未終了レコード一覧を返す */
function getOpenRecords() {
  const email   = Session.getActiveUser().getEmail();
  const secName = _getSecName(email);
  if (!secName) return [];

  const ss      = SpreadsheetApp.getActiveSpreadsheet();
  const sheet   = ss.getSheetByName(SHEET.record);
  const lastRow = sheet.getLastRow();
  if (lastRow < DATA_START) return [];

  const data   = sheet.getRange(DATA_START, 1, lastRow - DATA_START + 1, COL.recNote).getValues();
  const result = [];
  for (let i = 0; i < data.length; i++) {
    const rowSec   = String(data[i][COL.recSecName - 1]).trim();
    const rowStart = data[i][COL.recStart - 1];
    const rowEnd   = data[i][COL.recEnd   - 1];
    if (rowSec === secName && rowStart !== '' && rowEnd === '') {
      const rawDate = data[i][COL.recDate - 1];
      result.push({
        rowIndex : DATA_START + i,
        date     : _parseDateValue(rawDate),
        client   : String(data[i][COL.recClient - 1]).trim(),
        startTime: _formatTime(rowStart),
      });
    }
  }
  return result;
}

/** 稼働記録を手動修正 */
function correctRecord(rowIndex, endTime, clientName) {
  const email   = Session.getActiveUser().getEmail();
  const secName = _getSecName(email);
  if (!secName) return { ok: false, msg: '担当マスターにメールアドレスが登録されていません。' };

  const ss      = SpreadsheetApp.getActiveSpreadsheet();
  const sheet   = ss.getSheetByName(SHEET.record);
  const rowSec  = String(sheet.getRange(rowIndex, COL.recSecName).getValue()).trim();
  if (rowSec !== secName) return { ok: false, msg: '自分の稼働記録のみ修正できます。' };

  if (endTime) {
    if (!/^\d{1,2}:\d{2}$/.test(endTime)) return { ok: false, msg: '終了時刻の形式が正しくありません（HH:mm）。' };
    // 稼働記録の日付を取得してDate型で終了時刻を構築（startWork/endWorkと統一）
    const recDate = sheet.getRange(rowIndex, COL.recDate).getValue();
    const baseDate = recDate instanceof Date ? recDate : new Date();
    const [h, m] = endTime.split(':').map(Number);
    const endDate = new Date(baseDate);
    endDate.setHours(h, m, 0, 0);
    sheet.getRange(rowIndex, COL.recEnd).setValue(endDate).setNumberFormat('HH:mm');
  }
  sheet.getRange(rowIndex, COL.recFlag).setValue('手動修正');
  if (clientName) sheet.getRange(rowIndex, COL.recClient).setValue(clientName);
  return { ok: true };
}

// ============================================================
// カスタムメニュー
// ============================================================

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⚙️ 管理メニュー')
    .addItem('月次集計を更新',            'updateSummaries')
    .addItem('個別シートを作成・更新',     'createIndividualSheets')
    .addItem('すべて一括更新',            'updateAll')
    .addItem('当月のみ更新（高速）',       'updateCurrentMonth')
    .addSeparator()
    .addItem('稼働記録に書式を適用',       'formatRecordSheet')
    .addItem('顧客・秘書マスターを初期化', 'initClientSecMasterSheet')
    .addItem('担当マスターを初期化（行形式）', 'initMasterSheet')
    .addSeparator()
    .addItem('【移行】担当マスターをリスト形式に変換', 'migrateMasterToList')
    .addItem('【移行】稼働記録にメール列を追加',       'migrateAddEmailColumn')
    .addItem('原本シートを非表示',         'hideOriginalSheet')
    .addToUi();
}

/** 月次集計シートを更新 */
function updateSummaries() {
  _updateCombinedSummary();
  SpreadsheetApp.getUi().alert('月次集計を更新しました。');
}

/** 個別シートを作成・更新 */
function createIndividualSheets() {
  const errors = [];
  try { _createClientIndividualSheets(); } catch(e) { errors.push('C_シート: ' + e.message); Logger.log(e); }
  try { _createSecIndividualSheets();    } catch(e) { errors.push('S_シート: ' + e.message); Logger.log(e); }
  const msg = errors.length === 0 ? '個別シートを作成・更新しました。' : `エラー:\n${errors.join('\n')}`;
  SpreadsheetApp.getUi().alert(msg);
}

/** 当月のみ高速更新（タイムアウト対策） */
function updateCurrentMonth() {
  const now   = new Date();
  const month = Utilities.formatDate(now, 'Asia/Tokyo', 'yyyy-MM');
  const errors = [];
  try { _updateCombinedSummary();                    } catch(e) { errors.push('月次集計: ' + e.message); Logger.log(e); }
  try { _createClientIndividualSheets(month);        } catch(e) { errors.push('C_シート: ' + e.message); Logger.log(e); }
  try { _createSecIndividualSheets(month);           } catch(e) { errors.push('S_シート: ' + e.message); Logger.log(e); }
  const msg = errors.length === 0 ? `${month} を更新しました。` : `エラー: ${errors.join(', ')}`;
  try { SpreadsheetApp.getUi().alert(msg); } catch(e) { Logger.log(msg); }
}

/** すべてを一括更新（エラーハンドリング付き） */
function updateAll() {
  const errors = [];
  try { _updateCombinedSummary();       } catch(e) { errors.push('月次集計: ' + e.message); Logger.log(e); }
  try { _createClientIndividualSheets(); } catch(e) { errors.push('C_シート: ' + e.message); Logger.log(e); }
  try { _createSecIndividualSheets();    } catch(e) { errors.push('S_シート: ' + e.message); Logger.log(e); }

  const msg = errors.length === 0
    ? '全シートを更新しました。'
    : `一部エラーが発生しました:\n${errors.join('\n')}`;
  try { SpreadsheetApp.getUi().alert(msg); } catch(e) { Logger.log(msg); }
}

// ============================================================
// 管理ユーティリティ
// ============================================================

/** 原本シートを非表示 */
function hideOriginalSheet() {
  const s = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('原本');
  if (s) {
    s.hideSheet();
    try { SpreadsheetApp.getUi().alert('原本シートを非表示にしました。'); } catch(e) {}
  }
}

/** 担当マスターを行形式（リスト形式）で初期化 */
function initMasterSheet() {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  let sheet   = ss.getSheetByName(SHEET.master);
  if (!sheet) sheet = ss.insertSheet(SHEET.master);

  sheet.clearContents();
  sheet.clearFormats();

  // タイトル行
  sheet.getRange(1, 1, 1, 3).merge()
    .setValue('【担当マスター】 秘書×クライアント担当表')
    .setFontWeight('bold').setFontSize(13)
    .setBackground('#191939').setFontColor('#ffffff')
    .setHorizontalAlignment('center');

  // ヘッダー行（行2）
  sheet.getRange(2, 1, 1, 3)
    .setValues([['秘書名', 'メールアドレス', 'クライアント名']])
    .setFontWeight('bold').setBackground('#d9e8fb').setFontColor('#1a237e');

  // 列幅
  sheet.setColumnWidth(1, 130);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 150);

  Logger.log('担当マスターを初期化しました。行3以降にデータを追加してください。');
  SpreadsheetApp.getUi().alert(
    '担当マスターを初期化しました（行形式）。\n\n' +
    '行3以降に「秘書名 / メール / クライアント名」を\n' +
    '1行1対応で追加してください。'
  );
}

/** 顧客・秘書マスターシートを初期化 */
function initClientSecMasterSheet() {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  let sheet   = ss.getSheetByName(SHEET.clientSec);
  if (!sheet) sheet = ss.insertSheet(SHEET.clientSec);

  // ── クライアント管理表（A〜F列）──
  sheet.getRange(1, 1).setValue('【クライアント管理】').setFontWeight('bold');
  sheet.getRange(2, 1, 1, 6).setValues([[
    'クライアント名', 'プラン', '月額料金（円）', '月間上限時間（h）', '超過単価（円/h）', '適用開始月（yyyy/MM）'
  ]]).setFontWeight('bold').setBackground('#d9e8fb');
  sheet.getRange(3, 1).setValue('※適用開始月を空欄にするとデフォルト料金として扱われます')
    .setFontColor('#888888').setFontStyle('italic');

  // ── 秘書管理表（H〜K列）──
  sheet.getRange(1, 8).setValue('【秘書管理】').setFontWeight('bold');
  sheet.getRange(2, 8, 1, 4).setValues([['秘書名', 'メールアドレス', '時給（円/h）', '適用開始月（yyyy/MM）']])
    .setFontWeight('bold').setBackground('#fce8d9');
  sheet.getRange(3, 8).setValue('※適用開始月を空欄にするとデフォルト時給として扱われます')
    .setFontColor('#888888').setFontStyle('italic');

  // 列幅調整
  [150, 120, 130, 150, 140, 170, 30, 130, 200, 120, 170]
    .forEach((w, i) => sheet.setColumnWidth(i + 1, w));

  Logger.log('顧客・秘書マスターシートを初期化しました。');
}

// ============================================================
// データ移行スクリプト（1回のみ実行）
// ============================================================

/**
 * 担当マスターをマトリクス形式 → 行形式に変換（1回のみ実行）
 * 実行後: 担当マスターが行形式になり、getMyClients() が正しく動作する
 */
function migrateMasterToList() {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET.master);
  if (!sheet) { SpreadsheetApp.getUi().alert('担当マスターシートが見つかりません。'); return; }

  const rows = sheet.getDataRange().getValues();
  if (rows.length < 3) { SpreadsheetApp.getUi().alert('データがありません。'); return; }

  // 行2（index=1）がヘッダー、C列（index=2）以降がクライアント名
  const headerRow = rows[1];
  const newRows = [];

  for (let i = 2; i < rows.length; i++) {
    const secName = String(rows[i][0]).trim();
    const email   = String(rows[i][1]).trim();
    if (!secName || !email) continue;
    for (let c = 2; c < headerRow.length; c++) {
      const clientName = String(headerRow[c]).trim();
      if (clientName && rows[i][c] === true) {
        newRows.push([secName, email, clientName]);
      }
    }
  }

  if (newRows.length === 0) {
    SpreadsheetApp.getUi().alert('移行するデータが見つかりませんでした（TRUE列がない？）。');
    return;
  }

  sheet.clearContents();
  sheet.clearFormats();

  // タイトル・ヘッダー設定
  sheet.getRange(1, 1, 1, 3).merge()
    .setValue('【担当マスター】 秘書×クライアント担当表')
    .setBackground('#191939').setFontColor('#fff').setFontWeight('bold').setFontSize(13)
    .setHorizontalAlignment('center');
  sheet.getRange(2, 1, 1, 3)
    .setValues([['秘書名', 'メールアドレス', 'クライアント名']])
    .setBackground('#d9e8fb').setFontWeight('bold').setFontColor('#1a237e');
  sheet.getRange(3, 1, newRows.length, 3).setValues(newRows);

  sheet.setColumnWidth(1, 130);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 150);

  SpreadsheetApp.getUi().alert(`${newRows.length}件を行形式に移行しました。`);
}

/**
 * 稼働記録にメールアドレス列（C列）を追加（1回のみ実行）
 * ※ migrateMasterToList() 実行後に実行すること
 * 既存データのB列（秘書名）から担当マスターを参照してメールを補完
 */
function migrateAddEmailColumn() {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET.record);
  if (!sheet) { SpreadsheetApp.getUi().alert('稼働記録シートが見つかりません。'); return; }

  // 担当マスター（行形式）から 秘書名→メール のマップを作成
  const masterSheet = ss.getSheetByName(SHEET.master);
  const masterData  = masterSheet ? masterSheet.getDataRange().getValues() : [];
  const nameToEmail = {};
  for (let i = 2; i < masterData.length; i++) {
    const name  = String(masterData[i][0]).trim();
    const email = String(masterData[i][1]).trim();
    if (name && email && !nameToEmail[name]) nameToEmail[name] = email;
  }

  // C列（現在のクライアント名列）の前に列を挿入
  sheet.insertColumnBefore(3);

  // C列ヘッダーを設定（行3がヘッダー行）
  sheet.getRange(HEADER_ROW, COL.recEmail).setValue('メール').setFontWeight('bold');

  // 既存データのメール列を補完
  const lastRow = sheet.getLastRow();
  if (lastRow >= DATA_START) {
    const dataRows  = lastRow - DATA_START + 1;
    const secNames  = sheet.getRange(DATA_START, COL.recSecName, dataRows, 1).getValues();
    const emails    = secNames.map(([name]) => [nameToEmail[name] || '']);
    sheet.getRange(DATA_START, COL.recEmail, dataRows, 1).setValues(emails);
  }

  // 書式を適用（数式も更新）
  formatRecordSheet();

  SpreadsheetApp.getUi().alert(
    'メールアドレス列（C列）を稼働記録に追加しました。\n' +
    '既存レコードのメールアドレスを担当マスターから補完しました。'
  );
}

// ============================================================
// 月次集計シート
// ============================================================

function _updateCombinedSummary() {
  const ss       = SpreadsheetApp.getActiveSpreadsheet();
  const recSheet = ss.getSheetByName(SHEET.record);
  const rateMap  = _buildClientRateMap(ss);
  const secMap   = _buildSecRateMap(ss);
  const records  = _getRecords(recSheet);

  let sheet = ss.getSheetByName(SHEET.combined);
  if (!sheet) sheet = ss.insertSheet(SHEET.combined);
  sheet.clearContents();
  sheet.clearFormats();

  // ===== タイトル =====
  sheet.getRange(1, 1, 1, 14).merge()
    .setValue('【月次集計】 クライアント請求 & 秘書コスト')
    .setFontWeight('bold').setFontSize(13)
    .setBackground('#191939').setFontColor('#ffffff')
    .setHorizontalAlignment('center');

  const HEADER = 3;
  const DATA   = 4;

  // ===== 左ブロック: クライアントごとの合計 (A〜H列) =====
  const cliMap = {};
  records.forEach(r => {
    if (!r.hours || !r.date) return;
    const month = r.date.substring(0, 7);
    const key   = `${r.client}__${month}`;
    if (!cliMap[key]) cliMap[key] = { client: r.client, month, totalMs: 0 };
    cliMap[key].totalMs += r.hours;
  });
  const cliRows = Object.values(cliMap).sort((a, b) => {
    if (a.month !== b.month) return a.month.localeCompare(b.month);
    return a.client.localeCompare(b.client, 'ja');
  });

  sheet.getRange(HEADER, 1, 1, 8)
    .setValues([['月', 'クライアント名', '稼働時間', '上限時間(h)', '超過時間(h)', '月額料金（円）', '超過料金（円）', '合計請求金額（円）']])
    .setFontWeight('bold').setBackground('#fce8d9').setFontColor('#bf360c');

  if (cliRows.length > 0) {
    const out = cliRows.map(r => {
      const rate     = _getClientRate(rateMap, r.client, r.month);
      const hoursNum = r.totalMs / 3600000;
      const limitH   = rate ? rate.limitH   : '';
      const fee      = rate ? rate.fee      : '';
      const overRate = rate ? rate.overRate : 2500;
      const overH    = (rate && limitH !== '' && hoursNum > limitH) ? Math.max(0, hoursNum - limitH) : 0;
      const overFee  = (rate && overH > 0) ? Math.round(overH * overRate) : '';
      const total    = (fee !== '' && overFee !== '') ? fee + overFee
                     : (fee !== '')                   ? fee : '';
      return [r.month, r.client, _msToHHMM(r.totalMs),
              limitH, overH > 0 ? Math.round(overH * 100) / 100 : '', fee, overFee, total];
    });
    // 月列をテキスト形式で書き込み（Sheetsの日付自動変換を防ぐ）
    sheet.getRange(DATA, 1, out.length, 1).setNumberFormat('@');
    sheet.getRange(DATA, 1, out.length, 8).setValues(out);
    sheet.getRange(DATA, 6, out.length, 3).setNumberFormat('#,##0');
    out.forEach((_, i) => {
      if (i % 2 === 1) sheet.getRange(DATA + i, 1, 1, 8).setBackground('#fff8f5');
    });
  }

  // ===== 右ブロック: 秘書ごとの合計 (J〜N列, I列ギャップ) =====
  const SEC_COL = 10; // J列

  // 全秘書×全月のゼロ初期化（稼働ゼロの秘書も表示）
  const allSecNames = _getAllSecNames(ss);
  const allMonths   = [...new Set(records.filter(r => r.date).map(r => r.date.substring(0, 7)))].sort();

  const secAggMap = {};
  // ゼロ初期化
  allSecNames.forEach(secName => {
    allMonths.forEach(month => {
      const key = `${secName}__${month}`;
      if (!secAggMap[key]) secAggMap[key] = { secName, month, totalMs: 0 };
    });
  });
  // 実績を加算
  records.forEach(r => {
    if (!r.hours || !r.date) return;
    const month = r.date.substring(0, 7);
    const key   = `${r.secName}__${month}`;
    if (!secAggMap[key]) secAggMap[key] = { secName: r.secName, month, totalMs: 0 };
    secAggMap[key].totalMs += r.hours;
  });

  const secRows = Object.values(secAggMap).sort((a, b) => {
    if (a.month !== b.month) return a.month.localeCompare(b.month);
    return a.secName.localeCompare(b.secName, 'ja');
  });

  sheet.getRange(HEADER, SEC_COL, 1, 5)
    .setValues([['月', '秘書名', '稼働時間合計', '時給（円/h）', '報酬合計（円）']])
    .setFontWeight('bold').setBackground('#d9e8fb').setFontColor('#1a237e');

  if (secRows.length > 0) {
    const out = secRows.map(r => {
      const entry  = _getSecRate(secMap, r.secName, r.month);
      const rate   = entry ? entry.rate : '';
      const hours  = r.totalMs / 3600000;
      const reward = (rate && hours > 0) ? Math.round(hours * rate) : (rate ? 0 : '');
      return [r.month, r.secName, _msToHHMM(r.totalMs), rate, reward];
    });
    // 月列をテキスト形式で書き込み
    sheet.getRange(DATA, SEC_COL, out.length, 1).setNumberFormat('@');
    sheet.getRange(DATA, SEC_COL, out.length, 5).setValues(out);
    sheet.getRange(DATA, SEC_COL + 4, out.length, 1).setNumberFormat('#,##0');
    out.forEach((_, i) => {
      if (i % 2 === 1) sheet.getRange(DATA + i, SEC_COL, 1, 5).setBackground('#f5f8ff');
    });
  }

  // 列幅
  [100, 150, 90, 100, 90, 120, 110, 140, 30, 100, 130, 100, 100, 130]
    .forEach((w, i) => sheet.setColumnWidth(i + 1, w));
}

// ============================================================
// 個別シート作成
// ============================================================

/** クライアントごとの個別シートを作成・更新 (filterMonth指定時は当月レコードのみ) */
function _createClientIndividualSheets(filterMonth) {
  const ss       = SpreadsheetApp.getActiveSpreadsheet();
  const recSheet = ss.getSheetByName(SHEET.record);
  const rateMap  = _buildClientRateMap(ss);
  const records  = _getRecords(recSheet);

  const clientNames = new Set();
  const csSheet = ss.getSheetByName(SHEET.clientSec);
  if (csSheet) {
    const data = csSheet.getDataRange().getValues();
    for (let i = DATA_START - 1; i < data.length; i++) {
      const name = String(data[i][COL.csCliName - 1]).trim();
      if (name && !name.startsWith('※')) clientNames.add(name);
    }
  }
  records.forEach(r => { if (r.client) clientNames.add(r.client); });

  clientNames.forEach(clientName => {
    const sheetName = SHEET.cliPrefix + clientName;
    let sheet = ss.getSheetByName(sheetName);
    if (!sheet) sheet = ss.insertSheet(sheetName);
    const filteredRecords = filterMonth
      ? records.filter(r => r.date && r.date.substring(0, 7) === filterMonth)
      : records;
    _writeClientIndividualSheet(sheet, clientName, filteredRecords, rateMap);
  });
}

/**
 * クライアント個別シート書き込み（横並びレイアウト）
 *   左: 月別サマリー（A〜H列）  ギャップ: I列  右: 詳細記録（J〜P列）
 */
function _writeClientIndividualSheet(sheet, clientName, allRecords, rateMap) {
  sheet.clearContents();
  sheet.clearFormats();

  // タイトル
  sheet.getRange(1, 1, 1, 16).merge()
    .setValue(`【 ${clientName} 】 稼働記録`)
    .setFontWeight('bold').setFontSize(14)
    .setBackground('#191939').setFontColor('#ffffff')
    .setHorizontalAlignment('center');

  const cliRecords = allRecords.filter(r => r.client === clientName);

  // 月×秘書で集計
  const map = {};
  cliRecords.forEach(r => {
    if (!r.hours || !r.date) return;
    const month = r.date.substring(0, 7);
    const key   = `${month}__${r.secName}`;
    if (!map[key]) map[key] = { month, secName: r.secName, totalMs: 0, days: new Set() };
    map[key].totalMs += r.hours;
    map[key].days.add(r.date);
  });

  const summaryRows = Object.values(map).sort((a, b) => {
    if (a.month !== b.month) return a.month.localeCompare(b.month);
    return a.secName.localeCompare(b.secName, 'ja');
  });

  // ── 左: 月別サマリー ──
  sheet.getRange(3, 1, 1, 8)
    .setValues([['月', '秘書名', '稼働時間', '上限時間(h)', '超過時間(h)', '月額料金（円）', '超過料金（円）', '合計請求金額（円）']])
    .setFontWeight('bold').setBackground('#fce8d9').setFontColor('#bf360c');

  const detailCol = 10; // J列

  // ── 右: 詳細記録 ──
  sheet.getRange(3, detailCol, 1, 7)
    .setValues([['日付', '秘書名', '開始', '終了', '稼働時間', '作業内容', '備考']])
    .setFontWeight('bold').setBackground('#e8f5e9').setFontColor('#1b5e20');

  if (summaryRows.length > 0) {
    const out = summaryRows.map(r => {
      const rate     = _getClientRate(rateMap, clientName, r.month);
      const hoursNum = r.totalMs / 3600000;
      const limitH   = rate ? rate.limitH   : '';
      const fee      = rate ? rate.fee      : '';
      const overRate = rate ? rate.overRate : 2500;
      const overH    = (rate && limitH !== '' && hoursNum > limitH) ? Math.max(0, hoursNum - limitH) : 0;
      const overFee  = (rate && overH > 0) ? Math.round(overH * overRate) : '';
      const total    = (fee !== '' && overFee !== '') ? fee + overFee : (fee !== '') ? fee : '';
      return [r.month, r.secName, _msToHHMM(r.totalMs), limitH,
              overH > 0 ? Math.round(overH * 100) / 100 : '', fee, overFee, total];
    });
    // 月列をテキスト形式で書き込み
    sheet.getRange(4, 1, out.length, 1).setNumberFormat('@');
    sheet.getRange(4, 1, out.length, 8).setValues(out);
    sheet.getRange(4, 6, out.length, 3).setNumberFormat('#,##0');
    out.forEach((_, i) => {
      if (i % 2 === 1) sheet.getRange(4 + i, 1, 1, 8).setBackground('#fff8f5');
    });
  } else {
    sheet.getRange(4, 1).setValue('稼働記録がありません').setFontColor('#aaaaaa');
  }

  const sorted = cliRecords.filter(r => r.date).sort((a, b) => a.date.localeCompare(b.date));
  if (sorted.length > 0) {
    const detail = sorted.map(r => [
      r.date, r.secName, r.start || '', r.end || '',
      r.hours ? _msToHHMM(r.hours) : '', r.memo || '', r.note || '',
    ]);
    sheet.getRange(4, detailCol, detail.length, 7).setValues(detail);
  }

  [100, 130, 80, 90, 90, 110, 100, 130, 30, 100, 130, 70, 70, 80, 120, 120]
    .forEach((w, i) => sheet.setColumnWidth(i + 1, w));
}

/** 秘書ごとの個別シートを作成・更新 (filterMonth指定時は当月レコードのみ) */
function _createSecIndividualSheets(filterMonth) {
  const ss         = SpreadsheetApp.getActiveSpreadsheet();
  const recSheet   = ss.getSheetByName(SHEET.record);
  const secRateMap = _buildSecRateMap(ss);
  const records    = _getRecords(recSheet);

  const secNames = new Set();
  const csSheet  = ss.getSheetByName(SHEET.clientSec);
  if (csSheet) {
    const data = csSheet.getDataRange().getValues();
    for (let i = DATA_START - 1; i < data.length; i++) {
      const name = String(data[i][COL.csSecName - 1]).trim();
      if (name && !name.startsWith('※')) secNames.add(name);
    }
  }
  records.forEach(r => { if (r.secName) secNames.add(r.secName); });

  secNames.forEach(secName => {
    const sheetName = SHEET.secPrefix + secName;
    let sheet = ss.getSheetByName(sheetName);
    if (!sheet) sheet = ss.insertSheet(sheetName);
    const filteredRecords = filterMonth
      ? records.filter(r => r.date && r.date.substring(0, 7) === filterMonth)
      : records;
    _writeSecIndividualSheet(sheet, secName, filteredRecords, secRateMap);
  });
}

/**
 * 秘書個別シート書き込み（横並びレイアウト）
 *   左: 月別サマリー（A〜F列）  ギャップ: G列  右: 詳細記録（H〜N列）
 */
function _writeSecIndividualSheet(sheet, secName, allRecords, secRateMap) {
  sheet.clearContents();
  sheet.clearFormats();

  // タイトル
  sheet.getRange(1, 1, 1, 14).merge()
    .setValue(`【 ${secName} 】 稼働記録`)
    .setFontWeight('bold').setFontSize(14)
    .setBackground('#191939').setFontColor('#ffffff')
    .setHorizontalAlignment('center');

  const secRecords = allRecords.filter(r => r.secName === secName);

  // 月×クライアントで集計
  const map = {};
  secRecords.forEach(r => {
    if (!r.hours || !r.date) return;
    const month = r.date.substring(0, 7);
    const key   = `${month}__${r.client}`;
    if (!map[key]) map[key] = { month, client: r.client, totalMs: 0, days: new Set() };
    map[key].totalMs += r.hours;
    map[key].days.add(r.date);
  });

  const summaryRows = Object.values(map).sort((a, b) => {
    if (a.month !== b.month) return a.month.localeCompare(b.month);
    return a.client.localeCompare(b.client, 'ja');
  });

  // ── 左: 月別サマリー ──
  sheet.getRange(3, 1, 1, 6)
    .setValues([['月', 'クライアント名', '月間稼働時間', '稼働日数', '時給（円/h）', '報酬（円）']])
    .setFontWeight('bold').setBackground('#d9e8fb').setFontColor('#1a237e');

  const detailCol = 8; // H列

  // ── 右: 詳細記録 ──
  sheet.getRange(3, detailCol, 1, 7)
    .setValues([['日付', 'クライアント名', '開始', '終了', '稼働時間', '作業内容', '備考']])
    .setFontWeight('bold').setBackground('#e8f5e9').setFontColor('#1b5e20');

  if (summaryRows.length > 0) {
    const out = summaryRows.map(r => {
      const secEntry = _getSecRate(secRateMap, secName, r.month);
      const rate     = secEntry ? secEntry.rate : '';
      const hours    = r.totalMs / 3600000;
      const reward   = rate ? Math.round(hours * rate) : '';
      return [r.month, r.client, _msToHHMM(r.totalMs), r.days.size, rate, reward];
    });
    // 月列をテキスト形式で書き込み
    sheet.getRange(4, 1, out.length, 1).setNumberFormat('@');
    sheet.getRange(4, 1, out.length, 6).setValues(out);
    sheet.getRange(4, 6, out.length, 1).setNumberFormat('#,##0');
    out.forEach((_, i) => {
      if (i % 2 === 1) sheet.getRange(4 + i, 1, 1, 6).setBackground('#f5f8ff');
    });
  } else {
    sheet.getRange(4, 1).setValue('稼働記録がありません').setFontColor('#aaaaaa');
  }

  const sorted = secRecords.filter(r => r.date).sort((a, b) => a.date.localeCompare(b.date));
  if (sorted.length > 0) {
    const detail = sorted.map(r => [
      r.date, r.client, r.start || '', r.end || '',
      r.hours ? _msToHHMM(r.hours) : '', r.memo || '', r.note || '',
    ]);
    sheet.getRange(4, detailCol, detail.length, 7).setValues(detail);
  }

  [100, 150, 80, 70, 80, 100, 30, 100, 150, 70, 70, 80, 120, 120]
    .forEach((w, i) => sheet.setColumnWidth(i + 1, w));
}

/** 稼働記録シートの書式を整える */
function formatRecordSheet() {
  const ss      = SpreadsheetApp.getActiveSpreadsheet();
  const sheet   = ss.getSheetByName(SHEET.record);
  const lastRow = sheet.getLastRow();
  if (lastRow < DATA_START) return;

  const dataRows = lastRow - DATA_START + 1;
  const range = sheet.getRange(DATA_START, 1, dataRows, COL.recFlag);

  range.setBackground('#181839')
       .setFontColor('#ffffff')
       .setFontFamily('Meiryo')
       .setFontSize(11)
       .setHorizontalAlignment('center')
       .setVerticalAlignment('middle');

  sheet.getRange(DATA_START, COL.recMemo, dataRows, COL.recFlag - COL.recMemo + 1)
       .setHorizontalAlignment('left');

  sheet.getRange(DATA_START, COL.recDate,  dataRows, 1).setNumberFormat('yyyy/MM/dd');
  sheet.getRange(DATA_START, COL.recStart, dataRows, 1).setNumberFormat('HH:mm');
  sheet.getRange(DATA_START, COL.recEnd,   dataRows, 1).setNumberFormat('HH:mm');
  sheet.getRange(DATA_START, COL.recHours, dataRows, 1).setNumberFormat('[h]:mm');

  try { SpreadsheetApp.getUi().alert('稼働記録の書式を適用しました。'); } catch(e) {}
}

/** 新規追加行に統一フォーマットを適用 */
function _formatRecordRow(sheet, rowNum) {
  const range = sheet.getRange(rowNum, 1, 1, COL.recFlag);
  range.setBackground('#181839')
       .setFontColor('#ffffff')
       .setFontFamily('Meiryo')
       .setFontSize(11)
       .setHorizontalAlignment('center')
       .setVerticalAlignment('middle');
  sheet.getRange(rowNum, COL.recMemo, 1, COL.recFlag - COL.recMemo + 1)
       .setHorizontalAlignment('left');
}

// ============================================================
// 内部ヘルパー
// ============================================================

/** メールアドレスから秘書名を取得（行形式担当マスター対応） */
function _getSecName(email) {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET.master);
  const rows  = sheet.getDataRange().getValues();
  for (let i = 2; i < rows.length; i++) {
    if (String(rows[i][COL.masterEmail - 1]).trim() === email) {
      return String(rows[i][COL.masterSecName - 1]).trim();
    }
  }
  return null;
}

/** 稼働終了時刻をDate型で記録（日またぎ対応） */
function _setEndTime(sheet, rowIndex, jst) {
  sheet.getRange(rowIndex, COL.recEnd).setValue(jst).setNumberFormat('HH:mm');
}

function _toJST(date) {
  return new Date(date.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }));
}

/** 時刻値をHH:mm文字列に変換（Date型・シリアル値・文字列すべて対応） */
function _formatTime(val) {
  if (val === '' || val === null || val === undefined) return '';
  if (val instanceof Date) return Utilities.formatDate(val, 'Asia/Tokyo', 'HH:mm');
  if (typeof val === 'number') {
    if (val > 1) {
      // フルdatetimeシリアル値（startWork でDate型保存した場合）
      return Utilities.formatDate(new Date((val - 25569) * 86400000), 'Asia/Tokyo', 'HH:mm');
    } else if (val >= 0) {
      // 純粋な時刻フラクション（旧形式の互換処理）
      const totalMin = Math.round(val * 24 * 60);
      const h = Math.floor(totalMin / 60);
      const m = totalMin % 60;
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    }
  }
  return String(val);
}

/** 日付値をyyyy/MM/dd文字列に変換（シリアル値対応） */
function _parseDateValue(val) {
  if (!val) return '';
  if (val instanceof Date) return Utilities.formatDate(val, 'Asia/Tokyo', 'yyyy/MM/dd');
  if (typeof val === 'number' && val > 0) {
    return Utilities.formatDate(new Date((val - 25569) * 86400000), 'Asia/Tokyo', 'yyyy/MM/dd');
  }
  return String(val).trim();
}

function _getRecords(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < DATA_START) return [];
  const data = sheet.getRange(DATA_START, 1, lastRow - DATA_START + 1, COL.recNote).getValues();
  return data.map((r, i) => ({
    rowIndex : DATA_START + i,
    date     : _parseDateValue(r[COL.recDate    - 1]),
    secName  : String(r[COL.recSecName - 1]).trim(),
    email    : String(r[COL.recEmail   - 1]).trim(),
    client   : String(r[COL.recClient  - 1]).trim(),
    start    : _formatTime(r[COL.recStart  - 1]),
    end      : _formatTime(r[COL.recEnd    - 1]),
    hours    : _parseHours(r[COL.recHours  - 1]),
    memo     : r[COL.recMemo - 1],
    note     : r[COL.recNote - 1],
  })).filter(r => r.secName !== '' && r.secName !== '秘書名');
}

function _parseHours(val) {
  if (!val) return 0;
  if (typeof val === 'number') return val * 24 * 3600 * 1000;
  if (val instanceof Date) return (val.getHours() * 3600 + val.getMinutes() * 60) * 1000;
  return 0;
}

function _msToHHMM(ms) {
  const totalMin = Math.floor(ms / 60000);
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return `${h}:${String(m).padStart(2, '0')}`;
}

/** 顧客・秘書マスターから全秘書名リストを取得 */
function _getAllSecNames(ss) {
  const sheet = ss.getSheetByName(SHEET.clientSec);
  if (!sheet) return [];
  const data  = sheet.getDataRange().getValues();
  const names = [];
  for (let i = 2; i < data.length; i++) {
    const name = String(data[i][COL.csSecName - 1]).trim();
    if (name && !name.startsWith('※')) names.push(name);
  }
  return names;
}

function _buildClientRateMap(ss) {
  const sheet = ss.getSheetByName(SHEET.clientSec);
  if (!sheet) return {};
  const data  = sheet.getDataRange().getValues();
  const map   = {};
  for (let i = 2; i < data.length; i++) {
    const cliName  = String(data[i][COL.csCliName  - 1]).trim();
    const plan     = String(data[i][COL.csPlan     - 1]).trim();
    const fee      = Number(data[i][COL.csFee      - 1]);
    const limitH   = Number(data[i][COL.csLimitH   - 1]);
    const overRate = Number(data[i][COL.csOverRate - 1]);
    let   from     = data[i][COL.csFrom - 1];
    if (!cliName || cliName.startsWith('※')) continue;
    from = (from instanceof Date)
      ? Utilities.formatDate(from, 'Asia/Tokyo', 'yyyy/MM')
      : String(from).trim();
    if (!map[cliName]) map[cliName] = [];
    map[cliName].push({ plan, fee, limitH, overRate, from });
  }
  return map;
}

function _getClientRate(rateMap, clientName, month) {
  const entries = rateMap[clientName];
  if (!entries || entries.length === 0) return null;
  let defaultEntry = null;
  let bestEntry    = null;
  entries.forEach(e => {
    if (!e.from) {
      defaultEntry = e;
    } else if (e.from <= month) {
      if (!bestEntry || e.from > bestEntry.from) bestEntry = e;
    }
  });
  return bestEntry || defaultEntry || null;
}

function _buildSecRateMap(ss) {
  const sheet = ss.getSheetByName(SHEET.clientSec);
  if (!sheet) return {};
  const data  = sheet.getDataRange().getValues();
  const map   = {};
  for (let i = 2; i < data.length; i++) {
    const secName = String(data[i][COL.csSecName  - 1]).trim();
    const email   = String(data[i][COL.csSecEmail - 1]).trim();
    const rate    = Number(data[i][COL.csSecRate  - 1]);
    let   from    = data[i][COL.csSecFrom - 1];
    if (!secName || secName.startsWith('※')) continue;
    from = (from instanceof Date)
      ? Utilities.formatDate(from, 'Asia/Tokyo', 'yyyy/MM')
      : String(from).trim();
    if (!map[secName]) map[secName] = [];
    map[secName].push({ email, rate, from });
  }
  return map;
}

function _getSecRate(secRateMap, secName, month) {
  const entries = secRateMap[secName];
  if (!entries || entries.length === 0) return null;
  let defaultEntry = null;
  let bestEntry    = null;
  entries.forEach(e => {
    if (!e.from) {
      defaultEntry = e;
    } else if (e.from <= month) {
      if (!bestEntry || e.from > bestEntry.from) bestEntry = e;
    }
  });
  return bestEntry || defaultEntry || null;
}
