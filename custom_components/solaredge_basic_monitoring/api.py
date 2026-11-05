"""Async client for SolarEdge's OAuth-protected Monitoring API v2."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aiohttp import ClientError
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import API_BASE_URL


class SolarEdgeApiError(Exception):
    """Raised when SolarEdge returns an API or transport error."""


class SolarEdgeApi:
    """Client for site, device, and measurement resources."""

    def __init__(self, session: OAuth2Session, site_id: str) -> None:
        self._session = session
        self._site_id = site_id

    async def async_request(self, path: str, **params: Any) -> Any:
        """Make an authenticated API request and return decoded JSON."""
        url = f"{API_BASE_URL}/{path.lstrip('/')}"
        try:
            async with await self._session.async_request(
                "GET", url, params=params or None
            ) as response:
                if response.status == 429:
                    raise SolarEdgeApiError(
                        "SolarEdge API-verzoeklimiet bereikt (HTTP 429)."
                    )
                if response.status in (401, 403):
                    raise SolarEdgeApiError(
                        "SolarEdge heeft de OAuth-toegang geweigerd. Controleer de app-rechten en site-toestemming."
                    )
                if response.status == 404:
                    raise SolarEdgeApiError(
                        "Site of API-eindpunt niet gevonden. Controleer het site-ID en de API-rechten."
                    )
                if response.status >= 400:
                    body = (await response.text())[:300]
                    raise SolarEdgeApiError(
                        f"SolarEdge API antwoordde met HTTP {response.status}: {body}"
                    )
                return await response.json(content_type=None)
        except ClientError:
            # Never include request details in errors; they can contain credentials.
            raise SolarEdgeApiError("Verbinding met SolarEdge mislukt.") from None

    async def async_validate(self) -> dict[str, Any]:
        """Validate access by retrieving the selected site."""
        result = await self.async_request(f"sites/{self._site_id}")
        if not isinstance(result, dict) or not result:
            raise SolarEdgeApiError("SolarEdge retourneerde geen sitegegevens.")
        return result

    async def async_fetch_site_data(self) -> dict[str, Any]:
        """Fetch site, device, and measurement resources for this site."""
        now = datetime.now(timezone.utc)
        end_time = now.isoformat(timespec="seconds")
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(
            timespec="seconds"
        )
        requests: dict[str, tuple[str, dict[str, Any]]] = {
            "site": (f"sites/{self._site_id}", {}),
            "overview": (f"sites/{self._site_id}/overview", {}),
            "devices": (f"sites/{self._site_id}/devices", {}),
            "measurements": (
                f"sites/{self._site_id}/measurements",
                {"startTime": start_time, "endTime": end_time},
            ),
            "energy": (
                f"sites/{self._site_id}/energy",
                {"startTime": start_time, "endTime": end_time},
            ),
            "power": (
                f"sites/{self._site_id}/power",
                {"startTime": start_time, "endTime": end_time},
            ),
        }
        data: dict[str, Any] = {}
        for name, (path, params) in requests.items():
            try:
                data[name] = await self.async_request(path, **params)
            except SolarEdgeApiError as err:
                # Site access is required; fail setup instead of creating only
                # error sensors when the OAuth grant or site ID is invalid.
                if name == "site":
                    raise
                # Other resources can depend on the granted scopes and site plan.
                data[name] = {"error": str(err)}
        return data
