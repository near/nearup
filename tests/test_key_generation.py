import json
import os
import shutil

import pytest

from nearuplib.util import generate_node_key, generate_validator_key, initialize_keys
from nearuplib.nodelib import download_binaries

HOME = os.path.expanduser('~/.near/betanet')
BINARY_PATH = os.path.expanduser('~/.nearup/near/betanet')
WRONG_BINARY_PATH = os.path.expanduser('~/.nearup/near/testnet')
NEARUP_PATH = os.path.expanduser('~/.nearup/')
ACCOUNT_ID = 'mock.nearup.account'


def setup_module(module):  # pylint: disable=W0613
    if os.path.exists(HOME):
        shutil.rmtree(HOME)

    if os.path.exists(NEARUP_PATH):
        shutil.rmtree(NEARUP_PATH)

    os.makedirs(BINARY_PATH)
    os.makedirs(HOME)

    download_binaries('betanet', 'Linux')


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


@pytest.mark.run(order=0)
def test_generate_node_key():
    generate_node_key(HOME, BINARY_PATH)
    assert_node_key()

    with pytest.raises(SystemExit) as err:
        generate_node_key(HOME, WRONG_BINARY_PATH)
    assert err.value.code == 1


@pytest.mark.run(order=1)
def test_generate_validator_key():
    generate_validator_key(HOME, BINARY_PATH, ACCOUNT_ID)
    assert_validator_key()

    with pytest.raises(SystemExit) as err:
        generate_validator_key(HOME, WRONG_BINARY_PATH, ACCOUNT_ID)
    assert err.value.code == 1


@pytest.mark.run(order=2)
def test_initialize_keys_no_validator():
    initialize_keys(HOME, BINARY_PATH)
    assert_node_key()


@pytest.mark.run(order=3)
def test_initialize_keys_validator():
    initialize_keys(HOME, BINARY_PATH, ACCOUNT_ID)
    assert_node_key()
    assert_validator_key()
