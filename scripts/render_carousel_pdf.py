# -*- coding: utf-8 -*-
"""Splits output/carousel.html into 9 standalone single-slide HTML files,
screenshots each one at exactly 1080x1080 via headless Chrome, and combines
the 9 PNGs into output/carousel.pdf (one page per slide, no CSS pagination
involved -> pixel-perfect and reliable).
"""
import os, re, subprocess, sys
from bs4 import BeautifulSoup
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
SLIDES_DIR = os.path.join(OUT, "carousel_slides")
os.makedirs(SLIDES_DIR, exist_ok=True)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"C:\Users\Usuario\AppData\Local\Temp\claude\chrome_profile_carousel_render"

with open(os.path.join(OUT, "carousel.html"), encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

style_tag = str(soup.find("style"))
slides = soup.select(".slide")
print(f"Found {len(slides)} slides")

png_paths = []
for i, slide in enumerate(slides, start=1):
    slide_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1080px; overflow:hidden; }}
{style_tag[len('<style>'):-len('</style>')]}
</style></head>
<body>{str(slide)}</body></html>"""
    html_path = os.path.join(SLIDES_DIR, f"slide_{i:02d}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(slide_html)

    png_path = os.path.join(SLIDES_DIR, f"slide_{i:02d}.png")
    win_html_path = html_path  # already a Windows path since BASE is Windows-style
    subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        f"--user-data-dir={PROFILE}",
        "--window-size=1080,1080", "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--screenshot={png_path}",
        "--virtual-time-budget=4000",
        f"file:///{win_html_path.replace(os.sep, '/')}",
    ], capture_output=True, timeout=30)
    png_paths.append(png_path)
    print(f"  slide {i}: {'OK' if os.path.exists(png_path) else 'MISSING'}")

# Combine into one PDF
imgs = [Image.open(p).convert("RGB") for p in png_paths]
pdf_path = os.path.join(OUT, "carousel.pdf")
imgs[0].save(pdf_path, save_all=True, append_images=imgs[1:])
print(f"Written: {pdf_path} ({len(imgs)} pages)")
