# -*- coding: utf-8 -*-
"""Icone da pagina: silhueta de Alfredo Chaves (contorno oficial do IBGE) em verde.

Gera em frontend/public/: favicon.svg, favicon.ico, apple-touch-icon.png e icon-192.png.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parents[1]
PUBLIC = BASE / "frontend" / "public"
GREEN = "#1f9d63"

geo = json.loads((BASE / "data" / "ibge" / "malha_alfredo_chaves.geojson").read_text(encoding="utf-8"))
geom = geo["features"][0]["geometry"]
rings = [geom["coordinates"][0]] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]

lat0 = sum(y for r in rings for _, y in r) / sum(len(r) for r in rings)
k = math.cos(math.radians(lat0))
pts = [[(x * k, -y) for x, y in r] for r in rings]
xs = [x for r in pts for x, _ in r]
ys = [y for r in pts for _, y in r]
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
side = max(maxx - minx, maxy - miny)
pad = side * 0.06
size = side + 2 * pad
ox = minx - pad - (size - (maxx - minx) - 2 * pad) / 2
oy = miny - pad - (size - (maxy - miny) - 2 * pad) / 2


def norm(p, scale):
    return ((p[0] - ox) / size * scale, (p[1] - oy) / size * scale)


# SVG (viewBox 0 0 100 100)
paths = " ".join("M" + " L".join(f"{norm(p, 100)[0]:.2f},{norm(p, 100)[1]:.2f}" for p in r) + " Z" for r in pts)
(PUBLIC / "favicon.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="{paths}" fill="{GREEN}" '
    f'stroke="{GREEN}" stroke-width="1.2" stroke-linejoin="round"/></svg>\n', encoding="utf-8")


def raster(px: int, bg=None) -> Image.Image:
    ss = 8
    img = Image.new("RGBA", (px * ss, px * ss), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for r in pts:
        d.polygon([norm(p, px * ss) for p in r], fill=GREEN)
    return img.resize((px, px), Image.LANCZOS)


raster(48).save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
# icone de tela inicial: fundo claro da pagina e a silhueta com margem
base = Image.new("RGBA", (180, 180), "#faf9f7")
inner = raster(140)
base.alpha_composite(inner, (20, 20))
base.convert("RGB").save(PUBLIC / "apple-touch-icon.png")
big = Image.new("RGBA", (192, 192), "#faf9f7")
big.alpha_composite(raster(150), (21, 21))
big.convert("RGB").save(PUBLIC / "icon-192.png")
print("ok:", sorted(p.name for p in PUBLIC.iterdir()))
