import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock problematic submodules to avoid side effects during import
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.downloader import _seconds_to_hhmmss

class TestDownloaderUtils(unittest.TestCase):

    def test_seconds_to_hhmmss_zero(self):
        """Test zero seconds."""
        self.assertEqual(_seconds_to_hhmmss(0), "00:00:00")

    def test_seconds_to_hhmmss_sub_minute(self):
        """Test less than a minute."""
        self.assertEqual(_seconds_to_hhmmss(45), "00:00:45")

    def test_seconds_to_hhmmss_minute_boundary(self):
        """Test exactly one minute."""
        self.assertEqual(_seconds_to_hhmmss(60), "00:01:00")

    def test_seconds_to_hhmmss_sub_hour(self):
        """Test less than an hour."""
        self.assertEqual(_seconds_to_hhmmss(3599), "00:59:59")

    def test_seconds_to_hhmmss_hour_boundary(self):
        """Test exactly one hour."""
        self.assertEqual(_seconds_to_hhmmss(3600), "01:00:00")

    def test_seconds_to_hhmmss_multi_hour(self):
        """Test multiple hours."""
        self.assertEqual(_seconds_to_hhmmss(3665), "01:01:05")
        self.assertEqual(_seconds_to_hhmmss(7325), "02:02:05")

    def test_seconds_to_hhmmss_float_truncation(self):
        """Test that floating point inputs are properly truncated to integers."""
        self.assertEqual(_seconds_to_hhmmss(0.999), "00:00:00")
        self.assertEqual(_seconds_to_hhmmss(60.5), "00:01:00")
        self.assertEqual(_seconds_to_hhmmss(3601.9), "01:00:01")

if __name__ == '__main__':
    unittest.main()
