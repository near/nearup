import hashlib
import json
import logging
import os
import site
import shutil
import subprocess
import sys
import textwrap

import click

import psutil

from nearuplib.constants import DEFAULT_WAIT_TIMEOUT, LOGS_FOLDER, NODE_PID_FILE
from nearuplib.util import (
    download_binaries,
    download_config,
    download_genesis,
    latest_genesis_md5sum,
    new_release_ready,
    prompt_flag,
)
from nearuplib.watcher import is_watcher_running, run_watcher, stop_watcher
from nearuplib.tailer import next_logname


def read_validator_key(home_dir):
    key_path = os.path.join(home_dir, 'validator_key.json')
    try:
        with open(key_path) as key_file:
            return json.load(key_file)
    except FileNotFoundError:
        return None


def print_validator_info(home_dir):
    key_data = read_validator_key(home_dir)
    if key_data is None:
        logging.warning('Validator key not generated by neard as expected')
        return

    print(f"The validator's public key is {key_data['public_key']}")
    print(textwrap.fill(textwrap.dedent("""\
    The node will now run and will sync with the network, but this
    will not automatically initiate staking. In order to do that,
    you need to send a transaction to the network indicating your
    intent to stake. Please see
    https://docs.near.org/docs/develop/node/validator/staking-and-delegation.

    If you have near-cli (https://github.com/near/near-cli) installed, you
    can do this with the following command:
    """), width=80, break_on_hyphens=False, break_long_words=False))
    print(f'"near stake {key_data["account_id"]} '
          f'{key_data["public_key"]} <amount>"')

def init_near(home_dir, binary_path, chain_id, account_id, interactive=False):
    logging.info("Initializing the node configuration using near binary...")

    if interactive and account_id is None and click.confirm(textwrap.fill(textwrap.dedent("""\
    Would you like to initialize the NEAR node as a validator? If so,
    this will generate an extra key pair you\'ll be able to use to
    stake NEAR as a validator, which is distinct from the keys you'd
    use in normal transactions.
    """))):
        # TODO: check that the account exists and warn if not
        account_id = prompt_flag(
            textwrap.fill(textwrap.dedent("""\
            Enter an account ID. This should be an existing account
            you\'d like to use to stake NEAR as a validator. If you
            don\'t already have an account, please see
            https://docs.near.org/docs/develop/basics/create-account"""),
                          width=80, break_on_hyphens=False, break_long_words=False),
            account_id,
            default=None,
            interactive=interactive,
            type=str)
    cmd = [f'{binary_path}/neard', f'--home={home_dir}', 'init', f'--chain-id={chain_id}']
    if account_id:
        cmd.append(f'--account-id={account_id}')
    if chain_id in ['betanet', 'testnet']:
        cmd.append('--download-genesis')

    if interactive:
        print(f'Running "{" ".join(cmd)}"')
    subprocess.check_call(cmd)

    if interactive:
        print_validator_info(home_dir)


def genesis_changed(chain_id, home_dir):
    genesis_md5sum = latest_genesis_md5sum(chain_id)

    with open(os.path.join(os.path.join(home_dir, 'genesis.json')),
              'rb') as genesis_fd:
        local_genesis_md5sum = hashlib.md5(genesis_fd.read()).hexdigest()

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


def check_and_setup(binary_path, home_dir, chain_id, account_id, interactive=False):
    """Checks if there is already everything setup on this machine, otherwise sets up NEAR node."""
    if os.path.exists(os.path.join(home_dir)):
        if chain_id != 'localnet':
            with open(os.path.join(home_dir, 'genesis.json')) as genesis_fd:
                genesis_config = json.loads(genesis_fd.read())
                if genesis_config['chain_id'] != chain_id:
                    logging.error(
                        f"{home_dir} has wrong network configuration in genesis."
                        f"Specify different --home or specify the correct genesis.",
                    )
                    sys.exit(1)

        if chain_id in ['guildnet', 'betanet', 'testnet']:
            check_and_update_genesis(chain_id, home_dir)
        elif chain_id == 'mainnet':
            logging.info("Using the mainnet genesis...")
        else:
            logging.info("Using existing node configuration from %s for %s",
                         home_dir, chain_id)
        return

    logging.info("Setting up network configuration.")
    init_near(home_dir, binary_path, chain_id, account_id, interactive)
    download_config(chain_id, home_dir)

    if chain_id not in ['mainnet', 'guildnet', 'betanet', 'testnet']:
        with open(os.path.join(home_dir, 'genesis.json'), 'r+') as genesis_fd:
            genesis_config = json.load(genesis_fd)
            genesis_config['gas_price'] = 0
            genesis_config['min_gas_price'] = 0
            json.dump(genesis_config, genesis_fd)


def print_staking_key(home_dir):
    key_data = read_validator_key(home_dir)
    if key_data is None:
        return

    if not key_data['account_id']:
        logging.warning(
            "Node is not staking. Re-run init to specify staking account.")
        return
    logging.info("Stake for user '%s' with '%s'", key_data['account_id'],
                 key_data['public_key'])


def run_binary(path,
               home,
               action,
               neard_log=None,
               verbose=False,
               shards=None,
               validators=None,
               non_validators=None,
               boot_nodes=None,
               output=None,
               print_command=False):
    command = [path, '--home', str(home)]

    env = os.environ.copy()
    env['RUST_BACKTRACE'] = '1'

    # Note, we need to make these options mutually exclusive
    # for backwards capability reasons, until v1.0.0
    if verbose:
        env['RUST_LOG'] = 'debug,actix_web=info'
    elif neard_log:
        env['RUST_LOG'] = neard_log

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
        logname = f'{output}.log'
        if logname != next_logname(logname):
            shutil.move(logname, next_logname(logname))
        output = open(logname, 'w')

    if print_command:
        print(f'Running "{" ".join(command)}"')
    neard = subprocess.Popen(command, stderr=output, stdout=output, env=env)
    return neard


def proc_name_from_pid(pid):
    process = psutil.Process(pid)
    return process.name()


def is_neard_running():
    if os.path.exists(NODE_PID_FILE):
        logging.error("There is already binary nodes running.")
        logging.error("Either run nearup stop or by kill the process manually.")
        logging.warning(f"If this is a mistake, remove {NODE_PID_FILE}")
        return True
    return False


def run(home_dir,
        binary_path,
        boot_nodes,
        neard_log,
        verbose,
        chain_id,
        print_command=False,
        watch=False):
    proc = run_binary(os.path.join(binary_path, 'neard'),
                      home_dir,
                      'run',
                      neard_log=neard_log,
                      verbose=verbose,
                      boot_nodes=boot_nodes,
                      output=os.path.join(LOGS_FOLDER, chain_id),
                      print_command=print_command)
    proc_name = proc_name_from_pid(proc.pid)

    with open(NODE_PID_FILE, 'w') as pid_fd:
        pid_fd.write(f"{proc.pid}|{proc_name}|{chain_id}")
        pid_fd.close()

    logging.info("Node is running...")
    logging.info("To check logs call: `nearup logs` or `nearup logs --follow`")

    if watch:
        logging.info("Watcher is enabled. Starting watcher...")
        run_watcher(chain_id, home=home_dir)


def setup_and_run(binary_path,
                  home_dir,
                  boot_nodes,
                  chain_id,
                  account_id=None,
                  verbose=False,
                  interactive=False,
                  neard_log='',
                  watcher=True):
    if is_neard_running():
        sys.exit(1)

    if watcher and is_watcher_running():
        sys.exit(1)

    if binary_path == '':
        logging.info('Using officially compiled binary')
        uname = os.uname()[0]
        if uname not in ['Darwin', 'Linux']:
            logging.error(
                'Sorry your Operating System does not have officially compiled binary now.'
            )
            logging.error(
                'Compile a local binary and set --binary-path when running')
            sys.exit(1)

        binary_path = os.path.expanduser(f'~/.nearup/near/{chain_id}')
        if not os.path.exists(binary_path):
            os.makedirs(binary_path)

        download_binaries(chain_id, uname, chain_id == 'betanet')
    else:
        logging.info(f'Using local binary at {binary_path}')
        watcher = False  # ensure watcher doesn't run and try to download official binaries

    check_and_setup(binary_path, home_dir, chain_id, account_id, interactive)

    print_staking_key(home_dir)
    run(home_dir,
        binary_path,
        boot_nodes,
        neard_log,
        verbose,
        chain_id,
        watch=watcher,
        print_command=interactive)


def stop_nearup(keep_watcher=False):
    logging.warning("Stopping the near daemon...")
    stop_native()

    if not keep_watcher:
        logging.warning("Stopping the nearup watcher...")
        stop_watcher()
    else:
        logging.warning("Skipping the stopping of the nearup watcher...")


def restart_nearup(net,
                   path=os.path.join(site.USER_BASE, 'bin/nearup'),
                   home_dir='',
                   keep_watcher=True,
                   verbose=False):
    logging.warning("Restarting nearup...")

    if not os.path.exists(path):
        logging.error(
            "Please delete current nearup and install the new with `pip3 install --user nearup`"
        )
        logging.error(
            "For local development use: `pip3 install --user .` from root directory"
        )
        sys.exit(1)

    uname = os.uname()[0]
    if not new_release_ready(net, uname):
        logging.warning(
            f'Latest release for {net} is not ready. Skipping restart.')
        return

    logging.warning("Stopping nearup...")
    stop_nearup(keep_watcher=keep_watcher)

    logging.warning("Starting nearup...")
    setup_and_run(binary_path='',
                  home_dir=home_dir,
                  chain_id=net,
                  boot_nodes='',
                  verbose=verbose,
                  watcher=not keep_watcher)

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
                        try:
                            process.terminate()
                            process.wait(timeout=timeout)
                        except psutil.TimeoutExpired:
                            logging.warning(
                                f"Timeout expired. Killing process {pid}")
                            process.kill()

            os.remove(NODE_PID_FILE)
        else:
            logging.info("Near deamon is not running...")
    except Exception as ex:
        logging.error(f"There was an error while stopping watcher: {ex}")
        if os.path.exists(NODE_PID_FILE):
            os.remove(NODE_PID_FILE)
