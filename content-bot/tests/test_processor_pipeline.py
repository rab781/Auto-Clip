
import sys
import unittest
import shutil
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import os

# Mock modules that might be missing or require network
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Mock config to avoid import errors
sys.modules['config'] = MagicMock()
config_mock = sys.modules['config']
config_mock.VIDEO_SETTINGS = {"output_width": 1080, "output_height": 1920}
config_mock.AUDIO_SETTINGS = {"bgm_volume": 0.1, "original_audio_volume": 1.0}
config_mock.CAPTION_SETTINGS = {
    "font": "Arial", "font_size": 24, "outline_width": 2,
    "style": "simple", "words_per_line": 3
}
config_mock.TEMP_DIR = "tests/temp_mock"
config_mock.OUTPUT_DIR = "tests/out_mock"
config_mock.BGM_DIR = "tests/bgm_mock"

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import processor after mocking
from utils import processor

class TestProcessorPipeline(unittest.TestCase):
    def setUp(self):
        # Create temp dirs
        os.makedirs("tests/temp_mock", exist_ok=True)
        os.makedirs("tests/out_mock", exist_ok=True)
        os.makedirs("tests/bgm_mock", exist_ok=True)

        # Create dummy files if needed
        with open("tests/bgm_mock/bgm.mp3", "w") as f:
            f.write("dummy audio")

        # Reset mocks
        self.mock_subprocess = patch('subprocess.run').start()
        # Mock successful return
        self.mock_subprocess.return_value.returncode = 0
        self.mock_subprocess.return_value.stdout = "100.0"
        self.mock_subprocess.return_value.stderr = ""

        # Mock FaceTracker
        self.mock_tracker_cls = patch('utils.processor.FaceTracker').start()
        self.mock_tracker = self.mock_tracker_cls.return_value
        self.mock_tracker.get_average_face_position.return_value = 0.5

        # Mock other helpers
        self.mock_generate_srt = patch('utils.processor.generate_srt_from_segments').start()
        self.mock_generate_ass = patch('utils.processor.generate_animated_ass').start()

        # We need select_bgm_by_mood to return a path that exists or is handled
        self.mock_select_bgm = patch('utils.processor.select_bgm_by_mood').start()
        self.mock_select_bgm.return_value = "tests/bgm_mock/bgm.mp3"

        # Mock get_video_duration to avoid ffmpeg call in python
        self.mock_get_duration = patch('utils.processor._get_video_duration').start()
        self.mock_get_duration.return_value = 30.0

        # Mock generate_srt to create dummy file so existence checks pass
        def create_dummy_srt(segs, path, **kwargs):
            with open(path, "w") as f:
                f.write("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
            return str(path)
        self.mock_generate_srt.side_effect = create_dummy_srt

    def tearDown(self):
        patch.stopall()
        # Clean up
        if os.path.exists("tests/temp_mock"):
            shutil.rmtree("tests/temp_mock")
        if os.path.exists("tests/out_mock"):
            shutil.rmtree("tests/out_mock")
        if os.path.exists("tests/bgm_mock"):
            shutil.rmtree("tests/bgm_mock")

    def test_create_final_clip_optimized(self):
        """
        Test that create_final_clip calls ffmpeg with expected optimized filters.
        """
        clip_info = {
            "caption_title": "Test Clip",
            "mood": "energetic",
            "narrative_type": "story",
            "hook": "Hook",
            "reason": "Reason"
        }
        segments = [{"start": 0, "end": 10, "text": "Hello world"}]

        processor.create_final_clip(
            video_segment_path="input.mp4",
            clip_info=clip_info,
            segments=segments,
            clip_number=1,
            output_dir="tests/out_mock"
        )

        ffmpeg_calls = []
        for call_args in self.mock_subprocess.call_args_list:
            args = call_args[0][0] # The list of args
            if args[0] == 'ffmpeg':
                ffmpeg_calls.append(args)

        # Assertion for optimized state:
        # 1. _create_final_clip_optimized (single pass)
        # 2. generate_thumbnail
        self.assertEqual(len(ffmpeg_calls), 2)

        optimized_cmd = ffmpeg_calls[0]
        self.assertIn("-filter_complex", optimized_cmd)

    def test_create_final_clip_fallback(self):
        """
        Test that create_final_clip falls back to sequential processing if optimized pass fails.
        """
        clip_info = {
            "caption_title": "Test Clip Fallback",
            "mood": "energetic"
        }
        segments = [{"start": 0, "end": 10, "text": "Hello world"}]

        # Use side_effect to simulate failure ONLY on optimized pass
        def side_effect(cmd, **kwargs):
            # cmd is the list of arguments
            if '-filter_complex' in cmd:
                idx = cmd.index('-filter_complex') + 1
                filter_str = cmd[idx]

                # Optimized pass has crop AND subtitles (if subtitle exists)
                # Or just check for 'crop=' which is in convert_to_vertical too?
                # convert_to_vertical uses -vf, not -filter_complex (in my refactor, convert_to_vertical uses -vf)
                # Ah, convert_to_vertical uses: "-vf", filter_complex
                # So '-filter_complex' flag is ONLY used in optimized pass and add_background_music.

                if 'crop=' in filter_str:
                     ret = MagicMock()
                     ret.returncode = 1
                     ret.stderr = "Optimized pass failed"
                     ret.stdout = ""
                     return ret

            # Success for others
            ret = MagicMock()
            ret.returncode = 0
            ret.stdout = "100.0"
            ret.stderr = ""
            return ret

        self.mock_subprocess.side_effect = side_effect

        processor.create_final_clip(
            video_segment_path="input.mp4",
            clip_info=clip_info,
            segments=segments,
            clip_number=2,
            output_dir="tests/out_mock"
        )

        ffmpeg_calls = []
        for call_args in self.mock_subprocess.call_args_list:
            args = call_args[0][0]
            if args[0] == 'ffmpeg':
                ffmpeg_calls.append(args)

        print(f"Fallback test calls: {len(ffmpeg_calls)}")
        for i, cmd in enumerate(ffmpeg_calls):
            # Identifying the calls
            type_call = "Unknown"
            if '-filter_complex' in cmd and 'crop=' in cmd[cmd.index('-filter_complex')+1]:
                type_call = "Optimized (Expected Fail)"
            elif '-vf' in cmd and 'crop=' in cmd[cmd.index('-vf')+1]:
                type_call = "convert_to_vertical"
            elif '-vf' in cmd and 'subtitles=' in cmd[cmd.index('-vf')+1]:
                type_call = "burn_captions"
            elif '-filter_complex' in cmd and 'amix=' in cmd[cmd.index('-filter_complex')+1]:
                type_call = "add_background_music"
            elif '-vframes' in cmd:
                type_call = "generate_thumbnail"

            print(f"Call {i}: {type_call} - {' '.join(cmd[:5])}...")

        # We expect:
        # 1. Optimized pass (fails)
        # 2. convert_to_vertical
        # 3. burn_captions
        # 4. add_background_music
        # 5. generate_thumbnail
        # Total: 5 calls
        self.assertEqual(len(ffmpeg_calls), 5)

if __name__ == '__main__':
    unittest.main()
