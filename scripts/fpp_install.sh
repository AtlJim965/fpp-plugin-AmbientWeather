#!/bin/bash
set -e
# Ambient Weather Display - install, and every update (FPP runs this after
# pulling new code, since there is no fpp_upgrade.sh). Runs as root; safe to
# run again. Everything it creates outside the plugin folder is removed again
# by scripts/fpp_uninstall.sh - keep the two in step.
# set -e stops on the first unexpected failure; steps that may fail without
# harm (a chown on an odd file system, nothing running) end in `|| true`.
PLUGINDIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${FPPDIR:-/opt/fpp}/scripts/common" ]; then
    . "${FPPDIR:-/opt/fpp}/scripts/common" || true
fi
MEDIADIR="${MEDIADIR:-/home/fpp/media}"
LOGDIR="${LOGDIR:-$MEDIADIR/logs}"
OWNER="$(stat -c '%U:%G' "$MEDIADIR" 2>/dev/null || echo fpp:fpp)"
DATADIR="$MEDIADIR/plugindata/fpp-plugin-AmbientWeather"
SCRIPTSDIR="$MEDIADIR/scripts"

# our data folder (your Ambient Weather keys, and the overlay model's state
# from before the plugin first drew on it), owned by the media folder's owner so the settings page (web
# user) can use it too
mkdir -p "$DATADIR"
# settings from older versions: config/plugin.fpp-plugin-AmbientWeather.json
# (keys included) -> FPP's plugin settings file + plugindata/credentials.json
MEDIADIR="$MEDIADIR" LOGDIR="$LOGDIR" /usr/bin/python3 "$PLUGINDIR/ambient_weather.py" \
    --migrate >/dev/null 2>&1 || true
chown -R "$OWNER" "$DATADIR" 2>/dev/null || true
chmod 750 "$DATADIR" 2>/dev/null || true
[ -f "$DATADIR/credentials.json" ] && chmod 600 "$DATADIR/credentials.json"
chmod 755 "$PLUGINDIR/ambient_weather.py" "$PLUGINDIR"/scripts/*.sh 2>/dev/null || true

# AmbientWeather.sh in FPP's Scripts folder, so "Run Script" in playlists and
# the scheduler can start it
mkdir -p "$SCRIPTSDIR"
cat > "$SCRIPTSDIR/AmbientWeather.sh" <<EOF
#!/bin/bash
# Installed by fpp-plugin-AmbientWeather - settings are on the plugin page
# (Content Setup > Ambient Weather Display). Removed when the plugin is
# uninstalled.
# Arguments: --loop 60 | --off | --text "Your text {temp} {wind}"
exec /usr/bin/python3 "$PLUGINDIR/ambient_weather.py" "\$@"
EOF
chmod 755 "$SCRIPTSDIR/AmbientWeather.sh"
chown "$OWNER" "$SCRIPTSDIR/AmbientWeather.sh" 2>/dev/null || true

# After an update a running --loop is still the old code: restart it on the
# new code with the same arguments.
MEDIADIR="$MEDIADIR" LOGDIR="$LOGDIR" /usr/bin/python3 "$PLUGINDIR/ambient_weather.py" \
    --restart-running >/dev/null 2>&1 || true

echo "Ambient Weather Display installed. Settings: Content Setup > Ambient Weather Display."
exit 0
