import logging
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


def generate_key(cmd, key):
    logging.info(f"Generating {key}...")

    try:
        result = subprocess.check_call(cmd, stdout=subprocess.PIPE)
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


def initialize_keys(home, binary_path, account_id):
    logging.info("Generating the node keys...")
    generate_node_key(home, binary_path)

    if account_id:
        logging.info("Generating the validator keys...")
        generate_validator_key(home, binary_path, account_id)
