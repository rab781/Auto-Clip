import sys
from unittest.mock import MagicMock
sys.modules['yt_dlp'] = MagicMock()
sys.modules['yt_dlp.utils'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import unittest
if __name__ == '__main__':
    loader = unittest.TestLoader()
    tests = loader.discover('content-bot/tests')
    testRunner = unittest.runner.TextTestRunner(verbosity=2)
    testRunner.run(tests)
