import hashlib
import json
import logging
import os
import shutil
import stat
import subprocess

import psutil
from subprocess import Popen, PIPE

from nearuplib.constants import LOGS_FOLDER, NODE_PID_FILE, WATCHER_PID_FILE
from nearuplib.util import download_from_s3, read_from_s3, initialize_keys


def init(home_dir, binary_path, init_flags):
    logging.info("Initializing the node configuration using near binary...")
    target = f'{binary_path}/near'
    subprocess.call([target, '--home=%s' % home_dir, 'init'] + init_flags)


def init_official(chain_id, binary_path, home_dir, account_id):
    logging.info("Initializing the keys...")
    initialize_keys(home_dir, binary_path, '', account_id)

    logging.info("Downloading the genesis file...")
    download_genesis(chain_id, home_dir)

    logging.info("Downloading the config file...")
    download_config(chain_id, home_dir)


def get_chain_id_from_flags(flags):
    """Retrieve requested chain id from the flags."""
    chain_id_flags = [flag for flag in flags if flag.startswith('--chain-id=')]
    if len(chain_id_flags) == 1:
        return chain_id_flags[0][len('--chain-id='):]
    return ''


def genesis_changed(chain_id, home_dir):
    genesis_md5sum = get_genesis_md5sum(chain_id)
    local_genesis_md5sum = hashlib.md5(
        open(os.path.join(os.path.join(home_dir, 'genesis.json')),
             'rb').read()).hexdigest()
    if genesis_md5sum == local_genesis_md5sum:
        logging.info(f'Our genesis version is up to date')
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


def check_and_setup(binary_path, home_dir, init_flags, no_gas_price=False):
    """Checks if there is already everything setup on this machine, otherwise sets up NEAR node."""
    chain_id = get_chain_id_from_flags(init_flags)
    if os.path.exists(os.path.join(home_dir)):
        missing = []
        for file in ['node_key.json', 'config.json', 'genesis.json']:
            if not os.path.exists(os.path.join(home_dir, file)):
                missing.append(file)
        if missing:
            logging.error(
                f'Missing files {", ".join(missing)} in {home_dir}. Maybe last init was failed. either specify different --home or remove {home_dir} to start from scratch.',
            )
            exit(1)

        genesis_config = json.loads(
            open(os.path.join(os.path.join(home_dir, 'genesis.json'))).read())
        if genesis_config['chain_id'] != chain_id:
            logging.error(
                f"Folder {home_dir} already has network configuration for {genesis_config['chain_id']}\n"
                f"You want to run {chain_id}, either specify different --home or remove {home_dir} to start from scratch.",
            )
            exit(1)

        if chain_id in ['betanet', 'testnet']:
            check_and_update_genesis(chain_id, home_dir)
        else:
            logging.info(f'Start {chain_id}')
            logging.info("Using existing node configuration from %s for %s" %
                         (home_dir, genesis_config['chain_id']))
        return

    logging.info("Setting up network configuration.")
    account_id = [x for x in init_flags if x.startswith('--account-id')]
    if not account_id:
        logging.warn(
            "If you want to be a validator please specify the --account-id flag with the validator id."
        )
        account_id = ""
    else:
        account_id = account_id[0].split('=')[-1]

    if chain_id in ['betanet', 'testnet']:
        init_official(chain_id, binary_path, home_dir, account_id)
    else:
        init(home_dir, binary_path, init_flags)

    if chain_id not in ['betanet', 'testnet'] and no_gas_price:
        filename = os.path.join(home_dir, 'genesis.json')
        genesis_config = json.load(open(filename))
        genesis_config['gas_price'] = 0
        genesis_config['min_gas_price'] = 0
        json.dump(genesis_config, open(filename, 'w'))
    elif no_gas_price:
        logging.info(
            f'no_gas_price is only for local development network, ignoring for {chain_id}'
        )


def download_config(net, home_dir):
    download_from_s3(f'nearcore-deploy/{net}/config.json',
                     os.path.join(home_dir, 'config.json'))


def download_genesis(net, home_dir):
    download_from_s3(f'nearcore-deploy/{net}/genesis.json',
                     os.path.join(home_dir, 'genesis.json'))


def latest_deployed_version(net):
    return read_from_s3(f'nearcore-deploy/{net}/latest_deploy').strip()


def latest_deployed_release(net):
    return read_from_s3(f'nearcore-deploy/{net}/latest_release').strip()


def binary_changed(net):
    latest_deploy_version = latest_deployed_version(net)
    if os.path.exists(os.path.expanduser(f'~/.nearup/near/{net}/version')):
        with open(os.path.expanduser(f'~/.nearup/near/{net}/version')) as f:
            version = f.read().strip()
            if version == latest_deploy_version:
                logging.info('Downloaded binary version is up to date')
                return False
    return latest_deploy_version


def download_binaries(net, uname):
    commit = latest_deployed_version(net)
    branch = latest_deployed_release(net)

    if commit:
        logging.info(f'Downloading latest deployed version for {net}')

        binaries = ['near', 'keypair-generator', 'genesis-csv-to-json']
        for binary in binaries:
            download_url = f'nearcore/{uname}/{branch}/{commit}/{binary}'
            download_path = os.path.expanduser(f'~/.nearup/near/{net}/{binary}')

            logging.info(
                f"Downloading {binary} to {download_path} from {download_url}..."
            )
            download_from_s3(download_url, download_path)
            logging.info(f"Downloaded {binary} to {download_path}...")

            logging.info(f"Making the {binary} executable...")
            status = os.stat(download_path)
            os.chmod(download_path, status.st_mode | stat.S_IEXEC)

        with open(os.path.expanduser(f'~/.nearup/near/{net}/version'),
                  'w') as f:
            f.write(commit)


def get_genesis_time(net):
    return read_from_s3(f'nearcore-deploy/{net}/genesis_time')


def get_genesis_protocol_version(net):
    return int(read_from_s3(f'nearcore-deploy/{net}/protocol_version').strip())


def get_genesis_md5sum(net):
    return read_from_s3(f'nearcore-deploy/{net}/genesis_md5sum').strip()


def get_latest_deploy_at(net):
    return read_from_s3(f'nearcore-deploy/{net}/latest_deploy_at').strip()


def print_staking_key(home_dir):
    key_path = os.path.join(home_dir, 'validator_key.json')
    if not os.path.exists(key_path):
        return

    key_file = json.loads(open(key_path).read())
    if not key_file['account_id']:
        logging.warn(
            "Node is not staking. Re-run init to specify staking account.")
        return
    logging.info("Stake for user '%s' with '%s'" %
                 (key_file['account_id'], key_file['public_key']))


def get_port(home_dir, net):
    """Checks the ports saved in config.json"""
    config = json.load(open(os.path.join(home_dir, 'config.json')))
    p = config[net]['addr'][config[net]['addr'].find(':') + 1:]
    return p + ":" + p


def run_binary(path,
               home,
               action,
               verbose=None,
               shards=None,
               validators=None,
               non_validators=None,
               boot_nodes=None,
               output=None,
               watch=False):
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
        output = open(f'{output}.log', 'w')

    near = Popen(command, stderr=output, stdout=output)
    if watch:
        run_watcher(watch)
    return near


def run_watcher(watch):
    logging.info("Starting the nearup watcher...")
    path = os.path.expanduser('~/.local/bin/watcher.py')

    if not os.path.exists(path):
        logging.error(
            "Please delete current nearup and install the new with `pip3 install --user nearup`"
        )
        logging.error(
            "If you are using nearup for local development use: `pip3 install .` from root directory"
        )
        exit(1)

    p = Popen(['python3', path, watch['net'], watch['home']])

    with open(WATCHER_PID_FILE, 'w') as f:
        f.write(str(p.pid))


def proc_name_from_pid(pid):
    process = psutil.Process(pid)
    return process.name()


def check_exist_neard():
    if os.path.exists(NODE_PID_FILE):
        logging.warn("There is already binary nodes running. Stop it using:")
        logging.warn("nearup stop")
        logging.warn(f"If this is a mistake, remove {NODE_PID_FILE}")
        exit(1)


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
                      output=os.path.join(LOGS_FOLDER, chain_id),
                      watch=watch)
    proc_name = proc_name_from_pid(proc.pid)

    with open(NODE_PID_FILE, 'w') as pid_fd:
        pid_fd.write(f"{proc.pid}|{proc_name}|{chain_id}")
        pid_fd.close()

    logging.info("Node is running...")
    logging.info("To check logs call: `nearup logs` or `nearup logs --follow`")


def show_logs(follow, number_lines):
    if not os.path.exists(NODE_PID_FILE):
        logging.info('Node is not running')
        exit(1)

    pid_info = open(NODE_PID_FILE).read()
    if 'betanet' in pid_info:
        net = 'betanet'
    elif 'testnet' in pid_info:
        net = 'testnet'
    else:
        # TODO: localnet could have several logs, not showing them all but list log files here
        # Maybe better to support `nearup logs node0` usage.
        logging.info(
            f'You are running local net. Logs are in: ~/.nearup/localnet-logs/')
        exit(0)
    command = ['tail', '-n', str(number_lines)]
    if follow:
        command += ['-f']
    command += [os.path.expanduser(f'~/.nearup/logs/{net}.log')]
    try:
        subprocess.run(command, start_new_session=True)
    except KeyboardInterrupt:
        exit(0)


def check_binary_version(binary_path, chain_id):
    logging.info("Checking the current binary version...")
    latest_deploy_version = latest_deployed_version(chain_id)
    version = subprocess.check_output(
        [f'{binary_path}/near', '--version'],
        universal_newlines=True).split('(build ')[1].split(')')[0]
    if not latest_deploy_version.startswith(version):
        logging.warn(
            f'Current deployed version on {chain_id} is {latest_deploy_version}, but local binary is {version}. It might not work'
        )


def setup_and_run(binary_path,
                  home_dir,
                  init_flags,
                  boot_nodes,
                  verbose=False,
                  no_gas_price=False):
    check_exist_neard()
    chain_id = get_chain_id_from_flags(init_flags)

    if binary_path == '':
        logging.info(f'Using officially compiled binary')
        uname = os.uname()[0]
        if uname not in ['Linux', 'Darwin']:
            logging.error(
                'Sorry your Operating System does not have officially compiled binary now.\nPlease compile locally by `make debug` or `make release` in nearcore and set --binary-path'
            )
            exit(1)
        binary_path = os.path.expanduser(f'~/.nearup/near/{chain_id}')
        subprocess.check_output(['mkdir', '-p', binary_path])
        download_binaries(chain_id, uname)
        watch = {"net": chain_id, 'home': home_dir}
    else:
        logging.info(f'Using local binary at {binary_path}')
        check_binary_version(binary_path, chain_id)
        watch = False

    check_and_setup(binary_path, home_dir, init_flags, no_gas_price)

    print_staking_key(home_dir)

    run(home_dir, binary_path, boot_nodes, verbose, chain_id, watch=watch)


def stop_nearup(keep_watcher=False):
    logging.warn("Stopping the near daemon...")
    stop_native()

    if not keep_watcher:
        logging.warn("Stopping the nearup watcher...")
        stop_watcher()
    else:
        logging.warn("Skipping the stopping of the nearup watcher...")


def stop_native():
    try:
        if os.path.exists(NODE_PID_FILE):
            with open(NODE_PID_FILE) as f:
                for line in f.readlines():
                    pid, proc_name, _ = line.strip().split("|")
                    pid = int(pid)
                    process = psutil.Process(pid)
                    logging.info(
                        f"Near procces is {proc_name} with pid: {pid}...")
                    if proc_name in proc_name_from_pid(pid):
                        logging.info(
                            f"Stopping process {proc_name} with pid {pid}...")
                        process.kill()
            os.remove(NODE_PID_FILE)
        else:
            logging.info("Near deamon is not running...")
    except Exception as e:
        logging.error(f"There was an error while stopping watcher: {e}")


def stop_watcher():
    try:
        if os.path.exists(WATCHER_PID_FILE):
            with open(WATCHER_PID_FILE) as f:
                pid = int(f.read())
                process = psutil.Process(pid)
                logging.info(
                    f'Stopping near watcher {process.name()} with pid {pid}...')
                process.kill()
                os.remove(WATCHER_PID_FILE)
        else:
            logging.info("Nearup watcher is not running...")
    except Exception as e:
        logging.error(f"There was an error while stopping watcher: {e}")
