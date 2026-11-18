# Experiment report / 实验报告

Generated from saved artifacts at 2026-11-17T15:31:48.452251+00:00.

**Ended early at the user’s request / 已按用户要求提前结束测试。**

Stopped at 2026-11-17T15:31:15.135655+00:00. No automatic continuation is scheduled. All results and checkpoints are preserved. See the [termination record](termination.json).

The first planned stage completed 8 of its 12 evaluation entries. HealthBench retained 389 checkpoints before a grader-format failure; HealthBench Hard retained 123 checkpoints before the user-requested stop. Remaining evaluations and plan stages were not completed.

**These are actual local open-weight model experiments. They do not reproduce the historical paper models. Full-paper completion is not claimed.**

## Environment and protocol

- Host: Apple M1 Pro, 16 GB unified memory, macOS 26.6.1, arm64 Python 3.11.16.
- Default candidate: Qwen2.5-0.5B-Instruct, MLX 4-bit; grader: Qwen2.5-3B-Instruct, MLX 4-bit. Per-run manifests override these where explicitly configured.
- No paid model APIs were used. Model revision SHAs, package versions, source snapshots, dataset receipts, raw responses and scored inputs are stored under each run.
- Native MLX / Metal uses one worker. Candidate and grader have separate bounded KV caches. Token caps and truncations are recorded.
- Dataset inventory: [measured row counts](dataset_inventory.json), [download receipts](datasets.json). The complete public source collection is cached locally under `.cache/datasets`; full weight/data binaries are not committed.

## Executed coverage

[GPQA domain and HumanEval task diagnostics](complete_split_analysis/analysis.md) are generated separately; incomplete counts stay explicitly marked.

| Run | Evaluation | Run state | Stage state | Scored rows | Scope | Metric | Value | Limit hits |
|---|---|---|---|---:|---|---|---:|---:|
| [demo](runs/demo/analysis.md) | mmlu | completed | completed | 2 | subset | score | 0.000000 | 0 |
| [full-reference](runs/full-reference/analysis.md) | mmlu | ended_early | completed | 14042 | full split | score | 0.309571 | 368 |
| [full-reference](runs/full-reference/analysis.md) | math | ended_early | completed | 5000 | full split | score | 0.021600 | 1036 |
| [full-reference](runs/full-reference/analysis.md) | gpqa | ended_early | completed | 1980 | full split; 10 repeat(s) | score | 0.141919 | 455 |
| [full-reference](runs/full-reference/analysis.md) | mgsm | ended_early | completed | 2750 | full split | score | 0.029818 | 1010 |
| [full-reference](runs/full-reference/analysis.md) | drop | ended_early | completed | 9536 | full split | f1_score | 20.690936 | 298 |
| [full-reference](runs/full-reference/analysis.md) | humaneval | ended_early | completed | 164 | full split; 5 sample(s)/task | score | 0.236585 | 34 |
| [full-reference](runs/full-reference/analysis.md) | simpleqa | ended_early | completed | 4326 | full split | score | 0.003467 | 134 |
| [full-reference](runs/full-reference/analysis.md) | browsecomp | ended_early | completed | 1266 | full split | score | 0.133491 | 112 |
| [full-reference](runs/full-reference/analysis.md) | healthbench | ended_early | failed | 389 | full split | score | undefined | 37 |
| [full-reference](runs/full-reference/analysis.md) | healthbench_hard | ended_early | stopped early | 123 | full split | score | undefined | 15 |
| [full-reference](runs/full-reference/analysis.md) | healthbench_consensus | ended_early | not run | 0 | full split | score | undefined | 0 |
| [full-reference](runs/full-reference/analysis.md) | healthbench_meta | ended_early | not run | 0 | full split | score | undefined | 0 |
| [m1-browsing](runs/m1-browsing/analysis.md) | browsecomp | completed | completed | 1 | subset | score | 1.000000 | 0 |
| [m1-calibration-100](runs/m1-calibration-100/analysis.md) | simpleqa_calibration | failed | failed | 0 | subset | score | undefined | 0 |
| [m1-calibration-100-validity](runs/m1-calibration-100-validity/analysis.md) | simpleqa_calibration | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-complete-small](runs/m1-complete-small/analysis.md) | gpqa | completed | completed | 198 | full split; 1 repeat(s) | score | 0.085859 | 84 |
| [m1-complete-small](runs/m1-complete-small/analysis.md) | humaneval | completed | completed | 164 | full split; 1 sample(s)/task | score | 0.237805 | 7 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | mmlu | failed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | math | failed | completed | 1 | subset | score | 0.000000 | 1 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | gpqa | failed | completed | 1 | subset; 1 repeat(s) | score | 1.000000 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | mgsm | failed | completed | 11 | subset | score | 0.000000 | 8 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | drop | failed | completed | 1 | subset | f1_score | 0.000000 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | humaneval | failed | completed | 1 | subset; 5 sample(s)/task | score | 0.600000 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | simpleqa | failed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | browsecomp | failed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | healthbench | failed | completed | 1 | subset | score | 0.133333 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | healthbench_hard | failed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | healthbench_consensus | failed | completed | 1 | subset | score | 0.666667 | 0 |
| [m1-final-suite](runs/m1-final-suite/analysis.md) | healthbench_meta | failed | failed | 1 | subset | score | undefined | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | mmlu | development / excluded | completed | 5 | subset | score | 0.600000 | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | math | development / excluded | completed | 5 | subset | score | 0.200000 | 3 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | gpqa | development / excluded | failed | 0 | subset; 1 repeat(s) | score | undefined | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | mgsm | development / excluded | completed | 55 | subset | score | 0.090909 | 18 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | drop | development / excluded | completed | 5 | subset | f1_score | 0.000000 | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | humaneval | development / excluded | completed | 5 | subset; 5 sample(s)/task | score | 0.120000 | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | simpleqa | development / excluded | completed | 5 | subset | score | 0.000000 | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | browsecomp | development / excluded | failed | 4 | subset | score | undefined | 1 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | healthbench | development / excluded | pending | 2 | subset | score | undefined | 1 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | healthbench_hard | development / excluded | pending | 0 | subset | score | undefined | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | healthbench_consensus | development / excluded | pending | 0 | subset | score | undefined | 0 |
| [m1-local-suite](runs/m1-local-suite/analysis.md) | healthbench_meta | development / excluded | pending | 0 | subset | score | undefined | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_AR-XY | completed | completed | 1 | subset | score | 1.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_BN-BD | completed | completed | 1 | subset | score | 1.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_DE-DE | completed | completed | 1 | subset | score | 1.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_ES-LA | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_FR-FR | completed | completed | 1 | subset | score | 1.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_HI-IN | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_ID-ID | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_IT-IT | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_JA-JP | completed | completed | 1 | subset | score | 1.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_KO-KR | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_PT-BR | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_ZH-CN | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_SW-KE | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-multilingual](runs/m1-multilingual/analysis.md) | mmlu_YO-NG | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-physician-1](runs/m1-physician-1/analysis.md) | healthbench | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-physician-2](runs/m1-physician-2/analysis.md) | healthbench | completed | completed | 1 | subset | score | 0.297872 | 0 |
| [m1-physician-3](runs/m1-physician-3/analysis.md) | healthbench | completed | completed | 1 | subset | score | 0.136364 | 0 |
| [m1-reference-2](runs/m1-reference-2/analysis.md) | healthbench | completed | completed | 1 | subset | score | 0.297872 | 0 |
| [m1-reference-3](runs/m1-reference-3/analysis.md) | healthbench | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | mmlu | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | math | completed | completed | 1 | subset | score | 0.000000 | 1 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | gpqa | completed | completed | 1 | subset; 1 repeat(s) | score | 1.000000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | mgsm | completed | completed | 11 | subset | score | 0.000000 | 8 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | drop | completed | completed | 1 | subset | f1_score | 0.000000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | humaneval | completed | completed | 1 | subset; 5 sample(s)/task | score | 0.600000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | simpleqa | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | browsecomp | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | healthbench | completed | completed | 1 | subset | score | 0.133333 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | healthbench_hard | completed | completed | 1 | subset | score | 0.000000 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | healthbench_consensus | completed | completed | 1 | subset | score | 0.666667 | 0 |
| [m1-verified-suite](runs/m1-verified-suite/analysis.md) | healthbench_meta | completed | completed | 1 | subset | score | undefined | 0 |

## Current job states

| Managed plan | Latest recorded stage | State |
|---|---|---|
| full-reference | original-suite | ended_early |
| local-extensions | reference-group-3 | completed |
| local-validation | multilingual-smoke | completed |

## Calibration and browsing diagnostics

- `m1-calibration-100-validity`: 100 draws, 88 valid structured outputs, modal frequency 0.840, modal answer correct = False. One question is insufficient for population-level calibration claims.
- `m1-browsing`: 2 tool events; 2 recorded tool errors. Errors: No results found.; No results found.

“Scored rows” only counts completed checkpoints. A running stage may already have raw generations but no final score. Development diagnostics are excluded from final conclusions. The initial development run was stopped after discovering missing CSV values and malformed grader output; its retained error records document those findings.

## Analysis

[Two-model execution comparison](comparison/m1-models/comparison.csv) uses the same two MMLU questions with both local models. Both scored zero on that tiny pair; this is not evidence for a general ranking.

1. The all-evaluator validation uses one item per evaluator and one per MGSM language (22 scored rows if all 12 evaluators finish). It verifies connectivity between real data, local generation, grading and persistence. It cannot establish benchmark accuracy.
2. The complete-small protocol covers all 198 GPQA Diamond questions (one permutation/draw each) and all 164 HumanEval tasks (one generated program each). These are complete splits with reduced repetitions, not the upstream repeated-sampling protocol or the HumanEval paper's full sampling study.
3. Tiny-model scores and output-limit hits must be considered together. Missing final-answer formatting may be scored wrong by the original extraction rules. Invalid grader formatting instead produces a visible failure or a bounded, recorded format-repair request.
4. HealthBench uses the local 3B judge. Its clinical rubric decisions are not independently validated as equivalent to the paper grader. HealthBench Meta may have undefined balanced F1 on a one-item subset because a required class is absent.
5. DROP F1 is expressed on a 0–100 scale. Never take a cross-benchmark mean of these raw scores.
6. The closed-book BrowseComp run is a baseline; only runs configured with `--browse` actually use public-web tools. The local agent differs from the unpublished research agent.
7. Calibration retains every scheduled draw and explicitly records invalid/conflicting JSON. Such draws fail the structured-answer pass/consensus metric and are excluded from stated-confidence bins; valid-draw coverage is reported. A one-question 100-draw test exercises frequency estimation, not population calibration.

## Measured systems optimization

Four warm repeated-prefix calls averaged **4.146 s without prefix caching** and **0.183 s with caching** (22.7× latency ratio). All twelve greedy outputs matched. This is a synthetic 1,636–1,641-input-token microbenchmark, not a claimed whole-suite speedup. Timing depends on system load; the sample size is small.

[Raw A/B measurements](cache_performance.json) · [Chart](../docs/assets/cache-performance.svg) · [Script](../scripts/benchmark_cache.py)

## Full-scale work and non-reproduced experiments

The [full-reference plan](plans/full-reference.json) includes the released suite, ten MATH-500/GPQA repeats, original MATH-5000, 200-sample HumanEval at temperatures 0.2 and 0.8, translated MMLU, 100-draw SimpleQA calibration, three local browser budgets, and physician/reference evaluation. It is substantially larger than the validation run: translated MMLU alone adds 196,588 prompts, and full calibration needs 432,600 candidate generations before grading.

**Do not interpret this plan or a running background process as completed experiments.** See the job state and per-run checkpoints for current progress. Historical model training, proprietary agent internals, original human data collection and several original-paper ablations are not available in this repository; see the [paper audit](../docs/PAPER_AUDIT.md).

```bash
.venv/bin/python scripts/manage_experiments.py status
.venv/bin/python scripts/summarize_experiments.py
# Resume the same full plan after a clean stop:
.venv/bin/python scripts/manage_experiments.py start --resume
# Explicitly stop the managed full plan:
.venv/bin/python scripts/manage_experiments.py stop
```

## 中文说明

以上表格来自实际保存的运行记录。全部评测入口的小样本验证、完整数据划分的一次采样、原论文规模的重复实验，是三个不同范围。未完成或失败的实验不会伪造为成功。开发阶段诊断数据保留，但不参与正式结论。全量任务可能需要持续多日，模型评分能力和生成上限也会影响完成率与结论。

默认英文 README 与中文 README 均提供数据流图、结构流程图、运行命令和真实终端演示。MP4 配套自动播放 HTML 页面，GitHub README 用自动循环 GIF 兼容展示。
