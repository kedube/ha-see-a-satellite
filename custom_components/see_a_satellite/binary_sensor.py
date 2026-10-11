"""Binary sensor for the See A Satellite Tonight integration."""

from typing import Any, override

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import SeeASatelliteConfigEntry, SeeASatelliteCoordinator
from .entity import SeeASatelliteEntity, pass_attributes

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeeASatelliteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensor."""
    async_add_entities([PassInProgressSensor(entry.runtime_data)])


class PassInProgressSensor(SeeASatelliteEntity, BinarySensorEntity):
    """On while a satellite is visible overhead."""

    def __init__(self, coordinator: SeeASatelliteCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, "pass_in_progress")

    @property
    @override
    def is_on(self) -> bool:
        """Return whether a pass is in progress."""
        return self.coordinator.data.current(dt_util.utcnow()) is not None

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details of the pass in progress."""
        return pass_attributes(self.coordinator.data.current(dt_util.utcnow()))
