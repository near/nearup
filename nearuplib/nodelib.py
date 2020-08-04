import json
import logging
import os
import subprocess
import sys
import shutil
import hashlib

from os import unlink, kill
from subprocess import Popen, PIPE
from signal import SIGTERM

from nearuplib.util import download_near_s3, download

USER = str(os.getuid()) + ':' + str(os.getgid())


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
        prompt = "Enter your account ID"
        if chain_id != '':
            prompt += " (leave empty if not going to be a validator): "
        else:
            prompt += ": "
        account_id = input(prompt)
        init_flags.append('--account-id=%s' % account_id)
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
    download_near_s3(f'nearcore-deploy/{net}/config.json',
                     os.path.join(home_dir, 'config.json'))


def download_genesis(net, home_dir):
    download_near_s3(f'nearcore-deploy/{net}/genesis.json',
                     os.path.join(home_dir, 'genesis.json'))


def latest_deployed_version(net):
    return download_near_s3(f'nearcore-deploy/{net}/latest_deploy').strip()


def latest_deployed_release(net):
    return download_near_s3(f'nearcore-deploy/{net}/latest_release').strip()


def binary_changed(net):
    latest_deploy_version = latest_deployed_version(net)
    if os.path.exists(os.path.expanduser(f'~/.nearup/near/{net}/version')):
        with open(os.path.expanduser(f'~/.nearup/near/{net}/version')) as f:
            version = f.read().strip()
            if version == latest_deploy_version:
                logging.info('Downloaded binary version is up to date')
                return False
    return latest_deploy_version


def download_binary(net, uname):
    commit = latest_deployed_version(net)
    branch = latest_deployed_release(net)

    if commit:
        logging.info(f'Downloading latest deployed version for {net}')
        download_near_s3(f'nearcore/{uname}/{branch}/{commit}/near',
                         os.path.expanduser(f'~/.nearup/near/{net}/near'))
        download_near_s3(
            f'nearcore/{uname}/{branch}/{commit}/keypair-generator',
            os.path.expanduser(f'~/.nearup/near/{net}/keypair-generator'))
        download_near_s3(
            f'nearcore/{uname}/{branch}/{commit}/genesis-csv-to-json',
            os.path.expanduser(f'~/.nearup/near/{net}/genesis-csv-to-json'))
        subprocess.check_output(
            ['chmod', '+x',
             os.path.expanduser(f'~/.nearup/near/{net}/near')])
        subprocess.check_output([
            'chmod', '+x',
            os.path.expanduser(f'~/.nearup/near/{net}/keypair-generator')
        ])
        subprocess.check_output([
            'chmod', '+x',
            os.path.expanduser(f'~/.nearup/near/{net}/genesis-csv-to-json')
        ])
        with open(os.path.expanduser(f'~/.nearup/near/{net}/version'),
                  'w') as f:
            f.write(commit)


def get_genesis_time(net):
    return download_near_s3(f'nearcore-deploy/{net}/genesis_time')


def get_genesis_protocol_version(net):
    return int(
        download_near_s3(f'nearcore-deploy/{net}/protocol_version').strip())


def get_genesis_md5sum(net):
    return download_near_s3(f'nearcore-deploy/{net}/genesis_md5sum').strip()


def get_latest_deploy_at(net):
    return download_near_s3(f'nearcore-deploy/{net}/latest_deploy_at').strip()


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


NODE_PID = os.path.expanduser('~/.nearup/node.pid')


def run_binary(path,
               home,
               action,
               *,
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
    watch_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'watcher.py'))
    LOGS_FOLDER = os.path.expanduser('~/.nearup/logs')
    subprocess.check_output(['mkdir', '-p', LOGS_FOLDER])
    watch_log = open(os.path.expanduser('~/.nearup/logs/watcher.log'), 'w')

    logging.info("Starting the nearup watcher...")
    p = Popen(['python3', watch_script, watch['net'], watch['home']],
              stdout=watch_log,
              stderr=watch_log)

    with open(os.path.expanduser('~/.nearup/watcher.pid'), 'w') as f:
        f.write(str(p.pid))


def proc_name_from_pid(pid):
    proc = Popen(["ps", "-p", str(pid), "-o", "command="], stdout=PIPE)

    if proc.wait() != 0:
        # No process with this pid
        return ""
    else:
        return proc.stdout.read().decode().strip()


def check_exist_neard():
    if os.path.exists(NODE_PID):
        logging.warn("There is already binary nodes running. Stop it using:")
        logging.warn("nearup stop")
        logging.warn(f"If this is a mistake, remove {NODE_PID}")
        exit(1)


def run(home_dir, binary_path, boot_nodes, verbose, chain_id, watch=False):
    os.environ['RUST_BACKTRACE'] = '1'
    pid_fd = open(NODE_PID, 'w')
    # convert verbose = True to --verbose '' command line argument
    if verbose:
        verbose = ''
    else:
        verbose = None
    LOGS_FOLDER = os.path.expanduser('~/.nearup/logs')
    subprocess.check_output(['mkdir', '-p', LOGS_FOLDER])
    proc = run_binary(os.path.join(binary_path, 'near'),
                      home_dir,
                      'run',
                      verbose=verbose,
                      boot_nodes=boot_nodes,
                      output=os.path.join(LOGS_FOLDER, chain_id),
                      watch=watch)
    proc_name = proc_name_from_pid(proc.pid)
    pid_fd.close()
    logging.info(
        "Node is running! \nTo check logs call: `nearup logs` or `nearup logs --follow`"
    )


def show_logs(follow, number_lines):
    LOGS_FOLDER = os.path.expanduser('~/.nearup/logs')
    if not os.path.exists(NODE_PID):
        logging.info('Node is not running')
        exit(1)

    pid_info = open(NODE_PID).read()
    print(pid_info)
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
        proc = subprocess.Popen(command, start_new_session=True)
        proc.wait()
    except KeyboardInterrupt:
        proc.kill()
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
        download_binary(chain_id, uname)
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
    if os.path.exists(NODE_PID):
        with open(NODE_PID) as f:
            for line in f.readlines():
                pid, proc_name, _ = map(str.strip, line.strip(' \n').split("|"))
                pid = int(pid)
                if proc_name in proc_name_from_pid(pid):
                    logging.info(f"Stopping process {proc_name} with pid", pid)
                    kill(pid, SIGTERM)
                    # Ensure the pid is killed, not just SIGTERM signal sent
                    while True:
                        try:
                            os.kill(pid, 0)
                        except OSError:
                            break

        unlink(NODE_PID)


def stop_watcher():
    try:
        with open(os.path.expanduser(f'~/.nearup/watcher.pid')) as f:
            pid = int(f.read())
        kill(pid, SIGTERM)
        logging.info(f'Stopping near watcher with pid {pid}')
        os.remove(os.path.expanduser(f'~/.nearup/watcher.pid'))
    except OSError:
        pass
    except FileNotFoundError:
        pass
    else:
        while True:
            try:
                os.kill(pid, 0)
            except OSError:
                break


def generate_node_key(home, binary_path):
    cmd = [f'{binary_path}/keypair-generator']
    cmd.extend(['--home', home])
    cmd.extend(['--generate-config'])
    cmd.extend(['node-key'])
    try:
        subprocess.call(cmd)
    except KeyboardInterrupt:
        logging.warn("\nStopping NEARCore.")
    logging.info("Node key generated")


def generate_validator_key(home, binary_path, account_id):
    logging.info("Generating validator key...")
    cmd = [f'{binary_path}/keypair-generator']
    cmd.extend(['--home', home])
    cmd.extend(['--generate-config'])
    cmd.extend(['--account-id', account_id])
    cmd.extend(['validator-key'])
    try:
        subprocess.call(cmd)
    except KeyboardInterrupt:
        logging.warn("\nStopping NEARCore.")
    logging.info("Validator key generated")


def generate_signer_key(home, binary_path, account_id):
    logging.info("Generating signer keys...")
    cmd = [f'{binary_path}/keypair-generator']
    cmd.extend(['--home', home])
    cmd.extend(['--generate-config'])
    cmd.extend(['--account-id', account_id])
    cmd.extend(['signer-keys'])
    try:
        subprocess.call(cmd)
    except KeyboardInterrupt:
        logging.warn("\nStopping NEARCore.")
    logging.info("Signer keys generated")


def initialize_keys(home, binary_path, account_id, generate_signer_keys):
    if generate_signer_keys:
        logging.info("Generating the signer keys...")
        generate_signer_key(home, binary_path, account_id)

    logging.info("Generating the node keys...")
    generate_node_key(home, binary_path)

    if account_id:
        logging.info("Generating the validator keys...")
        generate_validator_key(home, binary_path, account_id)


def create_genesis(home, binary_path, chain_id, tracked_shards):
    if os.path.exists(os.path.join(home, 'genesis.json')):
        logging.warn("Genesis already exists")
        return
    logging.info("Creating genesis...")
    if not os.path.exists(os.path.join(home, 'accounts.csv')):
        raise Exception(
            "Failed to generate genesis: accounts.csv does not exist")

    cmd = [f'{binary_path}/genesis-csv-to-json']
    cmd.extend(['--home', home])
    cmd.extend(['--chain-id', chain_id])
    if len(tracked_shards) > 0:
        cmd.extend(['--tracked-shards', tracked_shards])
    try:
        subprocess.call(cmd)
    except KeyboardInterrupt:
        logging.warn("\nStopping NEARCore.")
    logging.info("Genesis created")
