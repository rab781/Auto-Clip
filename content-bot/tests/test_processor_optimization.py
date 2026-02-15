import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Mock dependencies BEFORE importing processor
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Now import the module to test
sys.path.append(str(Path(__file__).parent.parent))

# Import module directly to patch objects on it
from utils import processor

class TestProcessorOptimization(unittest.TestCase):

    @patch('subprocess.run')
    @patch('utils.processor._get_video_duration')
    def test_optimized_pipeline_construction(self, mock_duration, mock_run):
        """
        Verify that _create_final_clip_optimized constructs a single FFmpeg command
        with the correct filter chain.
        """
        mock_duration.return_value = 10.0
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        video_path = "segment.mp4"
        subtitle_path = Path("subs.srt")
        bgm_path = "bgm.mp3"
        final_path = Path("output.mp4")
        clip_info = {}

        processor._create_final_clip_optimized(
            video_path,
            clip_info,
            subtitle_path,
            bgm_path,
            final_path
        )

        args, _ = mock_run.call_args
        cmd = args[0]

        # Verify basic structure
        self.assertEqual(cmd[0], "ffmpeg")

        # Verify inputs
        self.assertIn("-i", cmd)
        input_indices = [i for i, x in enumerate(cmd) if x == "-i"]
        self.assertEqual(len(input_indices), 2) # Video and BGM
        self.assertEqual(cmd[input_indices[0]+1], str(video_path))
        self.assertEqual(cmd[input_indices[1]+1], str(bgm_path))

        # Verify filter complex
        self.assertIn("-filter_complex", cmd)
        idx = cmd.index("-filter_complex")
        filter_str = cmd[idx+1]

        print(f"Filter string: {filter_str}")

        # Check for crop, subtitles, and audio mix
        self.assertIn("crop=", filter_str)
        self.assertIn("subtitles=", filter_str)
        self.assertIn("amix=", filter_str)

        # Check mapping
        self.assertIn("-map", cmd)
        self.assertIn("[vout]", cmd)
        self.assertIn("[aout]", cmd)

    def test_create_final_clip_calls_optimized(self):
        """
        Verify that create_final_clip calls the optimized pipeline first.
        """
        with patch.object(processor, '_create_final_clip_optimized') as mock_opt, \
             patch.object(processor, '_create_final_clip_sequential') as mock_seq, \
             patch.object(processor, 'generate_srt_from_segments') as mock_srt, \
             patch.object(processor, 'select_bgm_by_mood') as mock_bgm, \
             patch.object(processor, 'generate_thumbnail') as mock_thumb, \
             patch.object(processor, 'generate_animated_ass') as mock_ass, \
             patch('builtins.open', new_callable=mock_open) as mock_file:

            mock_bgm.return_value = "bgm.mp3"

            processor.create_final_clip(
                "segment.mp4",
                {"mood": "happy"},
                [{"start": 0, "end": 1, "text": "hi"}],
                1,
                "output_dir"
            )

            mock_opt.assert_called_once()
            mock_seq.assert_not_called()

    def test_create_final_clip_fallback(self):
        """
        Verify that create_final_clip falls back to sequential if optimized fails.
        """
        with patch.object(processor, '_create_final_clip_optimized') as mock_opt, \
             patch.object(processor, '_create_final_clip_sequential') as mock_seq, \
             patch.object(processor, 'generate_srt_from_segments') as mock_srt, \
             patch.object(processor, 'select_bgm_by_mood') as mock_bgm, \
             patch.object(processor, 'generate_thumbnail') as mock_thumb, \
             patch.object(processor, 'generate_animated_ass') as mock_ass, \
             patch('builtins.open', new_callable=mock_open) as mock_file:

            mock_bgm.return_value = "bgm.mp3"
            mock_opt.side_effect = Exception("FFmpeg failed")

            processor.create_final_clip(
                "segment.mp4",
                {"mood": "happy"},
                [{"start": 0, "end": 1, "text": "hi"}],
                1,
                "output_dir"
            )

            mock_opt.assert_called_once()
            mock_seq.assert_called_once()

if __name__ == '__main__':
    unittest.main()
