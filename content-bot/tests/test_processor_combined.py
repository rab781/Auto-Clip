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

# Import processor module (after mocking dependencies)
from utils import processor

class TestProcessorOptimization(unittest.TestCase):

    @patch('subprocess.run')
    def test_convert_to_vertical_with_subtitles(self, mock_run):
        """
        Test that convert_to_vertical with subtitle_path generates a single ffmpeg command
        combining scale/crop and subtitles filters.
        """
        # Configure mock to return 0 returncode
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        video_path = "input.mp4"
        output_path = "output_vertical.mp4"
        subtitle_path = "captions.srt"

        # Check if function accepts subtitle_path argument (it won't yet, so we use kwargs or expect TypeError if not updated)
        try:
            processor.convert_to_vertical(video_path, output_path, subtitle_path=subtitle_path)
        except TypeError:
            self.fail("convert_to_vertical does not accept 'subtitle_path' argument yet")

        # Check the arguments passed to ffmpeg
        args, _ = mock_run.call_args
        cmd = args[0]

        # Verify it's an ffmpeg command
        self.assertEqual(cmd[0], "ffmpeg")

        # Find the filter argument (-vf)
        filter_arg = None
        for i, arg in enumerate(cmd):
            if arg == '-vf':
                filter_arg = cmd[i+1]
                break

        self.assertIsNotNone(filter_arg, "Should have -vf argument")

        # Verify filter combination
        # Should contain scale, crop, and subtitles
        self.assertIn("scale=", filter_arg)
        self.assertIn("crop=", filter_arg)
        self.assertIn(f"subtitles='{subtitle_path}'", filter_arg)

        print(f"\n[DEBUG] Combined Filter: {filter_arg}")

if __name__ == '__main__':
    unittest.main()
