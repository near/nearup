import hashlib
import logging
import os
import re
import stat
import textwrap

import boto3
from botocore import UNSIGNED
from botocore.client import Config
import click

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


def binary_download_url(net, uname, branch, commit, binary):
    if net == 'betanet':
        return f'nearcore/{uname}/{branch}/{commit}/nightly/{binary}'
    elif net == 'shardnet':
        return f'nearcore/{uname}/{branch}/{commit}/shardnet/{binary}'
    else:
        return f'nearcore/{uname}/{branch}/{commit}/{binary}'


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

    path = binary_download_url(net, uname, branch, commit, 'neard')

    return exists_on_s3(S3_BUCKETS["default"], path)


def download_genesis(net, home_dir):
    download_from_s3(S3_BUCKETS[net], f'nearcore-deploy/{net}/genesis.json',
                     os.path.join(home_dir, 'genesis.json'))


def download_binaries(net, uname):
    commit = latest_deployed_release_commit(net)
    branch = latest_deployed_release_branch(net)

    if commit:
        logging.info(f'Downloading latest deployed version for {net}')

        binary = 'neard'
        download_url = binary_download_url(net, uname, branch, commit, binary)

        download_url = f'nearcore/{uname}/{branch}/{commit}/{binary}'
        if net == 'betanet':
            download_url = f'nearcore/{uname}/{branch}/{commit}/nightly/{binary}'
        elif net == 'shardnet':
            download_url = f'nearcore/{uname}/{branch}/{commit}/shardnet/{binary}'

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


def write_md5sum_file(home_dir, filename, md5sum):
    if md5sum is None:
        return

    home_nearup_dir = os.path.join(home_dir, '.nearup')
    if not os.path.exists(home_nearup_dir):
        os.makedirs(home_nearup_dir)

    with open(os.path.join(home_nearup_dir, filename), 'w') as f:
        f.write(md5sum)


# expects genesis_md5sum to be a 2-tuple with genesis and records md5sums
def write_genesis_md5sum(home_dir, md5sums):
    (genesis_md5sum, records_md5sum) = md5sums
    write_md5sum_file(home_dir, 'genesis_md5sum', genesis_md5sum)
    write_md5sum_file(home_dir, 'records_md5sum', records_md5sum)


def read_md5sum_file(home_dir, name):
    md5sum_path = os.path.join(home_dir, f'.nearup/{name}_md5sum')
    try:
        return open(md5sum_path, 'r').read().strip()
    except FileNotFoundError:
        try:
            with open(os.path.join(os.path.join(home_dir, f'{name}.json')),
                      'rb') as fd:
                md5sum = hashlib.md5(fd.read()).hexdigest()
                write_md5sum_file(home_dir, f'{name}_md5sum', md5sum)
                return md5sum
        except FileNotFoundError:
            return None


def read_genesis_md5sum(home_dir):
    return (read_md5sum_file(home_dir,
                             'genesis'), read_md5sum_file(home_dir, 'records'))


def fetch_chain_file(net, filename):
    try:
        if net == "localnet":
            return read_from_s3(S3_BUCKETS['default'],
                                f'nearcore-deploy/testnet/{filename}').strip()
        if net == "guildnet":
            return read_from_s3(S3_BUCKETS['guildnet'],
                                f'nearcore-deploy/guildnet/{filename}').strip()
        return read_from_s3(S3_BUCKETS['default'],
                            f'nearcore-deploy/{net}/{filename}').strip()
    except NetworkError:
        # TODO, NetworkError masks the underlying error, which could have been somethiing
        # other than 404
        return None


def latest_genesis_md5sum(net):
    return (fetch_chain_file(net, 'genesis_md5sum'),
            fetch_chain_file(net, 'records_md5sum'))


_WRAPPER = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)


def wraptext(msg: str) -> str:
    msg = '\n'.join(line.lstrip() for line in msg.strip().splitlines())
    return '\n\n'.join(_WRAPPER.fill(para) for para in re.split('\n{2,}', msg))


def prompt_bool_flag(msg, value, *, interactive):
    if interactive:
        value = click.confirm(wraptext(msg), default=bool(value))
    return bool(value)


def prompt_flag(msg, flag_value, *, default, interactive, type=str):  # pylint: disable=redefined-builtin
    value = default
    if flag_value is not None:
        value = flag_value
    if interactive:
        value = click.prompt(wraptext(msg), type=type, default=value)
    return value
