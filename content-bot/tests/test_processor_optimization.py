import unittest
from unittest.mock import patch, MagicMock
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
from utils.processor import create_final_clip

class TestProcessorOptimization(unittest.TestCase):

    def setUp(self):
        self.clip_info = {
            "caption_title": "Test Clip",
            "mood": "energetic",
            "narrative_type": "story",
            "hook": "Test Hook",
            "reason": "Test Reason",
            "enhanced_caption": "Test Enhanced Caption"
        }
        self.segments = [
            {"text": "Hello world", "start": 0.0, "end": 1.0},
            {"text": "This is a test", "start": 1.0, "end": 2.0}
        ]
        self.video_segment_path = "tests/temp_mock/segment.mp4"
        self.output_dir = "tests/temp_mock/output"

        # Mock FaceTracker
        self.face_tracker_patch = patch('utils.processor.FaceTracker')
        self.mock_face_tracker = self.face_tracker_patch.start()
        self.mock_tracker_instance = MagicMock()
        self.mock_face_tracker.return_value = self.mock_tracker_instance
        self.mock_tracker_instance.get_average_face_position.return_value = 0.5 # Center

        # Mock _get_video_duration
        self.duration_patch = patch('utils.processor._get_video_duration')
        self.mock_duration = self.duration_patch.start()
        self.mock_duration.return_value = 30.0

        # Mock generate_srt_from_segments (returns a dummy path)
        self.srt_patch = patch('utils.processor.generate_srt_from_segments')
        self.mock_srt = self.srt_patch.start()
        self.mock_srt.return_value = "tests/temp_mock/temp.srt"

        # Mock generate_animated_ass
        self.ass_patch = patch('utils.processor.generate_animated_ass')
        self.mock_ass = self.ass_patch.start()
        # Side effect to create dummy file so .exists() returns True
        def create_dummy_ass(segments, output_path, settings):
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        self.mock_ass.side_effect = create_dummy_ass

        # Mock generate_thumbnail
        self.thumb_patch = patch('utils.processor.generate_thumbnail')
        self.mock_thumb = self.thumb_patch.start()
        self.mock_thumb.return_value = "tests/temp_mock/output/thumb.jpg"

        # Mock select_bgm_by_mood
        self.bgm_patch = patch('utils.processor.select_bgm_by_mood')
        self.mock_bgm = self.bgm_patch.start()
        self.mock_bgm.return_value = "tests/temp_mock/bgm.mp3"

    def tearDown(self):
        self.face_tracker_patch.stop()
        self.duration_patch.stop()
        self.srt_patch.stop()
        self.thumb_patch.stop()
        self.bgm_patch.stop()
        self.ass_patch.stop()

    @patch('subprocess.run')
    def test_create_final_clip_optimized_calls(self, mock_run):
        """
        Test that create_final_clip now uses the optimized single-pass pipeline.
        Expected ffmpeg calls: 1 (video processing) + 0 (thumbnail mocked) = 1.
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Ensure output directory exists (mocked or create dummy)
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', new_callable=MagicMock) as mock_open:

            result = create_final_clip(
                self.video_segment_path,
                self.clip_info,
                self.segments,
                1,
                self.output_dir
            )

        # Count ffmpeg calls
        ffmpeg_calls = 0
        ffmpeg_cmds = []
        for call in mock_run.call_args_list:
            args = call[0][0]
            if args[0] == 'ffmpeg':
                ffmpeg_calls += 1
                ffmpeg_cmds.append(args)

        print(f"FFmpeg calls: {ffmpeg_calls}")

        # Expect exactly 1 call for the optimized pipeline
        self.assertEqual(ffmpeg_calls, 1, f"Should have exactly 1 ffmpeg call, got {ffmpeg_calls}")

        # Verify the command contains filter_complex with scaling, cropping, subtitles, and mixing
        cmd = ffmpeg_cmds[0]
        cmd_str = " ".join(cmd)
        print(f"FFmpeg command: {cmd_str}")

        self.assertIn("scale=-1", cmd_str)
        self.assertIn("crop=", cmd_str)
        self.assertIn("subtitles=", cmd_str)
        self.assertIn("amix=", cmd_str)

    @patch('subprocess.run')
    def test_create_final_clip_optimized_no_bgm(self, mock_run):
        """
        Test optimization when no BGM is provided.
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Override bgm selection to return None
        self.mock_bgm.return_value = None

        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', new_callable=MagicMock) as mock_open:

            result = create_final_clip(
                self.video_segment_path,
                self.clip_info,
                self.segments,
                2, # Clip #2
                self.output_dir
            )

        ffmpeg_calls = 0
        ffmpeg_cmd = ""
        for call in mock_run.call_args_list:
            args = call[0][0]
            if args[0] == 'ffmpeg':
                ffmpeg_calls += 1
                ffmpeg_cmd = " ".join(args)

        self.assertEqual(ffmpeg_calls, 1)
        self.assertIn("scale=-1", ffmpeg_cmd)
        self.assertNotIn("amix=", ffmpeg_cmd) # No audio mixing
        self.assertIn("-map 0:a", ffmpeg_cmd) # Direct map of original audio

if __name__ == '__main__':
    unittest.main()
