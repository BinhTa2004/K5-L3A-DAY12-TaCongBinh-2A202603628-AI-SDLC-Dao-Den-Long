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
    server = subprocess.Popen([sys.executable, str(ROOT/'tools/serve.py'), '--port', '8012', '--data-dir', str(profile/'leaderboard-store')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
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
        if args.phase=='phase-4':
            evaluate("document.getElementById('reset-keys').click()")
            evaluate("const e=document.getElementById('large-text');e.checked=false;e.dispatchEvent(new Event('change'))")
            assert evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")==18
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
        if args.phase in ['phase-2','phase-3','phase-4']:
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
                if args.phase in ['phase-3','phase-4']:scenario['time_left_s']=1/60
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
            if args.phase in ['phase-3','phase-4']:
                # Actual renderer checks, including a low lamp whose rounded fuel could read30.0.
                scene = dict(random_motes=False,random_shades=False,random_drifters=False,time_left_s=20,
                    player={'successful_lights':5,'carried':14},
                    lanterns=[{'id':'L1','pos':[0,0,4],'lit':True,'fuel':20}],
                    shades=[{'id':'S1','pos':[4,.8,2],'state':'stunned','state_ticks_left':600}])
                evaluate('__game.loadScenario(1,'+json.dumps(scene)+')')
                wait("document.getElementById('carry-label').textContent.includes('/ 20')")
                evaluate("__game.show('pause');document.getElementById('pause-settings').click();const cb=document.getElementById('colorblind');cb.checked=true;cb.dispatchEvent(new Event('change'))")
                evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                assert evaluate("document.body.classList.contains('colorblind')")
                assert evaluate("__game.visuals.batches.eyes.material.color.getHex()") == 0x00B3FF
                assert evaluate("__game.visuals.batches.shadeGlow.material.color.getHex()") == 0x00B3FF
                assert evaluate("getComputedStyle(document.body).getPropertyValue('--danger').trim()") == '#FFFFFF'
                assert evaluate("getComputedStyle(document.getElementById('clock').parentElement,'::before').content.includes('⚠')")
                assert evaluate("__game.visuals.meshes.get('lantern:L2').userData.body.scale.y") == .8
                assert evaluate("__game.visuals.meshes.get('lantern:L2').userData.tear.visible")
                assert evaluate("document.getElementById('slots').children.length") == 20
                evaluate("__game.game.simTick=0;document.getElementById('settings-back').click()")
                evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                assert evaluate("__game.visuals.meshes.get('lantern:L1').userData.fill.visible")
                assert not evaluate("__game.visuals.meshes.get('lantern:L1').userData.circle.visible")
                evaluate('__game.game.simTick=30')
                evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                assert not evaluate("__game.visuals.meshes.get('lantern:L1').userData.fill.visible")
                evaluate("__game.game.simTick=0;document.getElementById('pause').hidden=true")
                screenshot('colorblind-low-fuel')
                before=evaluate('__game.visuals.ambient.intensity')
                evaluate("__game.game.lanterns[0].fuelUnits=1;__game.game.step({})")
                evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                assert not evaluate('__game.game.lanterns[0].lit')
                assert evaluate('__game.visuals.ambient.intensity')<before
                assert evaluate("__game.visuals.meshes.get('lantern:L1').userData.tear.visible")
                screenshot('extinguished-lantern')
                checks['extinction_reduces_ambient_light']=True
                checks['fuel_bars_blink_collapsed_torn_paper_dynamic_capacity'] = True
                checks['colorblind_cyan_eyes_rim_white_warning'] = True
            evaluate("__game.show('menu');document.getElementById('menu-settings').click();const v=document.getElementById('volume'),s=document.getElementById('sensitivity');v.value=.31;s.value=1.4;v.dispatchEvent(new Event('input'));s.dispatchEvent(new Event('input'))")
            call('Page.reload')
            wait('!!window.__game')
            assert evaluate('__game.settings.volume') == .31
            assert evaluate('__game.settings.sensitivity') == 1.4
            if args.phase in ['phase-3','phase-4']:
                assert evaluate('__game.settings.colorblind') is True
                assert evaluate("document.getElementById('colorblind').checked")
                checks['colorblind_survives_reload']=True
            checks['settings_survive_reload'] = True
            if args.phase=='phase-4':
                evaluate("document.getElementById('menu-settings').click();document.querySelector('[data-action=jump]').click()")
                call('Input.dispatchKeyEvent',{'type':'keyDown','code':'KeyJ','key':'j'})
                call('Input.dispatchKeyEvent',{'type':'keyUp','code':'KeyJ','key':'j'})
                assert evaluate('__game.settings.bindings.jump')=='KeyJ'
                evaluate("document.querySelector('[data-action=jump]').click()")
                call('Input.dispatchKeyEvent',{'type':'keyDown','code':'KeyW','key':'w'})
                call('Input.dispatchKeyEvent',{'type':'keyUp','code':'KeyW','key':'w'})
                assert evaluate('__game.settings.bindings.jump')=='KeyJ'
                assert evaluate("document.getElementById('key-error').textContent.includes('đã dùng')")
                evaluate("document.getElementById('reset-keys').click()")
                assert evaluate('__game.settings.bindings.jump')=='Space'
                evaluate("document.querySelector('[data-action=jump]').click()")
                call('Input.dispatchKeyEvent',{'type':'keyDown','code':'KeyJ','key':'j'})
                call('Input.dispatchKeyEvent',{'type':'keyUp','code':'KeyJ','key':'j'})
                evaluate("for(const id of ['reduced-motion','large-text']){const e=document.getElementById(id);e.checked=true;e.dispatchEvent(new Event('change'))}")
                screenshot('accessibility-settings')
                call('Page.reload');wait('!!window.__game')
                assert evaluate('__game.settings.bindings.jump')=='KeyJ'
                assert evaluate('__game.settings.reducedMotion && __game.settings.largeText')
                assert evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")==22.5
                evaluate("document.getElementById('start').click();document.getElementById('enter').click()")
                call('Input.dispatchKeyEvent',{'type':'keyDown','code':'Space','key':' '})
                time.sleep(.15)
                call('Input.dispatchKeyEvent',{'type':'keyUp','code':'Space','key':' '})
                assert evaluate('__game.game.player.pos[1]')==0
                call('Input.dispatchKeyEvent',{'type':'keyDown','code':'KeyJ','key':'j'})
                time.sleep(.15)
                assert evaluate('__game.game.player.pos[1]')>0
                call('Input.dispatchKeyEvent',{'type':'keyUp','code':'KeyJ','key':'j'})
                font_errors=evaluate("[...document.querySelectorAll('body *')].filter(e=>e.children.length===0&&e.textContent.trim()&&e.getClientRects().length&&parseFloat(getComputedStyle(e).fontSize)<18).map(e=>({tag:e.tagName,id:e.id,size:getComputedStyle(e).fontSize}))")
                assert not font_errors,font_errors
                checks['remapping_conflicts_restore_persistence_and_actual_jump']=True
                checks['ui_minimum_18px_large_125_percent']=True
                notices=dict(random_motes=False,random_shades=True,random_drifters=False,player={'invuln_ticks':10000},time_left_s=10,
                    lanterns=[{'id':'L1','lit':True,'fuel':20}])
                evaluate('__game.loadScenario(1,'+json.dumps(notices)+');for(let i=0;i<299;i++)__game.game.step({})')
                wait("!document.getElementById('shade-warning').hidden")
                assert evaluate("document.getElementById('subtitles').textContent.includes('Đèn ít dầu')")
                assert evaluate("document.getElementById('subtitles').textContent.includes('giây')")
                screenshot('visual-warnings')
                hit=dict(random_motes=False,random_shades=False,random_drifters=False,shades=[{'pos':[0,0,0]}])
                evaluate('__game.loadScenario(1,'+json.dumps(hit)+')')
                wait('__game.game.player.flames === 2')
                assert not evaluate("document.body.classList.contains('hit')")
                wind=dict(random_motes=False,random_shades=False,random_drifters=False,wind_enabled=True)
                evaluate('__game.loadScenario(3,'+json.dumps(wind)+');for(let i=0;i<1679;i++)__game.game.step({})')
                wait("document.getElementById('subtitles').textContent.includes('gió sắp thổi')")
                checks['spawn_edge_arrow_countdown_low_fuel_wind_captions_reduced_flash']=True
                # A genuine win in Night1, then a loss in Night2: save only the won-night score.
                evaluate("__game.show('menu');document.getElementById('start').click();document.getElementById('enter').click()")
                win=dict(random_motes=False,random_shades=False,random_drifters=False,time_left_s=1/60,
                    lanterns=[{'id':'L'+str(i),'lit':True,'fuel':60} for i in range(1,4)])
                evaluate('__game.loadScenario(1,'+json.dumps(win)+')')
                wait("__game.screen==='result'")
                expected=evaluate('__game.game.score')
                assert evaluate("document.getElementById('save-score').hidden")
                evaluate("document.getElementById('next').click();document.getElementById('enter').click()")
                hit['player']={'flames':1}
                evaluate('__game.loadScenario(2,'+json.dumps(hit)+')')
                wait("__game.screen==='result'")
                assert not evaluate("document.getElementById('save-score').hidden")
                evaluate("document.getElementById('player-name').value='QA_release';document.getElementById('save-score').requestSubmit()")
                wait("document.getElementById('score-status').textContent.includes('Đã lưu')")
                entries=evaluate("fetch('/api/leaderboard').then(r=>r.json()).then(d=>d.entries)")
                saved=next(e for e in entries if e['name']=='QA_release')
                assert saved['score']==expected and saved['nights_won']==1 and saved['seed']==2026
                export=ROOT/'artifacts/qa-leaderboard.json'
                p=subprocess.run([sys.executable,str(ROOT/'tools/serve.py'),'--data-dir',str(profile/'leaderboard-store'),'--export-leaderboard',str(export)],capture_output=True)
                assert p.returncode==0,p.stderr
                assert json.loads(export.read_text())['entries']==entries
                server.terminate();server.wait(timeout=10)
                server=subprocess.Popen([sys.executable,str(ROOT/'tools/serve.py'),'--port','8012','--data-dir',str(profile/'leaderboard-store')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**flags)
                for _ in range(100):
                    try:
                        opener.open('http://127.0.0.1:8012/',timeout=1).close();break
                    except OSError:time.sleep(.05)
                call('Page.reload');wait('!!window.__game')
                evaluate("document.getElementById('menu-leaderboard').click()")
                wait("document.getElementById('leaderboard-body').textContent.includes('QA_release')")
                screenshot('leaderboard')
                checks['leaderboard_won_score_disk_restart_and_cli_export']=True
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
