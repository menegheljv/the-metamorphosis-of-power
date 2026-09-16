# -*- coding: utf-8 -*-
"""
English twin of distritos_vereadores.py. Same data, translated chart text.
Produces output/en/chart_distritos_vereadores_heatmap.b64.
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
OUT = os.path.join(BASE, "output")
OUT_EN = os.path.join(BASE, "output", "en")
os.makedirs(OUT_EN, exist_ok=True)

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

comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
comp["local_votacao"] = comp["local_votacao"].str.strip()
secao_local = dict(zip(comp["NR_SECAO"], comp["local_votacao"]))

dist_map = pd.read_csv(os.path.join(DATA, "distritos_mapping.csv"), sep=";", encoding="utf-8")
dist_map["local_votacao"] = dist_map["local_votacao"].str.strip()
local_distrito = dict(zip(dist_map["local_votacao"], dist_map["distrito"]))

def distrito_for_secao(nr):
    local = secao_local.get(nr)
    return local_distrito.get(local) if local else None

YEARS = [2020, 2024]
NOSSOS = {2020: {"PTB", "REPUBLICANOS", "PATRIOTA"}, 2024: {"REPUBLICANOS", "PP", "PSDB"}}

all_rows, grp_rows = [], []
for year in YEARS:
    cand = pd.read_csv(os.path.join(DATA, f"candidatos_{year}_alfredo_chaves.csv"), sep=";", encoding="utf-8", dtype=str)
    cand.columns = [c.strip().upper() for c in cand.columns]
    cver = cand[cand["DS_CARGO"].str.strip().str.upper() == "VEREADOR"]
    grupo_sq = set(cver[cver["SG_PARTIDO"].isin(NOSSOS[year])]["SQ_CANDIDATO"].astype(str))

    df = pd.read_csv(os.path.join(DATA, f"secao_{year}_alfredo_chaves.csv"), sep=";", encoding="utf-8", dtype=str, quotechar='"')
    df.columns = [c.strip().upper() for c in df.columns]
    ver = df[df["DS_CARGO"].str.strip().str.upper() == "VEREADOR"].copy()
    ver["SQ_CANDIDATO"] = ver["SQ_CANDIDATO"].astype(str).str.strip()
    ver["QT_VOTOS"] = pd.to_numeric(ver["QT_VOTOS"], errors="coerce").fillna(0).astype(int)
    ver["NR_SECAO"] = pd.to_numeric(ver["NR_SECAO"], errors="coerce")
    ver = ver[~ver["NM_VOTAVEL"].str.strip().str.upper().isin(["VOTO BRANCO", "VOTO NULO"])]
    ver["distrito"] = ver["NR_SECAO"].apply(distrito_for_secao)
    ver["Ano"] = year

    all_rows.append(ver[["distrito", "Ano", "QT_VOTOS"]])
    grp_rows.append(ver[ver["SQ_CANDIDATO"].isin(grupo_sq)][["distrito", "Ano", "QT_VOTOS"]])

allv = pd.concat(all_rows, ignore_index=True)
grp = pd.concat(grp_rows, ignore_index=True)

tot = allv.groupby(["distrito", "Ano"])["QT_VOTOS"].sum().unstack(fill_value=0)
gvo = grp.groupby(["distrito", "Ano"])["QT_VOTOS"].sum().unstack(fill_value=0)
pct = (gvo / tot * 100).round(1)

DISTRITO_ORDER = ["Sede", "Crubixá", "Ibitiruí", "Matilde", "Ribeirão do Cristo", "Sagrada Família", "São Bento de Urânia"]
pct = pct.reindex(DISTRITO_ORDER)

fig, ax = plt.subplots(figsize=(6.2, 6), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

cmap = mcolors.LinearSegmentedColormap.from_list("redgreen", ["#c8433a", "#f5efe8", "#1f9d63"])
norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=50, vmax=100)

data = pct.values
im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")

for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        v = data[i, j]
        if pd.isna(v):
            ax.text(j, i, "no\ndata", ha="center", va="center", fontsize=8, color=MUTED)
        else:
            txt_color = "white" if (v < 25 or v > 75) else INK
            ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=12, fontfamily="Bricolage Grotesque", color=txt_color)

ax.set_xticks(range(len(YEARS)))
ax.set_xticklabels(YEARS, fontsize=11)
ax.set_yticks(range(len(DISTRITO_ORDER)))
ax.set_yticklabels(DISTRITO_ORDER, fontsize=11)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_xticks([x - 0.5 for x in range(1, len(YEARS))], minor=True)
ax.set_yticks([y - 0.5 for y in range(1, len(DISTRITO_ORDER))], minor=True)
ax.grid(which="minor", color=BG, linewidth=3)

fig.text(0.5, 0.97, "WHERE THE COUNCIL SLATE WAS STRONG", fontsize=14.5, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.905, "% of council votes for the group's slate, by district, 2020 and 2024", fontsize=9.5, color=MUTED, fontfamily="Anton", ha="center", va="top")
plt.tight_layout(rect=[0, 0, 1, 0.86])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")

chart_path = os.path.join(OUT_EN, "chart_distritos_vereadores_heatmap.b64")
with open(chart_path, "w", encoding="utf-8") as f:
    f.write(b64)
print(f"Saved: {chart_path}")
