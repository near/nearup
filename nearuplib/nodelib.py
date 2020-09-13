import json
import os
import subprocess
from nearuplib.util import download_near_s3, download, print
import sys
import shutil
import hashlib
from subprocess import Popen, PIPE
from os import unlink, kill
from signal import SIGTERM

USER = str(os.getuid()) + ':' + str(os.getgid())


def docker_init(image, home_dir, init_flags):
    """Inits the node configuration using docker."""
    subprocess.check_output(['mkdir', '-p', home_dir])
    subprocess.check_output([
        'docker', 'run', '-u', USER, '--rm', '-v',
        '%s:/srv/near' % home_dir, '-v',
        os.path.abspath('near/res') +
        ':/near/res', image, 'near', '--home=/srv/near', 'init'
    ] + init_flags)


def docker_init_official(chain_id, image, home_dir, account_id):
    """Inits the node configuration using docker for betanet and testnet"""
    initialize_keys(home_dir, '', False, image, account_id, False)
    download_genesis(chain_id, home_dir)
    download_config(chain_id, home_dir)


def nodocker_init(home_dir, binary_path, init_flags):
    """Inits the node configuration using near binary."""
    target = f'{binary_path}/near'
    subprocess.call([target, '--home=%s' % home_dir, 'init'] + init_flags)


def nodocker_init_official(chain_id, binary_path, home_dir, account_id):
    """Inits the node configuration using near binary for betanet and testnet"""
    initialize_keys(home_dir, binary_path, True, '', account_id, False)
    download_genesis(chain_id, home_dir)
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
        print(f'Our genesis version is up to date')
        return False
    else:
        print(
            f'Remote genesis protocol version md5 {genesis_md5sum}, ours is {local_genesis_md5sum}'
        )
        return True


def check_and_update_genesis(chain_id, home_dir):
    if genesis_changed(chain_id, home_dir):
        print(f'Update genesis config and remove stale data for {chain_id}')
        os.remove(os.path.join(home_dir, 'genesis.json'))
        download_genesis(chain_id, home_dir)
        if os.path.exists(os.path.join(home_dir, 'data')):
            shutil.rmtree(os.path.join(home_dir, 'data'))
        return True
    return False


def check_and_setup(nodocker,
                    binary_path,
                    image,
                    home_dir,
                    init_flags,
                    no_gas_price=False):
    """Checks if there is already everything setup on this machine, otherwise sets up NEAR node."""
    chain_id = get_chain_id_from_flags(init_flags)
    if os.path.exists(os.path.join(home_dir)):
        missing = []
        for file in ['node_key.json', 'config.json', 'genesis.json']:
            if not os.path.exists(os.path.join(home_dir, file)):
                missing.append(file)
        if missing:
            print(
                f'Missing files {", ".join(missing)} in {home_dir}. Maybe last init was failed. either specify different --home or remove {home_dir} to start from scratch.',
                file=sys.stderr)
            exit(1)

        genesis_config = json.loads(
            open(os.path.join(os.path.join(home_dir, 'genesis.json'))).read())
        if genesis_config['chain_id'] != chain_id:
            print(
                f"Folder {home_dir} already has network configuration for {genesis_config['chain_id']}\n"
                f"You want to run {chain_id}, either specify different --home or remove {home_dir} to start from scratch.",
                file=sys.stderr)
            exit(1)

        if chain_id in ['betanet', 'testnet']:
            check_and_update_genesis(chain_id, home_dir)
        else:
            print(f'Start {chain_id}')
            print("Using existing node configuration from %s for %s" %
                  (home_dir, genesis_config['chain_id']))
        return

    print("Setting up network configuration.")
    account_id = [x for x in init_flags if x.startswith('--account-id')]
    if not account_id:
        prompt = "Enter your Staking-Pool-contract ID (xxxxx.stakehouse.betanet)"
        if chain_id != '':
            prompt += " (leave empty if not going to be a validator): "
        else:
            prompt += ": "
        account_id = input(prompt)
        init_flags.append('--account-id=%s' % account_id)
    else:
        account_id = account_id[0].split('=')[-1]

    if nodocker:
        if chain_id in ['betanet', 'testnet']:
            nodocker_init_official(chain_id, binary_path, home_dir, account_id)
        else:
            nodocker_init(home_dir, binary_path, init_flags)
    else:
        if chain_id in ['betanet', 'testnet']:
            docker_init_official(chain_id, image, home_dir, account_id)
        else:
            docker_init(image, home_dir, init_flags)
    if chain_id not in ['betanet', 'testnet'] and no_gas_price:
        filename = os.path.join(home_dir, 'genesis.json')
        genesis_config = json.load(open(filename))
        genesis_config['gas_price'] = 0
        genesis_config['min_gas_price'] = 0
        json.dump(genesis_config, open(filename, 'w'))
    elif no_gas_price:
        print(
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


def docker_changed(net):
    image = net_to_docker_image(net)
    print(f'Docker image: {image}')
    local_version = subprocess.check_output(
        ['docker', 'image', 'ls', '-q', '--filter', f'reference={image}'],
        universal_newlines=True).strip()
    if local_version:
        print(f'Local docker version: {local_version}')
        repo, *tag = image.split(':')
        if tag:
            tag = tag[0]
        else:
            tag = 'latest'
        auth_token = json.loads(
            download(
                f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"
            ))['token']
        image_info = json.loads(
            download(
                f"https://index.docker.io/v2/{repo}/manifests/{tag}",
                headers=[
                    f"Authorization: Bearer {auth_token}",
                    "Accept: application/vnd.docker.distribution.manifest.v2+json"
                ]))
        remote_version = image_info["config"]["digest"].split(':')[1]
        print(f'Remote version: {remote_version}')
        if remote_version.startswith(local_version):
            print('Local docker image is up to date')
            return False
    return True


def binary_changed(net):
    latest_deploy_version = latest_deployed_version(net)
    if os.path.exists(os.path.expanduser(f'~/.nearup/near/{net}/version')):
        with open(os.path.expanduser(f'~/.nearup/near/{net}/version')) as f:
            version = f.read().strip()
            if version == latest_deploy_version:
                print('Downloaded binary version is up to date')
                return False
    return latest_deploy_version


def download_binary(net, uname):
    commit = latest_deployed_version(net)
    branch = latest_deployed_release(net)

    if commit:
        print(f'Downloading latest deployed version for {net}')
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
        print("Node is not staking. Re-run init to specify staking account.")
        return
    print("Stake for user '%s' with '%s'" %
          (key_file['account_id'], key_file['public_key']))


def docker_stop_if_exists(name):
    """Stops and removes given docker container."""
    if type(name) is list:
        names = name
    else:
        names = [name]
    try:
        subprocess.Popen(['docker', 'stop', *names],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
    except subprocess.CalledProcessError:
        pass
    try:
        subprocess.Popen(['docker', 'rm', *names],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
    except subprocess.CalledProcessError:
        pass


def get_port(home_dir, net):
    """Checks the ports saved in config.json"""
    config = json.load(open(os.path.join(home_dir, 'config.json')))
    p = config[net]['addr'][config[net]['addr'].find(':') + 1:]
    return p + ":" + p


def run_docker(image,
               home_dir,
               boot_nodes,
               verbose,
               container_name='nearcore',
               host_network=False,
               watch=False):
    """Runs NEAR core inside the docker container"""
    print("Starting NEAR client docker...")
    docker_stop_if_exists(container_name)
    # Start nearcore container, mapping home folder and ports.
    envs = [
        '-e', 'RUST_BACKTRACE=1', '-e',
        'RUST_LOG=%s' % os.environ.get('RUST_LOG', '')
    ]
    home_dir = os.path.abspath(home_dir)
    rpc_port = get_port(home_dir, 'rpc')
    network_port = get_port(home_dir, 'network')
    cmd = ['near', '--home', '/srv/near']
    if verbose:
        cmd += ['--verbose', '']
    cmd.append('run')
    if boot_nodes:
        cmd.append('--boot-nodes=%s' % boot_nodes)
    if host_network:
        network_flags = ['--network', 'host']
    else:
        network_flags = ['-p', rpc_port, '-p', network_port]
    subprocess.check_output(['mkdir', '-p', home_dir])
    try:
        subprocess.check_output([
            'docker', 'run', '-u', USER, '-d', '-v',
            '%s:/srv/near' %
            home_dir, *network_flags, '-v', '/tmp:/tmp', '--ulimit', 'core=-1',
            '--name', container_name, '--restart', 'unless-stopped'
        ] + envs + [image] + cmd)
    except subprocess.CalledProcessError as e:
        print('Failed to run docker near. Error:', file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        exit(1)
    if watch:
        run_watcher(watch, 'docker')


def run_docker_testnet(image,
                       home,
                       *,
                       shards=None,
                       validators=None,
                       non_validators=None):
    subprocess.check_output(['mkdir', '-p', home])
    home = os.path.abspath(home)
    command = [
        'docker', 'run', '-u', USER, '--rm', '-v',
        '%s:/srv/near' % home, image, 'near', '--home', '/srv/near', 'testnet'
    ]
    if shards:
        command.extend(['--shards', str(shards)])
    if validators:
        command.extend(['--v', str(validators)])
    if non_validators:
        command.extend(['--n', str(non_validators)])
    try:
        subprocess.check_output(command)
    except subprocess.CalledProcessError as e:
        print('Failed to run docker near. Error:', file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        exit(1)
    except FileNotFoundError as exc:
        print(
            "Failed to run docker near: docker is not installed or not in PATH",
            file=sys.stderr)
        exit(1)


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
        run_watcher(watch, 'nodocker')
    return near


def run_watcher(watch, docker):
    watch_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'watcher.py'))
    LOGS_FOLDER = os.path.expanduser('~/.nearup/logs')
    subprocess.check_output(['mkdir', '-p', LOGS_FOLDER])
    watch_log = open(os.path.expanduser('~/.nearup/logs/watcher.log'), 'w')
    p = Popen([
        'python3', watch_script, watch['net'], watch['home'], docker,
        *watch['args']
    ],
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
        print("There is already binary nodes running. Stop it using:")
        print("nearup stop")
        print(f"If this is a mistake, remove {NODE_PID}")
        exit(1)
    if shutil.which('docker') is not None:
        p = subprocess.Popen(['docker', 'ps', '-q', '-f', 'name=nearcore'],
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, _ = p.communicate()
        if out.strip():
            print("There is already docker node running. Stop it using:")
            print("nearup stop")
            exit(1)


def run_nodocker(home_dir,
                 binary_path,
                 boot_nodes,
                 verbose,
                 chain_id,
                 watch=False):
    """Runs NEAR core outside of docker."""
    print("Starting NEAR client...")
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
    print(proc.pid, "|", proc_name, "|", chain_id, file=pid_fd)
    pid_fd.close()
    print(
        "Node is running! \nTo check logs call: `nearup logs` or `nearup logs --follow`"
    )


def show_logs(follow, number_lines):
    LOGS_FOLDER = os.path.expanduser('~/.nearup/logs')
    if not os.path.exists(NODE_PID):
        print('Node is not running')
        exit(1)

    pid_info = open(NODE_PID).read()
    if 'betanet' in pid_info:
        net = 'betanet'
    elif 'testnet' in pid_info:
        net = 'testnet'
    else:
        # TODO: localnet could have several logs, not showing them all but list log files here
        # Maybe better to support `nearup logs node0` usage.
        print(
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
    latest_deploy_version = latest_deployed_version(chain_id)
    version = subprocess.check_output(
        [f'{binary_path}/near', '--version'],
        universal_newlines=True).split('(build ')[1].split(')')[0]
    if not latest_deploy_version.startswith(version):
        print(
            f'Warning: current deployed version on {chain_id} is {latest_deploy_version}, but local binary is {version}. It might not work'
        )


def net_to_docker_image(net):
    commit = latest_deployed_version(net)
    branch = latest_deployed_release(net)
    return f'nearprotocol/nearcore:{branch}-{commit}'


def setup_and_run(nodocker,
                  binary_path,
                  image,
                  home_dir,
                  init_flags,
                  boot_nodes,
                  verbose=False,
                  no_gas_price=False,
                  args=None):
    check_exist_neard()
    chain_id = get_chain_id_from_flags(init_flags)
    if nodocker:
        if binary_path == '':
            print(f'Using officially compiled binary')
            uname = os.uname()[0]
            if uname not in ['Linux', 'Darwin']:
                print(
                    'Sorry your Operating System does not have officially compiled binary now.\nPlease compile locally by `make debug` or `make release` in nearcore and set --binary-path'
                )
                exit(1)
            binary_path = os.path.expanduser(f'~/.nearup/near/{chain_id}')
            subprocess.check_output(['mkdir', '-p', binary_path])
            download_binary(chain_id, uname)
            watch = {"args": args, "net": chain_id, 'home': home_dir}
        else:
            print(f'Using local binary at {binary_path}')
            check_binary_version(binary_path, chain_id)
            watch = False
    else:
        if image == 'auto':
            image = net_to_docker_image(chain_id)
            watch = {"args": args, "net": chain_id, 'home': home_dir}
        else:
            watch = False
        try:
            print(f'Pull docker image {image}')
            subprocess.check_output(['docker', 'pull', image])
        except subprocess.CalledProcessError as exc:
            print("Failed to fetch docker containers: \n%s" % exc.stderr,
                  file=sys.stderr)
            exit(1)
        except FileNotFoundError as exc:
            print(
                "Failed to fetch docker containers, docker is not installed or not in PATH",
                file=sys.stderr)
            exit(1)

    check_and_setup(nodocker, binary_path, image, home_dir, init_flags,
                    no_gas_price)

    print_staking_key(home_dir)

    if nodocker:
        run_nodocker(home_dir,
                     binary_path,
                     boot_nodes,
                     verbose,
                     chain_id,
                     watch=watch)
    else:
        run_docker(image, home_dir, boot_nodes, verbose, watch=watch)
        print(
            "Node is running! \nTo check logs call: docker logs --follow nearcore"
        )


def stop(keep_watcher=False):
    if shutil.which('docker') is not None:
        p = subprocess.Popen(['docker', 'ps', '-q', '-f', 'name=nearcore'],
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, _ = p.communicate()
        if out.strip():
            stop_docker(out.split('\n'))
        else:
            stop_native()
    else:
        stop_native()
    if not keep_watcher:
        stop_watcher()


def stop_docker(containers):
    """Stops docker for Nearcore if they are running."""
    print('Stopping docker near')
    docker_stop_if_exists(containers)


def stop_native():
    if os.path.exists(NODE_PID):
        with open(NODE_PID) as f:
            for line in f.readlines():
                pid, proc_name, _ = map(
                    str.strip, line.strip(' \n').split("|"))
                pid = int(pid)
                if proc_name in proc_name_from_pid(pid):
                    print(f"Stopping process {proc_name} with pid", pid)
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
        print(f'Stopping near watcher with pid {pid}')
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
        subprocess.check_output([
            'docker', 'run', '-u', USER, '-v',
            '%s:/srv/keypair-generator' % home, image, 'keypair-generator',
            '--home=/srv/keypair-generator', '--generate-config', 'node-key'
        ])
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
        subprocess.check_output([
            'docker', 'run', '-u', USER, '-v',
            '%s:/srv/keypair-generator' % home, image, 'keypair-generator',
            '--home=/srv/keypair-generator', '--generate-config',
            '--account-id=%s' % account_id, 'validator-key'
        ])
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
        subprocess.check_output([
            'docker', 'run', '-u', USER, '-v',
            '%s:/srv/keypair-generator' % home, image, 'keypair-generator',
            '--home=/srv/keypair-generator', '--generate-config',
            '--account-id=%s' % account_id, 'signer-keys'
        ])
    print("Signer keys generated")


def initialize_keys(home, binary_path, nodocker, image, account_id,
                    generate_signer_keys):
    if generate_signer_keys:
        generate_signer_key(home, binary_path, nodocker, image, account_id)
    generate_node_key(home, binary_path, nodocker, image)
    if account_id:
        generate_validator_key(home, binary_path, nodocker, image, account_id)


def create_genesis(home, binary_path, nodocker, image, chain_id,
                   tracked_shards):
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
        subprocess.check_output([
            'docker', 'run', '-u', USER, '-v',
            '%s:/srv/genesis-csv-to-json' % home, image, 'genesis-csv-to-json',
            '--home=/srv/genesis-csv-to-json',
            '--chain-id=%s' % chain_id,
            '--tracked-shards=%s' % tracked_shards
        ])
    print("Genesis created")
