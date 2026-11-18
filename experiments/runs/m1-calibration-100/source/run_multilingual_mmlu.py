"""Run all 15 MMLU languages through the unified, resumable runner."""
import sys
from .cli import main
from .datasets import LANGUAGES

if __name__ == "__main__":
    main(["--eval", ",".join(["mmlu"] + [f"mmlu_{x}" for x in LANGUAGES]), *sys.argv[1:]])
