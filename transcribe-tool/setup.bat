@echo off
chcp 65001 >nul
title 文字起こしツール セットアップ
color 0A

echo.
echo ╔══════════════════════════════════════════════╗
echo ║      文字起こしツール  セットアップ          ║
echo ║      このウィンドウを閉じないでください      ║
echo ╚══════════════════════════════════════════════╝
echo.
echo このツールを使えるようにするための準備をします。
echo 画面の指示に従って進めてください。
echo.
pause


:: ─────────────────────────────────────
:: STEP 1: Python チェック
:: ─────────────────────────────────────
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [ステップ 1/5]  Python の確認
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ✗  Python が見つかりませんでした。
    echo.
    echo  今からブラウザで Python のダウンロードページを開きます。
    echo.
    echo  手順:
    echo    1. ブラウザで「Download Python」ボタンをクリック
    echo    2. インストーラーを実行
    echo    3. ★必ず★「Add Python to PATH」にチェックを入れる
    echo    4. Install Now をクリック
    echo    5. インストール完了後、このウィンドウに戻って Enter を押す
    echo.
    pause
    start https://www.python.org/downloads/
    echo.
    echo  Python のインストールが完了したら Enter を押してください...
    pause
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo  ✗  まだ Python が認識されていません。
        echo     パソコンを再起動してから、もう一度このファイルをダブルクリックしてください。
        echo.
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  ✓  %%v が見つかりました
echo.


:: ─────────────────────────────────────
:: STEP 2: 依存パッケージのインストール
:: ─────────────────────────────────────
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [ステップ 2/5]  必要なソフトのインストール
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  必要なソフトをインストールします（数分かかる場合があります）...
echo.

python -m pip install --upgrade pip -q
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo  ✗  インストール中にエラーが発生しました。
    echo     インターネット接続を確認してから、もう一度試してください。
    echo.
    pause
    exit /b 1
)
echo.
echo  ✓  インストール完了


:: ─────────────────────────────────────
:: STEP 3: FFmpeg チェック
:: ─────────────────────────────────────
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [ステップ 3/5]  FFmpeg の確認
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo  FFmpeg が見つかりません。自動でインストールします...
    echo.
    pip install imageio[ffmpeg] -q
    python -c "import imageio_ffmpeg; import shutil, os; ffmpeg=imageio_ffmpeg.get_ffmpeg_exe(); dest=os.path.join(os.path.dirname(os.path.abspath('%~f0')), 'ffmpeg.exe'); shutil.copy(ffmpeg, dest); print('OK')" >nul 2>&1
    :: winget で試みる
    winget install --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    ffmpeg -version >nul 2>&1
    if %errorlevel% neq 0 (
        echo  ブラウザで FFmpeg のダウンロードページを開きます。
        echo.
        echo  手順:
        echo    1. 「ffmpeg-release-essentials.zip」をダウンロード
        echo    2. ZIPを解凍
        echo    3. 中の bin フォルダにある ffmpeg.exe を
        echo       このフォルダ（%~dp0）にコピー
        echo    4. コピーが終わったら Enter を押す
        echo.
        pause
        start https://www.gyan.dev/ffmpeg/builds/
        echo  ffmpeg.exe のコピーが完了したら Enter を押してください...
        pause
    )
) else (
    echo  ✓  FFmpeg が見つかりました
)
echo.


:: ─────────────────────────────────────
:: STEP 4: HuggingFace トークン
:: ─────────────────────────────────────
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [ステップ 4/5]  HuggingFace トークンの設定
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  話者の識別機能を使うために HuggingFace のアカウントが必要です。
echo.
echo  ─ アカウントをお持ちでない方 ─────────────────────────
echo  1. 今からブラウザで登録ページを開きます（無料です）
echo  2. アカウントを作成してください
echo  3. 作成後、下の「モデル利用許可」の手順に進んでください
echo  ────────────────────────────────────────────────────────
echo.
echo  ─ トークンの取得手順 ────────────────────────────────────
echo  1. https://huggingface.co/settings/tokens を開く
echo  2. 「New token」をクリック → 名前を入力 → 「Read」を選択
echo  3. 「Generate a token」をクリック
echo  4. 表示されたトークン（hf_ で始まる文字列）をコピー
echo  ────────────────────────────────────────────────────────
echo.
echo  ─ モデルの利用許可（必須）───────────────────────────────
echo  下のページを開き「Agree and access repository」をクリック:
echo    https://huggingface.co/pyannote/speaker-diarization-3.1
echo  ────────────────────────────────────────────────────────
echo.
echo  準備ができたら Enter を押してください（ブラウザが開きます）...
pause
start https://huggingface.co/join
start https://huggingface.co/settings/tokens
start https://huggingface.co/pyannote/speaker-diarization-3.1

echo.
echo  トークンの準備ができたら、ここに貼り付けて Enter を押してください。
echo  （入力内容は画面に表示されません。貼り付け後 Enter キーを押してください）
echo.
set /p HF_TOKEN="  HuggingFace トークン: "

if "%HF_TOKEN%"=="" (
    echo.
    echo  ✗  トークンが入力されていません。もう一度セットアップを実行してください。
    pause
    exit /b 1
)
echo  ✓  トークンを受け取りました
echo.


:: ─────────────────────────────────────
:: STEP 5: DeepSeek API キー
:: ─────────────────────────────────────
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [ステップ 5/5]  DeepSeek API キーの設定
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  要約機能を使うために DeepSeek のアカウントが必要です。
echo.
echo  手順:
echo    1. 今からブラウザで DeepSeek のページを開きます（無料で始められます）
echo    2. アカウントを作成してログイン
echo    3. 「API Keys」→「Create new secret key」
echo    4. 表示されたキーをコピー
echo.
echo  準備ができたら Enter を押してください（ブラウザが開きます）...
pause
start https://platform.deepseek.com/api_keys

echo.
set /p DEEPSEEK_API_KEY="  DeepSeek API キー: "

if "%DEEPSEEK_API_KEY%"=="" (
    echo.
    echo  ✗  API キーが入力されていません。もう一度セットアップを実行してください。
    pause
    exit /b 1
)
echo  ✓  API キーを受け取りました
echo.


:: ─────────────────────────────────────
:: .env ファイルを作成
:: ─────────────────────────────────────
(
    echo HF_TOKEN=%HF_TOKEN%
    echo DEEPSEEK_API_KEY=%DEEPSEEK_API_KEY%
) > "%~dp0.env"

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  セットアップ完了！
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  準備が整いました。ツールを使うには：
echo.
echo    run.bat をダブルクリックして起動します。
echo.
echo  または、コマンドプロンプトで：
echo    python main.py  ^<音声ファイル or YouTube URL^>
echo.
pause
