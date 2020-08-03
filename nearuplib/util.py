import subprocess
import os
import builtins


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
