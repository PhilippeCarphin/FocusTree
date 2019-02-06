from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import focus

PORT_NUMBER = 5051
ADDRESS = '0.0.0.0'

THE_TREE = focus.TreeManager()

class FocusTreeRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
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
            self.end_headers()
            self.wfile.write(bytes(json.dumps(resp), 'utf-8'))


    def do_GET(self):
        self.send_response(200)
        print(self.path)
        if self.path == '/fuck_my_face':
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
        else:
            return self.send_tree()


    def send_file(self, filename):
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_javascript(self, filename):
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        self.send_file(filename)



    def send_tree(self):
        self.send_header('Content-type', 'text/text')
        self.end_headers()
        message = json.dumps({'current_task':"task", "tree":"tree", "ancestors":"ancestors"})
        self.wfile.write(bytes(THE_TREE.print_tree(), "utf-8"))

    def send_current(self):
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        message = json.dumps({'current_task': "task"})
        self.wfile.write(bytes(str(THE_TREE.current_task), "utf-8"))



if __name__ == "__main__":
    try:

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
