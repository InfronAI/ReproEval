# Local experiment analysis

Candidate: `mlx-community/Qwen2.5-0.5B-Instruct-4bit`. Grader: `mlx-community/Qwen2.5-3B-Instruct-4bit`.

**Scope: bounded subset. These are local-model measurements, not the original paper results.**

| Evaluation | State | Examples | Metric | Value | Output tokens | Limit hits |
|---|---|---:|---|---:|---:|---:|
| mmlu | completed | 1 | score | 0.000000 | 279 | 0 |
| mmlu_AR-XY | completed | 1 | score | 1.000000 | 285 | 0 |
| mmlu_BN-BD | completed | 1 | score | 1.000000 | 476 | 0 |
| mmlu_DE-DE | completed | 1 | score | 1.000000 | 210 | 0 |
| mmlu_ES-LA | completed | 1 | score | 0.000000 | 278 | 0 |
| mmlu_FR-FR | completed | 1 | score | 1.000000 | 364 | 0 |
| mmlu_HI-IN | completed | 1 | score | 0.000000 | 399 | 0 |
| mmlu_ID-ID | completed | 1 | score | 0.000000 | 317 | 0 |
| mmlu_IT-IT | completed | 1 | score | 0.000000 | 378 | 0 |
| mmlu_JA-JP | completed | 1 | score | 1.000000 | 478 | 0 |
| mmlu_KO-KR | completed | 1 | score | 0.000000 | 283 | 0 |
| mmlu_PT-BR | completed | 1 | score | 0.000000 | 270 | 0 |
| mmlu_ZH-CN | completed | 1 | score | 0.000000 | 217 | 0 |
| mmlu_SW-KE | completed | 1 | score | 0.000000 | 239 | 0 |
| mmlu_YO-NG | completed | 1 | score | 0.000000 | 243 | 0 |

## Interpretation and limits

- Small samples do not estimate full-benchmark performance reliably; no leaderboard comparison is valid.
- The local grader is not the paper grader. HealthBench Meta measures its agreement with physician labels; an undefined balanced F1 means that the subset lacks a required class, not a score of zero.
- DROP F1 is on the original 0–100 scale. Most other metrics are on 0–1; do not average across benchmarks.
- Token limit hits can remove final answers and lower scores. Full prompts are retained; inputs are never silently truncated.
- BrowseComp without --browse is a closed-book baseline, not a browsing-agent replication.
- Calls include any failed format retries. Completed checkpoint counts refer to scored examples, not API calls.
- Seeds, source hashes, dependency versions, model revisions, dataset hashes, raw traces, conversations and per-example checkpoints are saved with this run.
