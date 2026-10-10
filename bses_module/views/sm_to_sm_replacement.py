# Create your views here.
# bses_module/views.py
from datetime import datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import logging

from bses_module.schemas.sm_to_sm import SmartToSmartRequest, SmartToSmartResponse
from pydantic import ValidationError

from core.models import DeviceInstallation

from bses_module.models import SmToSmJob, States

from zonos_northbound_api.northbound_api_v2 import NorthboundApi
from zonos_northbound_api.northbound_client import client_v2

from config import settings

from core.models import Consumer, DeviceType, DeviceTemplate


from zoneinfo import ZoneInfo

from django.db import transaction
from core.models import (
    Device,
    DeviceStatus,
    Consumer,
    ServicePoint,
    DeviceInstallation,
    Contract,
    ElectricalNode,
    GeographicalNode,
    PaymentType,
    ConsumerParameterDefinition,
    ConsumerParameterValue,
    ServicePointParameterDefinition,
    ServicePointParameterValue,
    DeviceParameterDefinition,
    DeviceParameterValue,
    DeviceInstallationParameterDefinition,
    DeviceInstallationParameterValue,
)

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


def ensure_consumer(consumer_id: str, consumer_name: str) -> tuple[Consumer, bool]:
    consumer, created = Consumer.objects.get_or_create(
        consumer_id=consumer_id,
        defaults={
            "consumer_name": consumer_name,
        },
    )
    if created:
        logger.info(f"Consumer {consumer_id} created")
    else:
        logger.info(f"Consumer {consumer_id} already exists")
    return (consumer, created)


def create_service_point(
    service_point_id: str,
    electrical_node: ElectricalNode,
    geographical_node: GeographicalNode,
) -> ServicePoint:
    service_point = ServicePoint.objects.create(
        id=service_point_id,
        electrical_node=electrical_node,
        geographical_node=geographical_node,
    )
    logger.info(f"Service point {service_point_id} created")
    return service_point


def ensure_device(
    device_id: str, device_type: DeviceType, device_template: DeviceTemplate
) -> tuple[Device, bool]:
    device, created = Device.objects.get_or_create(
        device_id=device_id,
        defaults={
            "device_type": device_type,
            "device_template": device_template,
        },
    )
    if created:
        logger.info(f"Device {device_id} created")
    else:
        logger.info(f"Device {device_id} already exists")
    return (device, created)


def create_contract(
    service_point: ServicePoint, consumer: Consumer, start_date: datetime, payment_type: PaymentType
) -> Contract:
    contract = Contract.objects.create(
        consumer=consumer,
        service_point=service_point,
        start_date=start_date,
        is_active=True,
        payment_type=payment_type,
    )
    logger.info(f"Contract {contract.id} created")
    return contract


def create_device_installation(
    device: Device,
    service_point: ServicePoint,
    is_active: bool,
    start_date: datetime,
    end_date: datetime | None = None,
):
    device_installation = DeviceInstallation.objects.create(
        device=device,
        service_point=service_point,
        is_active=is_active,
        start_date=start_date,
        end_date=end_date,
    )
    logger.info(f"Device installation {device_installation.id} created")
    return device_installation


def bulk_set_consumer_parameters(consumer: Consumer, parameter_config: dict) -> None:
    parameters = ConsumerParameterDefinition.objects.filter(name__in=parameter_config.keys())
    ConsumerParameterValue.objects.bulk_create(
        [
            ConsumerParameterValue(
                consumer=consumer,
                parameter=parameter,
                value=parameter_config[parameter.name],
            )
            for parameter in parameters
        ]
    )


def bulk_set_service_point_parameters(service_point: ServicePoint, parameter_config: dict) -> None:
    parameters = ServicePointParameterDefinition.objects.filter(name__in=parameter_config.keys())
    ServicePointParameterValue.objects.bulk_create(
        [
            ServicePointParameterValue(
                service_point=service_point,
                parameter=parameter,
                value=parameter_config[parameter.name],
            )
            for parameter in parameters
        ]
    )


def bulk_set_device_parameters(device: Device, parameter_config: dict) -> None:
    parameters = DeviceParameterDefinition.objects.filter(name__in=parameter_config.keys())
    DeviceParameterValue.objects.bulk_create(
        [
            DeviceParameterValue(
                device=device,
                parameter=parameter,
                value=parameter_config[parameter.name],
            )
            for parameter in parameters
        ]
    )


def bulk_set_new_sm_device_installation_parameters(
    device_installation: DeviceInstallation, parameter_config: dict
) -> None:
    parameters = DeviceInstallationParameterDefinition.objects.filter(
        name__in=parameter_config.keys()
    )
    DeviceInstallationParameterValue.objects.bulk_create(
        [
            DeviceInstallationParameterValue(
                device_installation=device_installation,
                parameter=parameter,
                start_value=parameter_config[parameter.name],
            )
            for parameter in parameters
        ]
    )


def bulk_set_old_sm_device_installation_parameters(
    device_installation: DeviceInstallation,
    parameter_config: dict,
) -> None:

    parameters = DeviceInstallationParameterDefinition.objects.filter(
        name__in=parameter_config.keys()
    )

    for parameter in parameters:
        obj, created = DeviceInstallationParameterValue.objects.update_or_create(
            device_installation=device_installation,
            parameter=parameter,
            defaults={
                "end_value": parameter_config[parameter.name],
            },
        )

        logger.info(
            "Installation parameter %s: %s",
            parameter.name,
            "created" if created else "updated",
        )


class SmartToSmartReplacementView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = SmartToSmartRequest

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
        summary="Smart to Smart Meter Replacement",
        description="API to replace smart meters with smart meters or for new service connections",
        request=SmartToSmartRequest,
        responses=SmartToSmartResponse,
        tags=["Meter Lifecycle"],
    )
    def post(self, request, *args, **kwargs):

        body: SmartToSmartRequest = SmartToSmartRequest.model_validate(request.data)
        try:
            new_sm_device_id = body.newMeterDetails.metersrno
            old_sm_device_id = body.oldMeterDetails.metersrno

            # Get SM Device Type and Template
            new_sm_device_type_name = f"{body.newMeterDetails.parameters.metermake}_{body.newMeterDetails.parameters.meterphase}_{body.newMeterDetails.parameters.metercategory}"
            new_sm_device_template_name = f"{body.newMeterDetails.parameters.metermake}_{body.newMeterDetails.parameters.meterphase}_{body.newMeterDetails.parameters.metercategory}"
            new_sm_device_type = DeviceType.objects.filter(name=new_sm_device_type_name).exists()
            new_sm_device_template = DeviceTemplate.objects.filter(
                name=new_sm_device_template_name
            ).exists()

            if not new_sm_device_type or not new_sm_device_template:
                raise ValueError("SM device type or template does not exist")

            # Check if old SM device is already not installed
            if not DeviceInstallation.objects.filter(
                device_id=old_sm_device_id, is_active=True
            ).exists():
                raise ValueError(f"Old SM device {old_sm_device_id} is already not installed")

            # Check if new SM device is already installed
            if DeviceInstallation.objects.filter(
                device_id=new_sm_device_id, is_active=True
            ).exists():
                raise ValueError(f"New SM device {new_sm_device_id} is already installed")
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
                    "accountId": request.data.get("accountId"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        consumer_id = body.accountId

        try:
            # Create the job

            job_id = (body.meterReplacementTransactionId,)
            SmToSmJob.objects.create(
                job_id=job_id,
                consumer_id=consumer_id,
                old_sm_device_id=old_sm_device_id,
                new_sm_device_id=new_sm_device_id,
                payload=body.model_dump(mode="json"),
                job_created_at=body.timestamp,
                job_status=States.READY,
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
                    "accountId": body.accountId,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(f"Processing job {job_id}")
        logger.debug(f"Job: {job_id}")
        job_obj = SmToSmJob.objects.get(job_id=job_id)
        job_obj.job_status = States.IN_PROGRESS
        job_obj.job_message = f"{job_obj.job_message}\n Processing job {job_id}"
        job_obj.save()
        logger.info(f"Updated {job_id} job status to IN_PROGRESS")

        #            Task 1
        #                - ensure consumer
        #                - ensure service point
        #                - ensure new_sm_device
        #                - ensure old_sm_device
        #                - create contract
        #                - create new_sm_device installation
        #                - create old_sm_device uninstallation
        #                - else rollback

        try:
            with transaction.atomic():
                # Get consumer
                #                consumer = Consumer.objects.get(consumer_id=consumer_id)
                #                logger.info(f"Consumer {consumer_id} already exists")

                new_sm_device_template = DeviceTemplate.objects.get(
                    name=new_sm_device_template_name
                )
                new_sm_device_type = DeviceType.objects.get(name=new_sm_device_type_name)

                # Get Old Device
                old_sm_device = Device.objects.get(device_id=old_sm_device_id)
                old_sm_device.status = DeviceStatus.REMOVED
                old_sm_device.save()
                logger.info(f"Old device {old_sm_device_id} status changed to REMOVED")

                # Get Device Installation for Old Device Id
                old_sm_device_installation = DeviceInstallation.objects.get(
                    device=old_sm_device, is_active=True
                )

                # Set Old Device Installation end parameters
                bulk_set_old_sm_device_installation_parameters(
                    old_sm_device_installation,
                    body.oldMeterDetails.parameters.model_dump(exclude={"metersrno"}),
                )

                # set old device installation is active false
                old_sm_device_installation.is_active = False
                old_sm_device_installation.save()

                logger.info(
                    f"Old SM device installation {old_sm_device_installation.id} set to False"
                )

                # Create new SM device
                new_sm_device = Device.objects.create(
                    device_id=new_sm_device_id,
                    device_type=new_sm_device_type,
                    device_template=new_sm_device_template,
                )

                logger.info(f"New SM device {new_sm_device_id} created")

                # Set new SM device parameters
                bulk_set_device_parameters(
                    device=new_sm_device,
                    parameter_config=body.newMeterDetails.parameters.model_dump(
                        exclude={"metersrno"}
                    ),
                )

                logger.info(f"New SM device parameters set {new_sm_device_id}")

                # Create new SM device installation
                new_sm_device_installation = create_device_installation(
                    device=new_sm_device,
                    service_point=old_sm_device_installation.service_point,
                    is_active=True,
                    start_date=body.timestamp,
                )

                logger.info(f"New SM device installation {new_sm_device_installation.id} created")

                # Set parameters for new sm device installation
                bulk_set_new_sm_device_installation_parameters(
                    device_installation=new_sm_device_installation,
                    parameter_config=body.newMeterDetails.parameters.model_dump(
                        exclude={"metersrno"}
                    ),
                )

                job_obj.service_point_id = old_sm_device_installation.service_point.id
                job_obj.job_message = f"{job_obj.job_message}\n MDM Asset creation completed"
                job_obj.save()
                logger.info(f"Completed successfully for job {job_id}")

                #        Invoke zonos northbound api
                #            - Create customer
                #            - Create metering point
                #            - Set metering point parameters
                #            - Create device with device parameters

                group_uuid = "e327f3e7-774d-48e2-b44a-f26e5b3a9434"

                """try:
                    client_v2.createMeteringPoint(
                        meteringPointId=service_point_id,
                        groupUuid=group_uuid,
                        latitude=body.consumerMaster.parameters.latitude,
                        longitude=body.consumerMaster.parameters.longitude,
                    )
                except Exception as e:
                    logger.error(f"Metering Point creation error in task_2: {e}")
                    job_obj.job_status = States.FAILED
                    job_obj.job_message = (
                        f"{job_obj.job_message} > zonos metering point creation failed ({repr(e)})"
                    )
                    job_obj.save()
                    raise e"""

                # Create Device
                try:
                    device_id = new_sm_device_id
                    logger.info(f"Device type template name: {new_sm_device_type_name}")
                    logging.info(f"Device template name: {new_sm_device_template_name}")
                    device_type_uuid = str(DeviceType.objects.get(name=new_sm_device_type_name).id)
                    device_template_uuid = str(
                        DeviceTemplate.objects.get(name=new_sm_device_template_name).id
                    )

                    logger.info(f"Device type uuid: {device_type_uuid}")
                    logger.info(f"Device template uuid: {device_template_uuid}")
                    logger.info(f"Device id: {device_id}")
                    logger.info(f"Communication id: {device_id}")
                    logger.info(f"Group uuid: {group_uuid}")
                    logger.info(f"Store data: {True}")

                    device_parameters = {
                        f"ext.{key}": value if value is not None else ""
                        for key, value in body.newMeterDetails.parameters.model_dump(
                            mode="json",
                            exclude_none=True,
                        ).items()
                    }

                    device_parameters["ext.servicepointid"] = (
                        old_sm_device_installation.service_point.id
                    )

                    device: dict = {
                        "id": device_id,
                        "communicationId": device_id,
                        "groupId": group_uuid,
                        "typeId": device_type_uuid,
                        "templateId": device_template_uuid,
                        "model": body.newMeterDetails.parameters.meterphase,
                        "manufacturer": body.newMeterDetails.parameters.metermake,
                        "description": "",
                        "inventoryState": "installed",
                        "dispatchGroup": "",
                        "storeData": True,
                        "parentId": None,
                        "configuration": device_parameters,
                    }

                    response = client_v2.createDevice(device=device)
                    logger.info(f"Device creation response: {response}")

                except Exception as e:
                    logger.error(f"Device creation error in task_2: {e}")
                    job_obj.job_status = States.FAILED
                    job_obj.job_message = (
                        f"{job_obj.job_message} > zonos device creation failed ({repr(e)})"
                    )
                    job_obj.save()
                    raise e

                # Set Metering Point parameters
                try:
                    metering_point_parameters = {"ext.device_id": new_sm_device_id}

                    response = client_v2.bulkSetMeteringPointParameters(
                        meteringPoint=old_sm_device_installation.service_point.id,
                        parameters=metering_point_parameters,
                    )

                    logger.info(f"Metering Point parameters set response: {response}")

                except Exception as e:
                    logger.error(f"Metering Point parameters set error: {e}")
                    job_obj.job_status = States.FAILED
                    job_obj.job_message = f"{job_obj.job_message} > zonos metering point parameters set failed ({repr(e)})"
                    job_obj.save()
                    returnMessage = str(e)
                    errCode = "ERROR01"
            #                    raise e

            job_obj.job_status = States.COMPLETED
            job_obj.job_message = f"{job_obj.job_message}\n Zonos Asset creation completed"
            job_obj.save()
            returnMessage = "Consumer and meter created successfully"
            return Response(
                SmartToSmartResponse(
                    status=States.READY,
                    errorCode=None,
                    message="Consumer and meter created successfully",
                    meterReplacementTransactionId=body.meterReplacementTransactionId,
                    typeOfReplacementCode=body.typeOfReplacementCode,
                    accountId=body.accountId,
                ),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in Zonos Asset creation {e}")
            job_obj.job_status = States.FAILED
            job_obj.job_message = str(e)
            job_obj.save()
            returnMessage = str(e)
            errCode = "ERROR02"
            return Response(
                SmartToSmartResponse(
                    status=States.FAILED,
                    errorCode=errCode,
                    message=returnMessage,
                    meterReplacementTransactionId=body.meterReplacementTransactionId,
                    typeOfReplacementCode=body.typeOfReplacementCode,
                    accountId=body.accountId,
                ),
                status=status.HTTP_200_OK,
            )
