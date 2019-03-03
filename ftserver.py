#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from ftclient import get_options
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

    def do_POST(self):
        global THE_TREE
        status = 'OK'
        errors = None
        term_output = None
        term_error = None

        if self.path == '/api/send-command':
            self.send_response(200)
            content_length = int(self.headers['Content-Length'])
            command_line = self.rfile.read(content_length).decode('utf-8')

            server_commands = ['send-org', 'so', 'save-file']
            try:
                words = command_line.split();
                operation = words[0].lower()
                args = ' '.join(words[1:])
                if operation not in server_commands:
                    term_output = THE_TREE.execute_command(command_line)
                    THE_TREE.save_to_file(save_file)
                else:
                    if operation in ['save-file']:
                        THE_TREE.save_to_file(args)
                    elif operation in ['load-file']:
                        THE_TREE = focus.TreeManager.load_from_file(args)

            except focus.FocusTreeException as e:
                status = 'error'
                errors = str(e)
            except Exception as e:
                status = 'error'
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
        print(self.path)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            return self.send_tree()
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
        react_file = os.path.normpath(
            os.getcwd() + '/clients/ft-web-client/build/' + self.path
            )
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
        elif react_file.endswith('svg'):
            self.send_response(304)
            self.send_header('Content-Type', 'text/plain')
            pass
        else:
            self.send_header('Content-Type', 'text/plain')

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
        self.send_header('Content-type', 'text/plain')
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

        program_options = get_options()

        if program_options.config_file:
            save_file = os.path.dirname(program_options.config_file) + '/.focustree.save.{}.json'.format(program_options.port)
        else:
            save_file = os.path.expanduser('~/.focus-tree_{}.json'.format(program_options.port))

        THE_TREE = focus.TreeManager()
        try:
            THE_TREE = focus.TreeManager.load_from_file(save_file)
        except:
            THE_TREE = focus.TreeManager()

        server = HTTPServer(
            (program_options.host, program_options.port),
            FocusTreeRequestHandler
        )

        print("Server is started on {} port {}, save file is {}"
              .format(program_options.host, program_options.port, save_file))
        server.serve_forever()

    except KeyboardInterrupt:
        print("^C received, shutting down")
        server.socket.close()
