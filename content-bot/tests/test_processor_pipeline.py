import unittest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

# Mock missing dependencies
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the module to test
from utils import processor

class TestProcessorPipeline(unittest.TestCase):

    @patch('subprocess.run')
    def test_create_final_clip_optimized_structure(self, mock_run):
        """
        Verify that _create_final_clip_optimized constructs the correct single-pass command.
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Test parameters
        video_path = "input_segment.mp4"
        output_path = "output_final.mp4"
        crop_x = "(in_w-out_w)/2"
        subtitle_path = "subs.srt"
        bgm_path = "music.mp3"

        # Mock _get_video_duration to avoid another subprocess call
        with patch('utils.processor._get_video_duration', return_value=10.0):
            processor._create_final_clip_optimized(
                video_path, output_path, crop_x, subtitle_path, bgm_path
            )

        # Check the command
        args, _ = mock_run.call_args
        cmd = args[0]

        # Verify basic components
        self.assertIn("-filter_complex", cmd)
        self.assertIn("-map", cmd)

        # Find filter complex string
        filter_idx = cmd.index("-filter_complex")
        filter_str = cmd[filter_idx + 1]

        # Verify filter components
        # 1. Scaling and Cropping on [0:v]
        self.assertIn("scale=-1:1920", filter_str)
        self.assertIn("crop=1080:1920:(in_w-out_w)/2:0", filter_str)

        # 2. Subtitles
        self.assertIn("subtitles='subs.srt'", filter_str)

        # 3. Audio Mixing
        self.assertIn("amix=inputs=2", filter_str)

        # Verify inputs
        self.assertIn("input_segment.mp4", cmd)
        self.assertIn("music.mp3", cmd)

    @patch('subprocess.run')
    def test_create_final_clip_optimized_no_bgm(self, mock_run):
        """
        Verify optimized pipeline without BGM.
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        video_path = "input.mp4"
        output_path = "output.mp4"
        crop_x = "0"

        processor._create_final_clip_optimized(
            video_path, output_path, crop_x, subtitle_path="subs.srt", bgm_path=None
        )

        args, _ = mock_run.call_args
        cmd = args[0]

        filter_idx = cmd.index("-filter_complex")
        filter_str = cmd[filter_idx + 1]

        # Should NOT have audio mixing
        self.assertNotIn("amix", filter_str)

        # Should map original audio
        map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
        mapped_values = [cmd[i+1] for i in map_indices]
        self.assertIn("0:a", mapped_values)

    @patch('utils.processor._create_final_clip_optimized')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.generate_thumbnail')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('pathlib.Path.mkdir')
    def test_fallback_mechanism(self, mock_mkdir, mock_open, mock_thumb, mock_bgm, mock_burn, mock_vertical, mock_optimized):
        """
        Verify that create_final_clip falls back to sequential processing if optimized fails.
        """
        # Make optimized version fail
        mock_optimized.side_effect = Exception("FFmpeg failed")

        # Mock other helpers to succeed
        mock_vertical.return_value = "vertical.mp4"
        mock_burn.return_value = "captioned.mp4"
        mock_bgm.return_value = "final.mp4"
        mock_thumb.return_value = "thumb.jpg"

        # Setup inputs
        clip_info = {"caption_title": "Test", "mood": "chill"}
        segments = [{"text": "Hello", "start": 0, "end": 1}]

        # Mock side effects for file existence checks (Path.exists)
        # We need to mock Path objects created inside the function.
        # This is hard. Easier to rely on the fact that the fallback calls the individual functions.

        # Mock generate_srt/ass
        with patch('utils.processor.generate_srt_from_segments', return_value="subs.srt"), \
             patch('utils.processor.select_bgm_by_mood', return_value="music.mp3"), \
             patch('utils.processor._get_smart_crop_x', return_value="0"), \
             patch('pathlib.Path.exists', return_value=True):

            processor.create_final_clip(
                "input.mp4", clip_info, segments, 1, output_dir="out"
            )

        # Verify optimized was called
        mock_optimized.assert_called_once()

        # Verify fallback functions were called
        mock_vertical.assert_called_once()
        mock_burn.assert_called_once()
        mock_bgm.assert_called_once()

if __name__ == '__main__':
    unittest.main()
