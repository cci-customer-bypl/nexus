from unicodedata import name
from airflow.utils import retries
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import logging

from airflow.sdk import DAG, task

import django
from django.db import transaction

django.setup()


from zonos_northbound_api.northbound_client import client_v2
from config import settings
from core.models import (
    Device,
    Consumer,
    ServicePoint,
    DeviceInstallation,
    Contract,
    DeviceType,
    DeviceTemplate,
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
from bses_module.models import NonSmToSmJob, States
from bses_module.schemas.schemas import NonSmartToSmartRequest


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


def bulk_set_sm_device_installation_parameters(
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


def bulk_set_non_sm_device_installation_parameters(
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
                end_value=parameter_config[parameter.name],
            )
            for parameter in parameters
        ]
    )


with DAG(
    dag_id="BSES-non-SM-to-SM",
    start_date=datetime(2025, 1, 1, tzinfo=IST),
    schedule="*/2 * * * *",
    catchup=False,
) as dag:

    @task.short_circuit
    def get_jobs() -> list[dict]:
        jobs_queryset = NonSmToSmJob.objects.filter(job_status=States.READY)
        jobs: list = list(
            jobs_queryset.values(
                "job_id",
                "non_sm_device_id",
                "sm_device_id",
                "consumer_id",
                "service_point_id",
                "payload",
            )
        )
        logger.info(f"Jobs found: {len(jobs)}")

        if not jobs:
            logger.info("No jobs found")
            return []

        else:
            logger.info(f"Processing {len(jobs)} jobs")
            logger.debug(f"Jobs: {jobs}")
            updated_jobs = jobs_queryset.update(job_status=States.IN_PROGRESS)
            logger.info(f"Updated {updated_jobs} job statuses to IN_PROGRESS")
            return jobs

    @task(
        retries=0,
        retry_delay=timedelta(minutes=5),
        doc_md="""
            Task 1
                - ensure consumer
                - ensure service point
                - ensure sm_device
                - ensure non_sm_device
                - create contract
                - create sm_device installation
                - create non_sm_device uninstallation
                - else rollback
        """,
    )
    def task_1(job: dict) -> dict:

        sm_device_id = job["sm_device_id"]
        consumer_id = job["consumer_id"]

        job_obj = NonSmToSmJob.objects.get(job_id=job["job_id"])
        job_obj.job_message = f"{job_obj.job_message}\n Processing task 1"
        job_obj.save()

        try:
            body = NonSmartToSmartRequest.model_validate(job["payload"])
            with transaction.atomic():
                geographical_node = GeographicalNode.objects.get(name="Root")
                electrical_node = ElectricalNode.objects.get(name="Root")

                # Create or get consumer
                consumer, created = ensure_consumer(
                    consumer_id=consumer_id,
                    consumer_name=body.consumerMaster.parameters.consumerName,
                )

                # Create Service Point
                if created:
                    logger.info(f"Consumer {consumer_id} created")
                    service_point_id = f"{body.consumerMaster.accountId}_SP1"
                    service_point = create_service_point(
                        service_point_id=service_point_id,
                        electrical_node=electrical_node,
                        geographical_node=geographical_node,
                    )
                else:
                    logger.info(f"Consumer {consumer_id} already exists")
                    contracts = Contract.objects.filter(consumer=consumer)
                    service_point_id = f"{body.consumerMaster.accountId}_SP{contracts.count() + 1}"
                    service_point = create_service_point(
                        service_point_id=service_point_id,
                        electrical_node=electrical_node,
                        geographical_node=geographical_node,
                    )

                # Create Contract
                contract = create_contract(
                    service_point=service_point,
                    consumer=consumer,
                    start_date=body.timestamp,
                    payment_type=PaymentType.PREPAID
                    if body.newMeterDetails.paramters.prepaidpostpaidflag == True
                    else PaymentType.POSTPAID,
                )

                consumer_parameters = body.consumerMaster.parameters.model_dump()

                # Set consumer parameters
                bulk_set_consumer_parameters(
                    consumer=consumer, parameter_config=consumer_parameters
                )
                if body.consumerMaster.position:
                    bulk_set_consumer_parameters(
                        consumer=consumer,
                        parameter_config=body.consumerMaster.position.model_dump(),
                    )
                # Set service point parameters
                bulk_set_service_point_parameters(
                    service_point=service_point, parameter_config=consumer_parameters
                )
                type_template_name = f"{body.newMeterDetails.paramters.metermake}_{body.newMeterDetails.paramters.meterphase}_{body.newMeterDetails.paramters.metercategory}"
                sm_device_type = DeviceType.objects.get(name=type_template_name)
                sm_device_template = DeviceTemplate.objects.get(name=type_template_name)

                # Create SM device
                sm_device, created = ensure_device(
                    device_id=sm_device_id,
                    device_type=sm_device_type,
                    device_template=sm_device_template,
                )

                # Set SM device parameters
                bulk_set_device_parameters(
                    device=sm_device,
                    parameter_config=body.newMeterDetails.model_dump(exclude={"metersrno"}),
                )

                # Create SM device installation
                sm_device_installation = create_device_installation(
                    device=sm_device,
                    service_point=service_point,
                    is_active=True,
                    start_date=body.timestamp,
                )

                # Set parameters for sm device installation
                bulk_set_sm_device_installation_parameters(
                    device_installation=sm_device_installation,
                    parameter_config=body.newMeterDetails.model_dump(exclude={"metersrno"}),
                )

                # Get non sm device type and template
                non_sm_device_type = DeviceType.objects.get(
                    id="9c423eb7-e2dc-4a66-b82f-409be8bb4268"
                )
                non_sm_device_template = DeviceTemplate.objects.get(
                    id="705c53bc-5de5-4112-b80f-97a87dac3756"
                )

                if body.oldMeterDetails:
                    non_sm_device_id = body.oldMeterDetails.metersrno

                    # Create or get non SM device
                    non_sm_device, created = ensure_device(
                        device_id=non_sm_device_id,
                        device_type=non_sm_device_type,
                        device_template=non_sm_device_template,
                    )

                    # Set parameters for non sm device
                    bulk_set_device_parameters(
                        device=non_sm_device,
                        parameter_config=body.oldMeterDetails.model_dump(exclude={"metersrno"}),
                    )

                    # Un-install old non_sm_device
                    non_sm_device_installation = create_device_installation(
                        device=non_sm_device,
                        service_point=service_point,
                        is_active=False,
                        start_date=datetime(1970, 1, 1, tzinfo=IST),
                        end_date=body.timestamp,
                    )

                    # Set parameters for non sm device uninstallation
                    bulk_set_non_sm_device_installation_parameters(
                        device_installation=non_sm_device_installation,
                        parameter_config=body.oldMeterDetails.model_dump(exclude={"metersrno"}),
                    )
                job_obj.service_point_id = service_point.id
                job_obj.job_message = f"{job_obj.job_message}\n Task 1 MDM Asset creation completed"
                job_obj.save()
                job["service_point_id"] = service_point_id
            logger.info(f"Task 1 completed successfully for job {job_obj.job_id}")
            return job
        except Exception as e:
            logger.error(f"Error in task_1: {e}")
            job_obj.job_status = States.FAILED
            job_obj.job_message = str(e)
            job_obj.save()
            raise e

    @task(
        retries=5,
        retry_delay=timedelta(minutes=5),
        doc_md="""
        Invoke zonos northbound api
            - Create customer
            - Create metering point
            - Set metering point parameters
            - Create device with device parameters
        """,
    )
    def task_2(job: dict) -> dict:

        job_obj = NonSmToSmJob.objects.get(job_id=job["job_id"])

        job_obj.job_message = f"{job_obj.job_message}\n Processing task 2"
        job_obj.save()

        body: NonSmartToSmartRequest = NonSmartToSmartRequest.model_validate(job["payload"])
        group_uuid = "e327f3e7-774d-48e2-b44a-f26e5b3a9434"
        # Create customer
        try:
            client_v2.createCustomer(
                customerId=job["consumer_id"],
                language="en",
                timeZone="Asia/Kolkata",
                typeof="unknown",
                preferEmail=True,
            )
        except Exception as e:
            logger.error(f"Customer creation error in task_2: {e}")
            job_obj.job_status = States.FAILED
            job_obj.job_message = (
                f"{job_obj.job_message} > zonos customer creation failed ({repr(e)})"
            )
            job_obj.save()
            raise e

        # Create Metering Point
        try:
            client_v2.createMeteringPoint(
                meteringPointId=job["service_point_id"],
                groupUuid=group_uuid,
                latitude=body.consumerMaster.position.latitude
                if body.consumerMaster.position
                else None,
                longitude=body.consumerMaster.position.longitude
                if body.consumerMaster.position
                else None,
            )
        except Exception as e:
            logger.error(f"Metering Point creation error in task_2: {e}")
            job_obj.job_status = States.FAILED
            job_obj.job_message = (
                f"{job_obj.job_message} > zonos metering point creation failed ({repr(e)})"
            )
            job_obj.save()
            raise e

        # Create Device
        try:
            device_id = job["sm_device_id"]
            device_type_template_name = f"{body.newMeterDetails.paramters.metermake}_{body.newMeterDetails.paramters.meterphase}_{body.newMeterDetails.paramters.metercategory}"
            logger.info(f"Device type template name: {device_type_template_name}")
            device_type_uuid = str(DeviceType.objects.get(name=device_type_template_name).id)
            device_template_uuid = str(
                DeviceTemplate.objects.get(name=device_type_template_name).id
            )

            logger.info(f"Device type uuid: {device_type_uuid}")
            logger.info(f"Device template uuid: {device_template_uuid}")
            logger.info(f"Device id: {device_id}")
            logger.info(f"Communication id: {device_id}")
            logger.info(f"Group uuid: {group_uuid}")
            logger.info(f"Store data: {True}")

            device_parameters = {
                f"ext.{key}": value if value else ""
                for key, value in body.newMeterDetails.paramters.model_dump(
                    exclude={"metersrno"}, mode="json"
                ).items()
            }
            device_parameters["ext.servicepointid"] = job["service_point_id"]

            device: dict = {
                "id": device_id,
                "communicationId": device_id,
                "groupId": group_uuid,
                "typeId": device_type_uuid,
                "templateId": device_template_uuid,
                "model": body.newMeterDetails.paramters.meterphase,
                "manufacturer": body.newMeterDetails.paramters.metermake,
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
            metering_point_parameters = {
                f"ext.{key}": value
                for key, value in body.consumerMaster.model_dump(
                    exclude={"meterinstalldate", "latitude", "longitude", "meterStatus"},
                    mode="json",
                ).items()
            }
            metering_point_parameters["ext.device_id"] = device_id

            response = client_v2.bulkSetMeteringPointParameters(
                meteringPoint=job["service_point_id"],
                parameters=metering_point_parameters,
            )
            logger.info(f"Metering Point parameters set response: {response}")
        except Exception as e:
            logger.error(f"Metering Point parameters set error in task_2: {e}")
            job_obj.job_status = States.FAILED
            job_obj.job_message = (
                f"{job_obj.job_message} > zonos metering point parameters set failed ({repr(e)})"
            )
            job_obj.save()
            raise e

        return job

    @task
    def complete_job_status(job: dict) -> None:
        job_obj = NonSmToSmJob.objects.get(job_id=job["job_id"])
        job_obj.job_status = States.COMPLETED
        job_obj.job_message = f"{job_obj.job_message}\n Task 2 Zonos Asset creation completed"
        job_obj.save()

    jobs = get_jobs()

    task_1 = task_1.expand(job=jobs)
    task_2 = task_2.expand(job=task_1)
    complete_job_status.expand(job=task_2)
