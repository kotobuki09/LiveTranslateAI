import time
from collections import defaultdict


class PipelineMetrics:
    def __init__(self):
        self._marks: dict = defaultdict(list)
        self._latencies: dict = defaultdict(list)
        self._errors: dict = defaultdict(int)

    def mark(self, stage: str) -> None:
        self._marks[stage].append(time.monotonic())

    def observe_latency_ms(self, name: str, value: float) -> None:
        self._latencies[name].append(value)

    def inc_error(self, kind: str) -> None:
        self._errors[kind] += 1

    def error_count(self, kind: str) -> int:
        return self._errors[kind]

    def p50_latency_ms(self, name: str) -> float | None:
        vals = sorted(self._latencies.get(name, []))
        return vals[len(vals) // 2] if vals else None
