import os
import shutil

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from nearuplib.nodelib import restart_nearup, setup_and_run, stop_nearup
from nearuplib.constants import LOGS_FOLDER

NEAR_DIR = os.path.expanduser('~/.near/betanet')
NEARUP_DIR = '~/.nearup'

NEARUP_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../nearup',
)


def cleanup():
    if os.path.exists(NEAR_DIR):
        shutil.rmtree(NEAR_DIR)

    if os.path.exists(NEARUP_DIR):
        shutil.rmtree(NEARUP_DIR)

    if os.path.exists(LOGS_FOLDER):
        shutil.rmtree(LOGS_FOLDER)


def setup_module(module):  # pylint: disable=W0613
    cleanup()

    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)


def teardown_module(module):  # pylint: disable=W0613
    cleanup()


def test_nearup_still_runnable():
    setup_and_run(binary_path='',
                  home_dir=NEAR_DIR,
                  init_flags=['--chain-id=betanet'],
                  boot_nodes='',
                  verbose=True,
                  watcher=False)

    retry_strategy = Retry(total=5, backoff_factor=5)
    http = requests.Session()
    http.mount("http://", HTTPAdapter(max_retries=retry_strategy))

    resp = http.get('http://localhost:3030/status')
    assert resp.status_code == 200
    assert resp.text

    stop_nearup(keep_watcher=True)

    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get('http://localhost:3030/status')

    restart_nearup('betanet', NEARUP_PATH, NEAR_DIR, keep_watcher=True)

    resp = http.get('http://localhost:3030/status')
    assert resp.status_code == 200
    assert resp.text

    stop_nearup(keep_watcher=True)

    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get('http://localhost:3030/status')
