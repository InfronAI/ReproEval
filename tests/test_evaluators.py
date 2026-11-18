import json
import platform
from pathlib import Path

import pytest

from simple_evals import common
from simple_evals.browsecomp_eval import BrowseCompEval, decrypt, derive_key
from simple_evals.calibration_eval import parse_confidence, calibration_bins
from simple_evals.code_execution import check_completion, extract_completion
from simple_evals.healthbench_eval import HealthBenchEval, RubricItem, parse_json_to_dict
from simple_evals.simpleqa_eval import SimpleQAEval
from simple_evals.types import SamplerBase, SamplerResponse


class Fixed(SamplerBase):
    def __init__(self, text):
        self.text, self.calls = text, 0
    def __call__(self, messages):
        self.calls += 1
        return SamplerResponse(self.text, messages, {})


@pytest.mark.parametrize('text,expected', [('correct: yes', 'yes'), ('reasoning: no issues\ncorrect: no', 'no'), ('Correct: YES', 'yes')])
def test_browsecomp_grading_regression(text, expected):
    obj = object.__new__(BrowseCompEval)
    obj.grader_model = Fixed(text)
    assert obj.grade_sample('q', 'answer', 'prediction') == expected


def test_malformed_grading_is_not_an_incorrect_answer():
    obj = object.__new__(BrowseCompEval); obj.grader_model = Fixed('malformed')
    with pytest.raises(ValueError): obj.grade_sample('q', 'a', 'p')
    obj = object.__new__(SimpleQAEval); obj.grader_model = Fixed('Because it is correct')
    with pytest.raises(ValueError): obj.grade_sample('q', 'a', 'p')


@pytest.mark.parametrize('text,expected', [('A', 'A'), (' B\n', 'B'), ('C', 'C')])
def test_simpleqa_grades(text, expected):
    obj = object.__new__(SimpleQAEval); obj.grader_model = Fixed(text)
    assert obj.grade_sample('q', 'a', 'p') == expected


def test_healthbench_format_retry_is_bounded():
    obj = object.__new__(HealthBenchEval)
    obj.grader_model = Fixed('[]')
    with pytest.raises(ValueError, match='after 3'):
        obj.grade_sample([], 'answer', [], [RubricItem('criterion', 1, [])])
    assert obj.grader_model.calls == 3
    assert parse_json_to_dict('true') == {}


def test_code_extraction_multiline_and_helpers():
    source = '```python\nimport math\ndef square(\n    x: float,\n) -> float:\n    """Return the square."""\n    return math.pow(x, 2)\n```'
    result = extract_completion(source, 'square')
    assert '    return math.pow(x, 2)' in result
    assert 'import math' in result
    compile('def square(x):\n' + result, '<test>', 'exec')


@pytest.mark.skipif(platform.system() != 'Darwin', reason='macOS sandbox integration')
def test_execution_pass_fail_timeout_and_network():
    sample = {'prompt': 'def add(a, b):\n', 'test': 'def check(f):\n    assert f(1, 2) == 3', 'entry_point': 'add'}
    assert check_completion(sample, '    return a+b\n', 5)['passed']
    assert not check_completion(sample, '    return a-b\n', 5)['passed']
    assert check_completion(sample, '    while True: pass\n', 0.5)['result'] == 'timed out'
    assert not check_completion(sample, '    import socket\n    socket.create_connection(("1.1.1.1", 80), timeout=1)\n    return a+b\n', 5)['passed']


@pytest.mark.parametrize('text', ['{"answer":"x","confidence_score":101}', '{"answer":"x","confidence_score":true}', '{"answer":"x","confidence_score":NaN}'])
def test_invalid_confidence(text):
    with pytest.raises(ValueError): parse_confidence(text)


def test_calibration_boundaries():
    assert parse_confidence('```json\n{"answer":"x","confidence_score":100}\n```') == ('x', 1)
    bins = calibration_bins([(0, 0), (1, 1), (0.5, 1)], count=15)
    assert sum(b['n'] for b in bins) == 3
    assert bins[-1] == {'n': 1, 'confidence': 1.0, 'accuracy': 1.0}


def test_simpleqa_persists_secondary_metrics():
    obj = object.__new__(SimpleQAEval)
    obj.examples = [{'problem': 'q', 'answer': 'a'}]
    obj.grader_model = Fixed('A')
    result = obj(Fixed('a'))
    assert result.metrics['f1'] == 1
    assert result.metrics['accuracy_given_attempted'] == 1


def test_multilingual_answer_normalization():
    assert common.normalize_extracted_answer('a') == 'A'
    assert common.normalize_extracted_answer('Ａ') == 'A'
    assert common.normalize_extracted_answer('ব') == 'B'


def test_calibration_retains_invalid_draws():
    from simple_evals.calibration_eval import SimpleQACalibrationEval
    obj = object.__new__(SimpleQACalibrationEval)
    obj.examples = [{'problem': 'q', 'answer': 'a'}]
    obj.samples = 3
    obj.grader_model = Fixed('A')
    outputs = iter(['conflicting JSON', '{"answer":"a","confidence_score":80}', '{"answer":"a","confidence_score":90}'])
    class Draws(SamplerBase):
        temperature = 1
        def __call__(self, messages):
            return SamplerResponse(next(outputs), messages, {})
    result = obj(Draws())
    assert result.metrics['format_valid_rate'] == 2/3
    assert result.metrics['pass@1'] == 0
    assert result.metrics['pass@3'] == 1
    metadata = result.metadata['example_level_metadata'][0]
    assert len(metadata['answers']) == 3
    assert metadata['answers'][0] is None
    assert metadata['total_draws'] == 3
