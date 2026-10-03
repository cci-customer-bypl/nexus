from zonos_northbound_api.rest_client import Rest_client
from httpx import BasicAuth, Response
import logging
import httpx
from httpx._auth import BasicAuth
from httpx._exceptions import HTTPStatusError
from functools import wraps
from typing import TypeVar, ParamSpec, Concatenate, Callable

logger = logging.getLogger(__name__)


# def exception_handler(func):
#     """
#     Decorator that catches HTTPStatusError and logs the error message and response
#     and logs all other errors as well.
#     """

#     @functools.wraps(func)
#     def wrapper(self, *args, **kwargs):
#         try:
#             return func(self, *args, **kwargs)
#         except HTTPStatusError as e:
#             self._log_error(e)
#             raise e
#         except Exception as e:
#             logger.error(f"Error: {e}")
#             raise e

#     return wrapper


# def invalid_token_exception(func):
#     """
#     Decorator that catches 401 errors, refreshes the OAuth token,
#     updates the client auth header, and retries the call once.
#     """

#     @functools.wraps(func)
#     def wrapper(self, *args, **kwargs):
#         try:
#             return func(self, *args, **kwargs)
#         except HTTPStatusError as e:
#             if e.response.status_code == 401:
#                 logger.warning("Received 401 Unauthorized. Refreshing token and retrying...")
#                 access_token = self.request_api_token()
#                 logger.debug(f"New token generated: {access_token}")
#                 # Execute once directly without hitting an infinite retry loop
#                 self.restClient.authHeader = access_token
#                 return func(self, *args, **kwargs)
#             raise e

#     return wrapper
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

    @invalid_token_exception
    @exception_handler
    def getTransactionResults(self, trackingId: list[str]) -> list:
        endpoint: str = "/api/1/devices/control/bulk/get-transaction-results"
        data: list = trackingId
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response: Response = self.restClient.post(endpoint, data, headers)

        response.raise_for_status()

        return response.json()

    @invalid_token_exception
    @exception_handler
    def createGenericAction(
        self, device_id: str, executeAt: str, generic_action, external_id: str
    ) -> dict:
        endpoint: str = "/api/1/devices/control/generic/action"
        data: dict = {
            "devices": [device_id],
            "executeAt": executeAt,
            "retries": 0,
            "externalId": external_id,
            "name": generic_action,
            "generateQualityControlAlert": True,
            "priority": "HIGHEST",
        }
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response: Response = self.restClient.post(endpoint, data, headers)
        response.raise_for_status()

        return response.json()

    @invalid_token_exception
    @exception_handler
    def getDeviceEvents(self, deviceId: str, fromTime: str, toTime: str) -> list:
        endpoint: str = f"/api/1/bulk/device-events/get"
        data: list[dict[str, str]] = [{"device": deviceId, "from": fromTime, "to": toTime}]

        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def get_metereDataProfile(
        self, deviceId: str, profileId: str, fromTime: str, toTime: str
    ) -> list:

        endpoint = "/api/1/bulk/device-profiles/metered-data/get"
        data = [
            {
                "device": deviceId,
                "profile": profileId,
                "from": fromTime,
                "to": toTime,
                "fromInclusive": True,
                "toInclusive": True,
            }
        ]

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createDisconnectorControlConnect(
        self, deviceId: str, Armed: bool, force: bool, excuteAt: str, externalId: str
    ) -> dict:

        endpoint = "/api/1/devices/control/disconnect-control/connect"
        data = {
            "devices": [deviceId],
            "executeAt": excuteAt,
            "retries": 0,
            "externalId": externalId,
            "generateQualityControlAlert": True,
            "mode": {"armedConnect": Armed, "force": force},
            "retryDelay": 0,
            "priority": "HIGHEST",
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def getDisconnectControlConnectStatus(self, trackingId: str) -> dict:

        endpoint = f"/api/1/devices/control/disconnect-control/connect/{trackingId}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response: Response = self.restClient.get(endpoint, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createDisconnectorControlDisconnect(
        self, deviceId: str, excuteAt: str, externalId: str
    ) -> dict:

        endpoint = "/api/1/devices/control/disconnect-control/disconnect"
        data = {
            "devices": [deviceId],
            "executeAt": excuteAt,
            "retries": 0,
            "externalId": externalId,
            "generateQualityControlAlert": True,
            "priority": "HIGHEST",
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def getDisconnectControlDisconnectStatus(self, trackingId: str) -> dict:

        endpoint = f"/api/1/devices/control/disconnect-control/disconnect/{trackingId}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response: Response = self.restClient.get(endpoint, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createDisconnectorControlState(
        self, deviceId: str, executeAt: str, externalId: str
    ) -> dict:

        endpoint = "/api/1/devices/control/disconnect-control/get-state"
        data = {
            "devices": [deviceId],
            "externalId": externalId,
            "retries": 0,
            "executeAt": executeAt,
            "generateQualityControlAlert": True,
            "priority": "HIGHEST",
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response: Response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def getDisconnectorControlStateStatus(self, trackingId: str) -> dict:

        endpoint = f"/api/1/devices/control/disconnect-control/get-state/{trackingId}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        response: Response = self.restClient.get(endpoint, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createReadProfile(
        self,
        deviceId: str,
        profileId: str,
        readingReason: int,
        fromTime: str,
        toTime: str,
        externalId: str,
    ) -> dict:
        endpoint: str = f"/api/1/devices/control/meter-read/profiles/{profileId}"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "retryDelay": 0,
            "priority": "HIGHEST",
            "useProfileProgress": False,
            "readingReason": readingReason,
            "externalId": externalId,
            "from": fromTime,
            "to": toTime,
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def bulkCreateReadProfile(
        self,
        devices: list[str],
        profileId: str,
        readingReason: int,
        fromTime: str,
        toTime: str,
        externalId: str,
        executeAt: str | None,
        executeUntil: str | None,
        retries: int | None,
        retryDelay: int | None,
    ) -> dict:

        endpoint: str = f"/api/1/devices/control/meter-read/profiles/{profileId}"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": devices,
            "priority": "HIGHEST",
            "useProfileProgress": False,
            "readingReason": readingReason,
            "externalId": externalId,
            "from": fromTime,
            "to": toTime,
        }

        if executeAt is not None:
            data["executeAt"] = executeAt
        if executeUntil is not None:
            data["executeUntil"] = executeUntil
        if retries is not None:
            data["retries"] = retries
        if retryDelay is not None:
            data["retryDelay"] = retryDelay

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createReadTime(self, deviceId: str, externalId: str) -> dict:

        endpoint: str = "/api/1/devices/control/time/get"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createSyncTime(self, deviceId: str, externalId: str) -> dict:
        endpoint: str = "/api/1/devices/control/time/sync"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createMaximumDemandReset(self, deviceId: str, externalId: str) -> dict:

        endpoint: str = "/api/1/devices/control/maximum-demand-indicator/reset"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createReadParameter(self, deviceId: str, parameterName: str, externalId: str) -> dict:
        endpoint: str = "/api/1/devices/control/read-parameters"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "parameters": [parameterName],
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createWriteParameter(
        self, deviceId: str, parameterName: str, externalId: str, value: str
    ) -> dict:
        endpoint: str = "/api/1/devices/control/write-parameters"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "configuration": [{"name": parameterName, "value": value}],
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "LOWEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createReadLog(
        self, deviceId: str, logType: str, fromTime: str, toTime: str, externalId: str
    ) -> dict:

        endpoint: str = f"/api/1/devices/control/logs/{logType}/get"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "from": fromTime,
            "to": toTime,
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @exception_handler
    @invalid_token_exception
    def createGetActiviyCalender(
        self, deviceId: str, activityCalendarName: str, externalId: str
    ) -> dict:

        endpoint: str = "/api/2/devices/control/activity-calendar/get"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "activityCalendar": activityCalendarName,
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @exception_handler
    @invalid_token_exception
    def createSetActiviyCalender(
        self,
        deviceId: str,
        activityCalendarName: str,
        activityCalenderConfig: str,
        activityCalenderActivateAt: str,
        externalId: str,
    ) -> dict:

        endpoint: str = "/api/2/devices/control/activity-calendar/set"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "activityCalendar": activityCalendarName,
            "configuration": activityCalenderConfig,
            "activateAt": activityCalenderActivateAt,
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def getActivityCalendarConfiguration(self) -> list:
        endpoint: str = "/api/2/activity-calendar-configurations"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response: Response = self.restClient.get(endpoint, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createGetLoadLimiterConfiguration(self, deviceId: str, externalId: str) -> dict:

        endpoint: str = "/api/1/devices/control/load-limit/get"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "generateQualityControlAlert": True,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }

        response = self.restClient.post(endpoint, data, headers)
        return response.json()

    @invalid_token_exception
    @exception_handler
    def createSetLoadLimiterConfiguration(
        self,
        deviceId: str,
        normal_threshold: float,
        emergency_threshold: float | None,
        over_threshold_duration: int,
        under_threshold_duration: int,
        type: str,
        externalId: str,
    ) -> dict:

        endpoint: str = "/api/2/devices/control/load-limit/set"
        headers: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: dict = {
            "devices": [deviceId],
            "retries": 0,
            "externalId": externalId,
            "generateQualityControlAlert": True,
            "normalThreshold": normal_threshold,
            "emergencyThreshold": emergency_threshold,
            "overThresholdDuration": over_threshold_duration,
            "underThresholdDuration": under_threshold_duration,
            "type": type,
            "retryDelay": 0,
            "priority": "HIGHEST",
        }
        # logger.info(f"Request body for set Load Limiter Configuration: {data}")

        response = self.restClient.post(endpoint, data, headers)
        return response.json()
