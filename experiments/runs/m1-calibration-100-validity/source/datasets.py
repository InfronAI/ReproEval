"""Verified on-disk source cache. No credentials or model outputs in this cache."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = "https://openaipublic.blob.core.windows.net/simple-evals/"
LANGUAGES = "AR-XY BN-BD DE-DE ES-LA FR-FR HI-IN ID-ID IT-IT JA-JP KO-KR PT-BR ZH-CN SW-KE YO-NG".split()
SOURCES = {
    "mmlu": ROOT + "mmlu.csv",
    "math": ROOT + "math_500_test.csv",
    "math_full": ROOT + "math_test.csv",
    "gpqa": ROOT + "gpqa_diamond.csv",
    "simpleqa": ROOT + "simple_qa_test_set.csv",
    "browsecomp": ROOT + "browse_comp_test_set.csv",
    "drop_train": ROOT + "drop_v0_train.jsonl.gz",
    "drop": ROOT + "drop_v0_dev.jsonl.gz",
    "healthbench": ROOT + "healthbench/2025-05-07-06-14-12_oss_eval.jsonl",
    "healthbench_hard": ROOT + "healthbench/hard_2025-05-08-21-00-10.jsonl",
    "healthbench_consensus": ROOT + "healthbench/consensus_2025-05-09-20-00-46.jsonl",
    "healthbench_meta": ROOT + "healthbench/2025-05-07-06-14-12_oss_meta_eval.jsonl",
    **{f"mgsm_{x}": ROOT + f"mgsm_{x}.tsv" for x in "bn de en es fr ja ru sw te th zh".split()},
    **{f"mmlu_{x}": ROOT + f"mmlu_{x}.csv" for x in LANGUAGES},
}

def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def cache_dir():
    return Path(os.environ.get("SIMPLE_EVALS_CACHE", ".cache/datasets"))

def cached_path(source: str) -> Path:
    if not source.startswith(("https://", "http://")):
        return Path(source)
    root = cache_dir()
    root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(source.encode()).hexdigest()[:16]
    dest = root / (key + "-" + Path(urlparse(source).path).name)
    receipt = dest.with_name(dest.name + ".source.json")
    if dest.exists() and receipt.exists():
        record = json.loads(receipt.read_text())
        if record["sha256"] != sha256(dest):
            raise ValueError(f"Dataset integrity check failed: {dest}. Remove this cache entry to download again.")
        return dest
    if os.environ.get("SIMPLE_EVALS_OFFLINE") == "1":
        raise FileNotFoundError(f"Offline cache miss: {source}; run simple-evals prepare first")
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry))
        with session.get(source, timeout=(15, 90), stream=True) as response:
            response.raise_for_status()
            fd, temp = tempfile.mkstemp(dir=root, prefix="download-")
            try:
                size = 0
                with os.fdopen(fd, "wb") as f:
                    for chunk in response.iter_content(1024 * 1024):
                        size += len(chunk)
                        if size > 1024**3:
                            raise ValueError("Dataset exceeds 1 GiB download limit")
                        f.write(chunk)
                os.replace(temp, dest)
            finally:
                Path(temp).unlink(missing_ok=True)
    record = {"url": source, "sha256": sha256(dest), "bytes": dest.stat().st_size,
              "downloaded_at": datetime.now(timezone.utc).isoformat()}
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    return dest

def receipts():
    return [json.loads(p.read_text()) for p in sorted(cache_dir().glob("*.source.json"))]
