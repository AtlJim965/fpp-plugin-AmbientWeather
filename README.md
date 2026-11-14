# Ambient Weather Display for FPP

Shows the live temperature and wind speed from your own Ambient Weather
station on an FPP Pixel Overlay Model (LED matrix): as scrolling or centered
text, in one color or multi-color (per letter, rainbow, gradients and more),
or inside a striped Christmas border.

Full details are in the [documentation](DOCUMENTATION.md); changes are in the
[change log](CHANGELOG.md).

## Install

In FPP go to **Content Setup > Plugin Manager**, paste this into the box for
installing a plugin from a URL, and install:

```
https://raw.githubusercontent.com/AtlJim965/fpp-plugin-AmbientWeather/main/pluginInfo.json
```

## Use

1. Open **Content Setup > Ambient Weather Display** (press **F1** there for
   help on each setting).
2. Enter your Ambient Weather **API Key** and **Application Key** (create
   them at https://ambientweather.net/account).
3. Pick your overlay model, message, font, colors and position, and
   optionally the Christmas border.
4. Click **Save & Show Now** to see it on the matrix.

To run it from a playlist or the scheduler, add a **Run Script** command
with `AmbientWeather.sh` and optional arguments:

| Argument | What it does |
|---|---|
| *(none)* | Update the matrix once |
| `--loop 60` | Keep updating every 60 seconds |
| `--off` | Stop a running display, clear it and put the overlay model back |
| `--text "Your text {temp} {wind}"` | Different wording for this entry (`\|` starts a new line with the border on) |

## What it sends (privacy)

Each update asks Ambient Weather's server (`rt.ambientweather.net`) for your
station's latest readings, using your API Key and Application Key. Nothing
else about you or your show is sent, and it sends nothing when it isn't
running.

## Files it writes and what it changes

* `config/plugin.fpp-plugin-AmbientWeather.json`: your settings, including
  your Ambient Weather keys (readable only by FPP's user)
* `scripts/AmbientWeather.sh`: the **Run Script** entry, created on install
* `plugindata/fpp-plugin-AmbientWeather/`: the overlay model's state from
  before the plugin first drew on it
* `images/ambient_weather_*.png`: border-mode pictures, which FPP's overlay
  Image effect reads from its images folder. Old ones are deleted
  automatically.
* `logs/plugin-fpp-plugin-AmbientWeather.log`: the plugin's log (kept under
  about 1 MB)
* Your overlay model is switched on while the plugin draws on it.
  `--off` (or **Turn Display Off**) stops the display and puts the model back
  the way it was.

Updating restarts a running `--loop` display on the new code, with the same
arguments.

Uninstalling stops the display, puts the model back, and removes the script,
pictures, saved data and log. Your settings file is kept, so a reinstall
remembers your keys; delete `config/plugin.fpp-plugin-AmbientWeather.json` to
remove them too. Uninstalling can't edit your playlists or schedules, so
remove any **Run Script > AmbientWeather.sh** entries first.

## More

* [Documentation](DOCUMENTATION.md)
* [Change log](CHANGELOG.md)
* [Report a problem](https://github.com/AtlJim965/fpp-plugin-AmbientWeather/issues)
