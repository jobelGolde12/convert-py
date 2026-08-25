from __future__ import annotations

import os
from celery import Celery

BROKER = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
BACKEND = BROKER

app = Celery(
    "convert",
    broker=BROKER,
    backend=BACKEND,
    include=["app.workers.office_worker"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=29 * 60,
    worker_prefetch_multiplier=1,
)
