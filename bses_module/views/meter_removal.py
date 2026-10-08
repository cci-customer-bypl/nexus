# Create your views here.
# bses_module/views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import logging
# from zonos_northbound_api.northbound_api import NorthboundApi

from bses_module.schemas.meter_removal import MeterRemovalRequest, MeterRemovalResponse
from pydantic import ValidationError


from core.models import DeviceInstallation

#from bses_module.models import MeterRemovalJob, States

from zonos_northbound_api.northbound_api_v2 import NorthboundApi

from config import settings

from core.models import Consumer, DeviceType, DeviceTemplate

from zonos_northbound_api.northbound_client import client_v2
from django.db import transaction

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
        description="API to remove meters",
        request=MeterRemovalRequest,
        responses={200: MeterRemovalResponse},
        tags=["Meter Lifecycle"],
    )
    def post(self, request, *args, **kwargs):

        try:
            body: MeterRemovalRequest = MeterRemovalRequest.model_validate(request.data)
            sm_device_id = body.meterDetails.metersrno

            # Check if SM device is already installed
            if not DeviceInstallation.objects.filter(device_id=sm_device_id, is_active=True).exists():
                raise ValueError(f"SM device {sm_device_id} is not installed")
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

        consumer_id = body.accountId
        job_id = body.meterRemovalTransactionId,

        try:
            # Create the job

            MeterRemovalJob.objects.create(
                job_id=job_id
                consumer_id=consumer_id,
                sm_device_id=sm_device_id,
                service_point_id = device_installation.objects.get(device=sm_device_id,is_active=True).service_point,
                payload=body.model_dump(mode="json"),
                job_created_at=body.timestamp,
                job_status=States.READY,
            )

            return Response(
                {
                    "status": States.READY,
                    "errorCode": None,
                    "message": "Meter Removal job created successfully",
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

        job_obj = MeterRemovalJob.objects.get(job_id=job_id)
        job_obj.job_message = f"{job_obj.job_message}\n Processing Meter Removal"
        job_obj.save()
        try:
            with transaction.atomic():
                # Call ZONOS API to achieve
                # 1) Update device parameters,
                # 2) Uninstall device and
                # 3) Close metering point association

                # Update device parameters
                device_parameters = {
                    f"ext.{key}": value
                    for key, value in body.meterDetails.parameters.model_dump(
                        exclude={"meterstatus", "meterremovaldate"},
                        mode="json",
                    ).items()
                }

                response = client_v2.bulkSetDeviceParameters(
                    device=sm_device_id,
                    parameters=device_parameters,
                )
                logger.info(f"Device parameters set response: {response}")

                # Uninstall device 
                response = client_v2.uninstallDevice(
                    device=sm_device_id,
                )
                logger.info(f"Device uninstallation response: {response}")

                # Close metering point association
                response = client_v2.closeMeteringPointAssociation(
                    metering_point=service_point_id,
                    device=sm_device_id,
                )
                logger.info(f"Close Metering Point association response: {response}")

#            except Exception as e:
#                logger.error(f"Device parameters set error in task_2: {e}")
#                job_obj.job_status = States.FAILED
#                job_obj.job_message = (
#                    f"{job_obj.job_message} > zonos metering point parameters set failed ({repr(e)})"
#                )
#                job_obj.save()
#                raise e
            logger.info(f"Meter Removal completed successfully for job {job_obj.job_id}")
            job_obj.job_status = States.SUCCESS
            job_obj.job_message = "Meter Removal completed successfully"
            job_obj.save()
        except Exception as e:
            logger.error(f"Error in Meter Removal: {e}")
            job_obj.job_status = States.FAILED
            job_obj.job_message = str(e)
            job_obj.save()
            raise e
            

        # # 2. Success response envelope
        # return Response({
        #     "status": "SUCCESS",
        #     "errorCode": None,
        #     "message": "Consumer and meter created successfully",
        #     "meterRemovalTransactionId": data["meterRemovalTransactionId"],
        #     "typeOfRemovalCode": data["typeOfRemovalCode"],
        #     "accountId": data["consumerMaster"]["accountId"]
        # }, status=status.HTTP_200_OK)
