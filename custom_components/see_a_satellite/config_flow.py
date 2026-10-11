"""Config flow for the See A Satellite Tonight integration."""

import logging
from typing import Any, override

from see_a_satellite import CatalogError, fetch_site_catalog
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.const import (
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    UnitOfLength,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    LocationSelector,
    LocationSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CATALOG_BRIGHTEST,
    CATALOG_STARLINK,
    CATALOGS,
    CONF_CATALOG,
    CONF_CLOUD_COVER,
    CONF_MAX_MAGNITUDE,
    DEFAULT_MAX_MAGNITUDE,
    DOMAIN,
)
from .coordinator import SeeASatelliteConfigEntry

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LOCATION): LocationSelector(
            LocationSelectorConfig(radius=False)
        ),
        vol.Required(CONF_ELEVATION): NumberSelector(
            NumberSelectorConfig(
                min=-500,
                max=9000,
                step=1,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement=UnitOfLength.METERS,
            )
        ),
        vol.Required(CONF_CATALOG): SelectSelector(
            SelectSelectorConfig(
                options=CATALOGS,
                mode=SelectSelectorMode.LIST,
                translation_key=CONF_CATALOG,
            )
        ),
    }
)
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MAX_MAGNITUDE): NumberSelector(
            NumberSelectorConfig(
                min=-2, max=4, step=0.5, mode=NumberSelectorMode.SLIDER
            )
        ),
        vol.Required(CONF_CLOUD_COVER): BooleanSelector(),
    }
)


class SeeASatelliteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up predictions for a location."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the location and catalog."""
        errors: dict[str, str] = {}
        if user_input is not None:
            latitude = user_input[CONF_LOCATION][CONF_LATITUDE]
            longitude = user_input[CONF_LOCATION][CONF_LONGITUDE]
            catalog = user_input[CONF_CATALOG]
            await self.async_set_unique_id(f"{latitude:.4f}_{longitude:.4f}_{catalog}")
            self._abort_if_unique_id_configured()
            try:
                await fetch_site_catalog(async_get_clientsession(self.hass), catalog)
            except CatalogError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=self._title(latitude, longitude, catalog),
                    data={
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                        CONF_ELEVATION: user_input[CONF_ELEVATION],
                        CONF_CATALOG: catalog,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                USER_SCHEMA,
                user_input
                or {
                    CONF_LOCATION: {
                        CONF_LATITUDE: self.hass.config.latitude,
                        CONF_LONGITUDE: self.hass.config.longitude,
                    },
                    CONF_ELEVATION: self.hass.config.elevation,
                    CONF_CATALOG: CATALOG_BRIGHTEST,
                },
            ),
            errors=errors,
        )

    def _title(self, latitude: float, longitude: float, catalog: str) -> str:
        """Name the location after the home, or by its coordinates."""
        if (
            abs(latitude - self.hass.config.latitude) < 1e-4
            and abs(longitude - self.hass.config.longitude) < 1e-4
        ):
            title = self.hass.config.location_name
        else:
            title = f"{latitude:.4f}, {longitude:.4f}"
        if catalog == CATALOG_STARLINK:
            title += " Starlink"
        return title

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: SeeASatelliteConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return SeeASatelliteOptionsFlow()


class SeeASatelliteOptionsFlow(OptionsFlowWithReload):
    """Tune which passes are reported."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                {
                    CONF_MAX_MAGNITUDE: DEFAULT_MAX_MAGNITUDE,
                    CONF_CLOUD_COVER: True,
                    **self.config_entry.options,
                },
            ),
        )
