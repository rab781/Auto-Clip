import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).parent.parent))

# Mock heavy dependencies BEFORE importing from main
sys.modules['tqdm'] = MagicMock()
sys.modules['utils'] = MagicMock()
sys.modules['config'] = MagicMock()

from main import process_single_clip

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SEGMENTS = [
    {"start": 0,  "end": 5,  "text": "intro"},
    {"start": 10, "end": 15, "text": "segment one"},
    {"start": 20, "end": 25, "text": "segment two"},
    {"start": 30, "end": 35, "text": "segment three"},
]
START_TIMES = [s["start"] for s in SEGMENTS]   # [0, 10, 20, 30]


def _transcription(segments=None):
    return {"segments": segments if segments is not None else list(SEGMENTS)}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch('main.create_final_clip', return_value={"video": "v", "thumbnail": "t", "caption_file": "c"})
@patch('main.translate_segments', side_effect=lambda s: s)
@patch('main.generate_clip_caption', return_value="Caption")
@patch('main.download_video_segment')
def test_start_times_fast_path_uses_precomputed_list(
    mock_dl, mock_cap, mock_trans, mock_create
):
    """When start_times is provided, bisect_left is called with the precomputed list."""
    clip = {"start": 10, "end": 26}

    with patch('main.bisect') as mock_bisect_mod:
        mock_bisect_mod.bisect_left.return_value = 1
        process_single_clip(1, clip, "https://example.com", _transcription(), START_TIMES)

    mock_bisect_mod.bisect_left.assert_called_once_with(START_TIMES, clip["start"])


@patch('main.create_final_clip', return_value={"video": "v", "thumbnail": "t", "caption_file": "c"})
@patch('main.translate_segments', side_effect=lambda s: s)
@patch('main.generate_clip_caption', return_value="Caption")
@patch('main.download_video_segment')
def test_start_times_none_falls_back_to_per_call_extraction(
    mock_dl, mock_cap, mock_trans, mock_create
):
    """When start_times is None, bisect_left receives a freshly extracted key list."""
    clip = {"start": 10, "end": 26}

    with patch('main.bisect') as mock_bisect_mod:
        mock_bisect_mod.bisect_left.return_value = 1
        process_single_clip(1, clip, "https://example.com", _transcription(), start_times=None)

    args, _ = mock_bisect_mod.bisect_left.call_args
    # The first argument must be a new list equal to START_TIMES but not the same object
    assert args[0] == START_TIMES
    assert args[0] is not START_TIMES


@patch('main.create_final_clip', return_value={"video": "v", "thumbnail": "t", "caption_file": "c"})
@patch('main.translate_segments', side_effect=lambda s: s)
@patch('main.generate_clip_caption', return_value="Caption")
@patch('main.download_video_segment')
def test_empty_start_times_takes_fast_path_not_fallback(
    mock_dl, mock_cap, mock_trans, mock_create
):
    """An empty (but non-None) start_times must use the fast path, not the O(N) fallback."""
    clip = {"start": 5, "end": 15}
    empty_start_times = []
    transcription = _transcription([])  # no segments either

    with patch('main.bisect') as mock_bisect_mod:
        mock_bisect_mod.bisect_left.return_value = 0
        process_single_clip(1, clip, "https://example.com", transcription, empty_start_times)

    # bisect_left must have been called with the exact same object
    args, _ = mock_bisect_mod.bisect_left.call_args
    assert args[0] is empty_start_times


@patch('main.create_final_clip', return_value={"video": "v", "thumbnail": "t", "caption_file": "c"})
@patch('main.translate_segments', side_effect=lambda s: s)
@patch('main.generate_clip_caption', return_value="Caption")
@patch('main.download_video_segment')
def test_correct_segment_matching_with_start_times(
    mock_dl, mock_cap, mock_trans, mock_create
):
    """Segments within [clip.start, clip.end] are correctly extracted and time-shifted."""
    clip = {"start": 10, "end": 26}
    # Expected: segments at [10,15] and [20,25] are included; [30,35] triggers early exit
    result = process_single_clip(1, clip, "https://example.com", _transcription(), START_TIMES)

    assert result is not None
    mock_create.assert_called_once()
    _, kwargs = mock_create.call_args
    segs = kwargs["segments"]
    assert len(segs) == 2
    # Times are relative to clip start (10)
    assert segs[0] == {"start": 0,  "end": 5,  "text": "segment one"}
    assert segs[1] == {"start": 10, "end": 15, "text": "segment two"}


@patch('main.create_final_clip', return_value={"video": "v", "thumbnail": "t", "caption_file": "c"})
@patch('main.translate_segments', side_effect=lambda s: s)
@patch('main.generate_clip_caption', return_value="Caption")
@patch('main.download_video_segment')
def test_clip_number_not_shadowed_by_loop_variable(
    mock_dl, mock_cap, mock_trans, mock_create
):
    """The `i` parameter (clip number) must not be clobbered by the inner loop variable."""
    clip = {"start": 10, "end": 26}
    clip_number = 7  # distinct value easy to assert on

    result = process_single_clip(clip_number, clip, "https://example.com", _transcription(), START_TIMES)

    assert result is not None
    mock_create.assert_called_once()
    _, kwargs = mock_create.call_args
    assert kwargs["clip_number"] == clip_number
