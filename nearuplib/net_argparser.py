import argparse
import os


def create_net_argparser(*, description):
    TELEMETRY_URL = 'https://explorer.nearprotocol.com/api/nodes'

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--local', action='store_true',
                        help='deprecated: use --nodocker')
    parser.add_argument('--nodocker', action='store_true',
                        help='If set, compiles and runs the node on the machine directly (not inside the docker).')
    parser.add_argument('--binary-path', default='',
                        help='near binary path, set to nearcore/target/debug or nearcore/target/release to use locally compiled binary')
    parser.add_argument('--verbose', action='store_true',
                        help='If set, prints verbose logs')
    parser.add_argument('--home', default=os.path.expanduser('~/.near/'),
                        help='Home path for storing configs, keys and chain data (Default: ~/.near)')
    parser.add_argument(
        '--image', default='auto',
        help='Image to run in docker (default: auto)')
    parser.add_argument(
        '--boot-nodes',
        help='Specify boot nodes to load from (Default: "")')
    return parser
