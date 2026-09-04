"""
Unit tests for tools.py — _fmt, handle_tool_call, and _dispatch.
resolve_client and analyzer are mocked throughout.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Stub heavy ML packages
for _mod in ("faster_whisper", "scenedetect", "librosa", "cv2", "soundfile", "DaVinciResolveScript"):
    sys.modules.setdefault(_mod, MagicMock())
try:
    import numpy  # noqa: F401
except ImportError:
    sys.modules["numpy"] = MagicMock()

import tools  # noqa: E402
import resolve_client  # noqa: E402
import analyzer  # noqa: E402


# ---------------------------------------------------------------------------
# _fmt
# ---------------------------------------------------------------------------

class TestFmt:
    def test_zero(self):
        assert tools._fmt(0) == "0:00"

    def test_one_minute(self):
        assert tools._fmt(60) == "1:00"

    def test_ninety_seconds(self):
        assert tools._fmt(90) == "1:30"

    def test_less_than_one_minute(self):
        assert tools._fmt(45) == "0:45"

    def test_large_value(self):
        # 3661 s → 61 minutes 1 second
        assert tools._fmt(3661) == "61:01"

    def test_seconds_zero_padded(self):
        result = tools._fmt(61)
        # Should be "1:01", not "1:1"
        assert result == "1:01"


# ---------------------------------------------------------------------------
# handle_tool_call — exception wrapping
# ---------------------------------------------------------------------------

class TestHandleToolCall:
    def test_unknown_tool_returns_error(self):
        result = tools.handle_tool_call("nonexistent_tool", {})
        assert result["success"] is False
        assert "nonexistent_tool" in result["error"] or "desconocida" in result["error"]

    def test_exception_is_caught(self):
        # Patch _dispatch to raise an unexpected error
        with patch.object(tools, "_dispatch", side_effect=ValueError("boom")):
            result = tools.handle_tool_call("anything", {})
        assert result["success"] is False
        assert "boom" in result["error"]

    def test_successful_dispatch_returned(self):
        with patch.object(tools, "_dispatch", return_value={"success": True, "data": 42}):
            result = tools.handle_tool_call("anything", {})
        assert result == {"success": True, "data": 42}


# ---------------------------------------------------------------------------
# _dispatch — analysis tools: clip-not-found path
# ---------------------------------------------------------------------------

class TestDispatchAnalysisClipNotFound:
    def _no_clip(self):
        return patch.object(resolve_client, "get_clip_path", return_value=None)

    def test_transcribe_clip_not_found(self):
        with self._no_clip():
            result = tools._dispatch("transcribe_clip", {"clip_name": "missing"})
        assert result["success"] is False
        assert "missing" in result["error"]

    def test_detect_scene_cuts_not_found(self):
        with self._no_clip():
            result = tools._dispatch("detect_scene_cuts", {"clip_name": "missing"})
        assert result["success"] is False

    def test_get_audio_levels_not_found(self):
        with self._no_clip():
            result = tools._dispatch("get_audio_levels", {"clip_name": "missing"})
        assert result["success"] is False


# ---------------------------------------------------------------------------
# _dispatch — analysis tools: delegates to analyzer when clip found
# ---------------------------------------------------------------------------

class TestDispatchAnalysisWithClip:
    def _with_clip(self, path="/videos/interview.mp4"):
        return patch.object(resolve_client, "get_clip_path", return_value=path)

    def test_transcribe_clip_delegates_to_analyzer(self):
        expected = {"success": True, "segments": [], "full_text": ""}
        with self._with_clip(), patch.object(analyzer, "transcribe_clip", return_value=expected) as mock_tx:
            result = tools._dispatch("transcribe_clip", {"clip_name": "interview"})
        mock_tx.assert_called_once_with("/videos/interview.mp4", language=None)
        assert result == expected

    def test_detect_scene_cuts_delegates_to_analyzer(self):
        expected = {"success": True, "scenes": []}
        with self._with_clip(), patch.object(analyzer, "detect_scene_cuts", return_value=expected) as mock_sc:
            result = tools._dispatch("detect_scene_cuts", {"clip_name": "interview"})
        mock_sc.assert_called_once_with("/videos/interview.mp4")
        assert result == expected

    def test_get_audio_levels_delegates_to_analyzer(self):
        expected = {"success": True, "peak_db": -6.0}
        with self._with_clip(), patch.object(analyzer, "get_audio_levels", return_value=expected) as mock_al:
            result = tools._dispatch("get_audio_levels", {"clip_name": "interview"})
        mock_al.assert_called_once_with("/videos/interview.mp4")
        assert result == expected

    def test_language_forwarded_on_transcribe(self):
        expected = {"success": True, "segments": [], "full_text": ""}
        with self._with_clip(), patch.object(analyzer, "transcribe_clip", return_value=expected) as mock_tx:
            tools._dispatch("transcribe_clip", {"clip_name": "interview", "language": "en"})
        mock_tx.assert_called_once_with("/videos/interview.mp4", language="en")


# ---------------------------------------------------------------------------
# _dispatch — Resolve passthrough tools
# ---------------------------------------------------------------------------

class TestDispatchResolveTools:
    def test_get_project_info(self):
        expected = {"project_name": "MyProject"}
        with patch.object(resolve_client, "get_project_info", return_value=expected):
            result = tools._dispatch("get_project_info", {})
        assert result == expected

    def test_create_timeline_passes_name(self):
        with patch.object(resolve_client, "create_timeline", return_value={"success": True}) as mock_ct:
            tools._dispatch("create_timeline", {"name": "NewTimeline"})
        mock_ct.assert_called_once_with("NewTimeline", None)

    def test_create_timeline_passes_fps(self):
        with patch.object(resolve_client, "create_timeline", return_value={"success": True}) as mock_ct:
            tools._dispatch("create_timeline", {"name": "FPSTimeline", "fps": 30.0})
        mock_ct.assert_called_once_with("FPSTimeline", 30.0)

    def test_split_clip(self):
        with patch.object(resolve_client, "split_clip", return_value={"success": True}) as mock_sc:
            tools._dispatch("split_clip", {"time_sec": 12.5})
        mock_sc.assert_called_once_with(12.5)

    def test_delete_timeline_item(self):
        with patch.object(resolve_client, "delete_timeline_item", return_value={"success": True}) as mock_del:
            tools._dispatch("delete_timeline_item", {"item_index": 2})
        mock_del.assert_called_once_with(2)
