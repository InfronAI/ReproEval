# Complete-split diagnostics

These tables describe saved checkpoints. A partial count is not a completed benchmark result.

## gpqa: 198/198 tasks — complete

| Group | Scored tasks | Mean score |
|---|---:|---:|
| Biology | 19 | 0.052632 |
| Chemistry | 93 | 0.118280 |
| Physics | 86 | 0.058140 |

110 recorded responses lacked the required final answer marker. These are failures under the original answer extraction rule.
Among the 88 responses with an extractable answer, 17 were correct. This conditional diagnostic excludes format failures and must not replace the benchmark score.

Overall: 17/198 correct (8.59%); recorded evaluation wall time: 1107.0 seconds.

## humaneval: 164/164 tasks — complete

| Group | Scored tasks | Mean score |
|---|---:|---:|
| all tasks | 164 | 0.237805 |

Overall: 39/164 correct (23.78%); recorded evaluation wall time: 364.3 seconds.
This is observed pass@1 from one program per task. Larger-k success rates require additional independent generations and cannot be estimated from this run.

Each task has one generated answer/program in this protocol. GPQA uses a single choice permutation and HumanEval reports pass@1; no pass@5 or paper-scale sampling claim is made. Scores are descriptive for these fixed splits and local model settings.
