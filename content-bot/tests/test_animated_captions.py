import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Mock missing dependencies
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.animated_captions import generate_animated_ass

class TestAnimatedCaptions(unittest.TestCase):
    def setUp(self):
        self.output_path = "test_captions.ass"
        self.settings = {
            "font": "Arial",
            "font_size": 24,
            "words_per_line": 5,
            "highlight_color": "&H00FFFF"
        }

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_generate_animated_ass_sanitization(self):
        """
        Test that input text containing ASS special characters is sanitized.
        """
        # Malicious payload: attempts to change font size
        payload = "Hello {\\fs200}World"
        segments = [{"start": 0, "end": 2, "text": payload}]

        generate_animated_ass(segments, self.output_path, self.settings)

        self.assertTrue(os.path.exists(self.output_path), "Output file should be created")

        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that the ASS tag injection is neutralized (replaced with full-width chars)
        self.assertNotIn(r"{\fs200}", content, "Vulnerable ASS tag found in output!")
        self.assertIn("｛＼fs200｝", content, "Sanitized text not found in output")

    def test_generate_animated_ass_normal_text(self):
        """
        Test that normal text is processed correctly.
        """
        payload = "Hello World"
        segments = [{"start": 0, "end": 1, "text": payload}]

        generate_animated_ass(segments, self.output_path, self.settings)

        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Hello", content)
        self.assertIn("World", content)

if __name__ == "__main__":
    unittest.main()
