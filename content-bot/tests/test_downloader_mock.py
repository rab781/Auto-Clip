import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to path
# We need to add content-bot directory to sys.path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

class TestDownloaderMock(unittest.TestCase):

    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules, {
            'yt_dlp': MagicMock(),
            'yt_dlp.utils': MagicMock(),
            'requests': MagicMock(),
            'dotenv': MagicMock(),
            'cv2': MagicMock(),
            'mediapipe': MagicMock(),
            'numpy': MagicMock()
        })
        self.modules_patcher.start()

        # Ensure utils.downloader is imported/reloaded with mocks
        if 'utils.downloader' in sys.modules:
            import importlib
            importlib.reload(sys.modules['utils.downloader'])
        else:
            import utils.downloader

    def tearDown(self):
        self.modules_patcher.stop()

    @patch('utils.downloader.yt_dlp.YoutubeDL')
    def test_download_audio_only_success(self, mock_ydl_class):
        import utils.downloader
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Mock extract_info return value
        mock_info = {
            'requested_downloads': [{'filepath': '/tmp/output/test.mp3'}]
        }
        mock_ydl.extract_info.return_value = mock_info

        # Call function
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        output_dir = "tests/temp_mock"

        result = utils.downloader.download_audio_only(url, output_dir)

        # Verify
        self.assertEqual(result, '/tmp/output/test.mp3')

        # Verify YoutubeDL was initialized with correct options
        args, kwargs = mock_ydl_class.call_args
        opts = args[0]
        self.assertEqual(opts['format'], 'bestaudio/best')
        self.assertEqual(opts['postprocessors'][0]['key'], 'FFmpegExtractAudio')
        self.assertEqual(opts['postprocessors'][0]['preferredcodec'], 'mp3')
        self.assertTrue(opts['noplaylist'])
        self.assertTrue(opts['quiet'])

        # Verify extract_info called correctly
        mock_ydl.extract_info.assert_called_once_with(url, download=True)

    @patch('utils.downloader.yt_dlp.YoutubeDL')
    def test_download_audio_only_fallback(self, mock_ydl_class):
        import utils.downloader
        # Setup mock for fallback case (requested_downloads missing)
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {'title': 'Test Video'}
        mock_ydl.extract_info.return_value = mock_info

        # On Windows paths might differ, but we assume Linux environment here or use Path logic
        mock_ydl.prepare_filename.return_value = str(Path('tests/temp_mock/Test Video.webm'))

        # Call function
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        output_dir = "tests/temp_mock"

        result = utils.downloader.download_audio_only(url, output_dir)

        # Verify fallback logic (replacing extension with .mp3)
        expected = str(Path('tests/temp_mock/Test Video.mp3'))
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
