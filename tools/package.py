"""Produce a runnable local web build without repository metadata or secrets."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['phase-1', 'phase-2', 'phase-3'], required=True)
    args = parser.parse_args()
    version = json.loads((ROOT/'game.contract.json').read_text())['contract_version']
    if version != {'phase-1':'1.0','phase-2':'1.1','phase-3':'1.2'}[args.phase]:
        parser.error('Checkout the matching phase tag before packaging it')
    out = ROOT/'artifacts'/('dao-den-long-'+args.phase+'.zip')
    out.parent.mkdir(exist_ok=True)
    files = [ROOT/name for name in ['LICENSE', 'CREDITS.md', 'game.contract.json', 'requirements.txt', 'tools/serve.py', 'tools/headless.py']]
    for folder in ['web', 'src', 'vendor']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
    with ZipFile(out, 'w', ZIP_DEFLATED) as z:
        z.writestr('README.md', '# Dao Den Long — '+args.phase+'\n\nRun: python3 tools/serve.py\nOpen http://127.0.0.1:8000 in a WebGL browser. On Windows use python.\n\nWASD / arrows: move; Space: jump; Shift: dash; E: deposit/refuel; Q: pulse; Esc/P: pause. Drag mouse: camera; wheel: zoom.\nKeep 60% of the lamps lit until dawn. Fuel decays; relighting costs 5 motes. Colorblind palette is available in Settings.\n\nFor headless only: python3 -m pip install -r requirements.txt\npython3 tools/headless.py --seed 1 --night 1 --ticks 600 --out run.jsonl\n\nSource, specs, test evidence: https://github.com/BinhTa2004/K5-L3A-DAY12-TaCongBinh-2A202603628-AI-SDLC-Dao-Den-Long\n')
        for p in files:
            z.write(p, p.relative_to(ROOT).as_posix())
    print(out)
