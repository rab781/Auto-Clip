import unittest
import sys
from unittest.mock import MagicMock
from pathlib import Path
import os
import shutil

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
        self.output_dir = Path("tests/temp_captions")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.output_dir / "test_injection.ass"

    def tearDown(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    def test_ass_injection(self):
        # Malicious segment trying to inject ASS tags
        # {\c&H0000FF&} sets the color to red in ASS (BGR)
        injection_payload = "{\\c&H0000FF&}INJECTED"
        segments = [
            {"start": 0, "end": 1, "text": f"Normal {injection_payload} Text"}
        ]

        settings = {
            "font": "Arial",
            "font_size": 24,
            "words_per_line": 5,
            "highlight_color": "&H00FFFF",  # Default Yellow
        }

        generate_animated_ass(segments, str(self.output_path), settings)

        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()

        print("\n--- ASS Content Start ---")
        print(content)
        print("--- ASS Content End ---")

        # Check if the injection payload exists verbatim - it MUST NOT
        self.assertNotIn("{\\c&H0000FF&}", content)

        # Check if the sanitized version exists - it MUST be there
        # We replaced { with ｛, } with ｝, \ with ＼
        sanitized_payload = "｛＼c&H0000FF&｝INJECTED"
        self.assertIn(sanitized_payload, content)

if __name__ == "__main__":
    unittest.main()
