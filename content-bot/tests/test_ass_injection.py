import unittest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock dependencies BEFORE importing utils
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.animated_captions import generate_animated_ass

class TestASSInjection(unittest.TestCase):
    def setUp(self):
        self.output_path = "test_output.ass"

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_ass_injection_vulnerability(self):
        """
        Test that malicious ASS tags in input text are sanitized.
        """
        # Malicious input containing ASS tags (Bold tag)
        # Using a tag without spaces to ensure it stays in one word chunk
        malicious_text = "Hello {\\b1}BoldWorld"
        segments = [{"start": 0, "end": 1, "text": malicious_text}]
        settings = {}

        generate_animated_ass(segments, self.output_path, settings)

        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"\n[DEBUG] Generated ASS Content:\n{content}")

        # We expect the curly braces to be sanitized.
        # If vulnerability exists, "{\b1}" will be present literally as a tag.
        # This assertion should FAIL if the code is vulnerable.
        self.assertNotIn("{\\b1}", content, "Vulnerability: Malicious ASS tag found in output!")

if __name__ == '__main__':
    unittest.main()
