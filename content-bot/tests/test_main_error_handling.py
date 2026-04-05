import sys
import argparse
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import importlib
from unittest.mock import patch

# We mock the dependencies locally in the test scope or using patch.dict
import sys
sys.modules['tqdm'] = MagicMock()
sys.modules['utils'] = MagicMock()
sys.modules['config'] = MagicMock()

from main import main

@patch('main.argparse.ArgumentParser.parse_args')
@patch('main.process_video')
@patch('main.sys.exit')
@patch('builtins.print')
@patch('traceback.print_exc')
def test_main_error_handling_no_debug(mock_print_exc, mock_print, mock_exit, mock_process_video, mock_parse_args):
    """Test that stack traces are suppressed by default."""
    # Setup args without debug
    args = MagicMock()
    args.url = "https://youtube.com/watch?v=1234"
    args.url_flag = None
    args.dry_run = False
    args.debug = False
    mock_parse_args.return_value = args

    # Force an exception
    mock_process_video.side_effect = Exception("Test Error")

    # Call main
    main()

    # Verify traceback was NOT printed
    mock_print_exc.assert_not_called()
    mock_exit.assert_called_with(1)

@patch('main.argparse.ArgumentParser.parse_args')
@patch('main.process_video')
@patch('main.sys.exit')
@patch('builtins.print')
@patch('traceback.print_exc')
def test_main_error_handling_with_debug(mock_print_exc, mock_print, mock_exit, mock_process_video, mock_parse_args):
    """Test that stack traces are shown when debug flag is used."""
    # Setup args with debug
    args = MagicMock()
    args.url = "https://youtube.com/watch?v=1234"
    args.url_flag = None
    args.dry_run = False
    args.debug = True
    mock_parse_args.return_value = args

    # Force an exception
    mock_process_video.side_effect = Exception("Test Error")

    # Call main
    main()

    # Verify traceback WAS printed
    mock_print_exc.assert_called_once()
    mock_exit.assert_called_with(1)
