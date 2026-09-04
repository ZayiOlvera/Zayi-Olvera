"""
Unit tests for pure helper functions in resolve_client.py.
No DaVinci Resolve installation is required.
"""
import sys
import os
import math
import pytest
from unittest.mock import MagicMock

# Stub the DaVinci Resolve module so resolve_client.py can be imported.
sys.modules.setdefault("DaVinciResolveScript", MagicMock())

import resolve_client  # noqa: E402


class TestSecToTimecode:
    def test_zero(self):
        assert resolve_client._sec_to_timecode(0.0, 24.0) == "00:00:00:00"

    def test_one_second_24fps(self):
        assert resolve_client._sec_to_timecode(1.0, 24.0) == "00:00:01:00"

    def test_one_minute(self):
        assert resolve_client._sec_to_timecode(60.0, 24.0) == "00:01:00:00"

    def test_one_hour(self):
        assert resolve_client._sec_to_timecode(3600.0, 24.0) == "01:00:00:00"

    def test_90_seconds_24fps(self):
        # 90 s × 24 fps = 2160 frames → 00:01:30:00
        assert resolve_client._sec_to_timecode(90.0, 24.0) == "00:01:30:00"

    def test_sub_second_frames(self):
        # 1.5 s at 24 fps → 36 frames → 00:00:01:12
        assert resolve_client._sec_to_timecode(1.5, 24.0) == "00:00:01:12"

    def test_30fps(self):
        # 61 s at 30 fps → 00:01:01:00
        assert resolve_client._sec_to_timecode(61.0, 30.0) == "00:01:01:00"

    def test_frame_component_30fps(self):
        # 1.1 s at 30 fps → 33 frames → 00:00:01:03
        assert resolve_client._sec_to_timecode(1.1, 30.0) == "00:00:01:03"

    def test_large_value(self):
        # 3661 s at 30 fps → 01:01:01:00
        assert resolve_client._sec_to_timecode(3661.0, 30.0) == "01:01:01:00"

    def test_format_zero_padded(self):
        tc = resolve_client._sec_to_timecode(5.0, 24.0)
        parts = tc.split(":")
        assert len(parts) == 4
        assert all(len(p) == 2 for p in parts)


class TestFramesToSec:
    def _mock_project(self, fps=24.0):
        project = MagicMock()
        project.GetSetting.return_value = str(fps)
        return project

    def test_basic(self):
        project = self._mock_project(24.0)
        result = resolve_client._frames_to_sec(48, project)
        assert math.isclose(result, 2.0, rel_tol=1e-6)

    def test_zero_frames(self):
        project = self._mock_project(24.0)
        assert resolve_client._frames_to_sec(0, project) == 0.0

    def test_30fps(self):
        project = self._mock_project(30.0)
        result = resolve_client._frames_to_sec(90, project)
        assert math.isclose(result, 3.0, rel_tol=1e-6)

    def test_exception_returns_zero(self):
        project = MagicMock()
        project.GetSetting.side_effect = RuntimeError("broken")
        result = resolve_client._frames_to_sec("bad", project)
        assert result == 0.0


class TestFps:
    def test_reads_from_project(self):
        project = MagicMock()
        project.GetSetting.return_value = "29.97"
        fps = resolve_client._fps(project)
        assert math.isclose(fps, 29.97, rel_tol=1e-6)

    def test_exception_defaults_to_24(self):
        project = MagicMock()
        project.GetSetting.side_effect = ValueError("nope")
        assert resolve_client._fps(project) == 24.0
