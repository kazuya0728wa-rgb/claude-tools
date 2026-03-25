@echo off
chcp 65001 >nul
title 文字起こしツール
color 0B

echo.
echo ╔══════════════════════════════════════════════╗
echo ║          文字起こし・要約ツール              ║
echo ╚══════════════════════════════════════════════╝
echo.

:: .env の存在チェック
if not exist "%~dp0.env" (
    echo  ✗  セットアップが完了していません。
    echo     先に setup.bat をダブルクリックして実行してください。
    echo.
    pause
    exit /b 1
)

echo  対応形式: 音声ファイル（mp3, wav, m4a など）または YouTube URL
echo.
echo  処理したいファイルのパス、または YouTube の URL を入力してください。
echo  （ファイルはこのウィンドウにドラッグ＆ドロップもできます）
echo.
set /p SOURCE="  ファイル or URL: "

if "%SOURCE%"=="" (
    echo.
    echo  ✗  入力がありませんでした。
    pause
    exit /b 1
)

echo.
echo  処理を開始します。完了まで数分〜十数分かかります...
echo  このウィンドウを閉じないでください。
echo.

cd /d "%~dp0"
python main.py "%SOURCE%"

if %errorlevel% neq 0 (
    echo.
    echo  ✗  エラーが発生しました。上のメッセージを確認してください。
) else (
    echo.
    echo  ✓  完了しました！同じフォルダに transcript_*.md というファイルが作成されています。
)

echo.
pause
