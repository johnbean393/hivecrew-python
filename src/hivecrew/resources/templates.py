"""Templates resource for the Hivecrew API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hivecrew.models import Template, TemplateList

if TYPE_CHECKING:
    from hivecrew.client import HivecrewClient


class TemplatesResource:
    """Resource for managing VM templates.

    Templates are pre-configured macOS VM images used to run agent tasks.
    """

    def __init__(self, client: "HivecrewClient") -> None:
        self._client = client

    def list(self) -> TemplateList:
        """List all available VM templates.

        Returns:
            List of templates with the default template ID.

        Example:
            >>> templates = client.templates.list()
            >>> print(f"Default: {templates.default_template_id}")
            >>> for t in templates.templates:
            ...     print(f"{t.name}: {t.description}")
        """
        response = self._client._request("GET", "/templates")
        return TemplateList.model_validate(response.json())

    def get(self, template_id: str) -> Template:
        """Get details of a specific template.

        Args:
            template_id: The template ID.

        Returns:
            The template details.

        Example:
            >>> template = client.templates.get("golden-v3")
            >>> print(f"{template.name}: {template.cpu_count} CPUs")
        """
        response = self._client._request("GET", f"/templates/{template_id}")
        return Template.model_validate(response.json())
