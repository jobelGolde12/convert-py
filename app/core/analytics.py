"""Privacy-aware, server-side analytics event log.

Events are written as single-line structured JSON to the ``convert.analytics``
logger. No PII is collected: no IPs, filenames, emails, or user content — only
operational properties (format names, durations, byte counts, error codes).

Retention/destination is deployment-controlled by routing the
``convert.analytics`` logger (e.g. to a log shipper). Disable by setting the
logger level above INFO or removing the handler in logging configuration.
"""

from __future__ import annotations

import json
import logging

from app.core.clock import utcnow

_logger = logging.getLogger("convert.analytics")

ALLOWED_EVENTS = {
    "conversion_completed",
    "conversion_failed",
    "job_cancelled",
    "file_uploaded",
}


def track_event(event: str, **props: object) -> None:
    """Record one analytics event with a fixed schema and allow-listed names."""
    if event not in ALLOWED_EVENTS:
        _logger.warning("dropped unknown analytics event: %s", event)
        return
    payload = {"event": event, "ts": utcnow().isoformat(), **props}
    try:
        _logger.info(json.dumps(payload, separators=(",", ":"), default=str))
    except Exception:  # analytics must never break the request path
        pass
