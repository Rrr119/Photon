"""HTTP server for the SPA test fixtures.

Serves a site directory and logs every request path so tests can verify
that no resource is requested more than once.
"""
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONTENT_TYPES = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.txt': 'text/plain',
}

NOT_FOUND = b'<html><body><h1>404</h1></body></html>'


def make_server(site_dir, log_path, host='127.0.0.1', port=0):
    """Create a ThreadingHTTPServer serving site_dir, logging to log_path."""
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            with lock:
                with open(log_path, 'a') as log:
                    log.write(self.path + '\n')
            path = self.path.split('?')[0].split('#')[0]
            if path == '/':
                path = '/index.html'
            candidate = os.path.join(site_dir, path.lstrip('/'))
            if not os.path.isfile(candidate) and \
                    os.path.isfile(candidate + '.html'):
                candidate += '.html'
            if os.path.isfile(candidate):
                with open(candidate, 'rb') as handle:
                    body = handle.read()
                ext = os.path.splitext(candidate)[1]
                content_type = CONTENT_TYPES.get(ext,
                                                 'application/octet-stream')
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', str(len(NOT_FOUND)))
                self.end_headers()
                self.wfile.write(NOT_FOUND)

    server = ThreadingHTTPServer((host, port), Handler)
    server.port = server.server_address[1]
    return server
