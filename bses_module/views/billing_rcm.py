# Create your views here.

from datetime import datetime, timezone

from drf_spectacular.utils import extend_schema
from pydantic import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from httpx._exceptions import HTTPStatusError
from bses_module.schemas import BillingRcmRequest, BillingRcmResponse
from config import settings
from zonos_northbound_api.northbound_api import NorthboundApi
from bses_module.models import States
from bses_module.models import BillingRcmJob


class BillingRcmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.northbound_client: NorthboundApi = NorthboundApi(
            baseUrl=settings.ZONOS_NORTHBOUND_BASE_URL,
            tokenUrl=settings.ZONOS_NORTHBOUND_TOKEN_URL,
            username=settings.ZONOS_NORTHBOUND_USERNAME,
            password=settings.ZONOS_NORTHBOUND_PASSWORD,
        )

    def validation_errors(self, body: dict, exc: ValidationError) -> BillingRcmResponse:

        return BillingRcmResponse(
            status=States.FAILED,
            errorCode="REQ001",
            message="Validattion Failed",
            errors=exc.errors(include_url=False, include_context=False, include_input=False),
            externalId=body.get("externalId", ""),
        )

    def launch_odr(self, data: BillingRcmRequest):

        profile_id = "Billing Profile"
        response = self.northbound_client.bulkCreateReadProfile(
            data.devices,
            profile_id,
            data.readingReason,
            data.fromTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            data.toTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            data.externalId,
            datetime.now().astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            datetime.now()
            .replace(hour=23, minute=50, second=0, microsecond=0)
            .astimezone(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
            0,
            3600,
        )
        return response

    def insert_job(self, body: BillingRcmRequest):
        try:
            # Create the job

            for device_id in body.devices:
                BillingRcmJob.objects.create(
                    device_id=device_id,
                    external_id = body.externalId,
                    from_time = body.fromTime,
                    to_time = body.toTime,
                    reading_reason = body.readingReason,
                    job_created_at=datetime.now(),
                    job_status=States.READY,
                    remaining_attempts=3,
                    message=body.model_dump(mode="json"),
                )

            # job = BillingRcmJob.objects.get(job_id=body.meterReplacementTransactionId)
            return Response(
                {
                    "status": States.READY,
                    "errorCode": None,
                    "message": "Non SM to SM job created successfully",
                    "externalId": body.externalId,
                    "errors": []
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "status": "ERROR",
                    "errorCode": "REQ002",
                    "message": "Failed to create job",
                    "errors": repr(e),
                    "meterReplacementTransactionId": body.meterReplacementTransactionId,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="RCM - MDM ODR Billing Integration: Scheduled Daily ODR",
        description="Public endpoint for scheduling a Meter Reading Order (MRO), executing one Current Billing On-Demand Reading (ODR) per day",
        request=BillingRcmRequest,
        responses={200: BillingRcmResponse},
        tags=["On Demand Reading"],
    )
    def post(self, request, *args, **kwargs):
        try:
            # 1. Validate request using Pydantic
            body = BillingRcmRequest.model_validate(request.data)

        except ValidationError as exc:
            return Response(
                self.validation_errors(request.data, exc).model_dump(mode="json"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # data is now an OdrInbound Pydantic object
            self.launch_odr(body)
            self.insert_job(body)

            # 2. Success response envelope
            return Response(
                BillingRcmResponse(
                    status=States.READY,
                    errorCode=None,
                    message="ODR launched successfully",
                    externalId=body.externalId,
                    errors=[],
                ).model_dump(mode="json"),
                status=status.HTTP_200_OK,
            )
        except HTTPStatusError as error:
            # logger.error(f"Error launching ODR: {error}")
            return Response(
                BillingRcmResponse(
                    status=States.FAILED,
                    errorCode="REQ001",
                    message="Error launching ODR",
                    externalId=body.externalId,
                    errors=error.response.json(),
                ).model_dump(mode="json"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as error:
            # logger.error(f"Error launching ODR: {error}")
            return Response(
                BillingRcmResponse(
                    status=States.FAILED,
                    errorCode="REQ001",
                    message="Error launching ODR",
                    externalId=body.externalId,
                    errors=[],
                ).model_dump(mode="json"),
                status=status.HTTP_400_BAD_REQUEST,
            )
