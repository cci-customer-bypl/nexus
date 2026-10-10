import logging

from django.tasks import task


logger = logging.getLogger(__name__)


@task
def test_task(message: str) -> str:
    logger.info("Django task received message: %s", message)

    return f"Processed: {message}"
