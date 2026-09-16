# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os as _os_early
_FONT_DIR = _os_early.path.join(_os_early.path.dirname(_os_early.path.abspath(__file__)), "fonts")
for _f in ["Anton-Regular.ttf", "BricolageGrotesque-Regular.ttf", "BricolageGrotesque-SemiBold.ttf", "BricolageGrotesque-Bold.ttf"]:
    _p = _os_early.path.join(_FONT_DIR, _f)
    if _os_early.path.exists(_p):
        fm.fontManager.addfont(_p)
import matplotlib.patches as mpatches
import os, base64, io, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")

with open(os.path.join(OUT, "candidate_profile_summary.json"), encoding="utf-8") as f:
    S = json.load(f)

BLUE = "#5fd996"
RED = "#e2554c"
GOLD = "#caa0ac"
GREY = "#8f8f8f"
TITLE_GRAY = "#4d4d4d"
BG = "#ffffff"
GRID = "#e2e2e2"
INK = "#333333"
COR_LADO = {"nossos": BLUE, "adversario": RED, "terceiro": "#3d7fc4"}

plt.rcParams.update({
    "font.family": "Bricolage Grotesque",
    "axes.edgecolor": GRID,
    "axes.linewidth": 0.8,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "legend.labelcolor": INK,
})

def fig_to_b64(fig, dpi=180):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('ascii')
    plt.close(fig)
    return b64

charts = {}

# =====================================================================
# CHART - Idade e patrimonio dos candidatos a prefeito, 2020 e 2024
# =====================================================================
cand2020 = [("Ronaldo Bianchi", 58, S['patrimonio_prefeito_2020'].get('RONALDO BIANCHI', 0), "nossos"),
            ("Fernando (Dr Fernando)", 73, S['patrimonio_prefeito_2020'].get('DR FERNANDO', 0), "adversario"),
            ("Armando Zanata", 64, S['patrimonio_prefeito_2020'].get('ARMANDO ZANATA', 0), "terceiro")]
cand2024 = [("Hugo Luiz", 25, S['patrimonio_prefeito_2024'].get('HUGO LUIZ', 0), "nossos"),
            ("Rolmar Boteccia", 71, S['patrimonio_prefeito_2024'].get('ROLMAR BOTECCHIA', 0), "adversario"),
            ("Boldrini", 61, S['patrimonio_prefeito_2024'].get('BOLDRINI', 0), "terceiro")]

fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
for ax, cands, ano in zip(axes, [cand2020, cand2024], [2020, 2024]):
    names = [c[0] for c in cands]
    ages = [c[1] for c in cands]
    colors = [COR_LADO[c[3]] for c in cands]
    bars = ax.barh(names, ages, color=colors, height=0.55)
    for bar, age in zip(bars, ages):
        ax.text(age + 1.5, bar.get_y()+bar.get_height()/2, f"{age} anos", va='center', fontsize=10, color=INK)
    ax.set_xlim(0, 85)
    ax.set_title(f"CANDIDATOS A PREFEITO — {ano}", fontsize=12, fontfamily='Bricolage Grotesque')
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='x', color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
fig.suptitle("IDADE DOS CANDIDATOS A PREFEITO — CANDIDATURA DO GRUPO EM VERDE, 3º COLOCADO EM AZUL", fontsize=13, fontweight='bold', fontfamily='Anton', color=TITLE_GRAY, y=1.03)
plt.tight_layout()
charts['idade_candidatos'] = fig_to_b64(fig)

# =====================================================================
# CHART - Patrimonio declarado por candidato a prefeito
# =====================================================================
fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
for ax, cands, ano in zip(axes, [cand2020, cand2024], [2020, 2024]):
    names = [c[0] for c in cands]
    pat = [c[2] for c in cands]
    colors = [COR_LADO[c[3]] for c in cands]
    bars = ax.barh(names, pat, color=colors, height=0.55)
    for bar, p in zip(bars, pat):
        ax.text(p + max(pat)*0.02, bar.get_y()+bar.get_height()/2, f"R$ {p:,.0f}".replace(",","."), va='center', fontsize=9.5, color=INK)
    ax.set_title(f"PATRIMÔNIO DECLARADO — {ano}", fontsize=12, fontfamily='Bricolage Grotesque')
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='x', color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    ax.set_xlim(0, max(max(c[2] for c in cand2020), max(c[2] for c in cand2024))*1.25)
fig.suptitle("PATRIMÔNIO DECLARADO DOS CANDIDATOS A PREFEITO — CANDIDATURA DO GRUPO EM VERDE, 3º COLOCADO EM AZUL", fontsize=13, fontweight='bold', fontfamily='Anton', color=TITLE_GRAY, y=1.03)
plt.tight_layout()
charts['patrimonio_candidatos'] = fig_to_b64(fig)

for k, b64 in charts.items():
    with open(os.path.join(OUT, f"chart_{k}.b64"), 'w') as f:
        f.write(b64)

print("Charts gerados:", list(charts.keys()))
