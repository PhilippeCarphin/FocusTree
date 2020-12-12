import os
import json
from termcolor import colored
import argparse

FT_CONFIG_FILE_NAME = '.focustree.json'

def read_config_file():
    file = fs_parent_search(FT_CONFIG_FILE_NAME)
    if file:
        with open(file) as f:
            config = json.loads(f.read())
            config['config_file'] = file
            return config
    else:
        return None


def fs_parent_search(filename):
    """ Search up the directory tree until a file named 'filename' is found.
    This is like what git does to find the '.git' directory from anywhere in the
    repo regardless of what directory we are in """
    directory = os.getcwd()
    while True:
        file = os.path.join(directory, filename)
        if os.path.exists(file):
            return file
        if directory == '/':
            return None
        directory = os.path.split(directory)[0]

    return None

def command_line_parser():
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--port", type=int, help="Port of the server")
    p.add_argument("--host", help="Address of the server")
    p.add_argument("--save-file", help="Save file for the tree")
    p.add_argument("--config-file", help="Config file for persistent options")
    p.add_argument("-v", "--verbose", action="store_true", help="Address of the server")
    p.add_argument("ft_command", nargs='*', help="(optional) The command to send to focus tree, no command will launch an interactive client")
    return p.parse_args()

def get_args(look_for_config_file=True):
    cl_opts = command_line_parser()
    if look_for_config_file:
        config = read_config_file()
    else:
        config = None

    if config:
        cl_opts.config_file = config['config_file']

    def get_value(key, default=None, t=str):
        env_var = 'FOCUS_TREE_' + key.upper()
        if config and key in config:
            if cl_opts.verbose:
                print(colored('Getting {} from from config file {}'
                              .format(key, config['config_file']), 'yellow'))
            return t(config[key])
        elif env_var in os.environ:
            if cl_opts.verbose:
                print(colored('Getting {} from from environment variable {}'
                              .format(key, env_var), 'yellow'))
            return t(os.environ[env_var])
        else:
            if cl_opts.verbose:
                print(colored('Getting {} from hardcoded value {}'
                              .format(key, default), 'yellow'))
            return default

    if not cl_opts.port:
        cl_opts.port = get_value('port', 5051, int)
    if not cl_opts.host:
        cl_opts.host = get_value('host', 'localhost')

    return cl_opts


def write_config(config, directory):
    with open(os.path.join(directory, FT_CONFIG_FILE_NAME), 'w+') as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))
