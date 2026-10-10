# from datetime import datetime, timezone
# import logging

# from airflow.sdk import DAG, task

# import django

# django.setup()

# from bses_module.models import BillingRcmJob

# from bses_module.schemas import BillingRcmRequest

# from zonos_northbound_api.northbound_client import client


# logger = logging.getLogger(__name__)

# with DAG(
#     dag_id="billing_rcm",
#     start_date=datetime(2025, 1, 1),
#     schedule="0 0 * * *",
#     catchup=False,
# ) as dag:

#     @task.short_circuit
#     def get_jobs() -> list[dict]:
#         jobs = BillingRcmJob.objects.filter(remaining_attempts__gt=0)
#         logger.info(f"Found {len(jobs)} jobs")

#         if jobs.count() >= 1:
#             return list(
#                 jobs.values(
#                     "job_id",
#                     "device_id",
#                     "external_id",
#                     "from_time",
#                     "to_time",
#                     "reading_reason",
#                     "job_created_at",
#                     "job_last_run_at",
#                     "job_run_count",
#                     "message",
#                 )
#             )

#     @task
#     def launch_dct(job: dict) -> None:
#         job_obj = BillingRcmJob.objects.get(job_id=job["job_id"])
#         device_id = job["device_id"]
#         external_id = job["external_id"]
#         profile_id = "Billing Profile"
#         reading_reason = job["reading_reason"]
#         from_time = job["from_time"]
#         to_time = job["to_time"]
#         try:
#             client.createReadProfile(
#                 deviceId=device_id,
#                 externalId=external_id,
#                 profileId=profile_id,
#                 readingReason=reading_reason,
#                 fromTime=from_time,
#                 toTime=to_time,
#             )
#             job_obj.message = "Job launched successfully"
#             job_obj.remaining_attempts = job_obj.remaining_attempts - 1
#             job_obj.job_last_run_at = datetime.now()
#             job_obj.save()
#         except Exception as e:
#             logger.error(f"Error launching DCT job: {e}")
#             job_obj.message = str(e)
#             job_obj.save()

#     jobs = get_jobs()
#     launch_dct.expand(job=jobs)
