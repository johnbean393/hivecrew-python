"""System resource for the Hivecrew API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hivecrew.models import SystemConfig, SystemStatus

if TYPE_CHECKING:
    from hivecrew.client import HivecrewClient


class SystemResource:
    """Resource for system information and configuration.

    Provides access to system status, health, and configuration.
    """

    def __init__(self, client: "HivecrewClient") -> None:
        self._client = client

    def status(self) -> SystemStatus:
        """Get the current system status.

        Returns:
            System status including agent counts, VM info, and resources.

        Example:
            >>> status = client.system.status()
            >>> print(f"Status: {status.status}")
            >>> print(f"Running agents: {status.agents.running}/{status.agents.max_concurrent}")
        """
        response = self._client._request("GET", "/system/status")
        return SystemStatus.model_validate(response.json())

    def config(self) -> SystemConfig:
        """Get the current system configuration.

        Returns:
            System configuration settings.

        Example:
            >>> config = client.system.config()
            >>> print(f"Max concurrent VMs: {config.max_concurrent_vms}")
            >>> print(f"Default timeout: {config.default_timeout_minutes} minutes")
        """
        response = self._client._request("GET", "/system/config")
        return SystemConfig.model_validate(response.json())
