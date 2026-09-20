# -*- coding: utf-8 -*-
"""Fills the carousel_template.html with real chart b64 data, embeds the
project's local font files as base64 @font-face rules (no network
dependency, guarantees exact match with the case study), and writes
output/carousel.html, ready to be rendered to PDF via headless Chrome/Edge."""
import os, re, base64

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
FONT_DIR = os.path.join(BASE, "scripts", "fonts")

with open(os.path.join(OUT, "carousel_template.html"), encoding="utf-8") as f:
    html = f.read()

chart_keys = []  # no chart images in the native-visual redesign
for key in chart_keys:
    with open(os.path.join(OUT, f"chart_{key}.b64"), encoding="utf-8") as f:
        b64 = f.read().strip()
    html = html.replace("{{CHART_" + key.upper() + "}}", b64)

# ---- Embed local font files as base64 @font-face, replacing the Google Fonts @import ----
FONTS = [
    ("Anton",              400, "Anton-Regular.ttf"),
    ("Bricolage Grotesque", 400, "BricolageGrotesque-Regular.ttf"),
    ("Bricolage Grotesque", 600, "BricolageGrotesque-SemiBold.ttf"),
    ("Bricolage Grotesque", 700, "BricolageGrotesque-Bold.ttf"),
    ("IBM Plex Mono",       400, "IBMPlexMono-Regular.ttf"),
    ("IBM Plex Mono",       500, "IBMPlexMono-Medium.ttf"),
    ("IBM Plex Mono",       600, "IBMPlexMono-SemiBold.ttf"),
]
face_rules = []
for family, weight, fname in FONTS:
    with open(os.path.join(FONT_DIR, fname), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    face_rules.append(
        f"@font-face {{ font-family: '{family}'; font-weight: {weight}; font-style: normal; "
        f"src: url(data:font/ttf;base64,{b64}) format('truetype'); }}"
    )
font_css = "\n  ".join(face_rules)
html = re.sub(r"@import url\('https://fonts\.googleapis\.com[^']*'\);", font_css, html)

out_path = os.path.join(OUT, "carousel.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

remaining = html.count("{{")
print(f"Written: {out_path}")
print(f"Size (KB): {len(html) / 1024:.1f}")
print(f"Unfilled placeholders remaining: {remaining}")
