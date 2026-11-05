"""SolarEdge OAuth implementation details."""

from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation


class SolarEdgeOAuth2Implementation(LocalOAuth2Implementation):
    """Use OAuth 2.0 client-secret basic authentication at the token endpoint."""

    token_auth_method = "client_secret_basic"
