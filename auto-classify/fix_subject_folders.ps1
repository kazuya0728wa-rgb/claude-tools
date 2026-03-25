[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OD  = "C:\Users\kazuy\OneDrive"
$UNI = "C:\Users\kazuy\OneDrive\大学"

$subjects = @(
    '管理会計',
    '生産・流通マネジメント',
    '製品開発工学',
    '力学C',
    'イノベーションとオペレーションズのマネジメント',
    '生産システム論と進化型計算',
    '化学熱力学',
    '応用システム思考',
    '多変量解析法',
    '材料力学B',
    '国際協力論',
    '精神分析論',
    '共創ワークショップ演習'
)

foreach ($s in $subjects) {
    $src = "$OD\$s"
    $dst = "$UNI\$s"
    if (Test-Path $src) {
        Move-Item -LiteralPath $src -Destination $dst -Force
        Write-Host "移動: $s"
    } else {
        Write-Host "なし: $s"
    }
}

Write-Host "完了"
