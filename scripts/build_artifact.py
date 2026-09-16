# -*- coding: utf-8 -*-
import pandas as pd
import os
import json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")

with open(os.path.join(OUT, "template.html"), encoding="utf-8") as f:
    html = f.read()

chart_keys = ["historical_arc", "ibge_eleitorado", "slope", "grid", "municipio", "vereadores_2020", "vereadores_2024", "camara", "votos_vereadores",
              "financeiro_chapa", "custo_por_voto", "origem_receitas", "comparecimento",
              "genero_candidatos", "raca_candidatos",
              "campanha_visualizacoes", "campanha_engajamento", "campanha_categorias",
              "idade_candidatos", "patrimonio_candidatos", "pesquisas_timeline", "pesquisas_evolucao",
              "distritos_heatmap", "distritos_vereadores_heatmap", "coerencia_voto", "comparecimento_historico"]
for key in chart_keys:
    with open(os.path.join(OUT, f"chart_{key}.b64"), encoding="utf-8") as f:
        b64 = f.read().strip()
    placeholder = "{{CHART_%s}}" % key.upper()
    if placeholder not in html:
        print("WARNING: placeholder not found:", placeholder)
    html = html.replace(placeholder, b64)

# ---------------------------------------------------------------------
# tabela seção a seção (com local de votação)
# ---------------------------------------------------------------------
comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv")).sort_values("NR_SECAO")

def esc(s):
    if pd.isna(s):
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

rows = []
for _, r in comp.iterrows():
    is_flip = r.get('virou_de_derrota_para_vitoria') is True
    is_new = pd.isna(r['pct_2020'])
    cls = ' class="flip"' if is_flip else ''
    p2020 = "&mdash;" if pd.isna(r['pct_2020']) else f"{r['pct_2020']:.1f}%"
    p2024 = f"{r['pct_2024']:.1f}%"
    var = "&mdash;" if pd.isna(r['variacao_pp']) else f"{r['variacao_pp']:+.1f} p.p."
    local = esc(r.get('local_votacao', ''))
    if is_new:
        pill = '<span class="pill new">seção nova</span>'
    elif is_flip:
        pill = '<span class="pill win">virou</span>'
    else:
        pill = ''
    rows.append(
        f'<tr{cls}><td data-label="Seção">{int(r["NR_SECAO"])}</td><td data-label="Local">{local}</td>'
        f'<td data-label="% 2020">{p2020}</td><td data-label="% 2024">{p2024}</td>'
        f'<td data-label="Variação">{var}</td><td data-label="">{pill}</td></tr>'
    )

html = html.replace("{{TABLE_ROWS}}", "\n".join(rows))

# ---------------------------------------------------------------------
# tabela de locais de votação únicos
# ---------------------------------------------------------------------
locais = comp.dropna(subset=['local_votacao']).groupby(['local_votacao', 'endereco_votacao'])['NR_SECAO'].apply(
    lambda s: ', '.join(str(int(x)) for x in sorted(s))
).reset_index().sort_values('local_votacao')

locais = locais.reset_index(drop=True)
loc_rows = []
for i, r in locais.iterrows():
    loc_rows.append(
        f'<tr><td class="num">{i + 1}</td><td>{esc(r["local_votacao"])}</td><td>{esc(r["endereco_votacao"])}</td><td>{esc(r["NR_SECAO"])}</td></tr>'
    )
html = html.replace("{{TABLE_LOCAIS}}", "\n".join(loc_rows))

# ---------------------------------------------------------------------
# mapa interativo dos 18 locais de votação
# ---------------------------------------------------------------------
with open(os.path.join(BASE, "data", "locais_votacao_geocoded.csv"), encoding="utf-8") as f:
    geo = pd.read_csv(f)
with open(os.path.join(OUT, "basemap_meta.json"), encoding="utf-8") as f:
    meta = json.load(f)

import math
ZOOM, TS, X1, Y1 = meta["zoom"], meta["tile_size"], meta["x1"], meta["y1"]
W, H = meta["width_px"], meta["height_px"]

def deg2px(lat, lon):
    lat_rad = math.radians(lat)
    n = 2 ** ZOOM
    xtile = (lon + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n
    return (xtile - X1) * TS, (ytile - Y1) * TS

# order pins to match the numbered table above (same alphabetical order)
geo_by_local = {row["local_votacao"]: row for _, row in geo.iterrows()}
from collections import defaultdict
by_coord = defaultdict(list)
for i, r in locais.iterrows():
    g = geo_by_local[r["local_votacao"]]
    by_coord[(round(g["lat"], 5), round(g["lon"], 5))].append(i)

pins_js = []
for i, r in locais.iterrows():
    g = geo_by_local[r["local_votacao"]]
    px, py = deg2px(g["lat"], g["lon"])
    cluster = by_coord[(round(g["lat"], 5), round(g["lon"], 5))]
    if len(cluster) > 1:
        j = cluster.index(i)
        ang = 2 * math.pi * j / len(cluster)
        px += 52 * math.cos(ang)
        py += 52 * math.sin(ang)
    pct_x, pct_y = round(px / W * 100, 3), round(py / H * 100, 3)
    pins_js.append(
        '{n:%d,x:%s,y:%s,local:"%s",endereco:"%s",secoes:"%s"}' % (
            i + 1, pct_x, pct_y,
            r["local_votacao"].replace('"', "'"),
            str(r["endereco_votacao"]).replace('"', "'"),
            r["NR_SECAO"],
        )
    )
html = html.replace("{{MAP_PINS_JSON}}", "[" + ",".join(pins_js) + "]")

# ---------------------------------------------------------------------
# contorno oficial do município (IBGE malhas territoriais), sobreposto ao mapa
# ---------------------------------------------------------------------
with open(os.path.join(BASE, "data", "ibge", "malha_alfredo_chaves.geojson"), encoding="utf-8") as f:
    malha = json.load(f)
ring = malha["features"][0]["geometry"]["coordinates"][0]
boundary_pts = []
for lon, lat in ring:
    px, py = deg2px(lat, lon)
    boundary_pts.append(f"{px / W * 100:.3f},{py / H * 100:.3f}")
html = html.replace("{{BOUNDARY_POINTS}}", " ".join(boundary_pts))

with open(os.path.join(OUT, "basemap_alfredo_chaves.b64"), encoding="utf-8") as f:
    basemap_b64 = f.read().strip()
html = html.replace("{{BASEMAP_B64}}", basemap_b64)

final_path = os.path.join(OUT, "case_study.html")
with open(final_path, "w", encoding="utf-8") as f:
    f.write(html)

remaining = html.count("{{")
print("Written:", final_path)
print("Size (KB):", os.path.getsize(final_path) / 1024)
print("Unfilled placeholders remaining:", remaining)
