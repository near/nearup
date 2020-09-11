import os

from nearuplib.constants import WATCHER_PID_FILE
from nearuplib.watcher import run_watcher, stop_watcher

WATCHER_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../watcher',
)


def test_running_and_stopping_watcher():
    if os.path.exists(WATCHER_PID_FILE):
        os.remove(WATCHER_PID_FILE)

    run_watcher('betanet', WATCHER_PATH)
    assert os.path.exists(WATCHER_PID_FILE)

    stop_watcher()
    assert not os.path.exists(WATCHER_PID_FILE)
