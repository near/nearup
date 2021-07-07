import os

LOCALNET_FOLDER = os.path.expanduser("~/.nearup/near/localnet")
LOGS_FOLDER = os.path.expanduser('~/.nearup/logs')
LOCALNET_LOGS_FOLDER = os.path.expanduser("~/.nearup/logs/localnet")
NODE_PID_FILE = os.path.expanduser('~/.nearup/node.pid')
WATCHER_PID_FILE = os.path.expanduser('~/.nearup/watcher.pid')
DEFAULT_WAIT_TIMEOUT = 30

S3_BUCKETS = {
    'default': 'build.nearprotocol.com',
    'mainnet': 'build.nearprotocol.com',
    'testnet': 'build.nearprotocol.com',
    'betanet': 'build.nearprotocol.com',
    'guildnet': 'build.openshards.io',
}
