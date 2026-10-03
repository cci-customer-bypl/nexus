from collections.abc import Callable
from zonos_northbound_api.rest_client import Rest_client
from httpx import BasicAuth, Response
import logging
import httpx
from httpx._exceptions import HTTPStatusError
from functools import wraps
from typing import TypeVar, ParamSpec, Concatenate

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def exception_handler(
    func: Callable[Concatenate["NorthboundApi", P], R],
) -> Callable[Concatenate["NorthboundApi", P], R]:
    """
    Decorator that catches HTTPStatusError and logs the error message and response
    and logs all other errors as well.
    """

    @wraps(func)
    def wrapper(self: "NorthboundApi", *args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(self, *args, **kwargs)
        except HTTPStatusError as e:
            self._log_error(e)
            raise e
        except Exception as e:
            logger.error(f"Error: {e}")
            raise e

    return wrapper


def invalid_token_exception(
    func: Callable[Concatenate["NorthboundApi", P], R],
) -> Callable[Concatenate["NorthboundApi", P], R]:
    """
    Decorator that catches 401 errors, refreshes the OAuth token,
    updates the client auth header, and retries the call once.
    """

    @wraps(func)
    def wrapper(self: "NorthboundApi", *args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(self, *args, **kwargs)
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("Received 401 Unauthorized. Refreshing token and retrying...")
                access_token = self.request_api_token()
                logger.debug(f"New token generated: {access_token}")
                # Execute once directly without hitting an infinite retry loop
                self.restClient.authHeader = access_token
                return func(self, *args, **kwargs)
            raise e

    return wrapper


class NorthboundApi:
    baseUrl: str
    username: str
    password: str
    access_token: str
    restClient: Rest_client

    def __init__(self, baseUrl, tokenUrl, username, password) -> None:
        # type: (str, str, str, str) -> None
        """Initialize the HESNbApi with base URL, username, and password."""
        self.baseUrl = baseUrl
        self.tokenUrl = tokenUrl
        self.username = username
        self.password = password
        self.access_token = self.request_api_token()
        self.restClient = Rest_client(base_url=self.baseUrl, authHeader=self.access_token)

    def _log_error(self, e: HTTPStatusError):
        """
        Logs the error message and response if available
        """
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Status Code: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")

    def request_api_token(self) -> str:
        """
        request new OAuth token from authentication server and store it in API client
        """

        payload: dict = {"grant_type": "client_credentials"}
        response = httpx.post(
            url=self.tokenUrl,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=payload,
            auth=BasicAuth(username=self.username, password=self.password),
        )
        response.raise_for_status()
        response_data = response.json()
        access_token = f"Bearer {response_data['access_token']}"
        return access_token

    ###################################################

    @invalid_token_exception
    @exception_handler
    def createCustomer(
        self,
        customerId: str,
        language: str,
        timeZone: str,
        typeof: str,
        salutation: str | None = None,
        email: str | None = None,
        secondaryEmail: str | None = None,
        name: str | None = None,
        familyName: str | None = None,
        mobilePhone: str | None = None,
        secondaryPhone: str | None = None,
        preferEmail: str | None = None,
        acceptedTerms: bool | None = None,
        city: str | None = None,
        country: str | None = None,
        company: str | None = None,
        street: str | None = None,
        houseNumber: str | None = None,
        postCode: str | None = None,
        title: str | None = None,
        group: str | None = None,
    ) -> dict:
        endpoint: str = f"/api/1/customers/{customerId}"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "salutation": salutation,
            "email": email,
            "secondaryEmail": secondaryEmail,
            "givenName": name,
            "familyName": familyName,
            "mobilePhone": mobilePhone,
            "secondaryPhone": secondaryPhone,
            "preferEmail": preferEmail,
            "language": language,
            "timeZone": timeZone,
            "acceptedTerms": acceptedTerms,
            "city": city,
            "country": country,
            "company": company,
            "street": street,
            "houseNumber": houseNumber,
            "postCode": postCode,
            "title": title,
            "type": typeof,
            "group": group,
        }
        response = self.restClient.put(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createMeteringPoint(
        self,
        meteringPointId: str,
        groupUuid: str,
        description: str | None = None,
        settlementUnit: str | None = None,
        substationID: str | None = None,
        serviceLevel: str | None = None,
        location: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        company: str | None = None,
        street: str | None = None,
        houseNumber: str | None = None,
        floor: str | None = None,
        postalCode: str | None = None,
        city: str | None = None,
        district: str | None = None,
        region: str | None = None,
        country: str | None = None,
        timeZone: str | None = None,
        reference: str | None = None,
        state: str | None = None,
    ):
        endpoint: str = f"/api/2/metering-points/{meteringPointId}"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "groupUuid": groupUuid,
        }

        if description:
            data["description"] = description

        if settlementUnit:
            data["settlementUnit"] = settlementUnit

        if substationID:
            data["substationId"] = substationID

        if serviceLevel:
            data["serviceLevel"] = serviceLevel

        if location:
            data["location"] = location

        if latitude:
            data["latitude"] = latitude

        if longitude:
            data["longitude"] = longitude

        if company:
            data["address"]["company"] = company

        if street:
            data["address"]["street"] = street

        if houseNumber:
            data["address"]["houseNumber"] = houseNumber

        if floor:
            data["address"]["floor"] = floor

        if postalCode:
            data["address"]["postalCode"] = postalCode

        if city:
            data["address"]["city"] = city

        if district:
            data["address"]["district"] = district

        if region:
            data["address"]["region"] = region

        if country:
            data["address"]["country"] = country

        if timeZone:
            data["address"]["timeZone"] = timeZone

        if reference:
            data["address"]["reference"] = reference

        if state:
            data["state"] = state

        response: Response = self.restClient.put(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def setMeteringPointParameters(
        self, meteringPoint: str, parameter: str, activeAt: str | None
    ) -> list:
        endpoint: str = "/api/1/bulk/metering-point-parameters"
        data: list[dict[str, str | None]] = [
            {
                "meteringPoint": meteringPoint,
                "parameter": parameter,
            }
        ]

        if activeAt:
            data[0]["activeAt"] = activeAt

        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def bulkSetMeteringPointParameters(
        self,
        meteringPoint: str,
        parameters: dict[str, str] | None = None,
        activeAt: str | None = None,
    ) -> list:
        endpoint: str = "/api/1/bulk/metering-point-parameters"
        data: list[dict[str, str | dict[str, str] | None]] = [
            {
                "meteringPoint": meteringPoint,
                "parameters": parameters,
            }
        ]

        if activeAt:
            data[0]["activeAt"] = activeAt
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createDevice(
        self,
        device: dict,
    ) -> list:
        endpoint: str = "/api/3/devices"
        data: list[dict] = [device]

        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        print(data)
        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    # @invalid_token_exception
    # @exception_handler
    # def createDevice(
    #     self,
    #     device_id: str,
    #     communication_id: str,
    #     template_uuid: str,
    #     type_uuid: str,
    #     group_uuid: str,
    #     store_data: bool,
    #     parameters: dict[str, str] | None = None,
    #     identifiers: dict[str, str] | None = None,
    #     street: str | None = None,
    #     house_number: str | None = None,
    #     floor: str | None = None,
    #     postal_code: str | None = None,
    #     city: str | None = None,
    #     district: str | None = None,
    #     region: str | None = None,
    #     country: str | None = None,
    #     time_zone: str | None = None,
    #     reference: str | None = None,
    #     company: str | None = None,
    #     latitude: str | None = None,
    #     longitude: str | None = None,
    #     model: str | None = None,
    #     manufacturer: str | None = None,
    #     description: str | None = None,
    #     inventory_state: str | None = None,
    #     dispatch_group: str | None = None,
    # ) -> list:
    #     endpoint: str = "/api/3/devices"
    #     data: list[dict] = [
    #         {
    #             "id": device_id,
    #             "communicationId": communication_id,
    #             "templateId": template_uuid,
    #             "typeId": type_uuid,
    #             "groupUuid": group_uuid,
    #             "storeData": store_data,
    #             "identifiers": None,
    #             "configuration": None,
    #             "location": {
    #                 "position": {
    #                     "latitude": None,
    #                     "longitude": None,
    #                 },
    #                 "address": {
    #                     "street": None,
    #                     "houseNumber": None,
    #                     "floor": None,
    #                     "postalCode": None,
    #                     "city": None,
    #                     "district": None,
    #                     "region": None,
    #                     "country": None,
    #                     "timeZone": None,
    #                     "reference": None,
    #                     "company": None,
    #                 },
    #             },
    #             "model": None,
    #             "manufacturer": None,
    #             "description": None,
    #             "inventoryState": None,
    #             "dispatchGroup": None,
    #         }
    #     ]

    #     if identifiers:
    #         data[0]["identifiers"] = identifiers
    #     if parameters:
    #         data[0]["configuration"] = parameters
    #     if street:
    #         data[0]["location"]["street"] = street
    #     if house_number:
    #         data[0]["location"]["houseNumber"] = house_number
    #     if floor:
    #         data[0]["location"]["floor"] = floor
    #     if postal_code:
    #         data[0]["location"]["postalCode"] = postal_code
    #     if city:
    #         data[0]["location"]["city"] = city
    #     if district:
    #         data[0]["location"]["district"] = district
    #     if region:
    #         data[0]["location"]["region"] = region
    #     if country:
    #         data[0]["location"]["country"] = country
    #     if time_zone:
    #         data[0]["location"]["timeZone"] = time_zone
    #     if reference:
    #         data[0]["location"]["reference"] = reference
    #     if company:
    #         data[0]["location"]["company"] = company
    #     if latitude:
    #         data[0]["location"]["position"]["latitude"] = latitude
    #     if longitude:
    #         data[0]["location"]["position"]["longitude"] = longitude
    #     if model:
    #         data[0]["model"] = model
    #     if manufacturer:
    #         data[0]["manufacturer"] = manufacturer
    #     if description:
    #         data[0]["description"] = description
    #     if inventory_state:
    #         data[0]["inventoryState"] = inventory_state
    #     if dispatch_group:
    #         data[0]["dispatchGroup"] = dispatch_group

    #     headers: dict[str, str] = {
    #         "Accept": "application/json",
    #         "Content-Type": "application/json",
    #     }
    #     print(data)
    #     response: Response = self.restClient.post(endpoint, data, headers)
    #     return response.json()

    @invalid_token_exception
    @exception_handler
    def setDeviceParameter(
        self, device: str, parameters: dict[str, str], activeAt: str | None = None
    ) -> list:
        endpoint: str = "/api/1/bulk/device-parameters"
        data: list[dict[str, str | dict[str, str] | None]] = [
            {
                "device": device,
                "parameters": parameters,
            }
        ]

        if activeAt:
            data[0]["activeAt"] = activeAt
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()
