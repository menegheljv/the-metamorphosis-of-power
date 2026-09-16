# -*- coding: utf-8 -*-
"""
Cross-references TSE electoral data with IBGE population and GDP data
for Alfredo Chaves, ES (IBGE code 3200300).
Produces:
  - output/ibge_cruzamento.csv (the merged table)
  - output/chart_ibge_eleitorado.b64 (electorate vs. population coverage)
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os, base64
from io import BytesIO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")
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
GREEN = "#5fd996"
MAUVE = "#caa0ac"

# ---------------------------------------------------------------------------
# IBGE population (SIDRA table 6579, annual estimates)
# ---------------------------------------------------------------------------
pop = pd.read_csv(os.path.join(DATA, "ibge", "populacao_estimada_alfredo_chaves.csv"), sep=";")
pop["ano"] = pop["ano"].astype(int)
pop_by_year = dict(zip(pop["ano"], pop["populacao_estimada"]))

def pop_for(year):
    if year in pop_by_year:
        return pop_by_year[year]
    # linear-interpolate from the two nearest years IBGE actually published
    years = sorted(pop_by_year.keys())
    lower = max([y for y in years if y < year], default=None)
    upper = min([y for y in years if y > year], default=None)
    if lower is None or upper is None:
        return None
    frac = (year - lower) / (upper - lower)
    return round(pop_by_year[lower] + frac * (pop_by_year[upper] - pop_by_year[lower]))

# ---------------------------------------------------------------------------
# TSE "aptos" (registered voters) per election, from detalhe_votacao files
# ---------------------------------------------------------------------------
YEARS = [2004, 2008, 2012, 2016, 2020, 2024]
rows = []
for year in YEARS:
    df = pd.read_csv(os.path.join(DATA, f"detalhe_votacao_{year}_alfredo_chaves.csv"), sep=";", dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    pref = df[df["DS_CARGO"].str.strip().str.upper() == "PREFEITO"]
    aptos = int(pref.iloc[0]["QT_APTOS"])
    p = pop_for(year)
    rows.append({
        "ano": year,
        "eleitores_aptos": aptos,
        "populacao_estimada_ibge": p,
        "pct_populacao_registrada": round(aptos / p * 100, 1) if p else None,
    })

cross = pd.DataFrame(rows)
cross_path = os.path.join(OUT, "ibge_cruzamento.csv")
cross.to_csv(cross_path, index=False)
print("=== Eleitorado apto vs. população estimada (IBGE), Alfredo Chaves ===")
print(cross.to_string(index=False))
print(f"\nSaved: {cross_path}")

# ---------------------------------------------------------------------------
# Chart: % of population registered to vote, 2004-2024
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

x = cross["ano"].tolist()
y = cross["pct_populacao_registrada"].tolist()

ax.plot(x, y, color=GREEN, linewidth=2.5, zorder=2, marker="o", markersize=9,
        markerfacecolor=GREEN, markeredgecolor=BG, markeredgewidth=1.5)
for xi, yi in zip(x, y):
    ax.annotate(f"{yi:.1f}%", (xi, yi), textcoords="offset points", xytext=(0, 14),
                ha="center", fontsize=10, color=INK)

ax.set_xticks(x)
ax.set_ylim(50, 100)
ax.set_ylabel("Eleitores aptos como % da população estimada (IBGE)", color=INK)
fig.text(0.5, 0.94, "O ELEITORADO CRESCEU, A POPULAÇÃO NÃO",
         fontsize=15, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.865, "Alfredo Chaves, ES. Cruzamento TSE (eleitores aptos) x IBGE (população estimada)",
         fontsize=10.5, color=MUTED, fontfamily="Anton", ha="center", va="top")
ax.tick_params(colors=MUTED)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(GRID)
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout(rect=[0, 0, 1, 0.82])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")

chart_path = os.path.join(OUT, "chart_ibge_eleitorado.b64")
with open(chart_path, "w", encoding="utf-8") as f:
    f.write(b64)
print(f"Saved: {chart_path}")
