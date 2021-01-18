import json
import os
import shutil

from nearuplib.nodelib import download_binaries, init_near

HOME = os.path.expanduser('~/.near/betanet')
BINARY_PATH = os.path.expanduser('~/.nearup/near/betanet')
NEARUP_PATH = os.path.expanduser('~/.nearup/')
ACCOUNT_ID = 'mock.nearup.account'


def setup_module(module):  # pylint: disable=W0613
    if os.path.exists(HOME):
        shutil.rmtree(HOME)

    if os.path.exists(NEARUP_PATH):
        shutil.rmtree(NEARUP_PATH)

    os.makedirs(BINARY_PATH)
    os.makedirs(HOME)

    uname = os.uname()[0]
    download_binaries('betanet', uname)


def assert_node_key():
    node_key_path = os.path.join(HOME, 'node_key.json')
    assert os.path.exists(node_key_path)

    with open(node_key_path) as node_key:
        data = json.loads(node_key.read())
        assert data['account_id'] == ''
        assert 'public_key' in data
        assert 'secret_key' in data


def assert_validator_key():
    validator_key_path = os.path.join(HOME, 'validator_key.json')
    assert os.path.exists(validator_key_path)

    with open(validator_key_path) as node_key:
        data = json.loads(node_key.read())
        assert data['account_id'] == ACCOUNT_ID
        assert 'public_key' in data
        assert 'secret_key' in data


def test_init_near():
    init_near(HOME, BINARY_PATH, 'betanet',
              ['--chain-id=betanet', f'--account-id={ACCOUNT_ID}'])
    assert_node_key()
    assert_validator_key()
