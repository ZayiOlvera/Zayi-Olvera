"""
Unit tests for the _auto_edit_interview compound tool in tools.py.
All external calls (resolve_client, analyzer) are mocked.
"""
import sys
import math
import pytest
from unittest.mock import MagicMock, patch, call

for _mod in ("faster_whisper", "scenedetect", "librosa", "cv2", "soundfile", "DaVinciResolveScript"):
    sys.modules.setdefault(_mod, MagicMock())
try:
    import numpy  # noqa: F401
except ImportError:
    sys.modules["numpy"] = MagicMock()

import tools          # noqa: E402
import resolve_client  # noqa: E402
import analyzer        # noqa: E402


# Helpers to build fake data
def _make_transcription(segments=None, duration=10.0):
    segs = segments or [
        {"start": 0.0, "end": 2.0, "text": "hola mundo"},
        {"start": 2.5, "end": 4.0, "text": "eh"},
        {"start": 4.2, "end": 8.0, "text": "esto es importante"},
    ]
    return {"success": True, "segments": segs, "duration_sec": duration, "language": "es"}


def _make_project_info(timelines=None):
    return {"project_name": "TestProject", "timelines": timelines or []}


class TestAutoEditInterviewClipNotFound:
    def test_returns_error_when_clip_missing(self):
        with patch.object(resolve_client, "get_clip_path", return_value=None):
            result = tools._auto_edit_interview({"clip_name": "missing_clip"})
        assert result["success"] is False
        assert "missing_clip" in result["error"]


class TestAutoEditInterviewTranscriptionFails:
    def test_propagates_transcription_error(self):
        tx_fail = {"success": False, "error": "Whisper broke"}
        with patch.object(resolve_client, "get_clip_path", return_value="/video.mp4"), \
             patch.object(analyzer, "transcribe_clip", return_value=tx_fail):
            result = tools._auto_edit_interview({"clip_name": "interview"})
        assert result["success"] is False
        assert result["error"] == "Whisper broke"


class TestAutoEditInterviewHappyPath:
    def _run(self, existing_timelines=None, timeline_name=None):
        inp = {"clip_name": "interview"}
        if timeline_name:
            inp["timeline_name"] = timeline_name

        transcription = _make_transcription()
        fillers = [transcription["segments"][1]]  # "eh" segment
        keep_ranges = [
            {"start": 0.0, "end": 2.0},
            {"start": 4.2, "end": 8.0},
        ]
        project_info = _make_project_info(timelines=existing_timelines or [])

        with patch.object(resolve_client, "get_clip_path", return_value="/video.mp4") as _gcp, \
             patch.object(analyzer, "transcribe_clip", return_value=transcription) as _tx, \
             patch.object(analyzer, "find_filler_segments", return_value=fillers) as _ff, \
             patch.object(analyzer, "compute_keep_ranges", return_value=keep_ranges) as _ckr, \
             patch.object(resolve_client, "get_project_info", return_value=project_info) as _pi, \
             patch.object(resolve_client, "create_timeline", return_value={"success": True}) as _ct, \
             patch.object(resolve_client, "set_current_timeline", return_value={"success": True}) as _sct, \
             patch.object(resolve_client, "add_clip_to_timeline", return_value={"success": True}) as _act:
            result = tools._auto_edit_interview(inp)

        return result, {"create_timeline": _ct, "set_current_timeline": _sct, "add_clip": _act}

    def test_success_flag(self):
        result, _ = self._run()
        assert result["success"] is True

    def test_creates_new_timeline_when_absent(self):
        result, mocks = self._run(existing_timelines=[])
        mocks["create_timeline"].assert_called_once()
        mocks["set_current_timeline"].assert_not_called()

    def test_switches_to_existing_timeline(self):
        result, mocks = self._run(existing_timelines=["Auto_interview"], timeline_name="Auto_interview")
        mocks["set_current_timeline"].assert_called_once_with("Auto_interview")
        mocks["create_timeline"].assert_not_called()

    def test_adds_one_clip_per_keep_range(self):
        result, mocks = self._run()
        assert mocks["add_clip"].call_count == 2

    def test_segments_added_count(self):
        result, _ = self._run()
        assert result["segments_added"] == 2

    def test_fillers_removed_count(self):
        result, _ = self._run()
        assert result["fillers_removed"] == 1

    def test_kept_duration_calculated(self):
        result, _ = self._run()
        # keep_ranges: (0.0–2.0) + (4.2–8.0) = 2.0 + 3.8 = 5.8
        assert math.isclose(result["kept_duration_sec"], 5.8, abs_tol=0.01)

    def test_removed_duration_calculated(self):
        result, _ = self._run()
        # filler: 2.5–4.0 = 1.5 s
        assert math.isclose(result["removed_duration_sec"], 1.5, abs_tol=0.01)

    def test_transcript_language_in_result(self):
        result, _ = self._run()
        assert result["transcript_language"] == "es"

    def test_default_timeline_name_uses_clip_name(self):
        result, _ = self._run(timeline_name=None)
        assert "interview" in result["timeline"]

    def test_add_clip_called_with_correct_ranges(self):
        result, mocks = self._run()
        calls = mocks["add_clip"].call_args_list
        assert calls[0] == call(clip_name="interview", in_point_sec=0.0, out_point_sec=2.0)
        assert calls[1] == call(clip_name="interview", in_point_sec=4.2, out_point_sec=8.0)

    def test_partial_failure_still_counts_added(self):
        """If some add_clip calls fail, only successful ones count toward segments_added."""
        transcription = _make_transcription()
        fillers = [transcription["segments"][1]]
        keep_ranges = [{"start": 0.0, "end": 2.0}, {"start": 4.2, "end": 8.0}]
        project_info = _make_project_info()
        side_effects = [{"success": True}, {"success": False, "error": "timeline full"}]

        with patch.object(resolve_client, "get_clip_path", return_value="/video.mp4"), \
             patch.object(analyzer, "transcribe_clip", return_value=transcription), \
             patch.object(analyzer, "find_filler_segments", return_value=fillers), \
             patch.object(analyzer, "compute_keep_ranges", return_value=keep_ranges), \
             patch.object(resolve_client, "get_project_info", return_value=project_info), \
             patch.object(resolve_client, "create_timeline", return_value={"success": True}), \
             patch.object(resolve_client, "add_clip_to_timeline", side_effect=side_effects):
            result = tools._auto_edit_interview({"clip_name": "interview"})

        assert result["success"] is True
        assert result["segments_added"] == 1
