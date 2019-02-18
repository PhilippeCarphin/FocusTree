#!/usr/bin/env python3

from ftclient import get_options
import sys
import subprocess

opts = get_options()

url = 'http://{}:{}/index.html'.format(opts.host, opts.port)

if sys.platform == 'darwin':
    command = 'open'
else:
    command = 'xdg-open'

subprocess.run([command, url])
