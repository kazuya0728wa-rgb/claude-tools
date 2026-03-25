/**
 * スリーンク 統合管理ツール
 * Google Apps Script メインコード
 */

// =====================================================
// 設定
// =====================================================

const CONFIG = {
  sheetNames: {
    requester: '依頼者マスター',
    customer:  '顧客マスター',
    genre:     'ジャンルマスター',
    case:      '案件テーブル',
    delivery:  '成果物テーブル',
    invoice:   '依頼者請求テーブル',
  },
  caseStatus: {
    ordering:   '発注中',
    waiting:    '納品待ち',
    reviewing:  '承認待ち',
    invoicing:  '請求待ち',
    paying:     '支払待ち',
    paid:       '支払済み',
  },
  // 案件テーブルの列インデックス（1始まり）
  caseColumns: {
    id:          1,   // A: 案件番号
    reqId:       2,   // B: 依頼者番号
    reqName:     3,   // C: 依頼者LINE名
    cusId:       4,   // D: 顧客番号
    cusName:     5,   // E: 顧客名
    genreId:     6,   // F: ジャンル番号
    genreName:   7,   // G: ジャンル名
    detail:      8,   // H: 案件詳細
    orderDate:   9,   // I: 発注日
    dueDate:     10,  // J: 納品希望日
    estimated:   11,  // K: 予想費用
    status:      12,  // L: 状態
    lineMsg:     13,  // M: LINE文章
    deliveryUrl: 14,  // N: 成果物URL
    createdAt:   15,  // O: 登録日時
  },
};

// =====================================================
// カスタムメニュー
// =====================================================

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📋 スリーンク管理')
    .addItem('案件発注フォームを開く', 'openOrderForm')
    .addSeparator()
    .addItem('選択行のLINE文章を再生成', 'regenerateLineMessage')
    .addItem('選択行の案件番号を再生成', 'regenerateCaseId')
    .addSeparator()
    .addItem('WebAppを開く', 'openWebApp')
    .addToUi();
}

function openOrderForm() {
  const url = ScriptApp.getService().getUrl();
  if (!url) {
    SpreadsheetApp.getUi().alert('WebAppがデプロイされていません。\n拡張機能→Apps Script→デプロイからWebAppをデプロイしてください。');
    return;
  }
  const html = HtmlService.createHtmlOutput(
    `<script>window.open('${url}?page=order','_blank');google.script.host.close();</script>`
  );
  SpreadsheetApp.getUi().showModalDialog(html, '案件発注フォーム');
}

function openWebApp() {
  const url = ScriptApp.getService().getUrl();
  if (!url) {
    SpreadsheetApp.getUi().alert('WebAppがデプロイされていません。');
    return;
  }
  const html = HtmlService.createHtmlOutput(
    `<script>window.open('${url}','_blank');google.script.host.close();</script>`
  );
  SpreadsheetApp.getUi().showModalDialog(html, 'WebApp');
}

// =====================================================
// 案件番号・LINE文章の自動生成（onEdit トリガー）
// =====================================================

function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  if (sheet.getName() !== CONFIG.sheetNames.case) return;

  const row = e.range.getRow();
  if (row < 2) return; // ヘッダーをスキップ

  const col = e.range.getColumn();
  const c = CONFIG.caseColumns;

  // 依頼者番号・顧客番号・ジャンル番号・発注日・予想費用 のいずれかが変更されたら再生成
  const triggerCols = [c.reqId, c.cusId, c.genreId, c.orderDate, c.estimated];
  if (!triggerCols.includes(col)) return;

  // 必要な値を取得
  const rowData = sheet.getRange(row, 1, 1, 15).getValues()[0];
  const reqId    = rowData[c.reqId - 1];
  const cusId    = rowData[c.cusId - 1];
  const genreId  = rowData[c.genreId - 1];
  const orderDate = rowData[c.orderDate - 1];
  const estimated = rowData[c.estimated - 1];

  if (!reqId || !cusId || !genreId || !orderDate || !estimated) return;

  // マスターから名前を取得して自動入力
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const reqName = lookupName(ss, CONFIG.sheetNames.requester, reqId);
  const cusName = lookupName(ss, CONFIG.sheetNames.customer, cusId);
  const genreName = lookupName(ss, CONFIG.sheetNames.genre, genreId);

  if (reqName) sheet.getRange(row, c.reqName).setValue(reqName);
  if (cusName) sheet.getRange(row, c.cusName).setValue(cusName);
  if (genreName) sheet.getRange(row, c.genreName).setValue(genreName);

  // 案件番号を生成
  const caseId = buildCaseId(reqId, cusId, genreId, orderDate, estimated);
  sheet.getRange(row, c.id).setValue(caseId);

  // 状態が空なら「発注中」をセット
  if (!rowData[c.status - 1]) {
    sheet.getRange(row, c.status).setValue(CONFIG.caseStatus.ordering);
  }

  // 登録日時をセット
  if (!rowData[c.createdAt - 1]) {
    sheet.getRange(row, c.createdAt).setValue(new Date());
  }

  // LINE文章を生成
  const detail = rowData[c.detail - 1] || '';
  const dueDate = rowData[c.dueDate - 1] || '';
  const lineMsg = buildLineMessage(caseId, reqName, cusName, genreName, detail, orderDate, dueDate, estimated);
  sheet.getRange(row, c.lineMsg).setValue(lineMsg);
}

// =====================================================
// 案件番号生成
// =====================================================

/**
 * 案件番号を生成する
 * フォーマット: {依頼者番号}-{顧客番号}-{ジャンル番号}-{日付YYMMDD}-{金額}
 * 重複する場合は末尾に -2, -3 を付加
 */
function buildCaseId(reqId, cusId, genreId, orderDate, estimated) {
  const dateStr = Utilities.formatDate(new Date(orderDate), 'Asia/Tokyo', 'yyMMdd');
  const amount = Math.round(Number(String(estimated).replace(/[^0-9]/g, '')));
  const base = `${reqId}-${cusId}-${genreId}-${dateStr}-${amount}`;

  // 重複チェック
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const caseSheet = ss.getSheetByName(CONFIG.sheetNames.case);
  const existingIds = caseSheet.getRange('A2:A').getValues().flat().filter(v => v);

  let suffix = 0;
  let candidate = base;
  while (existingIds.includes(candidate)) {
    suffix++;
    candidate = `${base}-${suffix + 1}`;
  }
  return candidate;
}

// =====================================================
// LINE文章生成
// =====================================================

function buildLineMessage(caseId, reqName, cusName, genreName, detail, orderDate, dueDate, estimated) {
  const dateStr = orderDate ? Utilities.formatDate(new Date(orderDate), 'Asia/Tokyo', 'yyyy/MM/dd') : '';
  const dueDateStr = dueDate ? Utilities.formatDate(new Date(dueDate), 'Asia/Tokyo', 'yyyy/MM/dd') : '';
  const amount = Number(String(estimated).replace(/[^0-9]/g, '')).toLocaleString();

  return `【新規案件のご依頼について】

${reqName} さん、お世話になっております。
スリーンクの若松です。

新しい案件についてご依頼させていただきます。

━━━━━━━━━━━━━━━━
案件番号：${caseId}
クライアント：${cusName}
ジャンル：${genreName}
案件内容：${detail}
発注日：${dateStr}
納品希望日：${dueDateStr}
お支払い金額：¥${amount}
━━━━━━━━━━━━━━━━

ご確認の上、承諾いただけますようお願いいたします。
ご不明な点があればお気軽にご連絡ください。

よろしくお願いいたします。`;
}

// =====================================================
// カスタムメニューから手動再生成
// =====================================================

function regenerateCaseId() {
  const sheet = SpreadsheetApp.getActiveSheet();
  if (sheet.getName() !== CONFIG.sheetNames.case) {
    SpreadsheetApp.getUi().alert('案件テーブルを選択してください');
    return;
  }
  const row = sheet.getActiveCell().getRow();
  if (row < 2) return;

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rowData = sheet.getRange(row, 1, 1, 15).getValues()[0];
  const c = CONFIG.caseColumns;

  const reqId    = rowData[c.reqId - 1];
  const cusId    = rowData[c.cusId - 1];
  const genreId  = rowData[c.genreId - 1];
  const orderDate = rowData[c.orderDate - 1];
  const estimated = rowData[c.estimated - 1];

  if (!reqId || !cusId || !genreId || !orderDate || !estimated) {
    SpreadsheetApp.getUi().alert('依頼者番号・顧客番号・ジャンル番号・発注日・予想費用を入力してください');
    return;
  }

  const caseId = buildCaseId(reqId, cusId, genreId, orderDate, estimated);
  sheet.getRange(row, c.id).setValue(caseId);
  SpreadsheetApp.getUi().alert(`案件番号を生成しました: ${caseId}`);
}

function regenerateLineMessage() {
  const sheet = SpreadsheetApp.getActiveSheet();
  if (sheet.getName() !== CONFIG.sheetNames.case) {
    SpreadsheetApp.getUi().alert('案件テーブルを選択してください');
    return;
  }
  const row = sheet.getActiveCell().getRow();
  if (row < 2) return;

  const c = CONFIG.caseColumns;
  const rowData = sheet.getRange(row, 1, 1, 15).getValues()[0];

  const caseId   = rowData[c.id - 1];
  const reqName  = rowData[c.reqName - 1];
  const cusName  = rowData[c.cusName - 1];
  const genreName = rowData[c.genreName - 1];
  const detail   = rowData[c.detail - 1] || '';
  const orderDate = rowData[c.orderDate - 1];
  const dueDate  = rowData[c.dueDate - 1] || '';
  const estimated = rowData[c.estimated - 1];

  if (!caseId) {
    SpreadsheetApp.getUi().alert('まず案件番号を生成してください');
    return;
  }

  const lineMsg = buildLineMessage(caseId, reqName, cusName, genreName, detail, orderDate, dueDate, estimated);
  sheet.getRange(row, c.lineMsg).setValue(lineMsg);
  SpreadsheetApp.getUi().alert('LINE文章を再生成しました');
}

// =====================================================
// ユーティリティ
// =====================================================

function lookupName(ss, sheetName, id) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) return null;
  const data = sheet.getRange('A2:B').getValues();
  for (const row of data) {
    if (String(row[0]) === String(id)) return row[1];
  }
  return null;
}

function getSheetData(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) return [];
  const data = sheet.getDataRange().getValues();
  if (data.length < 2) return [];
  const headers = data[0];
  return data.slice(1).map(row => {
    const obj = {};
    headers.forEach((h, i) => { obj[h] = row[i]; });
    return obj;
  });
}

// =====================================================
// WebApp エントリーポイント
// =====================================================

function doGet(e) {
  const page = (e && e.parameter && e.parameter.page) || 'top';
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle('スリーンク 管理ツール')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const action = data.action;

    if (action === 'registerCase') return handleRegisterCase(data);
    if (action === 'submitDelivery') return handleSubmitDelivery(data);
    if (action === 'getCaseList') return handleGetCaseList(data);
    if (action === 'getFormData') return handleGetFormData();

    return jsonResponse({ success: false, error: `Unknown action: ${action}` });
  } catch (err) {
    return jsonResponse({ success: false, error: err.message });
  }
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// =====================================================
// WebApp ハンドラ
// =====================================================

/** フォームの初期データ（マスター一覧）を返す */
function handleGetFormData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const reqData = ss.getSheetByName(CONFIG.sheetNames.requester)
    .getRange('A2:B').getValues()
    .filter(r => r[0] && r[1])
    .map(r => ({ id: r[0], name: r[1] }));

  const cusData = ss.getSheetByName(CONFIG.sheetNames.customer)
    .getRange('A2:B').getValues()
    .filter(r => r[0] && r[1])
    .map(r => ({ id: r[0], name: r[1] }));

  const genreData = ss.getSheetByName(CONFIG.sheetNames.genre)
    .getRange('A2:B').getValues()
    .filter(r => r[0] && r[1])
    .map(r => ({ id: r[0], name: r[1] }));

  return jsonResponse({ success: true, requesters: reqData, customers: cusData, genres: genreData });
}

/** 案件を登録する */
function handleRegisterCase(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheetNames.case);

  const reqId   = data.requesterId;
  const cusId   = data.customerId;
  const genreId = data.genreId;
  const orderDate = new Date(data.orderDate);
  const estimated = Number(data.estimated);

  // マスターから名前を解決
  const reqName   = lookupName(ss, CONFIG.sheetNames.requester, reqId) || '';
  const cusName   = lookupName(ss, CONFIG.sheetNames.customer, cusId) || '';
  const genreName = lookupName(ss, CONFIG.sheetNames.genre, genreId) || '';

  // 案件番号を生成
  const caseId = buildCaseId(reqId, cusId, genreId, orderDate, estimated);

  // LINE文章を生成
  const dueDate = data.dueDate ? new Date(data.dueDate) : '';
  const lineMsg = buildLineMessage(
    caseId, reqName, cusName, genreName,
    data.detail || '', orderDate, dueDate, estimated
  );

  // 新行を追加
  sheet.appendRow([
    caseId,
    reqId,
    reqName,
    cusId,
    cusName,
    genreId,
    genreName,
    data.detail || '',
    orderDate,
    dueDate || '',
    estimated,
    CONFIG.caseStatus.ordering,
    lineMsg,
    '',  // 成果物URL
    new Date(), // 登録日時
  ]);

  return jsonResponse({ success: true, caseId, lineMsg });
}

/** 成果物を提出する */
function handleSubmitDelivery(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const caseSheet = ss.getSheetByName(CONFIG.sheetNames.case);
  const deliverySheet = ss.getSheetByName(CONFIG.sheetNames.delivery);

  const caseId = data.caseId;
  const deliveryUrl = data.deliveryUrl;
  const comment = data.comment || '';

  // 案件テーブルから該当行を検索
  const caseData = caseSheet.getRange('A2:O').getValues();
  let caseRow = -1;
  let reqId = '';
  let reqName = '';

  for (let i = 0; i < caseData.length; i++) {
    if (String(caseData[i][0]) === String(caseId)) {
      caseRow = i + 2;
      reqId = caseData[i][CONFIG.caseColumns.reqId - 1];
      reqName = caseData[i][CONFIG.caseColumns.reqName - 1];
      break;
    }
  }

  if (caseRow < 0) {
    return jsonResponse({ success: false, error: `案件番号 ${caseId} が見つかりません` });
  }

  // 成果物URLを案件テーブルに記入
  caseSheet.getRange(caseRow, CONFIG.caseColumns.deliveryUrl).setValue(deliveryUrl);

  // 案件状態を「承認待ち」に更新
  caseSheet.getRange(caseRow, CONFIG.caseColumns.status).setValue(CONFIG.caseStatus.reviewing);

  // 成果物テーブルに追記
  const lastId = deliverySheet.getLastRow() < 2 ? 1 :
    (Number(deliverySheet.getRange(deliverySheet.getLastRow(), 1).getValue()) || 0) + 1;

  deliverySheet.appendRow([
    lastId,
    caseId,
    new Date(),
    reqId,
    reqName,
    deliveryUrl,
    comment,
  ]);

  return jsonResponse({ success: true, message: '成果物を提出しました。承認をお待ちください。' });
}

/** 案件一覧を取得する（依頼者フィルタ対応） */
function handleGetCaseList(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheetNames.case);
  const allData = sheet.getRange('A2:O').getValues();
  const c = CONFIG.caseColumns;

  const filterReqId = data.requesterId ? String(data.requesterId) : null;

  const cases = allData
    .filter(row => row[0] && (!filterReqId || String(row[c.reqId - 1]) === filterReqId))
    .map(row => ({
      caseId:      row[c.id - 1],
      requesterId: row[c.reqId - 1],
      requesterName: row[c.reqName - 1],
      customerId:  row[c.cusId - 1],
      customerName: row[c.cusName - 1],
      genreId:     row[c.genreId - 1],
      genreName:   row[c.genreName - 1],
      detail:      row[c.detail - 1],
      orderDate:   row[c.orderDate - 1] ? Utilities.formatDate(new Date(row[c.orderDate - 1]), 'Asia/Tokyo', 'yyyy/MM/dd') : '',
      dueDate:     row[c.dueDate - 1] ? Utilities.formatDate(new Date(row[c.dueDate - 1]), 'Asia/Tokyo', 'yyyy/MM/dd') : '',
      estimated:   row[c.estimated - 1],
      status:      row[c.status - 1],
      deliveryUrl: row[c.deliveryUrl - 1],
    }));

  return jsonResponse({ success: true, cases });
}

// =====================================================
// google.script.run から呼び出す関数群（クライアント向け）
// =====================================================

/** フォームの初期データを返す（google.script.run用） */
function getFormDataForClient() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    const reqData = ss.getSheetByName(CONFIG.sheetNames.requester)
      .getRange('A2:B').getValues()
      .filter(r => r[0] && r[1])
      .map(r => ({ id: String(r[0]), name: String(r[1]) }));

    const cusData = ss.getSheetByName(CONFIG.sheetNames.customer)
      .getRange('A2:B').getValues()
      .filter(r => r[0] && r[1])
      .map(r => ({ id: String(r[0]), name: String(r[1]) }));

    const genreData = ss.getSheetByName(CONFIG.sheetNames.genre)
      .getRange('A2:B').getValues()
      .filter(r => r[0] && r[1])
      .map(r => ({ id: String(r[0]), name: String(r[1]) }));

    return { success: true, requesters: reqData, customers: cusData, genres: genreData };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

/** 案件を登録する（google.script.run用） */
function registerCaseFromWeb(requesterId, customerId, genreId, detail, orderDate, dueDate, estimated) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(CONFIG.sheetNames.case);

    const reqName   = lookupName(ss, CONFIG.sheetNames.requester, requesterId) || '';
    const cusName   = lookupName(ss, CONFIG.sheetNames.customer, customerId) || '';
    const genreName = lookupName(ss, CONFIG.sheetNames.genre, genreId) || '';

    const orderDateObj = new Date(orderDate);
    const dueDateObj   = dueDate ? new Date(dueDate) : '';
    const amount       = Number(estimated);

    const caseId = buildCaseId(requesterId, customerId, genreId, orderDateObj, amount);
    const lineMsg = buildLineMessage(caseId, reqName, cusName, genreName, detail, orderDateObj, dueDateObj, amount);

    sheet.appendRow([
      caseId, requesterId, reqName, customerId, cusName,
      genreId, genreName, detail,
      orderDateObj, dueDateObj || '',
      amount, CONFIG.caseStatus.ordering,
      lineMsg, '', new Date(),
    ]);

    return { success: true, caseId, lineMsg };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

/** 成果物を提出する（google.script.run用） */
function submitDeliveryFromWeb(caseId, deliveryUrl, comment) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const caseSheet = ss.getSheetByName(CONFIG.sheetNames.case);
    const deliverySheet = ss.getSheetByName(CONFIG.sheetNames.delivery);

    const caseData = caseSheet.getRange('A2:O').getValues();
    let caseRow = -1, reqId = '', reqName = '';

    for (let i = 0; i < caseData.length; i++) {
      if (String(caseData[i][0]) === String(caseId)) {
        caseRow = i + 2;
        reqId   = caseData[i][CONFIG.caseColumns.reqId - 1];
        reqName = caseData[i][CONFIG.caseColumns.reqName - 1];
        break;
      }
    }

    if (caseRow < 0) return { success: false, error: `案件番号 ${caseId} が見つかりません` };

    caseSheet.getRange(caseRow, CONFIG.caseColumns.deliveryUrl).setValue(deliveryUrl);
    caseSheet.getRange(caseRow, CONFIG.caseColumns.status).setValue(CONFIG.caseStatus.reviewing);

    const lastRow = deliverySheet.getLastRow();
    const nextId  = lastRow < 2 ? 1 : (Number(deliverySheet.getRange(lastRow, 1).getValue()) || 0) + 1;
    deliverySheet.appendRow([nextId, caseId, new Date(), reqId, reqName, deliveryUrl, comment || '']);

    return { success: true, message: '成果物を提出しました。管理者の承認をお待ちください。' };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

/** 案件一覧を取得する（google.script.run用） */
function getCaseListForClient(filterRequesterId) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(CONFIG.sheetNames.case);
    const allData = sheet.getRange('A2:O').getValues();
    const c = CONFIG.caseColumns;

    const cases = allData
      .filter(row => row[0] && (!filterRequesterId || String(row[c.reqId - 1]) === String(filterRequesterId)))
      .map(row => ({
        caseId:        String(row[c.id - 1]),
        requesterName: String(row[c.reqName - 1]),
        customerName:  String(row[c.cusName - 1]),
        genreName:     String(row[c.genreName - 1]),
        dueDate:       row[c.dueDate - 1] ? Utilities.formatDate(new Date(row[c.dueDate - 1]), 'Asia/Tokyo', 'yyyy/MM/dd') : '',
        status:        String(row[c.status - 1]),
        deliveryUrl:   String(row[c.deliveryUrl - 1]),
      }));

    return { success: true, cases };
  } catch (e) {
    return { success: false, error: e.message };
  }
}
