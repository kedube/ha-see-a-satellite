# See A Satellite Tonight for Home Assistant

A Home Assistant integration that predicts when satellites are visible to the
naked eye from your location. It is a port of James Darpinian's
[See A Satellite Tonight](https://james.darpinian.com/satellites/), made with
his permission. It uses the same satellite catalog and the same brightness and
visibility model, so it predicts the same passes as the website.

The satellite catalog (orbits, brightness values and models) is collected and
curated by the website. This integration downloads it a few times a day, keeps
a copy across restarts, and predicts the passes locally with the
[`see-a-satellite`](https://github.com/wildekek/see-a-satellite) library.

## Install

With [HACS](https://hacs.xyz): **HACS → ⋮ → Custom repositories**, add
`https://github.com/wildekek/ha-see-a-satellite` as an *Integration*, install
**See A Satellite Tonight**, and restart Home Assistant.

Manually: copy `custom_components/see_a_satellite` into your Home Assistant
config directory as `config/custom_components/see_a_satellite`, then restart.

Then go to **Settings → Devices & services → Add integration → See A Satellite
Tonight**. The defaults are your home location and elevation. Add the
integration again for more locations, or pick the *Starlink trains* catalog.

## Entities (per location)

| Entity | Description |
|---|---|
| `sensor.<name>_next_pass` | Start of the current or next pass. Attributes give the satellite, magnitude, rise/brightest/set direction and elevation, cloud cover, and an info link |
| `sensor.<name>_next_bright_pass` | Same, limited to passes the site labels **bright** |
| `sensor.<name>_passes_next_24_hours` | Count of passes in the next 24 hours, with a summary list |
| `binary_sensor.<name>_satellite_visible` | On while a pass is in progress |
| `calendar.<name>_satellite_passes` | Every pass of the next 5 days, with where-to-look instructions |
| `sensor.<name>_catalog_updated` | Diagnostic: when the orbital elements were last downloaded |

Options: the faintest magnitude to report (default 3, as on the site) and
whether to include the Open-Meteo cloud cover forecast.

Example automation trigger, 10 minutes before a bright pass:

```yaml
triggers:
  - trigger: calendar
    event: start
    offset: "-0:10:0"
    entity_id: calendar.home_satellite_passes
conditions:
  - condition: template
    value_template: "{{ 'bright' in trigger.calendar_event.summary }}"
```

## How it works

The `see-a-satellite` library is a Python port of the website's workers:
SGP4 propagation at one-minute steps, the site's brightness, extinction,
limiting-magnitude and Earth-shadow models, one-second refinement, and the
site's grouping and "bright" label. For Veenendaal over 5 days it reproduces
all 73 of the site's passes: start times within 9 s, end times within 19 s,
magnitudes within 0.03.

A full 5-day prediction for about 860 satellites takes about 3 s on a laptop,
so expect tens of seconds on a Raspberry Pi. It runs in an executor every 2
hours; the catalog is refreshed every 12 hours and shared by all locations.

## Development

```sh
python3 -m venv .venv && .venv/bin/pip install pytest-homeassistant-custom-component ruff see-a-satellite
.venv/bin/pytest
.venv/bin/ruff check custom_components tests
```

## Credits

Predictions, catalog and models: [See A Satellite Tonight](https://james.darpinian.com/satellites/)
by James Darpinian, ported with his permission. Cloud cover:
[Open-Meteo](https://open-meteo.com).
