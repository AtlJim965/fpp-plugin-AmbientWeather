#!/usr/bin/env python3
"""
ambient_weather.py - part of fpp-plugin-AmbientWeather

Shows current temperature and wind speed from an Ambient Weather station
on an FPP Pixel Overlay Model (LED matrix), optionally inside a
Christmas-colored border.

All settings come from the plugin's settings page in FPP
(Content Setup -> Ambient Weather Display). Command-line options
override them for a single run:

    AmbientWeather.sh                          # update once
    AmbientWeather.sh --loop 60                # keep updating every 60s
    AmbientWeather.sh --off                    # stop, clear, put the model back
    AmbientWeather.sh --text "The weather right now is:"
    AmbientWeather.sh --text "It's {temp} with {wind}!" --loop 60
    AmbientWeather.sh --text "Weather now:|{temp}  {wind}"   # | = new line
"""

import json
import os
import signal
import struct
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zlib

PLUGIN_NAME = "fpp-plugin-AmbientWeather"
MEDIA_DIR = os.environ.get("MEDIADIR", "/home/fpp/media")
CONFIG_FILE = f"{MEDIA_DIR}/config/plugin.{PLUGIN_NAME}.json"
IMAGES_DIR = f"{MEDIA_DIR}/images"
IMAGE_PREFIX = "ambient_weather_"
DATA_DIR = f"{MEDIA_DIR}/plugindata/{PLUGIN_NAME}"
MODEL_STATE_FILE = os.path.join(DATA_DIR, "model_state.json")
LOG_DIR = os.environ.get("LOGDIR", f"{MEDIA_DIR}/logs")
LOG_FILE = os.path.join(LOG_DIR, f"plugin-{PLUGIN_NAME}.log")
LOG_MAX_BYTES = 512 * 1024
SCRIPT = os.path.abspath(__file__)

DEFAULTS = {
    "api_key": "",
    "application_key": "",
    "station_mac": "",
    "fpp_host": "http://127.0.0.1",
    "model_name": "LED Panels",
    "font": "FreeSans",
    "font_size": 22,
    "color": "#FFFFFF",
    # multi-color text (FPP 10.2+ for scrolling text; drawn by this script
    # when the border is on)
    "text_color_mode": "Single",
    "text_palette": "Rainbow",
    "text_num_colors": 2,
    "text_color2": "#0000FF",
    "text_color3": "#00FF00",
    "text_color4": "#FFFF00",
    "text_color5": "#FF00FF",
    "text_color_speed": 0,
    "position": "Center",
    "scroll_speed": 35,
    "show_gust": False,
    "message": "{temp}  {wind}",
    "loop_interval": 60,
    # border
    "border_enabled": False,
    "border_thickness": 3,
    "border_palette": "Christmas",
    "border_custom_colors": "#FF0000,#FFFFFF,#00C83C",
    "border_stripe": 6,
    "border_chase": False,
    "chase_speed": 4,
}

PALETTES = {
    "Christmas": ["#FF0000", "#FFFFFF", "#00C83C"],
    "Red & Green": ["#FF0000", "#00C83C"],
    "Candy Cane": ["#FF0000", "#FFFFFF"],
    "Winter": ["#0080FF", "#FFFFFF", "#80D0FF"],
    "Gold & Silver": ["#FFAA00", "#C8C8C8"],
    "Rainbow": ["#FF0000", "#FF8000", "#FFFF00", "#00FF00", "#0080FF", "#A000FF"],
}

# Text colour palettes - the same colours FPP's own text effect uses
TEXT_PALETTES = {
    "Christmas": ["#FF0000", "#00FF00", "#FFFFFF"],
    "Halloween": ["#FF6000", "#8000FF", "#00FF00"],
    "Winter": ["#FFFFFF", "#80D0FF", "#0040FF"],
    "Fire": ["#FF0000", "#FF6000", "#FFC000", "#FFFF80"],
    "Ocean": ["#0020FF", "#00A0FF", "#00FFC0"],
    "Forest": ["#004000", "#00A000", "#80FF00"],
    "Patriotic": ["#FF0000", "#FFFFFF", "#0000FF"],
    "Pastel": ["#FFB0C0", "#B0E0FF", "#FFF0A0", "#B0FFC0"],
    "Party": ["#FF00A0", "#00FFFF", "#FFFF00", "#80FF00", "#FF4000"],
}
TEXT_COLOR_MODES = ["Single", "Per Letter", "Per Word", "Per Line", "Random Letter",
                    "Random Word", "Gradient Horizontal", "Gradient Vertical",
                    "Gradient Diagonal", "Sparkle", "Chase"]

AMBIENT_URL = os.environ.get("AMBIENT_URL", "https://rt.ambientweather.net/v1/devices")

cfg = dict(DEFAULTS)


def log(msg):
    """Print (shown on the settings page / FPP's script output) and append to
    logs/plugin-fpp-plugin-AmbientWeather.log (kept under ~1 MB)."""
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [pid {os.getpid()}] {msg}"
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)
    try:
        if os.path.isdir(LOG_DIR):
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > LOG_MAX_BYTES:
                os.replace(LOG_FILE, LOG_FILE + ".1")
            new = not os.path.exists(LOG_FILE)
            with open(LOG_FILE, "a") as f:
                f.write(line + "\n")
            if new:
                own(LOG_FILE)
    except Exception:
        pass


def as_bool(v):
    return v in (True, 1, "1", "true", "on", "True")


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
    for k in ("font_size", "scroll_speed", "loop_interval", "border_thickness",
              "border_stripe", "chase_speed", "text_num_colors", "text_color_speed"):
        try:
            cfg[k] = int(cfg.get(k))
        except (TypeError, ValueError):
            cfg[k] = DEFAULTS[k]
    for k in ("show_gust", "border_enabled", "border_chase"):
        cfg[k] = as_bool(cfg.get(k))


def hex_rgb(s, fallback=(255, 255, 255)):
    s = (s or "").strip().lstrip("#")
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return fallback


def border_colors():
    pal = PALETTES.get(cfg["border_palette"])
    if not pal:
        pal = [c for c in cfg["border_custom_colors"].split(",") if c.strip()]
    return [hex_rgb(c) for c in pal] or [(255, 0, 0), (0, 200, 60)]


def hue_rgb(h):
    """Full-brightness colour at position h (0..1) around the colour wheel."""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


def text_palette():
    """List of RGB colours, or None for Rainbow."""
    name = cfg.get("text_palette", "Rainbow")
    if name == "Rainbow":
        return None
    if name in TEXT_PALETTES:
        return [hex_rgb(c) for c in TEXT_PALETTES[name]]
    n = max(1, min(5, int(cfg.get("text_num_colors") or 2)))
    keys = ["color", "text_color2", "text_color3", "text_color4", "text_color5"][:n]
    return [hex_rgb(cfg.get(k)) for k in keys]


def pick(pal, i, count):
    """i-th of count colours from a palette (rainbow spreads over the wheel)."""
    if pal is None:
        return hue_rgb(i / max(1, count))
    return pal[i % len(pal)]


def blend(pal, t):
    """Colour at t (0..1) along a smooth blend through the palette."""
    if pal is None:
        return hue_rgb(t * 0.85)            # stop short of wrapping back to red
    if len(pal) == 1:
        return pal[0]
    t = min(max(t, 0.0), 1.0) * (len(pal) - 1)
    i = min(int(t), len(pal) - 2)
    f = t - i
    a, b = pal[i], pal[i + 1]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


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


# ------------------------------------------------------------- pixel font
FONT5x7 = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    " ": ["....."] * 7,
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "/": [".....", "....#", "...#.", "..#..", ".#...", "#....", "....."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "#": [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
    "%": ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "°": [".##..", "#..#.", "#..#.", ".##..", ".....", ".....", "....."],
}


def font_text(s):
    """Upper-case, strip accents, drop characters the pixel font can't draw."""
    out = []
    for ch in s.upper():
        if ch in FONT5x7:
            out.append(ch)
            continue
        plain = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
        out.append(plain if plain in FONT5x7 and plain else " ")
    return "".join(out)


def advance(ch, scale):
    return (4 if ch == " " else 6) * scale     # narrow spaces


def text_width(s, scale):
    return sum(advance(c, scale) for c in s) - scale if s else 0


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def text(self, x, y, s, c, scale=1, start=0):
        """Draw text. c is an (r,g,b) colour or a function
        c(char_number, px, py) -> (r,g,b) for multi-colour text.
        start = how many characters came before this line."""
        for n, ch in enumerate(s):
            for gy, row in enumerate(FONT5x7.get(ch, FONT5x7[" "])):
                for gx, bit in enumerate(row):
                    if bit == "#":
                        for dy in range(scale):
                            for dx in range(scale):
                                px, py = x + gx * scale + dx, y + gy * scale + dy
                                self.set(px, py, c(start + n, px, py) if callable(c) else c)
            x += advance(ch, scale)

    def png(self):
        row = self.w * 3
        raw = b"".join(b"\x00" + bytes(self.buf[y * row:(y + 1) * row])
                       for y in range(self.h))

        def chunk(t, d):
            return (struct.pack(">I", len(d)) + t + d +
                    struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF))
        return (b"\x89PNG\r\n\x1a\n" +
                chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def draw_border(cv, offset=0):
    """Striped border on all four sides. Stripes are slanted like a candy
    cane and move around the edge as `offset` changes (chase)."""
    t = max(1, min(cfg["border_thickness"], min(cv.w, cv.h) // 4))
    seg = max(1, cfg["border_stripe"])
    colors = border_colors()
    n = len(colors)
    W, H = cv.w, cv.h
    for y in range(H):
        for x in range(W):
            d = min(x, y, W - 1 - x, H - 1 - y)      # depth into the border
            if d >= t:
                continue
            # position along the edge, clockwise from the top-left corner
            if y == d:
                p = x
            elif x == W - 1 - d:
                p = W + y
            elif y == H - 1 - d:
                p = W + H + (W - 1 - x)
            else:
                p = 2 * W + H + (H - 1 - y)
            cv.set(x, y, colors[((p + d - offset) // seg) % n])


def layout_text(message, max_w, max_h):
    """Choose lines and a size for each line so the message fills the area.
    '|' in the message forces a new line. Returns [(text, scale), ...]."""
    explicit = [font_text(l).strip() for l in message.split("|")]
    explicit = [l for l in explicit if l] or [""]

    candidates = [explicit]
    if len(explicit) == 1:                       # also try 2- and 3-line splits
        words = explicit[0].split()
        for parts in (2, 3):
            if len(words) >= parts:
                candidates.append(split_balanced(words, parts))

    best, best_score = None, None
    for lines in candidates:
        scales = []
        for l in lines:
            s = 4
            while s > 1 and text_width(l, s) > max_w:
                s -= 1
            scales.append(s)
        # shrink the biggest lines until everything fits vertically
        while block_height(scales) > max_h and max(scales) > 1:
            i = scales.index(max(scales))
            scales[i] -= 1
        fits = (block_height(scales) <= max_h and
                all(text_width(l, s) <= max_w for l, s in zip(lines, scales)))
        score = (fits, min(scales), sum(scales), -len(lines))
        if best_score is None or score > best_score:
            best, best_score = list(zip(lines, scales)), score
    return best


def split_balanced(words, parts):
    total = len(" ".join(words))
    target = total / parts
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > target and len(lines) < parts - 1:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    lines.append(cur)
    return lines


def block_height(scales):
    gap = 2 if len(scales) > 1 else 0
    return sum(7 * s for s in scales) + gap * (len(scales) - 1) * max(1, min(scales))


def draw_frame(message, W, H, offset=0):
    cv = Canvas(W, H)
    draw_border(cv, offset)
    t = max(1, min(cfg["border_thickness"], min(W, H) // 4))
    pad = 2
    x0, y0 = t + pad, t + pad
    iw, ih = W - 2 * x0, H - 2 * y0
    lines = layout_text(message, iw, ih)
    scales = [s for _, s in lines]
    gap = (2 * max(1, min(scales))) if len(lines) > 1 else 0
    y = y0 + max(0, (ih - block_height(scales)) // 2)
    color = text_colorizer(lines, x0, y0, iw, ih)
    start = 0
    for text, s in lines:
        x = x0 + max(0, (iw - text_width(text, s)) // 2)
        cv.text(x, y, text, color, s, start)
        start += len(text)
        y += 7 * s + gap
    return cv


def text_colorizer(lines, x0, y0, iw, ih):
    """Colour (or colour function) for the border-mode pixel text, matching
    FPP's text colour modes. Sparkle and Chase are animated in FPP; here they
    are drawn as Per Letter."""
    import random
    mode = cfg.get("text_color_mode", "Single")
    if mode not in TEXT_COLOR_MODES or mode == "Single":
        return hex_rgb(cfg["color"])
    pal = text_palette()
    full = "".join(t for t, _ in lines)

    # which letter / word / line each character belongs to (spaces don't count)
    letter_no, word_no, line_no = [], [], []
    letters = words = 0
    in_word = False
    for li, (t, _) in enumerate(lines):
        in_word = False
        for ch in t:
            if ch == " ":
                letter_no.append(-1)
                word_no.append(-1)
                in_word = False
            else:
                if not in_word:
                    words += 1
                    in_word = True
                letter_no.append(letters)
                word_no.append(words - 1)
                letters += 1
            line_no.append(li)
    rnd = random.Random(full)                      # same message -> same colours
    rand_letters = [rnd.randrange(1 << 30) for _ in range(letters)]
    rand_words = [rnd.randrange(1 << 30) for _ in range(words)]

    def rand_pick(r, count):
        return hue_rgb((r % 1000) / 1000) if pal is None else pal[r % len(pal)]

    if mode in ("Per Letter", "Sparkle", "Chase"):
        return lambda i, px, py: pick(pal, max(letter_no[i], 0), letters)
    if mode == "Per Word":
        return lambda i, px, py: pick(pal, max(word_no[i], 0), words)
    if mode == "Per Line":
        return lambda i, px, py: pick(pal, line_no[i], len(lines))
    if mode == "Random Letter":
        return lambda i, px, py: rand_pick(rand_letters[max(letter_no[i], 0)], letters)
    if mode == "Random Word":
        return lambda i, px, py: rand_pick(rand_words[max(word_no[i], 0)], words)
    if mode == "Gradient Horizontal":
        return lambda i, px, py: blend(pal, (px - x0) / max(1, iw - 1))
    if mode == "Gradient Vertical":
        return lambda i, px, py: blend(pal, (py - y0) / max(1, ih - 1))
    if mode == "Gradient Diagonal":
        return lambda i, px, py: blend(pal, ((px - x0) / max(1, iw - 1) +
                                             (py - y0) / max(1, ih - 1)) / 2)
    return hex_rgb(cfg["color"])


# -------------------------------------------------------------------- FPP
class FPPError(Exception):
    pass


def model_url(path=""):
    return (f"{cfg['fpp_host']}/api/overlays/model/"
            f"{urllib.parse.quote(cfg['model_name'])}{path}")


def list_models():
    try:
        with urllib.request.urlopen(f"{cfg['fpp_host']}/api/overlays/models",
                                    timeout=5) as resp:
            return [m.get("Name") for m in json.load(resp)]
    except Exception:
        return []


_size = {}


def model_size():
    if "wh" not in _size:
        w, h = 192, 64
        try:
            with urllib.request.urlopen(model_url(), timeout=5) as r:
                m = json.load(r)
            w = int(m.get("width") or w)
            h = int(m.get("height") or h)
        except Exception as e:
            log(f"Couldn't read model size from FPP ({e}); assuming {w}x{h}")
        _size["wh"] = (w, h)
    return _size["wh"]


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


def fpp_command(command, args):
    body = json.dumps({"command": command, "multisyncCommand": False,
                       "multisyncHosts": "", "args": args}).encode()
    req = urllib.request.Request(f"{cfg['fpp_host']}/api/command", data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace").strip()[:300]
        raise FPPError(f"FPP command '{command}' failed: {e} - {detail}")


def own(path):
    """Files made while running as root are handed to the media folder's
    owner so FPP's web pages can still manage them."""
    try:
        if os.geteuid() == 0:
            st = os.stat(MEDIA_DIR)
            os.chown(path, st.st_uid, st.st_gid)
    except Exception:
        pass


# ------------------------------------------------- overlay model state
def remember_model_state():
    """Before the plugin first switches the model on, note whether it was on,
    so --off / uninstall can put it back. An earlier run's note is kept."""
    if os.path.exists(MODEL_STATE_FILE):
        return
    try:
        with urllib.request.urlopen(model_url(), timeout=5) as r:
            state = int(json.load(r).get("isActive", 0) or 0)
        os.makedirs(DATA_DIR, exist_ok=True)
        own(DATA_DIR)
        with open(MODEL_STATE_FILE, "w") as f:
            json.dump({"model": cfg["model_name"], "state": state}, f)
        own(MODEL_STATE_FILE)
    except Exception as e:
        log(f"Couldn't read the state of model '{cfg['model_name']}': {e}")


def enable_model():
    remember_model_state()
    fpp_put("/state", {"State": 1})


def restore_model_state():
    """Put the model back the way it was before the plugin first drew on it
    (off if nothing was saved)."""
    name, state = cfg["model_name"], 0
    try:
        with open(MODEL_STATE_FILE) as f:
            saved = json.load(f)
        name, state = saved.get("model") or name, int(saved.get("state", 0))
    except Exception:
        pass
    url = f"{cfg['fpp_host']}/api/overlays/model/{urllib.parse.quote(name)}/state"
    req = urllib.request.Request(url, data=json.dumps({"State": state}).encode(),
                                 headers={"Content-Type": "application/json"}, method="PUT")
    urllib.request.urlopen(req, timeout=10).read()
    try:
        os.remove(MODEL_STATE_FILE)
    except FileNotFoundError:
        pass
    return name, state


# ------------------------------------------------- other running copies
def running_copies():
    """{pid: [args]} of other processes running this script."""
    found = {}
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) == os.getpid():
            continue
        try:
            with open(f"/proc/{d}/cmdline", "rb") as f:
                argv = [a.decode(errors="replace") for a in f.read().split(b"\0") if a]
        except Exception:
            continue
        for i, a in enumerate(argv[:3]):
            if os.path.abspath(a) == SCRIPT and "python" in os.path.basename(argv[0]):
                found[int(d)] = argv[i + 1:]
                break
    return found


def stop_copies(only_loops=False, wait=5):
    copies = {p: a for p, a in running_copies().items()
              if not only_loops or "--loop" in a}
    for pid in copies:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    end = time.time() + wait
    while time.time() < end and any(os.path.exists(f"/proc/{p}") for p in copies):
        time.sleep(0.1)
    for pid in copies:
        if os.path.exists(f"/proc/{pid}"):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    return copies


def restart_loops():
    """After an update: restart running --loop copies on the new code, with
    the same arguments they were started with."""
    import subprocess
    stopped = stop_copies(only_loops=True)
    for pid, args in stopped.items():
        log(f"Restarting the running display (pid {pid}) with the updated code")
        subprocess.Popen([sys.executable, SCRIPT] + args, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True, env=dict(os.environ))
    return len(stopped)


_frame_no = [0]


def show_image(cv):
    _frame_no[0] += 1
    name = f"{IMAGE_PREFIX}{os.getpid()}_{_frame_no[0]}.png"
    path = os.path.join(IMAGES_DIR, name)
    with open(path, "wb") as f:
        f.write(cv.png())
    own(path)
    enable_model()
    fpp_command("Overlay Model Effect", [
        cfg["model_name"], "Enabled", "Image", "None", "Center", "0", "0", name])
    cleanup_images(keep=name, older_than=5)


def cleanup_images(keep=None, older_than=0):
    try:
        for fn in os.listdir(IMAGES_DIR):
            if fn.startswith(IMAGE_PREFIX) and fn.endswith(".png") and fn != keep:
                full = os.path.join(IMAGES_DIR, fn)
                if time.time() - os.path.getmtime(full) > older_than:
                    os.remove(full)
    except Exception:
        pass


def show_text(message):
    scrolling = cfg["position"] != "Center"
    enable_model()
    fpp_clear()
    fpp_put("/text", {
        "Message": " ".join(p.strip() for p in message.split("|")),
        "Color": cfg["color"],
        "Font": cfg["font"],
        "FontSize": cfg["font_size"],
        "AntiAlias": True,
        "Position": cfg["position"],
        "PixelsPerSecond": cfg["scroll_speed"] if scrolling else 0,
        "AutoEnable": False,
        **fpp_color_args(),
    })


def fpp_color_args():
    """FPP 10.2+ text colour options. Left out entirely for Single so older
    FPP versions get exactly the request they always did."""
    mode = cfg.get("text_color_mode", "Single")
    if mode == "Single" or mode not in TEXT_COLOR_MODES:
        return {}
    return {
        "ColorMode": mode,
        "Palette": cfg.get("text_palette", "Rainbow"),
        "NumColors": str(max(1, min(5, int(cfg.get("text_num_colors") or 2)))),
        "Color2": cfg.get("text_color2", "#0000FF"),
        "Color3": cfg.get("text_color3", "#00FF00"),
        "Color4": cfg.get("text_color4", "#FFFF00"),
        "Color5": cfg.get("text_color5", "#FF00FF"),
        "ColorSpeed": str(max(0, min(100, int(cfg.get("text_color_speed") or 0)))),
    }


def display(message, offset=0):
    if cfg["border_enabled"]:
        W, H = model_size()
        show_image(draw_frame(message, W, H, offset))
    else:
        show_text(message)


def turn_off():
    """Stop any running display, clear what the plugin drew, put the model
    back the way it was and delete the plugin's images."""
    stopped = stop_copies()
    if stopped:
        log(f"Stopped {len(stopped)} running copy(ies)")
    try:
        fpp_clear()
    finally:
        cleanup_images()
        name, state = restore_model_state()
        words = {0: "off", 1: "on", 2: "on (transparent)", 3: "on (transparent RGB)"}
        log(f"Model '{name}' put back {words.get(state, f'to state {state}')}")


def fetch_message():
    try:
        return build_message(get_weather())
    except Exception as e:
        log(f"Weather fetch failed: {e}")
        return None


def update_once():
    message = fetch_message()
    if message is None:
        return False
    try:
        display(message)
        log(f"Displayed: {message.replace('|', ' / ')}")
        return True
    except Exception as e:
        log(f"FPP display failed: {e}")
        return False


def run_loop(interval):
    chasing = cfg["border_enabled"] and cfg["border_chase"]
    log(f"Updating every {interval}s" + (" with chasing border" if chasing else ""))
    message, offset = None, 0
    while True:
        new = fetch_message()
        if new is not None:
            message = new
            log(f"Weather: {message.replace('|', ' / ')}")
        next_fetch = time.time() + interval
        if message is None:
            time.sleep(interval)
            continue
        if not chasing:
            try:
                display(message)
            except Exception as e:
                log(f"FPP display failed: {e}")
            time.sleep(max(0, next_fetch - time.time()))
            continue
        step = 1.0 / max(1, min(cfg["chase_speed"], 10))
        while time.time() < next_fetch:
            start = time.time()
            try:
                display(message, offset)
            except Exception as e:
                log(f"FPP display failed: {e}")
                time.sleep(5)
            offset += 1
            time.sleep(max(0, step - (time.time() - start)))


# ------------------------------------------------------------------- main
def main():
    load_config()
    args = sys.argv[1:]

    if "--text" in args:
        i = args.index("--text")
        if i + 1 < len(args):
            cfg["message"] = args[i + 1]
            del args[i:i + 2]

    if "--restart-running" in args:          # used by fpp_install.sh
        n = restart_loops()
        if n:
            log(f"Restarted {n} running display(s) on the updated code")
        return

    if "--off" in args:
        try:
            turn_off()
            log("Display stopped and cleared")
        except Exception as e:
            log(f"FPP display failed: {e}")
        return

    # a stop request (--off, uninstall, update) ends a loop quietly
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    if "--loop" in args:
        i = args.index("--loop")
        try:
            interval = int(args[i + 1])
        except (IndexError, ValueError):
            interval = cfg["loop_interval"]
        run_loop(max(interval, 30))     # Ambient data only updates ~1/min
    else:
        sys.exit(0 if update_once() else 1)


if __name__ == "__main__":
    main()
