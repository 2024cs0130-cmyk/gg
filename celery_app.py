import os
from datetime import datetime, timezone

from celery import Celery, Task
from celery.schedules import crontab
from kombu import Queue


REDIS_URL = os.getenv("REDIS_URL", "")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

DEFAULT_QUEUE = "default"
DEAD_LETTER_QUEUE = "dead_letter"


class ReliableTask(Task):
    # Global retry policy with exponential backoff and jitter.
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    max_retries = 5

    # Improve delivery guarantees when workers crash mid-task.
    acks_late = True
    reject_on_worker_lost = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        max_retries = self.max_retries if self.max_retries is not None else 0

        # If all retries are exhausted, publish a dead-letter event.
        if self.request.retries >= max_retries:
            self.app.send_task(
                "dead_letter_handler",
                kwargs={
                    "failed_task": {
                        "task_id": task_id,
                        "task_name": self.name,
                        "args": args,
                        "kwargs": kwargs,
                        "exception": str(exc),
                        "retries": self.request.retries,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
                queue=DEAD_LETTER_QUEUE,
                serializer="json",
            )

        super().on_failure(exc, task_id, args, kwargs, einfo)


celery_app = Celery(
    "app",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.Task = ReliableTask

celery_app.conf.update(
    include=["tasks", "health"],
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue=DEFAULT_QUEUE,
    task_queues=(
        Queue(DEFAULT_QUEUE),
        Queue(DEAD_LETTER_QUEUE),
    ),
    task_routes={
        "dead_letter_handler": {"queue": DEAD_LETTER_QUEUE},
    },
    beat_schedule={
        "poll-missed-commits-every-15-min": {
            "task": "poll_missed_commits",
            "schedule": crontab(minute="*/15"),
        }
    },
    timezone="UTC",
)


@celery_app.task(name="dead_letter_handler", bind=True)
def dead_letter_handler(self, failed_task):
    # Placeholder DLQ consumer: keep payload in result backend for inspection.
    return failed_task


# Import health module to register periodic tasks at startup.
import health  # noqa: E402,F401
