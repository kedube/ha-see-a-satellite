"""Fixtures for the See A Satellite Tonight tests."""

from collections.abc import Generator
from datetime import UTC, datetime
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from see_a_satellite import Satellite, parse_site_catalog

from custom_components.see_a_satellite.const import DOMAIN
from homeassistant.core import HomeAssistant

# The fixture catalog's satellites pass the test location from 19:08:36 UTC.
NOW = datetime(2026, 10, 10, 19, 5, tzinfo=UTC)


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load the integration from custom_components."""


@pytest.fixture
def satellites() -> list[Satellite]:
    """Satellites of the website's catalog that pass during the tests."""
    return parse_site_catalog(
        json.loads((FIXTURES / "brightest-sats.json").read_text())
    )


@pytest.fixture
def cloud_cover() -> list[tuple[datetime, int]]:
    """Hourly cloud cover, equal to the hour of the week."""
    start = datetime(2026, 10, 10, tzinfo=UTC).timestamp()
    return [
        (datetime.fromtimestamp(start + 3600 * i, UTC), i % 100) for i in range(168)
    ]


@pytest.fixture
def mock_see_a_satellite(
    satellites: list[Satellite], cloud_cover: list[tuple[datetime, int]]
) -> Generator[dict[str, AsyncMock]]:
    """Mock the library's network calls."""
    with (
        patch(
            "custom_components.see_a_satellite.coordinator.fetch_site_catalog",
            return_value=satellites,
        ) as fetch_site_catalog,
        patch(
            "custom_components.see_a_satellite.config_flow.fetch_site_catalog",
            new=fetch_site_catalog,
        ),
        patch(
            "custom_components.see_a_satellite.coordinator.fetch_cloud_cover",
            return_value=cloud_cover,
        ) as fetch_cloud_cover,
    ):
        yield {
            "fetch_site_catalog": fetch_site_catalog,
            "fetch_cloud_cover": fetch_cloud_cover,
        }


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "custom_components.see_a_satellite.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """A test location: the Dom Tower in Utrecht."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id="52.0907_5.1214",
        minor_version=2,
        data={"latitude": 52.0907, "longitude": 5.1214, "elevation": 5},
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    mock_see_a_satellite: dict[str, AsyncMock],
) -> MockConfigEntry:
    """Set up the integration at a fixed time."""
    freezer.move_to(NOW)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
