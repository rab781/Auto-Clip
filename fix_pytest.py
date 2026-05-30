import sys
import mock

# create a dummy pytest module and add it to sys.modules
dummy_pytest = mock.MagicMock()
sys.modules['pytest'] = dummy_pytest
