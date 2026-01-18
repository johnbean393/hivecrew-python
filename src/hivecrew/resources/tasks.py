"""Tasks resource for the Hivecrew API."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from hivecrew.exceptions import TaskTimeoutError
from hivecrew.models import Task, TaskAction, TaskFilesResponse, TaskList, TaskStatus

if TYPE_CHECKING:
    from hivecrew.client import HivecrewClient


class TasksResource:
    """Resource for managing tasks.

    Tasks are computer-use agent jobs that can be created, monitored, and controlled.
    """

    def __init__(self, client: "HivecrewClient") -> None:
        self._client = client

    def create(
        self,
        description: str,
        provider_name: str,
        model_id: str,
        files: Optional[list[Union[str, Path]]] = None,
    ) -> Task:
        """Create a new task.

        Args:
            description: The task description/instructions for the agent.
            provider_name: The AI provider name (e.g., "OpenRouter").
            model_id: The model ID (e.g., "anthropic/claude-sonnet-4.5").
            files: Optional list of file paths to upload with the task.

        Returns:
            The created task.

        Example:
            >>> task = client.tasks.create(
            ...     description="Open Safari and search for Python",
            ...     provider_name="OpenRouter",
            ...     model_id="anthropic/claude-sonnet-4.5"
            ... )
        """
        if files:
            # Multipart form upload
            form_data = {
                "description": description,
                "providerName": provider_name,
                "modelId": model_id,
            }
            file_tuples = []
            for file_path in files:
                path = Path(file_path)
                file_tuples.append(("files", (path.name, open(path, "rb"))))

            try:
                response = self._client._request(
                    "POST",
                    "/tasks",
                    data=form_data,
                    files=file_tuples,
                )
            finally:
                # Close file handles
                for _, (_, f) in file_tuples:
                    f.close()
        else:
            # JSON request
            response = self._client._request(
                "POST",
                "/tasks",
                json={
                    "description": description,
                    "providerName": provider_name,
                    "modelId": model_id,
                },
            )

        return Task.model_validate(response.json())

    def run(
        self,
        description: str,
        provider_name: str,
        model_id: str,
        files: Optional[list[Union[str, Path]]] = None,
        poll_interval: float = 5.0,
        timeout: Optional[float] = 1200.0,
    ) -> Task:
        """Create a task and wait for it to complete.

        This is a blocking method that creates a task and polls until it reaches
        a terminal state (completed, failed, cancelled, timedOut, or maxIterations).

        Args:
            description: The task description/instructions for the agent.
            provider_name: The AI provider name (e.g., "OpenRouter").
            model_id: The model ID (e.g., "anthropic/claude-sonnet-4.5").
            files: Optional list of file paths to upload with the task.
            poll_interval: How often to check task status, in seconds. Default 5.
            timeout: Maximum time to wait for completion, in seconds. Default 1200 (20 minutes).
                Set to None for no timeout.

        Returns:
            The completed task with full details.

        Raises:
            TaskTimeoutError: If the task doesn't complete within the timeout.

        Example:
            >>> task = client.tasks.run(
            ...     description="Take a screenshot of the desktop",
            ...     provider_name="OpenRouter",
            ...     model_id="anthropic/claude-sonnet-4.5",
            ...     timeout=300.0
            ... )
            >>> print(f"Task {task.status}: {task.result_summary}")
        """
        task = self.create(
            description=description,
            provider_name=provider_name,
            model_id=model_id,
            files=files,
        )

        start_time = time.monotonic()

        while True:
            task = self.get(task.id)

            if task.is_terminal():
                return task

            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    raise TaskTimeoutError(task.id, timeout)

            time.sleep(poll_interval)

    def list(
        self,
        status: Optional[list[Union[str, TaskStatus]]] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "createdAt",
        order: str = "desc",
    ) -> TaskList:
        """List tasks with optional filtering.

        Args:
            status: Filter by status(es). Can be strings or TaskStatus enum values.
            limit: Maximum number of results (1-200). Default 50.
            offset: Pagination offset. Default 0.
            sort: Sort field: "createdAt", "startedAt", or "completedAt". Default "createdAt".
            order: Sort order: "asc" or "desc". Default "desc".

        Returns:
            Paginated list of tasks.

        Example:
            >>> result = client.tasks.list(status=["running", "queued"], limit=10)
            >>> for task in result.tasks:
            ...     print(f"{task.id}: {task.status}")
        """
        params: dict[str, Union[str, int]] = {
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "order": order,
        }

        if status:
            # Convert enum values to strings and join
            status_strs = [s.value if isinstance(s, TaskStatus) else s for s in status]
            params["status"] = ",".join(status_strs)

        response = self._client._request("GET", "/tasks", params=params)
        return TaskList.model_validate(response.json())

    def get(self, task_id: str) -> Task:
        """Get details of a specific task.

        Args:
            task_id: The task ID.

        Returns:
            The task with full details.

        Example:
            >>> task = client.tasks.get("A1B2C3D4-E5F6-7890-ABCD-EF1234567890")
            >>> print(task.status)
        """
        response = self._client._request("GET", f"/tasks/{task_id}")
        return Task.model_validate(response.json())

    def cancel(self, task_id: str) -> Task:
        """Cancel a running or queued task.

        Args:
            task_id: The task ID.

        Returns:
            The updated task.
        """
        return self._update(task_id, TaskAction.CANCEL)

    def pause(self, task_id: str) -> Task:
        """Pause a running task.

        Args:
            task_id: The task ID.

        Returns:
            The updated task.
        """
        return self._update(task_id, TaskAction.PAUSE)

    def resume(self, task_id: str, instructions: Optional[str] = None) -> Task:
        """Resume a paused task.

        Args:
            task_id: The task ID.
            instructions: Optional new instructions to provide when resuming.

        Returns:
            The updated task.
        """
        return self._update(task_id, TaskAction.RESUME, instructions=instructions)

    def _update(
        self,
        task_id: str,
        action: TaskAction,
        instructions: Optional[str] = None,
    ) -> Task:
        """Update a task with an action.

        Args:
            task_id: The task ID.
            action: The action to perform.
            instructions: Optional instructions (for resume action).

        Returns:
            The updated task.
        """
        body: dict[str, str] = {"action": action.value}
        if instructions:
            body["instructions"] = instructions

        response = self._client._request("PATCH", f"/tasks/{task_id}", json=body)
        return Task.model_validate(response.json())

    def delete(self, task_id: str) -> None:
        """Delete a task.

        Args:
            task_id: The task ID.
        """
        self._client._request("DELETE", f"/tasks/{task_id}")

    def list_files(self, task_id: str) -> TaskFilesResponse:
        """List files associated with a task.

        Args:
            task_id: The task ID.

        Returns:
            Response containing input and output files.

        Example:
            >>> files = client.tasks.list_files(task_id)
            >>> for f in files.output_files:
            ...     print(f"{f.name}: {f.size} bytes")
        """
        response = self._client._request("GET", f"/tasks/{task_id}/files")
        return TaskFilesResponse.model_validate(response.json())

    def download_file(
        self,
        task_id: str,
        filename: str,
        destination: Union[str, Path],
        file_type: str = "output",
    ) -> Path:
        """Download a file from a task.

        Args:
            task_id: The task ID.
            filename: The name of the file to download.
            destination: Path where the file should be saved. Can be a directory
                (file will be saved with original name) or full file path.
            file_type: Either "input" or "output". Default "output".

        Returns:
            Path to the downloaded file.

        Example:
            >>> path = client.tasks.download_file(
            ...     task_id,
            ...     "screenshot.png",
            ...     "./downloads/"
            ... )
            >>> print(f"Downloaded to {path}")
        """
        dest = Path(destination)

        # If destination is a directory, use the original filename
        if dest.is_dir():
            dest = dest / filename

        params = {"type": file_type}
        response = self._client._request(
            "GET",
            f"/tasks/{task_id}/files/{filename}",
            params=params,
            stream=True,
        )

        # Write the file
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return dest
