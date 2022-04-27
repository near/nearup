import json
import logging
import os
import pathlib
import shutil
import sys

from nearuplib.constants import NODE_PID_FILE, LOCALNET_FOLDER, LOCALNET_LOGS_FOLDER
from nearuplib.nodelib import run_binary, proc_name_from_pid, is_neard_running
from nearuplib import util


def run(binary_path,
        home,
        num_nodes,
        num_shards,
        override,
        verbose=True,
        interactive=False):
    home = pathlib.Path(home)

    if home.exists():
        if util.prompt_bool_flag(
                'Would you like to remove data from the previous localnet run?',
                override,
                interactive=interactive):
            logging.info("Removing old data.")
            shutil.rmtree(home)
    elif interactive:
        print(
            util.wraptext('''
            Starting localnet NEAR nodes.  This is a test network entirely local
            to this machine.  Validators and non-validating nodes will be
            started, and will communicate with each other on localhost,
            producing blocks on top of a genesis block generated locally.
        '''))
        print()

    if not home.exists():
        num_nodes = util.prompt_flag(
            'How many validator nodes would you like to initialize this localnet with?',
            num_nodes,
            default=4,
            interactive=interactive,
            type=int,
        )
        num_shards = util.prompt_flag(
            'How many shards would you like to initialize this localnet with?'
            '\nSee https://near.org/papers/nightshade/#sharding-basics',
            num_shards,
            default=1,
            interactive=interactive,
            type=int,
        )
        fixed_shards = False
        if num_shards > 1:
            fixed_shards = util.prompt_bool_flag(
                'Would you like to setup fixed accounts per each shard (shard0, shard1)?',
                False,
                interactive=interactive,
            )
        archival_nodes = util.prompt_bool_flag(
            "Should these nodes be archival nodes (keep full history)?",
            False,
            interactive=interactive)

        run_binary(binary_path,
                   home,
                   'localnet',
                   shards=num_shards,
                   validators=num_nodes,
                   fixed_shards=fixed_shards,
                   archival_nodes=archival_nodes,
                   print_command=interactive).wait()

    # Edit args files
    num_nodes = 0
    while True:
        path = home / f'node{num_nodes}' / 'config.json'
        if not path.exists():
            break

        data = json.loads(path.read_text())
        data['rpc']['addr'] = f'0.0.0.0:{3030 + num_nodes}'
        data['network']['addr'] = f'0.0.0.0:{24567 + num_nodes}'
        path.write_text(json.dumps(data, indent=2))
        num_nodes += 1

    # Load public key from first node
    data = json.loads((home / 'node0' / 'node_key.json').read_text())
    public_key = data['public_key']

    # Recreate log folder
    shutil.rmtree(LOCALNET_LOGS_FOLDER, ignore_errors=True)
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
            pid_fd.write(f'{proc.pid}|{proc_name}|localnet\n')

    logging.info('Localnet was spawned successfully...')
    logging.info(f'Localnet logs written in: {LOCALNET_LOGS_FOLDER}')
    logging.info('Check localnet status at http://127.0.0.1:3030/status')


def entry(binary_path, home, num_nodes, num_shards, override, verbose,
          interactive):
    if binary_path:
        binary_path = os.path.join(binary_path, 'neard')
    else:
        uname = os.uname()[0]
        binary_path = os.path.join(LOCALNET_FOLDER, 'neard')
        if not os.path.exists(LOCALNET_FOLDER):
            os.makedirs(LOCALNET_FOLDER)
        util.download_binaries('localnet', uname)

    if is_neard_running():
        sys.exit(1)

    run(binary_path, home, num_nodes, num_shards, override, verbose,
        interactive)
