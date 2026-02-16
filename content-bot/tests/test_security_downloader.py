import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

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

from utils.downloader import get_video_info, download_audio_only, download_video_segment

class TestSecurityDownloader(unittest.TestCase):

    @patch('utils.downloader.validate_youtube_url')
    def test_argument_injection_bypass_validation(self, mock_validate):
        """
        Test that even if validation is bypassed, yt-dlp arguments are not injected.
        This confirms the presence and effectiveness of the '--' delimiter.
        """
        # Mock validation to allow anything
        mock_validate.return_value = True

        # Payload that would be interpreted as a flag if injection exists
        payload = "--version"

        try:
            get_video_info(payload)
            self.fail("Should have raised an exception (yt-dlp error)")
        except Exception as e:
            # If yt-dlp tried to download "--version", it fails with exit code != 0
            # and raises Exception("yt-dlp error...").
            # If it executed "--version", it succeeds (exit code 0) and prints version,
            # which causes JSON decode error in get_video_info.
            self.assertIn("yt-dlp error", str(e),
                          "yt-dlp executed the flag instead of treating it as a URL!")

    def test_get_video_info_injection(self):
        """Test that passing a flag as URL is blocked by validation."""
        payload = "--help"

        # Should be blocked by URL validation now
        try:
            get_video_info(payload)
            self.fail("No exception raised for invalid URL/flag injection")
        except ValueError as e:
            self.assertIn("Security validation failed", str(e))
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e)}")

    def test_download_audio_injection(self):
        """Test that download_audio_only validation blocks flags."""
        payload = "--version"
        output_dir = "tests/temp"

        with self.assertRaises(ValueError) as cm:
            download_audio_only(payload, output_dir)

        self.assertIn("Security validation failed", str(cm.exception))

    def test_download_video_segment_injection(self):
        """Test that download_video_segment validation blocks flags."""
        payload = "--version"
        output_path = "tests/temp/segment.mp4"
        start = 0
        end = 10

        with self.assertRaises(ValueError) as cm:
            download_video_segment(payload, start, end, output_path)

        self.assertIn("Security validation failed", str(cm.exception))

    def test_url_validation(self):
        """Test URL validation logic."""
        # Valid URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]

        for url in valid_urls:
            try:
                # calling get_video_info triggers validation first.
                # It might fail later with network error or yt-dlp error,
                # but NOT Security validation failed.
                get_video_info(url)
            except ValueError as e:
                if "Security validation failed" in str(e):
                     self.fail(f"Valid URL failed validation: {url}")
            except Exception:
                # Ignore other errors (network, etc)
                pass

        # Invalid URLs
        invalid_urls = [
            "http://example.com/video",
            "https://google.com",
            "file:///etc/passwd",
            "http://localhost:8000/video.mp4",
            "ftp://youtube.com/video",
            "javascript:alert(1)",
        ]

        for url in invalid_urls:
            with self.assertRaises(ValueError) as cm:
                get_video_info(url)
            self.assertIn("Security validation failed", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
