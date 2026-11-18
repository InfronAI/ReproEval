# Paper and implementation audit

Audit baseline: OpenAI `simple-evals`, commit `652c89d` (full SHA in each run manifest). This repository is an evaluation suite, **not an implementation of a single paper**. Its declared design is simple zero-shot chain-of-thought evaluation of chat models, with a three-example DROP exception. Recreating all historical model training, human dataset collection, and proprietary browsing agents is outside the released source and cannot truthfully be claimed as “100% reproduction.”

The local implementation keeps the published evaluator prompts, dataset splits and scoring formulas unless a bug is explicitly listed below. [Seven central prompt constants](../experiments/prompt_preservation.json) were compared against the original git revision and match exactly. Local model substitution, quantization, token limits, the browsing adapter and the calibration instruction are recorded experimental differences. “Full” means every row of the selected released split, not every experiment in every cited paper.

## Source-to-protocol mapping

| Family / primary source | Released procedure retained | Local support and remaining differences |
|---|---|---|
| [MMLU](https://arxiv.org/abs/2009.03300) | 57 subjects, answer-letter extraction, category metrics | 14,042 test rows and all 15 repository languages; repository zero-shot CoT differs from historical few-shot/base-model settings |
| [MATH](https://arxiv.org/abs/2103.03874) | Stepwise solution, final-answer extraction, equivalence grader | Both 5,000-row MATH and 500-row MATH-500 available; the CLI explicitly defaults to MATH-500. The paper's training experiments and original models are not recreated |
| [GPQA](https://arxiv.org/abs/2311.12022) | Seeded choice permutations, repeated answer accuracy | Diamond split has 198 rows; it is not the paper's complete 448-question collection. `--paper-repeats` follows the upstream CLI's 10 repeats, while the evaluator class default was 4 |
| [DROP](https://arxiv.org/abs/1903.00161) | Three training demonstrations, normalized EM and token F1 | 9,536 dev rows; F1 uses a 0–100 scale. Demonstration sampling remains seed 42 and is scheduled before threads |
| [MGSM](https://arxiv.org/abs/2210.03057) | Language-specific CoT instructions, numeric answer matching | 250 rows × 11 languages. Original paper's additional prompting/scaling ablations and other datasets are not implemented by this repository |
| [HumanEval](https://arxiv.org/abs/2107.03374) | 164 official programs/tests; unbiased pass@k estimator | Correct body extraction, independent timed processes and macOS sandbox; configurable samples and k. No Codex training or historical 200-sample run is implied by a five-sample run |
| [SimpleQA paper](https://cdn.openai.com/papers/simpleqa.pdf) | 4,326 questions; A/B/C grading, attempted accuracy and F1 | Added persisted F1, stated-confidence bins, 100-draw frequency, consensus@n and pass@n entry point. Calibration's JSON instruction is a paraphrase of Appendix C; model/grader differ from the paper. Invalid structured draws are retained and reported, not silently replaced; confidence bins exclude invalid confidence values |
| [BrowseComp](https://openai.com/index/browsecomp/) | 1,266 encrypted questions; decryption, answer format and yes/no grading | Corrected grader extraction; optional bounded public-web agent and 2/5/10-step sweep. It is a new local agent, not the unpublished deep-research implementation; no-tool results remain explicitly closed book. Original aggregation strategies and proprietary compute controls are not reproduced |
| [HealthBench](https://openai.com/index/healthbench/) | Weighted positive/negative criteria, clipped aggregate, per-tag bootstrap, physician and reference modes | Main, hard, consensus, meta, physician groups and Professional custom-input/length-adjustment options retained. A small local judge cannot stand in for the paper's validated GPT-4.1 grader |

HealthBench source files contain 5,000 / 1,000 / 3,671 / 29,511 rows for main / hard / consensus / meta respectively. These counts are measured from the actual downloaded files in [dataset_inventory.json](../experiments/dataset_inventory.json). Consensus rows are the released file's units, not necessarily independent conversations. All 37 downloaded source objects have byte sizes and SHA-256 receipts in [datasets.json](../experiments/datasets.json); HumanEval's packaged archive is separately hashed in the inventory.

## Verified upstream defects and compatibility changes

| Finding | Correction / evidence |
|---|---|
| `BrowseComp.grade_sample` returned the entire `correct: yes` match and compared it to `yes` | Return captured yes/no label; regression tests cover both classes and capitalization |
| SimpleQA calculated F1 and attempted accuracy but only printed them | Persist both metrics in result JSON |
| Root `types.py` could shadow the standard library; hyphenated module path was difficult to install | Standard `src/simple_evals` package, Python ≥3.11 metadata and console entry point |
| CLI eagerly built every OpenAI/Anthropic sampler | Lazy registry and selected backends; list/doctor commands require no API keys |
| Samplers and rubric parsing could retry forever | SDK requests bounded by retries and timeout; grader formats limited to three attempts, with neutral format-repair instructions after a malformed first output |
| Bad requests/malformed grades could be silently counted as model errors | Infrastructure/grade-format failures become explicit failed runs, with retained checkpoints |
| HumanEval requested 250 examples from 164 by default and ignored its configured timeout | Default all tasks; honor timeout; support pass@k only when enough samples exist |
| HumanEval's string slice broke multiline signatures and helpers | AST-based function-body extraction, with original test programs |
| DROP shared a random generator across workers | Precompute demonstrations in original example order |
| MGSM swallowed sampling exceptions and then used an uninitialized conversation | Propagate failure with its trace |
| Thread pools failed on empty inputs and nested rubric pools multiplied thread count | Empty-safe ordered map; one local worker and serial nested grading |
| Small meta-eval subsets sometimes lack a class | Balanced F1 remains undefined (`null`), with class counts retained |
| Bootstrap depended on global random state | Fixed local bootstrap RNG without changing the statistic |
| HealthBench injected grader text into Jinja template source | Treat grader text as escaped template data |
| GPQA ancillary CSV columns contain NaN | Serialize nonfinite/missing values as JSON null, preserving question and answer fields |

## Reproduction stages

1. Install natively on Apple Silicon; record hardware, Python and dependency versions.
2. Download original sources; validate SHA-256 on every cached read. Keep official canaries intact. Benchmark material must not be used for training.
3. Resolve and record immutable candidate/grader model revisions; load quantized weights using [MLX LM](https://github.com/ml-explore/mlx-lm).
4. Run all released evaluators on small deterministic subsets to validate the entire pipeline.
5. Run selected complete datasets with the same explicit settings; retain per-example outputs rather than replacing an incomplete run with a claimed score.
6. Run calibration, multilingual evaluation, physician/reference scoring and optional browse budgets separately. Changes in prompt, samples, tools or model constitute a separate experiment.
7. Aggregate saved measurements into JSON, CSV, HTML and Markdown. Treat incomplete/failed stages as such.

The [full reference plan](../experiments/plans/full-reference.json) specifies the released-dataset runs and supported extensions. Running a plan is different from having completed it. Current executed coverage is in [the experiment report](../experiments/REPORT.md), which is the authoritative statement of what was actually measured.

## Hard limits on equivalence

The open releases do not include all training pipelines, historical proprietary model snapshots, research-agent internals, or human data-generation labor described across these papers. This fork does not invent them. Newly implemented local browsing and calibration are useful experiments, but neither proves equivalence to the original papers. Grader quality, incomplete generations, class coverage and sample sizes are explicit analysis limitations.
