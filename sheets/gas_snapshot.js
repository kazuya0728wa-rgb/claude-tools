// ============================================================
// 月次ランキング スナップショット GASコード
// 使い方:
//   1. このコードをApps Scriptエディタに貼り付ける
//   2. createAllSnapshots2026() を一度実行 → 2026年の全月シートを作成
//   3. setMonthlyTrigger() を一度実行 → 以降は毎月1日に自動作成
// ============================================================

/**
 * 指定月のランキングスナップショットシートを作成する
 * @param {number} year  - 例: 2026
 * @param {number} month - 例: 2 (2月)
 */
function createMonthlySnapshot(year, month) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetName = year + '-' + String(month).padStart(2, '0');

  // 既に存在する場合はスキップ
  if (ss.getSheetByName(sheetName)) {
    Logger.log('既に存在します: ' + sheetName);
    return;
  }

  // 月次ランキング_表示 をコピー（デザイン・書式を完全引き継ぎ）
  const sourceSheet = ss.getSheetByName('月次ランキング_表示');
  if (!sourceSheet) {
    Logger.log('ERROR: 月次ランキング_表示 シートが見つかりません');
    return;
  }

  const newSheet = sourceSheet.copyTo(ss);
  newSheet.setName(sheetName);

  // 位置を調整（月次ランキング_表示 の直後に配置）
  const sourceIndex = sourceSheet.getIndex(); // 1-based
  ss.setActiveSheet(newSheet);
  ss.moveActiveSheet(sourceIndex + 1);

  // A6の数式を対象月に固定（動的な EOMONTH(TODAY(),-1)+1 → DATE(year,month,1) に置換）
  const rangeA6 = newSheet.getRange('A6');
  const formula = rangeA6.getFormula();
  const fixedFormula = formula.replace(
    /EOMONTH\(TODAY\(\),-1\)\+1/,
    'DATE(' + year + ',' + month + ',1)'
  );
  rangeA6.setFormula(fixedFormula);

  // シートを非表示にしたい場合はコメントを外す
  // newSheet.hideSheet();

  Logger.log('作成完了: ' + sheetName);
  SpreadsheetApp.flush();
}

/**
 * 2026年の全月スナップショットを作成する（今月分は除く）
 * 一度だけ手動で実行してください。
 */
function createAllSnapshots2026() {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1; // 1-based

  for (let month = 1; month <= 12; month++) {
    // 現在進行中の月以降はスキップ（まだ完結していない）
    if (2026 > currentYear) {
      // 2026年が過去年の場合は全月作成
    } else if (2026 === currentYear && month >= currentMonth) {
      Logger.log('スキップ（未完結）: 2026-' + String(month).padStart(2, '0'));
      continue;
    }

    createMonthlySnapshot(2026, month);
    Utilities.sleep(1500); // レート制限対策
  }

  Logger.log('=== 2026年 全スナップショット作成完了 ===');
}

/**
 * 毎月1日に自動実行するトリガーを設定する
 * 一度だけ手動で実行してください。
 */
function setMonthlyTrigger() {
  // 既存の monthlyAutoSnapshot トリガーを削除（重複防止）
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'monthlyAutoSnapshot') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  // 毎月1日 0:00〜1:00 に実行
  ScriptApp.newTrigger('monthlyAutoSnapshot')
    .timeBased()
    .onMonthDay(1)
    .atHour(0)
    .create();

  Logger.log('月次トリガーを設定しました（毎月1日 0:00〜1:00）');
}

/**
 * 毎月1日に自動実行される関数
 * 前月のスナップショットを作成する
 */
function monthlyAutoSnapshot() {
  const now = new Date();
  // 前月を計算
  const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const year = prevMonth.getFullYear();
  const month = prevMonth.getMonth() + 1;

  Logger.log('月次自動スナップショット開始: ' + year + '-' + String(month).padStart(2, '0'));
  createMonthlySnapshot(year, month);
}

// ============================================================
// 既存のonEditトリガー（入力時刻の自動設定）は残すこと
// ============================================================
