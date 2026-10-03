import logging
from typing import Any, Dict, List, Union
import httpx
from httpx import Response

logger = logging.getLogger(__name__)


class Rest_client:
    """A class to handle REST API calls."""

    def __init__(self, base_url: str, authHeader: str):
        self.base_url = base_url
        self.authHeader = authHeader  # Holds "Bearer "

    def _prepare_headers(self, request_headers: Dict[str, Any]) -> Dict[str, str]:
        """Inject default headers and the Authorization Bearer token."""
        headers = dict(request_headers) if request_headers else {}
        headers["Content-Type"] = "application/json"
        if self.authHeader:
            headers["Authorization"] = self.authHeader
        return headers

    def get(
        self, endpoint: str, request_headers: Dict[str, Any], timeout: int = 30
    ) -> Response:
        headers = self._prepare_headers(request_headers)
        url = f"{self.base_url}{endpoint}"

        response: Response = httpx.get(
            url, headers=headers, verify=False, timeout=timeout
        )
        response.raise_for_status()
        return response

    def post(
        self,
        endpoint: str,
        data: Union[Dict[str, Any], List[Any]],
        request_headers: Dict[str, Any],
        timeout: int = 30,
    ) -> Response:
        headers = self._prepare_headers(request_headers)
        url = f"{self.base_url}{endpoint}"

        response: Response = httpx.post(
            url, json=data, headers=headers, verify=False, timeout=timeout
        )
        response.raise_for_status()
        return response

    def put(
        self,
        endpoint: str,
        data: Dict[str, Any],
        request_headers: Dict[str, Any],
        timeout: int = 30,
    ) -> Response:
        headers = self._prepare_headers(request_headers)
        url = f"{self.base_url}{endpoint}"

        response: Response = httpx.put(
            url, json=data, headers=headers, verify=False, timeout=timeout
        )
        response.raise_for_status()
        return response


# import httpx
# from httpx import BasicAuth
# import logging
# from sys import stdout, stderr, stdin
# # logging.basicConfig(level=logging.NOTSET, format='%(asctime)s - %(levelname)s - %(message)s', stream=stdout)
# from typing import Optional, Dict, Any, Union, List, Tuple, Callable, Type, Iterator, Iterable, Sequence, Mapping, Set, FrozenSet, Deque, Generator, AsyncGenerator
# # from models.response import Response
# from httpx import Response

# logger = logging.getLogger(__name__)

# class Rest_client:
#     """A class to handle REST API calls."""

#     def __init__(self, base_url, authHeader):
#         #type: (str, BasicAuth) -> None
#         """Initialize the REST client with a base URL.
#         Args:
#             base_url (str): The base (https://hostname) URL for the API.
#         """
#         self.base_url = base_url
#         self.authHeader = authHeader


#     def get(self, endpoint, request_headers,timeout=30):
#     #type: (str, Dict[str, Any], int) -> Response
#         """
#         Send a POST request to the specified endpoint.

#         Args:
#             endpoint (str): API endpoint path
#             data (dict): JSON data to send in request body
#             headers (dict): Additional headers for the request
#             timeout (int): Request timeout in seconds (default: 30)

#         Returns:
#             dict: JSON response data

#         Raises:
#             APIException: For API-related errors
#             NetworkException: For network-related errors
#         """
#         request_headers['Content-Type'] = 'application/json'
#         try:

#             url = f"{self.base_url}{endpoint}"

#             # Make the request
#             response:Response = httpx.get(
#                 url,
#                 headers=request_headers,
#                 auth=self.authHeader,
#                 verify=False,
#                 timeout=timeout
#             )

#             # Raise for HTTP error status codes
#             response.raise_for_status()

#             # Return JSON response
#             return response

#         except httpx.HTTPStatusError as e:
#             error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
#             logger.error(f"API Error: {error_msg}")
#             raise httpx.HTTPStatusError(
#                 f"API Error: {error_msg}",
#                 request=e.request,
#                 response=e.response
#             )

#         except httpx.TimeoutException:
#             error_msg = f"Request timeout after {timeout} seconds"
#             logger.error(f"Timeout Error: {error_msg}")
#             raise TimeoutError(error_msg)  # Built-in Python exception

#         except httpx.ConnectError as e:
#             error_msg = f"Connection failed: {str(e)}"
#             logger.error(f"Connection Error: {error_msg}")
#             raise ConnectionError(error_msg)  # Built-in Python exception

#         except httpx.RequestError as e:
#             error_msg = f"Request error: {str(e)}"
#             logger.error(f"Request Error: {error_msg}")
#             raise ConnectionError(error_msg)  # Built-in Python exception

#         except ValueError as e:
#             # JSON decode error
#             error_msg = f"Invalid JSON response: {str(e)}"
#             logger.error(f"JSON Error: {error_msg}")
#             raise ValueError(error_msg)  # Built-in Python exception

#         except Exception as e:
#             error_msg = f"Unexpected error: {str(e)}"
#             logger.error(f"Unexpected Error: {error_msg}")
#             raise RuntimeError(error_msg)  # Built-in Python exception

#     def post(self, endpoint, data, request_headers, timeout=30):
#     #type: (str, Dict[str, Any] | list, Dict[str, Any],int) -> Response
#         """
#         Send a POST request to the specified endpoint.

#         Args:
#             endpoint (str): API endpoint path
#             data (dict): JSON data to send in request body
#             headers (dict): Additional headers for the request
#             timeout (int): Request timeout in seconds (default: 30)

#         Returns:
#             dict: JSON response data

#         Raises:
#             APIException: For API-related errors
#             NetworkException: For network-related errors
#         """
#         request_headers['Content-Type'] = 'application/json'
#         try:

#             url = f"{self.base_url}{endpoint}"

#             # Make the request
#             response:Response = httpx.post(
#                 url,
#                 json=data,
#                 headers=request_headers,
#                 auth=self.authHeader,
#                 verify=False,
#                 timeout=timeout
#             )

#             # Raise for HTTP error status codes
#             response.raise_for_status()

#             # Return JSON response
#             return response

#         except httpx.HTTPStatusError as e:
#             error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
#             logger.error(f"API Error: {error_msg}")
#             raise httpx.HTTPStatusError(
#                 f"API Error: {error_msg}",
#                 request=e.request,
#                 response=e.response
#             )

#         except httpx.TimeoutException:
#             error_msg = f"Request timeout after {timeout} seconds"
#             logger.error(f"Timeout Error: {error_msg}")
#             raise TimeoutError(error_msg)  # Built-in Python exception

#         except httpx.ConnectError as e:
#             error_msg = f"Connection failed: {str(e)}"
#             logger.error(f"Connection Error: {error_msg}")
#             raise ConnectionError(error_msg)  # Built-in Python exception

#         except httpx.RequestError as e:
#             error_msg = f"Request error: {str(e)}"
#             logger.error(f"Request Error: {error_msg}")
#             raise ConnectionError(error_msg)  # Built-in Python exception

#         except ValueError as e:
#             # JSON decode error
#             error_msg = f"Invalid JSON response: {str(e)}"
#             logger.error(f"JSON Error: {error_msg}")
#             raise ValueError(error_msg)  # Built-in Python exception

#         except Exception as e:
#             error_msg = f"Unexpected error: {str(e)}"
#             logger.error(f"Unexpected Error: {error_msg}")
#             raise RuntimeError(error_msg)  # Built-in Python exception

#     def put(self, endpoint, data, request_headers,timeout=30):
#     #type: (str, Dict[str, Any], Dict[str, Any],int) -> Response
#         """
#         Send a PUT request to the specified endpoint.

#         Args:
#             endpoint (str): API endpoint path
#             data (dict): JSON data to send in request body
#             headers (dict): Additional headers for the request
#             timeout (int): Request timeout in seconds (default: 30)

#         Returns:
#             dict: JSON response data

#         Raises:
#             APIException: For API-related errors
#             NetworkException: For network-related errors
#         """
#         try:
#             url = f"{self.base_url}{endpoint}"

#             # Make the request
#             response:Response = httpx.put(
#                 url,
#                 json=data,
#                 headers=request_headers,
#                 auth=self.authHeader,
#                 verify=False,
#                 timeout=timeout
#             )

#             # Raise for HTTP error status codes
#             response.raise_for_status()

#             # Return JSON response
#             return response

#         except httpx.HTTPStatusError as e:
#             error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
#             logger.error(f"API Error: {error_msg}")
#             raise httpx.HTTPStatusError(
#                 f"API Error: {error_msg}",
#                 request=e.request,
#                 response=e.response
#             )

#         except httpx.TimeoutException:
#             error_msg = f"Request timeout after {timeout} seconds"
#             logger.error(f"Timeout Error: {error_msg}")
#             raise TimeoutError(error_msg)  # Built-in Python exception

#         except httpx.ConnectError as e:
#             error_msg = f"Connection failed: {str(e)}"
#             logger.error(f"Connection Error: {error_msg}")
#             raise ConnectionError(error_msg)  # Built-in Python exception

#         except httpx.RequestError as e:
#             error_msg = f"Request error: {str(e)}"
#             logger.error(f"Request Error: {error_msg}")
#             raise ConnectionError(error_msg)  # Built-in Python exception

#         except ValueError as e:
#             # JSON decode error
#             error_msg = f"Invalid JSON response: {str(e)}"
#             logger.error(f"JSON Error: {error_msg}")
#             raise ValueError(error_msg)  # Built-in Python exception

#         except Exception as e:
#             error_msg = f"Unexpected error: {str(e)}"
#             logger.error(f"Unexpected Error: {error_msg}")
#             raise RuntimeError(error_msg)  # Built-in Python exception
