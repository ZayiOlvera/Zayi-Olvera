"""
Video analysis: transcription (faster-whisper), scene detection (PySceneDetect),
audio levels (librosa), and reference video style analysis (OpenCV + PIL).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import config


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe_clip(file_path: str, language: Optional[str] = None) -> dict:
    """
    Transcribe audio from a video/audio file using faster-whisper.
    Returns timestamped segments and a full text string.
    """
    if not os.path.isfile(file_path):
        return {"success": False, "error": f"Archivo no encontrado: {file_path}"}

    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        return {
            "success": False,
            "error": "faster-whisper no instalado. Ejecuta: pip install faster-whisper",
        }

    lang = language or config.WHISPER_LANGUAGE
    model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    segments_gen, info = model.transcribe(
        file_path,
        language=lang,
        vad_filter=True,  # skip silent parts for speed
        vad_parameters={"min_silence_duration_ms": 300},
    )

    segments = []
    full_text_parts = []
    for seg in segments_gen:
        segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        })
        full_text_parts.append(seg.text.strip())

    return {
        "success": True,
        "language": info.language,
        "duration_sec": info.duration,
        "segments": segments,
        "full_text": " ".join(full_text_parts),
    }


def find_filler_segments(segments: list[dict]) -> list[dict]:
    """
    Given transcription segments, return those that are silences or filler words.
    These are candidates for removal in auto-edit.
    """
    fillers = [w.lower() for w in config.FILLER_WORDS]
    bad = []
    for seg in segments:
        text = seg["text"].lower().strip()
        is_filler = any(text == f or text.startswith(f + " ") or text.endswith(" " + f) for f in fillers)
        # Very short segments with no meaningful content
        is_short_noise = len(text.split()) <= 2 and (seg["end"] - seg["start"]) < 0.8
        if is_filler or is_short_noise:
            bad.append(seg)
    return bad


def compute_keep_ranges(
    segments: list[dict],
    filler_segments: list[dict],
    total_duration: float,
    silence_gap_threshold: float = 0.4,
) -> list[dict]:
    """
    Given all segments and the ones to remove, return a list of
    {'start': s, 'end': e} ranges that should be KEPT on the timeline.
    """
    remove_ids = {(s["start"], s["end"]) for s in filler_segments}

    keep = []
    last_end = 0.0
    for seg in segments:
        if (seg["start"], seg["end"]) in remove_ids:
            continue
        gap = seg["start"] - last_end
        if gap > silence_gap_threshold and keep:
            # big enough gap — close previous keep range, start new one
            keep[-1]["end"] = last_end
            keep.append({"start": seg["start"], "end": seg["end"]})
        elif not keep:
            keep.append({"start": seg["start"], "end": seg["end"]})
        else:
            keep[-1]["end"] = seg["end"]
        last_end = seg["end"]

    if not keep and segments:
        # Fallback: keep everything
        keep = [{"start": segments[0]["start"], "end": segments[-1]["end"]}]
    return keep


# ---------------------------------------------------------------------------
# Scene detection
# ---------------------------------------------------------------------------

def detect_scene_cuts(file_path: str) -> dict:
    """
    Detect scene cuts in a video using PySceneDetect.
    Returns a list of cut timestamps in seconds.
    """
    if not os.path.isfile(file_path):
        return {"success": False, "error": f"Archivo no encontrado: {file_path}"}

    try:
        from scenedetect import open_video, SceneManager  # type: ignore
        from scenedetect.detectors import ContentDetector  # type: ignore
    except ImportError:
        return {
            "success": False,
            "error": "scenedetect no instalado. Ejecuta: pip install scenedetect[opencv]",
        }

    video = open_video(file_path)
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=config.SCENE_DETECT_THRESHOLD))
    manager.detect_scenes(video, show_progress=False)
    scene_list = manager.get_scene_list()

    cuts = []
    for scene in scene_list:
        start_time = scene[0].get_seconds()
        end_time = scene[1].get_seconds()
        cuts.append({"start": round(start_time, 3), "end": round(end_time, 3)})

    cut_timestamps = [c["start"] for c in cuts[1:]]  # first scene starts at 0
    avg_duration = (
        sum(c["end"] - c["start"] for c in cuts) / len(cuts) if cuts else 0
    )

    return {
        "success": True,
        "scene_count": len(cuts),
        "cut_timestamps_sec": cut_timestamps,
        "scenes": cuts,
        "avg_scene_duration_sec": round(avg_duration, 2),
    }


# ---------------------------------------------------------------------------
# Audio levels
# ---------------------------------------------------------------------------

def get_audio_levels(file_path: str) -> dict:
    """
    Analyze audio peak and RMS levels using librosa.
    """
    if not os.path.isfile(file_path):
        return {"success": False, "error": f"Archivo no encontrado: {file_path}"}

    try:
        import librosa  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return {
            "success": False,
            "error": "librosa no instalado. Ejecuta: pip install librosa",
        }

    y, sr = librosa.load(file_path, sr=None, mono=True)
    peak_db = float(20 * np.log10(np.max(np.abs(y)) + 1e-9))
    rms = librosa.feature.rms(y=y)[0]
    avg_rms_db = float(20 * np.log10(np.mean(rms) + 1e-9))

    # Silence ratio
    silent_frames = np.sum(rms < 10 ** (config.SILENCE_THRESHOLD_DB / 20))
    silence_ratio = float(silent_frames / len(rms))

    return {
        "success": True,
        "peak_db": round(peak_db, 1),
        "avg_rms_db": round(avg_rms_db, 1),
        "silence_ratio": round(silence_ratio, 3),
        "duration_sec": round(len(y) / sr, 2),
        "recommendation": _audio_recommendation(peak_db, avg_rms_db),
    }


def _audio_recommendation(peak_db: float, rms_db: float) -> str:
    if peak_db > -1:
        return "Audio clippeado (pico > -1 dB). Reduce el volumen."
    if rms_db < -30:
        return "Audio muy bajo (RMS < -30 dB). Sube el volumen o aplica normalización."
    if rms_db > -12:
        return "Audio alto (RMS > -12 dB). Considera un ligero ducking."
    return "Niveles de audio correctos."


# ---------------------------------------------------------------------------
# Reference video analysis
# ---------------------------------------------------------------------------

def analyze_reference_video(file_path: str) -> dict:
    """
    Analyze a reference video to extract editing style:
    - Pacing (avg cut duration)
    - Color temperature / look
    - Saturation level
    """
    if not os.path.isfile(file_path):
        return {"success": False, "error": f"Archivo no encontrado: {file_path}"}

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return {
            "success": False,
            "error": "opencv-python no instalado. Ejecuta: pip install opencv-python",
        }

    # --- Pacing via scene detection ---
    scene_data = detect_scene_cuts(file_path)
    avg_cut = scene_data.get("avg_scene_duration_sec", 0)
    scene_count = scene_data.get("scene_count", 0)

    # --- Color analysis: sample frames evenly ---
    cap = cv2.VideoCapture(file_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    sample_count = min(30, max(5, total_frames // 50))
    step = max(1, total_frames // sample_count)

    hue_values = []
    saturation_values = []
    brightness_values = []
    warmth_scores = []

    for i in range(sample_count):
        frame_idx = i * step
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        hue_values.append(float(np.mean(h)))
        saturation_values.append(float(np.mean(s)))
        brightness_values.append(float(np.mean(v)))

        # Warmth: red/orange/yellow hues (0–30 and 150–180 in OpenCV H range 0–180)
        warm_mask = ((h < 30) | (h > 150)) & (s > 50)
        warmth_scores.append(float(np.mean(warm_mask)))

    cap.release()

    avg_sat = sum(saturation_values) / len(saturation_values) if saturation_values else 0
    avg_bri = sum(brightness_values) / len(brightness_values) if brightness_values else 0
    avg_warmth = sum(warmth_scores) / len(warmth_scores) if warmth_scores else 0

    color_temp = "cálido" if avg_warmth > 0.15 else "frío/neutro"
    saturation_desc = (
        "muy saturado" if avg_sat > 180
        else "saturado" if avg_sat > 120
        else "moderado" if avg_sat > 60
        else "desaturado / cinematográfico"
    )
    brightness_desc = (
        "muy brillante" if avg_bri > 200
        else "brillante" if avg_bri > 150
        else "normal" if avg_bri > 80
        else "oscuro"
    )

    pacing_desc = (
        "muy rápido (< 2s por escena)" if avg_cut < 2
        else "rápido (2–4s)" if avg_cut < 4
        else "moderado (4–8s)" if avg_cut < 8
        else "lento (> 8s)"
    )

    return {
        "success": True,
        "file": file_path,
        "pacing": {
            "avg_cut_duration_sec": round(avg_cut, 2),
            "scene_count": scene_count,
            "description": pacing_desc,
        },
        "color": {
            "temperature": color_temp,
            "saturation": saturation_desc,
            "brightness": brightness_desc,
            "avg_saturation_raw": round(avg_sat, 1),
            "avg_brightness_raw": round(avg_bri, 1),
        },
        "summary": (
            f"Edición {pacing_desc}, tono {color_temp}, imagen {saturation_desc} y {brightness_desc}. "
            f"{scene_count} cortes detectados."
        ),
    }
