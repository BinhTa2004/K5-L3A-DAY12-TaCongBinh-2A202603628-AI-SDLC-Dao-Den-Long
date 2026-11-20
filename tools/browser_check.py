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
    parser.add_argument('--software', action='store_true')
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
    graphics = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] if args.software else ['--enable-gpu-rasterization']
    browser = subprocess.Popen([chrome, '--headless=new', '--no-first-run', '--no-default-browser-check', '--no-proxy-server', '--remote-debugging-port=9232', '--remote-allow-origins=*', *graphics, '--window-size=1280,720', '--user-data-dir='+str(profile), 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
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
        checks = {}
        per_night = [{'night': 1, 'average_fps': fps}]
        if args.phase == 'phase-2':
            sys.path.insert(0, str(ROOT/'tools'))
            from headless import simulate
            contract = json.loads((ROOT/'game.contract.json').read_text())
            options = dict(contract=contract, seed=99, night=2, ticks=1500, snapshotEvery=10,
                           scenario={'player': {'invuln_ticks': 2000}}, inputs={})
            checks['browser_headless_byte_parity'] = evaluate('Lantern.run('+json.dumps(options)+')') == simulate(options)
            assert checks['browser_headless_byte_parity']
            for n in [1, 2, 3]:
                # Representative populated scene, with damage disabled only to keep QA running.
                evaluate(f"__game.begin({n});document.getElementById('enter').click();__game.game.player.invuln=10000")
                evaluate("for(let i=0;i<__game.game.map.shadeMax;i++){let p=__game.game.map.shadePoints[i].slice();p[1]=.8;__game.game.shades.push({id:'QA'+i,pos:p,state:'wander',timer:0,pushTicks:0,recoilTicks:0})}")
                if n >= 2:
                    evaluate("__game.game.drifters.push({id:'QA1',pos:[8,0,0],state:'idle',stolen:0,timer:0,dir:[1,0],hasStolen:false},{id:'QA2',pos:[-8,0,0],state:'idle',stolen:0,timer:0,dir:[1,0],hasStolen:false})")
                time.sleep(.4)
                screenshot('night-'+str(n))
                value = evaluate('new Promise(resolve=>{let n=0,start=performance.now();function sample(now){n++;if(now-start>=3000)resolve(n*1000/(now-start));else requestAnimationFrame(sample)}requestAnimationFrame(sample)})')
                per_night.append({'night': n, 'average_fps': value, 'max_shades': [6,8,10][n-1], 'drifters': 0 if n==1 else 2})
            evaluate("__game.show('menu');document.getElementById('start').click()")
            expected_total = 0
            for n in [1, 2, 3]:
                assert evaluate('__game.screen') == 'intro'
                assert evaluate('__game.game.night') == n
                evaluate("document.getElementById('enter').click()")
                count = [5, 6, 7][n-1]
                lanterns = [{'id': 'L'+str(i), 'lit': True} for i in range(2, count+1)]
                # Controlled scenario tests a genuine deposit -> win -> next-night UI transition.
                scenario = dict(random_motes=False, random_shades=False, random_drifters=False,
                                wind_enabled=False, player={'pos': [0, 6, 6] if n==3 else [0,0,25 if n==1 else 20], 'carried': 10},
                                lanterns=lanterns)
                evaluate('__game.loadScenario('+str(n)+','+json.dumps(scenario)+')')
                call('Input.dispatchKeyEvent', {'type': 'keyDown', 'code': 'KeyE', 'key': 'e'})
                wait("__game.screen === 'result'")
                call('Input.dispatchKeyEvent', {'type': 'keyUp', 'code': 'KeyE', 'key': 'e'})
                assert evaluate('__game.game.state') == 'won'
                expected_total += evaluate('__game.game.score')
                if n < 3:
                    evaluate("document.getElementById('next').click()")
            assert evaluate("document.getElementById('result-title').textContent") == 'Bình Minh'
            assert str(expected_total) in evaluate("document.getElementById('result-score').textContent.replaceAll('.','')")
            screenshot('campaign-dawn')
            checks['three_night_campaign_and_total'] = True
            lose = {'random_motes': False, 'random_shades': False, 'random_drifters': False,
                    'player': {'flames': 1}, 'shades': [{'pos': [0,0,0]}]}
            evaluate('__game.loadScenario(2,'+json.dumps(lose)+')')
            wait("__game.screen === 'result'")
            assert evaluate('__game.game.state') == 'lost'
            evaluate("document.getElementById('next').click()")
            assert evaluate('__game.screen') == 'intro'
            assert evaluate('__game.game.night') == 2
            checks['loss_retries_same_night'] = True
            evaluate("__game.show('menu');document.getElementById('menu-settings').click();const v=document.getElementById('volume'),s=document.getElementById('sensitivity');v.value=.31;s.value=1.4;v.dispatchEvent(new Event('input'));s.dispatchEvent(new Event('input'))")
            call('Page.reload')
            wait('!!window.__game')
            assert evaluate('__game.settings.volume') == .31
            assert evaluate('__game.settings.sensitivity') == 1.4
            checks['settings_survive_reload'] = True
        gpu = evaluate("(()=>{const gl=__game.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)})()")
        report = {'viewport': [1280, 720], 'renderer': gpu,
                  'average_fps': fps, 'movement': True, 'pause': True, 'runtime_errors': errors,
                  'checks': checks, 'per_night': per_night,
                  'note': 'Measured with requestAnimationFrame on this machine; grading hardware may differ.'}
        (out/'browser.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
        assert not errors, errors
        assert all(n['average_fps'] >= 30 for n in per_night), per_night
    finally:
        if ws:
            ws.close()
        browser.terminate()
        server.terminate()
        browser.wait(timeout=15)
        server.wait(timeout=15)


if __name__ == '__main__':
    main()
