# -*- coding: utf-8 -*-
"""English twin of distritos_analysis.py. Same data, translated chart text.

Cross-references the group's vote share per precinct, across all six mayoral
elections (2004-2024), with which of Alfredo Chaves' 7 official districts
each precinct belongs to - via its 2024 polling location, mapped to
district using the city hall's own locality list
(alfredochaves.es.gov.br/detalhe-da-materia/info/6517/localidades-e-distancia).

Produces:
  - output/en/chart_distritos_heatmap.b64
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
import os, base64
from io import BytesIO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT_PT = os.path.join(BASE, "output")
OUT = os.path.join(BASE, "output", "en")
os.makedirs(OUT, exist_ok=True)

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
for _f in ["Anton-Regular.ttf", "BricolageGrotesque-Regular.ttf", "BricolageGrotesque-SemiBold.ttf", "BricolageGrotesque-Bold.ttf"]:
    _p = os.path.join(_FONT_DIR, _f)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams["font.family"] = "Bricolage Grotesque"

BG = "#ffffff"
INK = "#333333"
MUTED = "#8f8f8f"
TITLE_GRAY = "#4d4d4d"
GRID = "#e2e2e2"

# ---------------------------------------------------------------------------
# 1) precinct -> polling location (2024) -> district
# ---------------------------------------------------------------------------
comp = pd.read_csv(os.path.join(OUT_PT, "comparativo_candidato_prefeito_por_secao.csv"))
comp["local_votacao"] = comp["local_votacao"].str.strip()
secao_local = dict(zip(comp["NR_SECAO"], comp["local_votacao"]))

dist_map = pd.read_csv(os.path.join(DATA, "distritos_mapping.csv"), sep=";")
dist_map["local_votacao"] = dist_map["local_votacao"].str.strip()
local_distrito = dict(zip(dist_map["local_votacao"], dist_map["distrito"]))

def distrito_for_secao(nr_secao):
    local = secao_local.get(nr_secao)
    if local is None:
        return None
    return local_distrito.get(local)

# ---------------------------------------------------------------------------
# 2) per-precinct group vote share, all six elections
# ---------------------------------------------------------------------------
YEARS = [2004, 2008, 2012, 2016, 2020, 2024]
GROUP_CANDIDATE = {
    2004: "JORGE GABRIEL MENEGHEL", 2008: "DANIEL ORLANDI", 2012: "SERGIO BIANCHI",
    2016: "RONALDO BIANCHI", 2020: "RONALDO BIANCHI", 2024: "HUGO LUIZ PICOLI MENEGHEL",
}

rows = []
for year in YEARS:
    df = pd.read_csv(os.path.join(DATA, f"secao_{year}_alfredo_chaves.csv"), sep=";", encoding="utf-8", dtype=str, quotechar='"')
    df.columns = [c.strip().upper() for c in df.columns]
    pref = df[df["DS_CARGO"].str.strip().str.upper() == "PREFEITO"].copy()
    pref["QT_VOTOS"] = pd.to_numeric(pref["QT_VOTOS"], errors="coerce").fillna(0).astype(int)
    pref["NR_SECAO"] = pd.to_numeric(pref["NR_SECAO"], errors="coerce")
    pref = pref.dropna(subset=["NR_SECAO"])
    pref["NR_SECAO"] = pref["NR_SECAO"].astype(int)
    pref = pref[~pref["NM_VOTAVEL"].str.upper().isin(["VOTO BRANCO", "VOTO NULO"])]

    cand_name = GROUP_CANDIDATE[year]
    for secao, g in pref.groupby("NR_SECAO"):
        total = g["QT_VOTOS"].sum()
        if total == 0:
            continue
        grupo_votos = g[g["NM_VOTAVEL"].str.upper() == cand_name]["QT_VOTOS"].sum()
        pct = round(grupo_votos / total * 100, 1)
        distrito = distrito_for_secao(secao)
        rows.append({"ano": year, "secao": secao, "pct_grupo": pct, "total_votos": total, "distrito": distrito})

full = pd.DataFrame(rows)
matched = full.dropna(subset=["distrito"])

# ---------------------------------------------------------------------------
# 3) aggregate: average group % per district per year, weighted by total votes
# ---------------------------------------------------------------------------
def wavg(g):
    return (g["pct_grupo"] * g["total_votos"]).sum() / g["total_votos"].sum()

agg = matched.groupby(["distrito", "ano"]).apply(wavg, include_groups=False).reset_index(name="pct_grupo_pond")
pivot = agg.pivot(index="distrito", columns="ano", values="pct_grupo_pond")

DISTRITO_ORDER = ["Sede", "Crubixá", "Ibitiruí", "Matilde", "Ribeirão do Cristo", "Sagrada Família", "São Bento de Urânia"]
DISTRITO_LABEL_EN = {
    "Sede": "Seat (town)", "Crubixá": "Crubixá", "Ibitiruí": "Ibitiruí", "Matilde": "Matilde",
    "Ribeirão do Cristo": "Ribeirão do Cristo", "Sagrada Família": "Sagrada Família",
    "São Bento de Urânia": "São Bento de Urânia",
}
pivot = pivot.reindex(DISTRITO_ORDER)
labels_en = [DISTRITO_LABEL_EN[d] for d in DISTRITO_ORDER]

# ---------------------------------------------------------------------------
# Chart: heatmap, districts x years, diverging red (adversary) - green (group)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.5, 6), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

cmap = mcolors.LinearSegmentedColormap.from_list("redgreen", ["#c8433a", "#f5efe8", "#1f9d63"])
norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=50, vmax=100)

data = pivot.values
im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")

for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        v = data[i, j]
        if pd.isna(v):
            ax.text(j, i, "no\ndata", ha="center", va="center", fontsize=8, color=MUTED)
        else:
            txt_color = "white" if (v < 25 or v > 75) else INK
            ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=11, fontfamily="Bricolage Grotesque", color=txt_color)

ax.set_xticks(range(len(YEARS)))
ax.set_xticklabels(YEARS, fontsize=10.5)
ax.set_yticks(range(len(DISTRITO_ORDER)))
ax.set_yticklabels(labels_en, fontsize=10.5)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_xticks([x - 0.5 for x in range(1, len(YEARS))], minor=True)
ax.set_yticks([y - 0.5 for y in range(1, len(DISTRITO_ORDER))], minor=True)
ax.grid(which="minor", color=BG, linewidth=3)

fig.text(0.5, 0.97, "WHERE THE GROUP WAS STRONG, WHERE IT WAS WEAK", fontsize=15, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.915, "% of the group's mayoral candidate, by district, 2004–2024 (weighted average by each district's precinct valid votes)", fontsize=10, color=MUTED, fontfamily="Anton", ha="center", va="top")
plt.tight_layout(rect=[0, 0, 1, 0.88])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")
with open(os.path.join(OUT, "chart_distritos_heatmap.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: en/chart_distritos_heatmap.b64")
