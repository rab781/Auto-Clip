import unittest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock missing dependencies
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Now import the function to test
# Note: we import directly from the file to avoid triggering package init if possible,
# or we rely on mocks if it does.
from utils.animated_captions import generate_animated_ass

class TestAssInjection(unittest.TestCase):
    def test_ass_injection_sanitization(self):
        """
        Test that special characters in text are sanitized to prevent ASS injection.
        """
        # Malicious payload: tries to change alignment to top-center (an8)
        malicious_text = "Hello {\\an8}World"
        segments = [
            {"start": 0, "end": 1, "text": malicious_text}
        ]
        output_path = "test_output.ass"
        settings = {
            "font": "Arial",
            "font_size": 24,
            "words_per_line": 5,
            # Ensure animated style is used
            "style": "animated"
        }

        generate_animated_ass(segments, output_path, settings)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)

        # The malicious payload "{\an8}" should NOT be active.
        # It should be escaped or replaced.
        # If it is present exactly as "{\an8}", then injection succeeded.

        print(f"Content snippet: {content[:200]}...")

        # We verify that the raw tag is NOT present
        self.assertNotIn(r"{\an8}", content, "ASS tag injection detected! Input '{\\an8}' was found raw in output.")

        # We verify that the sanitized version IS present
        # { -> ｛, } -> ｝, \ -> ＼
        # Input: Hello {\an8}World
        # Expected snippet: ... ｛＼an8｝World ... (depending on split logic, but characters should be replaced)

        # Since the code splits by space:
        # words = ["Hello", "{\an8}World"]
        # or similar depending on where spaces are.
        # "Hello {\an8}World" -> ["Hello", "{\an8}World"]

        # The sanitized version of "{\an8}World" should be "｛＼an8｝World"
        if "｛＼an8｝" not in content:
             self.fail(f"Sanitization failed or unexpected format. Content snippet: {content[:200]}")

if __name__ == '__main__':
    unittest.main()
