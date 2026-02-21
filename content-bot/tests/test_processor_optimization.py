import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Mock dependencies
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['utils.face_tracker'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

from utils import processor

class TestProcessorOptimization(unittest.TestCase):
    def setUp(self):
        self.mock_subprocess = patch('subprocess.run').start()
        self.mock_subprocess.return_value.returncode = 0
        self.mock_subprocess.return_value.stdout = ""
        self.mock_subprocess.return_value.stderr = ""

        self.mock_path_exists = patch('pathlib.Path.exists').start()
        self.mock_path_exists.return_value = True

        # Patch built-in open to avoid file system errors
        self.mock_open = patch('builtins.open', MagicMock()).start()
        self.mock_mkdir = patch('pathlib.Path.mkdir').start()

    def tearDown(self):
        patch.stopall()

    @patch('utils.processor._create_final_clip_optimized')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.select_bgm_by_mood')
    def test_optimization_success(self, mock_select_bgm, mock_srt, mock_ass, mock_thumb, mock_bgm, mock_burn, mock_convert, mock_optimized):
        """Verify that optimized path is taken and sequential steps are skipped"""
        # Setup mocks
        mock_optimized.return_value = "final.mp4"
        mock_thumb.return_value = "thumb.jpg"
        mock_select_bgm.return_value = "bgm.mp3"

        clip_info = {"caption_title": "Test Clip", "mood": "energetic"}
        segments = [{"start": 0, "end": 1, "text": "hello"}]

        processor.create_final_clip(
            video_segment_path="input.mp4",
            clip_info=clip_info,
            segments=segments,
            clip_number=1,
            output_dir="output"
        )

        # Optimized function should be called
        mock_optimized.assert_called_once()

        # Sequential functions should NOT be called
        mock_convert.assert_not_called()
        mock_burn.assert_not_called()
        mock_bgm.assert_not_called()

        # Thumbnail generation should still happen
        mock_thumb.assert_called_once()

    @patch('utils.processor._create_final_clip_optimized')
    @patch('utils.processor.convert_to_vertical')
    @patch('utils.processor.burn_captions')
    @patch('utils.processor.add_background_music')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.select_bgm_by_mood')
    @patch('shutil.copy')
    def test_optimization_failure_fallback(self, mock_copy, mock_select_bgm, mock_srt, mock_ass, mock_thumb, mock_bgm, mock_burn, mock_convert, mock_optimized):
        """Verify fallback to sequential processing if optimized path fails"""
        # Setup mocks to fail optimization
        mock_optimized.side_effect = Exception("Optimization failed")

        # Setup sequential mocks
        mock_convert.return_value = "vertical.mp4"
        mock_burn.return_value = "captioned.mp4"
        mock_bgm.return_value = "final.mp4"
        mock_thumb.return_value = "thumb.jpg"
        mock_select_bgm.return_value = "bgm.mp3"

        clip_info = {"caption_title": "Test Clip", "mood": "energetic"}
        segments = [{"start": 0, "end": 1, "text": "hello"}]

        processor.create_final_clip(
            video_segment_path="input.mp4",
            clip_info=clip_info,
            segments=segments,
            clip_number=1,
            output_dir="output"
        )

        # Optimized function called and failed
        mock_optimized.assert_called_once()

        # Fallback sequential functions SHOULD be called
        mock_convert.assert_called_once()
        mock_burn.assert_called_once()
        mock_bgm.assert_called_once()

        # Thumbnail generation should still happen
        mock_thumb.assert_called_once()

    @patch('utils.processor.select_bgm_by_mood')
    def test_optimized_function_ffmpeg_calls(self, mock_select_bgm):
        """Verify _create_final_clip_optimized calls subprocess with correct filter chain"""
        mock_select_bgm.return_value = "bgm.mp3"

        # Mock FaceTracker to return None (Center Crop)
        with patch('utils.processor.FaceTracker') as MockTracker:
            instance = MockTracker.return_value
            instance.get_average_face_position.return_value = None

            # Call the optimized function directly
            processor._create_final_clip_optimized(
                video_path="input.mp4",
                output_path="output.mp4",
                subtitle_path="subs.srt",
                bgm_path="bgm.mp3"
            )

            # Check subprocess call
            # We expect one call to ffprobe (for duration) and one for ffmpeg
            # Since we mocked subprocess.run, let's inspect the calls

            # Filter for ffmpeg call (not ffprobe)
            ffmpeg_calls = [
                call for call in self.mock_subprocess.call_args_list
                if call[0][0][0] == 'ffmpeg'
            ]

            self.assertEqual(len(ffmpeg_calls), 1, "Should call ffmpeg exactly once")

            args = ffmpeg_calls[0][0][0]
            # Check for filter_complex
            self.assertIn('-filter_complex', args)

            # Verify filter chain components
            filter_str = args[args.index('-filter_complex') + 1]
            self.assertIn('crop=', filter_str)
            self.assertIn('subtitles=', filter_str)
            self.assertIn('amix=', filter_str)

if __name__ == '__main__':
    unittest.main()
