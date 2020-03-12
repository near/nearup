#!/usr/bin/env python3
import os
import subprocess
import sys
import platform

version = platform.python_version_tuple()
major_version = int(version[0])
minor_version = int(version[1])
if major_version < 3 or minor_version < 6:
    sys.stderr.write('Require Python 3.6 or higher to run nearup\n')
    exit(2)

nearup_dir = os.path.expanduser('~/.nearup')
main_script = os.path.expanduser('~/.nearup/main.py')
if os.path.exists(main_script):
    p = subprocess.Popen('cd ' + nearup_dir + ' && git pull',
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    _stdout, _stderr = p.communicate()
    if p.returncode != 0:
        sys.stderr.write('Warning: Failed to update nearup.')
    args = ['python3', main_script] + sys.argv[1:]
    subprocess.run(args)
else:
    p = subprocess.Popen(
        ['git', 'clone', 'https://github.com/nearprotocol/nearup', os.path.expanduser('~/.nearup')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _stdout, _stderr = p.communicate()
    if p.returncode != 0:
        sys.stderr.write('Failed to obtain nearup. Please retry')
        subprocess.check_output(['rm', '-rf', os.path.expanduser('~/.nearup')])
        exit(1)
    args = ['python3', main_script] + sys.argv[1:]
    subprocess.run(args)
