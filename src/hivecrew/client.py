"""Hivecrew API client."""

import os
from typing import Any, Optional

import requests

from hivecrew.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    HivecrewError,
    NotFoundError,
    PayloadTooLargeError,
    ServerError,
)
from hivecrew.resources.providers import ProvidersResource
from hivecrew.resources.system import SystemResource
from hivecrew.resources.tasks import TasksResource
from hivecrew.resources.templates import TemplatesResource

DEFAULT_BASE_URL = "http://localhost:5482/api/v1"
DEFAULT_TIMEOUT = 30.0


class HivecrewClient:
    """Client for interacting with the Hivecrew REST API.

    Args:
        api_key: The API key for authentication. If not provided, reads from
            HIVECREW_API_KEY environment variable.
        base_url: The base URL of the Hivecrew API. Defaults to http://localhost:5482/api/v1
        timeout: Request timeout in seconds. Defaults to 30.

    Example:
        >>> client = HivecrewClient(api_key="hc_xxx")
        >>> task = client.tasks.run(
        ...     description="Open Safari and search for Python",
        ...     provider_name="OpenRouter",
        ...     model_id="anthropic/claude-sonnet-4.5"
        ... )
        >>> print(task.status)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = api_key or os.environ.get("HIVECREW_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it as an argument or set HIVECREW_API_KEY "
                "environment variable."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Create a session for connection pooling
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

        # Initialize resource endpoints
        self.tasks = TasksResource(self)
        self.providers = ProvidersResource(self)
        self.templates = TemplatesResource(self)
        self.system = SystemResource(self)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
        stream: bool = False,
    ) -> requests.Response:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (e.g., "/tasks")
            params: Query parameters
            json: JSON body
            data: Form data (for multipart requests)
            files: Files to upload
            stream: Whether to stream the response

        Returns:
            The response object

        Raises:
            HivecrewError: If the request fails
        """
        url = f"{self.base_url}{path}"

        # For file uploads, don't send Content-Type header (let requests set it)
        headers = {}
        if files:
            headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=headers if files else None,
                timeout=self.timeout,
                stream=stream,
            )
        except requests.exceptions.Timeout as e:
            raise HivecrewError(f"Request timed out: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise HivecrewError(f"Connection error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise HivecrewError(f"Request failed: {e}") from e

        self._handle_error_response(response)
        return response

    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle error responses from the API.

        Args:
            response: The response object

        Raises:
            Appropriate HivecrewError subclass based on status code
        """
        if response.ok:
            return

        # Try to extract error message from JSON response
        message = f"HTTP {response.status_code}"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_info = error_data["error"]
                if isinstance(error_info, dict):
                    message = error_info.get("message", message)
                else:
                    message = str(error_info)
        except (ValueError, KeyError):
            message = response.text or message

        status_code = response.status_code
        if status_code == 400:
            raise BadRequestError(message)
        elif status_code == 401:
            raise AuthenticationError(message)
        elif status_code == 404:
            raise NotFoundError(message)
        elif status_code == 409:
            raise ConflictError(message)
        elif status_code == 413:
            raise PayloadTooLargeError(message)
        elif status_code >= 500:
            raise ServerError(message)
        else:
            raise HivecrewError(message, status_code=status_code)

    def health_check(self) -> bool:
        """Check if the Hivecrew API server is running.

        This endpoint does not require authentication.

        Returns:
            True if the server is healthy, False otherwise
        """
        try:
            # Health check is at root level, not under /api/v1
            base = self.base_url.replace("/api/v1", "")
            response = requests.get(f"{base}/health", timeout=self.timeout)
            return response.ok and response.text.strip() == "OK"
        except requests.exceptions.RequestException:
            return False

    def close(self) -> None:
        """Close the client session."""
        self._session.close()

    def __enter__(self) -> "HivecrewClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
