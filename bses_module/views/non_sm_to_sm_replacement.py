# Create your views here.
# bses_module/views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import logging
# from zonos_northbound_api.northbound_api import NorthboundApi

from bses_module.schemas.schemas import NonSmartToSmartRequest, NonSmartToSmartResponse
from pydantic import ValidationError


from core.models import DeviceInstallation

from bses_module.models import NonSmToSmJob, States

from zonos_northbound_api.northbound_api_v2 import NorthboundApi

from config import settings

from core.models import Consumer, DeviceType, DeviceTemplate
from bses_module.models import NonSmToSmJob

logger = logging.getLogger(__name__)


class NonSmartToSmartReplacementView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = NonSmartToSmartRequest

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.northbound_client: NorthboundApi = NorthboundApi(
            baseUrl=settings.ZONOS_NORTHBOUND_BASE_URL,
            tokenUrl=settings.ZONOS_NORTHBOUND_TOKEN_URL,
            username=settings.ZONOS_NORTHBOUND_USERNAME,
            password=settings.ZONOS_NORTHBOUND_PASSWORD,
        )

    def validation_errors(self, exc: ValidationError):
        return exc.errors(include_url=False, include_context=False, include_input=False)

    @extend_schema(
        summary="UC-05: Non-Smart to Smart Meter Replacement",
        description="API to replace non-smart meters with smart meters or for new service connections",
        request=NonSmartToSmartRequest,
        responses={200: NonSmartToSmartResponse},
        tags=["Meter Lifecycle"],
    )
    def post(self, request, *args, **kwargs):

        try:
            body: NonSmartToSmartRequest = NonSmartToSmartRequest.model_validate(request.data)
            sm_device_id = body.newMeterDetails.metersrno

            # Get SM Device Type and Template
            sm_device_type_name = f"{body.newMeterDetails.paramters.metermake}_{body.newMeterDetails.paramters.meterphase}_{body.newMeterDetails.paramters.metercategory}"
            sm_device_template_name = f"{body.newMeterDetails.paramters.metermake}_{body.newMeterDetails.paramters.meterphase}_{body.newMeterDetails.paramters.metercategory}"
            sm_device_type = DeviceType.objects.filter(name=sm_device_type_name).exists()
            sm_device_template = DeviceTemplate.objects.filter(
                name=sm_device_template_name
            ).exists()

            if not sm_device_type or not sm_device_template:
                raise ValueError("SM device type or template does not exist")

            duplicate_job_exists = NonSmToSmJob.objects.filter(
                sm_device_id=sm_device_id,
                job_status__in=[States.READY, States.IN_PROGRESS],
            ).exists()

            if duplicate_job_exists:
                raise ValidationError(f"Job is already running for smart meter {sm_device_id}")

            # Check if SM device is already installed
            if DeviceInstallation.objects.filter(device_id=sm_device_id, is_active=True).exists():
                raise ValueError(f"SM device {sm_device_id} is already installed")
        except (ValidationError, ValueError) as exc:
            return Response(
                {
                    "status": "ERROR",
                    "errorCode": "REQ001",
                    "message": "Validattion Failed",
                    "errors": self.validation_errors(exc)
                    if isinstance(exc, ValidationError)
                    else repr(exc),
                    "meterReplacementTransactionId": request.data.get(
                        "meterReplacementTransactionId"
                    ),
                    "typeOfReplacementCode": request.data.get("typeOfReplacementCode"),
                    "accountId": request.data.get("consumerMaster")["accountId"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        consumer_id = body.consumerMaster.accountId
        sm_device_id = body.newMeterDetails.metersrno
        non_sm_device_id = body.oldMeterDetails.metersrno if body.oldMeterDetails else None

        try:
            # Create the job

            NonSmToSmJob.objects.create(
                job_id=body.meterReplacementTransactionId,
                consumer_id=consumer_id,
                sm_device_id=sm_device_id,
                non_sm_device_id=non_sm_device_id if non_sm_device_id else "None",
                payload=body.model_dump(mode="json"),
                job_created_at=body.timestamp,
                job_status=States.READY,
            )

            # job = NonSmToSmJob.objects.get(job_id=body.meterReplacementTransactionId)
            return Response(
                {
                    "status": States.READY,
                    "errorCode": "RDY0001",
                    "message": "Non SM to SM job created successfully",
                    "meterReplacementTransactionId": body.meterReplacementTransactionId,
                    "typeOfReplacementCode": body.typeOfReplacementCode,
                    "accountId": body.consumerMaster.accountId,
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
                    "typeOfReplacementCode": body.typeOfReplacementCode,
                    "accountId": body.consumerMaster.accountId,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # # 2. Success response envelope
        # return Response({
        #     "status": "SUCCESS",
        #     "errorCode": None,
        #     "message": "Consumer and meter created successfully",
        #     "meterReplacementTransactionId": data["meterReplacementTransactionId"],
        #     "typeOfReplacementCode": data["typeOfReplacementCode"],
        #     "accountId": data["consumerMaster"]["accountId"]
        # }, status=status.HTTP_200_OK)
