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
integration again for more locations.

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

### Full example: announce bright passes on a speaker

This automation runs 10 minutes before a bright pass, but only when a light in
the gazebo is on. It reads the calendar event and announces the pass in plain
language: what the object is, where to look, how high and how bright it is,
how long it stays visible, and what the clouds will be like. It uses Music
Assistant with Piper TTS; you can use `tts.speak` with any media player
instead. Replace the calendar, area, speaker and TTS entities with your own.

```yaml
alias: See A Satellite Tonight
description: >-
  10 minutes before a bright satellite pass, announce it on the gazebo
  speakers in plain language, only when a gazebo light is on.
mode: single
triggers:
  - trigger: calendar
    event: start
    offset: "-0:10:0"
    entity_id: calendar.home_satellite_passes
conditions:
  # Stands in for "someone is in the gazebo".
  - condition: light.is_on
    target:
      area_id: gazebo
    options:
      behavior: any
      for: "00:00:00"
  - alias: Bright satellite
    condition: template
    value_template: "{{ 'bright' in trigger.calendar_event.summary }}"
actions:
  # Builds the message from the event: the kind of object instead of its
  # catalog name, 12-hour times, sky height in words instead of degrees, and
  # advice on brightness and cloud cover. Falls back to a short message if the
  # description format changes.
  - variables:
      message: |-
        {%- set ev = trigger.calendar_event -%}
        {%- set d = ev.description -%}
        {%- set dirs = {'N':'north','NNE':'north-north-east','NE':'north-east','ENE':'east-north-east','E':'east','ESE':'east-south-east','SE':'south-east','SSE':'south-south-east','S':'south','SSW':'south-south-west','SW':'south-west','WSW':'west-south-west','W':'west','WNW':'west-north-west','NW':'north-west','NNW':'north-north-west'} -%}
        {%- set pts = d | regex_findall('at (\\d{1,2}):(\\d{2}):\\d{2} in the ([NESW]{1,3}), (\\d+)° up') -%}
        {%- set mins = ((as_datetime(ev.start) - now()).total_seconds() / 60) | round(0) | int -%}
        {%- set raw = ev.summary | regex_replace('^\\W+', '') | regex_replace('\\s*\\(bright\\)', '') | trim -%}
        {%- set multi = '+' in raw -%}
        {%- set base = raw | regex_replace('\\s*\\+\\d+', '') | trim -%}
        {%- if base == 'ISS' -%}{%- set what = 'the International Space Station, with astronauts on board,' -%}
        {%- elif 'R/B' in base and base.startswith('CZ') -%}{%- set what = 'a spent Chinese rocket stage' -%}
        {%- elif 'R/B' in base -%}{%- set what = 'a spent rocket stage' -%}
        {%- elif base.upper().startswith('STARLINK') -%}{%- set what = 'a Starlink satellite' -%}
        {%- else -%}{%- set what = 'a satellite' -%}{%- endif -%}
        {%- if pts | length < 3 -%}
        Heads up! In about {{ mins }} minutes, {{ what }} will fly over. Look up!
        {%- else -%}
        {%- set ns = namespace(h=[], t=[], dir=[]) -%}
        {%- for p in pts -%}
        {%- set deg = p[3] | int -%}
        {%- set ns.h = ns.h + ['just above the horizon' if deg < 20 else 'low in the sky' if deg < 40 else 'halfway up the sky' if deg < 60 else 'high in the sky' if deg < 80 else 'almost straight overhead'] -%}
        {%- set ns.t = ns.t + [((p[0] | int) % 12 or 12) ~ ':' ~ p[1]] -%}
        {%- set ns.dir = ns.dir + [dirs.get(p[2], p[2])] -%}
        {%- endfor -%}
        {%- set mag = (d | regex_findall_index('magnitude (-?[\\d.]+)') | float(2)) -%}
        {%- set cloud = (d | regex_findall_index('cloud cover: (\\d+)%') | int(-1)) -%}
        {%- set dur = ((as_datetime(ev.end) - as_datetime(ev.start)).total_seconds() / 60) | round(0) | int -%}
        Heads up! In about {{ mins }} minutes, {{ what }} will fly over{{ ', together with a companion' if multi }}. At {{ ns.t[0] }}, look to the {{ ns.dir[0] }}, {{ ns.h[0] }}. It's {{ 'very bright, brighter than almost any star' if mag < 0 else 'bright and easy to spot' if mag < 2 else 'fairly faint, so look carefully' }}, at its best {{ ns.h[1] }} to the {{ ns.dir[1] }}. It disappears in the {{ ns.dir[2] }} {{ 'in less than a minute' if dur < 1 else 'about a minute later' if dur == 1 else 'about ' ~ dur ~ ' minutes later' }}. {{ '' if cloud < 0 else 'Skies look clear, so you should see it well.' if cloud < 25 else 'There are some clouds around, so you may need a bit of luck.' if cloud < 70 else 'It looks cloudy, so you might miss it.' }}
        {%- endif -%}
  - action: music_assistant.play_announcement
    target:
      entity_id: media_player.gazebo_speakers
    data:
      message: "{{ message }}"
      tts_entity_id: tts.piper
      announce_volume: 40
      use_pre_announce: true
```

## How it works

The `see-a-satellite` library is a Python port of the website's workers:
SGP4 propagation at one-minute steps, the site's brightness, extinction,
limiting-magnitude and Earth-shadow models, one-second refinement, and the
site's grouping and "bright" label. Compared with the site for one location
over 5 days, it reproduces all 73 of its passes: start times within 9 s, end
times within 19 s, magnitudes within 0.03.

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
