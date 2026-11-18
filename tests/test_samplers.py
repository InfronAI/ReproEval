from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from simple_evals.sampler.chat_completion_sampler import ChatCompletionSampler
from simple_evals.sampler.responses_sampler import ResponsesSampler


def test_chat_does_not_turn_failure_into_wrong_answer():
    sampler = object.__new__(ChatCompletionSampler)
    sampler.system_message = None
    sampler.model, sampler.temperature, sampler.max_tokens = 'test', 0, 16
    create = Mock(side_effect=RuntimeError('simulated transport error'))
    sampler.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with pytest.raises(RuntimeError): sampler([{'role': 'user', 'content': 'q'}])
    assert create.call_count == 1  # SDK handles only its own bounded retry policy.


def test_reasoning_responses_honors_output_limit():
    sampler = object.__new__(ResponsesSampler)
    sampler.system_message = None
    sampler.model, sampler.max_tokens = 'reasoning-test', 123
    sampler.reasoning_model, sampler.reasoning_effort = True, 'low'
    create = Mock(return_value=SimpleNamespace(output_text='answer', usage=None))
    sampler.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    assert sampler([{'role': 'user', 'content': 'q'}]).response_text == 'answer'
    assert create.call_args.kwargs['max_output_tokens'] == 123
    assert 'temperature' not in create.call_args.kwargs


def test_format_repair_does_not_choose_label():
    from simple_evals import common
    from simple_evals.types import SamplerResponse
    responses = iter(['missing', 'no'])
    seen = []
    def sampler(messages):
        seen.append([dict(m) for m in messages])
        return SamplerResponse(next(responses), messages, {})
    def parse(text):
        if text not in ['yes', 'no']: raise ValueError('format')
        return text
    result, _ = common.sample_with_validation(sampler, [{'role':'user','content':'original'}], parse, 'Return yes or no.')
    assert result == 'no'
    assert len(seen) == 2
    assert seen[0] == [{'role':'user','content':'original'}]
    assert seen[1][-1]['content'] == 'Return yes or no.'
