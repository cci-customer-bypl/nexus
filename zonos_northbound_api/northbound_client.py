from config import settings
from zonos_northbound_api.northbound_api import NorthboundApi
from zonos_northbound_api.northbound_api_v2 import NorthboundApi as NorthboundApiV2

client_v2 = NorthboundApiV2(
    baseUrl=settings.ZONOS_NORTHBOUND_BASE_URL,
    tokenUrl=settings.ZONOS_NORTHBOUND_TOKEN_URL,
    username=settings.ZONOS_NORTHBOUND_USERNAME,
    password=settings.ZONOS_NORTHBOUND_PASSWORD,
)

client = NorthboundApi(
    baseUrl=settings.ZONOS_NORTHBOUND_BASE_URL,
    tokenUrl=settings.ZONOS_NORTHBOUND_TOKEN_URL,
    username=settings.ZONOS_NORTHBOUND_USERNAME,
    password=settings.ZONOS_NORTHBOUND_PASSWORD,
)
