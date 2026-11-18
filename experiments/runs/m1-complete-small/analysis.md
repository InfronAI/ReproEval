# Local experiment analysis

Candidate: `mlx-community/Qwen2.5-0.5B-Instruct-4bit`. Grader: `mlx-community/Qwen2.5-3B-Instruct-4bit`.

**Scope: full selected datasets. These are local-model measurements, not the original paper results.**

| Evaluation | State | Examples | Metric | Value | Output tokens | Limit hits |
|---|---|---:|---|---:|---:|---:|
| gpqa | completed | 198 | score | 0.085859 | 119919 | 84 |
| humaneval | completed | 164 | score | 0.237805 | 39793 | 7 |

## Interpretation and limits

- Small samples do not estimate full-benchmark performance reliably; no leaderboard comparison is valid.
- The local grader is not the paper grader. HealthBench Meta measures its agreement with physician labels; an undefined balanced F1 means that the subset lacks a required class, not a score of zero.
- DROP F1 is on the original 0–100 scale. Most other metrics are on 0–1; do not average across benchmarks.
- Token limit hits can remove final answers and lower scores. Full prompts are retained; inputs are never silently truncated.
- BrowseComp without --browse is a closed-book baseline, not a browsing-agent replication.
- Calls include any failed format retries. Completed checkpoint counts refer to scored examples, not API calls.
- Seeds, source hashes, dependency versions, model revisions, dataset hashes, raw traces, conversations and per-example checkpoints are saved with this run.
