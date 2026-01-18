"""Custom exceptions for the Hivecrew SDK."""

from typing import Optional


class HivecrewError(Exception):
    """Base exception for all Hivecrew SDK errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(HivecrewError):
    """Raised when API authentication fails (401)."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message, code="unauthorized", status_code=401)


class BadRequestError(HivecrewError):
    """Raised when the request is malformed (400)."""

    def __init__(self, message: str = "Invalid request parameters") -> None:
        super().__init__(message, code="bad_request", status_code=400)


class NotFoundError(HivecrewError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found", status_code=404)


class ConflictError(HivecrewError):
    """Raised when an action conflicts with the current state (409)."""

    def __init__(self, message: str = "Action not allowed for current state") -> None:
        super().__init__(message, code="conflict", status_code=409)


class PayloadTooLargeError(HivecrewError):
    """Raised when a file upload is too large (413)."""

    def __init__(self, message: str = "File upload too large") -> None:
        super().__init__(message, code="payload_too_large", status_code=413)


class ServerError(HivecrewError):
    """Raised when the server encounters an error (500)."""

    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(message, code="internal_error", status_code=500)


class TaskTimeoutError(HivecrewError):
    """Raised when waiting for a task to complete times out."""

    def __init__(self, task_id: str, timeout: float) -> None:
        message = f"Task {task_id} did not complete within {timeout} seconds"
        super().__init__(message, code="task_timeout")
        self.task_id = task_id
        self.timeout = timeout
