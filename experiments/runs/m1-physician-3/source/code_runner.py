"""Isolated worker for HumanEval. Invoked in a fresh interpreter, never a thread fork."""
import json
import sys


def main():
    payload = json.load(sys.stdin)
    from human_eval.execution import reliability_guard, swallow_io
    program = payload["program"]
    reliability_guard()
    try:
        with swallow_io():
            exec(program, {})
        result = {"passed": True, "result": "passed"}
    except BaseException as exc:
        result = {"passed": False, "result": f"failed: {type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
