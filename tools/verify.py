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
    feature_checks = []
    if args.phase == 'phase-2':
        for case in json.loads((ROOT/'tests/scenarios/features.json').read_text()):
            options = dict(contract=contract, seed=2026, night=case['night'], ticks=case['ticks'],
                           snapshotEvery=1, scenario=case['scenario'], inputs=case['inputs'])
            output = simulate(options)
            rows = [json.loads(line) for line in output.splitlines()]
            names = {r.get('name') for r in rows if r['type'] == 'event'}
            passed = set(case['events']).issubset(names)
            snapshots = [r for r in rows if r['type'] == 'snapshot']
            final = snapshots[-1]
            observations = {
                'dash': lambda: final['player']['pos'][2] == 2.8,
                'charm': lambda: len([r for r in rows if r.get('name') == 'dash']) == 2 and final['player']['charm_s'] > 0,
                'drifter-steal': lambda: final['player']['carried'] == 7 and final['drifters'][0]['stolen'] == 3,
                'drifter-drop': lambda: final['drifters'] == [] and final['motes_active'] == 3,
                'pause': lambda: final['sim_tick'] == 30 and any(s['state'] == 'paused' for s in snapshots),
                'launch-pad': lambda: final['player']['grounded'] and final['player']['pos'][0] > 42,
                'wind': lambda: any(s['wind']['active'] for s in snapshots) and not final['wind']['active'] and final['player']['pos'] != snapshots[0]['player']['pos'],
                'fall-respawn': lambda: final['player']['flames'] == 2 and final['player']['pos'] == [0,0,0] and len([r for r in rows if r.get('name') == 'player_hit']) == 1,
            }
            passed = passed and observations[case['name']]()
            (destination/(case['name']+'.jsonl')).write_text(output, encoding='utf-8', newline='\n')
            feature_checks.append(dict(name=case['name'], passed=passed))
    for night in range(1, 2 if args.phase == 'phase-1' else 4):
        scenario = dict(player={'invuln_ticks': 30000})
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
        core_sha256=hashlib.sha256((ROOT/'src/core.js').read_text(encoding='utf-8').encode()).hexdigest(),
        contract_sha256=hashlib.sha256((ROOT/'game.contract.json').read_text(encoding='utf-8').encode()).hexdigest(),
        tests_exit_code=process.returncode, headless=samples, features=feature_checks)
    report['passed'] = process.returncode == 0 and all(s['deterministic'] and s['elapsed_seconds'] <= 30 for s in samples) and all(c['passed'] for c in feature_checks)
    (destination / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(process.stdout + process.stderr)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
