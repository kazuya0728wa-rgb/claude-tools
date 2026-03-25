/**
 * 営業管理システム・完全構築スクリプト (Pro版)
 * 作成者: Gemini
 * 更新: Claude Code
 *   - 継続・２回目列追加に伴う列番号修正（P列→Q列）
 *   - Settings シート廃止（月次ランキングは常に前月表示）
 *   - 月次スナップショット機能追加
 *   - 成約管理シート追加（複数成約の決済管理に対応）
 */

const CONFIG = {
  sheetNames: {
    members: 'セールスメンバー',
    report:   '日報提出',
    contract: '成約管理',
    ranking:  '今月のランキング'
  },
  colors: {
    headerBg:   '#ff6d01',
    headerText: '#ffffff',
    rankTop:    '#fff2cc',
    rankNormal: '#fff2cc',
    border:     '#000000'
  },
  columns: {
    reportTimestamp: 14, // N列（K・O・P列削除後）
    reportRef: {
      wins:   'G',  // 成約数
      deals:  'D',  // 商談数
      cancel: 'E',  // キャンセル・不着席
      loss:   'I'   // 損切数
    },
    contractRef: {
      sales: 'E'    // 今回決済金額（成約管理シート）
    }
  }
};

// ============================================================
// Web App（日報提出フォーム）
// ============================================================

function doGet() {
  return HtmlService.createHtmlOutputFromFile('フォーム')
    .setTitle('日報提出')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** フォームの初期データ（メンバー一覧・案件名一覧）をクライアントに返す */
function getFormData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const memberSheet = ss.getSheetByName(CONFIG.sheetNames.members);
  const rows = memberSheet.getRange('A2:D').getValues();
  const members = rows
    .filter(r => r[0] && r[2] === '稼働')
    .map(r => String(r[0]));
  const cases = rows
    .map(r => String(r[3] || '').trim())
    .filter(v => v !== '');
  return { members, cases };
}

/**
 * フォームの送信データをシートに書き込む
 * data.contracts: [{caseName, payMethod, payAmount, totalAmount, paidRemain, remainDate}]
 */
function submitReport(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const reportSheet   = ss.getSheetByName(CONFIG.sheetNames.report);
  const contractSheet = ss.getSheetByName(CONFIG.sheetNames.contract);

  // 成約の合計金額を集計（日報提出L/M列用）
  const contracts = data.contracts || [];
  const totalPay   = contracts.reduce(function(s, c) { return s + Number(c.payAmount   || 0); }, 0);
  const totalGoods = contracts.reduce(function(s, c) { return s + Number(c.totalAmount || 0); }, 0);

  // 日報提出シート（活動サマリー・15列構成）
  const reportRow = [
    data.date,                       // A: 日付
    data.name,                       // B: 氏名
    data.caseNames || '',            // C: 案件名
    Number(data.deals   || 0),       // D: 商談数
    Number(data.cancel  || 0),       // E: キャンセル・不着席
    Number(data.repeat  || 0),       // F: 継続・２回目
    Number(data.wins    || 0),       // G: 成約数
    Number(data.losses  || 0),       // H: 失注数
    Number(data.cuts    || 0),       // I: 損切数
    data.lossReason || '',           // J: 失注理由/録画URL
    totalPay,                        // K: 今回決済金額（成約合計）
    totalGoods,                      // L: 商品総額（成約合計）
    '',                              // M: 残額（ARRAYFORMULA）
    new Date(),                      // N: 入力時刻（自動）
    data.memo || '',                 // O: メモ
  ];
  reportSheet.getRange(firstEmptyRowInA(reportSheet), 1, 1, reportRow.length).setValues([reportRow]);

  // 成約管理シート（成約ごとに1行）
  contracts.forEach(function(c) {
    if (!c.caseName && !Number(c.payAmount) && !Number(c.totalAmount)) return;
    const contractRow = [
      data.date,                     // A: 日付
      data.name,                     // B: 氏名
      c.caseName     || '',          // C: 案件名
      c.payMethod    || '',          // D: 決済方法
      Number(c.payAmount   || 0),   // E: 今回決済金額
      Number(c.totalAmount || 0),   // F: 商品総額
      '',                            // G: 残額（ARRAYFORMULA）
      false,                         // H: 残額決済済
      c.remainDate   || '',          // I: 残額決済期限
      new Date(),                    // J: 入力時刻（自動）
    ];
    contractSheet.getRange(firstEmptyRowInA(contractSheet), 1, 1, contractRow.length).setValues([contractRow]);
  });

  return { success: true };
}

// ============================================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🏆ランキング管理')
    .addItem('▶ システム完全構築（リセット）', 'setupSystem')
    .addToUi();
}

/**
 * メイン実行関数
 */
function setupSystem() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetTimeZone('Asia/Tokyo');

  setupMemberSheet(ss);
  setupReportSheet(ss);
  setupContractSheet(ss);
  setupRankingSheet(ss);
  setupTriggers(ss);

  Browser.msgBox('✅ システム構築完了');
}

// ----------------------------------------------------
// 1. メンバー管理シート
// ----------------------------------------------------
function setupMemberSheet(ss) {
  const sheet = getOrCreateSheet(ss, CONFIG.sheetNames.members);
  const headers = ['氏名', '稼働開始日', '状態', '案件名'];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers])
    .setBackground(CONFIG.colors.headerBg).setFontColor('white').setFontWeight('bold');
  sheet.getRange('C2:C1000').setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(['稼働', '休止'], true)
      .build()
  );
  sheet.getRange('B:B').setNumberFormat('yyyy/MM/dd');
}

// ----------------------------------------------------
// 2. 日報シート
// ----------------------------------------------------
function setupReportSheet(ss) {
  const sheet = getOrCreateSheet(ss, CONFIG.sheetNames.report);

  const headers = [
    '日付', '氏名', '案件/会社名', '商談数', 'キャンセル・不着席',
    '継続・２回目', '成約数', '失注数', '損切数', '失注理由/録画URL',
    '今回決済金額', '商品総額', '残額(自動)',
    '入力時刻(自動)', 'メモ'
  ]; // A〜O列（全15列）

  sheet.getRange(1, 1, 1, headers.length).setValues([headers])
    .setBackground(CONFIG.colors.headerBg).setFontColor('white').setFontWeight('bold');
  sheet.setFrozenRows(1);

  const memberSheet = ss.getSheetByName(CONFIG.sheetNames.members);
  const nameRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(memberSheet.getRange('A2:A'), true)
    .build();
  sheet.getRange('B2:B').setDataValidation(nameRule);

  sheet.getRange('A:A').setNumberFormat('yyyy/MM/dd');
  sheet.getRange('K:M').setNumberFormat('#,##0');
  sheet.getRange('N:N').setNumberFormat('yyyy/MM/dd HH:mm:ss');
}

// ----------------------------------------------------
// 3. 成約管理シート（新規）
// ----------------------------------------------------
function setupContractSheet(ss) {
  const sheet = getOrCreateSheet(ss, CONFIG.sheetNames.contract);

  const headers = [
    '日付', '氏名', '案件名', '決済方法',
    '今回決済金額', '商品総額', '残額(自動)', '残額決済済', '残額決済期限',
    '入力時刻(自動)'
  ]; // A〜J列（全10列）

  sheet.getRange(1, 1, 1, headers.length).setValues([headers])
    .setBackground(CONFIG.colors.headerBg).setFontColor('white').setFontWeight('bold');
  sheet.setFrozenRows(1);

  const memberSheet = ss.getSheetByName(CONFIG.sheetNames.members);
  const nameRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(memberSheet.getRange('A2:A'), true)
    .build();
  sheet.getRange('B2:B').setDataValidation(nameRule);

  // 残額計算式（G列 = 商品総額F - 今回決済金額E）
  sheet.getRange('G2:G').clearContent();
  sheet.getRange('G2').setFormula(
    '=ARRAYFORMULA(IF(F2:F="", "", IF(F2:F-E2:E<0, 0, F2:F-E2:E)))'
  );

  sheet.getRange('H2:H').setDataValidation(
    SpreadsheetApp.newDataValidation().requireCheckbox().build()
  );

  sheet.getRange('A:A').setNumberFormat('yyyy/MM/dd');
  sheet.getRange('E:G').setNumberFormat('#,##0');
  sheet.getRange('I:I').setNumberFormat('yyyy/MM/dd');
  sheet.getRange('J:J').setNumberFormat('yyyy/MM/dd HH:mm:ss');
}

// ----------------------------------------------------
// 4. ランキングシート
// ----------------------------------------------------
function setupRankingSheet(ss) {
  const sheet = getOrCreateSheet(ss, CONFIG.sheetNames.ranking);
  sheet.clear();
  sheet.setHiddenGridlines(true);

  sheet.getRange('A1:F3').merge().setValue('🏆 月次 セールスランキング 🏆')
    .setBackground('#ff4500').setFontColor('white').setFontSize(24).setFontWeight('bold')
    .setHorizontalAlignment('center').setVerticalAlignment('middle');

  const headerLabels = [['順位', '氏名', '売上', '商談数', '成約数', '成約率']];
  sheet.getRange('A6:F6').setValues(headerLabels)
    .setBackground(CONFIG.colors.headerBg).setFontColor('white').setFontWeight('bold')
    .setHorizontalAlignment('center');

  const col = CONFIG.columns.reportRef;
  const cCol = CONFIG.columns.contractRef;
  const formula = `=LET(
    対象月, EOMONTH(TODAY(),-1)+1,
    開始日, 対象月,
    終了日, EOMONTH(対象月, 0),

    メンバー名, '${CONFIG.sheetNames.members}'!A2:A,
    状態, '${CONFIG.sheetNames.members}'!C2:C,
    稼働メンバー, FILTER(メンバー名, 状態="稼働"),

    日報日付, '${CONFIG.sheetNames.report}'!A2:A,
    日報氏名, '${CONFIG.sheetNames.report}'!B2:B,
    日報商談, '${CONFIG.sheetNames.report}'!${col.deals}2:${col.deals},
    日報キャンセル, '${CONFIG.sheetNames.report}'!${col.cancel}2:${col.cancel},
    日報成約, '${CONFIG.sheetNames.report}'!${col.wins}2:${col.wins},
    日報損切, '${CONFIG.sheetNames.report}'!${col.loss}2:${col.loss},

    成約日付, '${CONFIG.sheetNames.contract}'!A2:A,
    成約氏名, '${CONFIG.sheetNames.contract}'!B2:B,
    成約金額, '${CONFIG.sheetNames.contract}'!${cCol.sales}2:${cCol.sales},

    集計データ,
      MAP(稼働メンバー,
        LAMBDA(氏名,
          LET(
            売上,
              SUMIFS(成約金額, 成約氏名, 氏名,
                     成約日付, ">="&開始日,
                     成約日付, "<="&終了日),
            商談数,
              SUMIFS(日報商談, 日報氏名, 氏名,
                     日報日付, ">="&開始日,
                     日報日付, "<="&終了日)
              - SUMIFS(日報損切, 日報氏名, 氏名,
                     日報日付, ">="&開始日,
                     日報日付, "<="&終了日)
              - SUMIFS(日報キャンセル, 日報氏名, 氏名,
                     日報日付, ">="&開始日,
                     日報日付, "<="&終了日),
            成約数,
              SUMIFS(日報成約, 日報氏名, 氏名,
                     日報日付, ">="&開始日,
                     日報日付, "<="&終了日),
            成約率, IFERROR(成約数/商談数, 0),
            HSTACK(氏名, 売上, 商談数, 成約数, 成約率)
          )
        )
      ),

    並び替え, SORT(集計データ, 2, FALSE, 5, FALSE),
    順位, SEQUENCE(ROWS(並び替え)),

    IFERROR(HSTACK(順位, 並び替え), "データなし")
  )`;

  sheet.getRange('A7').setFormula(formula);
}

/** A列で最初に空白になっている行番号を返す（ヘッダー行=1 を除く） */
function firstEmptyRowInA(sheet) {
  var vals = sheet.getRange('A2:A' + Math.max(sheet.getLastRow() + 1, 2)).getValues();
  for (var i = 0; i < vals.length; i++) {
    if (vals[i][0] === '' || vals[i][0] === null) return i + 2;
  }
  return vals.length + 2;
}

function getOrCreateSheet(ss, name) {
  let s = ss.getSheetByName(name);
  return s ? s : ss.insertSheet(name);
}

// ----------------------------------------------------
// トリガー（入力時刻の自動設定）
// ----------------------------------------------------
function setupTriggers(ss) {
  if (!ss) ss = SpreadsheetApp.getActiveSpreadsheet();
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'onEditTimestamp') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('onEditTimestamp').forSpreadsheet(ss).onEdit().create();
}

function onEditTimestamp(e) {
  if (!e) return;
  const sheet = e.range.getSheet();
  const sheetName = sheet.getName();

  // 日報提出シート：Q列（17列目）にタイムスタンプ
  if (sheetName === CONFIG.sheetNames.report) {
    const row = e.range.getRow();
    if (row < 2) return;
    const dateVal = sheet.getRange(row, 1).getValue();
    const nameVal = sheet.getRange(row, 2).getValue();
    const timeCell = sheet.getRange(row, CONFIG.columns.reportTimestamp);
    if (dateVal && nameVal && timeCell.getValue() === '') {
      timeCell.setValue(new Date());
    }
  }

  // 成約管理シート：J列（10列目）にタイムスタンプ
  if (sheetName === CONFIG.sheetNames.contract) {
    const row = e.range.getRow();
    if (row < 2) return;
    const dateVal = sheet.getRange(row, 1).getValue();
    const nameVal = sheet.getRange(row, 2).getValue();
    const timeCell = sheet.getRange(row, 10);
    if (dateVal && nameVal && timeCell.getValue() === '') {
      timeCell.setValue(new Date());
    }
  }
}

// ============================================================
// 月次スナップショット機能
// ============================================================

/**
 * 指定月のランキングスナップショットシートを作成する
 * @param {number} year  - 例: 2026
 * @param {number} month - 例: 2
 */
function createMonthlySnapshot(year, month) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetName = year + '-' + String(month).padStart(2, '0');

  if (ss.getSheetByName(sheetName)) {
    Logger.log('既に存在します: ' + sheetName);
    return;
  }

  const sourceSheet = ss.getSheetByName(CONFIG.sheetNames.ranking);
  if (!sourceSheet) {
    Logger.log('ERROR: ' + CONFIG.sheetNames.ranking + ' が見つかりません');
    return;
  }

  // デザイン・書式を完全引き継ぎしてコピー
  const newSheet = sourceSheet.copyTo(ss);
  newSheet.setName(sheetName);

  // 月次ランキング_表示 の直後に配置
  const sourceIndex = sourceSheet.getIndex();
  ss.setActiveSheet(newSheet);
  ss.moveActiveSheet(sourceIndex + 1);

  // A6の数式を対象月に固定（EOMONTH(TODAY(),-1)+1 → DATE(year,month,1)）
  const rangeA6 = newSheet.getRange('A6');
  const formula = rangeA6.getFormula();
  const fixedFormula = formula.replace(
    /EOMONTH\(TODAY\(\),-1\)\+1/,
    'DATE(' + year + ',' + month + ',1)'
  );
  rangeA6.setFormula(fixedFormula);

  Logger.log('作成完了: ' + sheetName);
  SpreadsheetApp.flush();
}

/**
 * 2026年の全月スナップショットを作成する（今月分は除く）
 * メニュー「📚 2026年全月スナップショット作成」から実行してください。
 */
function createAllSnapshots2026() {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  for (let month = 1; month <= 12; month++) {
    if (2026 === currentYear && month >= currentMonth) {
      Logger.log('スキップ（未完結）: 2026-' + String(month).padStart(2, '0'));
      continue;
    }
    createMonthlySnapshot(2026, month);
    Utilities.sleep(1500);
  }

  Logger.log('=== 2026年 全スナップショット作成完了 ===');
  Browser.msgBox('✅ 2026年スナップショット作成完了');
}

/**
 * 毎月1日に自動実行するトリガーを設定する
 * メニュー「⏰ 月次自動トリガー設定」から一度だけ実行してください。
 */
function setMonthlyTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'monthlyAutoSnapshot') {
      ScriptApp.deleteTrigger(t);
    }
  });

  ScriptApp.newTrigger('monthlyAutoSnapshot')
    .timeBased()
    .onMonthDay(1)
    .atHour(0)
    .create();

  Browser.msgBox('✅ 月次トリガーを設定しました\n毎月1日に前月分のスナップショットを自動作成します。');
}

/**
 * 毎月1日に自動実行される関数（前月のスナップショットを作成）
 */
function monthlyAutoSnapshot() {
  const now = new Date();
  const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  createMonthlySnapshot(prevMonth.getFullYear(), prevMonth.getMonth() + 1);
}
