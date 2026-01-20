"""Hivecrew Python SDK - A Python client for the Hivecrew REST API."""

from hivecrew.client import HivecrewClient
from hivecrew.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    HivecrewError,
    NotFoundError,
    PayloadTooLargeError,
    ServerError,
    TaskTimeoutError,
)
from hivecrew.models import (
    FileInfo,
    Model,
    Provider,
    ProviderList,
    Recurrence,
    RecurrenceType,
    ScheduleConfig,
    ScheduledTask,
    ScheduledTaskList,
    ScheduleType,
    SystemConfig,
    SystemStatus,
    Task,
    TaskAction,
    TaskFilesResponse,
    TaskList,
    TaskStatus,
    Template,
    TemplateList,
    TokenUsage,
)
from hivecrew.resources.tasks import TaskResult

__version__ = "0.1.0"

__all__ = [
    # Client
    "HivecrewClient",
    # Exceptions
    "HivecrewError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "NotFoundError",
    "PayloadTooLargeError",
    "ServerError",
    "TaskTimeoutError",
    # Task Models
    "Task",
    "TaskList",
    "TaskResult",
    "TaskStatus",
    "TaskAction",
    "TaskFilesResponse",
    "TokenUsage",
    "FileInfo",
    # Schedule Models
    "ScheduleConfig",
    "ScheduledTask",
    "ScheduledTaskList",
    "ScheduleType",
    "Recurrence",
    "RecurrenceType",
    # Provider Models
    "Provider",
    "ProviderList",
    "Model",
    # Template Models
    "Template",
    "TemplateList",
    # System Models
    "SystemStatus",
    "SystemConfig",
]
