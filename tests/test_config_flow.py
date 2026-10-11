"""Tests for the See A Satellite Tonight config flow."""

from unittest.mock import AsyncMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from see_a_satellite import CatalogError

from custom_components.see_a_satellite.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

USER_INPUT = {
    "location": {"latitude": 52.0277, "longitude": 5.5583},
    "elevation": 10,
}


@pytest.mark.usefixtures("mock_setup_entry")
async def test_user_flow(
    hass: HomeAssistant, mock_see_a_satellite: dict[str, AsyncMock]
) -> None:
    """A location is set up once the catalog is reachable."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "52.0277, 5.5583"
    assert result["data"] == {
        "latitude": 52.0277,
        "longitude": 5.5583,
        "elevation": 10,
    }
    assert result["result"].unique_id == "52.0277_5.5583"
    mock_see_a_satellite["fetch_site_catalog"].assert_awaited_once()


@pytest.mark.usefixtures("mock_setup_entry")
@pytest.mark.parametrize(
    ("side_effect", "error"),
    [(CatalogError("boom"), "cannot_connect"), (RuntimeError("boom"), "unknown")],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_see_a_satellite: dict[str, AsyncMock],
    side_effect: Exception,
    error: str,
) -> None:
    """Errors are shown and the form can be resubmitted."""
    mock_see_a_satellite["fetch_site_catalog"].side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_see_a_satellite["fetch_site_catalog"].side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("mock_setup_entry", "mock_see_a_satellite")
async def test_title_of_home(hass: HomeAssistant) -> None:
    """The home location is named after the home."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "location": {
                "latitude": hass.config.latitude,
                "longitude": hass.config.longitude,
            },
            "elevation": 0,
        },
    )
    assert result["title"] == "test home"


async def test_duplicate_location(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The same location can only be added once."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_options_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Options are stored on the entry."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"max_magnitude": 1.5, "cloud_cover": False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {"max_magnitude": 1.5, "cloud_cover": False}
