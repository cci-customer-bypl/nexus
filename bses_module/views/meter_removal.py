# Create your views here.
# bses_module/views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import logging
# from zonos_northbound_api.northbound_api import NorthboundApi

from bses_module.schemas import MeterRemovalRequest, MeterRemovalResponse
from pydantic import ValidationError


from core.models import DeviceInstallation

from bses_module.models import MeterRemovalJob, States

from zonos_northbound_api.northbound_api_v2 import NorthboundApi

from config import settings

from core.models import Consumer, DeviceType, DeviceTemplate

logger = logging.getLogger(__name__)


class MeterRemovalView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = MeterRemovalRequest

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
        summary="Meter Removal",
        description="API to removal meters",
        request=MeterRemovalRequest,
        responses={200: MeterRemovalResponse},
        tags=["Meter Lifecycle"],
    )
    def post(self, request, *args, **kwargs):

        try:
            body: MeterRemovalRequest = MeterRemovalRequest.model_validate(request.data)
            sm_device_id = body.meterDetails.metersrno

            # Get SM Device Type and Template
            sm_device_type_name = f"{body.meterDetails.metermake}_{body.meterDetails.meterphase}_{body.meterDetails.metercategory}"
            sm_device_template_name = f"{body.meterDetails.metermake}_{body.meterDetails.meterphase}_{body.meterDetails.metercategory}"
            sm_device_type = DeviceType.objects.filter(name=sm_device_type_name).exists()
            sm_device_template = DeviceTemplate.objects.filter(
                name=sm_device_template_name
            ).exists()

            if not sm_device_type or not sm_device_template:
                raise ValueError("SM device type or template does not exist")

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
                    "meterRemovalTransactionId": request.data.get(
                        "meterRemovalTransactionId"
                    ),
                    "typeOfRemovalCode": request.data.get("typeOfRemovalCode"),
                    "accountId": request.data.get("consumerMaster")["accountId"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        consumer_id = body.consumerMaster.accountId
        sm_device_id = body.meterDetails.metersrno
        non_sm_device_id = body.oldMeterDetails.metersrno if body.oldMeterDetails else None

        try:
            # Create the job

            MeterRemovalJob.objects.create(
                job_id=body.meterRemovalTransactionId,
                consumer_id=consumer_id,
                sm_device_id=sm_device_id,
                non_sm_device_id=non_sm_device_id if non_sm_device_id else "None",
                payload=body.model_dump(mode="json"),
                job_created_at=body.timestamp,
                job_status=States.READY,
            )

            # job = MeterRemovalJob.objects.get(job_id=body.meterRemovalTransactionId)
            return Response(
                {
                    "status": States.READY,
                    "errorCode": None,
                    "message": "Non SM to SM job created successfully",
                    "meterRemovalTransactionId": body.meterRemovalTransactionId,
                    "typeOfRemovalCode": body.typeOfRemovalCode,
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
                    "meterRemovalTransactionId": body.meterRemovalTransactionId,
                    "typeOfRemovalCode": body.typeOfRemovalCode,
                    "accountId": body.consumerMaster.accountId,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # # 2. Success response envelope
        # return Response({
        #     "status": "SUCCESS",
        #     "errorCode": None,
        #     "message": "Consumer and meter created successfully",
        #     "meterRemovalTransactionId": data["meterRemovalTransactionId"],
        #     "typeOfRemovalCode": data["typeOfRemovalCode"],
        #     "accountId": data["consumerMaster"]["accountId"]
        # }, status=status.HTTP_200_OK)
