import requests
import focus
from termcolor import colored

SERVER_PORT = 8181
SERVER_ADDRESS = 'localhost'


if __name__ == "__main__":
    r = requests.get('http://localhost:5051/api/tree')
    server_tm = focus.TreeManager.from_dict(r.json())
    server_tm.save_to_file('from_client.json')
    print(server_tm.print_tree())
    while True:

        command_line = input(colored('FocusTree> ', 'green'))
        if command_line == '':
            continue
        r = requests.post('http://localhost:5051/api/send-command', data=command_line).json()
        if r['status'] != 'OK':
            print(colored('ERROR : ' + r['error'], 'red'))
        print(r['term_output'])

        r = requests.get('http://localhost:5051/api/tree')
        server_tm = focus.TreeManager.from_dict(r.json())
        # server_tm.save_to_file('from_client.json')
        # print(server_tm.print_tree())



