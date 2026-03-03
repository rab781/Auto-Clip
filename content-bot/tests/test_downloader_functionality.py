import unittest
from unittest.mock import MagicMock, patch
import sys
import json
from pathlib import Path

# Mock dependencies before import
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.downloader import get_video_info

class TestDownloaderFunctionality(unittest.TestCase):

    @patch('utils.downloader.subprocess.run')
    def test_get_video_info_success(self, mock_run):
        # Mock successful yt-dlp execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "title": "Test Video",
            "duration": 120,
            "uploader": "Test Channel",
            "description": "A test video description",
            "thumbnail": "https://example.com/thumb.jpg"
        })
        mock_run.return_value = mock_result

        # We need a valid URL to pass validation, but yt-dlp won't be called for real
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        info = get_video_info(url)

        self.assertEqual(info["title"], "Test Video")
        self.assertEqual(info["duration"], 120)
        self.assertEqual(info["uploader"], "Test Channel")
        self.assertEqual(info["description"], "A test video description")
        self.assertEqual(info["thumbnail"], "https://example.com/thumb.jpg")

        # Verify subprocess was called correctly
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        # args[0] is the command list passed to subprocess.run
        # We check if 'yt_dlp' is somewhere in the command
        self.assertTrue(any("yt_dlp" in str(arg) for arg in args[0]))
        # We check if the URL is passed correctly as the last argument
        self.assertEqual(args[0][-1], url)

if __name__ == '__main__':
    unittest.main()
