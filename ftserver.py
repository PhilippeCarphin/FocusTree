from http.server import BaseHTTPRequestHandler, HTTPServer
import json

PORT_NUMBER = 8181
ADDRESS = '0.0.0.0'

class FocusTreeRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        if self.path == '/fuck_my_face':
            return self.send_tree()
        elif self.path == '/current_task':
            return self.send_current()
        elif self.path == '/index.html':
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.send_file('index.html')
        else:
            return self.send_tree()


    def send_file(self, filename):
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


    def send_tree(self):
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        message = json.dumps({'current_task':"task", "tree":"tree", "ancestors":"ancestors"})
        self.wfile.write(bytes(message, "utf-8"))

    def send_current(self):
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        message = json.dumps({'current_task': "task"})
        self.wfile.write(bytes(message, "utf-8"))



if __name__ == "__main__":
    try:
        server = HTTPServer(
            (ADDRESS, PORT_NUMBER),
            FocusTreeRequestHandler
        )

        print("Server is started on {} port {}".format(ADDRESS, PORT_NUMBER))

        server.serve_forever()

    except KeyboardInterrupt:
        print("^C received, shutting down")
        server.socket.close()
