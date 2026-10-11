"""The See A Satellite Tonight integration.

Predicts when satellites are visible to the naked eye from a location, the way
https://james.darpinian.com/satellites/ does.
"""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SeeASatelliteConfigEntry, SeeASatelliteCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: SeeASatelliteConfigEntry
) -> bool:
    """Set up See A Satellite Tonight from a config entry."""
    coordinator = SeeASatelliteCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SeeASatelliteConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
