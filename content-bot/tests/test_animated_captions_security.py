
import unittest
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.animated_captions import generate_animated_ass

class TestAnimatedCaptionsSecurity(unittest.TestCase):
    def test_ass_injection_sanitization(self):
        """
        Test that ASS tags and escape characters are sanitized in the output.
        """
        # Malicious segment containing ASS tags and commands
        segments = [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "Hello {\\c&H0000FF&}World \\N Newline"
            }
        ]

        output_path = "tests/test_output.ass"
        settings = {
            "font": "Arial",
            "font_size": 20,
            "outline_width": 1,
            "shadow_depth": 0,
            "margin_bottom": 10,
            "words_per_line": 5
        }

        try:
            generate_animated_ass(segments, output_path, settings)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify that tags are sanitized
            self.assertNotIn("{\\c&H0000FF&}", content, "ASS tags should be sanitized")
            self.assertNotIn("\\N", content, "Backslashes should be sanitized")

            # Verify sanitized version
            self.assertIn("(/c&H0000FF&)", content, "Curly braces should become parens, backslash forward slash")
            self.assertIn("/N", content)

        finally:
            # Cleanup
            if Path(output_path).exists():
                Path(output_path).unlink()

if __name__ == '__main__':
    unittest.main()
