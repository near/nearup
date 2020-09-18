import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys

from subprocess import Popen

import psutil

from nearuplib.constants import DEFAULT_WAIT_TIMEOUT, LOGS_FOLDER, NODE_PID_FILE
from nearuplib.util import (
    download_binaries,
    download_config,
    download_genesis,
    latest_genesis_md5sum,
)
from nearuplib.watcher import run_watcher, stop_watcher


def init_near(home_dir, binary_path, chain_id, init_flags):
    logging.info("Initializing the node configuration using near binary...")

    cmd = [f'{binary_path}/near', f'--home={home_dir}', 'init'] + init_flags
    if chain_id in ['betanet', 'testnet']:
        # force download genesis
        cmd.append('--download-genesis')

    subprocess.call(cmd)


def init(home_dir, binary_path, chain_id, init_flags):
    # initialize near
    init_near(home_dir, binary_path, chain_id, init_flags)

    # download config.json for bootnodes, etc
    download_config(chain_id, home_dir)


def get_chain_id_from_flags(flags):
    """Retrieve requested chain id from the flags."""
    chain_id_flags = [flag for flag in flags if flag.startswith('--chain-id=')]
    if len(chain_id_flags) == 1:
        return chain_id_flags[0][len('--chain-id='):]
    return ''


def genesis_changed(chain_id, home_dir):
    genesis_md5sum = latest_genesis_md5sum(chain_id)
    local_genesis_md5sum = hashlib.md5(
        open(os.path.join(os.path.join(home_dir, 'genesis.json')),
             'rb').read()).hexdigest()
    if genesis_md5sum == local_genesis_md5sum:
        logging.info('The genesis version is up to date')
        return False

    logging.info(
        f'Remote genesis protocol version md5 {genesis_md5sum}, ours is {local_genesis_md5sum}'
    )
    return True


def check_and_update_genesis(chain_id, home_dir):
    if genesis_changed(chain_id, home_dir):
        logging.info(
            f'Update genesis config and remove stale data for {chain_id}')
        os.remove(os.path.join(home_dir, 'genesis.json'))
        download_genesis(chain_id, home_dir)
        if os.path.exists(os.path.join(home_dir, 'data')):
            shutil.rmtree(os.path.join(home_dir, 'data'))
        return True
    return False


def check_and_setup(binary_path, home_dir, init_flags):
    """Checks if there is already everything setup on this machine, otherwise sets up NEAR node."""
    chain_id = get_chain_id_from_flags(init_flags)
    if os.path.exists(os.path.join(home_dir)):
        missing = []
        for file in ['node_key.json', 'config.json', 'genesis.json']:
            if not os.path.exists(os.path.join(home_dir, file)):
                missing.append(file)
        if missing:
            logging.error(
                f'Missing files {", ".join(missing)} in {home_dir}. Maybe last init was failed.'
            )
            logging.error(
                'Either specify different --home or remove {home_dir} to start from scratch.'
            )
            sys.exit(1)

        genesis_config = json.loads(
            open(os.path.join(os.path.join(home_dir, 'genesis.json'))).read())
        if genesis_config['chain_id'] != chain_id:
            logging.error(
                f"Folder {home_dir} has network configuration for {genesis_config['chain_id']}"
                f"Either specify different --home or remove {home_dir} to start from scratch.",
            )
            sys.exit(1)

        if chain_id in ['betanet', 'testnet']:
            check_and_update_genesis(chain_id, home_dir)
        else:
            logging.info("Using existing node configuration from %s for %s",
                         home_dir, genesis_config['chain_id'])
        return

    logging.info("Setting up network configuration.")
    init(home_dir, binary_path, chain_id, init_flags)

    if chain_id not in ['betanet', 'testnet']:
        filename = os.path.join(home_dir, 'genesis.json')
        genesis_config = json.load(open(filename))
        genesis_config['gas_price'] = 0
        genesis_config['min_gas_price'] = 0
        json.dump(genesis_config, open(filename, 'w'))


def print_staking_key(home_dir):
    key_path = os.path.join(home_dir, 'validator_key.json')
    if not os.path.exists(key_path):
        return

    key_file = json.loads(open(key_path).read())
    if not key_file['account_id']:
        logging.warning(
            "Node is not staking. Re-run init to specify staking account.")
        return
    logging.info("Stake for user '%s' with '%s'", key_file['account_id'],
                 key_file['public_key'])


def run_binary(path,
               home,
               action,
               verbose=None,
               shards=None,
               validators=None,
               non_validators=None,
               boot_nodes=None,
               output=None):
    command = [path, '--home', home]

    if verbose or verbose == '':
        command.extend(['--verbose', verbose])

    command.append(action)

    if shards:
        command.extend(['--shards', str(shards)])
    if validators:
        command.extend(['--v', str(validators)])
    if non_validators:
        command.extend(['--n', str(non_validators)])
    if boot_nodes:
        command.extend(['--boot-nodes', boot_nodes])

    if output:
        output = open(f'{output}.log', 'a')

    near = Popen(command, stderr=output, stdout=output)
    return near


def proc_name_from_pid(pid):
    process = psutil.Process(pid)
    return process.name()


def check_exist_neard():
    if os.path.exists(NODE_PID_FILE):
        logging.warning(
            "There is already binary nodes running. Stop it using: nearup stop")
        logging.warning(f"If this is a mistake, remove {NODE_PID_FILE}")
        sys.exit(1)


def run(home_dir, binary_path, boot_nodes, verbose, chain_id, watch=False):
    os.environ['RUST_BACKTRACE'] = '1'
    # convert verbose = True to --verbose '' command line argument
    if verbose:
        verbose = ''
    else:
        verbose = None
    proc = run_binary(os.path.join(binary_path, 'near'),
                      home_dir,
                      'run',
                      verbose=verbose,
                      boot_nodes=boot_nodes,
                      output=os.path.join(LOGS_FOLDER, chain_id))
    proc_name = proc_name_from_pid(proc.pid)

    with open(NODE_PID_FILE, 'w') as pid_fd:
        pid_fd.write(f"{proc.pid}|{proc_name}|{chain_id}")
        pid_fd.close()

    logging.info("Node is running...")
    logging.info("To check logs call: `nearup logs` or `nearup logs --follow`")

    if watch:
        logging.info("Watcher is enabled. Starting watcher...")
        run_watcher(chain_id)


def setup_and_run(binary_path,
                  home_dir,
                  init_flags,
                  boot_nodes,
                  verbose=False,
                  no_watcher=False):
    check_exist_neard()
    chain_id = get_chain_id_from_flags(init_flags)
    watch = False

    if binary_path == '':
        logging.info('Using officially compiled binary')
        uname = os.uname()[0]
        if uname not in ['Linux']:
            logging.error(
                'Sorry your Operating System does not have officially compiled binary now.'
            )
            logging.error(
                'Compile a local binary and set --binary-path when running')
            sys.exit(1)
        binary_path = os.path.expanduser(f'~/.nearup/near/{chain_id}')

        if not os.path.exists(binary_path):
            os.makedirs(binary_path)

        download_binaries(chain_id, uname)
        watch = True
    else:
        logging.info(f'Using local binary at {binary_path}')

    check_and_setup(binary_path, home_dir, init_flags)

    print_staking_key(home_dir)

    if no_watcher:
        watch = False

    run(home_dir, binary_path, boot_nodes, verbose, chain_id, watch=watch)


def stop_nearup(keep_watcher=False):
    logging.warning("Stopping the near daemon...")
    stop_native()

    if not keep_watcher:
        logging.warning("Stopping the nearup watcher...")
        stop_watcher()
    else:
        logging.warning("Skipping the stopping of the nearup watcher...")


def restart_nearup(net,
                   path=os.path.expanduser('~/.local/bin/nearup'),
                   keep_watcher=True):
    logging.warning("Restarting nearup...")

    if not os.path.exists(path):
        logging.error(
            "Please delete current nearup and install the new with `pip3 install --user nearup`"
        )
        logging.error(
            "For local development use: `pip3 install --user .` from root directory"
        )
        sys.exit(1)

    logging.warning("Stopping nearup...")
    stop_nearup(keep_watcher=keep_watcher)

    logging.warning("Starting nearup...")
    setup_and_run(binary_path='',
                  home_dir='',
                  init_flags=[f'--chain-id={net}'],
                  boot_nodes='',
                  verbose=True,
                  no_watcher=keep_watcher)

    logging.info("Nearup has been restarted...")


def stop_native(timeout=DEFAULT_WAIT_TIMEOUT):
    try:
        if os.path.exists(NODE_PID_FILE):
            with open(NODE_PID_FILE) as pid_file:
                for line in pid_file.readlines():
                    pid, proc_name, _ = line.strip().split("|")
                    pid = int(pid)
                    process = psutil.Process(pid)
                    logging.info(
                        f"Near procces is {proc_name} with pid: {pid}...")
                    if proc_name in proc_name_from_pid(pid):
                        logging.info(
                            f"Stopping process {proc_name} with pid {pid}...")
                        process.terminate()
                        process.wait(timeout=timeout)
            os.remove(NODE_PID_FILE)
        else:
            logging.info("Near deamon is not running...")
    except Exception as ex:
        logging.error(f"There was an error while stopping watcher: {ex}")
        if os.path.exists(NODE_PID_FILE):
            os.remove(NODE_PID_FILE)
