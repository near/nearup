import sys
import argparse
import configparser
from subprocess import Popen
from shutil import rmtree
from os import mkdir, kill, unlink
from signal import SIGTERM
from os.path import exists, expanduser, join
import json


def run_binary(path, home, action, shards=None, validators=None, non_validators=None, boot_nodes=None, output=None):
    command = [path, '--home', home, action]
    if shards:
        command.extend(['--shards', str(shards)])
    if validators:
        command.extend(['--v', str(validators)])
    if non_validators:
        command.extend(['--n', str(non_validators)])
    if boot_nodes:
        command.extend(['--boot-nodes', boot_nodes])

    if output:
        stdout = open(f'{output}.out', 'w')
        stderr = open(f'{output}.err', 'w')
    else:
        stdout = None
        stderr = None

    return Popen(command, stdout=stdout, stderr=stderr)


def run(args):
    if args.overwrite:
        if exists(args.home):
            print("Removing old data.")
            rmtree(args.home)

    if not exists(args.home):
        run_binary(args.binary_path, args.home,
                   'testnet', shards=args.num_shards, validators=args.num_nodes).wait()

    # Edit args files
    for i in range(0, args.num_nodes):
        args_json = join(args.home, f'node{i}', 'config.json')
        with open(args_json, 'r') as f:
            data = json.load(f)
        data['rpc']['addr'] = f'0.0.0.0:{3030 + i}'
        data['network']['addr'] = f'0.0.0.0:{24567 + i}'
        with open(args_json, 'w') as f:
            json.dump(data, f, indent=2)

    # Load public key from first node
    with open(join(args.home, f'node0', 'node_key.json'), 'r') as f:
        data = json.load(f)
        pk = data['public_key']

    # Recreate log folder
    rmtree('logs', ignore_errors=True)
    mkdir('logs')

    # Spawn network
    pid_fd = open('node.pid', 'w')
    for i in range(0, args.num_nodes):
        proc = run_binary(args.binary_path, join(args.home, f'node{i}'), 'run',
                          boot_nodes=f'{pk}@127.0.0.1:24567' if i > 0 else None, output=f'logs/node{i}')
        print(proc.pid, file=pid_fd)
    pid_fd.close()


def entry():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary-path', help="near binary path, set to nearcore/target/debug or nearcore/target/release to use locally compiled binary")
    parser.add_argument('--home', default=expanduser('~/.near/localnet'),
                        help='Home path for storing configs, keys and chain data (Default: ~/.near/localnet)')
    parser.add_argument('--num-nodes', help="Number of nodes", default=4, type=int)
    parser.add_argument('--num-shards', help="Number of shards", default=1, type=int)
    parser.add_argument('--overwrite', default=False, action='store_true', help="Overwrite previous node data if exists.")
    parser.add_argument('--stop', default=False, action='store_true', help="Stop localnet if it is running.")

    args = parser.parse_args(sys.argv[2:])

    if args.binary_path is None:
        parser.print_usage()
        exit(0)

    args.binary_path = join(args.binary_path, 'near')

    path = 'node.pid'
    if args.stop:
        if exists(path):
            with open(path) as f:
                for x in f.readlines():
                    pid = int(x.strip(' \n'))
                    print("Killing:", pid)
                    kill(pid, SIGTERM)
            unlink(path)
    else:
        if exists(path):
            print("There is already a test running. Stop it using:")
            print("python3 start_localnet.py -k")
            print("If this is a mistake, remove node.pid")
            exit(1)

        run(args)
