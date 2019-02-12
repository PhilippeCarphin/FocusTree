import os
import requests
import focus
from termcolor import colored

class REPLDoneError(Exception):
    pass

def read_command():
    try:
        return input(colored('FocusTree> ', 'green'))
    except EOFError as e:
        raise REPLDoneError("EOF entered")

def eval_command(command_line):
    payload = command_line if command_line != '' else 'current'
    words = command_line.split()
    operation = words[0]
    client_commands = ['save-org']
    if operation in client_commands:
        if operation == 'save-org':
            the_tree = get_tree()
            resp = save_org_command(''.join(words[1:]), the_tree)
    else:
        request_url = 'http://{}:{}/api/send-command' .format(
            SERVER_ADDRESS,
            PORT_NUMBER
            )
        print(request_url)
        resp = requests.post(request_url, data=payload).json()
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
        try:
            loop()
        except REPLDoneError:
            break
        except KeyboardInterrupt:
            break

def get_tree():
    request_url = 'http://{}:{}/api/tree'.format(SERVER_ADDRESS, PORT_NUMBER)
    print(request_url)
    resp = requests.get(request_url)
    return focus.TreeManager.from_dict(resp.json())

def save_org_command(filename, tree):
    with open(filename, 'w+') as f:
        f.write(tree.to_org())
    return {
        'command': 'save-org ' + filename,
        'status': 'OK',
        'error': None,
        'term_output': 'saved file {}'.format(os.getcwd() + '/' + filename),
        'term_error':''
        }

if __name__ == "__main__":
    PORT_NUMBER = 5051
    SERVER_ADDRESS = 'localhost'

    import sys
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--port':
            i+=1
            PORT_NUMBER = int(sys.argv[i])
        elif sys.argv[i] == '--host':
            i+=1
            SERVER_ADDRESS = sys.argv[i]
        else:
            print(colored("Unrecognized command line option {}".format(sys.argv[i]), 'red'))
            quit(1)
        i += 1


    tree = get_tree()
    print(tree.printable_tree())

    REPL()
