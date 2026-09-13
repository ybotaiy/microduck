"""Run frozen, held-out static ball cases for rules and learned controllers."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


# These physical positions are not used as model inputs, training labels, or
# checkpoint-selection cases.  Keep this grid fixed once an evaluation starts.
CASES = [(x, y) for x in (.65, .8, .95) for y in (-.35, -.12, .12, .35)]


def command(python, root, controller, model, out, ball):
    cmd = [str(python), 'sim/experiment.py', '--mode', 'ball', '--seconds', '20',
           '--ball', str(ball[0]), str(ball[1]), '--vision', '--vision-controller', controller,
           '--out', str(out)]
    if controller == 'learned':
        cmd.extend(['--controller-model', str(model)])
    return cmd


def run(args):
    records = []
    for controller in ('rules', 'learned'):
        for index, ball in enumerate(CASES):
            directory = args.out / controller / f'{index:02d}'
            completed = subprocess.run(command(args.python, args.root, controller, args.model,
                                               directory, ball), cwd=args.root,
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            summary_path = directory / 'summary.json'
            summary = json.loads(summary_path.read_text()) if summary_path.exists() else None
            records.append({'controller': controller, 'case': index, 'ball': ball,
                            'returncode': completed.returncode,
                            'success': bool(summary and summary['success']),
                            'final_distance': summary['final_distance'] if summary else None,
                            'fell': summary['fell'] if summary else None,
                            'touched_ball': summary['touched_ball'] if summary else None,
                            'guard_reason': summary.get('guard_reason') if summary else None,
                            'stderr': completed.stderr[-1000:]})
    counts = {name: sum(row['success'] for row in records if row['controller'] == name)
              for name in ('rules', 'learned')}
    result = {'suite': 'frozen-held-out-static-grid-v1', 'cases_per_controller': len(CASES),
              'counts': counts, 'records': records,
              'note': 'Static controlled magenta-ball simulation only; this does not measure search, occlusion, clutter, or hardware.'}
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'suite': result['suite'], 'counts': counts}, indent=2))
    if any(row['returncode'] for row in records):
        raise SystemExit('One or more simulator subprocesses failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args())
