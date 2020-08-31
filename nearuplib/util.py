import logging
import os
import subprocess

import boto3
from botocore import UNSIGNED
from botocore.client import Config

from nearuplib.constants import S3_BUCKET


def download_from_s3(path, filepath=None):
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    s3.download_file(S3_BUCKET, path, filepath)


def read_from_s3(path):
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    response = s3.get_object(Bucket=S3_BUCKET, Key=path)
    return response['Body'].read().decode('utf-8')


def generate_node_key(home, binary_path):
    cmd = [
        f'{binary_path}/keypair-generator', '--home', home, '--generate-config',
        'node-key'
    ]
    try:
        subprocess.call(cmd, stdout=subprocess.PIPE)
    except KeyboardInterrupt:
        logging.warn("\nStopping NEARCore.")
    logging.info("Node key generated")


def generate_validator_key(home, binary_path, account_id):
    logging.info("Generating validator key...")
    cmd = [
        f'{binary_path}/keypair-generator', '--home', home, '--generate-config',
        '--account-id', account_id, 'validator-key'
    ]
    try:
        subprocess.call(cmd, stdout=subprocess.PIPE)
    except KeyboardInterrupt:
        logging.warn("\nStopping NEARCore.")
    logging.info("Validator key generated")


def generate_signer_key(home, binary_path, account_id):
    logging.info("Generating signer keys...")
    cmd = [
        f'{binary_path}/keypair-generator', '--home', home, '--generate-config',
        '--account-id', account_id, 'signer-keys'
    ]
    try:
        subprocess.call(cmd, stdout=subprocess.PIPE)
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
