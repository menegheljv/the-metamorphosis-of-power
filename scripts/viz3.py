# -*- coding: utf-8 -*-
import pandas as pd
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

with open(os.path.join(OUT, "extra_summary.json"), encoding="utf-8") as f:
    S = json.load(f)

BLUE = "#5fd996"
BLUE_TINT = "#1f3d2f"
RED = "#e2554c"
GOLD = "#caa0ac"
GREY = "#8f8f8f"
TITLE_GRAY = "#4d4d4d"
BG = "#ffffff"
GRID = "#e2e2e2"
INK = "#333333"

plt.rcParams.update({
    "font.family": "Bricolage Grotesque",
    "axes.edgecolor": GRID,
    "axes.linewidth": 0.8,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.titlecolor": TITLE_GRAY,
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
# CHART 1 - Receita declarada, TODOS os candidatos a prefeito (2020 e 2024)
# =====================================================================
# terceiro elemento: "nossos" | "adversario" | "terceiro" (candidato minoritario, sempre GOLD)
cand2020 = [("Fernando\n(PSB — eleito)", 108642.29, "adversario"),
            ("Bianchi\n(Republicanos)", 53120.00, "nossos"),
            ("Zanata\n(PDT)", 32722.09, "terceiro")]
cand2024 = [("Hugo Luiz\n(PP — eleito)", 155597.43, "nossos"),
            ("Boteccia\n(PSB)", 119400.00, "adversario"),
            ("Boldrini\n(PL)", 141130.00, "terceiro")]

COR_LADO = {"nossos": BLUE, "adversario": RED, "terceiro": "#3d7fc4"}

fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4), sharey=False)
for ax, cands, ano in zip(axes, [cand2020, cand2024], [2020, 2024]):
    cands_sorted = sorted(cands, key=lambda c: c[1])
    names = [c[0] for c in cands_sorted]
    vals = [c[1] for c in cands_sorted]
    colors = [COR_LADO[c[2]] for c in cands_sorted]
    bars = ax.barh(names, vals, color=colors, height=0.55)
    for bar, v in zip(bars, vals):
        ax.text(v + max(vals)*0.02, bar.get_y()+bar.get_height()/2, f"R$ {v:,.0f}".replace(",", "."),
                 va='center', fontsize=9.5, fontfamily='Bricolage Grotesque', color=INK)
    ax.set_title(f"RECEITA DECLARADA — {ano}", fontsize=12, fontfamily='Bricolage Grotesque')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(vals)*1.32)
fig.suptitle("FINANCIAMENTO DAS CAMPANHAS A PREFEITO — TODOS OS CANDIDATOS\nALFREDO CHAVES (ES) · CANDIDATURA DO GRUPO EM VERDE, PRINCIPAL ADVERSÁRIO EM VERMELHO, 3º COLOCADO EM AZUL",
             fontsize=12.5, fontweight='bold', fontfamily='Anton', y=1.05)
plt.tight_layout()
charts['financeiro_chapa'] = fig_to_b64(fig)

# =====================================================================
# CHART 2 - Custo por voto, TODOS os candidatos a prefeito (2020 e 2024)
# =====================================================================
cvcand2020 = [("Fernando\n5.196 votos", 102342.29/5196, "adversario"),
              ("Bianchi\n3.681 votos", 50000.00/3681, "nossos"),
              ("Zanata\n336 votos", 26999.56/336, "terceiro")]
cvcand2024 = [("Hugo Luiz\n5.779 votos", 154237.43/5779, "nossos"),
              ("Boteccia\n3.177 votos", 115000.00/3177, "adversario"),
              ("Boldrini\n999 votos", 141130.00/999, "terceiro")]

fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4), sharey=False)
for ax, cands, ano in zip(axes, [cvcand2020, cvcand2024], [2020, 2024]):
    cands_sorted = sorted(cands, key=lambda c: c[1])
    names = [c[0] for c in cands_sorted]
    vals = [c[1] for c in cands_sorted]
    colors = [COR_LADO[c[2]] for c in cands_sorted]
    bars = ax.barh(names, vals, color=colors, height=0.55)
    for bar, v in zip(bars, vals):
        ax.text(v + max(vals)*0.02, bar.get_y()+bar.get_height()/2, f"R$ {v:.2f}/voto",
                 va='center', fontsize=9.5, fontfamily='Bricolage Grotesque', color=INK)
    ax.set_title(f"EFICIÊNCIA DE INVESTIMENTO POR VOTO — {ano}", fontsize=12, fontfamily='Bricolage Grotesque')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(vals)*1.35)
fig.suptitle("EFICIÊNCIA DE INVESTIMENTO POR VOTO — DESPESA PAGA / VOTOS VÁLIDOS, TODOS OS CANDIDATOS A PREFEITO\nCANDIDATURA DO GRUPO EM VERDE, PRINCIPAL ADVERSÁRIO EM VERMELHO, 3º COLOCADO EM AZUL",
             fontsize=12.5, fontweight='bold', fontfamily='Anton', y=1.05)
plt.tight_layout()
charts['custo_por_voto'] = fig_to_b64(fig)

# =====================================================================
# CHART 3 - Origem das receitas da chapa, 2020 vs 2024 (grouped horizontal bars)
# =====================================================================
origem2020 = {"Partido político": 57460.0, "Recursos próprios": 22030.8, "Pessoas físicas": 14440.2, "Outros candidatos": 2625.0}
origem2024 = {"Partido político": 166372.43, "Recursos próprios": 34547.11, "Pessoas físicas": 18648.65, "Outros candidatos": 7000.0}
cats = list(origem2020.keys())
y = range(len(cats))
fig, ax = plt.subplots(figsize=(8.2, 4.8))
h = 0.35
ax.barh([i + h/2 for i in y], [origem2020[c] for c in cats], height=h, color=RED, label='2020')
ax.barh([i - h/2 for i in y], [origem2024[c] for c in cats], height=h, color=BLUE, label='2024')
ax.set_yticks(list(y))
ax.set_yticklabels(cats, fontsize=10.5)
ax.invert_yaxis()
ax.set_xlabel('Receita declarada (R$)', fontsize=10)
ax.set_title('DE ONDE VEIO O DINHEIRO DA CHAPA', fontsize=13, fontweight='bold', fontfamily='Anton', pad=12)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='x', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
ax.legend(loc='lower right', frameon=False, fontsize=9.5)
plt.tight_layout()
charts['origem_receitas'] = fig_to_b64(fig)

# =====================================================================
# CHART 4 - Comparecimento vs Abstencao (municipio, cargo Prefeito)
# =====================================================================
fig, ax = plt.subplots(figsize=(7.2, 4.6))
anos = ['2020', '2024']
comp = [S['turnout']['comparecimento_2020'], S['turnout']['comparecimento_2024']]
abst = [S['turnout']['abstencoes_2020'], S['turnout']['abstencoes_2024']]
y = range(len(anos))
ax.barh(y, comp, color=BLUE, height=0.5, label='Compareceram')
ax.barh(y, abst, left=comp, color=GREY, height=0.5, label='Abstenções')
for i, (c, a) in enumerate(zip(comp, abst)):
    ax.text(c/2, i, f"{c:,}".replace(",", "."), va='center', ha='center', color='white', fontsize=10.5, fontfamily='Bricolage Grotesque')
    ax.text(c + a/2, i, f"{a:,}".replace(",", "."), va='center', ha='center', color='white', fontsize=10.5, fontfamily='Bricolage Grotesque')
ax.set_yticks(list(y))
ax.set_yticklabels([f"2020 ({S['turnout']['pct_comparecimento_2020']}%)", f"2024 ({S['turnout']['pct_comparecimento_2024']}%)"], fontsize=11)
ax.set_xlabel('Eleitores aptos', fontsize=10)
ax.set_title('COMPARECIMENTO VS. ABSTENÇÃO — ELEITORADO APTO AO VOTO', fontsize=12.5, fontweight='bold', fontfamily='Anton', pad=12)
ax.spines[['top', 'right', 'left']].set_visible(False)
ax.tick_params(left=False)
handles = [mpatches.Patch(color=BLUE, label='Compareceram'), mpatches.Patch(color=GREY, label='Abstenções')]
ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False, fontsize=9.5)
plt.tight_layout()
charts['comparecimento'] = fig_to_b64(fig)

for k, b64 in charts.items():
    with open(os.path.join(OUT, f"chart_{k}.b64"), 'w') as f:
        f.write(b64)

print("Charts gerados:", list(charts.keys()))
