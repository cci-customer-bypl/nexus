from django.tasks import task
import logging
from datetime import datetime, timezone

from bses_module.models import BillingRcmJob

from bses_module.schemas.schemas import BillingRcmRequest

from zonos_northbound_api.northbound_client import client


logger = logging.getLogger(__name__)


def launch_dct(job: BillingRcmJob) -> None:
    job_obj = job
    device_id = job.device_id
    external_id = job.external_id
    profile_id = "Billing Profile"
    reading_reason = job.reading_reason
    from_time = job.from_time
    to_time = job.to_time
    try:
        client.createReadProfile(
            deviceId=device_id.device_id,
            externalId=external_id,
            profileId=profile_id,
            readingReason=int(reading_reason),
            fromTime=from_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            toTime=to_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        job_obj.message = "Job launched successfully"
        job_obj.remaining_attempts = job_obj.remaining_attempts - 1
        job_obj.job_last_run_at = datetime.now()
        job_obj.save()
    except Exception as e:
        logger.error(f"Error launching DCT job: {e}")
        job_obj.message = str(e)
        job_obj.save()


@task
def scheduled_launch_dct():
    jobs = BillingRcmJob.objects.filter(remaining_attempts__gt=0)
    logger.info(f"Found {len(jobs)} jobs")

    for job in jobs:
        launch_dct(job)
