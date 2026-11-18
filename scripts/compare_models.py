"""Sequential model comparison using the same evaluation configuration and seeds."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models', required=True, help='Comma-separated model IDs')
    p.add_argument('--eval', default='mmlu')
    p.add_argument('--backend', default='mlx')
    p.add_argument('--output', type=Path, required=True)
    size=p.add_mutually_exclusive_group()
    size.add_argument('--examples', type=int, default=5)
    size.add_argument('--full', action='store_true')
    p.add_argument('--resume', action='store_true')
    args, extra=p.parse_known_args()
    args.output.mkdir(parents=True,exist_ok=True)
    rows=[]
    failures=[]
    for model in args.models.split(','):
        slug=re.sub(r'[^a-zA-Z0-9._-]+','-',model)+'-'+hashlib.sha256(model.encode()).hexdigest()[:8]
        output=args.output/slug
        command=[sys.executable,'-m','simple_evals','--backend',args.backend,'--model',model,
                 '--eval',args.eval,'--output',str(output),*extra]
        command+=['--full'] if args.full else ['--examples',str(args.examples)]
        if args.resume and (output/'manifest.json').exists():command.append('--resume')
        result=subprocess.run(command)
        if result.returncode:failures.append(model)
        if (output/'summary.json').exists():
            for row in json.loads((output/'summary.json').read_text()):
                rows.append({'model':model,**row})
        if rows:
            with (args.output/'comparison.csv').open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    (args.output/'comparison.json').write_text(json.dumps({'results':rows,'failed_models':failures},indent=2)+'\n')
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
