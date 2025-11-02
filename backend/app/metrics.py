# backend/app/metrics.py
from dataclasses import dataclass, field
from time import perf_counter
from typing import Dict
import threading

@dataclass
class Buckets:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def observe(self, ms: float):
        self.count += 1
        self.total_ms += ms
        if ms > self.max_ms:
            self.max_ms = ms

    def p50(self) -> float:
        # simple proxy: avg; (upgrade to HDR histogram later)
        return self.avg()

    def p95(self) -> float:
        # proxy: max for MVP (safe upper bound)
        return self.max_ms

    def avg(self) -> float:
        return (self.total_ms / self.count) if self.count else 0.0

@dataclass
class Metrics:
    lock: threading.Lock = field(default_factory=threading.Lock)
    calls_total: int = 0
    intents: Dict[str, int] = field(default_factory=dict)
    handoffs: int = 0
    refusals: int = 0
    redactions: int = 0
    tool_success: int = 0
    tool_fail: int = 0
    rag_latency: Buckets = field(default_factory=Buckets)
    answer_latency: Buckets = field(default_factory=Buckets)
    confidence_sum: float = 0.0
    confidence_count: int = 0

    def inc(self, key: str, delta: int = 1):
        with self.lock:
            if key == "calls_total":
                self.calls_total += delta
            elif key == "handoffs":
                self.handoffs += delta
            elif key == "refusals":
                self.refusals += delta
            elif key == "redactions":
                self.redactions += delta
            elif key == "tool_success":
                self.tool_success += delta
            elif key == "tool_fail":
                self.tool_fail += delta
            else:
                self.intents[key] = self.intents.get(key, 0) + delta

    def observe_latency(self, bucket: str, ms: float):
        with self.lock:
            (self.answer_latency if bucket == "answer" else self.rag_latency).observe(ms)

    def observe_conf(self, value: float):
        with self.lock:
            self.confidence_sum += value
            self.confidence_count += 1

    def snapshot(self) -> Dict:
        with self.lock:
            return {
                "calls_total": self.calls_total,
                "intents": dict(self.intents),
                "handoffs": self.handoffs,
                "refusals": self.refusals,
                "redactions": self.redactions,
                "tool": {"success": self.tool_success, "fail": self.tool_fail},
                "latency_ms": {
                    "answer": {
                        "avg": round(self.answer_latency.avg(), 2),
                        "p50": round(self.answer_latency.p50(), 2),
                        "p95": round(self.answer_latency.p95(), 2),
                        "count": self.answer_latency.count,
                    },
                    "rag": {
                        "avg": round(self.rag_latency.avg(), 2),
                        "p50": round(self.rag_latency.p50(), 2),
                        "p95": round(self.rag_latency.p95(), 2),
                        "count": self.rag_latency.count,
                    },
                },
                "confidence_avg": round(
                    (self.confidence_sum / self.confidence_count) if self.confidence_count else 0.0, 3
                ),
            }

METRICS = Metrics()

class timed:
    """Context manager for timing blocks."""
    def __init__(self, bucket: str):
        self.bucket = bucket
        self.t0 = 0.0
    def __enter__(self):
        self.t0 = perf_counter()
    def __exit__(self, exc_type, exc, tb):
        from .metrics import METRICS
        METRICS.observe_latency(self.bucket, (perf_counter() - self.t0) * 1000.0)

