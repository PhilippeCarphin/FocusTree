#!/usr/bin/env python3

from ftclient import get_options
import subprocess

opts = get_options()

command_line = 'open http://{}:{}/index.html'.format(opts.host, opts.port)

subprocess.run(command_line.split())
