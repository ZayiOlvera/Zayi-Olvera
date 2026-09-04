"""
Tests for config.py — default values and environment variable overrides.
"""
import os
import sys
import math
import importlib
import pytest


def _reload_config(monkeypatch, env_vars: dict):
    """Re-import config with specific environment variables set."""
    for key, val in env_vars.items():
        monkeypatch.setenv(key, val)
    # Remove cached module so it is re-evaluated with new env
    if "config" in sys.modules:
        del sys.modules["config"]
    import config as cfg
    return cfg


class TestConfigDefaults:
    def test_claude_model(self):
        import config
        assert config.CLAUDE_MODEL == "claude-sonnet-4-6"

    def test_whisper_model_default(self, monkeypatch):
        monkeypatch.delenv("WHISPER_MODEL", raising=False)
        cfg = _reload_config(monkeypatch, {})
        assert cfg.WHISPER_MODEL == "small"

    def test_whisper_language_default(self, monkeypatch):
        monkeypatch.delenv("WHISPER_LANGUAGE", raising=False)
        cfg = _reload_config(monkeypatch, {})
        assert cfg.WHISPER_LANGUAGE == "es"

    def test_scene_detect_threshold_default(self, monkeypatch):
        monkeypatch.delenv("SCENE_DETECT_THRESHOLD", raising=False)
        cfg = _reload_config(monkeypatch, {})
        assert math.isclose(cfg.SCENE_DETECT_THRESHOLD, 27.0)

    def test_silence_threshold_default(self, monkeypatch):
        monkeypatch.delenv("SILENCE_THRESHOLD_DB", raising=False)
        cfg = _reload_config(monkeypatch, {})
        assert math.isclose(cfg.SILENCE_THRESHOLD_DB, -40.0)

    def test_silence_min_duration_default(self, monkeypatch):
        monkeypatch.delenv("SILENCE_MIN_DURATION_SEC", raising=False)
        cfg = _reload_config(monkeypatch, {})
        assert math.isclose(cfg.SILENCE_MIN_DURATION_SEC, 0.5)


class TestConfigEnvOverrides:
    def test_whisper_model_override(self, monkeypatch):
        cfg = _reload_config(monkeypatch, {"WHISPER_MODEL": "large-v3"})
        assert cfg.WHISPER_MODEL == "large-v3"

    def test_whisper_language_override(self, monkeypatch):
        cfg = _reload_config(monkeypatch, {"WHISPER_LANGUAGE": "en"})
        assert cfg.WHISPER_LANGUAGE == "en"

    def test_scene_detect_threshold_override(self, monkeypatch):
        cfg = _reload_config(monkeypatch, {"SCENE_DETECT_THRESHOLD": "15.0"})
        assert math.isclose(cfg.SCENE_DETECT_THRESHOLD, 15.0)

    def test_silence_threshold_override(self, monkeypatch):
        cfg = _reload_config(monkeypatch, {"SILENCE_THRESHOLD_DB": "-50.0"})
        assert math.isclose(cfg.SILENCE_THRESHOLD_DB, -50.0)

    def test_api_key_override(self, monkeypatch):
        cfg = _reload_config(monkeypatch, {"ANTHROPIC_API_KEY": "sk-test-1234"})
        assert cfg.ANTHROPIC_API_KEY == "sk-test-1234"


class TestFillerWords:
    def test_filler_words_is_list(self):
        import config
        assert isinstance(config.FILLER_WORDS, list)

    def test_filler_words_not_empty(self):
        import config
        assert len(config.FILLER_WORDS) > 0

    def test_common_fillers_present(self):
        import config
        fillers_lower = [f.lower() for f in config.FILLER_WORDS]
        for expected in ("eh", "um", "pues", "o sea"):
            assert expected in fillers_lower, f"Expected filler '{expected}' not found"

    def test_all_fillers_are_strings(self):
        import config
        assert all(isinstance(f, str) for f in config.FILLER_WORDS)
