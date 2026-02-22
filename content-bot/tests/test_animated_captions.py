
import unittest
import os
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock missing dependencies in sys.modules BEFORE importing anything from project
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()
sys.modules["yt_dlp.utils"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["mediapipe"] = MagicMock()
sys.modules["mediapipe.solutions"] = MagicMock()
sys.modules["config"] = MagicMock()
sys.modules["config"].CAPTION_SETTINGS = {}

from utils.animated_captions import generate_animated_ass

class TestAnimatedCaptions(unittest.TestCase):
    def setUp(self):
        self.test_output = "test_output.ass"
        self.settings = {
            "font": "Arial",
            "font_size": 20,
            "outline_width": 1,
            "shadow_depth": 1,
            "margin_bottom": 10,
            "highlight_color": "&H00FFFF",
            "words_per_line": 5
        }

    def tearDown(self):
        if os.path.exists(self.test_output):
            os.remove(self.test_output)

    def test_ass_injection(self):
        # Input text with ASS tags
        # We use a payload that tries to inject a style override
        payload = "Hello {\\b1}World{\\b0}"

        segments = [
            {"start": 0, "end": 1, "text": payload}
        ]

        generate_animated_ass(segments, self.test_output, self.settings)

        with open(self.test_output, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify the injection is PREVENTED
        self.assertNotIn(r"{\b1}World{\b0}", content)

        # Verify that brackets and backslash are replaced with full-width equivalents
        # "Hello {\b1}World{\b0}" -> "Hello ｛＼b1｝World｛＼b0｝"
        # Note: Depending on split() logic, spaces might vary slightly, but characters should be there.
        self.assertIn("｛", content)
        self.assertIn("｝", content)
        self.assertIn("＼", content)

        # Verify the specific sanitized string is present (ignoring ASS formatting tags)
        # The content will look like: Dialogue: ...,Default,,0,0,0,,{\c...}Hello {\c...} {\c...}｛＼b1｝World｛＼b0｝{\c...}
        # We check for the sanitized characters in sequence
        self.assertIn("｛＼b1｝World｛＼b0｝", content)

if __name__ == "__main__":
    unittest.main()
