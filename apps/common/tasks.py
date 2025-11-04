from celery import shared_task
import time


@shared_task(bind=True)
def ping(self, delay: int = 0) -> str:
    """Simple health task to verify Celery worker is running.

    Args:
        delay: optional sleep seconds to simulate work
    Returns:
        str: pong message
    """
    if delay:
        time.sleep(delay)
    return "pong"
