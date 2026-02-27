
import unittest
from unittest.mock import patch, MagicMock, ANY
import sys
from pathlib import Path
import os
import shutil

# Mock dependencies
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Mock config
sys.modules['config'] = MagicMock()
from config import VIDEO_SETTINGS, AUDIO_SETTINGS, CAPTION_SETTINGS, TEMP_DIR, OUTPUT_DIR, BGM_DIR

# Setup paths
sys.path.append(str(Path(__file__).parent.parent))

# Import processor after mocking
from utils import processor

class TestProcessorPipeline(unittest.TestCase):
    def setUp(self):
        self.clip_info = {
            "caption_title": "Test Clip",
            "mood": "happy",
            "hook": "Test Hook",
            "reason": "Test Reason",
            "narrative_type": "Test Type"
        }
        self.segments = [{"start": 0, "end": 5, "text": "Hello world"}]
        self.output_dir = "out"

        # Ensure output dir exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    @patch('utils.processor._create_final_clip_optimized')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.select_bgm_by_mood')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor._get_video_duration')
    def test_optimized_pipeline_success(self, mock_duration, mock_thumb, mock_bgm_add, mock_bgm_select, mock_burn, mock_srt, mock_vertical, mock_optimized):
        """Test that create_final_clip calls optimized version first"""

        # Setup mocks
        # _create_final_clip_optimized should return the path to the video file (string), not a dict
        mock_optimized.return_value = "optimized.mp4"
        mock_duration.return_value = 10.0
        mock_bgm_select.return_value = "music.mp3"
        mock_thumb.return_value = "thumb.jpg"

        # Run
        processor.create_final_clip("input.mp4", self.clip_info, self.segments, 1, self.output_dir)

        # Verify optimized pipeline was called
        mock_optimized.assert_called_once()

        # Verify sequential pipeline was NOT called
        mock_vertical.assert_not_called()
        mock_burn.assert_not_called()
        mock_bgm_add.assert_not_called()

    @patch('utils.processor._create_final_clip_optimized')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.select_bgm_by_mood')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor._get_video_duration')
    def test_fallback_mechanism(self, mock_duration, mock_thumb, mock_bgm_add, mock_bgm_select, mock_burn, mock_srt, mock_vertical, mock_optimized):
        """Test that create_final_clip falls back to sequential if optimized fails"""

        # Setup mocks to simulate failure in optimized pipeline
        mock_optimized.side_effect = Exception("Optimization failed")

        # Setup sequential mocks
        mock_vertical.return_value = "vertical.mp4"
        mock_srt.return_value = "subs.srt"
        mock_burn.return_value = "captioned.mp4"
        mock_bgm_select.return_value = "music.mp3"
        mock_bgm_add.return_value = "final.mp4"
        mock_thumb.return_value = "thumb.jpg"
        mock_duration.return_value = 10.0

        # Run
        processor.create_final_clip("input.mp4", self.clip_info, self.segments, 1, self.output_dir)

        # Verify optimized pipeline was attempted
        mock_optimized.assert_called_once()

        # Verify sequential pipeline WAS called as fallback
        mock_vertical.assert_called_once()
        mock_srt.assert_called_once()

if __name__ == '__main__':
    unittest.main()
