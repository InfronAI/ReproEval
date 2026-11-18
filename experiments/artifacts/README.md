# Recorded experiment artifacts

These lossless archives preserve the original per-example checkpoints, model/grader traces, result JSON and HTML reports from the full-reference campaign. The campaign was ended early; see the [report](../REPORT.md) and [termination record](../termination.json).

Small summaries, metrics, dataset receipts and frozen source snapshots remain directly browsable under [runs/full-reference](../runs/full-reference/). Large payloads are archived to avoid GitHub’s per-file size limit and a 96,000-file checkout.

## Verify or restore

From the repository root, using Python 3.11 or later (standard library only):

```bash
# Verify archive and individual-content checksums without restoring anything.
python3 scripts/archive_experiments.py verify

# Restore all raw artifacts to their original project paths.
python3 scripts/archive_experiments.py restore

# Or restore only one evaluator.
python3 scripts/archive_experiments.py restore --eval gpqa
```

Restoration never invokes a model or restarts an experiment. It refuses to overwrite a different existing file. After restoration, detailed HTML reports and checkpoint inputs are available at their original paths; `simple_evals analyze` can rebuild summaries without inference. Frozen dependencies and configuration are still required for any deliberate future experiment resume.

Checksums, content digests, member counts and byte sizes are recorded in [index.json](index.json). Original records remain unchanged; archive headers remove owner/group names while preserving file timestamps.

| Evaluation | Archive | Files | Compressed MiB |
|---|---|---:|---:|
| browsecomp | [full-reference-browsecomp.tar.gz](full-reference-browsecomp.tar.gz) | 4,073 | 5.12 |
| drop | [full-reference-drop.tar.gz](full-reference-drop.tar.gz) | 19,074 | 88.12 |
| gpqa | [full-reference-gpqa.tar.gz](full-reference-gpqa.tar.gz) | 3,962 | 10.64 |
| healthbench | [full-reference-healthbench.tar.gz](full-reference-healthbench.tar.gz) | 5,200 | 6.78 |
| healthbench_hard | [full-reference-healthbench_hard.tar.gz](full-reference-healthbench_hard.tar.gz) | 1,689 | 2.34 |
| humaneval | [full-reference-humaneval.tar.gz](full-reference-humaneval.tar.gz) | 986 | 0.64 |
| math | [full-reference-math.tar.gz](full-reference-math.tar.gz) | 15,003 | 16.79 |
| mgsm | [full-reference-mgsm.tar.gz](full-reference-mgsm.tar.gz) | 5,502 | 5.99 |
| mmlu | [full-reference-mmlu.tar.gz](full-reference-mmlu.tar.gz) | 28,086 | 37.41 |
| simpleqa | [full-reference-simpleqa.tar.gz](full-reference-simpleqa.tar.gz) | 12,980 | 9.06 |

Total: 96,555 files, 1021.88 MiB before compression and 182.90 MiB archived.

## 中文说明

归档完整保存逐题检查点、模型及评分轨迹、结果 JSON 和详细 HTML 报告。代码、汇总、指标、数据来源及源码快照可直接浏览。执行上面的 `restore` 命令即可还原原始目录；只使用 Python 标准库，不会启动模型或恢复已提前结束的实验。归档校验值与内容摘要见 `index.json`。
