# -*- coding: utf-8 -*-
"""English twin of campanha_digital.py. Same data, translated chart text."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
RED = "#e2554c"

df = pd.read_csv(os.path.join(DATA, "campanha_digital_posts.csv"), sep=";")
df["data"] = pd.to_datetime(df["data"])
df["engajamento"] = df["likes"] + df["comentarios"] + df["compartilhamentos"]
df = df.sort_values("data")

FASE_ORDER = ["filiacao", "pre-campanha", "lancamento", "campanha", "reta-final", "resultado"]
FASE_LABEL = {
    "filiacao": "Affiliation\n(Mar/24)",
    "pre-campanha": "Pre-campaign\n(Apr-May/24)",
    "lancamento": "Launch\n(Jun/24)",
    "campanha": "Campaign\n(Jul-Aug/24)",
    "reta-final": "Home stretch\n(Sep-Oct/24)",
    "resultado": "Result\n(10/06/24)",
}

resumo = df.groupby("fase").agg(engajamento_medio=("engajamento", "mean")).reindex(FASE_ORDER)

FASE_COLOR = {
    "filiacao": "#3d7fc4", "pre-campanha": MUTED, "lancamento": "#c9781f",
    "campanha": RED, "reta-final": GREEN, "resultado": GREEN,
}

# ---------------------------------------------------------------------------
# Chart 1: views over time
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.scatter(df["data"], df["views"], s=32, color=GREEN, zorder=3)
ax.plot(df["data"], df["views"], color=GRID, linewidth=1, zorder=1)

milestones = [
    ("2024-03-27", "Affiliation to PP"),
    ("2024-06-07", "Pre-candidacy\nlaunch"),
    ("2024-08-03", "Running mate\nannounced"),
    ("2024-10-06", "Win"),
]
milestone_pts = []
for d, label in milestones:
    dt = pd.Timestamp(d)
    y = df.loc[(df["data"] - dt).abs().idxmin(), "views"]
    milestone_pts.append((dt, y))
    ax.annotate(label, (dt, y), textcoords="offset points", xytext=(0, 14), ha="center",
                fontsize=8, color=RED, fontweight="bold")

ms_x, ms_y = zip(*milestone_pts)
ax.scatter(ms_x, ms_y, s=90, color=RED, zorder=4, edgecolors=BG, linewidths=1.5)

ax.set_ylabel("Views per post", color=INK)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
ax.tick_params(colors=MUTED)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(GRID)
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
fig.text(0.5, 0.965, "FROM 9,300 TO 41,000 VIEWS PER POST", fontsize=15, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.905, "Views per Instagram post, from party affiliation (Mar/24) to the win (10/06/24)", fontsize=10, color=MUTED, fontfamily="Anton", ha="center", va="top")
plt.tight_layout(rect=[0, 0, 1, 0.86])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")
with open(os.path.join(OUT, "chart_campanha_visualizacoes.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_campanha_visualizacoes.b64")

# ---------------------------------------------------------------------------
# Chart 2: average engagement by phase
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5.4), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

x = range(len(FASE_ORDER))
vals = [resumo.loc[f, "engajamento_medio"] for f in FASE_ORDER]
bars = ax.bar(x, vals, color=GREEN, width=0.6)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 15, f"{v:.0f}", ha="center", fontsize=10, fontfamily="Bricolage Grotesque", color=INK)
ax.set_xticks(list(x))
ax.set_xticklabels([FASE_LABEL[f] for f in FASE_ORDER], fontsize=9)
ax.set_ylabel("Average engagement per post\n(likes + comments + shares)", color=INK, fontsize=10)
fig.text(0.5, 0.965, "ENGAGEMENT NEARLY QUINTUPLED BY THE RESULT", fontsize=13.5, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.9, "Average engagement by campaign phase (likes, comments and shares) — the affiliation phase has just 1 post in the sample", fontsize=9.5, color=MUTED, fontfamily="Anton", ha="center", va="top")
ax.tick_params(colors=MUTED)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(GRID)
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout(rect=[0, 0, 1, 0.84])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")
with open(os.path.join(OUT, "chart_campanha_engajamento.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_campanha_engajamento.b64")

# ---------------------------------------------------------------------------
# Chart 3: post count and average engagement by content category
# ---------------------------------------------------------------------------
CAT_LABEL = {
    "evento": "Event / walk", "administrativo": "Administrative\n(council)",
    "coligacao": "Coalition / endorsement", "proposta": "Policy proposal",
    "pesquisa": "Election poll", "testemunho": "Testimonial",
    "resposta-ataque": "Response to attack", "contagem-regressiva": "Countdown",
    "data-comemorativa": "Holiday post", "resultado": "Result", "marco": "Campaign milestone",
    "midia": "Press coverage", "filiacao": "Affiliation",
}
por_categoria = df.groupby("categoria").agg(
    posts=("data", "count"), engajamento_medio=("engajamento", "mean"),
).sort_values("posts", ascending=False)
cat_order = por_categoria.index.tolist()
GOLD = "#9c6b7a"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6), dpi=160)
fig.patch.set_facecolor(BG)
for ax in (ax1, ax2):
    ax.set_facecolor(BG)

y = range(len(cat_order))
ax1.barh(list(y), [por_categoria.loc[c, "posts"] for c in cat_order], color=MUTED, height=0.62)
ax1.set_yticks(list(y))
ax1.set_yticklabels([CAT_LABEL.get(c, c).split("\n")[0] for c in cat_order], fontsize=9.5)
ax1.invert_yaxis()
ax1.set_xlabel("Number of posts", fontsize=9.5, color=INK)
ax1.set_title("WHAT GOT POSTED", fontsize=11.5, fontweight="bold", fontfamily="Anton", color=MUTED, loc="left", pad=10)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax1.spines[spine].set_color(GRID)
ax1.tick_params(colors=MUTED)
ax1.xaxis.grid(True, color=GRID, linewidth=0.7)
ax1.set_axisbelow(True)

cat_order2 = por_categoria.sort_values("engajamento_medio", ascending=True).index.tolist()
y2 = range(len(cat_order2))
ax2.barh(list(y2), [por_categoria.loc[c, "engajamento_medio"] for c in cat_order2], color=GREEN, height=0.62)
ax2.set_yticks(list(y2))
ax2.set_yticklabels([CAT_LABEL.get(c, c).split("\n")[0] for c in cat_order2], fontsize=9.5)
ax2.set_xlabel("Average engagement per post", fontsize=9.5, color=INK)
ax2.set_title("WHAT ENGAGED MOST", fontsize=11.5, fontweight="bold", fontfamily="Anton", color=MUTED, loc="left", pad=10)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax2.spines[spine].set_color(GRID)
ax2.tick_params(colors=MUTED)
ax2.xaxis.grid(True, color=GRID, linewidth=0.7)
ax2.set_axisbelow(True)

fig.text(0.5, 0.985, "STREET EVENTS ARE THE MOST COMMON POST — BUT TESTIMONIALS ENGAGE MORE", fontsize=12, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
plt.tight_layout(rect=[0, 0, 1, 0.92])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")
with open(os.path.join(OUT, "chart_campanha_categorias.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_campanha_categorias.b64")
