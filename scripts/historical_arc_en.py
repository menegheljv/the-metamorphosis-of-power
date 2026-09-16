# -*- coding: utf-8 -*-
"""
English twin of historical_arc.py. Same data, translated chart text.
Produces output/en/chart_historical_arc.b64.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import base64
from io import BytesIO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
for _f in ["Anton-Regular.ttf", "BricolageGrotesque-Regular.ttf", "BricolageGrotesque-SemiBold.ttf", "BricolageGrotesque-Bold.ttf"]:
    _p = os.path.join(_FONT_DIR, _f)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams['font.family'] = 'Bricolage Grotesque'
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output", "en")
os.makedirs(OUT, exist_ok=True)

YEARS = [2004, 2008, 2012, 2016, 2020, 2024]

def read_secao(year):
    path = os.path.join(DATA, f"secao_{year}_alfredo_chaves.csv")
    df = pd.read_csv(path, sep=';', encoding='utf-8', dtype=str, quotechar='"')
    df.columns = [c.strip().upper() for c in df.columns]
    return df

rows = []
for year in YEARS:
    df = read_secao(year)
    pref = df[df["DS_CARGO"].str.strip().str.upper() == "PREFEITO"].copy()
    pref["QT_VOTOS"] = pd.to_numeric(pref["QT_VOTOS"], errors="coerce").fillna(0).astype(int)
    pref = pref[~pref["NM_VOTAVEL"].str.upper().isin(["VOTO BRANCO", "VOTO NULO"])]
    totals = pref.groupby("NM_VOTAVEL")["QT_VOTOS"].sum().sort_values(ascending=False)
    total_validos = int(totals.sum())
    winner = totals.index[0]
    winner_votes = int(totals.iloc[0])
    winner_pct = round(winner_votes / total_validos * 100, 1)
    runner_up = totals.index[1] if len(totals) > 1 else None
    runner_up_votes = int(totals.iloc[1]) if len(totals) > 1 else None
    runner_up_pct = round(runner_up_votes / total_validos * 100, 1) if runner_up_votes is not None else None
    our_group_won = year == 2024
    rows.append({
        "ano": year,
        "candidato_do_grupo": winner if our_group_won else runner_up,
        "pct_candidato_do_grupo": winner_pct if our_group_won else runner_up_pct,
        "resultado_do_grupo": "won" if our_group_won else "lost",
    })

summary = pd.DataFrame(rows)

BG = "#ffffff"
INK = "#333333"
MUTED = "#8f8f8f"
TITLE_GRAY = "#4d4d4d"
GRID = "#e2e2e2"
GREEN = "#5fd996"
RED = "#e2554c"

fig, ax = plt.subplots(figsize=(9, 5.2), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

x = summary["ano"].tolist()
y = summary["pct_candidato_do_grupo"].tolist()
colors = [RED if r == "lost" else GREEN for r in summary["resultado_do_grupo"]]

ax.plot(x, y, color=MUTED, linewidth=2, zorder=1)
ax.scatter(x, y, s=180, c=colors, zorder=2, edgecolors=BG, linewidths=1.5)

for xi, yi, name in zip(x, y, summary["candidato_do_grupo"]):
    label = f"{name.title()}\n{yi:.1f}%"
    ax.annotate(label, (xi, yi), textcoords="offset points", xytext=(0, 16),
                ha="center", fontsize=8.5, color=INK)

ax.set_xticks(x)
ax.set_xlim(x[0] - 1.6, x[-1] + 1.6)
ax.set_ylim(0, 70)
ax.set_ylabel("Vote share of the group's candidate, % of valid votes", color=INK)
ax.set_title("FIVE LOSSES AND THE TURNAROUND — MAYOR, ALFREDO CHAVES 2004–2024", fontsize=13, pad=14, color=TITLE_GRAY, fontweight="bold", fontfamily='Anton')
ax.tick_params(colors=MUTED)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(GRID)

plt.tight_layout()
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")

chart_path = os.path.join(OUT, "chart_historical_arc.b64")
with open(chart_path, "w", encoding="utf-8") as f:
    f.write(b64)
print(f"Saved: {chart_path}")
