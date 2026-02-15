import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import module under test
# We don't mock sys.modules['requests'] here because we want to patch it specifically
# or we can mock it if we don't want real requests at all (which we don't).
# However, ai_logic imports requests.

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

if __name__ == '__main__':
    unittest.main()
