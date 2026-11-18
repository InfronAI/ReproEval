"""Reproducible, bounded-by-default evaluation CLI."""
import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import runtime
from .analysis import analyze
from .datasets import SOURCES, cached_path, receipts, sha256
from .registry import EVALS, create_eval

DEFAULT_MODEL = 'mlx-community/Qwen2.5-0.5B-Instruct-4bit'
DEFAULT_GRADER = 'mlx-community/Qwen2.5-3B-Instruct-4bit'


def positive(value):
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return n


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['run', 'doctor', 'prepare', 'analyze'], nargs='?', default='run')
    p.add_argument('--backend', choices=['mlx', 'openai', 'o-chat', 'responses', 'anthropic'], default='mlx')
    p.add_argument('--model', default=DEFAULT_MODEL)
    p.add_argument('--grader-model', default=DEFAULT_GRADER)
    p.add_argument('--grader-backend', choices=['mlx', 'openai', 'o-chat', 'responses', 'anthropic'])
    p.add_argument('--reasoning-effort', choices=['low', 'medium', 'high'])
    p.add_argument('--system-message')
    p.add_argument('--model-revision')
    p.add_argument('--grader-revision')
    p.add_argument('--eval', default='all')
    p.add_argument('--list-evals', action='store_true')
    p.add_argument('--list-models', action='store_true')
    size = p.add_mutually_exclusive_group()
    size.add_argument('--examples', type=positive, default=3, help='per evaluator; per language for MGSM')
    size.add_argument('--full', action='store_true', help='all rows, may take days on a laptop')
    p.add_argument('--debug', action='store_true', help='alias for one example')
    p.add_argument('--workers', '--n-threads', dest='workers', type=positive, default=1)
    p.add_argument('--max-tokens', type=positive, default=512)
    p.add_argument('--grader-max-tokens', type=positive, default=512)
    p.add_argument('--max-context', type=positive, default=16384)
    p.add_argument('--no-prefix-cache', action='store_true')
    p.add_argument('--temperature', type=float, default=0.5)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--n-repeats', type=positive)
    p.add_argument('--paper-repeats', action='store_true', help='legacy CLI repeats: 10 for MATH/GPQA')
    p.add_argument('--calibration-samples', type=positive, default=100)
    p.add_argument('--pass-k', default='1,2,5,10,100')
    p.add_argument('--samples-per-task', type=positive, default=5)
    p.add_argument('--code-timeout', type=float, default=10)
    p.add_argument('--math-split', choices=['math_test', 'math_500_test'], default='math_500_test')
    p.add_argument('--output', type=Path)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--offline', action='store_true')
    p.add_argument('--cache-dir', type=Path, default=Path('.cache/datasets'))
    p.add_argument('--healthbench-input-path')
    p.add_argument('--healthbench-length-adjustment-center', type=float)
    p.add_argument('--healthbench-length-adjustment-penalty-per-500-chars', type=float)
    p.add_argument('--healthbench-professional-mode', action='store_true')
    p.add_argument('--healthbench-use-gpt-5-4-low-grader', action='store_true')
    p.add_argument('--physician-group', choices=['Group 1', 'Group 2', 'Group 3'])
    p.add_argument('--reference-completions', action='store_true')
    p.add_argument('--browse', action='store_true', help='enable the optional bounded local browsing agent for BrowseComp')
    p.add_argument('--browse-steps', type=positive, default=5)
    return p


def make_sampler(args, role, trace_dir):
    is_grader = role == 'grader'
    backend = (args.grader_backend or args.backend) if is_grader else args.backend
    model = args.grader_model if is_grader else args.model
    tokens = args.grader_max_tokens if is_grader else args.max_tokens
    temperature = 0.0 if is_grader else args.temperature
    if backend == 'mlx':
        from .sampler.mlx_sampler import MLXSampler
        return MLXSampler(model, temperature=temperature, max_tokens=tokens,
                          revision=args.grader_revision if is_grader else args.model_revision,
                          max_context=args.max_context, role=role, trace_dir=trace_dir,
                          prefix_cache=not args.no_prefix_cache)
    if backend == 'anthropic':
        from .sampler.claude_sampler import ClaudeCompletionSampler
        return ClaudeCompletionSampler(model, temperature=temperature, max_tokens=tokens)
    if backend == 'o-chat':
        from .sampler.o_chat_completion_sampler import OChatCompletionSampler
        return OChatCompletionSampler(model=model, reasoning_effort=args.reasoning_effort)
    if backend == 'responses':
        from .sampler.responses_sampler import ResponsesSampler
        return ResponsesSampler(model, temperature=temperature, max_tokens=tokens,
                                reasoning_model=model.startswith(('o1', 'o3', 'o4', 'gpt-5')),
                                reasoning_effort='low' if args.healthbench_use_gpt_5_4_low_grader else args.reasoning_effort,
                                system_message=args.system_message)
    from .sampler.chat_completion_sampler import ChatCompletionSampler
    return ChatCompletionSampler(model, temperature=temperature, max_tokens=tokens, system_message=args.system_message)


def source_hashes():
    base = Path(__file__).parent
    return {str(p.relative_to(base)): sha256(p) for p in sorted(base.rglob('*.py'))}


def main(argv=None):
    p = parser(); args = p.parse_args(argv)
    if args.list_evals:
        print('\n'.join(EVALS)); return
    if args.list_models:
        print(DEFAULT_MODEL + '\n' + DEFAULT_GRADER + '\nAny model ID supported by the selected backend.'); return
    os.environ['SIMPLE_EVALS_CACHE'] = str(args.cache_dir)
    if args.offline: os.environ['SIMPLE_EVALS_OFFLINE'] = '1'
    if args.command == 'doctor':
        info = {'python': platform.python_version(), 'platform': platform.platform(),
                'machine': platform.machine(), 'apple_silicon': platform.system() == 'Darwin' and platform.machine() == 'arm64',
                'api_keys_configured': {k: bool(os.environ.get(k)) for k in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']}}
        try:
            import mlx.core as mx
            info['metal_available'] = mx.metal.is_available()
            info['mlx_version'] = importlib.metadata.version('mlx')
        except ImportError: info['metal_available'] = False
        print(json.dumps(info, indent=2)); return
    if args.command == 'prepare':
        selected = SOURCES if args.eval == 'all' else {name: SOURCES[name] for name in args.eval.split(',')}
        for name, url in selected.items():
            path = cached_path(url); print(f'{name}: {path.stat().st_size:,} bytes · {sha256(path)}', flush=True)
        runtime.atomic_json(args.output or Path('experiments/datasets.json'), receipts()); return
    if args.command == 'analyze':
        if not args.output: p.error('analyze requires --output RUN_DIRECTORY')
        print(json.dumps(analyze(args.output), indent=2)); return
    if args.debug: args.examples, args.full = 1, False
    try:
        args.pass_k = [positive(k) for k in args.pass_k.split(',')]
    except (ValueError, argparse.ArgumentTypeError):
        p.error('--pass-k must be comma-separated positive integers')
    if args.temperature < 0 or args.code_timeout <= 0: p.error('invalid temperature or code timeout')
    if args.backend == 'mlx' and args.workers != 1: p.error('MLX runs with --workers 1 to preserve deterministic Metal scheduling')
    if (args.healthbench_length_adjustment_center is None) != (args.healthbench_length_adjustment_penalty_per_500_chars is None):
        p.error('both HealthBench length-adjustment flags must be provided together')
    if args.healthbench_input_path and 'healthbench' not in args.eval.split(',') and args.eval != 'all':
        p.error('--healthbench-input-path requires the main healthbench evaluation')
    if args.reference_completions and args.physician_group not in {'Group 2', 'Group 3'}:
        p.error('--reference-completions requires --physician-group Group 2 or Group 3')
    if args.healthbench_use_gpt_5_4_low_grader:
        args.grader_model, args.grader_backend = 'gpt-5.4-2026-03-05', 'responses'
    if args.healthbench_professional_mode and not (args.eval == 'healthbench' and args.healthbench_input_path and args.healthbench_use_gpt_5_4_low_grader and args.healthbench_length_adjustment_center is not None):
        p.error('Professional mode requires healthbench only, custom input, GPT-5.4 low grader and length adjustment')
    names = [n for n in EVALS if n != 'simpleqa_calibration'] if args.eval == 'all' else args.eval.split(',')
    for name in names:
        if name not in EVALS and name not in SOURCES: p.error(f'unknown evaluation {name}')
        if name not in EVALS and not name.startswith('mmlu_'): p.error(f'{name} is a source, not an evaluation')
    if len(set(names)) != len(names): p.error('duplicate evaluations')
    output = args.output or Path('experiments/runs') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()
              if k not in {'command', 'output', 'resume', 'cache_dir', 'offline', 'list_models', 'list_evals'}}
    config['evals'] = names
    fingerprint = runtime.digest({'config': config, 'source': source_hashes()})
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / 'manifest.json'
    if manifest_path.exists():
        if not args.resume: p.error('output already contains a run; use --resume or a new --output')
        manifest = json.loads(manifest_path.read_text())
        if manifest['fingerprint'] != fingerprint: p.error('configuration or source changed; choose a new output directory')
        current_packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}
        if manifest['packages'] != current_packages:
            p.error('dependency environment changed; choose a new output directory')
    else:
        if args.resume: p.error('cannot resume: manifest does not exist')
        manifest = {'status': 'running', 'config': config, 'fingerprint': fingerprint, 'source_hashes': source_hashes(),
                    'started_at': datetime.now(timezone.utc).isoformat(), 'platform': platform.platform(),
                    'python': sys.version, 'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}}
        manifest['git_commit'] = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
        runtime.atomic_json(manifest_path, manifest)
        import shutil
        for relative in manifest['source_hashes']:
            destination = output / 'source' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(__file__).parent / relative, destination)
    # Prevent concurrent writers and repeated model loads on accidental double starts.
    import fcntl
    with (output / '.run.lock').open('w') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: p.error('another process is writing this run')
        runtime.workers, runtime.seed = args.workers, args.seed
        candidate = grader = None
        failed = []
        from . import common
        for name in names:
            folder = output / name; folder.mkdir(exist_ok=True)
            if (folder / 'metrics.json').exists():
                print(f'{name}: already complete', flush=True); continue
            print(f'\n=== {name} ===', flush=True)
            started = time.monotonic()
            try:
                if candidate is None: candidate = make_sampler(args, 'candidate', folder / 'traces')
                needs_grader = name in {'math', 'simpleqa', 'simpleqa_calibration', 'browsecomp'} or name.startswith('healthbench')
                if needs_grader and grader is None: grader = make_sampler(args, 'grader', folder / 'traces')
                for sampler in [candidate, grader]:
                    if sampler is not None and hasattr(sampler, 'trace_dir'): sampler.trace_dir = folder / 'traces'
                revisions = {role: getattr(sampler, 'revision', None) for role, sampler in [('candidate', candidate), ('grader', grader)]}
                if manifest.get('model_revisions') and any(v is not None and manifest['model_revisions'].get(k) not in (None, v) for k, v in revisions.items()):
                    raise ValueError('model revision changed since original run')
                manifest['model_revisions'] = {**manifest.get('model_revisions', {}), **{k: v for k, v in revisions.items() if v is not None}}
                runtime.atomic_json(manifest_path, manifest)
                evaluation = create_eval(name, args, grader)
                runtime.atomic_json(folder / 'datasets.json', receipts())
                runtime.checkpoint_dir = folder / 'checkpoints'
                active = grader if name == 'healthbench_meta' else candidate
                if args.browse and name == 'browsecomp':
                    from .sampler.browse_sampler import BrowseSampler
                    active = BrowseSampler(candidate, max_steps=args.browse_steps, trace_dir=folder / 'browse')
                result = evaluation(active)
                runtime.atomic_json(folder / 'results.json', result)
                (folder / 'report.html').write_text(common.make_report(result))
                runtime.atomic_json(folder / 'metrics.json', {**(result.metrics or {}), 'score': result.score,
                                                            'wall_seconds': time.monotonic() - started})
                (folder / 'error.json').unlink(missing_ok=True)
                print(f'{name}: score={result.score} · {len(result.convos)} examples', flush=True)
            except KeyboardInterrupt:
                manifest['status'] = 'interrupted'
                manifest['updated_at'] = datetime.now(timezone.utc).isoformat()
                runtime.atomic_json(manifest_path, manifest)
                raise
            except Exception as exc:
                import traceback
                failed.append(name)
                runtime.atomic_json(folder / 'error.json', {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()})
                print(f'{name}: FAILED: {exc}', file=sys.stderr, flush=True)
            finally:
                runtime.checkpoint_dir = None
                analyze(output)
        manifest['source_changed_during_run'] = manifest['source_hashes'] != source_hashes()
        if manifest['source_changed_during_run']:
            failed.append('source_changed_during_run')
        manifest['status'] = 'failed' if failed else 'completed'
        manifest['updated_at'] = datetime.now(timezone.utc).isoformat()
        runtime.atomic_json(manifest_path, manifest)
        print(f'\nResults: {output / "index.html"}', flush=True)
        if failed: raise SystemExit(1)


if __name__ == '__main__':
    main()
