from datetime import datetime
from decimal import Decimal

from typing import Literal, Any
from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict, AwareDatetime
from bses_module.models import States

DateTimeStr = Field(json_schema_extra={"example": "1970-01-01T00:00:00Z"})
# ==============================================================================
# Hierarchy Schemas
# ==============================================================================


class GeographicalMasterHierarchy(BaseModel):
    subDivisionCode: str


class ElectricalMasterHierarchy(BaseModel):
    dtrCode: str


class ConsumerMasterHierarchy(BaseModel):
    geographicalMasterHierarchy: GeographicalMasterHierarchy
    electricalMasterHierarchy: ElectricalMasterHierarchy


# ==============================================================================
# Consumer Master Schema
# ==============================================================================

class ConsumerPosition(BaseModel):

    latitude: float 
    longitude: float 

class ConsumerMasterParameters(BaseModel):
    consumerName: str
    address1: str
    connectionStatus: str
    tariffCode: str

    sanctionedLoad: str = Field(examples=["0.840"])

    loadUnit: str
    meterTypeFlag: str

    isVip: str = Field(default="N", max_length=1, examples=["Y", "N"])

    # Optional
    firstName: str | None = None
    middleName: str | None = None
    lastName: str | None = None
    title: str | None = None

    houseNumber: str | None = None
    street: str | None = None
    street2: str | None = None
    street3: str | None = None
    street4: str | None = None

    city: str | None = None
    pinCode: str | None = None

    mobileNumber: str | None = None
    alternatePhone: str | None = None
    fax: str | None = None

    email: EmailStr | None = None

    consumerType: str | None = None
    meterStatus: str | None = None
    supplyTypeCode: str | None = None
    rateType: str | None = None

    customerEntryDate: datetime | None = None

    prepaidPostpaidFlag: str | None = None
    netMeterFlag: str | None = None
    temporaryFlag: str | None = None

    companyCode: str | None = None
    postingDate: str | None = None
    processCode: str | None = None
    runDate: str | None = None
    adjustmentType: str | None = None
    scheduledBillingDate: str | None = None


class ConsumerMaster(BaseModel):
    # Mandatory
    accountId: str = Field(min_length=1, max_length=32)
    parameters: ConsumerMasterParameters
    position: ConsumerPosition | None = Field(default=None, examples=[{ "latitude": 28.6139,"longitude": 77.2090,}])


# ==============================================================================
# Financial Details Schema
# ==============================================================================


class FinancialDetails(BaseModel):
    arrears: Decimal | None = None
    securityDepositAmount: Decimal | None = None
    adjustmentAmount: Decimal | None = None
    freezeCreditAmount: Decimal | None = None
    creditLimit: Decimal | None = None
    finalOutstandingAmount: Decimal | None = None
    debitAmount: Decimal | None = None
    edApplicable: Decimal | None = None


# ==============================================================================
# Old Meter Details Schema
# ==============================================================================
class OldMeterParameters(BaseModel):
    metermake: str
    meterphase: str
    metercategory: str
    metercurrentrating: str | None = None
    multiplyingfactor: Decimal | None = None
    ctratio: str | None = None
    ptratio: str | None = None
    kwhimportfinal: Decimal | None = None
    kvahimportfinal: Decimal | None = None
    kwhexportfinal: Decimal | None = None
    kvahexportfinal: Decimal | None = None
    kwhpeak: Decimal | None = None
    kwhoffpeak: Decimal | None = None
    kvahpeak: Decimal | None = None
    kvahoffpeak: Decimal | None = None
    kwhpeakexport: Decimal | None = None
    kwhoffpeakexport: Decimal | None = None
    meterremovaldate: datetime | None = None

class OldMeterDetails(BaseModel):
    metersrno: str
    meterType: str
    parameters: OldMeterParameters
    


# ==============================================================================
# New Meter Details Schema
# ==============================================================================

class NewMeterParamters(BaseModel):
    metermake: str = Field(min_length=1)
    meterphase: str = Field(min_length=1)
    metercategory: str = Field(min_length=1)
    metercurrentrating: str | None = None
    multiplyingfactor: Decimal | None = None
    ctratio: str | None = None
    ptratio: str | None = None
    kwhimportinitial: Decimal | None = None
    kvahimportinitial: Decimal | None = None
    kwhexportinitial: Decimal | None = None
    kvahexportinitial: Decimal | None = None
    kwhpeak: Decimal | None = None
    kwhoffpeak: Decimal | None = None
    kvahpeak: Decimal | None = None
    kvahoffpeak: Decimal | None = None
    kwhpeakexport: Decimal | None = None
    kwhoffpeakexport: Decimal | None = None
    prepaidpostpaidflag: bool
    netmeterflag: str | None = None
    meterstatus: str
    meterinstalldate: datetime

class NewMeterDetails(BaseModel):
    metersrno: str = Field(min_length=1)
    meterType: str
    paramters: NewMeterParamters


# ==============================================================================
# Additional Non-Mandatory Parameters Schema
# ==============================================================================


class AdditionalNonMandatoryParams(BaseModel):
    shuntCapacitorFlag: str | None = None
    registerGroup: str | None = None


# ==============================================================================
# Non-Smart → Smart Inbound
# ==============================================================================


class NonSmartToSmartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: str
    timestamp: datetime = DateTimeStr
    requestId: str
    meterReplacementTransactionId: str
    typeOfReplacementCode: Literal["1"]
    retryCount: int | None = None

    consumerMaster: ConsumerMaster
    consumerMasterHierarchy: ConsumerMasterHierarchy
    newMeterDetails: NewMeterDetails

    financialDetails: FinancialDetails | None = None
    oldMeterDetails: OldMeterDetails | None = None
    additionalNonMandatoryParams: AdditionalNonMandatoryParams | None = None


class NonSmartToSmartResponse(BaseModel):
    status: str
    errorCode: str | None = None
    message: str
    meterReplacementTransactionId: str
    typeOfReplacementCode: str
    accountId: str


# ==============================================================================
# ODR
# ==============================================================================


class BillingRcmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    devices: list[str] = Field(min_length=1)
    readingReason: int = Field(gt=0, lt=100)
    externalId: str
    fromTime: AwareDatetime = DateTimeStr
    toTime: AwareDatetime = DateTimeStr
    priority: Literal["HIGHEST", "HIGH", "NORMAL", "LOW", "LOWEST"] = "NORMAL"

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.fromTime > self.toTime:
            raise ValueError("fromTime must be before toTime")
        return self

    @model_validator(mode="after")
    def duplicate_devices_check(self):
        if len(set(self.devices)) != len(self.devices):
            raise ValueError("Duplicate devices found")
        return self


class BillingRcmResponse(BaseModel):
    status: States
    errorCode: str | None = None
    message: str
    externalId: str
    errors: Any | None = None
