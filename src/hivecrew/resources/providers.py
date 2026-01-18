"""Providers resource for the Hivecrew API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hivecrew.models import ModelList, Provider, ProviderList

if TYPE_CHECKING:
    from hivecrew.client import HivecrewClient


class ProvidersResource:
    """Resource for managing AI providers.

    Providers are AI service configurations (e.g., OpenRouter, Anthropic).
    """

    def __init__(self, client: "HivecrewClient") -> None:
        self._client = client

    def list(self) -> ProviderList:
        """List all configured AI providers.

        Returns:
            List of providers.

        Example:
            >>> providers = client.providers.list()
            >>> for p in providers.providers:
            ...     print(f"{p.display_name}: {'default' if p.is_default else ''}")
        """
        response = self._client._request("GET", "/providers")
        return ProviderList.model_validate(response.json())

    def get(self, provider_id: str) -> Provider:
        """Get details of a specific provider.

        Args:
            provider_id: The provider ID.

        Returns:
            The provider details.

        Example:
            >>> provider = client.providers.get("provider-123")
            >>> print(provider.display_name)
        """
        response = self._client._request("GET", f"/providers/{provider_id}")
        return Provider.model_validate(response.json())

    def list_models(self, provider_id: str) -> ModelList:
        """List available models for a provider.

        Args:
            provider_id: The provider ID.

        Returns:
            List of available models.

        Example:
            >>> models = client.providers.list_models("provider-123")
            >>> for m in models.models:
            ...     print(f"{m.id}: {m.context_length} tokens")
        """
        response = self._client._request("GET", f"/providers/{provider_id}/models")
        return ModelList.model_validate(response.json())
