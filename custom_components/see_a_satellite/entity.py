"""Base entity and pass descriptions for the See A Satellite Tonight integration."""

from typing import Any

from see_a_satellite import LookAngle

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTRIBUTION, DOMAIN, WEBSITE_URL
from .coordinator import SatellitePass, SeeASatelliteCoordinator

_COMPASS = (
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
)  # fmt: skip

# Same "About" links as the website.
_INFO_LINKS = {
    20580: "https://en.wikipedia.org/wiki/Hubble_Space_Telescope",
    25544: "https://en.wikipedia.org/wiki/International_Space_Station",
    41765: "https://en.wikipedia.org/wiki/Tiangong-2",
    41868: "https://en.wikipedia.org/wiki/Shenzhou_11",
    42830: "https://earthsky.org/space/mayak-bright-russian-satellite-july-august-2017",
    43552: "https://brownspace.org/equisat/",
    48274: "https://en.wikipedia.org/wiki/Tiangong_space_station",
    53807: "https://ast-science.com/spacemobile-network/bluewalker-3/",
    59588: "https://www.nasa.gov/mission/acs3/",
}
_INFO_PREFIXES = (
    ("Starlink", "https://en.wikipedia.org/wiki/Starlink"),
    ("SPACEMOBILE", "https://en.wikipedia.org/wiki/AST_SpaceMobile"),
    ("QIANFAN", "https://en.wikipedia.org/wiki/Qianfan"),
    ("HULIANWANG", "https://en.wikipedia.org/wiki/Guowang"),
    ("GUOWANG", "https://en.wikipedia.org/wiki/Guowang"),
    ("ARIANE", "https://en.wikipedia.org/wiki/Ariane_(rocket_family)"),
    ("COSMOS", "https://en.wikipedia.org/wiki/Kosmos_(satellite)"),
    ("CZ-3", "https://en.wikipedia.org/wiki/Long_March_3"),
    ("SL-", "https://en.wikipedia.org/wiki/Zenit_(rocket_family)"),
    ("FALCON 9", "https://en.wikipedia.org/wiki/Falcon_9"),
    ("ATLAS", "https://en.wikipedia.org/wiki/Atlas_(rocket_family)"),
    ("BLOCK DM-SL", "https://en.wikipedia.org/wiki/Blok_D"),
    ("BREEZE-M", "https://en.wikipedia.org/wiki/Briz_(rocket_stage)"),
    ("CZ-", "https://en.wikipedia.org/wiki/Long_March_(rocket_family)"),
    ("TITAN", "https://en.wikipedia.org/wiki/Titan_(rocket_family)"),
    ("H-2", "https://en.wikipedia.org/wiki/H-II"),
)


def info_url(norad_id: int, name: str) -> str:
    """Where to read about a satellite."""
    if norad_id in _INFO_LINKS:
        return _INFO_LINKS[norad_id]
    for prefix, url in _INFO_PREFIXES:
        if name.startswith(prefix):
            return url
    return f"https://heavens-above.com/satinfo.aspx?satid={norad_id}"


def compass(azimuth: float) -> str:
    """16-point compass direction of an azimuth in degrees."""
    return _COMPASS[round(azimuth / 22.5) % 16]


def pass_title(p: SatellitePass) -> str:
    """Short name of a pass, e.g. "ISS" or "Starlink-123 +59"."""
    title = p.group.primary.satellite.name.removesuffix(" prediction")
    if (extra := p.group.satellite_count - 1) > 0:
        title += f" +{extra}"
    return title


def _look(angle: LookAngle) -> str:
    return f"{compass(angle.azimuth)}, {angle.elevation:.0f}° up"


def pass_description(p: SatellitePass) -> str:
    """Human readable instructions for where and when to look."""
    t = p.group.primary
    local = dt_util.as_local
    lines = [
        f"Appears at {local(t.start):%H:%M:%S} in the {_look(t.rise)}.",
        f"Brightest at {local(t.brightest_time):%H:%M:%S} in the {_look(t.brightest)}"
        f" (magnitude {t.min_magnitude:.1f}).",
        f"Disappears at {local(t.end):%H:%M:%S} in the {_look(t.set)}.",
    ]
    if p.group.satellite_count > 1:
        lines.append(f"{p.group.satellite_count} satellites pass together.")
    if p.cloud_cover is not None:
        lines.append(f"Forecast cloud cover: {p.cloud_cover}%.")
    lines.append(
        f"About {t.satellite.name}: {info_url(t.satellite.norad_id, t.satellite.name)}"
    )
    return "\n".join(lines)


def pass_attributes(p: SatellitePass | None) -> dict[str, Any]:
    """State attributes describing a pass."""
    if p is None:
        return {}
    t = p.group.primary
    attrs: dict[str, Any] = {
        "satellite": t.satellite.name,
        "norad_id": t.satellite.norad_id,
        "start": t.start.isoformat(),
        "end": p.end.isoformat(),
        "duration": round((p.end - p.start).total_seconds()),
        "magnitude": round(p.group.min_magnitude, 1) + 0.0,  # no -0.0
        "bright": p.bright,
        "before_sunset": p.group.before_sunset,
        "rise_direction": compass(t.rise.azimuth),
        "rise_azimuth": t.rise.azimuth,
        "rise_elevation": t.rise.elevation,
        "brightest_time": t.brightest_time.isoformat(),
        "brightest_direction": compass(t.brightest.azimuth),
        "brightest_azimuth": t.brightest.azimuth,
        "brightest_elevation": t.brightest.elevation,
        "set_direction": compass(t.set.azimuth),
        "set_azimuth": t.set.azimuth,
        "set_elevation": t.set.elevation,
        "cloud_cover": p.cloud_cover,
        "satellite_count": p.group.satellite_count,
        "info_url": info_url(t.satellite.norad_id, t.satellite.name),
    }
    if len(p.group.transits) > 1:
        attrs["satellites"] = [x.satellite.name for x in p.group.transits[:20]]
    return attrs


class SeeASatelliteEntity(CoordinatorEntity[SeeASatelliteCoordinator]):
    """Common device and naming for all entities of a location."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: SeeASatelliteCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="James Darpinian",
            model="See A Satellite Tonight",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=(
                f"{WEBSITE_URL}#loc={coordinator.latitude:.4f},{coordinator.longitude:.4f}"
            ),
        )
