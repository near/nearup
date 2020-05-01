import subprocess
import os

def download(url, filepath=None):
    if filepath:
        if os.path.exists(filepath):
            os.remove(filepath)
        subprocess.check_output(
            ['curl', '--proto', '=https', '--tlsv1.2', '-sSfL', url, '-o', filepath])
    else:
        return subprocess.check_output(
            ['curl', '--proto', '=https', '--tlsv1.2', '-sSfL', url], universal_newlines=True)


def download_near_s3(path, filepath=None):
    return download(
        f'https://s3-us-west-1.amazonaws.com/build.nearprotocol.com/{path}', filepath)
