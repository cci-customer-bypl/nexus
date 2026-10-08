# from django.core.validators import MinValueValidator
from datetime import datetime
from django.db import models

from core.models import Device

from uuid import uuid4

# Create your models here.


class BillingRcmJob(models.Model):
    job_id = models.UUIDField(primary_key=True, default=uuid4, editable=False, db_column="job_id")
    device_id = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="billing_rcm_records",
        db_column="device_id",
    )
    external_id = models.CharField(max_length=100, db_column="external_id")
    from_time = models.DateTimeField(db_column="from_time")
    to_time = models.DateTimeField(db_column="to_time")
    reading_reason = models.CharField(max_length=100, db_column="reading_reason")
    job_created_at = models.DateTimeField(auto_now_add=True, db_column="job_created_at")
    job_last_run_at = models.DateTimeField(null=True, blank=True, db_column="job_last_run_at")
    remaining_attempts = models.PositiveIntegerField(
        default=1,
        help_text="Number of execution attempts remaining",
        db_column="remaining_attempts",
    )
    message = models.TextField(null=True, blank=True, db_column="message")

    class Meta:
        db_table = "billing_rcm_jobs"
        ordering = ["-job_created_at"]
        indexes = [
            models.Index(fields=["remaining_attempts"], name="billing_rcm_retries_idx"),
        ]

    def __str__(self):
        return f"{self.device_id} - {self.external_id}"


class States(models.TextChoices):
    READY = "READY", "Ready"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class NonSmToSmJob(models.Model):
    job_id = models.CharField(max_length=100, primary_key=True, editable=False, db_column="job_id")
    sm_device_id = models.CharField(max_length=100, db_column="sm_device_id")
    non_sm_device_id = models.CharField(max_length=100, null=True, db_column="non_sm_device_id")
    consumer_id = models.CharField(max_length=100, db_column="consumer_id")
    service_point_id = models.CharField(max_length=100, null=True, db_column="service_point_id")
    job_created_at = models.DateTimeField(auto_now_add=True, db_column="job_created_at")
    job_run_at = models.DateTimeField(auto_now=True, db_column="job_run_at")
    payload = models.JSONField(db_column="payload")
    job_status = models.CharField(max_length=100, choices=States.choices, db_column="job_status")
    job_message = models.TextField(db_column="job_message")
    retries = models.IntegerField(
        default=1,
        help_text="Number of times the job has been retried",
        db_column="retries",
    )

    class Meta:
        db_table = "non_sm_to_sm_jobs"
        ordering = ["-job_created_at"]
        indexes = [
            models.Index(fields=["job_id"], name="non_sm_to_sm_jobs_job_id_idx"),
        ]

    def __str__(self):
        return f"{self.job_id},{self.job_status},{self.consumer_id},{self.service_point_id},{self.non_sm_device_id},{self.sm_device_id}"


class MeterRemovalJob(models.Model):
    job_id = models.CharField(max_length=100, primary_key=True, editable=False, db_column="job_id")
    sm_device_id = models.CharField(max_length=100, db_column="sm_device_id")
    consumer_id = models.CharField(max_length=100, db_column="consumer_id")
    service_point_id = models.CharField(max_length=100, null=True, db_column="service_point_id")
    job_created_at = models.DateTimeField(auto_now_add=True, db_column="job_created_at")
    job_run_at = models.DateTimeField(auto_now=True, db_column="job_run_at")
    payload = models.JSONField(db_column="payload")
    job_status = models.CharField(max_length=100, choices=States.choices, db_column="job_status")
    job_message = models.TextField(db_column="job_message")
    retries = models.IntegerField(
        default=1,
        help_text="Number of times the job has been retried",
        db_column="retries",
    )

    class Meta:
        db_table = "meter_removal_jobs"
        ordering = ["-job_created_at"]
        indexes = [
            models.Index(fields=["job_id"], name="non_sm_to_sm_jobs_job_id_idx"),
        ]

    def __str__(self):
        return f"{self.job_id},{self.job_status},{self.consumer_id},{self.service_point_id},{self.sm_device_id}"
