import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib

# Add project root to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

class TestSecurityDownloader(unittest.TestCase):

    def setUp(self):
        # Mock dependencies using patch.dict on sys.modules
        self.modules_patcher = patch.dict(sys.modules, {
            'yt_dlp': MagicMock(),
            'yt_dlp.utils': MagicMock(),
            'requests': MagicMock(),
            'dotenv': MagicMock(),
            'cv2': MagicMock(),
            'mediapipe': MagicMock(),
            'numpy': MagicMock()
        })
        self.modules_patcher.start()

        # Reload utils.downloader to ensure it uses mocked dependencies
        if 'utils.downloader' in sys.modules:
            importlib.reload(sys.modules['utils.downloader'])
        else:
            import utils.downloader

    def tearDown(self):
        self.modules_patcher.stop()

    @patch('utils.downloader._validate_youtube_url')
    def test_argument_injection_bypass_validation(self, mock_validate):
        """
        Test that even if validation is bypassed, yt-dlp arguments are not injected.
        This confirms the presence and effectiveness of the '--' delimiter.
        """
        import utils.downloader

        # Mock validation to allow anything
        mock_validate.return_value = True

        # Payload that would be interpreted as a flag if injection exists
        payload = "--version"

        try:
            utils.downloader.get_video_info(payload)
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
        import utils.downloader
        payload = "--help"

        # Should be blocked by URL validation now
        try:
            utils.downloader.get_video_info(payload)
            self.fail("No exception raised for invalid URL/flag injection")
        except ValueError as e:
            self.assertIn("Security validation failed", str(e))
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e)}")

    def test_download_audio_injection(self):
        """Test that download_audio_only validation blocks flags."""
        import utils.downloader
        payload = "--version"
        output_dir = "tests/temp"

        with self.assertRaises(ValueError) as cm:
            utils.downloader.download_audio_only(payload, output_dir)

        self.assertIn("Security validation failed", str(cm.exception))

    def test_download_video_segment_injection(self):
        """Test that download_video_segment validation blocks flags."""
        import utils.downloader
        payload = "--version"
        output_path = "tests/temp/segment.mp4"
        start = 0
        end = 10

        with self.assertRaises(ValueError) as cm:
            utils.downloader.download_video_segment(payload, start, end, output_path)

        self.assertIn("Security validation failed", str(cm.exception))

    def test_url_validation(self):
        """Test URL validation logic."""
        import utils.downloader
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
                utils.downloader.get_video_info(url)
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
                utils.downloader.get_video_info(url)
            self.assertIn("Security validation failed", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
