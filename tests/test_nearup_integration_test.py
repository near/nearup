import os
import shutil
import json
import logging
import pytest
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from nearuplib.nodelib import restart_nearup, setup_and_run, stop_nearup
from nearuplib.constants import LOGS_FOLDER
from nearuplib.localnet import entry
from nearuplib.util import download_binaries

BETANET_NEAR_DIR = os.path.expanduser('~/.near/betanet')
LOCALNET_NEAR_DIR = os.path.expanduser('~/.near/localnet')
BINARY_DIR = os.path.expanduser('~/.nearup/near/betanet')
NEARUP_DIR = '~/.nearup'

NEARUP_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../nearup',
)


def cleanup():
    logging.info("running cleanup")
    if os.path.exists(BETANET_NEAR_DIR):
        shutil.rmtree(BETANET_NEAR_DIR)

    if os.path.exists(LOCALNET_NEAR_DIR):
        shutil.rmtree(LOCALNET_NEAR_DIR)

    if os.path.exists(NEARUP_DIR):
        shutil.rmtree(NEARUP_DIR)

    if os.path.exists(LOGS_FOLDER):
        shutil.rmtree(LOGS_FOLDER)


def setup_module(module):  # pylint: disable=W0613
    logging.info("running setup module")
    cleanup()

    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)


def teardown_module(module):  # pylint: disable=W0613
    logging.info("running teardown module")
    cleanup()


def download_betanet_binary(dir):
    logging.info("running download_betanet_binary")

    uname = os.uname()[0]
    download_binaries('betanet', uname)

    expected_binary = 'neard'
    path = os.path.join(dir, expected_binary)

    # check if the binary exists
    assert os.path.exists(path)

    # check if the binary is executable
    assert os.access(path, os.X_OK)


def test_nearup_still_runnable_betanet():
    setup_and_run(binary_path='',
                  home_dir=BETANET_NEAR_DIR,
                  chain_id='betanet',
                  boot_nodes='',
                  verbose=True,
                  watcher=False)

    retry_strategy = Retry(total=5, backoff_factor=5)
    http = requests.Session()
    http.mount("http://", HTTPAdapter(max_retries=retry_strategy))

    logging.info("checking status")
    resp = http.get('http://localhost:3030/status')
    assert resp.status_code == 200
    assert resp.text

    logging.info("stopping nearup")
    stop_nearup(keep_watcher=True)

    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get('http://localhost:3030/status')

    logging.info("restarting nearup")
    restart_nearup('betanet', NEARUP_PATH, BETANET_NEAR_DIR, keep_watcher=True)

    logging.info("checking status")
    resp = http.get('http://localhost:3030/status')
    assert resp.status_code == 200
    assert resp.text

    logging.info("stopping nearup")
    stop_nearup(keep_watcher=True)

    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get('http://localhost:3030/status')


def test_nearup_still_runnable_localnet():
    # use betanet binary because downloading localnet doesn't work so well
    download_betanet_binary(BINARY_DIR)

    n = 4
    entry(binary_path=BINARY_DIR,
          home=LOCALNET_NEAR_DIR,
          num_nodes=n,
          num_shards=n,
          override=True,
          fix_accounts=True,
          archival_nodes=True,
          tracked_shards="all",
          verbose=True,
          interactive=False)

    retry_strategy = Retry(total=5, backoff_factor=5)
    http = requests.Session()
    http.mount("http://", HTTPAdapter(max_retries=retry_strategy))

    for i in range(n):
        logging.info(f"Checking the config of the {i}th node")
        config_path = os.path.join(LOCALNET_NEAR_DIR, f"node{i}", "config.json")
        assert os.path.exists(config_path)

        with open(config_path) as file:
            config = json.load(file)
            # test the --archival-nodes argument
            assert config['archive'] == True

    for i in range(n):
        logging.info(f"Checking the genesis of the {i}th node")
        genesis_path = os.path.join(LOCALNET_NEAR_DIR, f"node{i}",
                                    "genesis.json")
        assert os.path.exists(genesis_path)

        with open(genesis_path) as file:
            genesis = json.load(file)
            # test the --num-nodes argument
            assert len(genesis['validators']) == 4
            # test the --fixed-accounts argument
            assert genesis['shard_layout']["V1"]["fixed_shards"] == [
                "shard0", "shard1", "shard2"
            ]

    for i in range(n):
        logging.info(f"Checking the status of the {i}th node.")
        port = 3030 + i
        resp = http.get(f'http://localhost:{port}/status')
        assert resp.status_code == 200
        assert resp.text

    stop_nearup(keep_watcher=True)

    for i in range(n):
        with pytest.raises(requests.exceptions.ConnectionError):
            port = 3030 + i
            requests.get(f'http://localhost:{port}/status')
