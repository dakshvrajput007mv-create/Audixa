"""
transcriber.py - Whisper AI transcription and auto-chapter generation for Audixa.
Uses faster-whisper for fast, high-accuracy speech recognition supporting
English, Hindi, and code-switched Hindi-English (Hinglish).
"""

import os
import re
import uuid
from typing import Dict, List, Tuple, Any, Optional

# Global cache for loaded Whisper models to avoid re-loading on each request
_MODELS: Dict[str, Any] = {}


def get_whisper_model(model_size: str = "base"):
    """Loads and caches faster-whisper model on CPU with int8 quantization."""
    global _MODELS
    # Normalize model size name
    if model_size not in ["tiny", "base", "small", "medium"]:
        model_size = "base"

    if model_size not in _MODELS:
        try:
            from faster_whisper import WhisperModel
            print(f"[Audixa] Loading Whisper model '{model_size}' (CPU / int8)...")
            _MODELS[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
            print(f"[Audixa] Model '{model_size}' loaded successfully.")
        except Exception as e:
            print(f"[Audixa] Error loading faster-whisper model '{model_size}': {e}")
            raise e

    return _MODELS[model_size]


def clean_text(text: str) -> str:
    """Cleans whitespace and trailing punctuation for clean display."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def generate_auto_chapters(
    segments: List[Dict[str, Any]], 
    total_duration: float
) -> List[Dict[str, Any]]:
    """
    Generates structured, sensible chapters from transcription segments.
    Heuristic:
      1. Identifies significant pause gaps (>= 1.5s between segments)
      2. If pause gaps are too few/many, clusters segments every 30-60 seconds
      3. Extracts an opening phrase or contextual summary for the chapter title
      4. Always includes an 'Introduction' chapter starting at 0.0s
    """
    if not segments:
        return [{
            "id": str(uuid.uuid4()),
            "title": "Introduction",
            "start_time": 0.0,
            "end_time": max(total_duration, 1.0),
            "order_index": 0
        }]

    # Ensure segments are sorted
    sorted_segs = sorted(segments, key=lambda s: s["start_time"])
    chapter_starts = [0.0]

    # Heuristic 1: Detect pause gaps >= 1.5s
    last_end = sorted_segs[0]["end_time"]
    for i in range(1, len(sorted_segs)):
        current_start = sorted_segs[i]["start_time"]
        gap = current_start - last_end
        time_since_last_chapter = current_start - chapter_starts[-1]

        # Break if significant pause gap (>1.5s) AND at least 20s from previous chapter start
        if gap >= 1.5 and time_since_last_chapter >= 20.0:
            chapter_starts.append(current_start)
        # Or if it's been more than 60s without a chapter break and there is a mild pause (>=0.5s)
        elif time_since_last_chapter >= 60.0 and gap >= 0.5:
            chapter_starts.append(current_start)

        last_end = max(last_end, sorted_segs[i]["end_time"])

    # If only 1 chapter was found and audio is longer than 45s, create periodic chapters
    if len(chapter_starts) == 1 and total_duration > 45.0:
        step = min(60.0, total_duration / 3.0)
        curr = step
        while curr < total_duration - 15.0:
            # Snap to nearest segment start
            nearest_seg = min(sorted_segs, key=lambda s: abs(s["start_time"] - curr))
            if nearest_seg["start_time"] not in chapter_starts and nearest_seg["start_time"] > chapter_starts[-1] + 15.0:
                chapter_starts.append(nearest_seg["start_time"])
            curr += step

    # Build chapters list with titles and boundaries
    chapter_starts = sorted(list(set(chapter_starts)))
    chapters = []

    for idx, start_t in enumerate(chapter_starts):
        # Determine end time
        if idx + 1 < len(chapter_starts):
            end_t = chapter_starts[idx + 1]
        else:
            end_t = max(total_duration, sorted_segs[-1]["end_time"])

        # Find first segment belonging to this chapter to infer title
        matching_segs = [s for s in sorted_segs if s["start_time"] >= start_t - 0.5 and s["start_time"] < end_t]
        
        if idx == 0:
            title = "Introduction"
        elif matching_segs:
            first_text = matching_segs[0]["text"].strip()
            # Truncate to first 4-7 words for a snappy title
            words = first_text.split()
            if len(words) > 5:
                snippet = " ".join(words[:5]) + "..."
            else:
                snippet = first_text
            # Remove trailing commas/periods
            snippet = snippet.rstrip(".,;:- ")
            title = f"Topic {idx + 1}: {snippet}" if snippet else f"Chapter {idx + 1}"
        else:
            title = f"Chapter {idx + 1}"

        chapters.append({
            "id": str(uuid.uuid4()),
            "title": title,
            "start_time": round(start_t, 2),
            "end_time": round(end_t, 2),
            "order_index": idx
        })

    return chapters


def transcribe_audio(
    file_path: str,
    language_mode: str = "auto",
    model_size: str = "base",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Transcribes the audio file using faster-whisper.
    
    Args:
        file_path: Absolute path to media file.
        language_mode: 'en' for English, 'hi' for Hindi, 'auto' for Hinglish / Auto-detect.
        model_size: 'tiny', 'base', 'small', or 'medium'.

    Returns:
        (segments, chapters, metadata_dict)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at: {file_path}")

    # Set Whisper language parameter
    whisper_lang = None
    if language_mode == "en":
        whisper_lang = "en"
    elif language_mode == "hi":
        whisper_lang = "hi"
    else:  # auto / hinglish
        whisper_lang = None

    model = get_whisper_model(model_size)

    print(f"[Audixa] Transcribing '{file_path}' (lang={whisper_lang}, model={model_size})...")
    segments_raw, info = model.transcribe(
        file_path,
        language=whisper_lang,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,  # Filter out background noise & silence
    )

    detected_lang = info.language
    lang_probability = round(info.language_probability, 4)
    total_duration = round(info.duration, 2) if info.duration else 0.0

    segments = []
    max_end_time = 0.0

    for idx, seg in enumerate(segments_raw):
        clean_seg_text = clean_text(seg.text)
        if not clean_seg_text:
            continue

        seg_start = round(seg.start, 2)
        seg_end = round(seg.end, 2)
        max_end_time = max(max_end_time, seg_end)

        segments.append({
            "id": str(uuid.uuid4()),
            "start_time": seg_start,
            "end_time": seg_end,
            "text": clean_seg_text,
            "order_index": idx,
        })

    if total_duration <= 0.0:
        total_duration = max_end_time

    # Generate smart chapters
    chapters = generate_auto_chapters(segments, total_duration)

    metadata = {
        "detected_language": detected_lang,
        "language_probability": lang_probability,
        "duration": total_duration,
        "model_size": model_size,
    }

    print(f"[Audixa] Transcription complete: {len(segments)} segments, {len(chapters)} chapters, duration={total_duration}s")
    return segments, chapters, metadata
