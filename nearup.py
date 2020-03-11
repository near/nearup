#!/usr/bin/env python3
import sys
import platform

version = platform.python_version_tuple()
major_version = int(version[0])
minor_version = int(version[1])
if major_version < 3 or minor_version < 6:
    sys.stderr.write('Require Python 3.6 or higher to run nearup')
    exit(1)

print('NEARUP')
