# ============================================================
# ダウンロードフォルダ 自動分類スクリプト
# 実行頻度: 毎日9時（タスクスケジューラ）
# 対象: Downloads直下のファイルのみ（サブフォルダは触らない）
#
# ==================== 分類ルール ====================
#
# 【削除予定】→ Downloads\_削除予定\ に移動
#   条件（いずれか該当）:
#   - 拡張子が .exe / .msi（ソフトのインストーラー）
#   - 拡張子が .crdownload（ダウンロード途中のファイル）
#   - 拡張子が .webm（Chromeのチュートリアル動画等）
#   - 拡張子が .webp / .gif（一時的にDLした画像）
#   - ファイル名が25文字以上の英数字のみ（Amazonサムネイル等）
#   - ファイル名が13桁以上の数字始まり（タイムスタンプ画像）
#   - ファイル名に "ChatGPT Image" / "Gemini" / "Firefly" を含む
#
# 【就活】→ OneDrive\就活\ に移動
#   条件: ファイル名に以下のいずれかを含む
#   - BCG / ボストン / コンサルティング / ケース面接（→ 就活\BCG\）
#   - 就活 / 選考 / 面接 / エントリーシート（→ 就活\その他\）
#
# 【物販】→ OneDrive\物販\ に移動
#   - 請求書フォルダ: 請求書 / 5-Roses / 3Link / INV- / 合同会社
#   - 領収書フォルダ: 領収書 / receipt
#   - 取引データフォルダ: orders_ / FBA / 入庫 / 保管 / warehousing（CSV/PDF）
#   - マニュアルフォルダ: マニュアル / 仕入 / 納品 / 検品 / keepa / リサーチ / 梱包 / 作業標準
#   - 契約書フォルダ: 契約書 / 委託
#   - 管理シートフォルダ: せどり / 在庫管理
#
# 【インターン】→ OneDrive\インターン\ に移動
#   - 相談会\韓国美容: 韓国 / korea_beauty / 한국 / 미팅
#   - 相談会\ララ: ララ / Lala / LalaBloom
#   - 相談会: クリニック / 相談会 / clinic
#
# 【大学】→ OneDrive\大学\[科目名]\ に移動（2026年春学期）
#   科目ごとのキーワード（下記ルール参照）
#   科目不明でも大学関連と判断した場合 → 大学\その他\
#   ※大学関連の条件: レポート/第N回/期末/演習/過去問/シラバス/1X24C 等
#                    かつ拡張子が pdf/docx/xlsx/pptx のいずれか
#
# 【その他】→ OneDrive\その他\ に移動
#   - スキャン書類: Adobe Scan / スキャンした書類
#
# 【未分類】→ Downloadsにそのまま残す（手動で判断）
#   上記どれにも該当しないファイル
# ============================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$DL  = "C:\Users\kazuy\Downloads"
$OD  = "C:\Users\kazuy\OneDrive"
$UNI = "$OD\大学"   # 大学フォルダのルート（科目フォルダはここの直下に作成）
$LOG = "C:\Users\kazuy\Projects\auto-classify\classify.log"

$moved   = 0
$skipped = 0

function Move-File($src, $dstFolder) {
    if (-not (Test-Path $dstFolder)) {
        New-Item -ItemType Directory -Force -Path $dstFolder | Out-Null
    }
    try {
        Move-Item -LiteralPath $src -Destination $dstFolder -Force -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Log($msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm')] $msg"
    Add-Content -Path $LOG -Value $line -Encoding UTF8
}

# Downloads直下のファイルのみ対象
$files = Get-ChildItem -Path $DL -File | Where-Object { $_.DirectoryName -eq $DL }
Log "=== 分類開始 ($($files.Count)件) ==="

foreach ($f in $files) {
    $name = $f.Name
    $ext  = $f.Extension.ToLower()
    $dst  = $null

    # ----------------------------------------------------------
    # 【削除予定】
    # ----------------------------------------------------------
    if ($ext -match '\.(exe|msi)') {
        # インストーラー（インストール済みなら不要）
        $dst = "$DL\_削除予定\インストーラー"
    }
    elseif ($ext -eq '.crdownload') {
        # ダウンロード途中 → スキップ（触らない）
        $dst = $null
    }
    elseif ($ext -match '\.(webm|webp|gif)') {
        # 一時的な動画・画像（Chromeの録画・ランダムDL）
        $dst = "$DL\_削除予定\その他"
    }
    elseif ($ext -match '\.(jpg|jpeg|png)' -and ($name -match '^[A-Za-z0-9+_\-]{25,}\.(jpg|jpeg|png)$' -or $name -match '^\d{13,}')) {
        # ランダムハッシュ名 or タイムスタンプ名の画像（Amazonサムネイル等）
        $dst = "$DL\_削除予定\画像"
    }
    elseif ($name -match 'ChatGPT Image|Gemini_Generated|Firefly_') {
        # AI生成画像
        $dst = "$DL\_削除予定\画像"
    }

    # ----------------------------------------------------------
    # 【就活】
    # ----------------------------------------------------------
    elseif ($name -match 'BCG|ボストン.*コンサルティング|ケース面接') {
        $dst = "$OD\就活\BCG"
    }
    elseif ($name -match '就活|選考|面接|エントリーシート') {
        $dst = "$OD\就活\その他"
    }

    # ----------------------------------------------------------
    # 【物販】
    # ----------------------------------------------------------
    elseif ($name -match '請求書|5-Roses|3Link|INV-[0-9]|合同会社.*御中') {
        $dst = "$OD\物販\請求書"
    }
    elseif ($name -match '領収書|receipt') {
        $dst = "$OD\物販\領収書"
    }
    elseif ($name -match '^orders_[0-9]|^Labels|itemlabel|Amazon.com item|配送ラベル' -or
            ($ext -eq '.csv' -and $name -match 'FBA|入庫|保管|warehousing')) {
        $dst = "$OD\物販\取引データ"
    }
    elseif ($name -match 'マニュアル|仕入|納品|検品|清掃|keepa|リサーチ|梱包|作業標準') {
        $dst = "$OD\物販\マニュアル"
    }
    elseif ($name -match '契約書|委託') {
        $dst = "$OD\物販\契約書"
    }
    elseif ($name -match 'せどり|在庫管理') {
        $dst = "$OD\物販\管理シート"
    }

    # ----------------------------------------------------------
    # 【インターン】
    # ----------------------------------------------------------
    elseif ($name -match '韓国|korea_beauty|한국|미팅') {
        $dst = "$OD\インターン\相談会\韓国美容"
    }
    elseif ($name -match 'ララ|LalaBloom') {
        $dst = "$OD\インターン\相談会\ララ"
    }
    elseif ($name -match 'クリニック|相談会') {
        $dst = "$OD\インターン\相談会"
    }

    # ----------------------------------------------------------
    # 【大学 - 科目別】 ※すべて $UNI（OneDrive\大学）直下の科目フォルダへ
    # ----------------------------------------------------------
    elseif ($name -match '管理会計') {
        $dst = "$UNI\管理会計"
    }
    elseif ($name -match '生産.*流通|流通.*マネジメント') {
        $dst = "$UNI\生産・流通マネジメント"
    }
    elseif ($name -match '製品開発') {
        $dst = "$UNI\製品開発工学"
    }
    elseif ($name -match '力学C') {
        $dst = "$UNI\力学C"
    }
    elseif ($name -match 'イノベーション.*オペレ|オペレ.*イノベーション') {
        $dst = "$UNI\イノベーションとオペレーションズのマネジメント"
    }
    elseif ($name -match '生産システム論|進化型計算') {
        $dst = "$UNI\生産システム論と進化型計算"
    }
    elseif ($name -match '化学熱力学') {
        $dst = "$UNI\化学熱力学"
    }
    elseif ($name -match '応用システム思考') {
        $dst = "$UNI\応用システム思考"
    }
    elseif ($name -match '多変量解析') {
        $dst = "$UNI\多変量解析法"
    }
    elseif ($name -match '材料力学B') {
        $dst = "$UNI\材料力学B"
    }
    elseif ($name -match '国際協力論') {
        $dst = "$UNI\国際協力論"
    }
    elseif ($name -match '精神分析論') {
        $dst = "$UNI\精神分析論"
    }
    elseif ($name -match '共創ワークショップ') {
        $dst = "$UNI\共創ワークショップ演習"
    }
    # 大学 - 科目不明だが大学関連（PDF/Word/Excel/PPT のみ）
    elseif ($ext -match '\.(pdf|docx|doc|xlsx|pptx|ppt)$' -and
            $name -match 'レポート|第[0-9]+回|期末|テスト対策|小テスト|演習|過去問|シラバス|handout|講義|授業|1X24C') {
        $dst = "$UNI\その他"
    }

    # ----------------------------------------------------------
    # 【その他】
    # ----------------------------------------------------------
    elseif ($ext -eq '.m4a' -or $ext -eq '.mp3' -or $ext -eq '.wav') {
        $dst = "$OD\その他\録音"
    }
    elseif ($name -match 'Adobe Scan|スキャンした書類') {
        $dst = "$OD\その他\スキャン書類"
    }

    # 移動実行（$dst が null のものは未分類としてDownloadsに残す）
    if ($null -ne $dst) {
        if (Move-File $f.FullName $dst) {
            Log "移動: $name → $($dst.Replace('C:\Users\kazuy\', ''))"
            $moved++
        }
    } else {
        $skipped++
    }
}

Log "=== 完了: 移動 $moved 件, 未分類（Downloads残り） $skipped 件 ==="
Write-Host "移動: $moved 件 / 未分類: $skipped 件"
