"""Real local cache A/B measurements with fixed outputs, not an accuracy benchmark."""
import json
from pathlib import Path
from simple_evals.sampler.mlx_sampler import MLXSampler


def main():
    prefix = ('This is a synthetic systems performance test. The reference number is 42. ' * 100)
    prompts = [[{'role': 'user', 'content': prefix + '\nReturn only the reference number.'}],
               [{'role': 'user', 'content': prefix + '\nWhich reference number was given? Return only the number.'}]]
    rows = []
    for enabled in [False, True]:
        sampler = MLXSampler('mlx-community/Qwen2.5-3B-Instruct-4bit', temperature=0,
                             max_tokens=32, prefix_cache=enabled)
        for repetition in range(3):
            for index, messages in enumerate(prompts):
                response = sampler(messages)
                rows.append({'prefix_cache': enabled, 'repetition': repetition, 'prompt_index': index,
                             'response': response.response_text, **response.response_metadata})
    baseline = [x['response'] for x in rows if not x['prefix_cache']]
    cached = [x['response'] for x in rows if x['prefix_cache']]
    output = {'purpose': 'Synthetic performance A/B, not benchmark accuracy',
              'outputs_identical': baseline == cached, 'measurements': rows}
    Path('experiments/cache_performance.json').write_text(json.dumps(output, indent=2) + '\n')
    if baseline != cached:
        raise RuntimeError('Cache changed greedy outputs; investigate before enabling')
    print(json.dumps(output, indent=2))


if __name__ == '__main__': main()
