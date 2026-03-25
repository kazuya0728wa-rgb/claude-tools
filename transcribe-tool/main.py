import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

import whisper
import yt_dlp
from pyannote.audio import Pipeline
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def download_audio(url: str, output_dir: str) -> str:
    """動画URLから音声をダウンロード"""
    output_path = os.path.join(output_dir, "audio")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "quiet": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path + ".wav"


def transcribe(audio_path: str) -> dict:
    """Whisperで文字起こし（日本語・韓国語自動判定）"""
    print("\n[1/4] 文字起こし中...")
    model = whisper.load_model("medium")
    result = model.transcribe(audio_path, language=None, verbose=False)
    detected_lang = result.get("language", "不明")
    print(f"      検出言語: {detected_lang}")
    return result


def diarize(audio_path: str, hf_token: str):
    """pyannoteで話者分離"""
    print("[2/4] 話者分離中...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )
    diarization = pipeline(audio_path)
    return diarization


def assign_speakers(whisper_segments: list, diarization) -> list:
    """Whisperのセグメントにpyannoteの話者ラベルを付与"""
    result = []
    for seg in whisper_segments:
        midpoint = (seg["start"] + seg["end"]) / 2
        speaker = "不明"
        for turn, _, spk in diarization.itertracks(yield_label=True):
            if turn.start <= midpoint <= turn.end:
                speaker = spk
                break
        result.append({
            "start": seg["start"],
            "end": seg["end"],
            "speaker": speaker,
            "text": seg["text"].strip(),
        })
    return result


def summarize(transcript_text: str, deepseek_key: str) -> str:
    """DeepSeek APIで要約生成"""
    print("[3/4] 要約生成中...")
    client = OpenAI(
        api_key=deepseek_key,
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは優秀な要約アシスタントです。"
                    "音声の文字起こしを分析し、日本語で以下の形式で出力してください：\n"
                    "1. 全体の概要（2〜3文）\n"
                    "2. 主なトピック（箇条書き）\n"
                    "3. 結論・アクションアイテム（あれば）"
                ),
            },
            {
                "role": "user",
                "content": f"以下の文字起こしを要約してください：\n\n{transcript_text}",
            },
        ],
    )
    return response.choices[0].message.content


def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def save_output(segments: list, summary: str, source: str) -> Path:
    """結果をMarkdownファイルに保存"""
    print("[4/4] ファイルに保存中...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"transcript_{timestamp}.md")

    lines = [
        "# 文字起こし・要約レポート",
        "",
        f"**ソース:** {source}",
        f"**作成日時:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## 要約",
        "",
        summary,
        "",
        "---",
        "",
        "## 文字起こし",
        "",
    ]

    for seg in segments:
        lines.append(f"**[{seg['speaker']}  {format_time(seg['start'])}]** {seg['text']}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def process(audio_path: str, source: str, hf_token: str, deepseek_key: str):
    whisper_result = transcribe(audio_path)
    diarization = diarize(audio_path, hf_token)
    segments = assign_speakers(whisper_result["segments"], diarization)

    transcript_text = "\n".join(
        f"[{seg['speaker']}] {seg['text']}" for seg in segments
    )

    summary = summarize(transcript_text, deepseek_key)
    output_path = save_output(segments, summary, source)
    print(f"\n完了！保存先: {output_path.resolve()}")


def main():
    if len(sys.argv) < 2:
        print("使用方法: python main.py <音声ファイルまたは動画URL>")
        print("例1: python main.py meeting.mp3")
        print("例2: python main.py https://www.youtube.com/watch?v=xxxxx")
        sys.exit(1)

    source = sys.argv[1]

    hf_token = os.getenv("HF_TOKEN")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    if not hf_token:
        print("エラー: .env ファイルに HF_TOKEN が設定されていません")
        sys.exit(1)
    if not deepseek_key:
        print("エラー: .env ファイルに DEEPSEEK_API_KEY が設定されていません")
        sys.exit(1)

    if source.startswith("http"):
        print("動画をダウンロード中...")
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = download_audio(source, tmpdir)
            process(audio_path, source, hf_token, deepseek_key)
    else:
        if not os.path.exists(source):
            print(f"エラー: ファイルが見つかりません: {source}")
            sys.exit(1)
        process(source, source, hf_token, deepseek_key)


if __name__ == "__main__":
    main()
