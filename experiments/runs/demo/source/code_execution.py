"""Timed subprocess execution with an OS sandbox on macOS."""
import ast
import json
import os
import platform
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_completion(text, entry_point):
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    text = match.group(1) if match else text
    try:
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point:
                # Use the model's body under the official signature; keep helper imports/functions.
                body = "\n".join("    " + line for stmt in node.body
                                  for line in ast.unparse(stmt).splitlines())
                helpers = [ast.unparse(n) for n in tree.body if n is not node]
                return body + ("\n\n" + "\n\n".join(helpers) if helpers else "") + "\n"
    except SyntaxError:
        pass
    return text


def check_completion(sample, completion, timeout=3.0):
    program = sample["prompt"] + completion + "\n" + sample["test"] + "\ncheck(" + sample["entry_point"] + ")"
    with tempfile.TemporaryDirectory(prefix="simple-evals-code-") as tmp:
        command = [sys.executable, "-I", str(Path(__file__).with_name("code_runner.py"))]
        if platform.system() == "Darwin":
            # Generated code has no network access and cannot read the user's home directory.
            # Allow OS runtime services; deny all network and writes outside the task tempdir.
            profile = '(version 1)(allow default)(deny network*)(deny file-write*)'
            exempt = [str(Path(sys.prefix).resolve()), str(Path(__file__).parent.resolve()), str(Path(tmp).resolve())]
            profile += '(deny file-read-data (require-all (subpath ' + json.dumps(str(Path.home())) + ')'
            profile += ''.join('(require-not (subpath ' + json.dumps(x) + '))' for x in exempt) + '))'
            profile += '(allow file-write* (literal "/dev/null") (subpath ' + json.dumps(str(Path(tmp).resolve())) + '))'
            command = ["/usr/bin/sandbox-exec", "-p", profile, *command]
        elif os.environ.get("SIMPLE_EVALS_ALLOW_UNSANDBOXED_CODE") != "1":
            raise RuntimeError("HumanEval requires the macOS sandbox or an isolated container with SIMPLE_EVALS_ALLOW_UNSANDBOXED_CODE=1")
        process = subprocess.Popen(command, cwd=tmp, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True,
                                   env={"PATH": "/usr/bin:/bin", "TMPDIR": tmp, "PYTHONHASHSEED": "0"})
        try:
            stdout, stderr = process.communicate(json.dumps({"program": program}), timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            return {"passed": False, "result": "timed out"}
        if process.returncode:
            raise RuntimeError(f"HumanEval worker failed ({process.returncode}): {stderr[:1000]}")
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid HumanEval worker output: {stderr[:500]}") from exc
