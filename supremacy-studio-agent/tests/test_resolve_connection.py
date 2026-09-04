"""
Tests for resolve_client.connect() and related connection-failure scenarios.
All DaVinci Resolve interactions are mocked.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.modules.setdefault("DaVinciResolveScript", MagicMock())

import resolve_client  # noqa: E402


class TestConnect:
    def test_missing_module_raises(self):
        with patch.object(resolve_client, "_load_resolve_module", return_value=None):
            with pytest.raises(RuntimeError, match="módulo de DaVinci Resolve"):
                resolve_client.connect()

    def test_resolve_not_running_raises(self):
        dvr = MagicMock()
        dvr.scriptapp.return_value = None
        with patch.object(resolve_client, "_load_resolve_module", return_value=dvr):
            with pytest.raises(RuntimeError, match="no está corriendo"):
                resolve_client.connect()

    def test_no_open_project_raises(self):
        dvr = MagicMock()
        resolve = MagicMock()
        pm = MagicMock()
        pm.GetCurrentProject.return_value = None
        resolve.GetProjectManager.return_value = pm
        dvr.scriptapp.return_value = resolve
        with patch.object(resolve_client, "_load_resolve_module", return_value=dvr):
            with pytest.raises(RuntimeError, match="proyecto abierto"):
                resolve_client.connect()

    def test_successful_connect(self):
        dvr = MagicMock()
        resolve = MagicMock()
        project = MagicMock()
        media_pool = MagicMock()
        timeline = MagicMock()
        pm = MagicMock()
        pm.GetCurrentProject.return_value = project
        resolve.GetProjectManager.return_value = pm
        project.GetMediaPool.return_value = media_pool
        project.GetCurrentTimeline.return_value = timeline
        dvr.scriptapp.return_value = resolve
        with patch.object(resolve_client, "_load_resolve_module", return_value=dvr):
            result = resolve_client.connect()
        assert result == (resolve, project, media_pool, timeline)


class TestGetClipPath:
    def _make_clips(self):
        return [
            {"name": "Interview_Raw.mp4", "file_path": "/videos/Interview_Raw.mp4", "duration_sec": 300.0, "type": "Video", "fps": "24"},
            {"name": "BRoll_Office.mp4", "file_path": "/videos/BRoll_Office.mp4", "duration_sec": 60.0, "type": "Video", "fps": "24"},
        ]

    def test_exact_match(self):
        with patch.object(resolve_client, "list_media_pool_clips", return_value=self._make_clips()):
            path = resolve_client.get_clip_path("Interview_Raw.mp4")
        assert path == "/videos/Interview_Raw.mp4"

    def test_partial_match(self):
        with patch.object(resolve_client, "list_media_pool_clips", return_value=self._make_clips()):
            path = resolve_client.get_clip_path("Interview")
        assert path == "/videos/Interview_Raw.mp4"

    def test_case_insensitive(self):
        with patch.object(resolve_client, "list_media_pool_clips", return_value=self._make_clips()):
            path = resolve_client.get_clip_path("interview_raw.mp4")
        assert path == "/videos/Interview_Raw.mp4"

    def test_no_match_returns_none(self):
        with patch.object(resolve_client, "list_media_pool_clips", return_value=self._make_clips()):
            path = resolve_client.get_clip_path("NonExistentClip")
        assert path is None

    def test_empty_pool_returns_none(self):
        with patch.object(resolve_client, "list_media_pool_clips", return_value=[]):
            path = resolve_client.get_clip_path("anything")
        assert path is None
