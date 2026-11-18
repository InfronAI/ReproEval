"""SimpleQA §4 / Appendix D: confidence, frequency, consensus@n and pass@n.

The JSON instruction is a local paraphrase of Appendix C; see docs/PAPER_AUDIT.md.
"""
from collections import Counter
import json
import math

import numpy as np

from . import common
from .simpleqa_eval import SimpleQAEval
from .types import SingleEvalResult

PROMPT = ('Question: {question}\nGive your best guess. Return JSON containing "answer" '
          '(a string) and "confidence_score" (a number from 0 to 100).')


def parse_confidence(text):
    text = text.strip().removeprefix('```json').removesuffix('```').strip()
    value = json.loads(text)
    answer, confidence = value['answer'], value['confidence_score']
    if not isinstance(answer, str) or type(confidence) not in (int, float):
        raise ValueError('Invalid confidence JSON types')
    if not math.isfinite(confidence) or not 0 <= confidence <= 100:
        raise ValueError('Confidence must be in [0, 100]')
    return answer, confidence / 100


def calibration_bins(pairs, *, count=15, quantile=False):
    if not pairs:
        return []
    values = np.array(pairs, dtype=float)
    if quantile:
        groups = np.array_split(values[np.argsort(values[:, 0], kind='stable')], min(count, len(values)))
    else:
        assignments = np.minimum((values[:, 0] * count).astype(int), count - 1)
        groups = [values[assignments == i] for i in range(count)]
    return [{'n': len(group), 'confidence': float(group[:, 0].mean()), 'accuracy': float(group[:, 1].mean())}
            for group in groups if len(group)]


class SimpleQACalibrationEval(SimpleQAEval):
    def __init__(self, grader_model, num_examples=None, samples=100):
        super().__init__(grader_model, num_examples=num_examples)
        if samples < 1:
            raise ValueError('samples must be positive')
        self.samples = samples

    def __call__(self, sampler):
        if getattr(sampler, 'temperature', None) != 1.0:
            raise ValueError('SimpleQA frequency calibration requires --temperature 1')

        def fn(row):
            messages = [sampler._pack_message('user', PROMPT.format(question=row['problem']))]
            answers, confidence, raw = [], [], []
            for _ in range(self.samples):
                text = sampler(messages).response_text
                answer, conf = parse_confidence(text)
                answers.append(answer); confidence.append(conf); raw.append(text)
            # Exact string groups; first occurrence breaks ties reproducibly.
            grades = {answer: self.grade_sample(row['problem'], row['answer'], answer) == 'A'
                      for answer in dict.fromkeys(answers)}
            modal, n_modal = Counter(answers).most_common(1)[0]
            correct = [int(grades[a]) for a in answers]
            metrics = {'stated_brier': float(np.mean((np.array(confidence) - correct) ** 2)),
                       'answer_frequency': n_modal / self.samples}
            for n in range(1, self.samples + 1):
                metrics[f'pass@{n}'] = float(any(correct[:n]))
                metrics[f'consensus@{n}'] = float(grades[Counter(answers[:n]).most_common(1)[0][0]])
            return SingleEvalResult(score=float(grades[modal]), metrics=metrics,
                convo=messages + [{'role': 'assistant', 'content': s} for s in raw],
                html=common.jinja_env.from_string(common.HTML_JINJA).render(prompt_messages=messages,
                    next_message={'role': 'assistant', 'content': raw[0]}, score=float(grades[modal]),
                    correct_answer=row['answer'], extracted_answer=modal),
                example_level_metadata={'answers': answers, 'confidence': confidence, 'correct': correct,
                    'modal_answer': modal, 'modal_correct': grades[modal], 'modal_frequency': n_modal / self.samples})

        rows = common.map_with_progress(fn, self.examples)
        result = common.aggregate_results(rows)
        stated, frequency = [], []
        for row in rows:
            m = row.example_level_metadata
            # Figure 2 left: one stated-confidence draw per question.
            stated.append((m['confidence'][0], m['correct'][0]))
            frequency.append((m['modal_frequency'], m['modal_correct']))
        result.metadata['stated_bins_15'] = calibration_bins(stated, count=15)
        result.metadata['frequency_bins_30'] = calibration_bins(frequency, count=30, quantile=True)
        return result
