#!/usr/bin/env python3
"""Execute a checked-in plan sequentially; never silently skip failures."""
import argparse
import json
import time
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--wait-for', type=Path, action='append', default=[])
    p.add_argument('--keep-going', action='store_true')
    p.add_argument('--state', type=Path)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    plan = json.loads(args.plan.read_text())
    from simple_evals.runtime import atomic_json
    states = []
    failures = []
    for dependency in args.wait_for:
        job = json.loads(dependency.read_text())
        while True:
            command_line = subprocess.run(['ps', '-p', str(job['pid']), '-o', 'command='], capture_output=True, text=True).stdout
            if str(Path(__file__).resolve()) not in command_line:
                break
            if args.state: atomic_json(args.state, [{'status': 'waiting', 'dependency': str(dependency), 'pid': job['pid']}])
            time.sleep(5)
    for stage in plan['stages']:
        command = [sys.executable, '-m', 'simple_evals', *stage['args']]
        output = Path(stage['args'][stage['args'].index('--output') + 1])
        if args.resume and (output / 'manifest.json').exists():
            command.append('--resume')
        print(stage['name'], '\n', ' '.join(command), flush=True)
        if not args.dry_run:
            state = {'name': stage['name'], 'command': command, 'status': 'running'}
            states.append(state)
            if args.state: atomic_json(args.state, states)
            try:
                process = subprocess.run(command)
                state['returncode'] = process.returncode
                state['status'] = 'completed' if process.returncode == 0 else 'failed'
            except KeyboardInterrupt:
                state['status'] = 'interrupted'
                if args.state: atomic_json(args.state, states)
                raise
            if args.state: atomic_json(args.state, states)
            details = Path(__file__).with_name('analyze_complete_splits.py')
            if details.exists(): subprocess.run([sys.executable, str(details)], check=True)
            report = Path(__file__).with_name('summarize_experiments.py')
            if report.exists(): subprocess.run([sys.executable, str(report)], check=True)
            if state['status'] == 'failed':
                failures.append(stage['name'])
                if not args.keep_going: raise SystemExit(process.returncode)
    if failures: raise SystemExit(1)


if __name__ == '__main__': main()
