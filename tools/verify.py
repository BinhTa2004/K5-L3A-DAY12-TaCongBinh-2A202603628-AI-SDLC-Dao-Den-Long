"""Verification gate. Evidence is generated only by real executions."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from headless import simulate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['phase-1', 'phase-2'], required=True)
    args = parser.parse_args()
    destination = ROOT / 'docs/proof' / args.phase
    destination.mkdir(parents=True, exist_ok=True)
    process = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT, capture_output=True, text=True)
    (destination / 'tests.txt').write_text(process.stdout + process.stderr, encoding='utf-8')
    contract = json.loads((ROOT / 'game.contract.json').read_text())
    samples = []
    for night in range(1, 2 if args.phase == 'phase-1' else 4):
        scenario = dict(random_motes=False, random_shades=False, random_drifters=False,
                        shades=[], drifters=[], player={'invuln_ticks': 30000})
        options = dict(contract=contract, seed=2026, night=night, ticks=21600,
                       snapshotEvery=10, scenario=scenario, inputs={})
        start = time.perf_counter()
        output = simulate(options)
        elapsed = time.perf_counter() - start
        identical = output == simulate(options)
        (destination / f'night-{night}.jsonl').write_text(output, encoding='utf-8', newline='\n')
        samples.append(dict(night=night, elapsed_seconds=elapsed, deterministic=identical,
                            sha256=hashlib.sha256(output.encode()).hexdigest(), end=json.loads(output.splitlines()[-1])))
    report = dict(phase=args.phase, platform=platform.platform(), python=platform.python_version(),
        core_sha256=hashlib.sha256((ROOT/'src/core.js').read_bytes()).hexdigest(),
        contract_sha256=hashlib.sha256((ROOT/'game.contract.json').read_bytes()).hexdigest(),
        tests_exit_code=process.returncode, headless=samples)
    report['passed'] = process.returncode == 0 and all(s['deterministic'] and s['elapsed_seconds'] <= 30 for s in samples)
    (destination / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(process.stdout + process.stderr)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
