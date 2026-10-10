from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, AwareDatetime
from bses_module.models import States
from typing import Literal, Any

DateTimeStr = Field(json_schema_extra={"example": "1970-01-01T00:00:00Z"})

# ==============================================================================
# Meter Removal
# ==============================================================================


class MeterRemovalParameters(BaseModel):
    metermake: str | None = None
    meterphase: str | None = None
    metercategory: str | None = None
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
    prepaidpostpaidflag: str | None = None
    netmeterflag: str | None = None
    meterstatus: str
    meterremovaldate: AwareDatetime = DateTimeStr


class MeterRemovalMeterDetails(BaseModel):
    metersrno: str
    parameters: MeterRemovalParameters


class MeterRemovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: AwareDatetime = DateTimeStr
    requestId: str | None = None
    meterRemovalTransactionId: str
    typeOfRemovalCode: Literal["4"]
    accountId: str

    meterDetails: MeterRemovalMeterDetails


class MeterRemovalResponse(BaseModel):
    status: States
    errorCode: str
    message: str
    meterRemovalTransactionId: str
    typeOfRemovalCode: str
    accountId: str
