import json
from pathlib import Path

import pytest

from simple_evals import common, runtime
from simple_evals.types import SingleEvalResult


@pytest.fixture(autouse=True)
def restore_runtime():
    old = runtime.checkpoint_dir, runtime.workers, runtime.seed
    runtime.checkpoint_dir = None
    runtime.workers = 1
    yield
    runtime.checkpoint_dir, runtime.workers, runtime.seed = old


def test_empty_and_ordered_map():
    assert common.map_with_progress(lambda x: x, []) == []
    runtime.workers = 4
    assert common.map_with_progress(lambda x: x * x, [3, 1, 2], pbar=False) == [9, 1, 4]


def test_resume_after_interruption(tmp_path):
    runtime.checkpoint_dir = tmp_path
    called = []
    def work(x):
        called.append(x)
        if x == 2:
            raise RuntimeError('interrupted')
        return SingleEvalResult(score=x)
    with pytest.raises(RuntimeError):
        common.map_with_progress(work, [1, 2, 3], pbar=False)
    assert len(list(tmp_path.glob('*.json'))) == 1
    called.clear()
    def finish(x):
        called.append(x)
        return SingleEvalResult(score=x)
    results = common.map_with_progress(finish, [1, 2, 3], pbar=False)
    assert called == [2, 3]
    assert [r.score for r in results] == [1, 2, 3]


def test_checkpoint_rejects_changed_input(tmp_path):
    runtime.checkpoint_dir = tmp_path
    common.map_with_progress(lambda x: SingleEvalResult(score=1), ['a'], pbar=False)
    with pytest.raises(ValueError, match='input changed'):
        common.map_with_progress(lambda x: SingleEvalResult(score=1), ['b'], pbar=False)


def test_nested_checkpoints_do_not_collide(tmp_path):
    runtime.checkpoint_dir = tmp_path
    def work(x):
        grades = common.map_with_progress(lambda y: y, [1, 2, 3], pbar=False)
        return (SingleEvalResult(score=sum(grades)), True)
    result = common.map_with_progress(work, [10, 20], pbar=False)
    assert len(list(tmp_path.glob('*.json'))) == 2
    assert common.map_with_progress(work, [10, 20], pbar=False) == result


def test_html_escape_and_bootstrap():
    html = common.message_to_html({'role': 'user', 'content': '<script>alert(1)</script>'})
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert common._compute_stat([0, 1, 1], 'bootstrap_std') == common._compute_stat([0, 1, 1], 'bootstrap_std')
    with pytest.raises(ValueError, match='empty'):
        common.aggregate_results([])


def test_seed_is_stable_across_resume(tmp_path):
    runtime.checkpoint_dir = tmp_path
    def fn(x):
        return SingleEvalResult(score=0, metrics={'seed': runtime.request_seed('candidate')})
    first = common.map_with_progress(fn, ['same', 'same'], pbar=False)
    assert first[0].metrics != first[1].metrics
    (tmp_path / '000001.json').unlink()
    again = common.map_with_progress(fn, ['same', 'same'], pbar=False)
    assert first == again


def test_missing_csv_values_are_valid_json(tmp_path):
    runtime.atomic_json(tmp_path / 'row.json', {'optional': float('nan'), 'answer': 'C'})
    assert json.loads((tmp_path / 'row.json').read_text()) == {'optional': None, 'answer': 'C'}


def test_result_serializes_nested_defaultdict(tmp_path):
    from collections import defaultdict
    from simple_evals.types import EvalResult
    result = EvalResult(None, {}, [], [], {'agreements': defaultdict(dict, {'doctor': {'score': 1}})})
    runtime.atomic_json(tmp_path / 'result.json', result)
    assert json.loads((tmp_path / 'result.json').read_text())['metadata']['agreements']['doctor']['score'] == 1


def test_undefined_report_score_is_not_zero():
    from simple_evals.types import EvalResult
    result = EvalResult(None, {'n': 1}, [], [], {})
    assert '<td>undefined</td>' in common.make_report(result)
