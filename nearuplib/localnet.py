import sys
import argparse
import configparser
from subprocess import Popen, PIPE
from shutil import rmtree
from os import mkdir
from os.path import exists, expanduser, join
import json
from nearuplib.nodelib import run_binary, NODE_PID, proc_name_from_pid, run_docker_testnet, run_docker, check_exist_neard


def run(args):
    if args.overwrite:
        if exists(args.home):
            print("Removing old data.")
            rmtree(args.home)

    if not exists(args.home):
        if args.docker_image:
            run_docker_testnet(args.docker_image, args.home,
                               shards=args.num_shards, validators=args.num_nodes)
        else:
            run_binary(args.binary_path, args.home,
                       'testnet', shards=args.num_shards, validators=args.num_nodes).wait()

    # Edit args files
    for i in range(0, args.num_nodes):
        args_json = join(args.home, f'node{i}', 'config.json')
        with open(args_json, 'r') as f:
            data = json.load(f)
        data['rpc']['addr'] = f'0.0.0.0:{3030 + i}'
        data['network']['addr'] = f'0.0.0.0:{24567 + i}'
        data['archive'] = True
        with open(args_json, 'w') as f:
            json.dump(data, f, indent=2)

    # Load public key from first node
    with open(join(args.home, f'node0', 'node_key.json'), 'r') as f:
        data = json.load(f)
        pk = data['public_key']

    # Recreate log folder
    LOGS_FOLDER = expanduser("~/.nearup/localnet-logs")
    rmtree(LOGS_FOLDER, ignore_errors=True)
    mkdir(LOGS_FOLDER)

    # Spawn network
    if args.docker_image:
        for i in range(0, args.num_nodes):
            run_docker(args.docker_image, join(args.home, f'node{i}'), boot_nodes=f'{pk}@127.0.0.1:24567' if i > 0 else None,
                       verbose=args.verbose, container_name=f'nearcore{i}', host_network=True)
    else:
        pid_fd = open(NODE_PID, 'w')
        for i in range(0, args.num_nodes):
            proc = run_binary(args.binary_path, join(args.home, f'node{i}'), 'run', verbose=args.verbose,
                              boot_nodes=f'{pk}@127.0.0.1:24567' if i > 0 else None, output=join(LOGS_FOLDER, f'node{i}'))
            proc_name = proc_name_from_pid(proc.pid)
            print(proc.pid, "|", proc_name, "|", 'localnet', file=pid_fd)
        pid_fd.close()

    print("Local network was spawned successfully.")
    if args.docker_image:
        print(
            f"Check logs at: 'docker logs -f nearcore<i>', i is {','.join(list(map(str, range(4))))}")
    else:
        print(f"Check logs at: {LOGS_FOLDER}")
    print("Check network status at http://127.0.0.1:3030/status")


def entry():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--docker-image', help='docker image to run localnet with docker, if specified will run docker instead of binary')
    group.add_argument(
        '--binary-path', help="near binary path, set to nearcore/target/debug or nearcore/target/release to use locally compiled binary")
    parser.add_argument('--home', default=expanduser('~/.near/localnet'),
                        help='Home path for storing configs, keys and chain data (Default: ~/.near/localnet)')
    parser.add_argument(
        '--num-nodes', help="Number of nodes", default=4, type=int)
    parser.add_argument(
        '--num-shards', help="Number of shards", default=1, type=int)
    parser.add_argument('--overwrite', default=False, action='store_true',
                        help="Overwrite previous node data if exists.")
    parser.add_argument('--verbose', help="Show debug from selected target.")

    args = parser.parse_args(sys.argv[2:])

    if args.binary_path:
        args.binary_path = join(args.binary_path, 'neard')

    check_exist_neard()

    run(args)
