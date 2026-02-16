import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock missing dependencies
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Import the module to test
from utils.processor import create_final_clip, VIDEO_SETTINGS, AUDIO_SETTINGS, CAPTION_SETTINGS

class TestProcessorOptimization(unittest.TestCase):

    @patch('utils.processor.subprocess.run')
    @patch('utils.processor.FaceTracker')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.select_bgm_by_mood')
    def test_create_final_clip_optimized(self, mock_bgm, mock_thumb, mock_ass, mock_srt, mock_tracker, mock_run):
        """
        Test that create_final_clip constructs a single FFmpeg command for the main processing steps.
        """
        # Configure mocks
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Mock FaceTracker
        mock_tracker_instance = mock_tracker.return_value
        mock_tracker_instance.get_average_face_position.return_value = 0.5

        # Mock generate_srt to return a dummy path
        mock_srt.return_value = "temp/subtitle.srt"
        mock_ass.return_value = "temp/subtitle.ass"

        # Mock generate_thumbnail to return a dummy path
        mock_thumb.return_value = "output/thumb.jpg"

        # Mock BGM selection to return None (no music)
        mock_bgm.return_value = None

        # Input data
        video_segment_path = "temp/segment.mp4"
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
        output_dir = "output"

        # Mock Path.exists to return True so optimized path is taken
        with patch('pathlib.Path.exists', return_value=True):
            # Call the function
            with patch('utils.processor._get_video_duration', return_value=10.0):
                result = create_final_clip(
                    video_segment_path,
                    clip_info,
                    segments,
                    clip_number,
                    output_dir
                )

        self.assertTrue(mock_run.called)
        # Verify we only called ffmpeg once (optimized) instead of multiple times
        # Note: generate_thumbnail is mocked to NOT call run, so valid call count is 1.
        self.assertEqual(mock_run.call_count, 1, "Optimized path should call ffmpeg exactly once")

        call_args = mock_run.call_args[0][0]

        # Verify it's an ffmpeg command
        self.assertEqual(call_args[0], "ffmpeg")

        # Verify filter complex is present
        self.assertIn("-filter_complex", call_args)

        # Verify specific filters are in the complex filter string
        filter_str = call_args[call_args.index("-filter_complex") + 1]

        # Check for crop (scale+crop)
        self.assertIn("crop=", filter_str)

        # Check for subtitles
        self.assertIn("subtitles=", filter_str)

    @patch('utils.processor.subprocess.run')
    @patch('utils.processor.FaceTracker')
    @patch('utils.processor.generate_srt_from_segments')
    @patch('utils.processor.generate_animated_ass')
    @patch('utils.processor.generate_thumbnail')
    @patch('utils.processor.select_bgm_by_mood')
    def test_create_final_clip_optimized_with_bgm(self, mock_bgm, mock_thumb, mock_ass, mock_srt, mock_tracker, mock_run):
        # Configure mocks
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        mock_tracker_instance = mock_tracker.return_value
        mock_tracker_instance.get_average_face_position.return_value = 0.5

        mock_srt.return_value = "temp/subtitle.srt"
        mock_ass.return_value = "temp/subtitle.ass"
        mock_thumb.return_value = "output/thumb.jpg"
        mock_bgm.return_value = "assets/bgm/music.mp3"

        with patch('pathlib.Path.exists', return_value=True):
            with patch('utils.processor._get_video_duration', return_value=10.0):
                 create_final_clip(
                    "temp/segment.mp4",
                    {"caption_title": "Test", "mood": "chill"},
                    [{"start": 0, "end": 10, "text": "Hello"}],
                    1,
                    "output"
                )

        # Verify arguments
        self.assertTrue(mock_run.called)
        self.assertEqual(mock_run.call_count, 1, "Optimized path should call ffmpeg exactly once")
        call_args = mock_run.call_args[0][0]
        filter_str = call_args[call_args.index("-filter_complex") + 1]

        # Check for audio mix
        self.assertIn("amix=", filter_str)
        self.assertIn("aloop=", filter_str)

if __name__ == '__main__':
    unittest.main()
