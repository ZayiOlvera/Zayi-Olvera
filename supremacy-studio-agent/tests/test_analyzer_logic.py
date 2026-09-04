"""
Unit tests for pure-logic functions in analyzer.py.
No external dependencies (no Whisper, librosa, cv2, etc.) are required.
"""
import sys
import os
import pytest

# Stub out heavy optional imports so analyzer.py can be imported in CI
# without the ML packages installed.
for _mod in ("faster_whisper", "scenedetect", "librosa", "cv2", "soundfile"):
    if _mod not in sys.modules:
        from unittest.mock import MagicMock
        sys.modules[_mod] = MagicMock()
# numpy is used inline; provide a lightweight stub if missing
try:
    import numpy  # noqa: F401
except ImportError:
    sys.modules["numpy"] = MagicMock()

import analyzer  # noqa: E402


# ---------------------------------------------------------------------------
# find_filler_segments
# ---------------------------------------------------------------------------

class TestFindFillerSegments:
    def _seg(self, text, start=0.0, end=1.0):
        return {"text": text, "start": start, "end": end}

    def test_exact_filler_match(self):
        segs = [self._seg("eh"), self._seg("hola")]
        result = analyzer.find_filler_segments(segs)
        assert len(result) == 1
        assert result[0]["text"] == "eh"

    def test_filler_as_prefix(self):
        # "o sea que más" starts with filler "o sea"
        segs = [self._seg("o sea que más")]
        result = analyzer.find_filler_segments(segs)
        assert len(result) == 1

    def test_filler_as_suffix(self):
        # "bueno pues" ends with filler "pues"
        segs = [self._seg("bueno pues")]
        result = analyzer.find_filler_segments(segs)
        assert len(result) == 1

    def test_non_filler_passes_through(self):
        segs = [self._seg("el equipo terminó el proyecto")]
        result = analyzer.find_filler_segments(segs)
        assert result == []

    def test_short_noise_removed(self):
        # 2 words, duration < 0.8 s → short noise
        segs = [self._seg("ok sí", start=0.0, end=0.5)]
        result = analyzer.find_filler_segments(segs)
        assert len(result) == 1

    def test_short_noise_kept_when_long_enough(self):
        # 2 words but duration >= 0.8 s → not short noise
        segs = [self._seg("ok sí", start=0.0, end=1.0)]
        result = analyzer.find_filler_segments(segs)
        assert result == []

    def test_empty_segments(self):
        assert analyzer.find_filler_segments([]) == []

    def test_multiple_fillers(self):
        segs = [
            self._seg("eh"),
            self._seg("um"),
            self._seg("esto es importante"),
        ]
        result = analyzer.find_filler_segments(segs)
        assert len(result) == 2

    def test_case_insensitive(self):
        segs = [self._seg("EH"), self._seg("Um")]
        result = analyzer.find_filler_segments(segs)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# compute_keep_ranges
# ---------------------------------------------------------------------------

class TestComputeKeepRanges:
    def _seg(self, start, end, text="hola"):
        return {"start": start, "end": end, "text": text}

    def test_no_fillers_one_range(self):
        segs = [self._seg(0.0, 2.0), self._seg(2.1, 4.0)]
        result = analyzer.compute_keep_ranges(segs, [], 4.0)
        assert len(result) == 1
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 4.0

    def test_all_filtered_fallback(self):
        segs = [self._seg(0.0, 1.0), self._seg(1.5, 2.5)]
        result = analyzer.compute_keep_ranges(segs, segs, 2.5)
        # Fallback: keep everything
        assert len(result) == 1
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 2.5

    def test_gap_above_threshold_splits_ranges(self):
        # Gap of 1.0 s between seg1 and seg2 exceeds default threshold 0.4 s
        segs = [
            self._seg(0.0, 2.0),
            self._seg(3.0, 5.0),  # gap = 1.0 s
        ]
        result = analyzer.compute_keep_ranges(segs, [], 5.0)
        assert len(result) == 2
        assert result[0] == {"start": 0.0, "end": 2.0}
        assert result[1] == {"start": 3.0, "end": 5.0}

    def test_gap_below_threshold_merged(self):
        # Gap of 0.2 s < 0.4 s → merged into one range
        segs = [
            self._seg(0.0, 2.0),
            self._seg(2.2, 4.0),
        ]
        result = analyzer.compute_keep_ranges(segs, [], 4.0)
        assert len(result) == 1
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 4.0

    def test_filler_removed_mid_sequence(self):
        # Gap from seg0.end (2.0) to seg2.start (2.3) = 0.3 s < threshold 0.4 s → merged
        segs = [
            self._seg(0.0, 2.0),
            self._seg(2.1, 2.2, text="eh"),  # filler
            self._seg(2.3, 5.0),
        ]
        fillers = [segs[1]]
        result = analyzer.compute_keep_ranges(segs, fillers, 5.0)
        # The two good segments have a gap of 0.3 s (below threshold) → one merged range
        assert len(result) == 1
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 5.0

    def test_single_segment(self):
        segs = [self._seg(1.0, 3.0)]
        result = analyzer.compute_keep_ranges(segs, [], 3.0)
        assert result == [{"start": 1.0, "end": 3.0}]

    def test_empty_segments_returns_empty(self):
        result = analyzer.compute_keep_ranges([], [], 0.0)
        assert result == []

    def test_custom_gap_threshold(self):
        # With a large threshold, even a 2 s gap gets merged
        segs = [self._seg(0.0, 1.0), self._seg(3.0, 5.0)]
        result = analyzer.compute_keep_ranges(segs, [], 5.0, silence_gap_threshold=5.0)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _audio_recommendation
# ---------------------------------------------------------------------------

class TestAudioRecommendation:
    def test_clipping(self):
        msg = analyzer._audio_recommendation(peak_db=0.0, rms_db=-20.0)
        assert "clippeado" in msg

    def test_too_quiet(self):
        msg = analyzer._audio_recommendation(peak_db=-6.0, rms_db=-35.0)
        assert "bajo" in msg

    def test_too_loud(self):
        msg = analyzer._audio_recommendation(peak_db=-6.0, rms_db=-10.0)
        assert "alto" in msg

    def test_ok_levels(self):
        msg = analyzer._audio_recommendation(peak_db=-6.0, rms_db=-20.0)
        assert "correctos" in msg

    def test_boundary_clipping(self):
        # Exactly -1 dB should NOT trigger clipping (condition is peak > -1)
        msg = analyzer._audio_recommendation(peak_db=-1.0, rms_db=-20.0)
        assert "correctos" in msg

    def test_boundary_quiet(self):
        # Exactly -30 dB RMS should NOT trigger "too quiet" (condition is rms < -30)
        msg = analyzer._audio_recommendation(peak_db=-6.0, rms_db=-30.0)
        assert "correctos" in msg
