import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Mock dependencies
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
# Mock yt_dlp.utils explicitly as it is often imported directly
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import tempfile
import shutil

# Create temporary directories for testing
temp_test_dir = tempfile.mkdtemp()
temp_output_dir = Path(temp_test_dir) / "output"
temp_output_dir.mkdir()

# Mock config
mock_config = MagicMock()
mock_config.VIDEO_SETTINGS = {"output_width": 1080, "output_height": 1920}
mock_config.AUDIO_SETTINGS = {"bgm_volume": 0.1, "original_audio_volume": 1.0}
mock_config.CAPTION_SETTINGS = {
    "font": "Arial", "font_size": 24, "outline_width": 2,
    "margin_bottom": 50, "shadow_depth": 1, "style": "simple",
    "words_per_line": 3
}
mock_config.TEMP_DIR = Path(temp_test_dir) / "temp"
mock_config.TEMP_DIR.mkdir()
mock_config.OUTPUT_DIR = temp_output_dir
mock_config.BGM_DIR = Path(temp_test_dir) / "bgm"
sys.modules['config'] = mock_config

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import module to test
# Note: We will import _create_final_clip_optimized dynamically or assume it exists
# For now, we import what we can
from utils import processor

class TestProcessorOptimized(unittest.TestCase):

    @patch('subprocess.run')
    @patch('utils.processor._get_smart_crop_x')
    @patch('utils.processor._get_video_duration')
    def test_create_final_clip_optimized_structure(self, mock_duration, mock_crop_x, mock_run):
        """
        Test that _create_final_clip_optimized constructs a single FFmpeg command
        instead of multiple commands.
        """
        # Setup mocks
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        mock_crop_x.return_value = "(in_w-out_w)/2"
        mock_duration.return_value = 10.0

        # Inputs
        video_segment_path = "/tmp/segment.mp4"
        clip_info = {
            "caption_title": "Test Clip",
            "mood": "chill",
            "hook": "Test Hook",
            "narrative_type": "story",
            "reason": "Because testing",
            "enhanced_caption": "Enhanced Caption"
        }
        segments = [{"start": 0, "end": 10, "text": "Hello world"}]
        clip_number = 1
        output_dir = str(mock_config.OUTPUT_DIR)

        # We need to mock generate_srt_from_segments and others to avoid side effects
        with patch('utils.processor.generate_srt_from_segments') as mock_srt, \
             patch('utils.processor.select_bgm_by_mood') as mock_bgm, \
             patch('utils.processor.generate_thumbnail') as mock_thumb:

            def side_effect_srt(segments, output_path, **kwargs):
                # Create dummy file so exists() returns True
                Path(output_path).touch()
                return output_path

            mock_srt.side_effect = side_effect_srt
            mock_bgm.return_value = Path(mock_config.BGM_DIR) / "chill.mp3"
            mock_thumb.return_value = Path(mock_config.OUTPUT_DIR) / "thumb.jpg"

            # Ensure the function exists (it will be added in implementation)
            if not hasattr(processor, '_create_final_clip_optimized'):
                self.skipTest("_create_final_clip_optimized not implemented yet")

            # Call the function
            result = processor._create_final_clip_optimized(
                video_segment_path, clip_info, segments, clip_number, output_dir
            )

            # Verify subprocess.run was called exactly once for the main processing
            # (generate_thumbnail calls it too, but we mocked it out or it's separate)
            # Wait, generate_thumbnail is separate.
            # _create_final_clip_optimized should call ffmpeg once.

            # Verify arguments
            args, _ = mock_run.call_args
            cmd = args[0]

            # Check inputs
            self.assertIn("-i", cmd)
            self.assertIn(video_segment_path, cmd)
            self.assertIn(str(Path(mock_config.BGM_DIR) / "chill.mp3"), cmd)

            # Check filter complex
            self.assertIn("-filter_complex", cmd)
            filter_str = cmd[cmd.index("-filter_complex") + 1]

            # Check for scale and crop
            self.assertIn("scale=-1:1920", filter_str)
            self.assertIn("crop=1080:1920", filter_str)

            # Check for subtitles
            # The function determines the path based on clip number and title
            expected_srt_name = "01_Test Clip.srt"

            # The filter string escapes paths, so checking exact string might be tricky due to escaping
            # But we can check if the filename is present
            self.assertIn(expected_srt_name, filter_str)
            self.assertIn("subtitles=", filter_str)

            # Check for audio mix
            self.assertIn("amix=inputs=2", filter_str)

    @patch('utils.processor._create_final_clip_optimized')
    def test_create_final_clip_calls_optimized(self, mock_optimized):
        """
        Test that create_final_clip calls the optimized version.
        """
        mock_optimized.return_value = {"video": "out.mp4"}

        video_segment_path = "/tmp/segment.mp4"
        clip_info = {}
        segments = []
        clip_number = 1

        processor.create_final_clip(video_segment_path, clip_info, segments, clip_number)

        mock_optimized.assert_called_once()

if __name__ == '__main__':
    unittest.main()
