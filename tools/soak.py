"""Ten seeded nights, one process and one QuickJS context; real RSS measurements."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    import psutil
    import quickjs
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--nights',type=int,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.nights<1:parser.error('nights must be positive')
    started=time.perf_counter()
    ctx=quickjs.Context()
    ctx.eval((ROOT/'src/core.js').read_text(encoding='utf-8'))
    ctx.eval('globalThis.contract='+ (ROOT/'game.contract.json').read_text(encoding='utf-8')+';')
    ctx.eval('globalThis.soakGame=new Lantern.Game(contract,'+str(args.seed)+',1);')
    ctx.gc()
    process=psutil.Process()
    start=process.memory_info().rss/1024**2
    ctx.eval('''globalThis.playSoak=function(seed,night){
      const g=soakGame,rand=Lantern.random(seed);let move=[0,0];
      for(let tick=0;tick<g.duration*60&&!['won','lost'].includes(g.state);tick++){
        if(tick%30===0){const a=rand()*Math.PI*2;move=[Math.cos(a),Math.sin(a)];}
        g.step({move,cam_yaw_deg:0,jump:rand()<.05,dash:rand()<.03,pulse:rand()<.02,interact:rand()<.10});
      }
      return g.state;
    };''')
    results=[];errors=[]
    for i in range(args.nights):
        seed=args.seed+i;night=i%3+1
        try:
            if i:ctx.eval(f'soakGame=new Lantern.Game(contract,{seed},{night});')
            results.append(ctx.eval(f'playSoak({seed},{night})'))
        except Exception as exc:
            results.append('crash');errors.append(str(exc))
        ctx.gc()
    ctx.eval(f'soakGame=new Lantern.Game(contract,{args.seed+args.nights-1},{(args.nights-1)%3+1});')
    ctx.gc()
    end=process.memory_info().rss/1024**2
    report=dict(nights=args.nights,crashes=len(errors),results=results,mem_start_mb=round(start,3),mem_end_mb=round(end,3),duration_s=round(time.perf_counter()-started,3))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if errors:print('\n'.join(errors),file=sys.stderr)
    return 0 if not errors and end<=1.2*start else 1


if __name__=='__main__':
    sys.exit(main())
