"""Prometheus metrics collection."""
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Request metrics
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Chat-specific metrics
chat_messages_total = Counter(
    'chat_messages_total',
    'Total chat messages processed',
    ['role']
)

safety_blocks_total = Counter(
    'safety_blocks_total',
    'Total safety blocks',
    ['type']  # 'input' or 'output'
)

router_decisions_total = Counter(
    'router_decisions_total',
    'Total router decisions',
    ['strategy', 'endpoint']
)

interpreter_fallbacks_total = Counter(
    'interpreter_fallbacks_total',
    'Total interpreter fallback calls'
)

# System metrics
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

database_connections = Gauge(
    'database_connections',
    'Number of database connections'
)


def get_metrics_response() -> Response:
    """Get Prometheus metrics as HTTP response."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )



