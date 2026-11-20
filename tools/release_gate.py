"""Validate concrete release artifacts before tagging or publishing."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile
from bench import metrics

ROOT=Path(__file__).resolve().parents[1]


def check():
    proof=ROOT/'docs/proof/phase-4'
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    report=read(proof/'report.json');gui=read(proof/'browser.json');package=read(proof/'package.json')
    bench=read(ROOT/'bench.json');soak=read(ROOT/'soak.json');raw=read(proof/'bench-frames.json')
    calculated=metrics(raw)
    archive=ROOT/'artifacts/dao-den-long-v1.0.0.zip'
    video=ROOT/'docs/demo/demo.mp4'
    ffprobe=shutil.which('ffprobe')
    if not ffprobe:raise RuntimeError('ffprobe is required for release validation')
    duration=float(json.loads(subprocess.check_output([ffprobe,'-v','error','-show_entries','format=duration','-of','json',str(video)],text=True))['format']['duration'])
    checks={
        'contract_1_3':read(ROOT/'game.contract.json')['contract_version']=='1.3',
        'regression_and_headless':report['passed'],
        'evidence_matches_core':report['core_sha256']==hashlib.sha256((ROOT/'src/core.js').read_text(encoding='utf-8').encode()).hexdigest(),
        'gui_all_checks':not gui['runtime_errors'] and all(gui['checks'].values()),
        'benchmark_thresholds':bench['avg_fps']>=60 and bench['p1_low_fps']>=30 and bench['load_ms']<=10000,
        'benchmark_raw_recalculates':all(abs(bench[k]-calculated[k])<1e-8 for k in calculated),
        'soak_thresholds':soak['nights']==10 and soak['crashes']==0 and soak['mem_end_mb']<=1.2*soak['mem_start_mb'],
        'clean_package':package['passed'] and package['archive_sha256']==hashlib.sha256(archive.read_bytes()).hexdigest(),
        'video_under_5_min':0<duration<300,
        'required_documents':all((ROOT/p).is_file() for p in ['README.md','CHANGELOG.md','CREDITS.md','LICENSE','AGENTS.md','.agents/skills/verify-game/SKILL.md','docs/retro.md']),
    }
    with ZipFile(archive) as z:
        checks['no_private_runtime_data']=not any(n.startswith(('.git/','artifacts/')) or n.endswith('.env') for n in z.namelist())
        checks['runtime_modules']=all(n in z.namelist() for n in ['tools/serve.py','tools/leaderboard.py','tools/headless.py','tools/bench.py','tools/soak.py','tools/cdp.py','web/index.html','web/release.js','src/benchmark.js','game.contract.json'])
    result=dict(passed=all(checks.values()),checks=checks,video_duration_s=duration,
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),video_sha256=hashlib.sha256(video.read_bytes()).hexdigest())
    (proof/'release-gate.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    result=check();print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
