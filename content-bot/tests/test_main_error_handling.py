
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# 1. Mock global dependencies via sys.modules
sys.modules['tqdm'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['moviepy'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()
sys.modules['scipy'] = MagicMock()
sys.modules['scipy.io'] = MagicMock()
sys.modules['scipy.io.wavfile'] = MagicMock()

# Mock traceback globally since it is imported inside the function
mock_traceback_module = MagicMock()
sys.modules['traceback'] = mock_traceback_module

# Mock config
mock_config = MagicMock()
mock_config.DOWNLOADS_DIR = 'mock_downloads'
mock_config.TEMP_DIR = 'mock_temp'
mock_config.OUTPUT_DIR = 'mock_output'
sys.modules['config'] = mock_config

# Mock utils package and its submodules
mock_utils = MagicMock()
sys.modules['utils'] = mock_utils

# 2. Add project root to sys.path so we can import main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 3. Import main (after mocking)
import main

class TestMainErrorHandling(unittest.TestCase):

    def setUp(self):
        # Reset mocks before each test
        mock_traceback_module.reset_mock()

    @patch('main.process_video')
    @patch('sys.exit')
    @patch('argparse.ArgumentParser.parse_args')
    def test_stack_trace_hidden_by_default(self, mock_parse_args, mock_exit, mock_process):
        """Verify stack trace is NOT shown by default when exception occurs."""
        # Setup: Simulate args without debug flag
        # We need to ensure 'debug' attribute exists, defaulting to False if not present in original code
        # But we will add it. For now, we simulate the 'before' state where 'debug' might not exist or be False.
        # If we pass an object that doesn't have debug, code will fail if we access args.debug.
        # But wait, the current code DOES NOT access args.debug.
        # So this test checks that traceback IS printed (current behavior).
        # Wait, I want to write a test that FAILS now and PASSES later.

        # Current code: always prints traceback.
        # New code: only prints if args.debug is True.

        # So, to test "hidden by default", I set debug=False (or don't set it).
        # The test should ASSERT NOT CALLED.
        # Currently, it WILL BE CALLED. So test fails. Good.

        mock_args = MagicMock()
        mock_args.url = "http://youtube.com/watch?v=123"
        mock_args.debug = False
        mock_args.dry_run = False
        mock_args.url_flag = None
        mock_parse_args.return_value = mock_args

        # Setup: process_video raises an exception
        mock_process.side_effect = Exception("Simulated Failure")

        # Execute
        main.main()

        # Verify
        mock_traceback_module.print_exc.assert_not_called()
        mock_exit.assert_called_with(1)

    @patch('main.process_video')
    @patch('sys.exit')
    @patch('argparse.ArgumentParser.parse_args')
    def test_stack_trace_shown_with_debug(self, mock_parse_args, mock_exit, mock_process):
        """Verify stack trace IS shown when --debug flag is present."""
        # Setup: Simulate args WITH debug flag
        mock_args = MagicMock()
        mock_args.url = "http://youtube.com/watch?v=123"
        mock_args.debug = True
        mock_args.dry_run = False
        mock_args.url_flag = None
        mock_parse_args.return_value = mock_args

        # Setup: process_video raises an exception
        mock_process.side_effect = Exception("Simulated Failure")

        # Execute
        main.main()

        # Verify
        mock_traceback_module.print_exc.assert_called_once()
        mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()
