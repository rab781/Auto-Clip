
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add content-bot to sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Mock environment variables to avoid real API calls or config errors
with patch.dict(os.environ, {"CHUTES_API_KEY": "fake_key", "CHUTES_BASE_URL": "https://fake.url"}):
    from utils import ai_logic

class TestAILogicSecurity(unittest.TestCase):

    @patch('requests.post')
    def test_analyze_content_for_clips_timeout(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "[]"}}]
        }
        mock_post.return_value = mock_response

        # Call the function with dummy video_info
        transcription = {"text": "some text", "segments": []}
        video_info = {"duration": 60, "title": "Test Video"}
        ai_logic.analyze_content_for_clips(transcription, video_info)

        # Check if timeout was passed
        args, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs, "analyze_content_for_clips: timeout argument missing!")
        # We expect a timeout around 120-180s for heavy analysis
        self.assertGreaterEqual(kwargs['timeout'], 60, "analyze_content_for_clips: timeout too short!")

    @patch('requests.post')
    def test_generate_clip_caption_timeout(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Great video!"}}]
        }
        mock_post.return_value = mock_response

        # Call the function
        clip_info = {"caption_title": "Title", "hook": "hook", "narrative_type": "story", "reason": "reason"}
        transcript_segment = "segment text"
        ai_logic.generate_clip_caption(clip_info, transcript_segment)

        # Check if timeout was passed
        args, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs, "generate_clip_caption: timeout argument missing!")
        self.assertGreaterEqual(kwargs['timeout'], 30, "generate_clip_caption: timeout too short!")

if __name__ == '__main__':
    unittest.main()
