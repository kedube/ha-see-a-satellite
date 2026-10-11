# TODO

Direction (2026-10-11): James's website collects and curates the catalog; we only
consume it. With a single upstream data source this stays a HACS integration, not
a core integration.

## Library (`~/src/see-a-satellite`)
- [x] Create the GitHub repo `wildekek/see-a-satellite` and push.
- [ ] Publish `see-a-satellite` 0.1.0 to PyPI (the integration requires it).

## HACS integration (this repo)
- [x] Create the GitHub repo `wildekek/ha-see-a-satellite` and push.
- [x] Brand images in `custom_components/see_a_satellite/brand/` (icon.png, icon@2x.png;
      HA 2026.10 serves these for custom integrations, no brands PR needed).
- [ ] First release `v0.1.0` (tag must match `version` in manifest.json).
- [ ] Optionally submit to the HACS default repository list.
- [ ] Tell James: the integration downloads his catalog twice a day per HA install
      (stored across restarts), with a `see-a-satellite` User-Agent.

## Retired
- Core branch `see-a-satellite` in `~/src/core` (local only, not pushed): kept for
  reference; no docs/brands PRs or core PR.
- Public catalog (CelesTrak + Quicksat + MMT-9 + SCORE): reached 62/73 of the site's
  passes at best and needs fragile sources; dropped in favour of the site's catalog.
