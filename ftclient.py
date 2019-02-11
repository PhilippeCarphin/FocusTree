import requests
import focus
from termcolor import colored

SERVER_PORT = 8181
SERVER_ADDRESS = 'localhost'

def read_command():
    return input(colored('FocusTree> ', 'green'))

def eval_command(command_line):
    payload = command_line if command_line != '' else 'current'
    resp = requests.post(
        'http://{}:{}/api/send-command'.format(SERVER_ADDRESS, PORT_NUMBER),
        data=payload)
    return resp.json()

def print_output(resp):
    if resp['status'] != 'OK':
        print(colored('ERROR : ' + resp['error'], 'red'))
    print(resp['term_output'])

def loop():
    command_line = read_command()
    resp = eval_command(command_line)
    if resp:
        print_output(resp)

def REPL():
    while True:
        loop()

def get_tree():
    resp = requests.get('http://{}:{}/api/tree'.format(SERVER_ADDRESS, PORT_NUMBER))
    return focus.TreeManager.from_dict(resp.json())

if __name__ == "__main__":
    PORT_NUMBER = 5051
    import sys
    if len(sys.argv) >= 3:
        if sys.argv[1] == '--port':
            PORT_NUMBER = int(sys.argv[2])

    tree = get_tree()
    print(tree.print_tree())

    REPL()
