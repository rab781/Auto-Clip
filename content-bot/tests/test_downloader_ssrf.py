import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Mock dependencies before importing downloader
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Add project root to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.downloader import get_video_info

class TestDownloaderSSRF(unittest.TestCase):

    @patch('utils.downloader.socket.getaddrinfo')
    def test_ssrf_private_ip(self, mock_getaddrinfo):
        from utils.downloader import _check_domain_resolves_to_public_ip
        _check_domain_resolves_to_public_ip.cache_clear()
        """Test that SSRF protection blocks domains resolving to private IPs."""
        # Mock DNS resolution to return a private IP
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('192.168.1.1', 0))]

        # Even with a seemingly valid domain, it should be blocked if it resolves to a private IP
        url = "https://youtube.com/watch?v=123"

        with self.assertRaises(ValueError) as cm:
            get_video_info(url)

        self.assertIn("Security validation failed: Domain resolves to non-public IP", str(cm.exception))

    @patch('utils.downloader.socket.getaddrinfo')
    def test_ssrf_loopback_ip(self, mock_getaddrinfo):
        from utils.downloader import _check_domain_resolves_to_public_ip
        _check_domain_resolves_to_public_ip.cache_clear()
        """Test that SSRF protection blocks domains resolving to loopback IPs."""
        # Mock DNS resolution to return a loopback IP
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('127.0.0.1', 0))]

        url = "https://youtube.com/watch?v=123"

        with self.assertRaises(ValueError) as cm:
            get_video_info(url)

        self.assertIn("Security validation failed: Domain resolves to non-public IP", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
