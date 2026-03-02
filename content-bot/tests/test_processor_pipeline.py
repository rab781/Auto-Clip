import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import shutil

# Ensure we can import from content-bot
sys.path.append(str(Path(__file__).parent.parent))

# Mock global dependencies that might not be available in test environment
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

from utils.processor import create_final_clip, _create_final_clip_optimized
from config import CAPTION_SETTINGS

class TestProcessorPipeline(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path("tests/temp_pipeline_out")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("tests/temp_pipeline_temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Original configs
        self.original_style = CAPTION_SETTINGS.get("style")

    def tearDown(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

        if self.original_style is not None:
            CAPTION_SETTINGS["style"] = self.original_style

    @patch('utils.processor._get_video_duration')
    @patch('utils.processor.select_bgm_by_mood')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.convert_to_vertical')
    @patch('subprocess.run')
    def test_optimized_pipeline_success(self, mock_run, mock_convert, mock_thumb, mock_srt, mock_ass, mock_bgm, mock_duration):
        """Test the optimized single-pass pipeline execution."""

        # Mocks setup
        mock_duration.return_value = 10.0
        mock_bgm.return_value = "dummy_bgm.mp3"

        # Return success for all subprocess calls
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        clip_info = {
            "caption_title": "test_clip",
            "mood": "energetic"
        }
        segments = [{"start": 0, "end": 10, "text": "test"}]

        # We need a dummy ASS file to exist for the test (the code checks if it exists)
        def mock_generate_ass(*args, **kwargs):
            Path(args[1]).touch()
        mock_ass.side_effect = mock_generate_ass

        CAPTION_SETTINGS["style"] = "animated"

        result = create_final_clip("dummy_video.mp4", clip_info, segments, 1, str(self.output_dir))

        # Verify optimized pipeline was called
        # The optimized pass should have specific arguments
        optimized_called = False
        for call in mock_run.call_args_list:
            args = call[0][0]
            if "-filter_complex" in args:
                idx = args.index("-filter_complex")
                if "scale" in args[idx+1] and "amix" in args[idx+1]:
                    optimized_called = True
                    break

        self.assertTrue(optimized_called, "Optimized single-pass FFmpeg command was not called.")

        # We shouldn't call convert_to_vertical, burn_captions, or add_background_music directly
        self.assertFalse(mock_convert.called, "convert_to_vertical should not be called in optimized pipeline")

    @patch('utils.processor._get_video_duration')
    @patch('utils.processor.select_bgm_by_mood')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('subprocess.run')
    def test_optimized_pipeline_fallback(self, mock_run, mock_add_bgm, mock_burn, mock_convert, mock_thumb, mock_ass, mock_bgm, mock_duration):
        """Test fallback to sequential pipeline if optimized pass fails."""

        mock_duration.return_value = 10.0
        mock_bgm.return_value = "dummy_bgm.mp3"

        mock_convert.return_value = "vertical.mp4"
        mock_burn.return_value = "captioned.mp4"
        mock_add_bgm.return_value = "final.mp4"

        # Fail the optimized subprocess, succeed for thumbnail
        def side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if "-filter_complex" in args[0] and "amix" in "".join(args[0]):
                mock_result.returncode = 1 # Fail
            else:
                mock_result.returncode = 0 # Success for thumbnail and other simple calls
            return mock_result

        mock_run.side_effect = side_effect

        clip_info = {
            "caption_title": "fallback_clip",
        }
        segments = [{"start": 0, "end": 10, "text": "test"}]

        def mock_generate_ass(*args, **kwargs):
            Path(args[1]).touch()
        mock_ass.side_effect = mock_generate_ass
        CAPTION_SETTINGS["style"] = "animated"

        result = create_final_clip("dummy_video.mp4", clip_info, segments, 2, str(self.output_dir))

        # Verify fallback was triggered
        self.assertTrue(mock_convert.called, "Fallback convert_to_vertical was not called")
        self.assertTrue(mock_burn.called, "Fallback burn_captions was not called")
        self.assertTrue(mock_add_bgm.called, "Fallback add_background_music was not called")

if __name__ == '__main__':
    unittest.main()
