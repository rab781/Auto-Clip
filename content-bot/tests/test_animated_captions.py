import unittest
import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock yt_dlp before importing utils
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Now import the module under test
# Note: we need to import generate_animated_ass AFTER mocking
try:
    from utils.animated_captions import generate_animated_ass
    from config import CAPTION_SETTINGS
except ImportError:
    # If config or something else fails due to missing .env etc
    sys.modules['dotenv'] = MagicMock()
    from utils.animated_captions import generate_animated_ass
    from config import CAPTION_SETTINGS

class TestAnimatedCaptionsSecurity(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for output files
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.test_dir.name) / "test_output.ass"

    def tearDown(self):
        # Cleanup
        self.test_dir.cleanup()

    def test_ass_injection(self):
        """
        Test that ASS control characters in text are sanitized.
        A malicious input might try to inject style overrides or positioning tags.
        """
        # Malicious payload: trying to change position or color
        # e.g., {\pos(0,0)} or {\c&H0000FF&}
        # The space is important because the splitter splits by space
        malicious_text = "Hello {\\pos(0,0)}World"

        segments = [
            {"start": 0.0, "end": 1.0, "text": malicious_text}
        ]

        # Generate ASS file
        generate_animated_ass(segments, str(self.output_path), CAPTION_SETTINGS)

        # Read the generated file
        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"\n[DEBUG] Generated ASS Content:\n{content[:500]}...")

        # If vulnerable, the file will contain the raw "{\pos(0,0)}" sequence
        # inside the Dialogue line's text field.

        if r"{\pos(0,0)}" in content:
            self.fail("VULNERABILITY FOUND: Raw ASS tags were injected into the subtitle file!")

        # If sanitized, it should contain full-width equivalents or escaped chars
        # Expected: "｛\pos(0,0)｝" or similar

if __name__ == '__main__':
    unittest.main()
