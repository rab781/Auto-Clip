
import unittest
from unittest.mock import MagicMock
import sys
import os
from pathlib import Path

# Mock yt_dlp and other dependencies before importing module under test
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.animated_captions import generate_animated_ass

class TestAnimatedCaptions(unittest.TestCase):
    def setUp(self):
        self.output_path = "test_output.ass"
        self.settings = {
            "font": "Arial",
            "font_size": 24,
            "words_per_line": 5,
            "highlight_color": "&H00FFFF"
        }

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_ass_sanitization(self):
        """Test that ASS special characters are sanitized."""
        # Malicious payload with ASS tags
        payload = "Hello {\\fs200}World"
        segments = [{"start": 0, "end": 2, "text": payload}]

        generate_animated_ass(segments, self.output_path, self.settings)

        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that the ASS tag {\\fs200} is NOT present as a tag
        # The sanitization replaces { with ｛ and } with ｝ and \ with ＼
        # So we expect "｛＼fs200｝" in the output

        self.assertNotIn("{\\fs200}", content, "ASS tag injection detected!")
        # We check for the sanitized version. Note that the function replaces characters individually.
        # { -> ｛
        # \ -> ＼
        # } -> ｝
        self.assertIn("｛＼fs200｝", content, "Sanitized text not found in output")

    def test_normal_text(self):
        """Test that normal text is processed correctly."""
        segments = [{"start": 0, "end": 2, "text": "Hello World"}]
        generate_animated_ass(segments, self.output_path, self.settings)

        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Hello", content)
        self.assertIn("World", content)

if __name__ == '__main__':
    unittest.main()
