"""Sensors exposing every scalar value returned by SolarEdge endpoints."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SITE_ID, DOMAIN
from .coordinator import SolarEdgeDataUpdateCoordinator


def _flatten(value: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    """Yield every scalar in a nested JSON response with a stable path."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from _flatten(child, child_path)
    elif isinstance(value, list):
        # Time-series endpoints can return hundreds of rows. A HA sensor should
        # represent the latest observation of each field, not create an entity
        # for each historical sample (which would grow without bound).
        if value:
            yield from _flatten(value[-1], f"{path}.latest" if path else "latest")
    elif value is not None and isinstance(value, (str, int, float, bool)):
        yield path, value


def _unit_for_path(payload: Any, path: str) -> str | None:
    """Find the closest SolarEdge `unit` field enclosing a response value."""
    unit: Any = None
    current = payload
    for part in path.split("."):
        if isinstance(current, dict):
            if isinstance(current.get("unit"), str):
                unit = current["unit"]
            current = current.get(part)
        elif isinstance(current, list) and part == "latest" and current:
            current = current[-1]
        else:
            return unit
    if isinstance(current, dict) and isinstance(current.get("unit"), str):
        unit = current["unit"]
    return unit if isinstance(unit, str) else None


def _entity_id(endpoint: str, path: str) -> str:
    """Build a stable entity unique ID from an endpoint and JSON path."""
    slug = re.sub(r"[^a-z0-9]+", "_", f"{endpoint}_{path}".lower()).strip("_")
    return slug[:180]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up dynamically discovered SolarEdge scalar sensors."""
    coordinator: SolarEdgeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_ids: set[str] = set()

    @callback
    def _add_new_sensors() -> None:
        new_entities: list[SolarEdgeValueSensor] = []
        for endpoint, payload in (coordinator.data or {}).items():
            for path, _value in _flatten(payload):
                unique_id = _entity_id(endpoint, path)
                if unique_id not in known_ids:
                    known_ids.add(unique_id)
                    new_entities.append(
                        SolarEdgeValueSensor(coordinator, entry, endpoint, path, unique_id)
                    )
        if new_entities:
            async_add_entities(new_entities)

    _add_new_sensors()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_sensors))


class SolarEdgeValueSensor(CoordinatorEntity[SolarEdgeDataUpdateCoordinator], SensorEntity):
    """A sensor representing one scalar field in an API response."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarEdgeDataUpdateCoordinator,
        entry: ConfigEntry,
        endpoint: str,
        path: str,
        unique_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._path = path
        self._attr_unique_id = f"{entry.data[CONF_SITE_ID]}_{unique_id}"
        self._attr_name = f"{endpoint.replace('_', ' ').title()} · {path.replace('.', ' · ')}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_SITE_ID])},
            name=coordinator.site_name,
            manufacturer="SolarEdge",
            model="Monitoring API",
            configuration_url="https://monitoring.solaredge.com/",
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return a unit when the response provides one near this field."""
        payload = (self.coordinator.data or {}).get(self._endpoint, {})
        return _unit_for_path(payload, self._path)

    @property
    def native_value(self) -> Any:
        """Return the latest value for this response field."""
        payload = (self.coordinator.data or {}).get(self._endpoint, {})
        for path, value in _flatten(payload):
            if path == self._path:
                # HA states have a 255-character limit.
                if isinstance(value, str) and len(value) > 250:
                    return value[:247] + "..."
                return "On" if value is True else "Off" if value is False else value
        return None
