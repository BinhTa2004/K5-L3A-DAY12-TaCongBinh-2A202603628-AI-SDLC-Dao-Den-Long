"""Run the exact browser simulation in QuickJS, without a window or GPU."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def simulate(options):
    import quickjs
    context = quickjs.Context()
    context.eval((ROOT / 'src/core.js').read_text(encoding='utf-8'))
    return context.eval('Lantern.run(' + json.dumps(options, allow_nan=False) + ')')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--night', type=int, required=True)
    parser.add_argument('--ticks', type=int, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--scenario', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--snapshot-every', type=int, default=10)
    args = parser.parse_args()
    try:
        def read(path):
            return json.loads(path.read_text(encoding='utf-8-sig')) if path else {}
        options = dict(contract=read(ROOT / 'game.contract.json'), seed=args.seed,
                       night=args.night, ticks=args.ticks, snapshotEvery=args.snapshot_every,
                       scenario=read(args.scenario), inputs=read(args.inputs))
        result = simulate(options)
    except (ValueError, OSError) as exc:
        print(f'Invalid input: {exc}', file=sys.stderr)
        return 2
    except ImportError:
        print('Install dependencies: python3 -m pip install -r requirements.txt', file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2 if 'ContractError' in str(exc) else 1
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result, encoding='utf-8', newline='\n')
    except OSError as exc:
        print(f'Cannot write output: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
