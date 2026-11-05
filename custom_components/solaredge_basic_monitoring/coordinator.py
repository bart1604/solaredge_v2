"""Data update coordinator for SolarEdge."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_register_implementation,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolarEdgeApi, SolarEdgeApiError
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_SITE_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OAUTH_AUTHORIZE_URL,
    OAUTH_TOKEN_URL,
)
from .oauth import SolarEdgeOAuth2Implementation

_LOGGER = logging.getLogger(__name__)


class SolarEdgeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch site data from SolarEdge on a fixed schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        implementation = SolarEdgeOAuth2Implementation(
            hass,
            entry.data["auth_implementation"],
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            OAUTH_AUTHORIZE_URL,
            OAUTH_TOKEN_URL,
        )
        async_register_implementation(hass, DOMAIN, implementation)
        self.api = SolarEdgeApi(
            OAuth2Session(hass, entry, implementation), entry.data[CONF_SITE_ID]
        )
        self.site_name = f"SolarEdge site {entry.data[CONF_SITE_ID]}"
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Retrieve site, device, and measurement resources."""
        try:
            data = await self.api.async_fetch_site_data()
        except SolarEdgeApiError as err:
            raise UpdateFailed(str(err)) from err

        site = data.get("site", {})
        if isinstance(site, dict):
            self.site_name = site.get("name") or self.site_name
        return data
