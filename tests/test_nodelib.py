import json
import os
import shutil
from pathlib import Path

import pytest

from nearuplib.nodelib import check_and_setup

ACCOUNT_ID = 'mock.nearup.account'
BETANET_HOME = os.path.expanduser('~/.near/betanet')
BETANET_BINARY_PATH = os.path.expanduser('~/.near/near/betanet')
BETANET_INIT_FLAGS = ['--chain-id=betanet', f'--account-id={ACCOUNT_ID}']
LOCALNET_HOME = os.path.expanduser('~/.near/localnet')
LOCALNET_BINARY_PATH = os.path.expanduser('~/.near/near/localnet')
LOCALNET_INIT_FLAGS = ['--chain-id=localnet']


def cleanup():
    if os.path.exists(LOCALNET_HOME):
        shutil.rmtree(LOCALNET_HOME)

    if os.path.exists(BETANET_HOME):
        shutil.rmtree(BETANET_HOME)


def setup_module(module):  # pylint: disable=W0613
    cleanup()
    os.makedirs(BETANET_HOME)
    os.makedirs(LOCALNET_HOME)


def teardown_module(module):  # pylint: disable=W0613
    cleanup()


def write_config_files(home):
    Path(f'{home}/node_key.json').touch()
    Path(f'{home}/config.json').touch()
    Path(f'{home}/genesis.json').touch()


def write_genesis(home, chain_id):
    with open(f'{home}/genesis.json', 'w') as genesis:
        json.dump({'chain_id': chain_id}, genesis)


def test_check_and_setup_localnet_existing_config():
    """Home directory exists with config"""
    write_config_files(LOCALNET_HOME)
    write_genesis(LOCALNET_HOME, 'localnet')

    try:
        check_and_setup(LOCALNET_BINARY_PATH, LOCALNET_HOME,
                        LOCALNET_INIT_FLAGS)
    except Exception as ex:
        pytest.fail(f'unexpected expection {ex}')


def test_check_and_setup_betanet_existing_config():
    """Home directory for betanet exists with config"""
    write_config_files(BETANET_HOME)
    write_genesis(BETANET_HOME, 'betanet')

    try:
        check_and_setup(BETANET_BINARY_PATH, BETANET_HOME, BETANET_INIT_FLAGS)
    except Exception as ex:
        pytest.fail(f'unexpected exception {ex}')
