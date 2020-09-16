import logging
import os
import stat
import subprocess
import sys

import boto3
from botocore import UNSIGNED
from botocore.client import Config

from nearuplib.constants import S3_BUCKET


def download_from_s3(path, filepath=None):
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    s3_client.download_file(S3_BUCKET, path, filepath)


def read_from_s3(path):
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=path)
    return response['Body'].read().decode('utf-8')


def download_config(net, home_dir):
    download_from_s3(f'nearcore-deploy/{net}/config.json',
                     os.path.join(home_dir, 'config.json'))


def download_genesis(net, home_dir):
    download_from_s3(f'nearcore-deploy/{net}/genesis.json',
                     os.path.join(home_dir, 'genesis.json'))


def download_binaries(net, uname):
    commit = latest_deployed_release_commit(net)
    branch = latest_deployed_release_branch(net)

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

        # TODO: seperate into download_metadata function with missing metadata
        with open(os.path.expanduser(f'~/.nearup/near/{net}/version'),
                  'w') as version_file:
            version_file.write(commit)


def latest_deployed_release_commit(net):
    return read_from_s3(f'nearcore-deploy/{net}/latest_deploy').strip()


def latest_deployed_release_commit_has_changed(net, commit):
    latest_commit = latest_deployed_release_commit(net)

    logging.info(f"Current release commit is: {commit}")
    logging.info(f"Latest release commit is {latest_commit}")

    if not commit:
        return False

    return commit != latest_commit


def latest_deployed_release_branch(net):
    return read_from_s3(f'nearcore-deploy/{net}/latest_release').strip()


def latest_deployed_release_time(net):
    return read_from_s3(f'nearcore-deploy/{net}/latest_deploy_at').strip()


def latest_genesis_md5sum(net):
    return read_from_s3(f'nearcore-deploy/{net}/genesis_md5sum').strip()


def generate_key(cmd, key):
    logging.info(f"Generating {key}...")

    try:
        subprocess.check_call(cmd, stdout=subprocess.PIPE)
    except KeyboardInterrupt:
        logging.error("\nStopping NEARCore.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error(f"Unable to generate {key}.")
        sys.exit(1)

    logging.info(f"{key.capitalize()} generated...")


def generate_node_key(home, binary_path):
    cmd = [
        f'{binary_path}/keypair-generator', '--home', home, '--generate-config',
        'node-key'
    ]
    generate_key(cmd, 'node key')


def generate_validator_key(home, binary_path, account_id):
    cmd = [
        f'{binary_path}/keypair-generator', '--home', home, '--generate-config',
        '--account-id', account_id, 'validator-key'
    ]
    generate_key(cmd, 'validator key')


def initialize_keys(home, binary_path, account_id=None):
    logging.info("Generating the node keys...")
    generate_node_key(home, binary_path)

    if account_id:
        logging.info("Generating the validator keys...")
        generate_validator_key(home, binary_path, account_id)
