#!/usr/bin/env python

import argparse
import json
import os
import subprocess
import urllib.request
import sys
import shutil

USER = str(os.getuid())+':'+str(os.getgid())


def clone_repo():
    """Clone nearcore repo"""
    raise NotImplementedError()


def install_cargo():
    """Installs cargo/Rust."""
    try:
        subprocess.call(
            [os.path.expanduser('~/.cargo/bin/cargo'), '--version'])
    except OSError:
        print("Installing Rust...")
        subprocess.check_output(
            'curl https://sh.rustup.rs -sSf | sh -s -- -y', shell=True)


def docker_init(image, home_dir, init_flags):
    """Inits the node configuration using docker."""
    subprocess.check_output(['mkdir', '-p', home_dir])
    subprocess.check_output(['docker', 'run', '-u', USER,
                             '-v', '%s:/srv/near' % home_dir,
                             '-v', os.path.abspath('near/res') + ':/near/res',
                             image, 'near', '--home=/srv/near', 'init'] + init_flags)


def docker_init_official(chain_id, image, home_dir, account_id):
    initialize_keys(home_dir, True, False, image,
                    account_id, False)
    download_genesis(chain_id, home_dir)
    download_config(chain_id, home_dir)


def nodocker_init(home_dir, is_release, init_flags):
    """Inits the node configuration using local build."""
    raise NotImplementedError()
    target = './target/%s/near' % ('release' if is_release else 'debug')
    subprocess.call([target,
                     '--home=%s' % home_dir, 'init'] + init_flags)


def get_chain_id_from_flags(flags):
    """Retrieve requested chain id from the flags."""
    chain_id_flags = [flag for flag in flags if flag.startswith('--chain-id=')]
    if len(chain_id_flags) == 1:
        return chain_id_flags[0][len('--chain-id='):]
    return ''


def compile_package(package_name, is_release):
    """Compile given package using cargo"""
    flags = ['-p', package_name]
    if is_release:
        flags = ['--release'] + flags
    code = subprocess.call(
        [os.path.expanduser('~/.cargo/bin/cargo'), 'build'] + flags)
    if code != 0:
        print("Compilation failed, aborting")
        exit(code)


def check_and_setup(nodocker, is_release, image, home_dir, init_flags, no_gas_price=False):
    """Checks if there is already everything setup on this machine, otherwise sets up NEAR node."""
    if nodocker:
        raise NotImplementedError()
        compile_package('near', is_release)

    chain_id = get_chain_id_from_flags(init_flags)
    if os.path.exists(os.path.join(home_dir)):
        missing = []
        for file in ['node_key.json', 'validator_key.json', 'config.json', 'genesis.json']:
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

        if chain_id in ['devnet', 'betanet', 'testnet']:
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
                if chain_id == 'devnet':
                    print(f'Update devnet config for new boot nodes')
                    os.remove(os.path.join(home_dir, 'config.json'))
                    download_config('devnet', home_dir)
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

    if chain_id == 'testnet':
        raise NotImplementedError()
        testnet_genesis_hash = open('near/res/testnet_genesis_hash').read()
        testnet_genesis_records = 'near/res/testnet_genesis_records_%s.json' % testnet_genesis_hash
        if not os.path.exists(testnet_genesis_records):
            print('Downloading testnet genesis records')
            url = 'https://s3-us-west-1.amazonaws.com/testnet.nearprotocol.com/testnet_genesis_records_%s.json' % testnet_genesis_hash
            urllib.urlretrieve(url, testnet_genesis_records)
        init_flags.extend(['--genesis-config', 'near/res/testnet_genesis_config.json', '--genesis-records', testnet_genesis_records,
                           '--genesis-hash', testnet_genesis_hash])

    if nodocker:
        raise NotImplementedError()
        nodocker_init(home_dir, is_release, init_flags)
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
    urllib.request.urlretrieve(
        f'https://s3-us-west-1.amazonaws.com/build.nearprotocol.com/nearcore-deploy/{net}/config.json', os.path.join(home_dir, 'config.json'))


def download_genesis(net, home_dir):
    urllib.request.urlretrieve(
        f'https://s3-us-west-1.amazonaws.com/build.nearprotocol.com/nearcore-deploy/{net}/genesis.json', os.path.join(home_dir, 'genesis.json'))


def get_genesis_time(net):
    response = urllib.request.urlopen(
        f'https://s3-us-west-1.amazonaws.com/build.nearprotocol.com/nearcore-deploy/{net}/genesis_time')
    data = response.read()
    return data.decode('utf-8').strip()


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


def run_nodocker(home_dir, is_release, boot_nodes, telemetry_url, verbose):
    """Runs NEAR core outside of docker."""
    print("Starting NEAR client...")
    print("Autoupdate is not supported at the moment for runs outside of docker")
    cmd = ['./target/%s/near' % ('release' if is_release else 'debug')]
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


def setup_and_run(nodocker, is_release, image, home_dir, init_flags, boot_nodes, telemetry_url, verbose=False, no_gas_price=False):
    if nodocker:
        raise NotImplementedError()
        clone_repo()
        install_cargo()
    else:
        if image == 'auto':
            chain_id = get_chain_id_from_flags(init_flags)
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

    check_and_setup(nodocker, is_release, image,
                    home_dir, init_flags, no_gas_price)

    print_staking_key(home_dir)

    if nodocker:
        run_nodocker(home_dir, is_release, boot_nodes, telemetry_url, verbose)
    else:
        run_docker(image, home_dir, boot_nodes, telemetry_url, verbose)


def stop_docker():
    """Stops docker for Nearcore and watchtower if they are running."""
    docker_stop_if_exists('watchtower')
    docker_stop_if_exists('nearcore')


def generate_node_key(home, is_release, nodocker, image):
    print("Generating node key...")
    if nodocker:
        cmd = ['./target/%s/keypair-generator' %
               ('release' if is_release else 'debug')]
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


def generate_validator_key(home, is_release, nodocker, image, account_id):
    print("Generating validator key...")
    if nodocker:
        cmd = ['./target/%s/keypair-generator' %
               ('release' if is_release else 'debug')]
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


def generate_signer_key(home, is_release, nodocker, image, account_id):
    print("Generating signer keys...")
    if nodocker:
        cmd = ['./target/%s/keypair-generator' %
               ('release' if is_release else 'debug')]
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


def initialize_keys(home, is_release, nodocker, image, account_id, generate_signer_keys):
    if nodocker:
        install_cargo()
        compile_package('keypair-generator', is_release)
    else:
        try:
            subprocess.check_output(['docker', 'pull', image])
        except subprocess.CalledProcessError as exc:
            print("Failed to fetch docker containers: %s" % exc)
            exit(1)
    if generate_signer_keys:
        generate_signer_key(home, is_release, nodocker, image, account_id)
    generate_node_key(home, is_release, nodocker, image)
    if account_id:
        generate_validator_key(home, is_release, nodocker, image, account_id)


def create_genesis(home, is_release, nodocker, image, chain_id, tracked_shards):
    if os.path.exists(os.path.join(home, 'genesis.json')):
        print("Genesis already exists")
        return
    print("Creating genesis...")
    if not os.path.exists(os.path.join(home, 'accounts.csv')):
        raise Exception(
            "Failed to generate genesis: accounts.csv does not exist")
    if nodocker:
        cmd = ['./target/%s/genesis-csv-to-json' %
               ('release' if is_release else 'debug')]
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


def start_stakewars(home, is_release, nodocker, image, telemetry_url, verbose, tracked_shards):
    if nodocker:
        install_cargo()
        compile_package('genesis-csv-to-json', is_release)
        compile_package('near', is_release)
    else:
        try:
            subprocess.check_output(['docker', 'pull', image])
        except subprocess.CalledProcessError as exc:
            print("Failed to fetch docker containers: %s" % exc)
            exit(1)
    create_genesis(home, is_release, nodocker, image,
                   'stakewars', tracked_shards)
    if nodocker:
        run_nodocker(home, is_release, boot_nodes='',
                     telemetry_url=telemetry_url, verbose=verbose)
    else:
        run_docker(image, home, boot_nodes='',
                   telemetry_url=telemetry_url, verbose=verbose)
