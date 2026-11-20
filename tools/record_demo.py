"""Record actual timed Chrome frames and actual command output into an MP4 demo."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from uuid import uuid4
from cdp import BrowserSession,ROOT


def main():
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('ffmpeg is required for recording')
    frames=ROOT/'artifacts'/('demo-frames-'+str(uuid4()));frames.mkdir(parents=True)
    output=ROOT/'docs/demo/demo.mp4';output.parent.mkdir(parents=True,exist_ok=True)
    count=0;fps=6;parts=[]
    with BrowserSession() as browser:
        browser.navigate();browser.wait('!!window.__game')
        def caption(text):
            browser.evaluate("(()=>{let e=document.getElementById('demo-caption');if(!e){e=document.createElement('div');e.id='demo-caption';e.style.cssText='position:fixed;bottom:175px;left:24px;max-width:80vw;background:#0e1430ed;color:#F5F1E6;font:20px/1.5 system-ui;padding:12px 18px;z-index:9999;border:1px solid #F2C14E;border-radius:6px;pointer-events:none';document.body.append(e)}e.textContent="+json.dumps(text)+"})()")
        def record(seconds):
            nonlocal count
            start=time.monotonic()
            for i in range(round(seconds*fps)):
                wait=start+i/fps-time.monotonic()
                if wait>0:time.sleep(wait)
                data=browser.call('Page.captureScreenshot',{'format':'jpeg','quality':72})['data']
                (frames/f'frame{count:05d}.jpg').write_bytes(base64.b64decode(data));count+=1
        def proof(title,text):
            browser.evaluate("(()=>{let e=document.getElementById('demo-proof');if(!e){e=document.createElement('section');e.id='demo-proof';e.style.cssText='position:fixed;inset:0;background:#0E1430;color:#F5F1E6;padding:35px;z-index:10000;font:22px/1.5 system-ui;overflow:auto';e.innerHTML='<h1 style=\"font:36px Georgia;color:#F2C14E\"></h1><pre style=\"white-space:pre-wrap;font:20px/1.5 monospace\"></pre>';document.body.append(e)}e.querySelector('h1').textContent="+json.dumps(title)+";e.querySelector('pre').textContent="+json.dumps(text)+"})()")
        def command(command,seconds):
            lines=[]
            process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            def reader():
                for line in process.stdout:lines.append(line.rstrip())
            worker=threading.Thread(target=reader,daemon=True);worker.start()
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                proof('KIỂM CHỨNG THỰC TẾ · CONTRACT 1.3',' '.join(command)+'\n\n'+'\n'.join(lines[-15:]))
                record(1)
            process.wait(timeout=60);worker.join(timeout=2)
            if process.returncode:raise RuntimeError('\n'.join(lines))
            proof('KẾT QUẢ LỆNH CHẠY THẬT',' '.join(command)+'\n\n'+'\n'.join(lines[-12:]))
            record(3)
            return lines
        caption('Đảo Đèn Lồng v1.0.0 · Bản chơi thực tế · Contract 1.3');record(4);parts.append('menu')
        browser.evaluate("document.getElementById('start').click()")
        caption('Giữ đảo sáng tới bình minh · Đèn có dầu và có thể tắt');record(3)
        browser.evaluate("document.getElementById('enter').click()")
        caption('Input thật: đi, nhặt đom đóm, nhảy và lướt')
        browser.key('KeyW','w');record(2);browser.key('KeyW','w',False)
        browser.key('Space',' ');record(1);browser.key('Space',' ',False)
        browser.key('ShiftLeft','Shift');record(1);browser.key('ShiftLeft','Shift',False)
        browser.key('KeyE','e');record(1);browser.key('KeyE','e',False)
        record(4);parts.append('live keyboard gameplay')
        browser.key('Escape','Escape');browser.key('Escape','Escape',False);record(2)
        browser.evaluate("document.getElementById('pause-settings').click()")
        caption('Đổi phím, giảm chuyển động, chữ lớn và bảng màu được lưu')
        record(3)
        browser.evaluate("for(const id of ['colorblind','reduced-motion']){const e=document.getElementById(id);e.checked=true;e.dispatchEvent(new Event('change'))}document.getElementById('keybindings').scrollIntoView()")
        record(4);parts.append('accessibility')
        browser.navigate('/?benchmark=1&seed=42&duration=30');browser.wait('!!window.__bench && __bench.firstFrame!==null')
        caption('Cảnh chuẩn: 200 Bóng Mực + 100 đom đóm · Số đo 30 giây riêng ở phần sau')
        record(8);parts.append('standard benchmark scene preview')
        browser.navigate();browser.wait('!!window.__game')
        browser.evaluate("__game.show('pause')")
        command([sys.executable,'-m','unittest','discover','-s','tests','-v'],8);parts.append('actual unit test execution')
        lines=command([sys.executable,'tools/headless.py','--seed','42','--night','1','--ticks','600','--out','artifacts/demo-headless.jsonl'],2)
        text=(ROOT/'artifacts/demo-headless.jsonl').read_text(encoding='utf-8').splitlines()
        snapshot=next(json.loads(line) for line in reversed(text) if json.loads(line)['type']=='snapshot')
        summary={key:snapshot[key] for key in ['tick','sim_tick','state','time_left_s','score','motes_active']}
        proof('HEADLESS · KẾT QUẢ TỪ LỆNH VỪA CHẠY','Dòng end nguyên văn:\n'+text[-1]+'\n\nTóm tắt snapshot cuối (đọc từ cùng JSONL):\n'+json.dumps(summary,indent=2));record(5);parts.append('actual headless execution')
        benchmark=json.loads((ROOT/'bench.json').read_text());soak=json.loads((ROOT/'soak.json').read_text())
        proof('BENCHMARK 30 GIÂY · SỐ ĐO CHẠY RIÊNG',json.dumps(benchmark,ensure_ascii=False,indent=2));record(8)
        proof('SOAK · 10 ĐÊM TRONG CÙNG TIẾN TRÌNH',json.dumps(soak,ensure_ascii=False,indent=2));record(6)
        verification=json.loads((ROOT/'docs/proof/phase-4/report.json').read_text())
        proof('BẰNG CHỨNG THEO PHASE', 'phase-1 → phase-2 → phase-3 → phase-4\n\nUnit + regression: đạt\n15 scenario headless: '+str(all(x['passed'] for x in verification['features']))+'\nOutput tất định: '+str(all(x['deterministic'] for x in verification['headless']))+'\n\nAGENTS.md · skill verify-game · CI\nADR-003 · CHANGELOG.md · docs/retro.md\n\nVideo này quay frame trình duyệt theo thời gian thực.\nBenchmark được đo riêng, không trong lúc quay.')
        record(6);parts.append('actual benchmark/soak reports and harness')
        if browser.errors:raise RuntimeError(browser.errors)
    subprocess.run([ffmpeg,'-y','-hide_banner','-loglevel','error','-framerate',str(fps),'-i',str(frames/'frame%05d.jpg'),'-vf','fps=24','-c:v','libx264','-preset','fast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    probe=shutil.which('ffprobe') or str(Path(ffmpeg).with_name('ffprobe.exe' if sys.platform=='win32' else 'ffprobe'))
    result=json.loads(subprocess.check_output([probe,'-v','error','-show_entries','format=duration','-of','json',str(output)],text=True))
    duration=float(result['format']['duration'])
    assert 0<duration<300
    metadata=dict(duration_s=duration,bytes=output.stat().st_size,capture_fps=fps,encoded_fps=24,frames=count,parts=parts,audio=False,note='Real timed Chrome frames; actual commands, seeded QA benchmark preview; benchmark timing was measured separately.')
    (ROOT/'docs/demo/capture.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':main()
