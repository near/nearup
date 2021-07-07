import glob
import logging
import os
import subprocess
import sys

from nearuplib.constants import NODE_PID_FILE


def next_logname(logname):
    files = glob.glob(f'{logname}.*')

    if not os.path.exists(logname):
        return logname

    highest_index = max([1] + [int(f.split('.')[-1]) for f in files])

    return f'{logname}.{highest_index}'


def show_logs(follow, number_lines):
    if not os.path.exists(NODE_PID_FILE):
        logging.info('Node is not running')
        sys.exit(1)

    with open(NODE_PID_FILE) as pid_file:
        pid_info = pid_file.readline()

    logging.info(pid_info)
    _, _, network = pid_info.strip().split("|")

    if network == "localnet":
        # TODO: localnet could have several logs, not showing them all but list log files here
        # Maybe better to support `nearup logs node0` usage.
        logging.info(
            'You are running local net. Logs are in: ~/.nearup/localnet-logs/')
        sys.exit(0)

    command = [
        'tail',
        '-n',
        str(number_lines),
        '-F' if follow else '',
        os.path.expanduser(f'~/.nearup/logs/{network}.log'),
    ]

    try:
        subprocess.run(command, start_new_session=True, check=True)
    except KeyboardInterrupt:
        sys.exit(0)
    except subprocess.CalledProcessError:
        logging.error("Unable to read logs. Please try again.")
        sys.exit(1)
