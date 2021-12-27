#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from program_options import get_args
import socket
import json
import os.path
import focus
import mailtool

def port_is_available(p):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(('localhost', p)) != 0

def find_available_ports(start, end):
    for p in range(start, end):
        if port_is_available(p):
            yield p

def get_first_open_port(start, end):
    return find_available_ports(start, end).send(None)

def test_find_available_ports():
    r = find_available_ports(5050,5055)

    print(r.send(None))
    print(get_first_open_port(5051, 5055))


class FocusTreeRequestHandler(BaseHTTPRequestHandler):
    def handle_command(self, command_line):
        words = command_line.split();
        operation = words[0].lower()
        args = ' '.join(words[1:])
        server_commands = ['send-org', 'so', 'save-file']
        if operation not in server_commands:
            return self.handle_normal_command(command_line)
        else:
            return self.handle_server_command(operation, args)

    def handle_normal_command(self, command_line):
            term_output = THE_TREE.execute_command(command_line)
            THE_TREE.save_to_file(save_file)
            return term_output

    def handle_server_command(self, operation, args):
        global THE_TREE
        if operation in ['so', 'send-org']:
                with open('focus-tree.org', 'w+') as f:
                    f.write(THE_TREE.to_org())
                mailtool.send_mail_connected(
                    'phil103@hotmail.com',
                    args,
                    'FocusTree: Your tree',
                    'Current contents of your tree',
                    HOTMAIL,
                    'focus-tree.org',
                )
        elif operation in ['save-file']:
            THE_TREE.save_to_file(args)
        elif operation in ['load-file']:
            THE_TREE = focus.TreeManager.load_from_file(args)

    def do_POST(self):
        status = 0
        errors = None
        term_output = None
        term_error = None

        if self.path == '/api/send-command':
            self.send_response(200)
            content_length = int(self.headers['Content-Length'])
            command_line = self.rfile.read(content_length).decode('utf-8')

            server_commands = ['send-org', 'so', 'save-file']
            try:
                term_output = self.handle_command(command_line)
            except focus.FocusTreeException as e:
                status = 1
                errors = str(e)
            except Exception as e:
                status = 1
                errors = str(e)
                raise e
            finally:
                resp = {
                    "command": command_line,
                    "status" : status,
                    "term_output": term_output,
                    "error"  : errors
                }
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(bytes(json.dumps(resp), 'utf-8'))

        elif self.path == '/api/send-tree':
            self.send_response(200)
            content_length = int(self.headers['Content-Length'])
            tree_json = self.rfile.read(content_length).decode('utf-8')

            print(tree_json)
            THE_TREE = focus.TreeManager.from_dict(json.loads(tree_json))
            THE_TREE.save_to_file(save_file)
            resp = {
                "command": '/api/send-tree',
                "status" : status,
                "term_output": "Loaded tree",
                "error"  : errors
            }
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(resp), 'utf-8'))


    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            return self.serve_static_react()
        elif self.path.startswith('/api/'):
            return self.serve_api()
        elif self.path.startswith('/simple-client/'):
            return self.serve_simple_client()
        else:
            try:
                return self.serve_static_react()
            except FileNotFoundError as e:
                print("serving static react: " + str(e))

    def serve_api(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path == '/api/tree':
            return self.send_tree()
        elif self.path == '/api/current-task':
            return self.send_current()

    def serve_simple_client(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path == '/simple-client/main.js':
            self.send_javascript('main.js')
        elif self.path == '/simple-client/index.html':
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.send_file('index.html')

    def serve_static_react(self):
        # SERVE FILES FOR REACT WEB CLIENT
        file_dir = os.path.dirname(os.path.realpath(__file__))
        client_dir =  os.path.join(file_dir, 'clients/ft-web-client/build/')
        react_file = os.path.normpath(client_dir + self.path)
        print("Serving static react file {react_file}".format(react_file=react_file))
        if   react_file.endswith('css'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/css')
        elif react_file.endswith('js'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript')
        elif react_file.endswith('html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
        elif react_file.endswith('.map'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
        elif react_file.endswith('.svg'):
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
        else:
            self.send_header('Content-Type', 'text/html')

        self.end_headers()
        self.send_file(react_file)


    def send_file(self, filename):
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_javascript(self, filename):
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        self.send_file(filename)

    def send_tree(self):
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        # hopefully_the_tree = focus.TreeManager.from_dict(THE_TREE.to_dict())
        # hopefully_the_tree.current_task = THE_TREE.current_task
        # message = json.dumps(hopefully_the_tree.to_dict())
        message = json.dumps(THE_TREE.to_dict())
        self.wfile.write(bytes(message, 'utf-8'))

if __name__ == "__main__":

    # test_find_available_ports()
    # quit()

    try:

        args = get_args()

        filename = '.focustree.save.{port}.json'.format(port=args.port)
        if args.config_file:
            directory = os.path.dirname(args.config_file)
        else:
            directory = os.environ['HOME']
        save_file = os.path.join(directory, filename)

        THE_TREE = focus.TreeManager()
        try:
            THE_TREE = focus.TreeManager.load_from_file(save_file)
        except:
            THE_TREE = focus.TreeManager()

        print('Starting server on host {host}, port {port}'.format(host=args.host, port=args.port))

        server = HTTPServer(
            (args.host, args.port),
            FocusTreeRequestHandler,
        )

        print('Server is started on host {host}, port {port}'.format(host=args.host, port=args.port))
        server.serve_forever()

    except KeyboardInterrupt:
        print("^C received, shutting down")
        server.socket.close()
