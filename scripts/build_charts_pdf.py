# -*- coding: utf-8 -*-
"""
Compiles every chart into a single reference PDF, one chart per page,
at high resolution (300 DPI source renders, output/hires/*.png --
produced by re-running each chart script under scripts/_hires_hook.py,
which re-rasterizes every figure at 300 DPI into output/hires/ without
touching the 160 DPI output/*.b64 files the website embeds).

Run `python3 scripts/build_hires_charts.py` first if output/hires/ is
missing or stale (e.g. after editing a chart script).

Embeds each PNG's pixels directly via Pillow's PDF writer instead of
routing through matplotlib's imshow(): imshow resamples the image onto
a new raster canvas at the figure's dpi, which softens fine text and
lines. Direct embedding keeps the exact source pixels, no
re-rasterization pass.

Usage: python3 scripts/build_charts_pdf.py
Produces: output/graficos.pdf
"""
import os

from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
HIRES = os.path.join(OUT, "hires")

# Physical DPI to report on each PDF page. This does NOT resample the
# image (Pillow embeds the source pixels as-is) -- it only sets how
# large the page prints/displays at 1:1, e.g. a 2700px-wide chart at
# 300 DPI yields a 9in-wide page -- roughly actual print size for
# these 300 DPI hi-res renders, never upsampling or downsampling a
# single pixel.
PDF_DPI = 300

# Curated order. Anything present in output/ but not listed here is
# skipped (basemap tiles, composite grids meant for internal review,
# etc.), not appended at the end, so a forgotten new chart fails loud
# instead of sneaking into the PDF.
CHARTS = [
    "chart_historical_arc.png",
    "chart_comparecimento_historico.png",
    "chart_ibge_eleitorado.png",
    "chart_comparecimento.png",
    "chart_campanha_visualizacoes.png",
    "chart_campanha_engajamento.png",
    "chart_campanha_categorias.png",
    "chart_coerencia_voto.png",
    "chart_slope.png",
    "chart_distritos_heatmap.png",
    "chart_municipio.png",
    "chart_financeiro_chapa.png",
    "chart_origem_receitas.png",
    "chart_custo_por_voto.png",
    "chart_camara.png",
    "chart_vereadores.png",
    "chart_vereadores_2020.png",
    "chart_vereadores_2024.png",
    "chart_votos_vereadores.png",
    "chart_pesquisas_timeline.png",
    "chart_pesquisas_evolucao.png",
    "chart_idade_candidatos.png",
    "chart_patrimonio_candidatos.png",
    "chart_genero_candidatos.png",
    "chart_raca_candidatos.png",
]

# Whitespace border added around every chart, as a fraction of that
# chart's own larger dimension -- so nothing ever touches the page
# edge (some charts had labels running right up to it) and bigger
# charts get proportionally bigger breathing room.
MARGIN_FRACTION = 0.06

out_path = os.path.join(OUT, "graficos.pdf")
images, written, missing = [], [], []

for fname in CHARTS:
    path = os.path.join(HIRES, fname)
    if not os.path.exists(path):
        missing.append(fname)
        continue
    chart = Image.open(path).convert("RGB")
    margin = round(max(chart.size) * MARGIN_FRACTION)
    padded = Image.new("RGB", (chart.width + 2 * margin, chart.height + 2 * margin), "white")
    padded.paste(chart, (margin, margin))
    images.append(padded)
    written.append(fname)

if not images:
    raise SystemExit("No chart images found -- run the chart scripts first.")

images[0].save(
    out_path, format="PDF", save_all=True, append_images=images[1:],
    resolution=PDF_DPI,
)

sizes = [f"{im.width}x{im.height}" for im in images]
print(f"Saved: {out_path}")
print(f"Pages written: {len(written)} (native pixel sizes: {min(sizes, key=len)} .. {max(sizes, key=len)})")
if missing:
    print("Missing (skipped):", missing)
