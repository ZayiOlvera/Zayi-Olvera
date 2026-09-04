"""
Tests for file-not-found and import-error guards in analyzer.py.
These verify that every public function returns a structured error dict
instead of raising an exception when the prerequisites are missing.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Stub heavy ML packages so analyzer.py can be imported.
for _mod in ("faster_whisper", "scenedetect", "librosa", "cv2", "soundfile"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
try:
    import numpy  # noqa: F401
except ImportError:
    sys.modules["numpy"] = MagicMock()

import analyzer  # noqa: E402


NONEXISTENT = "/tmp/this_file_does_not_exist_at_all.mp4"


class TestFileNotFoundGuards:
    def test_transcribe_clip_missing_file(self):
        result = analyzer.transcribe_clip(NONEXISTENT)
        assert result["success"] is False
        assert "no encontrado" in result["error"].lower() or NONEXISTENT in result["error"]

    def test_detect_scene_cuts_missing_file(self):
        result = analyzer.detect_scene_cuts(NONEXISTENT)
        assert result["success"] is False

    def test_get_audio_levels_missing_file(self):
        result = analyzer.get_audio_levels(NONEXISTENT)
        assert result["success"] is False

    def test_analyze_reference_video_missing_file(self):
        result = analyzer.analyze_reference_video(NONEXISTENT)
        assert result["success"] is False


class TestImportErrorGuards:
    def test_transcribe_clip_missing_faster_whisper(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        with patch.dict(sys.modules, {"faster_whisper": None}):
            result = analyzer.transcribe_clip(str(audio_file))
        assert result["success"] is False
        assert "faster-whisper" in result["error"]

    def test_detect_scene_cuts_missing_scenedetect(self, tmp_path):
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        with patch.dict(sys.modules, {"scenedetect": None}):
            result = analyzer.detect_scene_cuts(str(video_file))
        assert result["success"] is False
        assert "scenedetect" in result["error"]

    def test_get_audio_levels_missing_librosa(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        with patch.dict(sys.modules, {"librosa": None}):
            result = analyzer.get_audio_levels(str(audio_file))
        assert result["success"] is False
        assert "librosa" in result["error"]

    def test_analyze_reference_missing_cv2(self, tmp_path):
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        with patch.dict(sys.modules, {"cv2": None}):
            result = analyzer.analyze_reference_video(str(video_file))
        assert result["success"] is False
        assert "opencv" in result["error"].lower()
