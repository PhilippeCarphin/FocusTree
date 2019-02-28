#!/usr/bin/env python3

from program_options import get_options
import sys
import subprocess

opts = get_options()

url = 'http://{}:{}/index.html'.format(opts.host, opts.port)

if sys.platform == 'darwin':
    command = 'open'
else:
    # At CMC I have to open this with firefox because the old
    # version of chrome that I have can't show my web app
    # TODO Change to xdg-open
    command = 'firefox'

subprocess.Popen([command, url])
