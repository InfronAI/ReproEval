import json
import subprocess
import sys

import pytest

from simple_evals import datasets, cli


def test_cli_list_without_credentials(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    proc = subprocess.run([sys.executable, '-m', 'simple_evals', '--list-evals'], capture_output=True, text=True)
    assert proc.returncode == 0
    assert 'healthbench_meta' in proc.stdout


@pytest.mark.parametrize('args', [['--examples', '0'], ['--workers', '0'], ['--eval', '../../bad'], ['--full', '--examples', '1']])
def test_invalid_cli(args):
    with pytest.raises(SystemExit) as error:
        cli.main(args)
    assert error.value.code == 2


def test_cache_offline_and_integrity(tmp_path, monkeypatch):
    monkeypatch.setenv('SIMPLE_EVALS_CACHE', str(tmp_path))
    monkeypatch.setenv('SIMPLE_EVALS_OFFLINE', '1')
    with pytest.raises(FileNotFoundError, match='Offline'):
        datasets.cached_path('https://example.com/data.csv')
    import hashlib
    url = 'https://example.com/data.csv'
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    p = tmp_path / (key + '-data.csv')
    p.write_text('x\n1\n')
    receipt = p.with_name(p.name + '.source.json')
    receipt.write_text(json.dumps({'sha256': datasets.sha256(p), 'url': url}))
    assert datasets.cached_path(url) == p
    p.write_text('corrupt')
    with pytest.raises(ValueError, match='integrity'):
        datasets.cached_path(url)


def test_failed_run_returns_nonzero_and_records_error(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, 'make_sampler', lambda *a: object())
    def fail(*a): raise RuntimeError('expected fixture failure')
    monkeypatch.setattr(cli, 'create_eval', fail)
    output = tmp_path / 'run'
    with pytest.raises(SystemExit) as error:
        cli.main(['--eval', 'mmlu', '--output', str(output)])
    assert error.value.code == 1
    assert json.loads((output / 'mmlu/error.json').read_text())['message'] == 'expected fixture failure'
    assert json.loads((output / 'summary.json').read_text())[0]['status'] == 'failed'
    assert not (output / 'mmlu/metrics.json').exists()
