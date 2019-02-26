#!/usr/bin/env python3
from program_options import get_options, write_config
import os

if __name__ == '__main__':
    opts = get_options()

    write_config({
        'port': opts.port,
        'host': opts.host
    }, os.getcwd())
