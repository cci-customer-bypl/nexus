from datetime import datetime
from decimal import Decimal

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

DateTimeStr = Field(json_schema_extra={"example": "1970-01-01T00:00:00Z"})


class ConsumerMaster(BaseModel):
    # Mandatory
    accountId: str = Field(min_length=1, max_length=32)


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
    metersrno: str = Field(min_length=1)
    parameters: OldMeterParameters


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
    parameters: NewMeterParamters


# ==============================================================================
# Smart → Smart Inbound
# ==============================================================================


class SmartToSmartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: str
    timestamp: datetime = DateTimeStr
    requestId: str
    meterReplacementTransactionId: str
    typeOfReplacementCode: Literal["2"]
    retryCount: int | None = None

    consumerMaster: ConsumerMaster
    #    consumerMasterHierarchy: ConsumerMasterHierarchy
    newMeterDetails: NewMeterDetails

    # financialDetails: FinancialDetails | None = None
    oldMeterDetails: OldMeterDetails


class SmartToSmartResponse(BaseModel):
    status: str
    errorCode: str | None = None
    message: str
    meterReplacementTransactionId: str
    typeOfReplacementCode: str
    accountId: str
