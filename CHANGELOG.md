# Change log

All notable changes to the Ambient Weather Display plugin. Newest first. Part
of the [documentation](DOCUMENTATION.md).

When you change the plugin, add a line under **Unreleased** in the same
change: what a user will notice, in plain words. Move the lines under a dated
heading when the change is released.

## Unreleased

### Added

* **Help** for the settings page: press **F1** (or FPP's help button) for a
  description of each setting.
* A log file, `logs/plugin-fpp-plugin-AmbientWeather.log`, so you can see what
  the plugin did when it was run from a playlist or the scheduler.

### Changed

* **Turn Display Off** / `--off` now also stops a display running with
  `--loop`, and puts the overlay model back the way it was before the plugin
  first used it (instead of always switching it off).
* Updating the plugin restarts a running `--loop` display on the new code,
  with the same arguments.
* Uninstalling now stops a running display, puts the overlay model back, and
  removes the plugin's pictures, saved data and log as well as
  `AmbientWeather.sh`. Your settings are still kept.

## 2026-11-14

### Added

* **Multi-color text**: each letter, word or line a different color, random
  colors, gradients, Sparkle and Chase, with Rainbow, Christmas and other
  palettes or up to five colors of your own. Scrolling text uses FPP's own
  text colors (FPP 10.2 or newer).

## 2026-11-11

### Added

* **Christmas border**: a striped border on all four sides in Christmas,
  Candy Cane and other colors, with the message sized to fit inside it, `|`
  for a new line, and an optional chase while running with `--loop`.

### Fixed

* The install scripts and `ambient_weather.py` are marked executable.

## 2026-11-10

### Added

* First version: settings page, live temperature and wind (optionally gusts)
  from an Ambient Weather station, shown centered or scrolling on a Pixel
  Overlay Model, with `--loop`, `--off` and `--text` for playlists and the
  scheduler.
