from django.db.models import ForeignKey
from django.db import models

# Create your models here.
import uuid
from decimal import Decimal
from django.db import models


# ==============================================================================
# Choice Enums
# ==============================================================================


class ElectricalNodeType(models.TextChoices):
    DISCOM = "DISCOM", "DISCOM"
    CIRCLE = "CIRCLE", "CIRCLE"
    DIVISION = "DIVISION", "DIVISION"
    SUB_DIVISION = "SUB_DIVISION", "SUB_DIVISION"
    FEEDER = "FEEDER", "FEEDER"
    DTR = "DTR", "DTR"


class GeographicalNodeType(models.TextChoices):
    STATE = "STATE", "STATE"
    DISTRICT = "DISTRICT", "DISTRICT"
    CITY = "CITY", "CITY"
    AREA = "AREA", "AREA"
    LOCALITY = "LOCALITY", "LOCALITY"


class DeviceStatus(models.TextChoices):
    IN_SERVICE = "InService", "InService"
    REMOVED = "Removed", "Removed"
    IN_STORE = "InStore", "InStore"


class PaymentType(models.TextChoices):
    PREPAID = "PREPAID", "PREPAID"
    POSTPAID = "POSTPAID", "POSTPAID"


class ParameterDataType(models.TextChoices):
    STRING = "STRING", "STRING"
    NUMBER = "NUMBER", "NUMBER"
    BOOLEAN = "BOOLEAN", "BOOLEAN"


# ==============================================================================
# Hierarchy & Topology Models
# ==============================================================================


class ElectricalNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    node_type = models.CharField(max_length=50, choices=ElectricalNodeType.choices)
    parent = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="children",
        db_column="parent_id",
        help_text="NULL for root node",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "electrical_nodes"
        indexes = [
            models.Index(fields=["node_type"], name="elec_node_type_idx"),
            models.Index(fields=["parent"], name="elec_node_parent_idx"),
            models.Index(fields=["node_type", "name"], name="elec_node_type_name_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.node_type})"


class GeographicalNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    node_type = models.CharField(max_length=50, choices=GeographicalNodeType.choices)
    parent = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="children",
        db_column="parent_id",
        help_text="NULL for root node",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "geographical_nodes"
        indexes = [
            models.Index(fields=["node_type"], name="geo_node_type_idx"),
            models.Index(fields=["parent"], name="geo_node_parent_idx"),
            models.Index(fields=["node_type", "name"], name="geo_node_type_name_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.node_type})"


class ServicePoint(models.Model):
    id = models.CharField(max_length=50, primary_key=True, help_text="Unique Service Point ID")
    electrical_node = models.ForeignKey(
        ElectricalNode,
        on_delete=models.PROTECT,
        related_name="service_points",
        db_column="electrical_node_id",
    )
    geographical_node = models.ForeignKey(
        GeographicalNode,
        on_delete=models.PROTECT,
        related_name="service_points",
        db_column="geographical_node_id",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_points"
        indexes = [
            models.Index(fields=["electrical_node"], name="sp_elec_node_idx"),
            models.Index(fields=["geographical_node"], name="sp_geo_node_idx"),
            models.Index(fields=["electrical_node", "geographical_node"], name="sp_elec_geo_idx"),
        ]

    def __str__(self):
        return str(self.id)


# ==============================================================================
# Core Asset & Entity Models
# ==============================================================================


class DeviceType(models.Model):
    id = models.UUIDField(primary_key=True, editable=True)
    name = models.CharField(max_length=100, unique=True, help_text="Canonical device type name")
    description = models.CharField(max_length=255, null=True, blank=True)
    default_register = models.CharField(max_length=255, help_text="Canonical register name")

    class Meta:
        db_table = "device_types"
        indexes = [
            models.Index(fields=["name"], name="device_type_name_idx"),
        ]

    def __str__(self):
        return f"{self.name}:{self.id}:{self.default_register}"


class DeviceTemplate(models.Model):
    id = models.UUIDField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, help_text="Canonical template name")

    class Meta:
        db_table = "device_templates"
        indexes = [
            models.Index(fields=["name"], name="device_template_name_idx"),
        ]

    def __str__(self):
        return f"{self.name}:{self.id}"


class DeviceTypeTemplateMap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_type = models.ForeignKey(
        DeviceType,
        on_delete=models.PROTECT,
        related_name="templates",
        db_column="device_type_uuid",
    )
    device_template = models.ForeignKey(
        DeviceTemplate,
        on_delete=models.PROTECT,
        related_name="device_types",
        db_column="device_template_uuid",
    )

    class Meta:
        db_table = "device_type_template_map"
        indexes = [
            models.Index(fields=["device_type"], name="dttm_device_type_idx"),
            models.Index(fields=["device_template"], name="dttm_device_template_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device_type", "device_template"],
                name="unique_device_type_template",
            )
        ]

    def __str__(self):
        return f"{self.device_type}:{self.device_template}"


class Device(models.Model):
    device_id = models.CharField(
        max_length=100, primary_key=True, help_text="Unique meter/device identifier"
    )
    device_type = models.ForeignKey(
        DeviceType,
        on_delete=models.PROTECT,
        related_name="devices",
        db_column="device_type",
    )
    device_template = models.ForeignKey(
        DeviceTemplate,
        on_delete=models.PROTECT,
        related_name="devices",
        db_column="device_template",
    )
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    phase = models.CharField(max_length=20, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    current_rating = models.CharField(max_length=50, null=True, blank=True)
    multiplying_factor = models.DecimalField(
        max_digits=8, decimal_places=4, default=Decimal("1.0000")
    )
    ct_ratio = models.CharField(max_length=50, null=True, blank=True)
    pt_ratio = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=DeviceStatus.choices, default=DeviceStatus.IN_SERVICE
    )
    is_smart_meter = models.BooleanField(default=True)
    net_meter_flag = models.BooleanField(default=False)
    shunt_capacitor_flag = models.BooleanField(default=False)
    prepaid_opening_balance = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    register_group = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "devices"
        indexes = [
            models.Index(fields=["status"], name="device_status_idx"),
            models.Index(fields=["status", "is_smart_meter"], name="device_status_smart_idx"),
            models.Index(fields=["manufacturer"], name="device_mfr_idx"),
            models.Index(fields=["category", "phase"], name="device_cat_phase_idx"),
        ]

    def __str__(self):
        return str(self.device_id)


class Consumer(models.Model):
    consumer_id = models.CharField(
        max_length=50, primary_key=True, help_text="Unique Consumer ID / Account ID"
    )
    consumer_name = models.CharField(max_length=255)
    sub_division_code = models.CharField(max_length=50, null=True, blank=True)
    dtr_code = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consumers"
        indexes = [
            models.Index(fields=["consumer_name"], name="consumer_name_idx"),
            models.Index(fields=["sub_division_code"], name="consumer_subdiv_idx"),
            models.Index(fields=["dtr_code"], name="consumer_dtr_idx"),
        ]

    def __str__(self):
        return f"{self.consumer_id} - {self.consumer_name}"


# ==============================================================================
# Associations & Operational Models
# ==============================================================================


class DeviceInstallation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_point = models.ForeignKey(
        ServicePoint,
        on_delete=models.DO_NOTHING,
        related_name="device_installations",
        db_column="service_point_id",
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.DO_NOTHING,
        related_name="installations",
        db_column="device_id",
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(
        null=True, blank=True, help_text="NULL while installation is active"
    )

    class Meta:
        db_table = "device_installations"
        indexes = [
            models.Index(fields=["service_point", "is_active"], name="dev_inst_sp_act_idx"),
            models.Index(fields=["device", "is_active"], name="dev_inst_dev_act_idx"),
            models.Index(fields=["start_date", "end_date"], name="dev_inst_dates_idx"),
        ]

    def __str__(self):
        return f"{self.device} @ {self.service_point}"


class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_point = models.ForeignKey(
        ServicePoint,
        on_delete=models.PROTECT,
        related_name="contracts",
        db_column="service_point_id",
    )
    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.PROTECT,
        related_name="contracts",
        db_column="consumer_id",
    )
    is_active = models.BooleanField(default=True)
    payment_type = models.CharField(
        max_length=20, choices=PaymentType.choices, default=PaymentType.PREPAID
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="NULL while contract is active")

    class Meta:
        db_table = "contracts"
        indexes = [
            models.Index(fields=["service_point", "is_active"], name="contract_sp_act_idx"),
            models.Index(fields=["consumer", "is_active"], name="contract_cons_act_idx"),
            models.Index(fields=["start_date", "end_date"], name="contract_dates_idx"),
        ]

    def __str__(self):
        return f"Contract {self.id} ({self.consumer} -> {self.service_point})"


# ==============================================================================
# Parameter Definitions & Values (EAV Pattern)
# ==============================================================================


class ConsumerParameterDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Canonical parameter key")
    description = models.CharField(max_length=255, null=True, blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=ParameterDataType.choices,
        default=ParameterDataType.STRING,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "consumer_parameter_definitions"
        indexes = [
            models.Index(fields=["is_active"], name="cp_def_active_idx"),
        ]

    def __str__(self):
        return str(self.name)


class ConsumerParameterValue(models.Model):
    id = models.BigAutoField(primary_key=True)
    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.PROTECT,
        related_name="parameter_values",
        db_column="consumer_id",
    )
    parameter = models.ForeignKey(
        ConsumerParameterDefinition,
        on_delete=models.PROTECT,
        related_name="values",
        db_column="parameter_uuid",
    )
    value = models.CharField(max_length=255, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "consumer_parameter_values"
        ordering = ["-recorded_at"]
        indexes = [
            # Covers "get latest value for a specific consumer & parameter"
            models.Index(
                fields=["consumer", "parameter", "-recorded_at"],
                name="cp_val_cons_param_rec_idx",
            ),
            # Covers time-slice range queries across all consumers
            models.Index(fields=["-recorded_at"], name="cp_val_rec_desc_idx"),
            # Covers aggregating or pulling history by parameter definition
            models.Index(fields=["parameter", "-recorded_at"], name="cp_val_param_rec_idx"),
        ]


class ServicePointParameterDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Canonical parameter key")
    description = models.CharField(max_length=255, null=True, blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=ParameterDataType.choices,
        default=ParameterDataType.STRING,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "service_point_parameter_definitions"
        indexes = [
            models.Index(fields=["is_active"], name="sp_def_active_idx"),
        ]

    def __str__(self):
        return str(self.name)


class ServicePointParameterValue(models.Model):
    id = models.BigAutoField(primary_key=True)
    service_point = models.ForeignKey(
        ServicePoint,
        on_delete=models.PROTECT,
        related_name="parameter_values",
        db_column="service_point_id",
    )
    parameter = models.ForeignKey(
        ServicePointParameterDefinition,
        on_delete=models.PROTECT,
        related_name="values",
        db_column="parameter_uuid",
    )
    value = models.CharField(max_length=255, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "service_point_parameter_values"
        ordering = ["-recorded_at"]
        indexes = [
            # Covers "get latest value for a specific service point & parameter"
            models.Index(
                fields=["service_point", "parameter", "-recorded_at"],
                name="sp_val_sp_param_rec_idx",
            ),
            # Covers time-slice range queries across all service points
            models.Index(fields=["-recorded_at"], name="sp_val_rec_desc_idx"),
            # Covers aggregating or pulling history by parameter definition
            models.Index(fields=["parameter", "-recorded_at"], name="sp_val_param_rec_idx"),
        ]


class DeviceParameterDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Canonical parameter key")
    description = models.CharField(max_length=255, null=True, blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=ParameterDataType.choices,
        default=ParameterDataType.STRING,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "device_parameter_definitions"
        indexes = [
            models.Index(fields=["is_active"], name="dp_def_active_idx"),
        ]

    def __str__(self):
        return str(self.name)


class DeviceParameterValue(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="parameter_values",
        db_column="device_uuid",
    )
    parameter = models.ForeignKey(
        DeviceParameterDefinition,
        on_delete=models.PROTECT,
        related_name="values",
        db_column="parameter_uuid",
    )
    value = models.CharField(max_length=255, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_parameter_values"
        ordering = ["-recorded_at"]
        indexes = [
            # Covers "get latest reading/value for a specific device & parameter"
            models.Index(
                fields=["device", "parameter", "-recorded_at"],
                name="dp_val_dev_param_rec_idx",
            ),
            # Covers time-slice range queries across all devices
            models.Index(fields=["-recorded_at"], name="dp_val_rec_desc_idx"),
            # Covers aggregating or pulling history by parameter definition
            models.Index(fields=["parameter", "-recorded_at"], name="dp_val_param_rec_idx"),
        ]


class DeviceInstallationParameterDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Canonical parameter key")
    description = models.CharField(max_length=255, null=True, blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=ParameterDataType.choices,
        default=ParameterDataType.STRING,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "device_installation_parameter_definitions"
        indexes = [
            models.Index(fields=["is_active"], name="dip_def_active_idx"),
        ]

    def __str__(self):
        return str(self.name)


class DeviceInstallationParameterValue(models.Model):
    id = models.BigAutoField(primary_key=True)
    device_installation = models.ForeignKey(
        DeviceInstallation,
        on_delete=models.PROTECT,
        related_name="parameter_values",
        db_column="device_installation_id",
    )
    parameter = models.ForeignKey(
        DeviceInstallationParameterDefinition,
        on_delete=models.PROTECT,
        related_name="values",
        db_column="parameter_uuid",
    )
    start_value = models.CharField(max_length=255, null=True, blank=True)
    end_value = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "device_installation_parameter_values"
        constraints = [
            models.UniqueConstraint(
                fields=["device_installation", "parameter"],
                name="dip_val_unique_inst_param",
            ),
        ]
