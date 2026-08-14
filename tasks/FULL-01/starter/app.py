import sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

def make_server(db_path, port=0):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self): self.send_error(501)
        def do_POST(self): self.send_error(501)
        def do_PATCH(self): self.send_error(501)
        def log_message(self, *args): pass
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)

if __name__ == '__main__':
    server=make_server(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 8000)
    server.serve_forever()
