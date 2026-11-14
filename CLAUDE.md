# Ambient Weather Display FPP plugin - notes for whoever changes it

## On every update: recheck install against uninstall

FPP runs `scripts/fpp_install.sh` on install AND after every update (there is
no `fpp_upgrade.sh`), and `scripts/fpp_uninstall.sh` before it deletes the
plugin folder. Whenever a change makes the plugin create, write or change
anything outside its own folder, update both scripts in the same change:

1. List what the code writes: `grep -n "open(\|os.replace\|os.remove\|IMAGES_DIR\|LOG_FILE\|DATA_DIR\|/state\|file_put_contents" ambient_weather.py plugin_setup.php scripts/*.sh`
2. Every item must be in the comment at the top of `fpp_uninstall.sh` and
   removed (or put back) by it. Today that is:
   - running display copies (`--off`, then `pkill`)
   - overlay model state (saved in `plugindata/.../model_state.json`, put back
     by `restore_model_state()` on `--off`)
   - `images/ambient_weather_*.png`
   - `plugindata/fpp-plugin-AmbientWeather/` (keys and model state; kept on
     a Reinstall when `FPP_PLUGIN_REINSTALL=1`)
   - `logs/plugin-fpp-plugin-AmbientWeather.log*`
   - `scripts/AmbientWeather.sh`
   - kept on purpose: `config/plugin.fpp-plugin-AmbientWeather` (settings,
     no keys)
3. `fpp_install.sh` must stay safe to re-run, delete files that older
   versions left behind, `chown -R` plugindata to the media owner, and
   restart a running `--loop` (`--restart-running`) so it runs the new code.
4. Test the whole cycle on a stand-in FPP: snapshot the media folder, install,
   start a `--loop`, show once with the border on, `--off`, update (re-run
   fpp_install.sh while a loop runs), uninstall while running, delete the
   plugin folder, and diff the snapshot. Nothing may be left except the
   settings file; the model must be back in its original state and no copy
   may still be running. (`MEDIADIR`, `LOGDIR` and `AMBIENT_URL` can point
   the script at a stand-in.)
5. Update the "Files it writes and what it changes" section of README.md and
   the `privacy` block in pluginInfo.json if any of this changed.

## FPP's plugin guidelines

Follow FalconChristmas's `PLUGIN_GUIDELINES.md` and keep FPP's plugin check
clean (`python lint_plugin.py <plugin_dir> fpp-plugin-AmbientWeather` from
fpp-data's `.github/scripts`). Keys stay in `plugindata/` (0600), never in
the log or the page; one log file, rotated by FPP; theme-aware Bootstrap
classes only (no hard-coded colors) in the page.

## On every change: update the docs

Add a line to `CHANGELOG.md` under **Unreleased** describing what a user will
notice. If a setting, command, file or behaviour changed, update
`DOCUMENTATION.md` and `help/plugin_setup.php` too (and README.md where it
covers the same thing).
