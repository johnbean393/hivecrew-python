"""Pydantic models for Hivecrew API responses."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    QUEUED = "queued"
    WAITING_FOR_VM = "waitingForVM"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timedOut"
    MAX_ITERATIONS = "maxIterations"


class RecurrenceType(str, Enum):
    """Recurrence type for scheduled tasks."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Recurrence(BaseModel):
    """Recurrence configuration for scheduled tasks."""

    type: RecurrenceType
    days_of_week: Optional[list[int]] = Field(default=None, alias="daysOfWeek")
    day_of_month: Optional[int] = Field(default=None, alias="dayOfMonth")
    hour: int
    minute: int

    model_config = {"populate_by_name": True}


class ScheduleConfig(BaseModel):
    """Schedule configuration for creating scheduled tasks."""

    scheduled_at: Optional[datetime] = Field(default=None, alias="scheduledAt")
    recurrence: Optional[Recurrence] = None

    model_config = {"populate_by_name": True}


class ScheduleType(str, Enum):
    """Type of schedule."""

    ONE_TIME = "one-time"
    RECURRING = "recurring"


class ScheduledTask(BaseModel):
    """A scheduled task template."""

    id: str
    title: str
    description: str
    provider_name: str = Field(alias="providerName")
    model_id: str = Field(alias="modelId")
    output_directory: Optional[str] = Field(default=None, alias="outputDirectory")
    is_enabled: bool = Field(alias="isEnabled")
    schedule_type: ScheduleType = Field(alias="scheduleType")
    scheduled_at: Optional[datetime] = Field(default=None, alias="scheduledAt")
    recurrence: Optional[Recurrence] = None
    next_run_at: Optional[datetime] = Field(default=None, alias="nextRunAt")
    last_run_at: Optional[datetime] = Field(default=None, alias="lastRunAt")
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class ScheduledTaskList(BaseModel):
    """Paginated list of scheduled tasks."""

    schedules: list[ScheduledTask]
    total: int
    limit: int
    offset: int


class TaskAction(str, Enum):
    """Actions that can be performed on a task."""

    CANCEL = "cancel"
    PAUSE = "pause"
    RESUME = "resume"


class TokenUsage(BaseModel):
    """Token usage information for a task."""

    prompt: int
    completion: int
    total: int


class FileInfo(BaseModel):
    """Information about a file associated with a task."""

    name: str
    size: int
    mime_type: Optional[str] = Field(default=None, alias="mimeType")
    uploaded_at: Optional[datetime] = Field(default=None, alias="uploadedAt")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    model_config = {"populate_by_name": True}


class Task(BaseModel):
    """A Hivecrew task."""

    id: str
    title: Optional[str] = None
    description: str
    status: TaskStatus
    provider_name: str = Field(alias="providerName")
    model_id: str = Field(alias="modelId")
    created_at: datetime = Field(alias="createdAt")
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")
    result_summary: Optional[str] = Field(default=None, alias="resultSummary")
    was_successful: Optional[bool] = Field(default=None, alias="wasSuccessful")
    vm_id: Optional[str] = Field(default=None, alias="vmId")
    duration: Optional[int] = None
    step_count: Optional[int] = Field(default=None, alias="stepCount")
    token_usage: Optional[TokenUsage] = Field(default=None, alias="tokenUsage")
    input_files: list[FileInfo] = Field(default_factory=list, alias="inputFiles")
    output_files: list[FileInfo] = Field(default_factory=list, alias="outputFiles")
    # List response has counts instead of full file arrays
    input_file_count: Optional[int] = Field(default=None, alias="inputFileCount")
    output_file_count: Optional[int] = Field(default=None, alias="outputFileCount")

    model_config = {"populate_by_name": True}

    def is_terminal(self) -> bool:
        """Check if the task is in a terminal (finished) state."""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMED_OUT,
            TaskStatus.MAX_ITERATIONS,
        }


class TaskList(BaseModel):
    """Paginated list of tasks."""

    tasks: list[Task]
    total: int
    limit: int
    offset: int


class TaskFilesResponse(BaseModel):
    """Response for listing task files."""

    task_id: str = Field(alias="taskId")
    input_files: list[FileInfo] = Field(default_factory=list, alias="inputFiles")
    output_files: list[FileInfo] = Field(default_factory=list, alias="outputFiles")

    model_config = {"populate_by_name": True}


class Model(BaseModel):
    """An AI model available from a provider."""

    id: str
    name: str
    context_length: Optional[int] = Field(default=None, alias="contextLength")

    model_config = {"populate_by_name": True}


class Provider(BaseModel):
    """An AI provider configuration."""

    id: str
    display_name: str = Field(alias="displayName")
    base_url: Optional[str] = Field(default=None, alias="baseURL")
    is_default: bool = Field(default=False, alias="isDefault")
    has_api_key: bool = Field(default=False, alias="hasAPIKey")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    model_config = {"populate_by_name": True}


class ProviderList(BaseModel):
    """List of providers."""

    providers: list[Provider]


class ModelList(BaseModel):
    """List of models from a provider."""

    models: list[Model]


class Template(BaseModel):
    """A VM template configuration."""

    id: str
    name: str
    description: Optional[str] = None
    is_default: bool = Field(default=False, alias="isDefault")
    cpu_count: Optional[int] = Field(default=None, alias="cpuCount")

    model_config = {"populate_by_name": True}


class TemplateList(BaseModel):
    """List of templates."""

    templates: list[Template]
    default_template_id: Optional[str] = Field(default=None, alias="defaultTemplateId")

    model_config = {"populate_by_name": True}


class AgentsInfo(BaseModel):
    """Information about running agents."""

    running: int
    paused: int
    queued: int
    max_concurrent: int = Field(alias="maxConcurrent")

    model_config = {"populate_by_name": True}


class VMsInfo(BaseModel):
    """Information about virtual machines."""

    active: int
    pending: int
    available: int


class ResourcesInfo(BaseModel):
    """System resource information."""

    memory_total_gb: float = Field(alias="memoryTotalGB")

    model_config = {"populate_by_name": True}


class SystemStatus(BaseModel):
    """System status information."""

    status: str
    version: str
    uptime: int
    agents: AgentsInfo
    vms: VMsInfo
    resources: ResourcesInfo


class SystemConfig(BaseModel):
    """System configuration."""

    max_concurrent_vms: int = Field(alias="maxConcurrentVMs")
    default_timeout_minutes: int = Field(alias="defaultTimeoutMinutes")
    default_max_iterations: int = Field(alias="defaultMaxIterations")
    default_template_id: Optional[str] = Field(default=None, alias="defaultTemplateId")
    api_port: int = Field(alias="apiPort")

    model_config = {"populate_by_name": True}
