#!/usr/bin/env python3
"""Start, inspect, or stop a durable sequential local experiment plan."""
import argparse
import hashlib
import shutil
import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def alive(pid):
    command = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True).stdout
    return str(ROOT / 'scripts/run_plan.py') in command


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['start', 'status', 'stop'])
    p.add_argument('--plan', type=Path, default=Path('experiments/plans/full-reference.json'))
    p.add_argument('--resume', action='store_true')
    p.add_argument('--wait-for', type=Path, action='append', default=[], help='Wait for an existing managed job.json before starting')
    p.add_argument('--keep-going', action='store_true', help='Record failed stages and run the remaining independent stages')
    args = p.parse_args()
    os.chdir(ROOT)
    state_dir = ROOT / 'experiments/jobs' / args.plan.stem
    state_dir.mkdir(parents=True, exist_ok=True)
    record = state_dir / 'job.json'
    previous = json.loads(record.read_text()) if record.exists() else None
    if args.action == 'status':
        print(json.dumps({'job': previous, 'process_alive': bool(previous and alive(previous['pid'])),
                         'stage_status': json.loads((state_dir / 'stages.json').read_text()) if (state_dir / 'stages.json').exists() else None}, indent=2)); return
    if args.action == 'stop':
        if previous and alive(previous['pid']): os.killpg(previous['pid'], signal.SIGINT)
        return
    if previous and alive(previous['pid']): raise SystemExit('This plan is already running')
    plan_sha256 = hashlib.sha256(args.plan.read_bytes()).hexdigest()
    if args.resume and previous and previous.get('code_snapshot'):
        if previous['plan_sha256'] != plan_sha256:
            raise SystemExit('Plan changed: use a new plan/output, or restore the original plan to resume')
        code_snapshot = Path(previous['code_snapshot'])
        frozen_plan = Path(previous['frozen_plan'])
    else:
        snapshot = ROOT / '.cache/jobs' / args.plan.stem / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        code_snapshot = snapshot / 'src'
        shutil.copytree(ROOT / 'src/simple_evals', code_snapshot / 'simple_evals',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        frozen_plan = snapshot / 'plan.json'
        shutil.copy2(args.plan, frozen_plan)
    command = [sys.executable, '-u', str(ROOT / 'scripts/run_plan.py'), str(frozen_plan), '--state', str(state_dir / 'stages.json')]
    if args.resume: command.append('--resume')
    if args.keep_going: command.append('--keep-going')
    for dependency in args.wait_for: command.extend(['--wait-for', str(dependency)])
    with (state_dir / 'console.log').open('a') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
                                   env={**os.environ, 'PYTHONPATH': str(code_snapshot)})
    data = {'pid': process.pid, 'plan': str(args.plan), 'command': command, 'started_at': datetime.now(timezone.utc).isoformat(),
            'log': str((state_dir / 'console.log').relative_to(ROOT)),
            'code_snapshot': str(code_snapshot), 'frozen_plan': str(frozen_plan), 'plan_sha256': plan_sha256}
    record.write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(data, indent=2))


if __name__ == '__main__': main()
