import json
import os
import shutil

from nearuplib.util import download_binaries, download_config, download_genesis

HOME_DIR = os.path.expanduser('~/.near/betanet')
NEARUP_BINARY_DIR = os.path.expanduser('~/.nearup/near/betanet')


def setup_module(module):  # pylint: disable=W0613
    if os.path.exists(HOME_DIR):
        shutil.rmtree(HOME_DIR)

    if os.path.exists(NEARUP_BINARY_DIR):
        shutil.rmtree(NEARUP_BINARY_DIR)

    os.makedirs(HOME_DIR)
    os.makedirs(NEARUP_BINARY_DIR)


def test_download_binaries():
    uname = os.uname()[0]
    download_binaries('betanet', uname)

    expected_binary = 'neard'
    path = os.path.join(NEARUP_BINARY_DIR, expected_binary)

    # check if the binary exists
    assert os.path.exists(path)

    # check if the binary is executable
    assert os.access(path, os.X_OK)


def test_download_config():
    download_config('betanet', HOME_DIR)
    path = os.path.join(HOME_DIR, 'config.json')

    assert os.path.exists(path)
    with open(path) as config:
        json.loads(config.read())


def test_download_genesis():
    download_genesis('betanet', HOME_DIR)
    path = os.path.join(HOME_DIR, 'genesis.json')

    assert os.path.exists(path)
    with open(path) as genesis:
        json.loads(genesis.read())
