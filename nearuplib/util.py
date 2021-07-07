import logging
import os
import stat

import boto3
from botocore import UNSIGNED
from botocore.client import Config

from nearuplib.constants import S3_BUCKETS
from nearuplib.exceptions import NetworkError, capture_as


@capture_as(NetworkError)
def download_from_s3(bucket, path, filepath=None):
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    s3_client.download_file(bucket, path, filepath)


@capture_as(NetworkError)
def exists_on_s3(bucket, path):
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    try:
        s3_client.head_object(Bucket=bucket, Key=path)
    except s3_client.exceptions.NoSuchKey:
        return False

    return True


@capture_as(NetworkError)
def read_from_s3(bucket, path):
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    response = s3_client.get_object(Bucket=bucket, Key=path)
    return response['Body'].read().decode('utf-8')


def new_release_ready(net, uname):
    """Sanity check that a new release is ready for download."""
    if net in ["localnet", "guildnet"]:
        commit = latest_deployed_release_commit("testnet")
        branch = latest_deployed_release_branch("testnet")
    else:
        commit = latest_deployed_release_commit(net)
        branch = latest_deployed_release_branch(net)

    if not commit:
        return False

    path = f'nearcore/{uname}/{branch}/{commit}/neard'

    return exists_on_s3(S3_BUCKETS["default"], path)


def download_config(net, home_dir):
    download_from_s3(S3_BUCKETS[net], f'nearcore-deploy/{net}/config.json',
                     os.path.join(home_dir, 'config.json'))


def download_genesis(net, home_dir):
    download_from_s3(S3_BUCKETS[net], f'nearcore-deploy/{net}/genesis.json',
                     os.path.join(home_dir, 'genesis.json'))


def download_binaries(net, uname, nightly=False):
    commit = latest_deployed_release_commit(net)
    branch = latest_deployed_release_branch(net)

    if commit:
        logging.info(f'Downloading latest deployed version for {net}')

        binary = 'neard'

        download_url = f'nearcore/{uname}/{branch}/{commit}/{binary}'
        if nightly:
            download_url = f'nearcore/{uname}/{branch}/{commit}/nightly/{binary}'

        download_path = os.path.expanduser(f'~/.nearup/near/{net}/{binary}')

        logging.info(
            f"Downloading {binary} to {download_path} from {download_url}...")
        download_from_s3(S3_BUCKETS['default'], download_url, download_path)
        logging.info(f"Downloaded {binary} to {download_path}...")

        logging.info(f"Making the {binary} executable...")
        status = os.stat(download_path)
        os.chmod(download_path, status.st_mode | stat.S_IEXEC)

        # TODO: seperate into download_metadata function with missing metadata
        with open(os.path.expanduser(f'~/.nearup/near/{net}/version'),
                  'w') as version_file:
            version_file.write(commit)


def latest_deployed_release_commit(net):
    if net in ["localnet", "guildnet"]:
        return read_from_s3(S3_BUCKETS['default'],
                            'nearcore-deploy/testnet/latest_deploy').strip()
    return read_from_s3(S3_BUCKETS['default'],
                        f'nearcore-deploy/{net}/latest_deploy').strip()


def latest_deployed_release_commit_has_changed(net, commit):
    latest_commit = latest_deployed_release_commit(net)

    logging.info(f"Current release commit is: {commit}")
    logging.info(f"Latest release commit is {latest_commit}")

    if not commit:
        return False

    return commit != latest_commit


def latest_deployed_release_branch(net):
    if net in ["localnet", "guildnet"]:
        return read_from_s3(S3_BUCKETS['default'],
                            'nearcore-deploy/testnet/latest_release').strip()
    return read_from_s3(S3_BUCKETS['default'],
                        f'nearcore-deploy/{net}/latest_release').strip()


def latest_deployed_release_time(net):
    if net in ["localnet", "guildnet"]:
        return read_from_s3(S3_BUCKETS['default'],
                            'nearcore-deploy/testnet/latest_deploy_at').strip()
    return read_from_s3(S3_BUCKETS['default'],
                        f'nearcore-deploy/{net}/latest_deploy_at').strip()


def latest_genesis_md5sum(net):
    if net in ["localnet", "guildnet"]:
        return read_from_s3(S3_BUCKETS['default'],
                            'nearcore-deploy/testnet/genesis_md5sum').strip()
    return read_from_s3(S3_BUCKETS['default'],
                        f'nearcore-deploy/{net}/genesis_md5sum').strip()


def latest_genesis_md5sum_has_changed(net, md5_sum):
    latest_md5sum = latest_genesis_md5sum(net)

    if net in ["localnet", "guildnet"]:
        latest_md5sum = latest_genesis_md5sum("testnet")

    logging.info(f"Current genesis md5sum is {md5_sum}")
    logging.info(f"Latest genesis md5sum is {latest_md5sum}")

    return latest_md5sum != md5_sum
