# -*- coding: utf-8 -*-
"""Coerencia de voto (ticket consistency): per precinct, does the % that voted
for the group's mayoral candidate track the % that voted for the group's
council candidates? Compares that correlation in 2020 (Ronaldo Bianchi) vs.
2024 (Hugo Luiz).

Produces:
  - output/en/coerencia_voto.csv (per-precinct pct_prefeito_nosso, pct_vereador_nosso, ano)
  - output/en/chart_coerencia_voto.b64 (scatter, 2020 vs 2024, with trend lines)
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
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
GREEN = "#1f9d63"
GREEN_DEEP = "#157a4d"
RED = "#c8433a"

PREFEITO_NOSSO = {2020: "RONALDO BIANCHI", 2024: "HUGO LUIZ PICOLI MENEGHEL"}
NOSSOS_PARTIDOS = {2020: {"PTB", "REPUBLICANOS", "PATRIOTA"}, 2024: {"REPUBLICANOS", "PP", "PSDB"}}

def per_precinct(year):
    sec = pd.read_csv(os.path.join(DATA, f"secao_{year}_alfredo_chaves.csv"), sep=";", encoding="utf-8", dtype=str, quotechar='"')
    sec.columns = [c.strip().upper() for c in sec.columns]
    sec["QT_VOTOS"] = pd.to_numeric(sec["QT_VOTOS"], errors="coerce").fillna(0).astype(int)
    sec["NR_SECAO"] = pd.to_numeric(sec["NR_SECAO"], errors="coerce")
    sec = sec.dropna(subset=["NR_SECAO"])
    sec["NR_SECAO"] = sec["NR_SECAO"].astype(int)
    sec["NM_VOTAVEL"] = sec["NM_VOTAVEL"].str.strip().str.upper()
    sec["DS_CARGO"] = sec["DS_CARGO"].str.strip().str.upper()

    # candidato -> partido, para os candidatos a vereador desse ano
    cand_all = pd.read_csv(os.path.join(DATA, f"candidatos_{year}_alfredo_chaves.csv"), sep=";", encoding="utf-8", dtype=str, quotechar='"')
    cand_all.columns = [c.strip().upper() for c in cand_all.columns]
    cand = cand_all[cand_all["DS_CARGO"].str.strip().str.upper() == "VEREADOR"].copy()
    cand["NM_CANDIDATO"] = cand["NM_CANDIDATO"].str.strip().str.upper()
    partido_by_name = dict(zip(cand["NM_CANDIDATO"], cand["SG_PARTIDO"].str.strip().str.upper()))
    # voto de legenda: NM_VOTAVEL vem com o nome completo do partido, não um candidato -
    # mapeamos NM_PARTIDO (nome completo) -> SG_PARTIDO pra também classificar essas linhas
    partido_full_to_sg = dict(zip(
        cand["NM_PARTIDO"].str.strip().str.upper(), cand["SG_PARTIDO"].str.strip().str.upper()
    ))
    partido_by_name.update(partido_full_to_sg)

    # --- prefeito: % do candidato do grupo, por seção ---
    pref = sec[(sec["DS_CARGO"] == "PREFEITO") & (~sec["NM_VOTAVEL"].isin(["VOTO BRANCO", "VOTO NULO"]))]
    pref_rows = []
    for secao, g in pref.groupby("NR_SECAO"):
        total = g["QT_VOTOS"].sum()
        if total == 0:
            continue
        nosso = g[g["NM_VOTAVEL"] == PREFEITO_NOSSO[year]]["QT_VOTOS"].sum()
        pref_rows.append({"secao": secao, "pct_prefeito_nosso": nosso / total * 100})
    df_pref = pd.DataFrame(pref_rows)

    # --- vereador: % dos candidatos do grupo (soma), por seção ---
    ver = sec[(sec["DS_CARGO"] == "VEREADOR") & (~sec["NM_VOTAVEL"].isin(["VOTO BRANCO", "VOTO NULO"]))].copy()
    ver["PARTIDO"] = ver["NM_VOTAVEL"].map(partido_by_name)
    ver["NOSSO"] = ver["PARTIDO"].isin(NOSSOS_PARTIDOS[year])
    ver_rows = []
    unmatched = set(ver.loc[ver["PARTIDO"].isna(), "NM_VOTAVEL"].unique())
    for secao, g in ver.groupby("NR_SECAO"):
        total = g["QT_VOTOS"].sum()
        if total == 0:
            continue
        nosso = g[g["NOSSO"]]["QT_VOTOS"].sum()
        ver_rows.append({"secao": secao, "pct_vereador_nosso": nosso / total * 100})
    df_ver = pd.DataFrame(ver_rows)
    if unmatched:
        print(f"{year}: candidatos a vereador sem partido casado (excluidos do lado 'nossos'): {sorted(unmatched)}")

    out = df_pref.merge(df_ver, on="secao", how="inner")
    out["ano"] = year
    return out

df2020 = per_precinct(2020)
df2024 = per_precinct(2024)
full = pd.concat([df2020, df2024], ignore_index=True)
full.to_csv(os.path.join(OUT, "coerencia_voto.csv"), index=False)

r2020 = df2020["pct_prefeito_nosso"].corr(df2020["pct_vereador_nosso"])
r2024 = df2024["pct_prefeito_nosso"].corr(df2024["pct_vereador_nosso"])
print(f"2020: n={len(df2020)} precincts, correlation (Pearson r) = {r2020:.3f}")
print(f"2024: n={len(df2024)} precincts, correlation (Pearson r) = {r2024:.3f}")
print(f"R² 2020 = {r2020**2:.3f}   R² 2024 = {r2024**2:.3f}")

# ---------------------------------------------------------------------------
# Chart: scatter + trend line, 2020 vs 2024, side by side
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), dpi=160, sharey=True, sharex=True)
fig.patch.set_facecolor(BG)

for ax, df, year, color, r in zip(axes, [df2020, df2024], [2020, 2024], [RED, GREEN_DEEP], [r2020, r2024]):
    ax.set_facecolor(BG)
    ax.scatter(df["pct_prefeito_nosso"], df["pct_vereador_nosso"], s=46, color=color, alpha=0.75, edgecolor="white", linewidth=0.6, zorder=3)
    if len(df) > 1:
        m, b = np.polyfit(df["pct_prefeito_nosso"], df["pct_vereador_nosso"], 1)
        xs = np.array([df["pct_prefeito_nosso"].min(), df["pct_prefeito_nosso"].max()])
        ax.plot(xs, m * xs + b, color=INK, linewidth=1.6, linestyle="--", zorder=2, alpha=0.6)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel(f"% of valid votes for the group's mayoral candidate, {year}", fontsize=10, color=INK)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(GRID)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.text(0.05, 0.94, f"r = {r:.2f}  (R² = {r*r:.2f})", transform=ax.transAxes, fontsize=12, fontfamily="Bricolage Grotesque", color=color, va="top")

axes[0].set_ylabel("% of valid votes for the group's council candidates, same precinct", fontsize=10, color=INK)

fig.text(0.5, 0.99, "IN 2020, THE MAYOR AND COUNCIL VOTE MOVED TOGETHER. IN 2024, LESS SO.", fontsize=14.5, color=TITLE_GRAY, fontweight="bold", fontfamily="Anton", ha="center", va="top")
fig.text(0.5, 0.935, "Each point is one precinct: valid votes for mayor vs. for the group's council candidates", fontsize=9.5, color=MUTED, fontfamily="Anton", ha="center", va="top")
plt.tight_layout(rect=[0, 0, 1, 0.89])
buf = BytesIO()
plt.savefig(buf, format="png", facecolor=BG)
plt.close(fig)
b64 = base64.b64encode(buf.getvalue()).decode("ascii")
with open(os.path.join(OUT, "chart_coerencia_voto.b64"), "w", encoding="utf-8") as f:
    f.write(b64)
print("Saved: chart_coerencia_voto.b64")
