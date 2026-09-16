# -*- coding: utf-8 -*-
"""
Analyzes the digital campaign's Instagram post history (@hugoluiz11_), from
the candidate's party affiliation (27/03/2024) through the post-election
thank-you post (06/10/2024), based on a set of post-by-post screenshots
supplied by the user (WhatsApp-exported PDFs of the account's post history)
manually reviewed and transcribed into data/campanha_digital_posts.csv.
This is NOT TSE data - it's the campaign's own social media archive,
disclosed as such in the case study text.

Produces:
  - output/campanha_digital_resumo.csv (per-phase aggregates)
  - output/chart_campanha_visualizacoes.b64 (views over time)
  - output/chart_campanha_engajamento.b64 (avg. engagement by phase)
"""
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
RED = "#e2554c"

df = pd.read_csv(os.path.join(DATA, "campanha_digital_posts.csv"), sep=";")
df["data"] = pd.to_datetime(df["data"])
df["engajamento"] = df["likes"] + df["comentarios"] + df["compartilhamentos"]
df = df.sort_values("data")

FASE_ORDER = ["filiacao", "pre-campanha", "lancamento", "campanha", "reta-final", "resultado"]
FASE_LABEL = {
    "filiacao": "Filiação (mar/24)",
    "pre-campanha": "Pré-campanha\n(abr-mai/24)",
    "lancamento": "Lançamento\n(jun/24)",
    "campanha": "Campanha\n(jul-ago/24)",
    "reta-final": "Reta final\n(set-out/24)",
    "resultado": "Resultado\n(06/10/24)",
}

resumo = df.groupby("fase").agg(
    posts=("data", "count"),
    views_total=("views", "sum"),
    views_media=("views", "mean"),
    engajamento_medio=("engajamento", "mean"),
).reindex(FASE_ORDER)
resumo_path = os.path.join(OUT, "campanha_digital_resumo.csv")
resumo.to_csv(resumo_path)
print("=== Resumo por fase ===")
print(resumo.round(0).to_string())
print(f"\nTotal de posts analisados: {len(df)}")
print(f"Views somadas: {int(df['views'].sum()):,}".replace(",", "."))
print(f"Engajamento medio geral: {df['engajamento'].mean():.0f}")
print(f"Post de maior engajamento: {df.loc[df['engajamento'].idxmax(), 'tema']} ({df['engajamento'].max()})")
print(f"Saved: {resumo_path}")

por_categoria = df.groupby("categoria").agg(
    posts=("data", "count"), views_media=("views", "mean"), engajamento_medio=("engajamento", "mean"),
).sort_values("posts", ascending=False)
print("\n=== Resumo por categoria de conteúdo ===")
print(por_categoria.round(0).to_string())

# ---------------------------------------------------------------------------
# Chart 1: views over time, colored by phase, with milestones annotated
# ---------------------------------------------------------------------------
FASE_COLOR = {
    "filiacao": "#3d7fc4", "pre-campanha": MUTED, "lancamento": "#c9781f",
    "campanha": RED, "reta-final": GREEN, "resultado": GREEN,
}

fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.scatter(df["data"], df["views"], s=32, color=GREEN, zorder=3)
ax.plot(df["data"], df["views"], color=GRID, linewidth=1, zorder=1)

milestones = [
    ("2024-03-27", "Filiação ao PP"),
    ("2024-06-07", "Lançamento da\npré-candidatura"),
    ("2024-08-03", "Anúncio do\nvice-prefeito"),
    ("2024-10-06", "Vitória"),
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

ax.set_ylabel("Visualizações por post", color=INK)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
ax.tick_params(colors=MUTED)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(GRID)
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
fig.text(0.5, 0.965, "DE 9,3 MIL A 41 MIL VISUALIZAÇÕES", fontsize=15, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.905, "Visualizações por post no Instagram, filiação (mar/24) até a vitória (06/10/24)", fontsize=10, color=MUTED, fontfamily="Anton", ha="center", va="top")
plt.tight_layout(rect=[0, 0, 1, 0.86])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")
with open(os.path.join(OUT, "chart_campanha_visualizacoes.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_campanha_visualizacoes.b64")

# ---------------------------------------------------------------------------
# Chart 2: average engagement (likes+comments+shares) by phase
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
ax.set_ylabel("Engajamento médio por post\n(curtidas + comentários + compartilhamentos)", color=INK, fontsize=10)
fig.text(0.5, 0.965, "O ENGAJAMENTO QUASE QUINTUPLICOU ATÉ O RESULTADO", fontsize=13.5, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.9, "Engajamento médio por fase da campanha (curtidas, comentários e compartilhamentos) — a fase de filiação tem apenas 1 post na amostra", fontsize=9.5, color=MUTED, fontfamily="Anton", ha="center", va="top")
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
    "evento": "Evento / caminhada", "administrativo": "Administrativo\n(vereador)",
    "coligacao": "Coligação / apoios", "proposta": "Proposta de governo",
    "pesquisa": "Pesquisa eleitoral", "testemunho": "Testemunho / depoimento",
    "resposta-ataque": "Resposta a ataque", "contagem-regressiva": "Contagem regressiva",
    "data-comemorativa": "Data comemorativa", "resultado": "Resultado", "marco": "Marco da campanha",
    "midia": "Repercussão na mídia", "filiacao": "Filiação",
}
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
ax1.set_xlabel("Número de posts", fontsize=9.5, color=INK)
ax1.set_title("O QUE FOI POSTADO", fontsize=11.5, fontweight="bold", fontfamily="Anton", color=MUTED, loc="left", pad=10)
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
ax2.set_xlabel("Engajamento médio por post", fontsize=9.5, color=INK)
ax2.set_title("O QUE MAIS ENGAJOU", fontsize=11.5, fontweight="bold", fontfamily="Anton", color=MUTED, loc="left", pad=10)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax2.spines[spine].set_color(GRID)
ax2.tick_params(colors=MUTED)
ax2.xaxis.grid(True, color=GRID, linewidth=0.7)
ax2.set_axisbelow(True)

fig.text(0.5, 0.985, "EVENTO DE RUA É O CONTEÚDO MAIS COMUM — MAS TESTEMUNHO ENGAJA MAIS", fontsize=12.5, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
plt.tight_layout(rect=[0, 0, 1, 0.92])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")
with open(os.path.join(OUT, "chart_campanha_categorias.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_campanha_categorias.b64")
