#!/usr/bin/env python3
# Watch for genesis change, re-nearup when that happens
# This tool is launched by main.py as a background process

import sys
import os
import subprocess
import time
import traceback
from nearuplib.nodelib import get_latest_deploy_at
from nearuplib.util import print


def nearup_restart(args):
    main_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'main.py'))
    subprocess.check_output(['python3', main_script, 'stop', '--keep-watcher'])
    subprocess.Popen(['python3', main_script, *args])
    print('done')


if __name__ == '__main__':
    net = sys.argv[1]
    home_dir = sys.argv[2]
    docker = sys.argv[3]
    args = sys.argv[4:]
    latest_deploy_at = get_latest_deploy_at(net)

    while True:
        time.sleep(60)
        try:
            new_latest_deploy_at = get_latest_deploy_at(net)
            if new_latest_deploy_at and new_latest_deploy_at != latest_deploy_at:
                print(
                    f'new deploy happens at {new_latest_deploy_at}, restart nearup'
                )
                nearup_restart(args)
                break
        except:
            traceback.print_exc()
            pass
