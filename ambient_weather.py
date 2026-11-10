#!/usr/bin/env python3
"""
ambient_weather.py - part of fpp-plugin-AmbientWeather

Shows current temperature and wind speed from an Ambient Weather station
on an FPP Pixel Overlay Model (LED matrix).

All settings come from the plugin's settings page in FPP
(Content Setup -> Ambient Weather Display). Command-line options
override them for a single run:

    AmbientWeather.sh                          # update once
    AmbientWeather.sh --loop 60                # keep updating every 60s
    AmbientWeather.sh --off                    # clear + disable overlay
    AmbientWeather.sh --text "The weather right now is:"
    AmbientWeather.sh --text "It's {temp} with {wind}!" --loop 60
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PLUGIN_NAME = "fpp-plugin-AmbientWeather"
CONFIG_FILE = f"/home/fpp/media/config/plugin.{PLUGIN_NAME}.json"

DEFAULTS = {
    "api_key": "",
    "application_key": "",
    "station_mac": "",
    "fpp_host": "http://127.0.0.1",
    "model_name": "LED Panels",
    "font": "FreeSans",
    "font_size": 22,
    "color": "#FFFFFF",
    "position": "Center",
    "scroll_speed": 35,
    "show_gust": False,
    "message": "{temp}  {wind}",
    "loop_interval": 60,
}

AMBIENT_URL = "https://rt.ambientweather.net/v1/devices"

cfg = dict(DEFAULTS)


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg.update(json.load(f))
        except Exception as e:
            log(f"Could not read {CONFIG_FILE}: {e} (using defaults)")
    else:
        log("No settings saved yet - open Content Setup -> "
            "Ambient Weather Display in FPP")
    cfg["font_size"] = int(cfg.get("font_size") or 22)
    cfg["scroll_speed"] = int(cfg.get("scroll_speed") or 35)
    cfg["loop_interval"] = int(cfg.get("loop_interval") or 60)
    cfg["show_gust"] = cfg.get("show_gust") in (True, 1, "1", "true", "on")


# ---------------------------------------------------------------- weather
def get_weather():
    if not cfg["api_key"] or not cfg["application_key"]:
        raise RuntimeError("API Key / Application Key not set on the "
                           "plugin settings page")
    query = urllib.parse.urlencode({"apiKey": cfg["api_key"],
                                    "applicationKey": cfg["application_key"]})
    req = urllib.request.Request(f"{AMBIENT_URL}?{query}",
                                 headers={"User-Agent": "FPP-AmbientWeather/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            devices = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError("HTTP 401 Unauthorized - check your API Key "
                               "and Application Key")
        raise

    if not devices:
        raise RuntimeError("No stations found on this Ambient Weather account")

    mac = cfg["station_mac"].strip().lower()
    if mac:
        for dev in devices:
            if dev.get("macAddress", "").lower() == mac:
                return dev.get("lastData", {})
        raise RuntimeError(f"Station {cfg['station_mac']} not found on account")
    return devices[0].get("lastData", {})


def build_message(data):
    temp = data.get("tempf")
    wind = data.get("windspeedmph")
    gust = data.get("windgustmph")

    temp_txt = f"{round(temp)}°F" if temp is not None else "--°F"
    if wind is None:
        wind_txt = "Wind --"
    elif cfg["show_gust"] and gust is not None:
        wind_txt = f"Wind {round(wind)} G{round(gust)} mph"
    else:
        wind_txt = f"Wind {round(wind)} mph"

    template = cfg["message"] or "{temp}  {wind}"
    if "{temp}" not in template and "{wind}" not in template:
        template += " {temp}  {wind}"   # plain text given -> append weather
    return template.replace("{temp}", temp_txt).replace("{wind}", wind_txt)


# -------------------------------------------------------------------- FPP
class FPPError(Exception):
    pass


def model_url(path):
    return (f"{cfg['fpp_host']}/api/overlays/model/"
            f"{urllib.parse.quote(cfg['model_name'])}{path}")


def list_models():
    try:
        with urllib.request.urlopen(f"{cfg['fpp_host']}/api/overlays/models",
                                    timeout=5) as resp:
            return [m.get("Name") for m in json.load(resp)]
    except Exception:
        return []


def fpp_request(method, path, payload=None):
    url = model_url(path)
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        msg = f"{method} {url} -> HTTP {e.code}"
        if e.code == 404:
            models = list_models()
            if models and cfg["model_name"] not in models:
                msg += (f"\n  Model '{cfg['model_name']}' not found. "
                        f"FPP has these models: {models}")
        raise FPPError(msg)


def fpp_put(path, payload=None):
    return fpp_request("PUT", path, payload if payload is not None else {})


def fpp_clear():
    try:
        fpp_request("GET", "/clear")
    except FPPError:
        fpp_put("/clear")


def show_text(message):
    scrolling = cfg["position"] != "Center"
    fpp_put("/state", {"State": 1})
    fpp_clear()
    fpp_put("/text", {
        "Message": message,
        "Color": cfg["color"],
        "Font": cfg["font"],
        "FontSize": cfg["font_size"],
        "AntiAlias": True,
        "Position": cfg["position"],
        "PixelsPerSecond": cfg["scroll_speed"] if scrolling else 0,
        "AutoEnable": False,
    })


def turn_off():
    fpp_clear()
    fpp_put("/state", {"State": 0})


def update_once():
    try:
        message = build_message(get_weather())
    except Exception as e:
        log(f"Weather fetch failed: {e}")
        return False
    try:
        show_text(message)
        log(f"Displayed: {message}")
        return True
    except Exception as e:
        log(f"FPP display failed: {e}")
        return False


# ------------------------------------------------------------------- main
def main():
    load_config()
    args = sys.argv[1:]

    if "--text" in args:
        i = args.index("--text")
        if i + 1 < len(args):
            cfg["message"] = args[i + 1]
            del args[i:i + 2]

    if "--off" in args:
        try:
            turn_off()
            log("Overlay cleared and disabled")
        except Exception as e:
            log(f"FPP display failed: {e}")
        return

    if "--loop" in args:
        i = args.index("--loop")
        try:
            interval = int(args[i + 1])
        except (IndexError, ValueError):
            interval = cfg["loop_interval"]
        interval = max(interval, 30)   # Ambient data only updates ~1/min
        log(f"Updating every {interval}s")
        while True:
            update_once()
            time.sleep(interval)
    else:
        sys.exit(0 if update_once() else 1)


if __name__ == "__main__":
    main()
