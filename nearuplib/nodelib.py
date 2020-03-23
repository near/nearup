import json
import os
import subprocess
from nearuplib.util import download_near_s3
import sys
import shutil

USER = str(os.getuid())+':'+str(os.getgid())


def docker_init(image, home_dir, init_flags):
    """Inits the node configuration using docker."""
    subprocess.check_output(['mkdir', '-p', home_dir])
    subprocess.check_output(['docker', 'run', '-u', USER,
                             '-v', '%s:/srv/near' % home_dir,
                             '-v', os.path.abspath('near/res') + ':/near/res',
                             image, 'near', '--home=/srv/near', 'init'] + init_flags)


def docker_init_official(chain_id, image, home_dir, account_id):
    """Inits the node configuration using docker for devnet, betanet and testnet"""
    initialize_keys(home_dir, '', False, image,
                    account_id, False)
    download_genesis(chain_id, home_dir)
    download_config(chain_id, home_dir)


def nodocker_init(home_dir, binary_path, init_flags):
    """Inits the node configuration using near binary."""
    target = f'{binary_path}/near'
    subprocess.call([target,
                     '--home=%s' % home_dir, 'init'] + init_flags)


def nodocker_init_official(chain_id, binary_path, home_dir, account_id):
    """Inits the node configuration using near binary for devnet, betanet and testnet"""
    initialize_keys(home_dir, binary_path, True, '',
                    account_id, False)
    download_genesis(chain_id, home_dir)
    download_config(chain_id, home_dir)


def get_chain_id_from_flags(flags):
    """Retrieve requested chain id from the flags."""
    chain_id_flags = [flag for flag in flags if flag.startswith('--chain-id=')]
    if len(chain_id_flags) == 1:
        return chain_id_flags[0][len('--chain-id='):]
    return ''


def check_and_setup(nodocker, binary_path, image, home_dir, init_flags, no_gas_price=False):
    """Checks if there is already everything setup on this machine, otherwise sets up NEAR node."""
    chain_id = get_chain_id_from_flags(init_flags)
    if os.path.exists(os.path.join(home_dir)):
        missing = []
        for file in ['node_key.json', 'config.json', 'genesis.json']:
            if not os.path.exists(os.path.join(home_dir, file)):
                missing.append(file)
        if missing:
            print(
                f'Missing files {", ".join(missing)} in {home_dir}. Maybe last init was failed. either specify different --home or remove {home_dir} to start from scratch.', file=sys.stderr)
            exit(1)

        genesis_config = json.loads(
            open(os.path.join(os.path.join(home_dir, 'genesis.json'))).read())
        if genesis_config['chain_id'] != chain_id:
            print(f"Folder {home_dir} already has network configuration for {genesis_config['chain_id']}\n"
                  f"You want to run {chain_id}, either specify different --home or remove {home_dir} to start from scratch.", file=sys.stderr)
            exit(1)

        if chain_id == 'devnet':
            genesis_time = get_genesis_time(chain_id)
            if genesis_time == genesis_config['genesis_time']:
                print(f'Our genesis version up to date')
            else:
                print(
                    f'Remote genesis time {genesis_time}, ours is {genesis_config["genesis_time"]}')
                print(
                    f'Update genesis config and remove stale data for {chain_id}')
                os.remove(os.path.join(home_dir, 'genesis.json'))
                download_genesis('devnet', home_dir)
                if os.path.exists(os.path.join(home_dir, 'data')):
                    shutil.rmtree(os.path.join(home_dir, 'data'))
                print(f'Update devnet config for new boot nodes')
                os.remove(os.path.join(home_dir, 'config.json'))
                download_config('devnet', home_dir)
        elif chain_id in ['betanet', 'testnet']:
            protocol_version = get_genesis_protocol_version(chain_id)
            if protocol_version == genesis_config['protocol_version']:
                print(f'Our genesis version up to date')
            else:
                print(
                    f'Remote genesis protocol version {protocol_version}, ours is {genesis_config["protocol_version"]}')
                print(
                    f'Update genesis config and remove stale data for {chain_id}')
                os.remove(os.path.join(home_dir, 'genesis.json'))
                download_genesis(chain_id, home_dir)
                if os.path.exists(os.path.join(home_dir, 'data')):
                    shutil.rmtree(os.path.join(home_dir, 'data'))
        else:
            print(f'Start {chain_id}')
            print("Using existing node configuration from %s for %s" %
                  (home_dir, genesis_config['chain_id']))
        return

    print("Setting up network configuration.")
    if len([x for x in init_flags if x.startswith('--account-id')]) == 0:
        prompt = "Enter your account ID"
        if chain_id != '':
            prompt += " (leave empty if not going to be a validator): "
        else:
            prompt += ": "
        account_id = input(prompt)
        init_flags.append('--account-id=%s' % account_id)

    if nodocker:
        if chain_id in ['devnet', 'betanet', 'testnet']:
            nodocker_init_official(chain_id, binary_path, home_dir, account_id)
        else:
            nodocker_init(home_dir, binary_path, init_flags)
    else:
        if chain_id in ['devnet', 'betanet', 'testnet']:
            docker_init_official(chain_id, image, home_dir, account_id)
        else:
            docker_init(image, home_dir, init_flags)
    if chain_id not in ['devnet', 'betanet', 'testnet'] and no_gas_price:
        filename = os.path.join(home_dir, 'genesis.json')
        genesis_config = json.load(open(filename))
        genesis_config['gas_price'] = 0
        genesis_config['min_gas_price'] = 0
        json.dump(genesis_config, open(filename, 'w'))
    elif no_gas_price:
        print(
            f'no_gas_price is only for local development network, ignoring for {chain_id}')


def download_config(net, home_dir):
    download_near_s3(
        f'nearcore-deploy/{net}/config.json', os.path.join(home_dir, 'config.json'))


def download_genesis(net, home_dir):
    download_near_s3(
        f'nearcore-deploy/{net}/genesis.json', os.path.join(home_dir, 'genesis.json'))


def net_to_branch(net):
    if net == 'testnet':
        return 'stable'
    elif net == 'betanet':
        return 'beta'
    elif net == 'devnet':
        return 'master'
    else:
        raise Exception(f'Unknown net {net}')


def latest_deployed_version(net):
    return download_near_s3('nearcore-deploy/{net}/latest_deploy')


def download_binary(net, uname):
    latest_deploy_version = latest_deployed_version(net)
    if os.path.exists(os.path.expanduser('~/.nearup/near/version')):
        with open(os.path.expanduser('~/.nearup/near/version')) as f:
            version = f.read().strip()
            if version == latest_deploy_version:
                print('Downloaded binary version is up to date')
                return
    print(f'Downloading latest deployed version for {net}')
    download_near_s3(
        f'nearcore/{uname}/{net_to_branch(net)}/{latest_deploy_version}/near', os.path.expanduser('~/.nearup/near/near'))
    download_near_s3(
        f'nearcore/{uname}/{net_to_branch(net)}/{latest_deploy_version}/keypair-generator', os.path.expanduser('~/.nearup/near/keypair-generator'))
    download_near_s3(
        f'nearcore/{uname}/{net_to_branch(net)}/{latest_deploy_version}/genesis-csv-to-json', os.path.expanduser('~/.nearup/near/genesis-csv-to-json'))
    subprocess.check_output(
        ['chmod', '+x', os.path.expanduser('~/.nearup/near/near')])
    subprocess.check_output(
        ['chmod', '+x', os.path.expanduser('~/.nearup/near/keypair-generator')])
    subprocess.check_output(
        ['chmod', '+x', os.path.expanduser('~/.nearup/near/genesis-csv-to-json')])
    with open(os.path.expanduser('~/.nearup/near/version'), 'w') as f:
        f.write(latest_deploy_version)


def get_genesis_time(net):
    return download_near_s3(f'nearcore-deploy/{net}/genesis_time')


def get_genesis_protocol_version(net):
    return int(download_near_s3(f'nearcore-deploy/{net}/protocol_version').strip())


def print_staking_key(home_dir):
    key_path = os.path.join(home_dir, 'validator_key.json')
    if not os.path.exists(key_path):
        return

    key_file = json.loads(open(key_path).read())
    if not key_file['account_id']:
        print("Node is not staking. Re-run init to specify staking account.")
        return
    print("Stake for user '%s' with '%s'" %
          (key_file['account_id'], key_file['public_key']))


def docker_stop_if_exists(name):
    """Stops and removes given docker container."""
    try:
        subprocess.Popen(['docker', 'stop', name], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
    except subprocess.CalledProcessError:
        pass
    try:
        subprocess.Popen(['docker', 'rm', name], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
    except subprocess.CalledProcessError:
        pass


def get_port(home_dir, net):
    """Checks the ports saved in config.json"""
    config = json.load(open(os.path.join(home_dir, 'config.json')))
    p = config[net]['addr'][config[net]['addr'].find(':') + 1:]
    return p + ":" + p


def run_docker(image, home_dir, boot_nodes, telemetry_url, verbose):
    """Runs NEAR core inside the docker container"""
    print("Starting NEAR client docker...")
    docker_stop_if_exists('watchtower')
    docker_stop_if_exists('nearcore')
    # Start nearcore container, mapping home folder and ports.
    envs = [*(['-e', 'BOOT_NODES=%s' % boot_nodes] if boot_nodes else []),
            '-e', 'TELEMETRY_URL=%s' % telemetry_url,
            '-e', 'RUST_BACKTRACE=1']
    rpc_port = get_port(home_dir, 'rpc')
    network_port = get_port(home_dir, 'network')
    if verbose:
        envs.extend(['-e', 'VERBOSE=1'])
    subprocess.check_output(['mkdir', '-p', home_dir])
    subprocess.check_output(['docker', 'run', '-u', USER,
                             '-d', '-p', rpc_port, '-p', network_port, '-v', '%s:/srv/near' % home_dir,
                             '-v', '/tmp:/tmp',
                             '--ulimit', 'core=-1',
                             '--name', 'nearcore', '--restart', 'unless-stopped'] +
                            envs + [image])
    print("Node is running! \nTo check logs call: docker logs --follow nearcore")


def run_nodocker(home_dir, binary_path, boot_nodes, telemetry_url, verbose):
    """Runs NEAR core outside of docker."""
    print("Starting NEAR client...")
    cmd = [f'{binary_path}/near']
    cmd.extend(['--home', home_dir])
    if verbose:
        cmd += ['--verbose', '']
    cmd.append('run')
    cmd.append('--telemetry-url=%s' % telemetry_url)
    if boot_nodes:
        cmd.append('--boot-nodes=%s' % boot_nodes)
    try:
        subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\nStopping NEARCore.")


def check_binary_version(binary_path, chain_id):
    latest_deploy_version = latest_deployed_version(chain_id)
    version = subprocess.check_output(
        [f'{binary_path}/near', '--version'], universal_newlines=True).split('(build ')[1].split(')')[0]
    if not latest_deploy_version.startswith(version):
        print(
            f'Warning: current deployed version on {chain_id} is {latest_deploy_version}, but local binary is {version}. It might not work')


def setup_and_run(nodocker, binary_path, image, home_dir, init_flags, boot_nodes, telemetry_url, verbose=False, no_gas_price=False):
    chain_id = get_chain_id_from_flags(init_flags)
    if nodocker:
        if binary_path == '':
            print(f'Using officially compiled binary')
            uname = os.uname()[0]
            if uname != 'Linux':
                print(
                    'Sorry your Operating System does not have officially compiled binary now, please compile nearcore locally and set --binary-path')
                exit(1)
            binary_path = os.path.expanduser('~/.nearup/near')
            subprocess.check_output(['mkdir', '-p', binary_path])
            download_binary(chain_id, uname)
        else:
            print(f'Using local binary at {binary_path}')
            check_binary_version(binary_path, chain_id)
    else:
        if image == 'auto':
            if chain_id == 'betanet':
                image = 'nearprotocol/nearcore:beta'
            elif chain_id == 'devnet':
                image = 'nearprotocol/nearcore:master'
            else:
                image = 'nearprotocol/nearcore'
        try:
            print(f'Pull docker image {image}')
            subprocess.check_output(['docker', 'pull', image])
        except subprocess.CalledProcessError as exc:
            print("Failed to fetch docker containers: %s" % exc)
            exit(1)

    check_and_setup(nodocker, binary_path, image,
                    home_dir, init_flags, no_gas_price)

    print_staking_key(home_dir)

    if nodocker:
        run_nodocker(home_dir, binary_path, boot_nodes, telemetry_url, verbose)
    else:
        run_docker(image, home_dir, boot_nodes, telemetry_url, verbose)


def stop():
    out = subprocess.check_output(
        ['docker', 'ps', '-q', '-f', 'name=nearcore'], universal_newlines=True).strip()
    if out != '':
        stop_docker()
    else:
        stop_native()


def stop_docker():
    """Stops docker for Nearcore and watchtower if they are running."""
    docker_stop_if_exists('watchtower')
    print('Stopping docker near')
    docker_stop_if_exists('nearcore')


def stop_native():
    try:
        out = subprocess.check_output(['pgrep', 'near']).strip()
        if out != '':
            print(f'Stopping native near with PID {out}')
            subprocess.call(['kill', out])
    except subprocess.CalledProcessError:
        pass


def generate_node_key(home, binary_path, nodocker, image):
    print("Generating node key...")
    if nodocker:
        cmd = [f'{binary_path}/keypair-generator']
        cmd.extend(['--home', home])
        cmd.extend(['--generate-config'])
        cmd.extend(['node-key'])
        try:
            subprocess.call(cmd)
        except KeyboardInterrupt:
            print("\nStopping NEARCore.")
    else:
        subprocess.check_output(['mkdir', '-p', home])
        subprocess.check_output(['docker', 'run', '-u', USER, '-v', '%s:/srv/keypair-generator' % home,
                                 image, 'keypair-generator', '--home=/srv/keypair-generator', '--generate-config', 'node-key'])
    print("Node key generated")


def generate_validator_key(home, binary_path, nodocker, image, account_id):
    print("Generating validator key...")
    if nodocker:
        cmd = [f'{binary_path}/keypair-generator']
        cmd.extend(['--home', home])
        cmd.extend(['--generate-config'])
        cmd.extend(['--account-id', account_id])
        cmd.extend(['validator-key'])
        try:
            subprocess.call(cmd)
        except KeyboardInterrupt:
            print("\nStopping NEARCore.")
    else:
        subprocess.check_output(['mkdir', '-p', home])
        subprocess.check_output(['docker', 'run', '-u', USER, '-v', '%s:/srv/keypair-generator' % home, image, 'keypair-generator',
                                 '--home=/srv/keypair-generator', '--generate-config', '--account-id=%s' % account_id, 'validator-key'])
    print("Validator key generated")


def generate_signer_key(home, binary_path, nodocker, image, account_id):
    print("Generating signer keys...")
    if nodocker:
        cmd = [f'{binary_path}/keypair-generator']
        cmd.extend(['--home', home])
        cmd.extend(['--generate-config'])
        cmd.extend(['--account-id', account_id])
        cmd.extend(['signer-keys'])
        try:
            subprocess.call(cmd)
        except KeyboardInterrupt:
            print("\nStopping NEARCore.")
    else:
        subprocess.check_output(['mkdir', '-p', home])
        subprocess.check_output(['docker', 'run', '-u', USER, '-v', '%s:/srv/keypair-generator' % home, image, 'keypair-generator',
                                 '--home=/srv/keypair-generator', '--generate-config', '--account-id=%s' % account_id, 'signer-keys'])
    print("Signer keys generated")


def initialize_keys(home, binary_path, nodocker, image, account_id, generate_signer_keys):
    if generate_signer_keys:
        generate_signer_key(home, binary_path, nodocker, image, account_id)
    generate_node_key(home, binary_path, nodocker, image)
    if account_id:
        generate_validator_key(home, binary_path, nodocker, image, account_id)


def create_genesis(home, binary_path, nodocker, image, chain_id, tracked_shards):
    if os.path.exists(os.path.join(home, 'genesis.json')):
        print("Genesis already exists")
        return
    print("Creating genesis...")
    if not os.path.exists(os.path.join(home, 'accounts.csv')):
        raise Exception(
            "Failed to generate genesis: accounts.csv does not exist")
    if nodocker:
        cmd = [f'{binary_path}/genesis-csv-to-json']
        cmd.extend(['--home', home])
        cmd.extend(['--chain-id', chain_id])
        if len(tracked_shards) > 0:
            cmd.extend(['--tracked-shards', tracked_shards])
        try:
            subprocess.call(cmd)
        except KeyboardInterrupt:
            print("\nStopping NEARCore.")
    else:
        subprocess.check_output(['mkdir', '-p', home])
        subprocess.check_output(['docker', 'run', '-u', USER, '-v', '%s:/srv/genesis-csv-to-json' % home, image, 'genesis-csv-to-json',
                                 '--home=/srv/genesis-csv-to-json', '--chain-id=%s' % chain_id, '--tracked-shards=%s' % tracked_shards])
    print("Genesis created")


def start_stakewars(home, binary_path, nodocker, image, telemetry_url, verbose, tracked_shards):
    create_genesis(home, binary_path, nodocker, image,
                   'stakewars', tracked_shards)
    if nodocker:
        run_nodocker(home, binary_path, boot_nodes='',
                     telemetry_url=telemetry_url, verbose=verbose)
    else:
        run_docker(image, home, boot_nodes='',
                   telemetry_url=telemetry_url, verbose=verbose)
