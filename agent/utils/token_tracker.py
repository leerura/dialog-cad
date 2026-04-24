import asyncio
import functools
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class TokenUsage:
    node_name: str
    input_tokens: int
    output_tokens: int
    elapsed_ms: float

    @property
    def total_tokens(self):
        return self.input_tokens + self.output_tokens


@dataclass
class TokenTracker:
    records: list[TokenUsage] = field(default_factory=list)

    def add(self, usage: TokenUsage):
        self.records.append(usage)
        print(f"[TOKEN] {usage.node_name}: "
              f"in={usage.input_tokens} out={usage.output_tokens} "
              f"total={usage.total_tokens} ({usage.elapsed_ms:.0f}ms)")

    def summary(self):
        print("\n===== Token Usage Summary =====")
        for r in self.records:
            print(f"  {r.node_name:30s} | "
                  f"in={r.input_tokens:6d} out={r.output_tokens:6d} "
                  f"total={r.total_tokens:6d}")
        total = sum(r.total_tokens for r in self.records)
        print(f"  {'TOTAL':30s} | {total:>21d}")
        print("================================\n")

    def reset(self):
        self.records.clear()


tracker = TokenTracker()


def _extract_usage(meta) -> tuple[int, int]:
    if meta is None:
        return 0, 0
    if isinstance(meta, dict):
        return meta.get("input_tokens", 0), meta.get("output_tokens", 0)
    return getattr(meta, "input_tokens", 0), getattr(meta, "output_tokens", 0)


def track_tokens(node_name: str):
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(state, *args, **kwargs):
                start = time.time()
                result = await func(state, *args, **kwargs)
                elapsed = (time.time() - start) * 1000
                _record(node_name, result, elapsed)
                return result
            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(state, *args, **kwargs):
            start = time.time()
            result = func(state, *args, **kwargs)
            elapsed = (time.time() - start) * 1000
            _record(node_name, result, elapsed)
            return result
        return sync_wrapper
    return decorator


def _record(node_name: str, result, elapsed: float):
    if not isinstance(result, dict):
        tracker.add(TokenUsage(node_name=node_name, input_tokens=0, output_tokens=0, elapsed_ms=elapsed))
        return

    inp, out = 0, 0

    usage = result.get("last_token_usage")
    if usage:
        inp, out = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    else:
        for msg in reversed(result.get("messages", [])):
            meta = getattr(msg, "usage_metadata", None)
            if meta:
                inp, out = _extract_usage(meta)
                break

    tracker.add(TokenUsage(node_name=node_name, input_tokens=inp, output_tokens=out, elapsed_ms=elapsed))
