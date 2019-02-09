from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import focus

PORT_NUMBER = 5051
ADDRESS = '0.0.0.0'

THE_TREE = focus.TreeManager()

a_root_node = focus.make_test_tree()
THE_TREE.root_nodes.append(a_root_node)
REACT_MANIFEST = {}

class FocusTreeRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path == '/send-command':
            self.send_response(200)
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            print(str(post_data))

            status = 'OK'
            errors = None
            try:
                THE_TREE.execute_command(post_data)
            except IndexError as e:
                status = 'error'
                errors = str(e)

            resp = {
                "command": post_data,
                "status" : status,
                "error"  : errors
            }
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(resp), 'utf-8'))


    def do_GET(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        print(self.path)
        if self.path == '/fuck_my_face' or self.path == '/tree':
            return self.send_tree()
        elif self.path == '/current-task':
            print("CURRENT TASK")
            return self.send_current()
        elif self.path == '/files/main.js':
            self.send_javascript('main.js')
        elif self.path == '/index.html':
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.send_file('index.html')
        elif self.path == '/web-client':
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.send_file('./clients/ft-web-client/build/index.html')
        else:
            # ONLY PERTINENT TO SERVING THE STATIC COMPILED REACT WEB CLIENT
            if self.path.startswith('/static') or self.path == '/service-worker.js' or self.path == '/favicon.ico':
                fullpath = './clients/ft-web-client/build' + self.path
            elif self.path[1:] in REACT_MANIFEST:
                fullpath = self.path[1:]
            if self.path.endswith('css'): ct = 'text/css'
            elif self.path.endswith('js'): ct = 'text/javascript'
            elif self.path.endswith('html'): ct = 'text/html'
            elif self.path.endswith('svg'): ct = 'text/html'
            else: ct = ''
            self.send_header('Content-Type', ct)
            self.end_headers()
            # print("REACT MANIFEST: key:{}, value:{}".format(f,REACT_MANIFEST[f]))
            self.send_file(fullpath)


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
        message = json.dumps(THE_TREE.toDict())
        self.wfile.write(bytes(message, 'utf-8'))


    def send_current(self):
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        message = json.dumps({'current_task': "task"})
        self.wfile.write(bytes(str(THE_TREE.current_task), "utf-8"))



if __name__ == "__main__":
    try:

        with open('./clients/ft-web-client/build/manifest.json') as f:
            manifest = json.loads(f.read())
        # Obviously, frankly, this should be done with an argparse thingy
        import sys
        if len(sys.argv) >= 3:
            if sys.argv[1] == '--port':
                PORT_NUMBER = int(sys.argv[2])

        server = HTTPServer(
            (ADDRESS, PORT_NUMBER),
            FocusTreeRequestHandler
        )

        print("Server is started on {} port {}".format(ADDRESS, PORT_NUMBER))

        server.serve_forever()

    except KeyboardInterrupt:
        print("^C received, shutting down")
        server.socket.close()
