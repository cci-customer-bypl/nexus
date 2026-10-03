from pydantic import BaseModel, Field


class SetMeteringPointParametersRequest(BaseModel):
    meteringPoint: str = Field(min_length=1)
    parameters: dict
    activeAt: str
