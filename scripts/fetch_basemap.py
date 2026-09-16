# -*- coding: utf-8 -*-
"""
Fetches a small grid of OpenStreetMap tiles covering Alfredo Chaves, ES and
stitches them into a single base-map image, embedded later as a data: URI in
the interactive map (Claude Artifacts cannot fetch live map tiles at view
time - only cdnjs/jsdelivr/tailwind/jquery scripts and fonts.googleapis.com
stylesheets are allowed as external resources). One-off fetch, properly
attributed to (c) OpenStreetMap contributors in the map's caption.

Produces:
  - output/basemap_alfredo_chaves.png (stitched raster)
  - output/basemap_meta.json (zoom, tile origin, pixel size - for lat/lon -> px math)
"""
import math, os, time, urllib.request, json
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

ZOOM = 12
LON_MIN, LAT_MIN, LON_MAX, LAT_MAX = -41.02, -20.73, -40.63, -20.40
UA = "alfredo-chaves-case-study-research/1.0 (personal research map, one-off fetch)"

def deg2num(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    xtile = (lon + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n
    return xtile, ytile

x1f, y1f = deg2num(LAT_MAX, LON_MIN, ZOOM)
x2f, y2f = deg2num(LAT_MIN, LON_MAX, ZOOM)
x1, x2 = int(math.floor(x1f)), int(math.floor(x2f))
y1, y2 = int(math.floor(y1f)), int(math.floor(y2f))
print(f"Tile grid z={ZOOM}: x {x1}-{x2}, y {y1}-{y2} ({(x2-x1+1)}x{(y2-y1+1)} = {(x2-x1+1)*(y2-y1+1)} tiles)")

TS = 256
cols = x2 - x1 + 1
rows = y2 - y1 + 1
canvas = Image.new("RGB", (cols * TS, rows * TS), "#eef2f5")

for yi, y in enumerate(range(y1, y2 + 1)):
    for xi, x in enumerate(range(x1, x2 + 1)):
        url = f"https://tile.openstreetmap.org/{ZOOM}/{x}/{y}.png"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            from io import BytesIO
            tile_img = Image.open(BytesIO(data)).convert("RGB")
            canvas.paste(tile_img, (xi * TS, yi * TS))
            print("OK", ZOOM, x, y)
        except Exception as e:
            print("FAIL", ZOOM, x, y, e)
        time.sleep(0.6)

png_path = os.path.join(OUT, "basemap_alfredo_chaves.png")
canvas.save(png_path, optimize=True)
print(f"Saved: {png_path} ({canvas.size})")

meta = {
    "zoom": ZOOM, "tile_size": TS,
    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
    "width_px": cols * TS, "height_px": rows * TS,
}
with open(os.path.join(OUT, "basemap_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)
print("Saved: basemap_meta.json ->", meta)
