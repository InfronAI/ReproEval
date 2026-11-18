# Local experiment analysis

Candidate: `mlx-community/Qwen2.5-0.5B-Instruct-4bit`. Grader: `mlx-community/Qwen2.5-3B-Instruct-4bit`.

**Scope: bounded subset. These are local-model measurements, not the original paper results.**

| Evaluation | State | Examples | Metric | Value | Output tokens | Limit hits |
|---|---|---:|---|---:|---:|---:|
| mmlu | completed | 5 | score | 0.600000 | 1421 | 0 |
| math | completed | 5 | score | 0.200000 | 3268 | 3 |
| gpqa | failed | 0 | score | undefined | 0 | 0 |
| mgsm | completed | 55 | score | 0.090909 | 20981 | 18 |
| drop | completed | 5 | f1_score | 0.000000 | 314 | 0 |
| humaneval | completed | 5 | score | 0.120000 | 6042 | 0 |
| simpleqa | completed | 5 | score | 0.000000 | 915 | 0 |
| browsecomp | failed | 4 | score | undefined | 2393 | 1 |
| healthbench | pending | 2 | score | undefined | 3702 | 1 |
| healthbench_hard | pending | 0 | score | undefined | 0 | 0 |
| healthbench_consensus | pending | 0 | score | undefined | 0 | 0 |
| healthbench_meta | pending | 0 | score | undefined | 0 | 0 |

## Interpretation and limits

- Small samples do not estimate full-benchmark performance reliably; no leaderboard comparison is valid.
- The local grader is not the paper grader. HealthBench Meta measures its agreement with physician labels; an undefined balanced F1 means that the subset lacks a required class, not a score of zero.
- DROP F1 is on the original 0–100 scale. Most other metrics are on 0–1; do not average across benchmarks.
- Token limit hits can remove final answers and lower scores. Full prompts are retained; inputs are never silently truncated.
- BrowseComp without --browse is a closed-book baseline, not a browsing-agent replication.
- Calls include any failed format retries. Completed checkpoint counts refer to scored examples, not API calls.
- Seeds, source hashes, dependency versions, model revisions, dataset hashes, raw traces, conversations and per-example checkpoints are saved with this run.
