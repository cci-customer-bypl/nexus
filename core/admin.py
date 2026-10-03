from django.contrib import admin

from .models import (
    ElectricalNode,
    GeographicalNode,
    ServicePoint,
    DeviceType,
    DeviceTemplate,
    DeviceTypeTemplateMap,
    Device,
    Consumer,
    DeviceInstallation,
    Contract,
    ConsumerParameterDefinition,
    ConsumerParameterValue,
    ServicePointParameterDefinition,
    ServicePointParameterValue,
    DeviceParameterDefinition,
    DeviceParameterValue,
    DeviceInstallationParameterDefinition,
    DeviceInstallationParameterValue,
)


admin.site.site_header = "Cuculus MDM Administration"
admin.site.site_title = "Cuculus MDM Admin"
admin.site.index_title = "Cuculus MDM Management Portal"

# ==============================================================================
# Hierarchy & Topology
# ==============================================================================


@admin.register(ElectricalNode)
class ElectricalNodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "node_type",
        "parent",
        "created_at",
        "updated_at",
    )

    list_filter = ("node_type",)

    search_fields = (
        "name",
        "parent__name",
    )

    autocomplete_fields = ("parent",)

    ordering = (
        "node_type",
        "name",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


@admin.register(GeographicalNode)
class GeographicalNodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "node_type",
        "parent",
        "created_at",
        "updated_at",
    )

    list_filter = ("node_type",)

    search_fields = (
        "name",
        "parent__name",
    )

    autocomplete_fields = ("parent",)

    ordering = (
        "node_type",
        "name",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


@admin.register(ServicePoint)
class ServicePointAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "electrical_node",
        "geographical_node",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "electrical_node__name",
        "geographical_node__name",
    )

    autocomplete_fields = (
        "electrical_node",
        "geographical_node",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("id",)

    list_select_related = (
        "electrical_node",
        "geographical_node",
    )


# ==============================================================================
# Device Master Data
# ==============================================================================


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "default_register",
        "id",
    )

    search_fields = (
        "name",
        "default_register",
        "description",
    )

    readonly_fields = (
        # "id",
    )

    ordering = ("name",)


@admin.register(DeviceTemplate)
class DeviceTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "id",
    )

    search_fields = ("name",)

    readonly_fields = (
        # "id",
    )

    ordering = ("name",)


@admin.register(DeviceTypeTemplateMap)
class DeviceTypeTemplateMapAdmin(admin.ModelAdmin):
    list_display = (
        "device_type",
        "device_template",
        "id",
    )

    list_filter = (
        "device_type",
        "device_template",
    )

    search_fields = (
        "device_type__name",
        "device_template__name",
    )

    autocomplete_fields = (
        "device_type",
        "device_template",
    )

    readonly_fields = ("id",)

    list_select_related = (
        "device_type",
        "device_template",
    )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_id",
        "device_type",
        "device_template",
        "manufacturer",
        "phase",
        "category",
        "status",
        "is_smart_meter",
    )

    list_filter = (
        "status",
        "is_smart_meter",
        "net_meter_flag",
        "shunt_capacitor_flag",
        "device_type",
        "device_template",
        "phase",
        "category",
    )

    search_fields = (
        "device_id",
        "manufacturer",
        "device_type__name",
        "device_template__name",
        "register_group",
    )

    autocomplete_fields = (
        "device_type",
        "device_template",
    )

    ordering = ("device_id",)

    list_select_related = (
        "device_type",
        "device_template",
    )

    list_per_page = 50


# ==============================================================================
# Consumer
# ==============================================================================


@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = (
        "consumer_id",
        "consumer_name",
        "sub_division_code",
        "dtr_code",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "sub_division_code",
        "dtr_code",
    )

    search_fields = (
        "consumer_id",
        "consumer_name",
        "sub_division_code",
        "dtr_code",
    )

    ordering = ("consumer_id",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_per_page = 50


# ==============================================================================
# Associations / Operational Models
# ==============================================================================


@admin.register(DeviceInstallation)
class DeviceInstallationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "device",
        "service_point",
        "is_active",
        "start_date",
        "end_date",
    )

    list_filter = (
        "is_active",
        "start_date",
        "end_date",
    )

    search_fields = (
        "device__device_id",
        "service_point__id",
    )

    autocomplete_fields = (
        "device",
        "service_point",
    )

    readonly_fields = ("id",)

    ordering = ("-start_date",)

    list_select_related = (
        "device",
        "service_point",
    )


@admin.register(DeviceInstallationParameterDefinition)
class DeviceInstallationParameterDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "data_type",
        "is_active",
    )

    list_filter = (
        "data_type",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = ("name",)


@admin.register(DeviceInstallationParameterValue)
class DeviceInstallationParameterValueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "device_installation_id",
        "parameter",
        "start_value",
        "end_value",
    )

    list_filter = ("parameter",)

    search_fields = (
        "device_installation_id",
        "device_installation__device__device_id",
        "device_installation__service_point__id",
        "parameter__name",
    )

    autocomplete_fields = (
        "device_installation",
        "parameter",
    )

    list_select_related = (
        "device_installation",
        "parameter",
    )

    ordering = ("id",)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        "consumer",
        "service_point",
        "payment_type",
        "is_active",
        "start_date",
        "end_date",
    )

    list_filter = (
        "payment_type",
        "is_active",
        "start_date",
        "end_date",
    )

    search_fields = (
        "consumer__consumer_id",
        "consumer__consumer_name",
        "service_point__id",
    )

    autocomplete_fields = (
        "consumer",
        "service_point",
    )

    readonly_fields = ("id",)

    ordering = ("-start_date",)

    list_select_related = (
        "consumer",
        "service_point",
    )


# ==============================================================================
# Parameter Definitions
# ==============================================================================


@admin.register(ConsumerParameterDefinition)
class ConsumerParameterDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "data_type",
        "is_active",
        "id",
    )

    list_filter = (
        "data_type",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = ("id",)

    ordering = ("name",)


@admin.register(ServicePointParameterDefinition)
class ServicePointParameterDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "data_type",
        "is_active",
        "id",
    )

    list_filter = (
        "data_type",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = ("id",)

    ordering = ("name",)


@admin.register(DeviceParameterDefinition)
class DeviceParameterDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "data_type",
        "is_active",
        "id",
    )

    list_filter = (
        "data_type",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = ("id",)

    ordering = ("name",)


# ==============================================================================
# Parameter Values / History
# ==============================================================================


@admin.register(ConsumerParameterValue)
class ConsumerParameterValueAdmin(admin.ModelAdmin):
    list_display = (
        "consumer",
        "parameter",
        "value",
        "recorded_at",
    )

    list_filter = (
        "parameter",
        "recorded_at",
    )

    search_fields = (
        "consumer__consumer_id",
        "consumer__consumer_name",
        "parameter__name",
        "value",
    )

    autocomplete_fields = (
        "consumer",
        "parameter",
    )

    readonly_fields = (
        "id",
        "recorded_at",
    )

    ordering = ("-recorded_at",)

    list_select_related = (
        "consumer",
        "parameter",
    )

    date_hierarchy = "recorded_at"

    list_per_page = 100


@admin.register(ServicePointParameterValue)
class ServicePointParameterValueAdmin(admin.ModelAdmin):
    list_display = (
        "service_point",
        "parameter",
        "value",
        "recorded_at",
    )

    list_filter = (
        "parameter",
        "recorded_at",
    )

    search_fields = (
        "service_point__id",
        "parameter__name",
        "value",
    )

    autocomplete_fields = (
        "service_point",
        "parameter",
    )

    readonly_fields = (
        "id",
        "recorded_at",
    )

    ordering = ("-recorded_at",)

    list_select_related = (
        "service_point",
        "parameter",
    )

    date_hierarchy = "recorded_at"

    list_per_page = 100


@admin.register(DeviceParameterValue)
class DeviceParameterValueAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "parameter",
        "value",
        "recorded_at",
    )

    list_filter = (
        "parameter",
        "recorded_at",
    )

    search_fields = (
        "device__device_id",
        "parameter__name",
        "value",
    )

    autocomplete_fields = (
        "device",
        "parameter",
    )

    readonly_fields = (
        "id",
        "recorded_at",
    )

    ordering = ("-recorded_at",)

    list_select_related = (
        "device",
        "parameter",
    )

    date_hierarchy = "recorded_at"

    list_per_page = 100
