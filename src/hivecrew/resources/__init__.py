"""Hivecrew API resources."""

from hivecrew.resources.providers import ProvidersResource
from hivecrew.resources.schedules import SchedulesResource
from hivecrew.resources.system import SystemResource
from hivecrew.resources.tasks import TasksResource
from hivecrew.resources.templates import TemplatesResource

__all__ = [
    "TasksResource",
    "SchedulesResource",
    "ProvidersResource",
    "TemplatesResource",
    "SystemResource",
]
