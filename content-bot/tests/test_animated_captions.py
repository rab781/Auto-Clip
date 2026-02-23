
import sys
import os
import unittest
import unittest.mock
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Mock dependencies before import to avoid ImportErrors
sys.modules['yt_dlp'] = unittest.mock.MagicMock()
sys.modules['yt_dlp.utils'] = unittest.mock.MagicMock()
sys.modules['requests'] = unittest.mock.MagicMock()
sys.modules['dotenv'] = unittest.mock.MagicMock()

# Import after mocking
from utils.animated_captions import generate_animated_ass, sanitize_ass_text

class TestAnimatedCaptions(unittest.TestCase):
    def test_sanitize_ass_text(self):
        """Test the sanitization function directly."""
        self.assertEqual(sanitize_ass_text("Hello {World}"), "Hello ｛World｝")
        self.assertEqual(sanitize_ass_text("Path\\To\\File"), "Path＼To＼File")
        self.assertEqual(sanitize_ass_text("{\\c&H0000FF&}"), "｛＼c&H0000FF&｝")
        self.assertEqual(sanitize_ass_text("Normal Text"), "Normal Text")
        self.assertEqual(sanitize_ass_text(""), "")

    def test_generate_animated_ass_injection_prevention(self):
        """Test that generated ASS file contains sanitized text."""
        segments = [
            {"start": 0, "end": 2, "text": "Hello {\\c&H0000FF&}World"}
        ]
        settings = {
            "font": "Arial",
            "font_size": 20,
            "outline_width": 1,
            "shadow_depth": 0,
            "margin_bottom": 10,
            "words_per_line": 5,
            "highlight_color": "&H00FFFF",
        }

        output_path = "test_output.ass"
        try:
            generate_animated_ass(segments, output_path, settings)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify that the malicious tag is sanitized
            # It should look like ｛＼c&H0000FF&｝ in the output
            self.assertIn("｛＼c&H0000FF&｝", content)
            # The raw tag should NOT be present (unless part of our own sanitization check string which is unlikely here)
            # We check specifically for the start of the tag as it would appear if interpreted
            self.assertNotIn("{\\c&H0000FF&}", content)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

if __name__ == '__main__':
    unittest.main()
