# -*- coding: utf-8 -*-
"""
Cross-references TSE candidate/electorate demographics (sex, race/color) with
IBGE Census 2022 municipal demographics (sex, race/color, per-capita income)
for Alfredo Chaves, ES (IBGE code 3200300).

IBGE source: Censo Demografico 2022, SIDRA tables 9514 (sex), 9605 (race/color)
and 10295 (mean/median per-capita household income by sex and race/color),
fetched via the SIDRA API (apisidra/servicodados.ibge.gov.br) and stored in
data/ibge/censo2022_alfredo_chaves.csv for auditability.

Produces:
  - output/genero_por_ano.csv, output/raca_candidatos.csv (intermediate tables)
  - output/chart_genero_candidatos.b64, output/chart_raca_candidatos.b64
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
RED = "#e2554c"
GREY = "#b7b7b7"

# ---------------------------------------------------------------------------
# 1) Eleitorado por genero, 2008-2024 (TSE, perfil_eleitor_secao)
# ---------------------------------------------------------------------------
YEARS_ELEITORADO = [2008, 2012, 2016, 2020, 2024]
rows = []
for year in YEARS_ELEITORADO:
    df = pd.read_csv(os.path.join(DATA, f"perfil_eleitorado_{year}_alfredo_chaves.csv"), sep=";", dtype=str, encoding="latin1")
    df.columns = [c.strip().upper() for c in df.columns]
    df["QT_ELEITORES_PERFIL"] = pd.to_numeric(df["QT_ELEITORES_PERFIL"], errors="coerce").fillna(0).astype(int)
    g = df.groupby("DS_GENERO")["QT_ELEITORES_PERFIL"].sum()
    tot = int(g.sum())
    m, f = int(g.get("MASCULINO", 0)), int(g.get("FEMININO", 0))
    rows.append({"ano": year, "homens": m, "mulheres": f, "total": tot,
                 "pct_mulheres": round(f / tot * 100, 1), "pct_homens": round(m / tot * 100, 1)})
genero_eleitorado = pd.DataFrame(rows)
genero_eleitorado.to_csv(os.path.join(OUT, "genero_por_ano.csv"), index=False)

# ---------------------------------------------------------------------------
# 2) Candidatos por genero e raca/cor, 2020 e 2024 (TSE, perfil_candidatos)
# ---------------------------------------------------------------------------
cand_rows = []
for year in [2020, 2024]:
    df = pd.read_csv(os.path.join(DATA, f"perfil_candidatos_{year}_alfredo_chaves.csv"), sep=";", dtype=str, encoding="latin1")
    df.columns = [c.strip().upper() for c in df.columns]
    tot = len(df)
    g = df.groupby("DS_GENERO").size()
    r = df.groupby("DS_COR_RACA").size()
    cand_rows.append({
        "ano": year, "total_candidatos": tot,
        "pct_mulheres": round(g.get("FEMININO", 0) / tot * 100, 1),
        "pct_branca": round(r.get("BRANCA", 0) / tot * 100, 1),
        "pct_parda": round(r.get("PARDA", 0) / tot * 100, 1),
        "pct_preta": round(r.get("PRETA", 0) / tot * 100, 1),
    })
cand_demog = pd.DataFrame(cand_rows)
cand_demog.to_csv(os.path.join(OUT, "raca_candidatos.csv"), index=False)

# ---------------------------------------------------------------------------
# 3) IBGE Censo 2022 (populacao do municipio)
# ---------------------------------------------------------------------------
censo = pd.read_csv(os.path.join(DATA, "ibge", "censo2022_alfredo_chaves.csv"), sep=";")
def censo_val(categoria, subcategoria):
    row = censo[(censo["categoria"] == categoria) & (censo["subcategoria"] == subcategoria)]
    return float(row["valor"].iloc[0]) if len(row) else None

pop_homens = censo_val("sexo", "homens")
pop_mulheres = censo_val("sexo", "mulheres")
pop_total = pop_homens + pop_mulheres
pop_pct_mulheres = round(pop_mulheres / pop_total * 100, 1)

pop_branca = censo_val("raca", "branca")
pop_preta = censo_val("raca", "preta")
pop_parda = censo_val("raca", "parda")
pop_raca_total = pop_branca + pop_preta + pop_parda + censo_val("raca", "amarela") + censo_val("raca", "indigena")
pop_pct_branca = round(pop_branca / pop_raca_total * 100, 1)
pop_pct_preta = round(pop_preta / pop_raca_total * 100, 1)
pop_pct_parda = round(pop_parda / pop_raca_total * 100, 1)

print("=== Censo 2022 (IBGE), Alfredo Chaves ===")
print(f"Populacao: {int(pop_total)} ({pop_pct_mulheres}% mulheres)")
print(f"Raca/cor: branca {pop_pct_branca}%, parda {pop_pct_parda}%, preta {pop_pct_preta}%")
print(f"\nEleitorado por ano:\n{genero_eleitorado.to_string(index=False)}")
print(f"\nCandidatos por ano:\n{cand_demog.to_string(index=False)}")

# ---------------------------------------------------------------------------
# Chart 1: % mulheres — populacao, eleitorado 2024, candidatos 2020, candidatos 2024
# ---------------------------------------------------------------------------
cats = ["Mulheres na\npopulação (2022)", "Mulheres no\neleitorado (2024)", "Candidatas\nem 2020", "Candidatas\nem 2024"]
vals = [pop_pct_mulheres,
        genero_eleitorado[genero_eleitorado["ano"] == 2024]["pct_mulheres"].iloc[0],
        cand_demog[cand_demog["ano"] == 2020]["pct_mulheres"].iloc[0],
        cand_demog[cand_demog["ano"] == 2024]["pct_mulheres"].iloc[0]]
colors = [GREY, GREY, RED, GREEN]

fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
bars = ax.bar(cats, vals, color=colors, width=0.55)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 1.3, f"{v:.1f}%", ha="center", fontsize=11, fontfamily="Bricolage Grotesque", color=INK)
ax.axhline(50, color=GRID, linestyle="--", linewidth=1, zorder=0)
ax.text(-0.35, 51.6, "50%", color=MUTED, fontsize=9, ha="left")
ax.set_ylim(0, 62)
ax.set_ylabel("% mulheres", color=INK)
fig.text(0.5, 0.955, "QUEM CONCORRE NÃO É QUEM VOTA", fontsize=15, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.885, "Participação feminina — população, eleitorado e candidatos, Alfredo Chaves", fontsize=10.5, color=MUTED, fontfamily="Anton", ha="center", va="top")
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
with open(os.path.join(OUT, "chart_genero_candidatos.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_genero_candidatos.b64")

# ---------------------------------------------------------------------------
# Chart 2: raca/cor — populacao vs candidatos 2020 vs candidatos 2024
# ---------------------------------------------------------------------------
grupos = ["Branca", "Parda", "Preta"]
pop_pcts = [pop_pct_branca, pop_pct_parda, pop_pct_preta]
c20 = cand_demog[cand_demog["ano"] == 2020].iloc[0]
c24 = cand_demog[cand_demog["ano"] == 2024].iloc[0]
c20_pcts = [c20["pct_branca"], c20["pct_parda"], c20["pct_preta"]]
c24_pcts = [c24["pct_branca"], c24["pct_parda"], c24["pct_preta"]]

x = range(len(grupos))
w = 0.26
fig, ax = plt.subplots(figsize=(9, 5.4), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
b1 = ax.bar([i - w for i in x], pop_pcts, width=w, color=GREY, label="População (IBGE 2022)")
b2 = ax.bar([i for i in x], c20_pcts, width=w, color=RED, label="Candidatos 2020")
b3 = ax.bar([i + w for i in x], c24_pcts, width=w, color=GREEN, label="Candidatos 2024")
for bars in [b1, b2, b3]:
    for bar in bars:
        v = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=8.5, color=INK)
ax.set_xticks(list(x))
ax.set_xticklabels(grupos, fontsize=11)
ax.set_ylabel("% do total", color=INK)
ax.set_ylim(0, 80)
fig.text(0.5, 0.955, "QUEM CONCORRE SE PARECE COM QUEM VIVE AQUI?", fontsize=14.5, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.895, "Raça ou cor declarada — população do município vs. candidatos a prefeito e vereador", fontsize=10.5, color=MUTED, fontfamily="Anton", ha="center", va="top")
ax.legend(loc="upper right", frameon=False, fontsize=9.5)
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
with open(os.path.join(OUT, "chart_raca_candidatos.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_raca_candidatos.b64")
