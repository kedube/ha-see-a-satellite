"""Calendar of visible satellite passes."""

from datetime import datetime
from typing import override

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import (
    SatellitePass,
    SeeASatelliteConfigEntry,
    SeeASatelliteCoordinator,
)
from .entity import SeeASatelliteEntity, pass_description, pass_title

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeeASatelliteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the calendar."""
    async_add_entities([SatellitePassCalendar(entry.runtime_data)])


def _event(p: SatellitePass) -> CalendarEvent:
    summary = f"🛰️ {pass_title(p)}"
    if p.bright:
        summary += " (bright)"
    return CalendarEvent(
        start=p.start,
        end=p.end,
        summary=summary,
        description=pass_description(p),
        uid=f"{p.group.primary.satellite.norad_id}-{int(p.start.timestamp())}",
    )


class SatellitePassCalendar(SeeASatelliteEntity, CalendarEntity):
    """Every predicted visible pass for the next five days."""

    def __init__(self, coordinator: SeeASatelliteCoordinator) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator, "passes")

    @property
    @override
    def event(self) -> CalendarEvent | None:
        """The pass in progress or the next one."""
        p = self.coordinator.data.current_or_next(dt_util.utcnow())
        return _event(p) if p else None

    @override
    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Passes overlapping the requested range."""
        return [
            _event(p)
            for p in self.coordinator.data.passes
            if p.end > start_date and p.start < end_date
        ]
