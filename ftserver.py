from http.server import BaseHTTPRequestHandler, HTTPServer
import json

PORT_NUMBER = 8181
ADDRESS = '0.0.0.0'

class FocusTreeRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print(self)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        message = json.dumps({'current_task':"task", "tree":"tree", "ancestors":"ancestors"})
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
