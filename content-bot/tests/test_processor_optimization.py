
import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock missing dependencies BEFORE importing module
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Import module
from utils import processor

class TestProcessorOptimization(unittest.TestCase):

    def setUp(self):
        # Mock file operations to prevent actual IO
        self.mock_open = patch('builtins.open', mock_open()).start()

        # Patch config values
        self.patcher_config = patch.dict(processor.VIDEO_SETTINGS, {'output_width': 1080, 'output_height': 1920})
        self.patcher_config.start()

    def tearDown(self):
        patch.stopall()

    @patch('utils.processor._create_final_clip_optimized')
    @patch('utils.processor.subprocess.run')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('shutil.copy')
    def test_legacy_pipeline_fallback(self, mock_copy, mock_glob, mock_exists, mock_srt, mock_ass, mock_bgm, mock_burn, mock_vertical, mock_run, mock_optimized):
        """
        Verify that fallback to legacy pipeline happens when optimized function fails.
        """
        # Setup mocks
        mock_optimized.return_value = False # Simulate optimization failure

        mock_run.return_value.returncode = 0
        mock_exists.return_value = True
        mock_glob.return_value = [Path("bgm.mp3")]

        mock_vertical.return_value = "temp/vertical.mp4"
        mock_burn.return_value = "temp/captioned.mp4"
        mock_bgm.return_value = "output/final.mp4"

        clip_info = {"caption_title": "Test Clip", "mood": "energetic"}
        segments = [{"start": 0, "end": 5, "text": "Test"}]

        processor.create_final_clip(
            video_segment_path="input.mp4",
            clip_info=clip_info,
            segments=segments,
            clip_number=1,
            output_dir="output"
        )

        # Verify fallback calls were made
        mock_vertical.assert_called()
        mock_burn.assert_called()
        mock_bgm.assert_called()
        print("\n[TEST] Fallback verified: Legacy pipeline invoked after optimization failure.")

    @patch('utils.processor.subprocess.run')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_optimized_pipeline_success(self, mock_glob, mock_exists, mock_srt, mock_ass, mock_bgm, mock_burn, mock_vertical, mock_run):
        """
        Verify that optimized pipeline calls ffmpeg with correct complex filter
        and DOES NOT call legacy functions.
        """
        # Setup mocks
        mock_run.return_value.returncode = 0
        mock_exists.return_value = True
        mock_glob.return_value = [Path("bgm.mp3")]

        clip_info = {"caption_title": "Optimized Clip", "mood": "chill"}
        segments = [{"start": 0, "end": 5, "text": "Optimized"}]

        processor.create_final_clip(
            video_segment_path="input.mp4",
            clip_info=clip_info,
            segments=segments,
            clip_number=2,
            output_dir="output"
        )

        # Verify legacy functions NOT called
        mock_vertical.assert_not_called()
        mock_burn.assert_not_called()
        mock_bgm.assert_not_called()

        # Verify ffmpeg call arguments
        # We need to find the call that has filter_complex
        ffmpeg_calls = [call for call in mock_run.call_args_list if call[0][0][0] == 'ffmpeg']
        self.assertTrue(len(ffmpeg_calls) > 0)

        # The optimized call is likely the last one (or only one if thumbnail generation mocked out? No thumbnail generation is step 5)
        # _create_final_clip_optimized is called at step 3.
        # generate_thumbnail is called at step 5.

        # Let's inspect the call args
        optimized_call_found = False
        for call_args in ffmpeg_calls:
            cmd = call_args[0][0]
            if '-filter_complex' in cmd:
                optimized_call_found = True
                filter_complex_idx = cmd.index('-filter_complex') + 1
                filter_str = cmd[filter_complex_idx]

                print(f"\n[DEBUG] Filter String: {filter_str}")

                # Check for key components
                self.assertIn("crop=", filter_str)
                self.assertIn("subtitles=", filter_str)
                self.assertIn("amix=", filter_str)
                self.assertIn("aloop=", filter_str)
                break

        self.assertTrue(optimized_call_found, "Optimized FFmpeg command with filter_complex not found")
        print("\n[TEST] Optimized pipeline verified: Single FFmpeg pass used.")

if __name__ == '__main__':
    unittest.main()
