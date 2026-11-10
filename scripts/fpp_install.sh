#!/bin/bash
# fpp-plugin-AmbientWeather install script
# Adds AmbientWeather.sh to FPP's Scripts folder so it shows up in the
# "Run Script" command list for playlists and the scheduler.

PLUGINDIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTSDIR="/home/fpp/media/scripts"

chmod +x "${PLUGINDIR}/ambient_weather.py"

mkdir -p "${SCRIPTSDIR}"
cat > "${SCRIPTSDIR}/AmbientWeather.sh" <<EOF
#!/bin/bash
# Installed by fpp-plugin-AmbientWeather - settings are on the plugin page.
# Arguments: --loop 60 | --off | --text "Your text {temp} {wind}"
exec /usr/bin/python3 "${PLUGINDIR}/ambient_weather.py" "\$@"
EOF
chmod +x "${SCRIPTSDIR}/AmbientWeather.sh"
chown fpp:fpp "${SCRIPTSDIR}/AmbientWeather.sh" 2>/dev/null

echo "Ambient Weather Display installed. Configure it under Content Setup -> Ambient Weather Display."
