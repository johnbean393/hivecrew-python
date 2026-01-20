"""Schedules resource for the Hivecrew API."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from hivecrew.models import (
    Recurrence,
    ScheduleConfig,
    ScheduledTask,
    ScheduledTaskList,
    Task,
)

if TYPE_CHECKING:
    from hivecrew.client import HivecrewClient


class SchedulesResource:
    """Resource for managing scheduled tasks.

    Scheduled tasks are task templates that run at specified times. When a
    scheduled task triggers, it creates a new task that runs immediately.
    """

    def __init__(self, client: "HivecrewClient") -> None:
        self._client = client

    def create(
        self,
        title: str,
        description: str,
        provider_name: str,
        model_id: str,
        schedule: Union[ScheduleConfig, dict],
        output_directory: Optional[Union[str, Path]] = None,
    ) -> ScheduledTask:
        """Create a new scheduled task.

        Args:
            title: Title for the scheduled task.
            description: The task description/instructions for the agent.
            provider_name: The AI provider name (e.g., "OpenRouter").
            model_id: The model ID (e.g., "anthropic/claude-sonnet-4.5").
            schedule: Schedule configuration. Can be a ScheduleConfig object or dict.
                For one-time schedules, provide scheduledAt.
                For recurring schedules, provide recurrence with type, hour, minute,
                and optionally daysOfWeek (for weekly) or dayOfMonth (for monthly).
            output_directory: Optional directory for task output files.

        Returns:
            The created scheduled task.

        Example:
            >>> # One-time schedule
            >>> scheduled = client.schedules.create(
            ...     title="Generate Report",
            ...     description="Generate the weekly status report",
            ...     provider_name="OpenRouter",
            ...     model_id="anthropic/claude-sonnet-4.5",
            ...     schedule=ScheduleConfig(
            ...         scheduled_at=datetime(2026, 1, 21, 9, 0, 0)
            ...     )
            ... )

            >>> # Recurring schedule (every Monday at 9am)
            >>> scheduled = client.schedules.create(
            ...     title="Weekly Email Summary",
            ...     description="Check emails and create a summary",
            ...     provider_name="OpenRouter",
            ...     model_id="anthropic/claude-sonnet-4.5",
            ...     schedule=ScheduleConfig(
            ...         recurrence=Recurrence(
            ...             type=RecurrenceType.WEEKLY,
            ...             days_of_week=[2],  # Monday (1=Sunday)
            ...             hour=9,
            ...             minute=0
            ...         )
            ...     )
            ... )
        """
        # Convert output_directory to absolute path string
        output_dir_str: Optional[str] = None
        if output_directory:
            output_dir_str = str(Path(output_directory).expanduser().resolve())

        # Convert schedule to dict for API request
        if isinstance(schedule, ScheduleConfig):
            schedule_dict = schedule.model_dump(mode="json", by_alias=True, exclude_none=True)
        else:
            schedule_dict = schedule

        body: dict = {
            "title": title,
            "description": description,
            "providerName": provider_name,
            "modelId": model_id,
            "schedule": schedule_dict,
        }
        if output_dir_str:
            body["outputDirectory"] = output_dir_str

        response = self._client._request("POST", "/schedules", json=body)
        return ScheduledTask.model_validate(response.json())

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> ScheduledTaskList:
        """List scheduled tasks.

        Args:
            limit: Maximum number of results (1-200). Default 50.
            offset: Pagination offset. Default 0.

        Returns:
            Paginated list of scheduled tasks.

        Example:
            >>> result = client.schedules.list(limit=10)
            >>> for schedule in result.schedules:
            ...     print(f"{schedule.title}: next run at {schedule.next_run_at}")
        """
        params: dict[str, int] = {
            "limit": limit,
            "offset": offset,
        }

        response = self._client._request("GET", "/schedules", params=params)
        return ScheduledTaskList.model_validate(response.json())

    def get(self, schedule_id: str) -> ScheduledTask:
        """Get details of a specific scheduled task.

        Args:
            schedule_id: The scheduled task ID.

        Returns:
            The scheduled task with full details.

        Example:
            >>> schedule = client.schedules.get("A1B2C3D4...")
            >>> print(f"Next run: {schedule.next_run_at}")
        """
        response = self._client._request("GET", f"/schedules/{schedule_id}")
        return ScheduledTask.model_validate(response.json())

    def update(
        self,
        schedule_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_at: Optional[str] = None,
        recurrence: Optional[Union[Recurrence, dict]] = None,
        is_enabled: Optional[bool] = None,
    ) -> ScheduledTask:
        """Update a scheduled task.

        Args:
            schedule_id: The scheduled task ID.
            title: New title.
            description: New description.
            scheduled_at: New scheduled time as ISO 8601 datetime string (one-time).
            recurrence: New recurrence configuration.
            is_enabled: Enable or disable the schedule.

        Returns:
            The updated scheduled task.

        Example:
            >>> schedule = client.schedules.update(
            ...     schedule_id="A1B2C3D4...",
            ...     is_enabled=False
            ... )
        """
        body: dict = {}
        if title is not None:
            body["title"] = title
        if description is not None:
            body["description"] = description
        if scheduled_at is not None:
            body["scheduledAt"] = scheduled_at
        if recurrence is not None:
            if isinstance(recurrence, Recurrence):
                body["recurrence"] = recurrence.model_dump(mode="json", by_alias=True, exclude_none=True)
            else:
                body["recurrence"] = recurrence
        if is_enabled is not None:
            body["isEnabled"] = is_enabled

        response = self._client._request("PATCH", f"/schedules/{schedule_id}", json=body)
        return ScheduledTask.model_validate(response.json())

    def delete(self, schedule_id: str) -> None:
        """Delete a scheduled task.

        Args:
            schedule_id: The scheduled task ID.
        """
        self._client._request("DELETE", f"/schedules/{schedule_id}")

    def run_now(self, schedule_id: str) -> Task:
        """Trigger a scheduled task to run immediately.

        Creates a new task from the scheduled task template and runs it
        immediately. Does not affect the schedule's next run time.

        Args:
            schedule_id: The scheduled task ID.

        Returns:
            The created task.

        Example:
            >>> task = client.schedules.run_now("A1B2C3D4...")
            >>> print(f"Task created: {task.id}")
        """
        response = self._client._request("POST", f"/schedules/{schedule_id}/run")
        return Task.model_validate(response.json())
