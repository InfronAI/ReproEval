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
            answers, confidence, raw, format_errors = [], [], [], []
            for _ in range(self.samples):
                text = sampler(messages).response_text
                try:
                    answer, conf = parse_confidence(text)
                    format_errors.append(None)
                except (ValueError, KeyError, TypeError) as exc:
                    # Candidate format failures are measured behavior, not grader failures.
                    # Keep all scheduled draws; never pick among conflicting confidences.
                    answer, conf = None, None
                    format_errors.append(str(exc))
                answers.append(answer); confidence.append(conf); raw.append(text)
            # Exact string groups; first occurrence breaks ties reproducibly.
            grades = {answer: self.grade_sample(row['problem'], row['answer'], answer) == 'A'
                      for answer in dict.fromkeys(answers) if answer is not None}
            valid_answers = [a for a in answers if a is not None]
            modal, n_modal = Counter(valid_answers).most_common(1)[0] if valid_answers else (None, 0)
            correct = [int(grades.get(a, False)) for a in answers]
            valid_pairs = [(c, y) for c, y in zip(confidence, correct) if c is not None]
            metrics = {'format_valid_rate': len(valid_answers) / self.samples,
                       'answer_frequency': n_modal / self.samples}
            if valid_pairs:
                metrics['stated_brier_valid_only'] = float(np.mean([(c-y)**2 for c, y in valid_pairs]))
            for n in range(1, self.samples + 1):
                metrics[f'pass@{n}'] = float(any(correct[:n]))
                prefix = [a for a in answers[:n] if a is not None]
                metrics[f'consensus@{n}'] = float(grades[Counter(prefix).most_common(1)[0][0]]) if prefix else 0.0
            return SingleEvalResult(score=float(grades.get(modal, False)), metrics=metrics,
                convo=messages + [{'role': 'assistant', 'content': s} for s in raw],
                html=common.jinja_env.from_string(common.HTML_JINJA).render(prompt_messages=messages,
                    next_message={'role': 'assistant', 'content': raw[0]}, score=float(grades.get(modal, False)),
                    correct_answer=row['answer'], extracted_answer=modal),
                example_level_metadata={'answers': answers, 'confidence': confidence, 'correct': correct,
                    'modal_answer': modal, 'modal_correct': grades.get(modal, False), 'modal_frequency': n_modal / self.samples,
                    'format_errors': format_errors, 'valid_draws': len(valid_answers), 'total_draws': self.samples})

        rows = common.map_with_progress(fn, self.examples)
        result = common.aggregate_results(rows)
        stated, frequency = [], []
        for row in rows:
            m = row.example_level_metadata
            # Figure 2 left: one stated-confidence draw per question.
            if m['confidence'][0] is not None:
                stated.append((m['confidence'][0], m['correct'][0]))
            if m['valid_draws']:
                frequency.append((m['modal_frequency'], m['modal_correct']))
        result.metadata['invalid_format_policy'] = 'All draws retained; invalid JSON is a failed structured-answer draw for pass/consensus, excluded from confidence bins; frequency denominator includes all scheduled draws.'
        result.metadata['stated_bins_15'] = calibration_bins(stated, count=15)
        result.metadata['frequency_bins_30'] = calibration_bins(frequency, count=30, quantile=True)
        return result
