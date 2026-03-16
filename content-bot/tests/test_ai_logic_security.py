import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import module under test
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

from utils import ai_logic

class TestAILogicSecurity(unittest.TestCase):

    @patch('utils.ai_logic.requests.post')
    def test_analyze_content_for_clips_timeout(self, mock_post):
        """
        Test that analyze_content_for_clips calls requests.post with a timeout.
        """
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "[]"}}]
        }
        mock_post.return_value = mock_response

        # Dummy input
        transcription = {"text": "dummy text"}
        video_info = {"duration": 100}

        # Call function
        ai_logic.analyze_content_for_clips(transcription, video_info)

        # Verify timeout argument
        args, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs, "requests.post should be called with a timeout")
        self.assertGreater(kwargs['timeout'], 0, "Timeout should be positive")

    @patch('utils.ai_logic.requests.post')
    def test_generate_clip_caption_timeout(self, mock_post):
        """
        Test that generate_clip_caption calls requests.post with a timeout.
        """
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Cool caption"}}]
        }
        mock_post.return_value = mock_response

        # Dummy input
        clip_info = {"caption_title": "Title"}
        transcript_segment = "segment text"

        # Call function
        ai_logic.generate_clip_caption(clip_info, transcript_segment)

        # Verify timeout argument
        args, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs, "requests.post should be called with a timeout")
        self.assertGreater(kwargs['timeout'], 0, "Timeout should be positive")

class TestSanitizeErrorMsg(unittest.TestCase):

    def setUp(self):
        # Temporarily set a known API key for testing redaction
        self._original_key = ai_logic.CHUTES_API_KEY
        ai_logic.CHUTES_API_KEY = "super-secret-key-12345"

    def tearDown(self):
        ai_logic.CHUTES_API_KEY = self._original_key

    def test_key_is_redacted(self):
        msg = "Error: Authorization failed for key super-secret-key-12345"
        result = ai_logic._sanitize_error_msg(msg)
        self.assertNotIn("super-secret-key-12345", result)
        self.assertIn("[REDACTED_API_KEY]", result)

    def test_key_appearing_multiple_times_is_fully_redacted(self):
        msg = "Key super-secret-key-12345 used twice: super-secret-key-12345"
        result = ai_logic._sanitize_error_msg(msg)
        self.assertNotIn("super-secret-key-12345", result)
        self.assertEqual(result.count("[REDACTED_API_KEY]"), 2)

    def test_key_near_truncation_boundary_is_redacted_before_truncation(self):
        # Build a message where the API key spans the 100-char boundary.
        # Prefix of exactly 95 chars, then the key starts at position 95.
        prefix = "x" * 95
        msg = prefix + "super-secret-key-12345" + " extra text"
        # If truncation happened first (old behaviour), the key would be split and survive.
        # With the fix, full sanitization happens before truncation.
        sanitized_full = ai_logic._sanitize_error_msg(msg)
        truncated = sanitized_full[:100]
        self.assertNotIn("super-secret-key-12345", truncated)

    def test_message_without_key_is_unchanged(self):
        msg = "Some generic error occurred"
        result = ai_logic._sanitize_error_msg(msg)
        self.assertEqual(result, msg)

    def test_empty_string_returns_empty(self):
        result = ai_logic._sanitize_error_msg("")
        self.assertEqual(result, "")

    def test_none_returns_none(self):
        result = ai_logic._sanitize_error_msg(None)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
