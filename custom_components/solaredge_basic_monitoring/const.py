"""Constants for the SolarEdge Basic Monitoring integration."""

from datetime import timedelta

DOMAIN = "solaredge_basic_monitoring"
NAME = "SolarEdge Basic Monitoring"
DEFAULT_SCAN_INTERVAL = timedelta(hours=1)
CONF_SITE_ID = "site_id"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
API_BASE_URL = "https://monitoringapi.solaredge.com/v2"
OAUTH_AUTHORIZE_URL = f"{API_BASE_URL}/authorize"
OAUTH_TOKEN_URL = f"{API_BASE_URL}/token"
PLATFORMS = ["sensor"]
