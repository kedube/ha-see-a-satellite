"""Tests for the See A Satellite Tonight entities."""

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from homeassistant.components.calendar import (
    DOMAIN as CALENDAR_DOMAIN,
    SERVICE_GET_EVENTS,
)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from .conftest import NOW

pytestmark = pytest.mark.usefixtures("init_integration")


async def test_next_pass(hass: HomeAssistant) -> None:
    """The next pass is the website's first one, with where to look."""
    state = hass.states.get("sensor.home_next_pass")
    assert state.state == "2026-10-10T19:08:36+00:00"
    attrs = state.attributes
    assert attrs["satellite"] == "BlueWalker 3"
    assert attrs["norad_id"] == 53807
    assert attrs["magnitude"] == 0.3
    assert attrs["bright"] is True
    assert attrs["rise_direction"] == "WNW"
    assert attrs["cloud_cover"] == 20  # the first forecast hour after the start
    assert attrs["info_url"].startswith("https://ast-science.com/")

    assert hass.states.get("sensor.home_next_bright_pass").state == (
        "2026-10-10T19:08:36+00:00"
    )
    passes = hass.states.get("sensor.home_passes_next_24_hours")
    assert int(passes.state) == len(passes.attributes["passes"]) > 0
    catalog = hass.states.get("sensor.home_catalog_updated")
    assert catalog.attributes["satellites"] == 22


async def test_pass_in_progress(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The binary sensor follows the pass without polling."""
    visible = "binary_sensor.home_satellite_visible"
    assert hass.states.get(visible).state == STATE_OFF

    freezer.move_to(datetime(2026, 10, 10, 19, 8, 42, tzinfo=UTC))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(visible)
    assert state.state == STATE_ON
    assert state.attributes["satellite"] == "BlueWalker 3"
    # While in progress, the "next pass" is still this one.
    assert hass.states.get("sensor.home_next_pass").state == (
        "2026-10-10T19:08:36+00:00"
    )

    freezer.move_to(datetime(2026, 10, 10, 19, 9, 46, tzinfo=UTC))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(visible).state == STATE_OFF
    assert hass.states.get("sensor.home_next_pass").state > "2026-10-10T19:09:44+00:00"


async def test_passes_next_24h_follow_the_window(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    init_integration: MockConfigEntry,
) -> None:
    """A pass is counted as soon as it is less than 24 hours away."""
    now = datetime(2026, 10, 11, 3, 50, tzinfo=UTC)
    freezer.move_to(now)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    sensor = "sensor.home_passes_next_24_hours"
    before = int(hass.states.get(sensor).state)

    passes = init_integration.runtime_data.data.passes
    later = next(p for p in passes if p.start > now + timedelta(hours=24))
    # No pass starts or ends and no refresh is due before it comes into view.
    assert all(
        p.start > later.start - timedelta(hours=24) for p in passes if p.end > now
    )
    assert later.start - timedelta(hours=24) < now + timedelta(hours=2)
    freezer.move_to(later.start - timedelta(hours=24) + timedelta(seconds=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(sensor)
    assert int(state.state) == before + 1
    assert state.attributes["passes"][-1]["start"] == later.start.isoformat()


async def test_calendar(hass: HomeAssistant) -> None:
    """Every pass of the next days is a calendar event."""
    response = await hass.services.async_call(
        CALENDAR_DOMAIN,
        SERVICE_GET_EVENTS,
        {
            "entity_id": "calendar.home_satellite_passes",
            "start_date_time": NOW,
            "end_date_time": NOW + timedelta(days=5),
        },
        blocking=True,
        return_response=True,
    )
    events = response["calendar.home_satellite_passes"]["events"]
    assert len(events) >= 60
    assert events[0]["summary"] == "🛰️ BlueWalker 3 (bright)"
    assert "Appears at" in events[0]["description"]
    assert "Forecast cloud cover: 20%" in events[0]["description"]

    state = hass.states.get("calendar.home_satellite_passes")
    assert state.state == STATE_OFF
    assert state.attributes["message"] == "🛰️ BlueWalker 3 (bright)"
