"""Serve only game assets; repository internals and evidence stay private."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
from leaderboard import Leaderboard

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,store=None,**kwargs):
        self.store=store
        super().__init__(*args,**kwargs)

    def respond(self,value,status=200):
        data=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlsplit(self.path).path!='/api/leaderboard':
            self.send_error(404);return
        origin=self.headers.get('Origin')
        if origin and urlsplit(origin).netloc!=self.headers.get('Host'):
            self.send_error(403);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=4096 or self.headers.get_content_type()!='application/json':
                raise ValueError('Expected a small JSON request')
            value=json.loads(self.rfile.read(size))
            self.respond({'entries':self.store.add(value)},201)
        except (ValueError,TypeError) as exc:
            self.respond({'error':str(exc)},400)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path=='/api/leaderboard':
            self.respond({'entries':self.store.read()});return
        if path=='/api/evidence':
            names={'bench':ROOT/'bench.json','soak':ROOT/'soak.json','verification':ROOT/'docs/proof/phase-4/report.json'}
            self.respond({key:json.loads(p.read_text(encoding='utf-8')) if p.exists() else None for key,p in names.items()});return
        if path != '/' and path != '/game.contract.json' and not path.startswith(('/web/', '/src/', '/vendor/')):
            self.send_error(404)
            return
        target=(ROOT/unquote(path).lstrip('/')).resolve()
        allowed=path=='/' or target==ROOT/'game.contract.json' or any(target.is_relative_to(ROOT/f) for f in ['web','src','vendor'])
        if not allowed:
            self.send_error(404);return
        if path == '/':
            self.path = '/web/index.html'
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'artifacts/user-data')
    parser.add_argument('--export-leaderboard',type=Path)
    args = parser.parse_args()
    store=Leaderboard(args.data_dir)
    if args.export_leaderboard:
        store.export(args.export_leaderboard)
        raise SystemExit(0)
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT),store=store)) as server:
        print(f'Lantern Island: http://127.0.0.1:{args.port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
