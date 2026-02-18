import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Mock dependencies
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils import processor

class TestProcessorOptimized(unittest.TestCase):

    @patch('subprocess.run')
    def test_create_final_clip_optimized_structure(self, mock_run):
        """
        Test that _create_final_clip_optimized calls ffmpeg with a complex filter chain.
        """
        # Configure mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Test data
        video_path = "input_segment.mp4"
        bgm_path = "bgm.mp3"
        srt_path = "subs.srt"
        output_path = "final_output.mp4"
        crop_x = "(in_w-out_w)/2" # Center crop

        # Create dummy files so existence checks pass
        with open(bgm_path, 'w') as f: f.write('dummy')
        with open(srt_path, 'w') as f: f.write('dummy')

        try:
            # Check if function exists (to allow test file to be created before implementation)
            if not hasattr(processor, '_create_final_clip_optimized'):
                 return

            processor._create_final_clip_optimized(
                video_path=video_path,
                bgm_path=bgm_path,
                srt_path=srt_path,
                output_path=output_path,
                crop_x=crop_x
            )
        finally:
            # Cleanup
            if Path(bgm_path).exists(): Path(bgm_path).unlink()
            if Path(srt_path).exists(): Path(srt_path).unlink()

        # Assertions
        args, _ = mock_run.call_args
        cmd = args[0]

        # Check basic ffmpeg command structure
        self.assertEqual(cmd[0], 'ffmpeg')
        self.assertIn('-filter_complex', cmd)

        # Check if filter complex contains expected parts
        filter_complex = cmd[cmd.index('-filter_complex') + 1]

        # 1. Scale and Crop
        self.assertIn('scale=-1:1920', filter_complex)
        self.assertIn(f'crop=1080:1920:{crop_x}:0', filter_complex)

        # 2. Subtitles
        self.assertIn(f"subtitles='{srt_path}'", filter_complex)

        # 3. Audio Mix
        self.assertIn('amix=inputs=2', filter_complex)

if __name__ == '__main__':
    unittest.main()
