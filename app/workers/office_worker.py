from __future__ import annotations

import logging
import signal
import time

logger = logging.getLogger(__name__)


def run_office_worker(poll_interval: float = 1.0) -> None:
    running = True

    def handle_signal(signum, _frame):
        nonlocal running
        running = False
        logger.info("shutdown requested")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger.info("office worker starting")
    while running:
        # In a real deployment this would consume from Celery/Redis queue.
        # For Phase 4 we keep the inline FastAPI background task path and this
        # worker as a placeholder for later queue integration.
        time.sleep(poll_interval)
    logger.info("office worker stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_office_worker()
