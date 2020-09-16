import os

import pytest

from nearuplib.constants import WATCHER_PID_FILE
from nearuplib.watcher import run_watcher, stop_watcher

WATCHER_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../watcher',
)


def setup_module(module):  # pylint: disable=W0613
    if os.path.exists(WATCHER_PID_FILE):
        os.remove(WATCHER_PID_FILE)


def test_running_and_stopping_watcher():
    run_watcher('betanet', WATCHER_PATH)
    assert os.path.exists(WATCHER_PID_FILE)

    stop_watcher()
    assert not os.path.exists(WATCHER_PID_FILE)


def test_running_bad_path():
    with pytest.raises(SystemExit) as err:
        run_watcher('betanet', os.path.expanduser('~/does/not/exist'))

    assert err.value.code == 1
