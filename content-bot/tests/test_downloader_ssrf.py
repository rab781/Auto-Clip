import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Mock dependencies before import
from unittest.mock import MagicMock
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.downloader import _validate_youtube_url

class TestDownloaderSSRF(unittest.TestCase):

    @patch('socket.getaddrinfo')
    def test_ssrf_blocked_private_ip(self, mock_getaddrinfo):
        # Mock DNS resolution to a private IP
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('192.168.1.1', 80))
        ]

        with self.assertRaises(ValueError) as context:
            _validate_youtube_url("https://youtube.com/watch?v=123")

        self.assertIn("Domain resolves to internal IP", str(context.exception))

    @patch('socket.getaddrinfo')
    def test_ssrf_blocked_loopback_ip(self, mock_getaddrinfo):
        # Mock DNS resolution to loopback
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('127.0.0.1', 80))
        ]

        with self.assertRaises(ValueError) as context:
            _validate_youtube_url("https://youtube.com/watch?v=123")

        self.assertIn("Domain resolves to internal IP", str(context.exception))

    @patch('socket.getaddrinfo')
    def test_ssrf_allowed_public_ip(self, mock_getaddrinfo):
        # Mock DNS resolution to public IP
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('142.250.190.46', 80)) # Google IP
        ]

        # Should not raise exception
        try:
            _validate_youtube_url("https://youtube.com/watch?v=123")
        except Exception as e:
            self.fail(f"Unexpected exception for valid IP: {e}")

if __name__ == '__main__':
    unittest.main()
