from http.server import BaseHTTPRequestHandler, HTTPServer
import json

PORT_NUMBER = 8181
ADDRESS = '0.0.0.0'

class FocusTreeRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print(self.__dict__)
        print(self.path)
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

        if self.path == '/fuck_my_face':
            return self.send_tree()
        elif self.path == '/current_task':
            return self.send_current()
        else:
            return self.send_tree()


    def send_tree(self):
        message = json.dumps({'current_task':"task", "tree":"tree", "ancestors":"ancestors"})
        self.wfile.write(bytes(message, "utf-8"))

    def send_current(self):
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
