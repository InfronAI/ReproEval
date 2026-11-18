"""Lazy registry: selecting one evaluation never initializes other services."""
import importlib

EVALS = {
    'mmlu': ('mmlu_eval', 'MMLUEval'),
    'math': ('math_eval', 'MathEval'),
    'gpqa': ('gpqa_eval', 'GPQAEval'),
    'mgsm': ('mgsm_eval', 'MGSMEval'),
    'drop': ('drop_eval', 'DropEval'),
    'humaneval': ('humaneval_eval', 'HumanEval'),
    'simpleqa_calibration': ('calibration_eval', 'SimpleQACalibrationEval'),
    'simpleqa': ('simpleqa_eval', 'SimpleQAEval'),
    'browsecomp': ('browsecomp_eval', 'BrowseCompEval'),
    'healthbench': ('healthbench_eval', 'HealthBenchEval'),
    'healthbench_hard': ('healthbench_eval', 'HealthBenchEval'),
    'healthbench_consensus': ('healthbench_eval', 'HealthBenchEval'),
    'healthbench_meta': ('healthbench_meta_eval', 'HealthBenchMetaEval'),
}


def create_eval(name, args, grader):
    language = None
    if name.startswith('mmlu_'):
        language, name = name[5:], 'mmlu'
    module, cls = EVALS[name]
    factory = getattr(importlib.import_module('.' + module, 'simple_evals'), cls)
    num = None if args.full else args.examples
    kwargs = {'num_examples': num}
    repeats = args.n_repeats or (10 if args.paper_repeats and name in {'math', 'gpqa'} else 1)
    if name in {'math', 'gpqa', 'simpleqa', 'browsecomp'} and num is not None and repeats != 1:
        raise ValueError('Subset sampling requires --n-repeats 1 for this evaluator')
    if name == 'mmlu':
        kwargs['language'] = language or 'EN-US'
    elif name == 'math':
        kwargs.update(equality_checker=grader, split=args.math_split, n_repeats=repeats)
    elif name == 'gpqa':
        kwargs.update(n_repeats=repeats)
    elif name == 'mgsm':
        kwargs = {'num_examples_per_lang': num or 250}
    elif name == 'humaneval':
        kwargs.update(num_samples_per_task=args.samples_per_task, timeout=args.code_timeout, ks_passes=args.pass_k)
    elif name == 'simpleqa_calibration':
        kwargs.update(grader_model=grader, samples=args.calibration_samples)
    elif name in {'simpleqa', 'browsecomp'}:
        kwargs.update(grader_model=grader, n_repeats=repeats)
    elif name.startswith('healthbench'):
        kwargs.update(grader_model=grader, n_repeats=repeats, n_threads=args.workers)
        if name != 'healthbench_meta':
            kwargs.update(subset_name=name.split('_', 1)[1] if '_' in name else None,
                          input_path=args.healthbench_input_path if name == 'healthbench' else None,
                          length_adjustment_center=args.healthbench_length_adjustment_center,
                          length_adjustment_penalty_per_500_chars=args.healthbench_length_adjustment_penalty_per_500_chars,
                          physician_completions_mode=args.physician_group,
                          run_reference_completions=args.reference_completions)
    return factory(**kwargs)
