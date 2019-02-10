import requests
import focus

SERVER_PORT = 8181
SERVER_ADDRESS = 'localhost'


if __name__ == "__main__":
    r = requests.get('http://localhost:5051/api/tree')
    server_tm = focus.TreeManager.from_dict(r.json())
    server_tm.save_to_file('from_client.json')
    print(server_tm.print_tree())
    while True:

        command_line = input('FocusTree> ')
        r = requests.post('http://localhost:5051/api/send-command', data=command_line)
        print(r.json()['term_output'])

        r = requests.get('http://localhost:5051/api/tree')
        server_tm = focus.TreeManager.from_dict(r.json())
        # server_tm.save_to_file('from_client.json')
        # print(server_tm.print_tree())



