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

    @patch('utils.downloader.yt_dlp.YoutubeDL')
    def test_get_video_info_success(self, mock_ydl_class):
        # Mock successful yt-dlp execution
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Test Video",
            "duration": 120,
            "uploader": "Test Channel",
            "description": "A test video description",
            "thumbnail": "https://example.com/thumb.jpg"
        }
        mock_ydl.extract_info.return_value = mock_info

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        info = get_video_info(url)

        self.assertEqual(info["title"], "Test Video")
        self.assertEqual(info["duration"], 120)
        self.assertEqual(info["uploader"], "Test Channel")
        self.assertEqual(info["description"], "A test video description")
        self.assertEqual(info["thumbnail"], "https://example.com/thumb.jpg")

        # Verify extract_info called
        mock_ydl.extract_info.assert_called_once_with(url, download=False)

if __name__ == '__main__':
    unittest.main()
