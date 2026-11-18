#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  echo 'Use a native arm64 terminal on Apple Silicon for MLX.' >&2
  exit 1
fi
PYTHON_BIN=${PYTHON_BIN:-python3.11}
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo 'Install Python 3.11 first: brew install python@3.11' >&2
  exit 1
fi
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install -e '.[mlx,humaneval,dev,browse]'
.venv/bin/python -m simple_evals doctor
.venv/bin/python -m pytest -q
