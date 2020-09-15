import os

LOGS_FOLDER = os.path.expanduser('~/.nearup/logs')
LOCALNET_LOGS_FOLDER = os.path.expanduser("~/.nearup/logs/localnet")
NODE_PID_FILE = os.path.expanduser('~/.nearup/node.pid')
S3_BUCKET = 'build.nearprotocol.com'
WATCHER_PID_FILE = os.path.expanduser('~/.nearup/watcher.pid')
DEFAULT_WAIT_TIMEOUT = 30
