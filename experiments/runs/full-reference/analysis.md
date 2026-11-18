# Local experiment analysis

Candidate: `mlx-community/Qwen2.5-0.5B-Instruct-4bit`. Grader: `mlx-community/Qwen2.5-3B-Instruct-4bit`.

**Scope: full selected datasets. These are local-model measurements, not the original paper results.**

| Evaluation | State | Examples | Metric | Value | Output tokens | Limit hits |
|---|---|---:|---|---:|---:|---:|
| mmlu | completed | 14042 | score | 0.309571 | 5231611 | 368 |
| math | completed | 5000 | score | 0.021600 | 4341284 | 1036 |
| gpqa | completed | 1980 | score | 0.141919 | 1884161 | 455 |
| mgsm | completed | 2750 | score | 0.029818 | 2600177 | 1010 |
| drop | completed | 9536 | f1_score | 20.690936 | 1048786 | 298 |
| humaneval | completed | 164 | score | 0.236585 | 246997 | 34 |
| simpleqa | completed | 4326 | score | 0.003467 | 815058 | 134 |
| browsecomp | completed | 1266 | score | 0.133491 | 563247 | 112 |
| healthbench | failed | 389 | score | undefined | 404705 | 37 |
| healthbench_hard | pending | 123 | score | undefined | 140291 | 15 |
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
