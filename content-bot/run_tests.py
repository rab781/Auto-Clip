import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Add content-bot to sys.path so utils can be imported
sys.path.append(str(Path(__file__).parent))

# Mock global dependencies
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()

if __name__ == "__main__":
    # Execute pytest on the tests directory
    sys.exit(pytest.main(["content-bot/tests"]))
