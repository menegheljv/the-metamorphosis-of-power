# -*- coding: utf-8 -*-
"""
English twin of ibge_cruzamento.py. Same data, translated chart text.
Produces output/en/chart_ibge_eleitorado.b64.
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
GREEN = "#5fd996"

pop = pd.read_csv(os.path.join(DATA, "ibge", "populacao_estimada_alfredo_chaves.csv"), sep=";")
pop["ano"] = pop["ano"].astype(int)
pop_by_year = dict(zip(pop["ano"], pop["populacao_estimada"]))

def pop_for(year):
    if year in pop_by_year:
        return pop_by_year[year]
    years = sorted(pop_by_year.keys())
    lower = max([y for y in years if y < year], default=None)
    upper = min([y for y in years if y > year], default=None)
    if lower is None or upper is None:
        return None
    frac = (year - lower) / (upper - lower)
    return round(pop_by_year[lower] + frac * (pop_by_year[upper] - pop_by_year[lower]))

YEARS = [2004, 2008, 2012, 2016, 2020, 2024]
rows = []
for year in YEARS:
    df = pd.read_csv(os.path.join(DATA, f"detalhe_votacao_{year}_alfredo_chaves.csv"), sep=";", dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    pref = df[df["DS_CARGO"].str.strip().str.upper() == "PREFEITO"]
    aptos = int(pref.iloc[0]["QT_APTOS"])
    p = pop_for(year)
    rows.append({"ano": year, "pct_populacao_registrada": round(aptos / p * 100, 1) if p else None})

cross = pd.DataFrame(rows)

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
ax.set_ylabel("Registered voters as % of estimated population (IBGE)", color=INK)
fig.text(0.5, 0.94, "THE ELECTORATE GREW, THE POPULATION DIDN'T",
         fontsize=15, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.865, "Alfredo Chaves, Brazil. TSE (registered voters) x IBGE (estimated population)",
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
