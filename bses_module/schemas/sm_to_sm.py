from datetime import datetime
from decimal import Decimal

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

DateTimeStr = Field(json_schema_extra={"example": "1970-01-01T00:00:00Z"})


# ==============================================================================
# Old Meter Details Schema
# ==============================================================================
class OldMeterParametersSmToSM(BaseModel):
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


class OldMeterDetailsSmToSM(BaseModel):
    metersrno: str = Field(min_length=1)
    parameters: OldMeterParametersSmToSM


class NewMeterParamtersSmToSM(BaseModel):
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


class NewMeterDetailsSmToSM(BaseModel):
    metersrno: str = Field(min_length=1)
    parameters: NewMeterParamtersSmToSM


# ==============================================================================
# Smart → Smart Inbound
# ==============================================================================


class SmartToSmartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: str
    timestamp: datetime = DateTimeStr
    requestId: str = Field(min_length=1)
    meterReplacementTransactionId: str = Field(min_length=1)
    typeOfReplacementCode: Literal["2"]
    retryCount: int | None = None

    accountId: str = Field(min_length=1, max_length=32)
    #    consumerMasterHierarchy: ConsumerMasterHierarchy
    newMeterDetails: NewMeterDetailsSmToSM

    # financialDetails: FinancialDetails | None = None
    oldMeterDetails: OldMeterDetailsSmToSM


class SmartToSmartResponse(BaseModel):
    status: str
    errorCode: str | None = None
    message: str
    meterReplacementTransactionId: str
    typeOfReplacementCode: str
    accountId: str
