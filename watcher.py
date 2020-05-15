#!/usr/bin/env python3
# Watch for genesis change, re-nearup when that happens
# This tool is launched by main.py as a background process

import sys
import os
import subprocess
import time
import traceback
from nearuplib.nodelib import genesis_changed, binary_changed, docker_changed
from nearuplib.util import print


def nearup_restart(args):
    main_script = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'main.py'))
    subprocess.check_output(['python3', main_script, 'stop', '--keep-watcher'])
    subprocess.Popen(
        ['python3', main_script, *args])
    print('done')


if __name__ == '__main__':
    net = sys.argv[1]
    home_dir = sys.argv[2]
    docker = sys.argv[3]
    args = sys.argv[4:]

    while True:
        time.sleep(60)
        try:
            if genesis_changed(net, home_dir):
                nearup_restart(args)
                exit(0)
            elif docker == 'nodocker' and binary_changed(net):
                nearup_restart(args)
                exit(0)
            elif docker == 'docker' and docker_changed(net):
                nearup_restart(args)
                exit(0)
        except:
            traceback.print_exc()
            pass
