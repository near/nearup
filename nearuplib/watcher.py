import logging
import os
import sys

from subprocess import Popen

import psutil

from nearuplib.constants import DEFAULT_WAIT_TIMEOUT, WATCHER_PID_FILE


def run_watcher(net, path=os.path.expanduser('~/.local/bin/watcher')):
    logging.info("Starting the nearup watcher...")

    if not os.path.exists(path):
        logging.error(
            "Delete current nearup and install the new with `pip3 install --user nearup`"
        )
        logging.error(
            "To run nearup locally use: `pip3 install --user .` from root directory"
        )
        sys.exit(1)

    proc = Popen(['python3', path, 'run', net])

    with open(WATCHER_PID_FILE, 'w') as watcher_pid_file:
        watcher_pid_file.write(str(proc.pid))


def stop_watcher(timeout=DEFAULT_WAIT_TIMEOUT):
    try:
        if os.path.exists(WATCHER_PID_FILE):
            with open(WATCHER_PID_FILE) as pid_file:
                pid = int(pid_file.read())
                process = psutil.Process(pid)
                logging.info(
                    f'Stopping near watcher {process.name()} with pid {pid}...')
                process.terminate()
                process.wait(timeout=timeout)
                os.remove(WATCHER_PID_FILE)
        else:
            logging.info("Nearup watcher is not running...")
    except Exception as ex:
        logging.error(f"There was an error while stopping watcher: {ex}")
