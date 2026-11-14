#!/bin/bash
# Ambient Weather Display - uninstall. Runs as root; safe to run twice. FPP
# deletes the plugin folder itself afterwards; this undoes everything the
# plugin made or changed outside it (keep in step with fpp_install.sh and
# ambient_weather.py):
#   - any running display (AmbientWeather.sh --loop) and what it drew
#   - the overlay model's on/off state (put back as it was before the plugin
#     first drew on it)
#   - images/ambient_weather_*.png        border-mode frames
#   - plugindata/fpp-plugin-AmbientWeather/  saved model state
#   - logs/plugin-fpp-plugin-AmbientWeather.log (and the rotated .1 copy)
#   - scripts/AmbientWeather.sh           the Run Script entry
# Kept on purpose: config/plugin.fpp-plugin-AmbientWeather.json (your
# settings and Ambient Weather keys), so a reinstall remembers them. Delete
# that file by hand to remove them too.
PLUGINDIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${FPPDIR:-/opt/fpp}/scripts/common" ]; then
    . "${FPPDIR:-/opt/fpp}/scripts/common" >/dev/null 2>&1
fi
MEDIADIR="${MEDIADIR:-/home/fpp/media}"
LOGDIR="${LOGDIR:-$MEDIADIR/logs}"

# stop the display, clear the model and put its state back, then make sure
# nothing is left running
MEDIADIR="$MEDIADIR" LOGDIR="$LOGDIR" \
    timeout 15 /usr/bin/python3 "$PLUGINDIR/ambient_weather.py" --off >/dev/null 2>&1 || true
pkill -f "$PLUGINDIR/ambient_weather.py" 2>/dev/null || true

rm -f "$MEDIADIR"/images/ambient_weather_*.png
rm -rf "$MEDIADIR/plugindata/fpp-plugin-AmbientWeather"
rm -f "$LOGDIR"/plugin-fpp-plugin-AmbientWeather.log*
rm -f "$MEDIADIR/scripts/AmbientWeather.sh"
echo "Ambient Weather Display removed. Your settings file was kept."
exit 0
