
import unittest
import sys
import os
from pathlib import Path

# Add project root to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.downloader import get_video_info, download_audio_only, download_video_segment

class TestSecurityDownloader(unittest.TestCase):

    def test_get_video_info_injection(self):
        """Test that passing a flag as URL is treated as an invalid URL, not an option."""
        # Using --help as the injection payload
        payload = "--help"

        # If vulnerable, this would likely raise JSONDecodeError or return garbage
        # If fixed, this should raise an Exception from subprocess returning non-zero (invalid URL)

        # We need to catch Exception broadly because get_video_info might raise JSONDecodeError if vulnerable
        # or Exception("yt-dlp error") if fixed.
        try:
            get_video_info(payload)
            self.fail("No exception raised for invalid URL/flag injection")
        except Exception as e:
            # Check if it's the secure error (yt-dlp error)
            if "yt-dlp error" in str(e):
                # This is good
                pass
            else:
                # This is likely JSONDecodeError or similar, meaning vulnerability executed
                self.fail(f"Vulnerability executed or unexpected error: {e}")

    def test_download_audio_injection(self):
        """Test that download_audio_only treats flags as URLs."""
        payload = "--version"
        output_dir = "tests/temp"

        with self.assertRaises(Exception) as cm:
            download_audio_only(payload, output_dir)

        self.assertIn("yt-dlp error", str(cm.exception))

    def test_download_video_segment_injection(self):
        """Test that download_video_segment treats flags as URLs."""
        payload = "--version"
        output_path = "tests/temp/segment.mp4"
        start = 0
        end = 10

        with self.assertRaises(Exception) as cm:
            download_video_segment(payload, start, end, output_path)

        self.assertIn("yt-dlp error", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
