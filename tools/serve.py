"""Serve the map viewer on http://127.0.0.1:<port>/ and open it in the browser.

    python tools/serve.py examples/catalog.json          a catalog file (its maps are relative to it)
    python tools/serve.py --plugin my_project_plugin.py  a plugin that builds the catalog (see mapviewer_common.Source)

The catalog is re-read on every page load, so new or edited maps appear on a refresh. Listens on localhost only.
"""
import argparse, http.server, mimetypes, sys, threading, webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapviewer_common import VIEWER, Source  # noqa: E402

mimetypes.add_type('model/gltf+json', '.gltf')
mimetypes.add_type('model/gltf-binary', '.glb')


def make_handler(source):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split('?')[0]
            if path == '/':
                self.send_response(302)
                self.send_header('Location', f'/viewer/index.html?catalog=/data/{source.catalog_path}')
                self.end_headers()
                return
            body = None
            if path.startswith('/viewer/'):
                p = (VIEWER / path[len('/viewer/'):]).resolve()
                body = p.read_bytes() if p.is_file() and VIEWER in p.parents else None
            elif path.startswith('/data/'):
                from urllib.parse import unquote
                body = source.read(unquote(path[len('/data/'):]))
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(path)[0] or 'application/octet-stream')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass  # keep the console quiet; errors show in the browser

    return Handler


class Server(http.server.ThreadingHTTPServer):
    # Address reuse lets two servers share a port on Windows; refuse a busy port and move on instead.
    allow_reuse_address = False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('catalog', nargs='?')
    ap.add_argument('--plugin')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--no-browser', action='store_true')
    a = ap.parse_args()
    source = Source(a.catalog, a.plugin)
    server = None
    for port in range(a.port, a.port + 20):
        try:
            server = Server(('127.0.0.1', port), make_handler(source))
            break
        except OSError:
            continue
    if server is None:
        sys.exit(f'Ports {a.port}-{a.port + 19} are all busy.')
    url = f'http://127.0.0.1:{port}/'
    print(f'Map viewer: {url}\nPress Ctrl+C or close this window to stop it.', flush=True)
    if not a.no_browser:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
