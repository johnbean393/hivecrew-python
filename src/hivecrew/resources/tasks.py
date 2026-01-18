"""Tasks resource for the Hivecrew API."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from hivecrew.exceptions import TaskTimeoutError
from hivecrew.models import Task, TaskAction, TaskFilesResponse, TaskList, TaskStatus

if TYPE_CHECKING:
    from hivecrew.client import HivecrewClient


@dataclass
class TaskResult:
    """Result of a completed task run, including any output files.

    Attributes:
        task: The completed Task object with full details.
        output_files: List of paths to output files collected from the output directory.
    """

    task: Task
    output_files: list[Path] = field(default_factory=list)

    # Convenience properties to access common task attributes
    @property
    def id(self) -> str:
        return self.task.id

    @property
    def status(self) -> TaskStatus:
        return self.task.status

    @property
    def was_successful(self) -> Optional[bool]:
        return self.task.was_successful

    @property
    def result_summary(self) -> Optional[str]:
        return self.task.result_summary

    # Backwards compatibility alias
    @property
    def downloaded_files(self) -> list[Path]:
        """Alias for output_files (deprecated, use output_files instead)."""
        return self.output_files


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
        output_directory: Optional[Union[str, Path]] = None,
    ) -> Task:
        """Create a new task.

        Args:
            description: The task description/instructions for the agent.
            provider_name: The AI provider name (e.g., "OpenRouter").
            model_id: The model ID (e.g., "anthropic/claude-sonnet-4.5").
            files: Optional list of file paths to upload with the task.
            output_directory: Optional local directory where Hivecrew should copy
                output files from the VM's outbox. Overrides the default output
                directory configured in Hivecrew settings.
                Example: "./task_outputs"

        Returns:
            The created task.

        Example:
            >>> task = client.tasks.create(
            ...     description="Generate a report and save it to the outbox",
            ...     provider_name="OpenRouter",
            ...     model_id="anthropic/claude-sonnet-4.5",
            ...     output_directory="./outputs"
            ... )
        """
        # Convert output_directory to absolute path string
        output_dir_str: Optional[str] = None
        if output_directory:
            output_dir_str = str(Path(output_directory).expanduser().resolve())

        if files:
            # Multipart form upload
            form_data = {
                "description": description,
                "providerName": provider_name,
                "modelId": model_id,
            }
            if output_dir_str:
                form_data["outputDirectory"] = output_dir_str

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
            body: dict[str, str] = {
                "description": description,
                "providerName": provider_name,
                "modelId": model_id,
            }
            if output_dir_str:
                body["outputDirectory"] = output_dir_str

            response = self._client._request(
                "POST",
                "/tasks",
                json=body,
            )

        return Task.model_validate(response.json())

    def run(
        self,
        description: str,
        provider_name: str,
        model_id: str,
        files: Optional[list[Union[str, Path]]] = None,
        output_directory: Optional[Union[str, Path]] = None,
        poll_interval: float = 5.0,
        timeout: Optional[float] = 1200.0,
    ) -> TaskResult:
        """Create a task and wait for it to complete.

        This is a blocking method that creates a task and polls until it reaches
        a terminal state (completed, failed, cancelled, timedOut, or maxIterations).

        Args:
            description: The task description/instructions for the agent.
            provider_name: The AI provider name (e.g., "OpenRouter").
            model_id: The model ID (e.g., "anthropic/claude-sonnet-4.5").
            files: Optional list of file paths to upload with the task.
            output_directory: Local directory where Hivecrew should copy output files
                from the VM's outbox after task completion. Overrides the default
                output directory configured in Hivecrew settings. The SDK will
                automatically collect file paths from this directory.
                Example: "./task_outputs"
            poll_interval: How often to check task status, in seconds. Default 5.
            timeout: Maximum time to wait for completion, in seconds. Default 1200 (20 minutes).
                Set to None for no timeout.

        Returns:
            TaskResult containing the completed task and list of output file paths.

        Raises:
            TaskTimeoutError: If the task doesn't complete within the timeout.

        Example:
            >>> result = client.tasks.run(
            ...     description="Create a report and save it to the outbox",
            ...     provider_name="OpenRouter",
            ...     model_id="anthropic/claude-sonnet-4.5",
            ...     output_directory="./outputs"
            ... )
            >>> print(f"Task {result.status}: {result.result_summary}")
            >>> for path in result.output_files:
            ...     print(f"Output: {path}")
        """
        # Resolve output directory to absolute path
        output_dir: Optional[Path] = None
        if output_directory:
            output_dir = Path(output_directory).expanduser().resolve()
            output_dir.mkdir(parents=True, exist_ok=True)

        task = self.create(
            description=description,
            provider_name=provider_name,
            model_id=model_id,
            files=files,
            output_directory=output_dir,
        )

        start_time = time.monotonic()

        while True:
            task = self.get(task.id)

            if task.is_terminal():
                break

            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    raise TaskTimeoutError(task.id, timeout)

            time.sleep(poll_interval)

        # Collect output files from the output directory
        output_files: list[Path] = []
        if output_dir and task.was_successful:
            # Brief delay to allow file sync to complete
            time.sleep(1.0)

            # List all files in the output directory
            if output_dir.exists():
                for item in output_dir.iterdir():
                    if item.is_file():
                        output_files.append(item)

        return TaskResult(task=task, output_files=output_files)

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
