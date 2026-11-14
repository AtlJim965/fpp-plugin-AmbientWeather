# Ambient Weather Display for FPP - Documentation

## Contents

* [What it does](#what-it-does)
* [Requirements](#requirements)
* [Install, update and uninstall](#install-update-and-uninstall)
* [The settings page](#the-settings-page)
  * [Ambient Weather account](#ambient-weather-account)
  * [Matrix display](#matrix-display)
  * [Multi-color text](#multi-color-text)
  * [Christmas border](#christmas-border)
  * [Advanced](#advanced)
  * [Buttons](#buttons)
* [Playlists and the scheduler](#playlists-and-the-scheduler)
* [Files and network](#files-and-network)
* [Troubleshooting](#troubleshooting)
* [Change log](#change-log)

## What it does

Reads the latest temperature and wind speed (and optionally gusts) from your
Ambient Weather station and shows them on a Pixel Overlay Model, such as an
LED matrix, for example `47°F  Wind 6 mph` or `The weather right now is:
47°F  Wind 6 mph`. The text can scroll or sit centered, use one color or
several, and can be framed by a striped Christmas border.

## Requirements

* FPP 10.0 or newer. Multi-color scrolling text needs FPP 10.2 or newer; on
  older versions it shows in one color.
* A Pixel Overlay Model for the matrix (Input/Output Setup > Pixel Overlay
  Models).
* An Ambient Weather station on your ambientweather.net account, plus an
  **API Key** and **Application Key** from https://ambientweather.net/account
  (API Keys section).
* Internet access on the FPP.

## Install, update and uninstall

**Install:** in FPP go to **Content Setup > Plugin Manager**, paste this into
the box for installing a plugin from a URL, and install:

```
https://raw.githubusercontent.com/AtlJim965/fpp-plugin-AmbientWeather/main/pluginInfo.json
```

Installing adds `AmbientWeather.sh` to FPP's Scripts so **Run Script** can
start it.

**Update:** use **Update** in the Plugin Manager. Your settings and keys are
kept. A display running with `--loop` restarts on the new code with the same
arguments.

**Uninstall:** use **Uninstall** in the Plugin Manager. It stops a running
display, puts the overlay model back the way it was, and removes
`AmbientWeather.sh`, the border pictures, your keys, saved data and log.
Your settings file is kept, so a reinstall remembers your settings (you enter
the keys again); delete `config/plugin.fpp-plugin-AmbientWeather` to remove
them too. A **Reinstall** (FPP 10.4 and newer) keeps the keys as well.

Uninstalling can't edit your playlists or schedules. Remove any **Run Script
> AmbientWeather.sh** entries from them first.

## The settings page

**Content Setup > Ambient Weather Display**. Press **F1** on the page for a
short version of this section. Nothing is saved until you press **Save** or
**Save & Show Now**.

### Ambient Weather account

* **API Key** and **Application Key**: from ambientweather.net > Account >
  API Keys. They are stored only on the FPP, in the plugin's private data
  folder, and never shown again: once saved, the boxes say *saved - leave
  blank to keep it*. Type a new key to replace one.
* **Station MAC (optional)**: if your account has more than one station, the
  MAC address of the one to use (shown on ambientweather.net under Devices).
  Blank uses the first station.

### Matrix display

* **Overlay Model**: the Pixel Overlay Model to draw on.
* **Message**: what to show. `{temp}` and `{wind}` are replaced with the live
  readings, for example `The weather right now is: {temp}  {wind}`. Text
  without either gets the readings added at the end. With the border on, `|`
  starts a new line.
* **Show wind gust**: `Wind 5 G12 mph` instead of `Wind 5 mph`.
* **Font** and **Font size**: for scrolling or centered text. Not used with
  the border on (the border uses a built-in pixel font sized to fit).
* **Text colors**: see [Multi-color text](#multi-color-text).
* **Position**: *Center* for still text, or scroll right to left, left to
  right, bottom to top or top to bottom.
* **Scroll speed**: pixels per second for scrolling text.
* **Default loop interval**: seconds between updates for `--loop` without a
  number (at least 30; the station only reports about once a minute).

### Multi-color text

* **Text colors**: one color, each letter / word / line a different color, a
  random color per letter or word, a gradient (left to right, top to bottom
  or corner to corner), Sparkle or Chase.
* **Color palette** (shown for anything but one color): Rainbow, Christmas,
  Winter, Fire, Ocean, Forest, Patriotic, Pastel, Party, Halloween, or
  **Custom**, which uses **Color** plus up to four more colors (choose how
  many with *use the first N colors*).
* **Color movement**: 0 keeps the colors still; higher values make them flow
  through the letters. Sparkle and Chase need it above 0.

For scrolling and centered text the plugin uses FPP's own text colors
(FPP 10.2 or newer). With the border on the plugin draws the colors itself:
the colors stay still, and Sparkle and Chase show as one color per letter.

### Christmas border

* **Show border**: a striped border on all four sides with the message drawn
  inside it, as large as fits.
* **Border colors**: Christmas (red, white, green), Red & Green, Candy Cane,
  Winter, Gold & Silver, Rainbow, or Custom with **Custom colors** (a
  comma-separated list such as `#FF0000,#FFFFFF,#00C83C`).
* **Border thickness**: pixels (1 to 8).
* **Stripe length**: pixels per color.
* **Chase** and **Chase speed**: make the stripes move around the edge (steps
  per second). Only while running with `--loop`.

### Advanced

* **FPP address**: where the plugin reaches FPP's API. Leave it as
  `http://127.0.0.1`.

### Buttons

* **Save**: saves the settings.
* **Save & Show Now**: saves, then fetches the weather and shows it once. The
  result (or the error) appears under the buttons.
* **Turn Display Off**: stops a running display, clears it and puts the
  overlay model back the way it was.

## Playlists and the scheduler

Add a **Run Script** command with `AmbientWeather.sh`. Arguments:

| Argument | What it does |
|---|---|
| *(none)* | Update the matrix once |
| `--loop 60` | Keep updating every 60 seconds (any number, at least 30) |
| `--off` | Stop a running display, clear it and put the model back |
| `--text "..."` | Use this wording instead of the saved message, for this entry only |

`--text` and `--loop` can be combined, for example
`--text "The weather right now is:" --loop 60`. A `--loop` keeps running until
`--off`, **Turn Display Off**, an update or an uninstall stops it, or the FPP
restarts.

## Files and network

The plugin writes these files in FPP's media folder:

* `config/plugin.fpp-plugin-AmbientWeather`: settings (no keys), in FPP's
  plugin settings format. Kept when the plugin is uninstalled.
* `plugindata/fpp-plugin-AmbientWeather/credentials.json`: your Ambient
  Weather keys, readable only by FPP's user.
* `scripts/AmbientWeather.sh`: the Run Script entry.
* `plugindata/fpp-plugin-AmbientWeather/model_state.json`: whether the overlay
  model was on before the plugin first switched it on, so it can be put back.
* `images/ambient_weather_*.png`: border-mode pictures for FPP's overlay Image
  effect. Older ones are deleted after a few seconds.
* `logs/plugin-fpp-plugin-AmbientWeather.log`: the log. FPP rotates it.

On each update it sends one request to Ambient Weather's server
(`rt.ambientweather.net`) with your API Key and Application Key, and gets your
stations' latest readings back. It sends nothing else anywhere and contacts
nothing when it isn't running.

## Troubleshooting

* **"HTTP 401 Unauthorized"**: the API Key or Application Key is wrong, or
  they are swapped. Copy them again from ambientweather.net.
* **"Model 'X' not found"**: the Overlay Model setting doesn't match a model
  in FPP; the message lists the models FPP has.
* **Nothing changes after editing settings while a `--loop` runs**: a running
  loop reads the settings when it starts. Press **Turn Display Off** and start
  it again (or restart the playlist).
* **Colors don't show on scrolling text**: multi-color scrolling text needs
  FPP 10.2 or newer.
* **° shows as a box**: pick another **Font**; the list comes from FPP.
* For anything else, look in `logs/plugin-fpp-plugin-AmbientWeather.log`
  (Content Setup > File Manager > Logs).

## Change log

See [CHANGELOG.md](CHANGELOG.md).
