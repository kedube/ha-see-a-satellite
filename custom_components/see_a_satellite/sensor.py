"""Sensors for the See A Satellite Tonight integration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import SatelliteData, SatellitePass, SeeASatelliteConfigEntry
from .entity import SeeASatelliteEntity, pass_attributes, pass_title

PARALLEL_UPDATES = 0


def _next_pass(data: SatelliteData, now: datetime) -> datetime | None:
    p = data.current_or_next(now)
    return p.start if p else None


def _next_pass_attrs(data: SatelliteData, now: datetime) -> dict[str, Any]:
    return pass_attributes(data.current_or_next(now))


def _next_bright(data: SatelliteData, now: datetime) -> datetime | None:
    p = data.current_or_next(now, lambda p: p.bright)
    return p.start if p else None


def _next_bright_attrs(data: SatelliteData, now: datetime) -> dict[str, Any]:
    return pass_attributes(data.current_or_next(now, lambda p: p.bright))


def _upcoming(data: SatelliteData, now: datetime) -> list[SatellitePass]:
    horizon = now + timedelta(hours=24)
    return [p for p in data.passes if p.end > now and p.start < horizon]


def _upcoming_attrs(data: SatelliteData, now: datetime) -> dict[str, Any]:
    return {
        "passes": [
            {
                "start": p.start.isoformat(),
                "satellite": pass_title(p),
                "magnitude": round(p.group.min_magnitude, 1) + 0.0,
                "direction": pass_attributes(p)["rise_direction"],
                "cloud_cover": p.cloud_cover,
            }
            for p in _upcoming(data, now)[:20]
        ]
    }


@dataclass(frozen=True, kw_only=True)
class SeeASatelliteSensorDescription(SensorEntityDescription):
    """Describes a sensor computed from the predicted passes."""

    value_fn: Callable[[SatelliteData, datetime], datetime | int | None]
    attrs_fn: Callable[[SatelliteData, datetime], dict[str, Any]] | None = None


SENSORS: tuple[SeeASatelliteSensorDescription, ...] = (
    SeeASatelliteSensorDescription(
        key="next_pass",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_next_pass,
        attrs_fn=_next_pass_attrs,
    ),
    SeeASatelliteSensorDescription(
        key="next_bright_pass",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_next_bright,
        attrs_fn=_next_bright_attrs,
    ),
    SeeASatelliteSensorDescription(
        key="passes_next_24h",
        value_fn=lambda data, now: len(_upcoming(data, now)),
        attrs_fn=_upcoming_attrs,
    ),
    SeeASatelliteSensorDescription(
        key="catalog_updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data, now: data.catalog_updated,
        attrs_fn=lambda data, now: {"satellites": data.catalog_size},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeeASatelliteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        SeeASatelliteSensor(coordinator, description) for description in SENSORS
    )


class SeeASatelliteSensor(SeeASatelliteEntity, SensorEntity):
    """A sensor derived from the predicted passes."""

    entity_description: SeeASatelliteSensorDescription

    def __init__(
        self, coordinator, description: SeeASatelliteSensorDescription
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    @override
    def native_value(self) -> datetime | int | None:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.data, dt_util.utcnow())

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return details of the pass."""
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data, dt_util.utcnow())
