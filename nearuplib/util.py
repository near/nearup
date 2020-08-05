import logging
import os
import subprocess


def download(url, filepath=None, *, headers=None):
    if headers:
        headers = sum(list(map(lambda header: ['-H', header], headers)), [])
    else:
        headers = []
    if filepath:
        if os.path.exists(filepath):
            os.remove(filepath)
        subprocess.check_output([
            'curl', '--proto', '=https', '--tlsv1.2', '-sSfL', *headers, url,
            '-o', filepath
        ])
    else:
        return subprocess.check_output(
            ['curl', '--proto', '=https', '--tlsv1.2', '-sSfL', *headers, url],
            universal_newlines=True)


def download_near_s3(path, filepath=None):
    return download(
        f'https://s3-us-west-1.amazonaws.com/build.nearprotocol.com/{path}',
        filepath)


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
