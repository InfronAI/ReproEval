"""Generate portable analyses from saved measurements, without calling a model."""
import csv
import html
import json
from pathlib import Path
from .runtime import atomic_json


def analyze(run_dir):
    root = Path(run_dir)
    manifest = json.loads((root / 'manifest.json').read_text())
    rows = []
    for name in manifest['config']['evals']:
        folder = root / name
        metrics_path = folder / 'metrics.json'
        status = 'pending'
        score = None
        metric = 'score'
        if metrics_path.exists():
            values = json.loads(metrics_path.read_text())
            metric = 'f1_score' if name == 'drop' else 'score'
            score = values.get(metric)
            status = 'completed'
        elif (folder / 'error.json').exists():
            status = 'failed'
        n = len(list((folder / 'checkpoints').glob('*.json')))
        traces = [json.loads(p.read_text()) for p in (folder / 'traces').glob('*.json')]
        tokens = sum(t.get('usage', {}).get('output_tokens', 0) for t in traces)
        seconds = sum(t.get('seconds', 0) for t in traces)
        rows.append(dict(evaluation=name, status=status, examples=n, metric=metric, score=score,
                         generated_tokens=tokens, inference_seconds=round(seconds, 3),
                         token_limit_hits=sum(t.get('truncated', False) for t in traces)))
    atomic_json(root / 'summary.json', rows)
    with (root / 'summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    lines = ['# Local experiment analysis', '',
             f"Candidate: `{manifest['config']['model']}`. Grader: `{manifest['config']['grader_model']}`.", '',
             '**Scope: ' + ('full selected datasets' if manifest['config']['full'] else 'bounded subset') + '. These are local-model measurements, not the original paper results.**', '',
             '| Evaluation | State | Examples | Metric | Value | Output tokens | Limit hits |',
             '|---|---|---:|---|---:|---:|---:|']
    for row in rows:
        val = 'undefined' if row['score'] is None else f"{row['score']:.6f}"
        lines.append(f"| {row['evaluation']} | {row['status']} | {row['examples']} | {row['metric']} | {val} | {row['generated_tokens']} | {row['token_limit_hits']} |")
    lines += ['', '## Interpretation and limits', '',
              '- Small samples do not estimate full-benchmark performance reliably; no leaderboard comparison is valid.',
              '- The local grader is not the paper grader. HealthBench Meta measures its agreement with physician labels; an undefined balanced F1 means that the subset lacks a required class, not a score of zero.',
              '- DROP F1 is on the original 0–100 scale. Most other metrics are on 0–1; do not average across benchmarks.',
              '- Token limit hits can remove final answers and lower scores. Full prompts are retained; inputs are never silently truncated.',
              '- BrowseComp without --browse is a closed-book baseline, not a browsing-agent replication.',
              '- Calls include any failed format retries. Completed checkpoint counts refer to scored examples, not API calls.',
              '- Seeds, source hashes, dependency versions, model revisions, dataset hashes, raw traces, conversations and per-example checkpoints are saved with this run.', '']
    (root / 'analysis.md').write_text('\n'.join(lines))
    head = '<!doctype html><meta charset="utf-8"><title>Simple Evals · Local results</title><style>body{font:16px system-ui;background:#0c1423;color:#dbe5f2;max-width:1100px;margin:60px auto;padding:20px}a{color:#7dd3fc}table{width:100%;border-collapse:collapse}td,th{padding:15px;text-align:left;border-bottom:1px solid #334155}small{color:#94a3b8}</style>'
    body = '<h1>Simple Evals · Apple Silicon</h1><p>Actual local model measurements · ' + ('full selected datasets' if manifest['config']['full'] else 'bounded subset, not paper results') + '</p><p><small>' + html.escape(manifest['config']['model']) + '</small></p><table><tr><th>Evaluation</th><th>State</th><th>Examples</th><th>Metric</th><th>Value</th></tr>'
    for row in rows:
        value = 'undefined' if row['score'] is None else f"{row['score']:.4f}"
        link = f"<a href='{html.escape(row['evaluation'])}/report.html'>{html.escape(row['evaluation'])}</a>" if row['status'] == 'completed' else html.escape(row['evaluation'])
        body += f"<tr><td>{link}</td><td>{row['status']}</td><td>{row['examples']}</td><td>{row['metric']}</td><td>{value}</td></tr>"
    body += '</table><p>Raw records: <a href="summary.json">JSON</a> · <a href="summary.csv">CSV</a> · <a href="analysis.md">Analysis</a> · <a href="manifest.json">Provenance</a></p>'
    (root / 'index.html').write_text(head + body)
    return rows
