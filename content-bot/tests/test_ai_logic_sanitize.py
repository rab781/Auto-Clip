import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock dependencies before importing ai_logic
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['mediapipe.tasks'] = MagicMock()
sys.modules['mediapipe.tasks.python'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

class TestAILogicSanitize(unittest.TestCase):
    @patch('utils.ai_logic.CHUTES_API_KEY', 'test_key_with_special/chars+')
    def test_sanitize_error_msg_url_encoded_case_insensitive(self):
        import utils.ai_logic as ai_logic

        # Test plaintext
        msg_plain = "Error with test_key_with_special/chars+"
        sanitized_plain = ai_logic._sanitize_error_msg(msg_plain)
        self.assertEqual(sanitized_plain, "Error with [REDACTED]")

        # Test URL encoded uppercase
        msg_upper = "Error with test_key_with_special%2Fchars%2B"
        sanitized_upper = ai_logic._sanitize_error_msg(msg_upper)
        self.assertEqual(sanitized_upper, "Error with [REDACTED]")

        # Test URL encoded lowercase
        msg_lower = "Error with test_key_with_special%2fchars%2b"
        sanitized_lower = ai_logic._sanitize_error_msg(msg_lower)
        self.assertEqual(sanitized_lower, "Error with [REDACTED]")

        # Test mixed case
        msg_mixed = "Error with test_key_with_special%2Fchars%2b"
        sanitized_mixed = ai_logic._sanitize_error_msg(msg_mixed)
        self.assertEqual(sanitized_mixed, "Error with [REDACTED]")

if __name__ == '__main__':
    unittest.main()
