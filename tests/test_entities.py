"""Tests for the See A Satellite Tonight entities."""

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed

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
    state = hass.states.get("sensor.veenendaal_next_pass")
    assert state.state == "2026-10-10T19:08:40+00:00"
    attrs = state.attributes
    assert attrs["satellite"] == "BlueWalker 3"
    assert attrs["norad_id"] == 53807
    assert attrs["magnitude"] == 0.4
    assert attrs["bright"] is True
    assert attrs["rise_direction"] == "WNW"
    assert attrs["cloud_cover"] == 20  # the first forecast hour after the start
    assert attrs["info_url"].startswith("https://ast-science.com/")

    assert hass.states.get("sensor.veenendaal_next_bright_pass").state == (
        "2026-10-10T19:08:40+00:00"
    )
    passes = hass.states.get("sensor.veenendaal_passes_next_24_hours")
    assert int(passes.state) == len(passes.attributes["passes"]) > 0
    catalog = hass.states.get("sensor.veenendaal_catalog_updated")
    assert catalog.attributes["satellites"] == 22


async def test_pass_in_progress(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The binary sensor follows the pass without polling."""
    visible = "binary_sensor.veenendaal_satellite_visible"
    assert hass.states.get(visible).state == STATE_OFF

    freezer.move_to(datetime(2026, 10, 10, 19, 8, 42, tzinfo=UTC))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(visible)
    assert state.state == STATE_ON
    assert state.attributes["satellite"] == "BlueWalker 3"
    # While in progress, the "next pass" is still this one.
    assert hass.states.get("sensor.veenendaal_next_pass").state == (
        "2026-10-10T19:08:40+00:00"
    )

    freezer.move_to(datetime(2026, 10, 10, 19, 9, 46, tzinfo=UTC))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(visible).state == STATE_OFF
    assert (
        hass.states.get("sensor.veenendaal_next_pass").state
        > "2026-10-10T19:09:44+00:00"
    )


async def test_calendar(hass: HomeAssistant) -> None:
    """Every pass of the next days is a calendar event."""
    response = await hass.services.async_call(
        CALENDAR_DOMAIN,
        SERVICE_GET_EVENTS,
        {
            "entity_id": "calendar.veenendaal_satellite_passes",
            "start_date_time": NOW,
            "end_date_time": NOW + timedelta(days=5),
        },
        blocking=True,
        return_response=True,
    )
    events = response["calendar.veenendaal_satellite_passes"]["events"]
    assert len(events) >= 60
    assert events[0]["summary"] == "🛰️ BlueWalker 3 (bright)"
    assert "Appears at" in events[0]["description"]
    assert "Forecast cloud cover: 20%" in events[0]["description"]

    state = hass.states.get("calendar.veenendaal_satellite_passes")
    assert state.state == STATE_OFF
    assert state.attributes["message"] == "🛰️ BlueWalker 3 (bright)"
