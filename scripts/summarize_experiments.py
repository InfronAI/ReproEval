"""Regenerate the repository-level report from real run artifacts."""
import json
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = []
    active_outputs = set()
    for job_path in (ROOT / 'experiments/jobs').glob('*/job.json'):
        job = json.loads(job_path.read_text())
        command = subprocess.run(['ps', '-p', str(job['pid']), '-o', 'command='], capture_output=True, text=True).stdout
        state_path = job_path.with_name('stages.json')
        if str(ROOT / 'scripts/run_plan.py') not in command or not state_path.exists():
            continue
        for stage in json.loads(state_path.read_text()):
            args = stage.get('command', [])
            if stage['status'] == 'running' and '--output' in args:
                active_outputs.add((ROOT / args[args.index('--output') + 1]).resolve())
    for manifest_path in sorted((ROOT / 'experiments/runs').glob('*/manifest.json')):
        run = manifest_path.parent
        manifest = json.loads(manifest_path.read_text())
        config = manifest['config']
        if manifest.get('source_changed_during_run'):
            status = 'development / excluded'
        else:
            status = 'running' if run.resolve() in active_outputs else manifest.get('status', 'in progress')
        summaries = json.loads((run / 'summary.json').read_text()) if (run / 'summary.json').exists() else []
        if not summaries:
            summaries = [dict(evaluation=name, status='pending', metric='score', score=None, token_limit_hits=0) for name in config['evals']]
        for row in summaries:
            checkpoints = run / row['evaluation'] / 'checkpoints'
            # A fresh clone stores large raw checkpoints in verified archives.
            # Preserve the recorded summary until those archives are restored.
            if checkpoints.exists():
                row['examples'] = len(list(checkpoints.glob('*.json')))
            else:
                row['examples'] = row.get('examples', 0)
            if row['status'] == 'pending' and status == 'running' and row['examples']:
                row['status'] = 'running'
            if row['status'] == 'pending' and status == 'ended_early':
                row['status'] = 'stopped early' if row['examples'] else 'not run'
            repeats = config['n_repeats'] or (10 if config.get('paper_repeats') and row['evaluation'] in ('math', 'gpqa') else 1)
            row = dict(row, run=run.name, run_status=status, full=config['full'],
                       samples_per_task=config['samples_per_task'], repeats=repeats)
            rows.append(row)
    cache = json.loads((ROOT / 'experiments/cache_performance.json').read_text())
    measurements = cache['measurements']
    baseline = statistics.mean(x['seconds'] for x in measurements if not x['prefix_cache'] and x['repetition'] > 0)
    optimized = statistics.mean(x['seconds'] for x in measurements if x['prefix_cache'] and x['repetition'] > 0)
    now = datetime.now(timezone.utc).isoformat()
    text = ['# Experiment report / 实验报告', '', f'Generated from saved artifacts at {now}.', '',
            '**These are actual local open-weight model experiments. They do not reproduce the historical paper models. Full-paper completion is not claimed.**', '',
            '## Environment and protocol', '',
            '- Host: Apple M1 Pro, 16 GB unified memory, macOS 26.6.1, arm64 Python 3.11.16.',
            '- Default candidate: Qwen2.5-0.5B-Instruct, MLX 4-bit; grader: Qwen2.5-3B-Instruct, MLX 4-bit. Per-run manifests override these where explicitly configured.',
            '- No paid model APIs were used. Model revision SHAs, package versions, source snapshots, dataset receipts, raw responses and scored inputs are stored under each run.',
            '- Native MLX / Metal uses one worker. Candidate and grader have separate bounded KV caches. Token caps and truncations are recorded.',
            '- Dataset inventory: [measured row counts](dataset_inventory.json), [download receipts](datasets.json). The complete public source collection is cached locally under `.cache/datasets`; full weight/data binaries are not committed.', '',
            '## Executed coverage', '', '[GPQA domain and HumanEval task diagnostics](complete_split_analysis/analysis.md) are generated separately; incomplete counts stay explicitly marked.', '',
            '| Run | Evaluation | Run state | Stage state | Scored rows | Scope | Metric | Value | Limit hits |',
            '|---|---|---|---|---:|---|---|---:|---:|']
    termination_path = ROOT / 'experiments/termination.json'
    if termination_path.exists():
        termination = json.loads(termination_path.read_text())
        text[4:4] = [
            '**Ended early at the user’s request / 已按用户要求提前结束测试。**', '',
            f'Stopped at {termination["ended_at"]}. No automatic continuation is scheduled. All results and checkpoints are preserved. See the [termination record](termination.json).', '',
            'The first planned stage completed 8 of its 12 evaluation entries. HealthBench retained 389 checkpoints before a grader-format failure; HealthBench Hard retained 123 checkpoints before the user-requested stop. Remaining evaluations and plan stages were not completed.', '',
        ]
    for row in rows:
        value = 'undefined' if row['score'] is None else f"{row['score']:.6f}"
        scope = ('full split' if row['full'] else 'subset')
        if row['evaluation'] == 'humaneval': scope += f"; {row['samples_per_task']} sample(s)/task"
        if row['evaluation'] == 'gpqa': scope += f"; {row['repeats']} repeat(s)"
        target = "analysis.md" if (ROOT / "experiments/runs" / row["run"] / "analysis.md").exists() else "manifest.json"
        text.append(f"| [{row['run']}](runs/{row['run']}/{target}) | {row['evaluation']} | {row['run_status']} | {row['status']} | {row['examples']} | {scope} | {row['metric']} | {value} | {row['token_limit_hits']} |")
    text += ['', '## Current job states', '', '| Managed plan | Latest recorded stage | State |', '|---|---|---|']
    for state_path in sorted((ROOT / 'experiments/jobs').glob('*/stages.json')):
        states = json.loads(state_path.read_text())
        if states:
            last = states[-1]
            text.append(f"| {state_path.parent.name} | {last.get('name', last.get('dependency', 'waiting'))} | {last['status']} |")
    text += ['', '## Calibration and browsing diagnostics', '']
    for result_path in sorted((ROOT / 'experiments/runs').glob('*/simpleqa_calibration/results.json')):
        data = json.loads(result_path.read_text())
        for item in data['metadata']['example_level_metadata']:
            text.append(f"- `{result_path.parent.parent.name}`: {item['total_draws']} draws, {item['valid_draws']} valid structured outputs, modal frequency {item['modal_frequency']:.3f}, modal answer correct = {item['modal_correct']}. One question is insufficient for population-level calibration claims.")
    for browse_path in sorted((ROOT / 'experiments/runs').glob('*/browsecomp/browse/*.json')):
        data = json.loads(browse_path.read_text())
        events = data['events']
        errors = [event['tool_error'] for event in events if 'tool_error' in event]
        text.append(f"- `{browse_path.parents[2].name}`: {len(events)} tool events; {len(errors)} recorded tool errors. " + ('Errors: ' + '; '.join(errors) if errors else 'Inspect the retained observations for retrieved evidence.'))
    text += ['', '“Scored rows” only counts completed checkpoints. A running stage may already have raw generations but no final score. Development diagnostics are excluded from final conclusions. The initial development run was stopped after discovering missing CSV values and malformed grader output; its retained error records document those findings.', '',
             '## Analysis', '', '[Two-model execution comparison](comparison/m1-models/comparison.csv) uses the same two MMLU questions with both local models. Both scored zero on that tiny pair; this is not evidence for a general ranking.', '',
             '1. The all-evaluator validation uses one item per evaluator and one per MGSM language (22 scored rows if all 12 evaluators finish). It verifies connectivity between real data, local generation, grading and persistence. It cannot establish benchmark accuracy.',
             '2. The complete-small protocol covers all 198 GPQA Diamond questions (one permutation/draw each) and all 164 HumanEval tasks (one generated program each). These are complete splits with reduced repetitions, not the upstream repeated-sampling protocol or the HumanEval paper\'s full sampling study.',
             '3. Tiny-model scores and output-limit hits must be considered together. Missing final-answer formatting may be scored wrong by the original extraction rules. Invalid grader formatting instead produces a visible failure or a bounded, recorded format-repair request.',
             '4. HealthBench uses the local 3B judge. Its clinical rubric decisions are not independently validated as equivalent to the paper grader. HealthBench Meta may have undefined balanced F1 on a one-item subset because a required class is absent.',
             '5. DROP F1 is expressed on a 0–100 scale. Never take a cross-benchmark mean of these raw scores.',
             '6. The closed-book BrowseComp run is a baseline; only runs configured with `--browse` actually use public-web tools. The local agent differs from the unpublished research agent.',
             '7. Calibration retains every scheduled draw and explicitly records invalid/conflicting JSON. Such draws fail the structured-answer pass/consensus metric and are excluded from stated-confidence bins; valid-draw coverage is reported. A one-question 100-draw test exercises frequency estimation, not population calibration.', '',
             '## Measured systems optimization', '',
             f'Four warm repeated-prefix calls averaged **{baseline:.3f} s without prefix caching** and **{optimized:.3f} s with caching** ({baseline/optimized:.1f}× latency ratio). All twelve greedy outputs matched. This is a synthetic 1,636–1,641-input-token microbenchmark, not a claimed whole-suite speedup. Timing depends on system load; the sample size is small.', '',
             '[Raw A/B measurements](cache_performance.json) · [Chart](../docs/assets/cache-performance.svg) · [Script](../scripts/benchmark_cache.py)', '',
             '## Full-scale work and non-reproduced experiments', '',
             'The [full-reference plan](plans/full-reference.json) includes the released suite, ten MATH-500/GPQA repeats, original MATH-5000, 200-sample HumanEval at temperatures 0.2 and 0.8, translated MMLU, 100-draw SimpleQA calibration, three local browser budgets, and physician/reference evaluation. It is substantially larger than the validation run: translated MMLU alone adds 196,588 prompts, and full calibration needs 432,600 candidate generations before grading.', '',
             '**Do not interpret this plan or a running background process as completed experiments.** See the job state and per-run checkpoints for current progress. Historical model training, proprietary agent internals, original human data collection and several original-paper ablations are not available in this repository; see the [paper audit](../docs/PAPER_AUDIT.md).', '',
             '```bash',
             '.venv/bin/python scripts/manage_experiments.py status',
             '.venv/bin/python scripts/summarize_experiments.py',
             '# Resume the same full plan after a clean stop:',
             '.venv/bin/python scripts/manage_experiments.py start --resume',
             '# Explicitly stop the managed full plan:',
             '.venv/bin/python scripts/manage_experiments.py stop', '```', '',
             '## 中文说明', '',
             '以上表格来自实际保存的运行记录。全部评测入口的小样本验证、完整数据划分的一次采样、原论文规模的重复实验，是三个不同范围。未完成或失败的实验不会伪造为成功。开发阶段诊断数据保留，但不参与正式结论。全量任务可能需要持续多日，模型评分能力和生成上限也会影响完成率与结论。', '',
             '默认英文 README 与中文 README 均提供数据流图、结构流程图、运行命令和真实终端演示。MP4 配套自动播放 HTML 页面，GitHub README 用自动循环 GIF 兼容展示。', '']
    (ROOT / 'experiments/REPORT.md').write_text('\n'.join(text))
    (ROOT / 'experiments/coverage.json').write_text(json.dumps({'generated_at': now, 'rows': rows}, indent=2)+'\n')
    print('Updated experiments/REPORT.md and coverage.json')


if __name__ == '__main__': main()
