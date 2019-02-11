from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os.path
import focus
import mailtool


class FocusTreeRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path == '/api/send-command':
            self.send_response(200)
            content_length = int(self.headers['Content-Length'])
            command_line = self.rfile.read(content_length).decode('utf-8')

            status = 'OK'
            errors = None
            term_output = None
            server_commands = ['send-org']
            try:
                words = command_line.split();
                operation = words[0].lower()
                args = ' '.join(words[1:])
                if operation not in server_commands:
                    term_output = THE_TREE.execute_command(command_line)
                    THE_TREE.save_to_file(save_file)
                else:
                    if operation in ['send-org']:
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


    def do_GET(self):
        print(self.path)
        if self.path == '/':
            return self.send_tree()
        elif self.path.startswith('/api/'):
            return self.serve_api()
        elif self.path.startswith('/simple-client/'):
            return self.serve_simple_client()
        else:
            return self.serve_static_react()

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
    try:

        SERVER_ADDRESS = '0.0.0.0'
        PORT_NUMBER = 5051
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

        import sys
        if len(sys.argv) >= 3:
            if sys.argv[1] == '--port':
                PORT_NUMBER = int(sys.argv[2])

        save_file = os.path.expanduser('~/.focus-tree_{}.json'.format(PORT_NUMBER))
        THE_TREE = focus.TreeManager()
        try:
            THE_TREE = focus.TreeManager.load_from_file(save_file)
        except:
            THE_TREE = focus.TreeManager()

        server = HTTPServer(
            (SERVER_ADDRESS, PORT_NUMBER),
            FocusTreeRequestHandler
        )
        HOTMAIL = mailtool.make_hotmail_connection()

        print("Server is started on {} port {}, save file is {}".format(SERVER_ADDRESS, PORT_NUMBER, save_file))
        server.serve_forever()

    except KeyboardInterrupt:
        print("^C received, shutting down")
        server.socket.close()
