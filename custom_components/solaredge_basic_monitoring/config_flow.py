"""OAuth2 config flow for SolarEdge Basic Monitoring."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2FlowHandler,
    async_register_implementation,
)

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_SITE_ID,
    DOMAIN,
    OAUTH_AUTHORIZE_URL,
    OAUTH_TOKEN_URL,
)
from .oauth import SolarEdgeOAuth2Implementation

_LOGGER = logging.getLogger(__name__)


class SolarEdgeConfigFlow(OAuth2FlowHandler, domain=DOMAIN):
    """Handle SolarEdge's OAuth authorization-code flow."""

    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._site_id: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return the integration logger used by the shared OAuth flow."""
        return _LOGGER

    async def async_step_user(self, user_input: dict[str, str] | None = None):
        """Collect site and application credentials, then start OAuth."""
        if user_input is not None:
            self._site_id = user_input[CONF_SITE_ID].strip()
            self._client_id = user_input[CONF_CLIENT_ID].strip()
            self._client_secret = user_input[CONF_CLIENT_SECRET]
            await self.async_set_unique_id(self._site_id)
            self._abort_if_unique_id_configured()

            implementation_id = f"{DOMAIN}_{self.flow_id}"
            self.flow_impl = SolarEdgeOAuth2Implementation(
                self.hass,
                implementation_id,
                self._client_id,
                self._client_secret,
                OAUTH_AUTHORIZE_URL,
                OAUTH_TOKEN_URL,
            )
            async_register_implementation(self.hass, DOMAIN, self.flow_impl)
            return await self.async_step_auth()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SITE_ID): str,
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
        )

    async def async_oauth_create_entry(self, data: dict):
        """Persist OAuth tokens, credentials, and selected site."""
        assert self._site_id is not None
        assert self._client_id is not None
        assert self._client_secret is not None
        return self.async_create_entry(
            title=f"SolarEdge site {self._site_id}",
            data={
                CONF_SITE_ID: self._site_id,
                CONF_CLIENT_ID: self._client_id,
                CONF_CLIENT_SECRET: self._client_secret,
                "auth_implementation": self.flow_impl.domain,
                "token": data["token"],
            },
        )
