import click
import textwrap
import json
import logging
import os
import sys

from shutil import rmtree

from nearuplib.constants import NODE_PID_FILE, LOCALNET_FOLDER, LOCALNET_LOGS_FOLDER
from nearuplib.nodelib import run_binary, proc_name_from_pid, is_neard_running
from nearuplib.util import download_binaries, prompt_flag, prompt_bool_flag


def run(binary_path, home, num_nodes, num_shards, override, verbose=True, interactive=False):
    if os.path.exists(home):
        if interactive:
            override = prompt_bool_flag(
                'Would you like to remove data from the previous localnet run?',
                '--override',
                override)
        if override:
            logging.info("Removing old data.")
            rmtree(home)
    elif interactive:
        print(textwrap.fill(textwrap.dedent("""\
        Starting localnet NEAR nodes. This is a
        testnet entirely local to this machine.  Validators and
        non-validating nodes will be started, and will communicate
        with each other on localhost, producing blocks on top
        of a genesis block generated locally.
        """)))
        print('')

    if not os.path.exists(home):
        num_nodes = prompt_flag(
            'How many validator nodes would you like to initialize this localnet with?',
            '--num-nodes',
            num_nodes,
            4,
            interactive,
            type=int,
        )
        num_shards = prompt_flag(
            'How many shards would you like to initialize this localnet with?'
            '\nSee https://near.org/papers/nightshade/#sharding-basics',
            '--num-shards',
            num_shards,
            1,
            interactive,
            type=int,
        )
        run_binary(binary_path,
                   home,
                   'testnet',
                   shards=num_shards,
                   validators=num_nodes,
                   print_command=interactive).wait()

    i = 0
    # Edit args files
    while True:
        args_json = os.path.join(home, f'node{i}', 'config.json')

        if not os.path.exists(args_json):
            break

        with open(args_json, 'r') as config_file:
            data = json.load(config_file)
        data['rpc']['addr'] = f'0.0.0.0:{3030 + i}'
        data['network']['addr'] = f'0.0.0.0:{24567 + i}'

        with open(args_json, 'w') as config_file:
            json.dump(data, config_file, indent=2)
        i += 1
    num_nodes = i

    # Load public key from first node
    with open(os.path.join(home, 'node0', 'node_key.json'),
              'r') as node_key_file:
        data = json.load(node_key_file)
        public_key = data['public_key']

    # Recreate log folder
    rmtree(LOCALNET_LOGS_FOLDER, ignore_errors=True)
    os.mkdir(LOCALNET_LOGS_FOLDER)

    # Spawn network
    with open(NODE_PID_FILE, 'w') as pid_fd:
        for i in range(0, num_nodes):
            proc = run_binary(
                binary_path,
                os.path.join(home, f'node{i}'),
                'run',
                verbose=verbose,
                boot_nodes=f'{public_key}@127.0.0.1:24567' if i > 0 else None,
                output=os.path.join(LOCALNET_LOGS_FOLDER, f'node{i}'),
                print_command=interactive)
            proc_name = proc_name_from_pid(proc.pid)
            pid_fd.write(f"{proc.pid}|{proc_name}|localnet\n")

    logging.info("Localnet was spawned successfully...")
    logging.info(f"Localnet logs written in: {LOCALNET_LOGS_FOLDER}")
    logging.info("Check localnet status at http://127.0.0.1:3030/status")


def entry(binary_path, home, num_nodes, num_shards, override, verbose, interactive):
    if binary_path:
        binary_path = os.path.join(binary_path, 'neard')
    else:
        uname = os.uname()[0]
        binary_path = os.path.join(LOCALNET_FOLDER, "neard")
        if not os.path.exists(LOCALNET_FOLDER):
            os.makedirs(LOCALNET_FOLDER)
        download_binaries('localnet', uname)

    if is_neard_running():
        sys.exit(1)

    run(binary_path, home, num_nodes, num_shards, override, verbose, interactive)
