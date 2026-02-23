import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Mock dependencies before import
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import locally to avoid top-level side effects
from utils.processor import create_final_clip, _get_video_duration

class TestProcessorPipeline(unittest.TestCase):

    def setUp(self):
        self.mock_subprocess = patch('utils.processor.subprocess.run').start()
        self.mock_face_tracker = patch('utils.processor.FaceTracker').start()
        self.mock_gen_ass = patch('utils.processor.generate_animated_ass').start()
        self.mock_gen_srt = patch('utils.processor.generate_srt_from_segments').start()
        self.mock_get_duration = patch('utils.processor._get_video_duration').start()
        self.mock_path_exists = patch('pathlib.Path.exists').start()

        # Configure defaults
        self.mock_get_duration.return_value = 10.0
        self.mock_path_exists.return_value = True

        # Configure subprocess mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        self.mock_subprocess.return_value = mock_result

        # Configure FaceTracker
        self.mock_face_tracker_instance = self.mock_face_tracker.return_value
        self.mock_face_tracker_instance.get_average_face_position.return_value = 0.5

    def tearDown(self):
        patch.stopall()

    def test_create_final_clip_calls_optimized(self):
        """
        Test that create_final_clip calls ffmpeg fewer times with optimization.
        """
        # Input data
        video_segment_path = "input.mp4"
        clip_info = {"caption_title": "Test", "mood": "happy"}
        segments = [{"start": 0, "end": 5, "text": "Hello world"}]
        clip_number = 1

        with patch('builtins.open', new_callable=MagicMock):
             # Call function
             create_final_clip(video_segment_path, clip_info, segments, clip_number)

        # Verify calls
        # We need to filter subprocess calls to count only 'ffmpeg' calls
        ffmpeg_calls = 0
        cmds = []
        for call in self.mock_subprocess.call_args_list:
            args = call[0][0]
            if args[0] == 'ffmpeg':
                ffmpeg_calls += 1
                cmds.append(args)

        print(f"\n[DEBUG] FFmpeg calls detected: {ffmpeg_calls}")
        for i, cmd in enumerate(cmds):
            print(f"Call {i+1}: {' '.join(cmd)}")

        # Optimized expectation:
        # 1. _create_final_clip_optimized (ffmpeg)
        # 2. generate_thumbnail (ffmpeg)
        # Total 2 calls.
        self.assertEqual(ffmpeg_calls, 2, "Expected exactly 2 ffmpeg calls (optimized + thumbnail)")

        # Verify the first call is the optimized one
        opt_cmd = " ".join(cmds[0])
        self.assertIn("scale=-1:1920", opt_cmd)
        self.assertIn("crop=1080:1920", opt_cmd)
        self.assertIn("subtitles=", opt_cmd)

    def test_create_final_clip_calls_optimized_with_bgm(self):
        """
        Test that create_final_clip calls ffmpeg correctly when BGM is present.
        """
        # Input data
        video_segment_path = "input.mp4"
        clip_info = {"caption_title": "Test", "mood": "happy"}
        segments = [{"start": 0, "end": 5, "text": "Hello world"}]
        clip_number = 1

        # Use patch('utils.processor.Path.glob') won't work easily because Path is instantiated.
        # We can patch select_bgm_by_mood instead.
        with patch('utils.processor.select_bgm_by_mood', return_value="bgm.mp3"):
             with patch('builtins.open', new_callable=MagicMock):
                 # Call function
                 create_final_clip(video_segment_path, clip_info, segments, clip_number)

        # Verify calls
        ffmpeg_calls = 0
        cmds = []
        for call in self.mock_subprocess.call_args_list:
            args = call[0][0]
            if args[0] == 'ffmpeg':
                ffmpeg_calls += 1
                cmds.append(args)

        self.assertEqual(ffmpeg_calls, 2, "Expected exactly 2 ffmpeg calls with BGM")
        opt_cmd = " ".join(cmds[0])
        self.assertIn("amix=", opt_cmd)
        self.assertIn("-i bgm.mp3", opt_cmd)

if __name__ == '__main__':
    unittest.main()
