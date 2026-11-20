"""Real 1280x720 browser benchmark: 3s warmup, requested measurement, automatic exit."""
import time
PROCESS_START=time.perf_counter()
import argparse
import json
import math
from pathlib import Path
import platform
import sys
from cdp import BrowserSession,ROOT


def metrics(dts):
    n=len(dts)
    if not n or any(not math.isfinite(dt) or dt<=0 for dt in dts):raise ValueError('No valid frames')
    ordered=sorted(dts);k=max(1,math.ceil(.01*n))
    return dict(avg_fps=1000*n/sum(dts),p1_low_fps=1000/(sum(ordered[-k:])/k),frame_ms_p95=ordered[math.ceil(.95*n)-1],frames=n)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--duration',type=float,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--headless',action='store_true',help='Offscreen QA only; default is a normal non-fullscreen window')
    args=parser.parse_args()
    if args.duration<=0:parser.error('duration must be positive')
    with BrowserSession(headless=args.headless,unlimited=True) as browser:
        browser.navigate(f'/?benchmark=1&seed={args.seed}&duration={args.duration}')
        browser.wait('!!window.__bench && __bench.firstFrame!==null')
        load_ms=(time.perf_counter()-PROCESS_START)*1000
        browser.wait('__bench.done',timeout=args.duration+20)
        dts=browser.evaluate('__bench.dts')
        measured=metrics(dts)
        scene=browser.evaluate('({width:innerWidth,height:innerHeight,shades:__game.game.shades.length,motes:__game.game.motes.length,states:[...new Set(__game.game.shades.map(s=>s.state))],player:__game.game.player.pos,lamps:__game.game.lanterns.map(l=>({id:l.id,lit:l.lit,fuel:__game.game.fuel(l)})),input_disabled:true,warmup_s:3,duration_s:'+str(args.duration)+'})')
        assert scene['width']==1280 and scene['height']==720 and scene['shades']==200 and scene['motes']==100
        assert scene['states']==['wander'] and scene['player']==[0,0,0]
        assert sum(l['lit'] for l in scene['lamps'])==3 and all(l['fuel']==100 for l in scene['lamps'][:3])
        assert not browser.errors,browser.errors
        gpu=browser.evaluate("(()=>{const gl=__game.renderer.getContext(),x=gl.getExtension('WEBGL_debug_renderer_info');return x?gl.getParameter(x.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)})()")
        version=browser.call('Browser.getVersion')['product']
        report=dict(contract_version='1.3',**measured,load_ms=load_ms,peak_mem_mb=None,vsync_off=True,renderer='Three.js r160 / '+version+' / '+gpu,os=platform.platform())
        proof=ROOT/'docs/proof/phase-4';proof.mkdir(parents=True,exist_ok=True)
        (proof/'bench-frames.json').write_text(json.dumps(dts),encoding='utf-8')
        (proof/'bench-scene.json').write_text(json.dumps(scene,indent=2),encoding='utf-8')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
    return 0


if __name__=='__main__':
    sys.exit(main())
