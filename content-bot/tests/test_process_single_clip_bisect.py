import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock heavy/external deps BEFORE importing main
sys.modules.setdefault('tqdm', MagicMock())
sys.modules.setdefault('utils', MagicMock())
sys.modules.setdefault('config', MagicMock())

from main import process_single_clip  # noqa: E402 (import after sys.modules patching)


def _make_transcription(segment_starts):
    """Return a transcription dict with segments at the given start times (each 2s long)."""
    return {
        "segments": [
            {"start": float(s), "end": float(s) + 2.0, "text": f"word at {float(s)}"}
            for s in segment_starts
        ]
    }


class TestProcessSingleClipBisect(unittest.TestCase):
    """Unit tests for the start_times binary-search optimization in process_single_clip."""

    def setUp(self):
        # Segments at 0, 5, 10, 15, 20, 25, 30 seconds
        segment_starts = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
        self.transcription = _make_transcription(segment_starts)
        self.start_times = [s["start"] for s in self.transcription["segments"]]
        self.clip = {"start": 10.0, "end": 22.0, "caption_title": "Test Clip"}
        self.url = "https://youtube.com/watch?v=test"

    # ------------------------------------------------------------------
    # Helpers to create a consistent set of patches for each test
    # ------------------------------------------------------------------
    def _patch_deps(self):
        """Start patches for main's dependencies and return (patches, mocks) tuple.

        Returns:
            patches: list of active patch objects (stop them in a finally block)
            mocks: dict with keys 'download', 'caption', 'translate', 'create'
        """
        p_download = patch('main.download_video_segment')
        p_caption = patch('main.generate_clip_caption', return_value="Enhanced caption")
        p_translate = patch('main.translate_segments', side_effect=lambda segs: segs)
        p_create = patch('main.create_final_clip', return_value={
            "video": "/out/v.mp4",
            "thumbnail": "/out/t.jpg",
            "caption_file": "/out/c.txt",
        })
        patches = [p_download, p_caption, p_translate, p_create]
        mocks = {
            'download': p_download.start(),
            'caption': p_caption.start(),
            'translate': p_translate.start(),
            'create': p_create.start(),
        }
        return patches, mocks

    # ------------------------------------------------------------------
    # Tests: bisect call path
    # ------------------------------------------------------------------

    def test_with_start_times_calls_bisect_on_precalculated_list(self):
        """When start_times is provided, bisect should use that list directly."""
        patches, _ = self._patch_deps()
        try:
            with patch('main.bisect') as mock_bisect_mod:
                mock_bisect_mod.bisect_left.return_value = 2  # index of 10.0
                process_single_clip(
                    1, dict(self.clip), self.url, self.transcription, self.start_times
                )
                mock_bisect_mod.bisect_left.assert_called_once_with(self.start_times, 10.0)
        finally:
            for p in reversed(patches):
                p.stop()

    def test_without_start_times_computes_local_list_for_bisect(self):
        """When start_times is None, bisect should receive a locally computed list."""
        patches, _ = self._patch_deps()
        try:
            with patch('main.bisect') as mock_bisect_mod:
                mock_bisect_mod.bisect_left.return_value = 2
                process_single_clip(
                    1, dict(self.clip), self.url, self.transcription, None
                )
                args, _ = mock_bisect_mod.bisect_left.call_args
                called_list, called_val = args
                # Content should match the precalculated list …
                self.assertEqual(called_list, self.start_times)
                self.assertEqual(called_val, 10.0)
                # … but must be a newly built object, not the external list
                self.assertIsNot(called_list, self.start_times)
        finally:
            for p in reversed(patches):
                p.stop()

    # ------------------------------------------------------------------
    # Tests: segment matching correctness
    # ------------------------------------------------------------------

    def _get_segments_passed_to_create_final_clip(self, start_times_arg):
        """Run process_single_clip and return the `segments` kwarg passed to create_final_clip."""
        patches, mocks = self._patch_deps()
        try:
            process_single_clip(
                1, dict(self.clip), self.url, self.transcription, start_times_arg
            )
            return mocks['create'].call_args[1]["segments"]
        finally:
            for p in reversed(patches):
                p.stop()

    def test_correct_segments_matched_with_start_times(self):
        """Only segments whose times fall within the clip are included (fast path)."""
        segments = self._get_segments_passed_to_create_final_clip(self.start_times)
        # Clip [10, 22]: seg end must be <= 22.0
        # seg@10 end=12 ✓, seg@15 end=17 ✓, seg@20 end=22 ✓, seg@25 start>22 → break
        self.assertEqual(len(segments), 3)
        texts = {s["text"] for s in segments}
        self.assertEqual(texts, {"word at 10.0", "word at 15.0", "word at 20.0"})

    def test_correct_segments_matched_without_start_times(self):
        """Only segments whose times fall within the clip are included (fallback path)."""
        segments = self._get_segments_passed_to_create_final_clip(None)
        self.assertEqual(len(segments), 3)
        texts = {s["text"] for s in segments}
        self.assertEqual(texts, {"word at 10.0", "word at 15.0", "word at 20.0"})

    def test_segment_times_normalized_to_clip_start(self):
        """Segment start/end times must be offset relative to the clip's start time."""
        segments = self._get_segments_passed_to_create_final_clip(self.start_times)
        for seg in segments:
            self.assertGreaterEqual(seg["start"], 0.0)
            self.assertLessEqual(seg["end"], self.clip["end"] - self.clip["start"])

        # Spot-check the first matched segment (original start=10.0 → normalized 0.0)
        first = next(s for s in segments if s["text"] == "word at 10.0")
        self.assertAlmostEqual(first["start"], 0.0)
        self.assertAlmostEqual(first["end"], 2.0)

    def test_segment_beyond_clip_end_excluded_by_early_stop(self):
        """Segments with start > clip end are never included (early-stop optimization)."""
        segments = self._get_segments_passed_to_create_final_clip(self.start_times)
        starts = [s["start"] + self.clip["start"] for s in segments]
        self.assertTrue(all(t <= self.clip["end"] for t in starts))

    def test_empty_transcription_produces_empty_segments(self):
        """When transcription has no segments key, clip_segments should be empty."""
        patches, mocks = self._patch_deps()
        try:
            process_single_clip(
                1, dict(self.clip), self.url, {}, []
            )
            segments = mocks['create'].call_args[1]["segments"]
            self.assertEqual(segments, [])
        finally:
            for p in reversed(patches):
                p.stop()

    def test_empty_start_times_list_uses_bisect_on_it(self):
        """An empty start_times=[] (falsy but not None) must still use the fast path.

        This verifies the `is not None` guard: if we used `if start_times:` an
        empty list would incorrectly fall through to the local-computation branch.
        """
        patches, _ = self._patch_deps()
        try:
            # Transcription with one segment; clip starts before that segment
            transcription = _make_transcription([5.0])
            clip = {"start": 0.0, "end": 3.0, "caption_title": "Early clip"}
            with patch('main.bisect') as mock_bisect_mod:
                mock_bisect_mod.bisect_left.return_value = 0
                process_single_clip(1, clip, self.url, transcription, [])
                # bisect_left must have been called with the empty list we passed
                mock_bisect_mod.bisect_left.assert_called_once_with([], 0.0)
        finally:
            for p in reversed(patches):
                p.stop()

    # ------------------------------------------------------------------
    # Tests: error handling
    # ------------------------------------------------------------------

    def test_download_failure_returns_none(self):
        """A download failure should cause process_single_clip to return None."""
        with patch('main.download_video_segment', side_effect=Exception("Network error")):
            result = process_single_clip(
                1, dict(self.clip), self.url, self.transcription, self.start_times
            )
        self.assertIsNone(result)

    def test_create_final_clip_failure_returns_none(self):
        """A failure in create_final_clip should cause process_single_clip to return None."""
        patches, mocks = self._patch_deps()
        mocks['create'].side_effect = Exception("FFmpeg crashed")
        try:
            result = process_single_clip(
                1, dict(self.clip), self.url, self.transcription, self.start_times
            )
            self.assertIsNone(result)
        finally:
            for p in reversed(patches):
                p.stop()


if __name__ == '__main__':
    unittest.main()
