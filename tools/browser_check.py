"""Real Chrome/CDP checks. Requires Chrome and websocket-client (QA only)."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    import websocket
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', required=True)
    args = parser.parse_args()
    out = ROOT/'docs/proof'/args.phase
    out.mkdir(parents=True, exist_ok=True)
    profile = ROOT/'artifacts'/'chrome-qa'
    profile.mkdir(parents=True, exist_ok=True)
    candidates = [os.environ.get('CHROME_BIN', ''), r'C:\Program Files\Google\Chrome\Application\chrome.exe', '/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
    chrome = next((c for c in candidates if c and Path(c).is_file()), None)
    if not chrome:
        raise RuntimeError('Set CHROME_BIN to a Chrome executable')
    flags = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else {}
    server = subprocess.Popen([sys.executable, str(ROOT/'tools/serve.py'), '--port', '8012'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
    browser = subprocess.Popen([chrome, '--headless=new', '--no-first-run', '--no-default-browser-check', '--no-proxy-server', '--remote-debugging-port=9232', '--remote-allow-origins=*', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--window-size=1280,720', '--user-data-dir='+str(profile), 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
    ws = None
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(100):
            try:
                tabs = json.load(opener.open('http://127.0.0.1:9232/json', timeout=1))
                tab = next(t for t in tabs if t['type'] == 'page')
                break
            except Exception:
                time.sleep(.1)
        else:
            raise RuntimeError('Chrome debugging port unavailable')
        ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15, suppress_origin=True, http_proxy_host=None)
        counter = 0
        errors = []
        def call(method, params=None):
            nonlocal counter
            counter += 1
            ws.send(json.dumps({'id': counter, 'method': method, 'params': params or {}}))
            while True:
                response = json.loads(ws.recv())
                if response.get('method') == 'Runtime.exceptionThrown':
                    errors.append(response['params']['exceptionDetails'])
                if response.get('id') == counter:
                    if 'error' in response:
                        raise RuntimeError(response['error'])
                    return response.get('result', {})
        def evaluate(expression):
            result = call('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
            if 'exceptionDetails' in result:
                raise RuntimeError(result['exceptionDetails'])
            return result['result'].get('value')
        def wait(expression):
            for _ in range(150):
                if evaluate(expression):
                    return
                time.sleep(.1)
            raise AssertionError('Timed out: '+expression)
        def screenshot(name):
            result = call('Page.captureScreenshot', {'format': 'png'})
            (out/(name+'.png')).write_bytes(base64.b64decode(result['data']))
        call('Runtime.enable')
        call('Page.enable')
        call('Emulation.setDeviceMetricsOverride', {'width': 1280, 'height': 720, 'deviceScaleFactor': 1, 'mobile': False})
        call('Page.navigate', {'url': 'http://127.0.0.1:8012/'})
        wait('!!window.__game')
        screenshot('menu')
        evaluate("document.getElementById('start').click()")
        assert evaluate('__game.screen') == 'intro'
        evaluate("document.getElementById('enter').click()")
        wait("__game.game.tick > 10")
        start = evaluate('__game.game.player.pos[2]')
        call('Input.dispatchKeyEvent', {'type': 'keyDown', 'code': 'KeyW', 'key': 'w'})
        time.sleep(1)
        call('Input.dispatchKeyEvent', {'type': 'keyUp', 'code': 'KeyW', 'key': 'w'})
        assert evaluate('__game.game.player.pos[2]') > start
        screenshot('gameplay')
        evaluate('__game.pause()')
        assert evaluate('__game.screen') == 'pause'
        tick = evaluate('__game.game.simTick')
        time.sleep(.3)
        assert evaluate('__game.game.simTick') == tick
        evaluate('__game.pause()')
        assert evaluate('__game.screen') == 'play'
        # FPS is measured using real requestAnimationFrame time, not capped simulation dt.
        fps = evaluate('new Promise(resolve=>{let n=0,start=performance.now();function sample(now){n++;if(now-start>=3000)resolve(n*1000/(now-start));else requestAnimationFrame(sample)}requestAnimationFrame(sample)})')
        report = {'viewport': [1280, 720], 'renderer': 'Chrome headless / SwiftShader software WebGL',
                  'average_fps': fps, 'movement': True, 'pause': True, 'runtime_errors': errors,
                  'note': 'Software rendering on this machine; hardware FPS must be rechecked on the grading machine.'}
        (out/'browser.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
        assert not errors, errors
    finally:
        if ws:
            ws.close()
        browser.terminate()
        server.terminate()
        browser.wait(timeout=15)
        server.wait(timeout=15)


if __name__ == '__main__':
    main()
