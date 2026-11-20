"""Check a fresh extraction, rather than relying on files from the source tree."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from uuid import uuid4
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['phase-2','phase-3','phase-4'],default='phase-4')
    phase=parser.parse_args().phase
    archive = ROOT/'artifacts'/('dao-den-long-v1.0.0.zip' if phase=='phase-4' else 'dao-den-long-'+phase+'.zip')
    clean = ROOT/'artifacts'/('clean-'+str(uuid4()))
    clean.mkdir()
    with ZipFile(archive) as z:
        for name in z.namelist():
            target = (clean/name).resolve()
            if not target.is_relative_to(clean.resolve()):
                raise ValueError('Archive path outside extraction root')
        z.extractall(clean)
    command = [sys.executable, 'tools/headless.py', '--seed', '42', '--night', '3', '--ticks', '10', '--out', 'smoke.jsonl']
    process = subprocess.run(command, cwd=clean, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    rows = [json.loads(s) for s in (clean/'smoke.jsonl').read_text().splitlines()]
    assert rows[-1]['type'] == 'end' and rows[-1]['ticks'] == 10
    server = subprocess.Popen([sys.executable, 'tools/serve.py', '--port', '8013'], cwd=clean, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for i in range(50):
            try:
                response = opener.open('http://127.0.0.1:8013/', timeout=1)
                break
            except OSError:
                time.sleep(.1)
        assert response.status == 200
        assert b'game.js' in response.read()
        for path in ['/src/core.js', '/vendor/three.module.js', '/web/game.js', '/game.contract.json']:
            assert opener.open('http://127.0.0.1:8013'+path).status == 200
        if phase=='phase-4':
            assert json.load(opener.open('http://127.0.0.1:8013/api/leaderboard'))=={'entries':[]}
            value=dict(name='PackUser',score=477,nights_won=1,seed=42)
            request=urllib.request.Request('http://127.0.0.1:8013/api/leaderboard',data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            entries=json.load(opener.open(request))['entries']
            exported=clean/'exported.json'
            subprocess.run([sys.executable,'tools/serve.py','--export-leaderboard',str(exported)],cwd=clean,capture_output=True,check=True)
            assert json.loads(exported.read_text())['entries']==entries
        report = dict(passed=True, fresh_extraction=True, headless_cli=True, static_assets=True,leaderboard_export=phase=='phase-4',
                      archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), bytes=archive.stat().st_size)
        (ROOT/'docs/proof'/phase/'package.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        server.terminate()
        server.wait(timeout=10)
