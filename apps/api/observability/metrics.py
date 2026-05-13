"""Application metrics collection for monitoring dashboards."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EndpointMetrics:
    total_requests: int = 0
    total_errors: int = 0
    total_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    _latencies: list = field(default_factory=list)

    def record(self, latency_ms: float, is_error: bool = False) -> None:
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        if is_error:
            self.total_errors += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-500:]
        self._recalculate_percentiles()

    def _recalculate_percentiles(self) -> None:
        if not self._latencies:
            return
        sorted_l = sorted(self._latencies)
        n = len(sorted_l)
        self.p50_latency_ms = sorted_l[int(n * 0.5)]
        self.p95_latency_ms = sorted_l[int(n * 0.95)]
        self.p99_latency_ms = sorted_l[min(int(n * 0.99), n - 1)]

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0
        return round(self.total_latency_ms / self.total_requests, 2)

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return round(self.total_errors / self.total_requests * 100, 2)


class MetricsCollector:
    """In-process metrics collector. Exposes stats via /metrics endpoint."""

    def __init__(self):
        self._endpoints: dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self._start_time = time.time()

    def record_request(self, path: str, latency_ms: float, status_code: int) -> None:
        is_error = status_code >= 500
        normalized = self._normalize_path(path)
        self._endpoints[normalized].record(latency_ms, is_error)

    def get_stats(self) -> dict:
        uptime = time.time() - self._start_time
        total_requests = sum(e.total_requests for e in self._endpoints.values())
        total_errors = sum(e.total_errors for e in self._endpoints.values())

        top_endpoints = sorted(
            self._endpoints.items(),
            key=lambda x: x[1].total_requests,
            reverse=True,
        )[:10]

        return {
            "uptime_seconds": round(uptime, 0),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_pct": round(total_errors / max(total_requests, 1) * 100, 2),
            "endpoints": {
                path: {
                    "requests": m.total_requests,
                    "errors": m.total_errors,
                    "avg_ms": m.avg_latency_ms,
                    "p95_ms": round(m.p95_latency_ms, 2),
                    "p99_ms": round(m.p99_latency_ms, 2),
                    "error_rate_pct": m.error_rate,
                }
                for path, m in top_endpoints
            },
        }

    def _normalize_path(self, path: str) -> str:
        parts = path.rstrip("/").split("/")
        normalized = []
        for part in parts:
            try:
                if len(part) == 36 and part.count("-") == 4:
                    normalized.append(":id")
                    continue
            except (ValueError, AttributeError):
                pass
            normalized.append(part)
        return "/".join(normalized)


metrics_collector = MetricsCollector()
