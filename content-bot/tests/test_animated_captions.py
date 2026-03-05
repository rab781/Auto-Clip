import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Mock missing dependencies
sys.modules['requests'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.animated_captions import sanitize_ass_text, generate_animated_ass

class TestAnimatedCaptions(unittest.TestCase):

    def test_sanitize_ass_text(self):
        """
        Test that ASS tags are properly sanitized by replacing special characters.
        """
        # Input with special characters used in ASS tags
        input_text = "Hello {\\c&H0000FF&}World\\!"

        # Call the sanitization function
        sanitized_text = sanitize_ass_text(input_text)

        # Verify the special characters are replaced with full-width equivalents
        self.assertNotIn('{', sanitized_text)
        self.assertNotIn('}', sanitized_text)
        self.assertNotIn('\\', sanitized_text)

        self.assertIn('｛', sanitized_text)
        self.assertIn('｝', sanitized_text)
        self.assertIn('＼', sanitized_text)

        # Output should be the replaced string
        self.assertEqual("Hello ｛＼c&H0000FF&｝World＼!", sanitized_text)

    def test_generate_animated_ass_sanitizes_input(self):
        """
        Test that generate_animated_ass sanitizes the input text before processing.
        """
        # Create a temporary output file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.ass', delete=False) as temp_file:
            output_path = temp_file.name

        try:
            # Prepare dummy input data
            segments = [
                {"start": 0, "end": 2, "text": "Testing {injection} attack"}
            ]
            settings = {
                "font": "Arial",
                "font_size": 24,
                "outline_width": 2,
                "shadow_depth": 1,
                "margin_bottom": 50,
                "highlight_color": "&H00FFFF",
                "words_per_line": 2
            }

            # Call the function to generate ASS file
            generate_animated_ass(segments, output_path, settings)

            # Read the output file
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Verify that the original tag structure {injection} is not present
            self.assertNotIn("{injection}", content)

            # Instead, the sanitized version should be present
            # We look for "｛injection｝" in the generated dialogue lines
            self.assertIn("｛injection｝", content)

        finally:
            # Clean up temporary file
            Path(output_path).unlink()

if __name__ == '__main__':
    unittest.main()
