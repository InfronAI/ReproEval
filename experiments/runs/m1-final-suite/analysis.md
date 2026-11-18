# Local experiment analysis

Candidate: `mlx-community/Qwen2.5-0.5B-Instruct-4bit`. Grader: `mlx-community/Qwen2.5-3B-Instruct-4bit`.

**Scope: bounded subset. These are local-model measurements, not the original paper results.**

| Evaluation | State | Examples | Metric | Value | Output tokens | Limit hits |
|---|---|---:|---|---:|---:|---:|
| mmlu | completed | 1 | score | 0.000000 | 279 | 0 |
| math | completed | 1 | score | 0.000000 | 770 | 1 |
| gpqa | completed | 1 | score | 1.000000 | 597 | 0 |
| mgsm | completed | 11 | score | 0.000000 | 6671 | 8 |
| drop | completed | 1 | f1_score | 0.000000 | 66 | 0 |
| humaneval | completed | 1 | score | 0.600000 | 864 | 0 |
| simpleqa | completed | 1 | score | 0.000000 | 125 | 0 |
| browsecomp | completed | 1 | score | 0.000000 | 328 | 0 |
| healthbench | completed | 1 | score | 0.133333 | 1410 | 0 |
| healthbench_hard | completed | 1 | score | 0.000000 | 852 | 0 |
| healthbench_consensus | completed | 1 | score | 0.666667 | 355 | 0 |
| healthbench_meta | failed | 1 | score | undefined | 76 | 0 |

## Interpretation and limits

- Small samples do not estimate full-benchmark performance reliably; no leaderboard comparison is valid.
- The local grader is not the paper grader. HealthBench Meta measures its agreement with physician labels; an undefined balanced F1 means that the subset lacks a required class, not a score of zero.
- DROP F1 is on the original 0–100 scale. Most other metrics are on 0–1; do not average across benchmarks.
- Token limit hits can remove final answers and lower scores. Full prompts are retained; inputs are never silently truncated.
- BrowseComp without --browse is a closed-book baseline, not a browsing-agent replication.
- Calls include any failed format retries. Completed checkpoint counts refer to scored examples, not API calls.
- Seeds, source hashes, dependency versions, model revisions, dataset hashes, raw traces, conversations and per-example checkpoints are saved with this run.
