"""Test script for the tasks endpoint."""

from hivecrew import HivecrewClient


def test_create_task():
    """Test creating a task."""
    client = HivecrewClient()

    task = client.tasks.create(
        description="Open Safari and search for Python tutorials",
        provider_name="OpenRouter",
        model_id="anthropic/claude-sonnet-4.5",
    )

    print(f"Task created: {task.id}")
    print(f"Status: {task.status}")
    assert task.id is not None
    assert task.status.value == "queued"


if __name__ == "__main__":
    test_create_task()
