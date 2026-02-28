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

# Now import the module to test
from utils.processor import burn_captions

class TestProcessorSecurity(unittest.TestCase):

    @patch('subprocess.run')
    def test_burn_captions_escaping(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        video_path = "input.mp4"
        srt_path = "path/with'quote/test.srt"
        output_path = "output.mp4"

        burn_captions(video_path, srt_path, output_path)

        args, _ = mock_run.call_args
        cmd = args[0]

        self.assertIn("file:input.mp4", cmd)
        self.assertIn("file:output.mp4", cmd)

        # Check original test behavior: ensure single quotes escaped
        filter_arg = None
        for i, arg in enumerate(cmd):
            if arg == '-vf':
                filter_arg = cmd[i+1]
                break

        self.assertIsNotNone(filter_arg, "Should have found -vf argument")
        if r"'\''" not in filter_arg:
            self.fail(f"Single quote was not escaped correctly in ffmpeg filter string: {filter_arg}")

if __name__ == '__main__':
    unittest.main()
