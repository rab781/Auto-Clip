import unittest
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Mock problematic submodules of utils to avoid side effects during import
# This prevents utils/__init__.py from importing the actual modules
sys.modules['utils.ai_logic'] = MagicMock()
sys.modules['utils.downloader'] = MagicMock()
sys.modules['utils.processor'] = MagicMock()

# Also mock external dependencies just in case
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['config'] = MagicMock()

# Add project root to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.time_utils import format_timestamp

class TestTimeUtils(unittest.TestCase):

    def test_srt_format(self):
        self.assertEqual(format_timestamp(0, 'srt'), "00:00:00,000")
        self.assertEqual(format_timestamp(1, 'srt'), "00:00:01,000")
        self.assertEqual(format_timestamp(60, 'srt'), "00:01:00,000")
        self.assertEqual(format_timestamp(3600, 'srt'), "01:00:00,000")
        self.assertEqual(format_timestamp(3661, 'srt'), "01:01:01,000")
        self.assertEqual(format_timestamp(0.5, 'srt'), "00:00:00,500")
        self.assertEqual(format_timestamp(1.001, 'srt'), "00:00:01,001")
        self.assertEqual(format_timestamp(1.999, 'srt'), "00:00:01,999")

    def test_ass_format(self):
        self.assertEqual(format_timestamp(0, 'ass'), "0:00:00.00")
        self.assertEqual(format_timestamp(1, 'ass'), "0:00:01.00")
        self.assertEqual(format_timestamp(60, 'ass'), "0:01:00.00")
        self.assertEqual(format_timestamp(3600, 'ass'), "1:00:00.00")
        self.assertEqual(format_timestamp(3661, 'ass'), "1:01:01.00")
        self.assertEqual(format_timestamp(0.5, 'ass'), "0:00:00.50")
        self.assertEqual(format_timestamp(1.01, 'ass'), "0:00:01.01")
        # Note: 1.99 seconds -> 99 centiseconds
        self.assertEqual(format_timestamp(1.99, 'ass'), "0:00:01.99")

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            format_timestamp(0, 'invalid')

if __name__ == '__main__':
    unittest.main()
