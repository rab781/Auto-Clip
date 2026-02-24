import unittest
from unittest.mock import patch, MagicMock, ANY
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

# Import module to test
from utils.processor import create_final_clip, _create_final_clip_optimized, VIDEO_SETTINGS, AUDIO_SETTINGS

class TestProcessorPipeline(unittest.TestCase):

    def tearDown(self):
        # Clean up any files created
        import shutil
        if Path("out").exists():
            shutil.rmtree("out")

    @patch('subprocess.run')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.select_bgm_by_mood')
    @patch('utils.processor._get_video_duration', return_value=10.0)
    @patch('builtins.open', new_callable=MagicMock)
    def test_optimized_pipeline_success(self, mock_open, mock_dur, mock_select_bgm, mock_bgm, mock_burn, mock_vert, mock_srt, mock_thumb, mock_run):
        """Test that create_final_clip uses the optimized pipeline when successful."""

        # Setup mocks
        mock_run.return_value.returncode = 0
        mock_thumb.return_value = "thumb.jpg"
        mock_select_bgm.return_value = "bgm.mp3"

        # Mock file existence for bgm and srt
        with patch('pathlib.Path.exists', return_value=True):
            # Input data
            video_segment_path = "segment.mp4"
            clip_info = {"caption_title": "Test Clip", "mood": "chill"}
            segments = [{"text": "Hello world", "start": 0, "end": 1}]
            clip_number = 1

            # Call function
            result = create_final_clip(video_segment_path, clip_info, segments, clip_number, output_dir="out")

            # Assertions
            self.assertEqual(result["video"], str(Path("out/01_Test Clip.mp4")))

            # Verify optimized function called (implied by subprocess call with complex filter)
            # Check subprocess arguments for the optimized command
            # The optimized command has ONE ffmpeg call for video processing
            # We expect generate_thumbnail to be called (separate ffmpeg call)
            # We expect generate_srt_from_segments to be called

            # Check that fallback functions were NOT called
            mock_vert.assert_not_called()
            mock_burn.assert_not_called()
            mock_bgm.assert_not_called()

            # Verify subprocess was called with expected optimized args
            # We need to find the call that has filter_complex with scale, crop, subtitles, and amix
            found_optimized_call = False
            for call in mock_run.call_args_list:
                args = call[0][0]
                if '-filter_complex' in args:
                    filter_complex = args[args.index('-filter_complex') + 1]
                    if 'scale=' in filter_complex and 'subtitles=' in filter_complex and 'amix=' in filter_complex:
                        found_optimized_call = True
                        break

            self.assertTrue(found_optimized_call, "Optimized FFmpeg command not found")

    @patch('subprocess.run')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.select_bgm_by_mood')
    @patch('shutil.copy')
    @patch('builtins.open', new_callable=MagicMock)
    def test_optimized_pipeline_fallback(self, mock_open, mock_copy, mock_select_bgm, mock_bgm, mock_burn, mock_vert, mock_srt, mock_thumb, mock_run):
        """Test that create_final_clip falls back to sequential pipeline when optimized fails."""

        # Setup mocks
        mock_select_bgm.return_value = "bgm.mp3"

        # Make the FIRST subprocess run fail (optimized pass)
        # We create a side effect that raises an exception if 'amix' is in the arguments (identifying the optimized call)
        # and returns success otherwise (for thumbnail, probe, etc if any)

        def side_effect(cmd, **kwargs):
            # Check for optimized command characteristics
            # Optimized command has crop AND subtitles (if segments provided) in one filter_complex
            if '-filter_complex' in cmd:
                filter_complex = cmd[cmd.index('-filter_complex') + 1]
                if 'crop=' in filter_complex and 'subtitles=' in filter_complex:
                    raise Exception("FFmpeg failed")

            mock_res = MagicMock()
            mock_res.returncode = 0
            return mock_res

        mock_run.side_effect = side_effect

        # Setup fallback mocks to return paths
        mock_vert.return_value = "vertical.mp4"
        mock_burn.return_value = "captioned.mp4"
        mock_bgm.return_value = "final.mp4"
        mock_thumb.return_value = "thumb.jpg"

        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            # Input data
            video_segment_path = "segment.mp4"
            clip_info = {"caption_title": "Test Clip", "mood": "chill"}
            segments = [{"text": "Hello world", "start": 0, "end": 1}]
            clip_number = 1

            # Call function
            create_final_clip(video_segment_path, clip_info, segments, clip_number, output_dir="out")

            # Assertions
            # Verify fallback functions WERE called
            mock_vert.assert_called_once()
            mock_burn.assert_called_once()
            mock_bgm.assert_called_once()

    @patch('subprocess.run')
    def test_create_final_clip_optimized_command_structure(self, mock_run):
        """Test the structure of the optimized ffmpeg command."""
        mock_run.return_value.returncode = 0

        # Mock dependencies
        with patch('utils.processor._get_video_duration', return_value=10.0), \
             patch('utils.processor._get_smart_crop_x', return_value="0"), \
             patch('pathlib.Path.exists', return_value=True):

            _create_final_clip_optimized(
                "input.mp4",
                "output.mp4",
                "subs.srt",
                "bgm.mp3",
                0.5
            )

            args = mock_run.call_args[0][0]

            # Check inputs
            self.assertIn("input.mp4", args)
            self.assertIn("bgm.mp3", args)

            # Check filter complex
            idx = args.index("-filter_complex")
            filter_str = args[idx+1]

            # Should contain scale and crop
            self.assertIn("scale=-1", filter_str)
            self.assertIn("crop=", filter_str)

            # Should contain subtitles
            self.assertIn("subtitles=", filter_str)

            # Should contain audio mixing
            self.assertIn("amix=", filter_str)

            # Should map video and audio
            self.assertIn("-map", args)

            # Should use libx264
            self.assertIn("libx264", args)

if __name__ == '__main__':
    unittest.main()
