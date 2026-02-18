import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Mock missing dependencies
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()  # Fix: mock submodule as well
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
        """
        Test that burn_captions correctly escapes single quotes in the srt path
        when constructing the ffmpeg filter string.
        """
        # Configure mock to return 0 returncode
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Simulate a path with single quote
        video_path = "input.mp4"
        srt_path = "path/with'quote/test.srt"
        output_path = "output.mp4"

        # Call the function
        burn_captions(video_path, srt_path, output_path)

        # Check the arguments passed to ffmpeg
        args, _ = mock_run.call_args
        cmd = args[0]

        # Find the filter argument (-vf)
        filter_arg = None
        for i, arg in enumerate(cmd):
            if arg == '-vf':
                filter_arg = cmd[i+1]
                break

        self.assertIsNotNone(filter_arg, "Should have found -vf argument")

        # Check if filter argument is present
        print(f"\n[DEBUG] Filter Arg: {filter_arg}")

        # We expect the single quote to be escaped as '\''
        # This means the string should contain the literal characters: ' \ ' ' (without spaces)
        if r"'\''" not in filter_arg:
            self.fail(f"Single quote was not escaped correctly in ffmpeg filter string: {filter_arg}")

if __name__ == '__main__':
    unittest.main()
