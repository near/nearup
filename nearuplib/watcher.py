import logging
import os
import site
import sys

from subprocess import Popen

import psutil

from nearuplib.constants import DEFAULT_WAIT_TIMEOUT, WATCHER_PID_FILE


def check_watcher_file():
    if not os.path.exists(WATCHER_PID_FILE):
        return False

    with open(WATCHER_PID_FILE) as pid_file:
        try:
            pid = int(pid_file.readline().strip())
        except Exception:
            logging.error(
                f"Nearup watcher PID file {WATCHER_PID_FILE} has unexpected content."
            )
            return True

        logging.warning(
            f"Old Nearup watcher PID file {WATCHER_PID_FILE} found.")

        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            logging.error("Nearup watcher is running.")
            return True


def is_watcher_running():
    if check_watcher_file():
        logging.error("Run nearup stop or kill the process manually!")
        logging.warning(f"If this is a mistake, remove {WATCHER_PID_FILE}")
        return True
    return False


def run_watcher(net, path=os.path.join(site.USER_BASE, 'bin/watcher'), home=''):
    logging.info("Starting the nearup watcher...")

    if is_watcher_running():
        sys.exit(1)

    if not os.path.exists(path):
        logging.error(
            "Delete current nearup and install the new with `pip3 install --user nearup`"
        )
        logging.error(
            "To run nearup locally use: `pip3 install --user .` from root directory"
        )
        sys.exit(1)

    proc = Popen(['python3', path, 'run', net, home])

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

                try:
                    process.terminate()
                    process.wait(timeout=timeout)
                except psutil.TimeoutExpired:
                    logging.warning(
                        'Watcher taking a long time to terminate...')
                    logging.warning('Killing watcher with pid {pid}')
                    process.kill()

                os.remove(WATCHER_PID_FILE)
        else:
            logging.info("Nearup watcher is not running...")
    except Exception as ex:
        logging.error(f"There was an error while stopping watcher: {ex}")
