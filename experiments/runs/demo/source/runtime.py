"""Small, transparent experiment journal with per-example resumability."""
import dataclasses
import hashlib
import json
import math
import os
import threading
from pathlib import Path
from .types import SingleEvalResult

_state = threading.local()
checkpoint_dir: Path | None = None
workers = 1
seed = 0

def jsonable(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if dataclasses.is_dataclass(value):
        return jsonable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return jsonable(value.model_dump())
    if hasattr(value, "tolist"):
        return jsonable(value.tolist())
    if hasattr(value, "__dict__"):
        return jsonable(vars(value))
    return value

def digest(value):
    return hashlib.sha256(json.dumps(jsonable(value), sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{threading.get_ident()}.tmp")
    temp.write_text(json.dumps(jsonable(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    os.replace(temp, path)

def encode(value):
    if isinstance(value, SingleEvalResult):
        return {"kind": "single", "value": jsonable(value)}
    if isinstance(value, tuple):
        return {"kind": "tuple", "value": [encode(v) for v in value]}
    return {"kind": "plain", "value": jsonable(value)}

def decode(value):
    if value["kind"] == "single":
        return SingleEvalResult(**value["value"])
    if value["kind"] == "tuple":
        return tuple(decode(v) for v in value["value"])
    return value["value"]

def wrap_item(fn, index, item, depth):
    previous = getattr(_state, "path", ())
    _state.path = previous + (index,)
    old_depth = getattr(_state, "depth", 0)
    _state.depth = depth + 1
    _state.calls = 0
    try:
        path = checkpoint_dir / f"{index:06d}.json" if checkpoint_dir and depth == 0 else None
        item_hash = digest(item)
        if path and path.exists():
            saved = json.loads(path.read_text())
            if saved["input_sha256"] != item_hash:
                raise ValueError(f"Checkpoint input changed: {path}")
            return decode(saved["result"])
        result = fn(item)
        if path:
            atomic_json(path, {"index": index, "input_sha256": item_hash, "input": item, "result": encode(result)})
            print(f"  saved {path.name}", flush=True)
        return result
    finally:
        _state.path = previous
        _state.depth = old_depth

def request_seed(role):
    calls = getattr(_state, "calls", 0)
    _state.calls = calls + 1
    return int(digest([seed, getattr(_state, "path", ()), role, calls])[:8], 16)
