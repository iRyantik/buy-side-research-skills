"""
General-purpose audio transcription via Whisper API (OpenAI-compatible).
Splits audio into <10min chunks to bypass API limit.
Usage: python transcribe.py <audio_path> [language] [model]
Config via env: WHISPER_API_KEY, WHISPER_API_BASE, WHISPER_MODEL
"""
import sys
import os
import json
import subprocess
import tempfile
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_KEY = os.environ.get("WHISPER_API_KEY", "")
API_BASE = os.environ.get("WHISPER_API_BASE", "https://api.openai.com/v1")
MODEL = os.environ.get("WHISPER_MODEL", "whisper-large-v3-turbo")
CHUNK_SECONDS = 540  # 9 minutes per chunk (API limit: 600s)

SCRIPT_DIR = Path(__file__).resolve().parent
FFMPEG = SCRIPT_DIR / "ffmpeg.exe"


def get_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe or ffmpeg."""
    result = subprocess.run(
        [str(FFMPEG), "-i", audio_path, "-f", "null", "-"],
        capture_output=True, text=True,
    )
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            # Duration: 00:58:07.77
            parts = line.split("Duration: ")[1].split(",")[0].split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    raise RuntimeError("Cannot determine audio duration")


def split_audio(audio_path: str, chunk_seconds: int, tmpdir: str) -> list:
    """Split audio into chunks of chunk_seconds each."""
    duration = get_duration(audio_path)
    num_chunks = int(duration / chunk_seconds) + (1 if duration % chunk_seconds > 0 else 0)
    print(f"[SPLIT] {duration:.0f}s total -> {num_chunks} chunks of {chunk_seconds}s")

    chunks = []
    for i in range(num_chunks):
        start = i * chunk_seconds
        chunk_path = os.path.join(tmpdir, f"chunk_{i:03d}.mp3")
        subprocess.run([
            str(FFMPEG), "-y", "-i", audio_path,
            "-ss", str(start), "-t", str(chunk_seconds),
            "-acodec", "libmp3lame", "-ab", "64k",
            chunk_path,
        ], capture_output=True)
        chunks.append((chunk_path, start))
        print(f"  Chunk {i+1}/{num_chunks}: {start//60:02d}:{start%60:02d}")

    return chunks


def transcribe_chunk(chunk_path: str, start_offset: float, chunk_idx: int, language: str) -> dict:
    """Transcribe a single audio chunk."""
    file_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
    print(f"  [{chunk_idx}] Uploading ({file_size_mb:.1f}MB)...", end=" ")

    try:
        with open(chunk_path, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/audio/transcriptions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                files={"file": (os.path.basename(chunk_path), f)},
                data={
                    "model": MODEL,
                    "language": language,
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "segment",
                },
                timeout=300,
            )
    except Exception as e:
        print(f"ERROR: {e}")
        return None

    if resp.status_code != 200:
        print(f"ERROR {resp.status_code}: {resp.text[:200]}")
        return None

    result = resp.json()
    # Adjust timestamps by chunk start offset
    for seg in result.get("segments", []):
        seg["start"] = seg.get("start", 0) + start_offset
        seg["end"] = seg.get("end", 0) + start_offset
    result["_chunk_offset"] = start_offset

    segs = len(result.get("segments", []))
    print(f"OK ({segs} segments)")
    return result


def merge_results(results: list) -> dict:
    """Merge multiple chunk results into one."""
    valid = [r for r in results if r is not None]
    if not valid:
        return None

    merged = {
        "text": "",
        "segments": [],
        "language": valid[0].get("language", "unknown"),
        "duration": sum(float(r.get("duration", 0)) for r in valid),
    }

    all_segments = []
    for r in valid:
        all_segments.extend(r.get("segments", []))

    # Sort by start time
    all_segments.sort(key=lambda s: s.get("start", 0))

    # Remove overlaps (when chunk boundary splits a sentence)
    deduped = []
    last_end = 0
    for seg in all_segments:
        if seg.get("start", 0) >= last_end - 1.0:  # allow 1s overlap
            deduped.append(seg)
            last_end = seg.get("end", 0)

    merged["segments"] = deduped
    merged["text"] = " ".join(s.get("text", "") for s in deduped)
    return merged


def save_result(result: dict, audio_path: str, out_dir: Path = None):
    """Save full JSON + plain text transcript."""
    if out_dir is None:
        out_dir = SCRIPT_DIR

    base = Path(audio_path).stem
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"{base}_transcript.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON saved: {json_path}")

    txt_path = out_dir / f"{base}_transcript.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcription: {base}\n")
        f.write(f"# Model: {MODEL}\n")
        f.write(f"# Duration: {result.get('duration', 'N/A'):.0f}s\n")
        f.write(f"# Language: {result.get('language', 'N/A')}\n\n")
        for seg in result.get("segments", []):
            start = seg.get("start", 0)
            mins, secs = divmod(int(start), 60)
            ts = f"[{mins:02d}:{secs:02d}]"
            f.write(f"{ts} {seg.get('text', '').strip()}\n")
    print(f"[OK] Text saved: {txt_path}")

    return txt_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file_path> [language]")
        sys.exit(1)

    audio_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "zh"

    if not os.path.exists(audio_path):
        print(f"[ERROR] File not found: {audio_path}")
        sys.exit(1)

    if not FFMPEG.exists():
        print(f"[ERROR] ffmpeg not found at {FFMPEG}")
        sys.exit(1)

    print(f"[FILE] {audio_path}")
    print(f"[MODEL] {MODEL}")
    print(f"[LANG] {language}")

    # Split and transcribe
    with tempfile.TemporaryDirectory() as tmpdir:
        chunks = split_audio(audio_path, CHUNK_SECONDS, tmpdir)
        print(f"\n[STATUS] Transcribing {len(chunks)} chunks...")

        results = []
        for i, (chunk_path, offset) in enumerate(chunks):
            r = transcribe_chunk(chunk_path, offset, i + 1, language)
            results.append(r)

    # Merge and save
    merged = merge_results(results)
    if merged:
        txt_path = save_result(merged, audio_path, out_dir=SCRIPT_DIR)
        print(f"\n[DONE] Transcript -> {txt_path}")
    else:
        print("\n[FAIL] All chunks failed.")
        sys.exit(1)
