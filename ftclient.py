import os
import requests
import focus
from termcolor import colored

SERVER_PORT = 8181
SERVER_ADDRESS = 'localhost'

def read_command():
    return input(colored('FocusTree> ', 'green'))

def eval_command(command_line):
    payload = command_line if command_line != '' else 'current'
    words = command_line.split()
    operation = words[0]
    client_commands = ['save-org']
    if operation in client_commands:
        if operation == 'save-org':
            resp = save_org_command(words[1:])
    else:
        resp = requests.post(
            'http://{}:{}/api/send-command'.format(SERVER_ADDRESS, PORT_NUMBER),
            data=payload).json()
    return resp

def print_output(resp):
    if resp['status'] != 'OK':
        print(colored('ERROR : ' + resp['error'], 'red'))
    print(resp['term_output'])

def loop():
    command_line = read_command()
    if command_line == '': return
    resp = eval_command(command_line)
    if resp:
        print_output(resp)

def REPL():
    while True:
        loop()

def get_tree():
    resp = requests.get('http://{}:{}/api/tree'.format(SERVER_ADDRESS, PORT_NUMBER))
    return focus.TreeManager.from_dict(resp.json())

def save_org_command(filename):
    pass
    the_tree = get_tree()
    name = ''.join(words[1:])
    with open(name, 'w+') as f:
        f.write(the_tree.to_org())
    return {
        'command': command_line,
        'status': 'OK',
        'error': None,
        'term_output': 'saved file {}'.format(os.getcwd() + '/' + name),
        'term_error':''
        }

if __name__ == "__main__":
    PORT_NUMBER = 5051
    import sys
    if len(sys.argv) >= 3:
        if sys.argv[1] == '--port':
            PORT_NUMBER = int(sys.argv[2])

    tree = get_tree()
    print(tree.printable_tree())

    REPL()
