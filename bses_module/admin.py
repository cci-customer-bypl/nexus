from django.contrib import admin

from .models import BillingRcmJob, NonSmToSmJob, MeterRemovalJob, SmToSmJob


@admin.register(BillingRcmJob)
class BillingRcmJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "device_id",
        "external_id",
        "reading_reason",
        "remaining_attempts",
        "job_created_at",
        "job_last_run_at",
    )

    list_filter = (
        "reading_reason",
        "job_created_at",
        "job_last_run_at",
    )

    search_fields = (
        "job_id",
        "external_id",
        "device_id__id",
    )

    readonly_fields = ("job_id", "job_created_at", "job_last_run_at")

    ordering = ("-job_created_at",)

    # device_id is still a ForeignKey, so this is valid
    list_select_related = ("device_id",)

    date_hierarchy = "job_created_at"

    fieldsets = (
        (
            "Job Information",
            {
                "fields": (
                    "job_id",
                    "external_id",
                    "device_id",
                    "reading_reason",
                )
            },
        ),
        (
            "Reading Period",
            {
                "fields": (
                    "from_time",
                    "to_time",
                )
            },
        ),
        (
            "Execution Information",
            {
                "fields": (
                    "remaining_attempts",
                    "job_created_at",
                    "job_last_run_at",
                    "message",
                )
            },
        ),
    )


@admin.register(NonSmToSmJob)
class NonSmToSmJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "job_status",
        "consumer_id",
        "service_point_id",
        "non_sm_device_id",
        "sm_device_id",
        "retries",
        "job_created_at",
        "job_run_at",
    )

    list_filter = (
        "job_status",
        "job_created_at",
    )

    # These are now CharFields, so search them directly.
    search_fields = (
        "job_id",
        "consumer_id",
        "service_point_id",
        "sm_device_id",
        "non_sm_device_id",
    )

    readonly_fields = (
        "job_id",
        "job_created_at",
        "job_run_at",
    )

    ordering = ("-job_created_at",)

    date_hierarchy = "job_created_at"

    fieldsets = (
        (
            "Job Information",
            {
                "fields": (
                    "job_id",
                    "job_status",
                    "job_message",
                )
            },
        ),
        (
            "Device Migration",
            {
                "fields": (
                    "non_sm_device_id",
                    "sm_device_id",
                )
            },
        ),
        (
            "Consumer & Service Point",
            {
                "fields": (
                    "consumer_id",
                    "service_point_id",
                )
            },
        ),
        (
            "Execution Information",
            {
                "fields": (
                    "job_created_at",
                    "job_run_at",
                    "retries",
                )
            },
        ),
        (
            "Payload",
            {
                "fields": ("payload",),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(MeterRemovalJob)
class MeterRemovalJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "sm_device_id",
        "job_created_at",
        "job_run_at",
    )

    list_filter = (
        "job_created_at",
        "job_run_at",
    )

    search_fields = (
        "job_id",
        "sm_device_id__id",
    )

    readonly_fields = ("job_id", "job_created_at", "job_run_at")

    ordering = ("-job_created_at",)

    # device_id is still a ForeignKey, so this is valid
#    list_select_related = ("sm_device_id",)

    date_hierarchy = "job_created_at"

    fieldsets = (
        (
            "Job Information",
            {
                "fields": (
                    "job_id",
                    "sm_device_id",
                )
            },
        ),
        (
            "Execution Information",
            {
                "fields": (
                    "job_created_at",
                    "job_run_at",
                    "job_message",
                )
            },
        ),
    )


@admin.register(SmToSmJob)
class SmToSmJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "job_status",
        "consumer_id",
        "service_point_id",
        "old_sm_device_id",
        "new_sm_device_id",
        "retries",
        "job_created_at",
        "job_run_at",
    )

    list_filter = (
        "job_status",
        "job_created_at",
    )

    # These are now CharFields, so search them directly.
    search_fields = (
        "job_id",
        "consumer_id",
        "service_point_id",
        "new_sm_device_id",
        "old_sm_device_id",
    )

    readonly_fields = (
        "job_id",
        "job_created_at",
        "job_run_at",
    )

    ordering = ("-job_created_at",)

    date_hierarchy = "job_created_at"

    fieldsets = (
        (
            "Job Information",
            {
                "fields": (
                    "job_id",
                    "job_status",
                    "job_message",
                )
            },
        ),
        (
            "Device Migration",
            {
                "fields": (
                    "old_sm_device_id",
                    "new_sm_device_id",
                )
            },
        ),
        (
            "Consumer & Service Point",
            {
                "fields": (
                    "consumer_id",
                    "service_point_id",
                )
            },
        ),
        (
            "Execution Information",
            {
                "fields": (
                    "job_created_at",
                    "job_run_at",
                    "retries",
                )
            },
        ),
        (
            "Payload",
            {
                "fields": ("payload",),
                "classes": ("collapse",),
            },
        ),
    )