import sys
from unittest.mock import MagicMock

# Mock requests and config before importing ai_logic
mock_requests = MagicMock()
sys.modules["requests"] = mock_requests

sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()

mock_config = MagicMock()
mock_config.CHUTES_API_KEY = "test_key"
mock_config.CHUTES_BASE_URL = "test_url"
mock_config.WHISPER_MODEL = "test_model"
mock_config.LLM_MODEL = "test_model"
mock_config.VIDEO_SETTINGS = {"min_clip_duration": 10, "max_clip_duration": 60}
sys.modules["config"] = mock_config

import pytest
import json
import os

# Add the parent directory to sys.path to allow importing from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.ai_logic import _parse_clips_json

def test_parse_clips_json_valid_direct_list():
    """Test parsing a valid JSON array directly."""
    content = '[{"start": 0, "end": 10, "caption_title": "Test"}]'
    result = _parse_clips_json(content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["caption_title"] == "Test"

def test_parse_clips_json_with_text_around():
    """Test extracting a JSON array from surrounding text."""
    content = 'Here are the clips: [{"start": 0, "end": 10, "caption_title": "Test"}] hope you like them.'
    result = _parse_clips_json(content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["caption_title"] == "Test"

def test_parse_clips_json_invalid_json():
    """Test handling of completely invalid JSON."""
    content = 'Not a JSON at all'
    result = _parse_clips_json(content)
    assert result == []

def test_parse_clips_json_malformed_json_in_brackets():
    """Test handling of malformed JSON that looks like an array."""
    content = 'Clips: [{"start": 0, "end": 10, "caption_title": "Test"' # Missing closing brace/bracket
    result = _parse_clips_json(content)
    assert result == []

def test_parse_clips_json_empty_string():
    """Test handling of an empty string."""
    content = ''
    result = _parse_clips_json(content)
    assert result == []

def test_parse_clips_json_with_markdown_blocks():
    """Test extracting JSON from markdown code blocks."""
    content = '```json\n[{"start": 0, "end": 10, "caption_title": "Test"}]\n```'
    result = _parse_clips_json(content)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["caption_title"] == "Test"

def test_parse_clips_json_wrapped_in_object():
    """Test handling cases where the LLM returns an object instead of a list."""
    # If the LLM returns an object like this, we should try to find the list inside.
    content = '{"clips": [{"start": 0, "end": 10, "caption_title": "Test"}]}'
    result = _parse_clips_json(content)
    # The current implementation returns a dict, but we want it to return a list.
    # This test will initially fail (or assert the current behavior if we want)
    # Let's assert what we WANT it to do.
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["caption_title"] == "Test"

def test_parse_clips_json_direct_object_no_clips_key():
    """Test handling cases where the LLM returns an object that is NOT the expected format."""
    content = '{"some_other_key": "some_value"}'
    result = _parse_clips_json(content)
    # Should probably return empty list if it's not a list and doesn't contain a obvious list.
    assert result == []
