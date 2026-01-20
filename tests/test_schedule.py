"""Test script for the schedules endpoint."""

from datetime import datetime, timedelta, timezone

from hivecrew import HivecrewClient, ScheduleConfig


def test_create_scheduled_task():
    """Test creating a scheduled task."""
    client = HivecrewClient()

    # Schedule the task for 1 hour from now
    scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1)

    scheduled_task = client.schedules.create(
        title="Daily Backup Check",
        description="Check that all backups completed successfully",
        provider_name="OpenRouter",
        model_id="anthropic/claude-sonnet-4.5",
        schedule=ScheduleConfig(
            scheduled_at=scheduled_time,
        ),
    )

    print(f"Scheduled task created: {scheduled_task.id}")
    print(f"Title: {scheduled_task.title}")
    print(f"Next run at: {scheduled_task.next_run_at}")
    assert scheduled_task.id is not None
    assert scheduled_task.is_enabled is True


if __name__ == "__main__":
    test_create_scheduled_task()
