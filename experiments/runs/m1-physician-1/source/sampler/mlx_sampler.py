"""Apple Silicon inference without a server, credentials, or CUDA."""
import platform
import threading
import time
import uuid
from pathlib import Path

from .. import runtime
from ..types import SamplerBase, SamplerResponse

_models = {}
_lock = threading.RLock()


class MLXSampler(SamplerBase):
    def __init__(self, model="mlx-community/Qwen2.5-0.5B-Instruct-4bit", *,
                 temperature=0.5, max_tokens=512, max_context=16384,
                 revision=None, role="candidate", trace_dir=None, prefix_cache=True):
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise RuntimeError("MLX requires native arm64 Python on Apple Silicon macOS")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_context = max_context
        self.role = role
        self.trace_dir = Path(trace_dir) if trace_dir else None
        from mlx_lm.models.cache import LRUPromptCache
        self._prefix_cache = LRUPromptCache(max_size=2, max_bytes=256 * 1024**2) if prefix_cache else None
        from huggingface_hub import snapshot_download
        if Path(model).is_dir():
            self.path = Path(model).resolve()
        else:
            self.path = Path(snapshot_download(model, revision=revision,
                allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.jinja"],
                local_files_only=__import__("os").environ.get("SIMPLE_EVALS_OFFLINE") == "1"))
        self.revision = self.path.name
        with _lock:
            if str(self.path) not in _models:
                from mlx_lm import load
                _models[str(self.path)] = load(str(self.path))
            self._model, self.tokenizer = _models[str(self.path)]

    def __call__(self, message_list):
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler
        from mlx_lm.models.cache import make_prompt_cache
        import mlx.core as mx
        # A single Metal stream bounds memory; candidate and grader share this lock.
        with _lock:
            seed = runtime.request_seed(self.role)
            mx.random.seed(seed)
            prompt = self.tokenizer.apply_chat_template(message_list, tokenize=False,
                                                       add_generation_prompt=True)
            tokens = self.tokenizer.encode(prompt)
            input_tokens = len(tokens)
            if input_tokens + self.max_tokens > self.max_context:
                raise ValueError(f"Context budget exceeded: {input_tokens}+{self.max_tokens}>{self.max_context}; no prompt was truncated")
            start = time.monotonic()
            cache, remaining = (self._prefix_cache.fetch_nearest_cache(str(self.path), tokens)
                                if self._prefix_cache else (None, tokens))
            cached_tokens = len(tokens) - len(remaining)
            if cache is None:
                cache = make_prompt_cache(self._model)
            cache_key = list(tokens)
            chunks, last = [], None
            for last in stream_generate(self._model, self.tokenizer, prompt=remaining,
                                        max_tokens=self.max_tokens,
                                        prompt_cache=cache,
                                        sampler=make_sampler(temp=self.temperature)):
                chunks.append(last.text)
                cache_key.append(last.token)
            if last is None:
                raise ValueError("MLX returned no generation")
            text = "".join(chunks)
            if self._prefix_cache is not None:
                self._prefix_cache.insert_cache(str(self.path), cache_key, cache)
            usage = {"input_tokens": input_tokens, "output_tokens": last.generation_tokens,
                     "input_cached_tokens": cached_tokens,
                     "total_tokens": input_tokens + last.generation_tokens}
            metadata = {"usage": usage, "model": self.model, "revision": self.revision,
                        "role": self.role, "seed": seed, "seconds": time.monotonic() - start,
                        "generation_tokens_per_second": last.generation_tps,
                        "peak_memory_gb": mx.get_peak_memory() / 1e9,
                        "truncated": last.generation_tokens >= self.max_tokens,
                        "finish_reason": getattr(last, "finish_reason", None)}
            if self.trace_dir:
                runtime.atomic_json(self.trace_dir / f"{uuid.uuid4().hex}.json",
                                    {"messages": message_list, "response": text, **metadata})
            mx.clear_cache()
            return SamplerResponse(text, message_list, metadata)
