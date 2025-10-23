from __future__ import annotations
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

REQUESTS = Counter(
    'app_requests_total',
    'Total requests',
    labelnames=('endpoint', 'model', 'diet'),
)
ERRORS = Counter(
    'app_errors_total',
    'Total errors',
    labelnames=('type',),
)
LATENCY = Histogram(
    'app_request_latency_ms',
    'Request latency in milliseconds',
    labelnames=('endpoint', 'model'),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

def render_prometheus():
    return generate_latest(), CONTENT_TYPE_LATEST