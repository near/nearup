import argparse
import configparser
import json
import logging
import sys

from os import mkdir
from os.path import exists, expanduser, join
from shutil import rmtree
from subprocess import Popen, PIPE

from nearuplib.constants import NODE_PID_FILE
from nearuplib.nodelib import run_binary, proc_name_from_pid, check_exist_neard


def run(binary_path, home, num_nodes, num_shards, override, verbose):
    if override:
        if exists(home):
            logging.info("Removing old data.")
            rmtree(home)

    if not exists(home):
        run_binary(binary_path,
                   home,
                   'testnet',
                   shards=num_shards,
                   validators=num_nodes).wait()

    # Edit args files
    for i in range(0, num_nodes):
        args_json = join(home, f'node{i}', 'config.json')
        with open(args_json, 'r') as f:
            data = json.load(f)
        data['rpc']['addr'] = f'0.0.0.0:{3030 + i}'
        data['network']['addr'] = f'0.0.0.0:{24567 + i}'
        data['archive'] = True
        with open(args_json, 'w') as f:
            json.dump(data, f, indent=2)

    # Load public key from first node
    with open(join(home, f'node0', 'node_key.json'), 'r') as f:
        data = json.load(f)
        pk = data['public_key']

    # Recreate log folder
    LOGS_FOLDER = expanduser("~/.nearup/localnet-logs")
    rmtree(LOGS_FOLDER, ignore_errors=True)
    mkdir(LOGS_FOLDER)

    # Spawn network
    pid_fd = open(NODE_PID_FILE, 'w')
    for i in range(0, num_nodes):
        proc = run_binary(binary_path,
                          join(home, f'node{i}'),
                          'run',
                          verbose=verbose,
                          boot_nodes=f'{pk}@127.0.0.1:24567' if i > 0 else None,
                          output=join(LOGS_FOLDER, f'node{i}'))
        proc_name = proc_name_from_pid(proc.pid)
        pid_fd.write(f"{proc.pid}|{proc_name}|localnet\n")
    pid_fd.close()

    print("Local network was spawned successfully.")
    print(f"Check logs at: {LOGS_FOLDER}")
    print("Check network status at http://127.0.0.1:3030/status")


def entry(binary_path, home, num_nodes, num_shards, override, verbose):
    if binary_path:
        binary_path = join(binary_path, 'neard')

    check_exist_neard()

    run(binary_path, home, num_nodes, num_shards, override, verbose)
