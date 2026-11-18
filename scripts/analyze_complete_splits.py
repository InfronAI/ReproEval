"""Describe complete-split checkpoints without pretending partial runs are complete."""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from simple_evals.common import ANSWER_PATTERN_MULTICHOICE

ROOT = Path(__file__).resolve().parents[1]


def main():
    run = ROOT / 'experiments/runs/m1-complete-small'
    out = ROOT / 'experiments/complete_split_analysis'
    out.mkdir(parents=True, exist_ok=True)
    totals = {'gpqa': 198, 'humaneval': 164}
    lines = ['# Complete-split diagnostics', '', 'These tables describe saved checkpoints. A partial count is not a completed benchmark result.', '']
    for name in totals:
        groups = defaultdict(list)
        details = []
        for path in sorted((run / name / 'checkpoints').glob('*.json')):
            item = json.loads(path.read_text())
            result = item['result']['value']
            group = item['input'].get('High-level domain', 'all tasks')
            score = result['score']
            row = {'index':item['index'],'group':group,'score':score}
            if name == 'gpqa':
                text = result['convo'][-1]['content']
                match = re.search(ANSWER_PATTERN_MULTICHOICE, text)
                row['answer_extracted'] = bool(match)
            details.append(row); groups[group].append(score)
        complete = len(details) == totals[name] and (run / name / 'metrics.json').exists()
        lines += [f'## {name}: {len(details)}/{totals[name]} tasks — {"complete" if complete else "in progress"}', '', '| Group | Scored tasks | Mean score |', '|---|---:|---:|']
        for group, values in sorted(groups.items()):
            lines.append(f'| {group} | {len(values)} | {sum(values)/len(values):.6f} |')
        if name == 'gpqa':
            missing = sum(not r['answer_extracted'] for r in details)
            lines += ['', f'{missing} recorded responses lacked the required final answer marker. These are failures under the original answer extraction rule.']
            extracted = [r for r in details if r['answer_extracted']]
            if extracted:
                lines += [f'Among the {len(extracted)} responses with an extractable answer, {sum(r["score"] for r in extracted):g} were correct. This conditional diagnostic excludes format failures and must not replace the benchmark score.']
        metrics_path = run / name / 'metrics.json'
        if complete:
            metrics = json.loads(metrics_path.read_text())
            correct = sum(row['score'] for row in details)
            lines += ['', f'Overall: {correct:g}/{len(details)} correct ({metrics["score"]:.2%}); recorded evaluation wall time: {metrics["wall_seconds"]:.1f} seconds.']
            if name == 'humaneval':
                lines += ['This is observed pass@1 from one program per task. Larger-k success rates require additional independent generations and cannot be estimated from this run.']
        if details:
            with (out / f'{name}.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=details[0]);w.writeheader();w.writerows(details)
        lines += ['']
    lines += ['Each task has one generated answer/program in this protocol. GPQA uses a single choice permutation and HumanEval reports pass@1; no pass@5 or paper-scale sampling claim is made. Scores are descriptive for these fixed splits and local model settings.']
    (out/'analysis.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__': main()
