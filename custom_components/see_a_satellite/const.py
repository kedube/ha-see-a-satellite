"""Constants for the See A Satellite Tonight integration."""

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "see_a_satellite"
LOGGER = logging.getLogger(__package__)

WEBSITE_URL: Final = "https://james.darpinian.com/satellites/"

CONF_MAX_MAGNITUDE: Final = "max_magnitude"
CONF_CLOUD_COVER: Final = "cloud_cover"

# The website's catalog of the brightest satellites.
CATALOG: Final = "brightest"

DEFAULT_MAX_MAGNITUDE: Final = 3.0

CATALOG_REFRESH: Final = timedelta(hours=12)
PREDICTION_REFRESH: Final = timedelta(hours=2)
# How far ahead the passes_next_24h sensor looks.
UPCOMING_WINDOW: Final = timedelta(hours=24)

ATTRIBUTION: Final = (
    "Predictions by See A Satellite Tonight (james.darpinian.com/satellites), "
    "orbital data from CelesTrak, cloud cover from Open-Meteo"
)
