import argparse
import configparser
import json
import logging
import os
import sys

from shutil import rmtree
from subprocess import Popen, PIPE

from nearuplib.constants import NODE_PID_FILE, LOCALNET_LOGS_FOLDER
from nearuplib.nodelib import run_binary, proc_name_from_pid, check_exist_neard


def run(binary_path, home, num_nodes, num_shards, override, verbose):
    if override:
        if os.path.exists(home):
            logging.info("Removing old data.")
            rmtree(home)

    if not os.path.exists(home):
        run_binary(binary_path,
                   home,
                   'testnet',
                   shards=num_shards,
                   validators=num_nodes).wait()

    # Edit args files
    for i in range(0, num_nodes):
        args_json = os.path.join(home, f'node{i}', 'config.json')
        with open(args_json, 'r') as f:
            data = json.load(f)
        data['rpc']['addr'] = f'0.0.0.0:{3030 + i}'
        data['network']['addr'] = f'0.0.0.0:{24567 + i}'
        with open(args_json, 'w') as f:
            json.dump(data, f, indent=2)

    # Load public key from first node
    with open(os.path.join(home, f'node0', 'node_key.json'), 'r') as f:
        data = json.load(f)
        pk = data['public_key']

    # Recreate log folder
    rmtree(LOCALNET_LOGS_FOLDER, ignore_errors=True)
    os.mkdir(LOCALNET_LOGS_FOLDER)

    # Spawn network
    pid_fd = open(NODE_PID_FILE, 'w')
    for i in range(0, num_nodes):
        proc = run_binary(binary_path,
                          os.path.join(home, f'node{i}'),
                          'run',
                          verbose=verbose,
                          boot_nodes=f'{pk}@127.0.0.1:24567' if i > 0 else None,
                          output=os.path.join(LOCALNET_LOGS_FOLDER, f'node{i}'))
        proc_name = proc_name_from_pid(proc.pid)
        pid_fd.write(f"{proc.pid}|{proc_name}|localnet\n")
    pid_fd.close()

    logging.info("Localnet was spawned successfully...")
    logging.info(f"Localnet logs written in: {LOCALNET_LOGS_FOLDER}")
    logging.info("Check localnet status at http://127.0.0.1:3030/status")


def entry(binary_path, home, num_nodes, num_shards, override, verbose):
    if binary_path:
        binary_path = os.path.join(binary_path, 'neard')

    check_exist_neard()

    run(binary_path, home, num_nodes, num_shards, override, verbose)
