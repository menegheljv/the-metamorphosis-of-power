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
import matplotlib.dates as mdates
import os, base64, io
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")

BLUE = "#5fd996"
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

# 6 pesquisas reais (documento original da pesquisa em mãos) + resultado oficial TSE.
# Metodologia "estimulada" em todos os pontos (2 vias em abril, 3 vias a partir de agosto).
# Os documentos originais não usam a mesma base: 30/ago e o resultado oficial somam
# 100% entre os citados, mas 21/set, 28/set e 02/out (as três pesquisas de 3 vias com
# lacuna) deixam de 9,6 a 23,75 p.p. sem atribuir (indeciso / não respondeu), sinal de
# que reportam o percentual sobre o total de entrevistados, não sobre os votos válidos
# entre os candidatos citados. Normalizamos essas três para somar 100% entre os nomes
# perguntados. A pesquisa de 16/abr é diferente: só tinha 2 vias (Boldrini ainda não
# era candidato), então normalizá-la infla artificialmente os dois nomes existentes -
# mantemos o valor bruto ali, sem normalizar.
main_dates = [datetime(2024,4,16), datetime(2024,8,30), datetime(2024,9,21),
              datetime(2024,9,28), datetime(2024,10,2), datetime(2024,10,6)]
hugo   = [54.8, 57.4, 58.12, 62.62, 56.97, 58.05]
rolmar = [21.6, 30.8, 28.83, 21.31, 32.63, 31.91]
boldrini_dates = [datetime(2024,8,30), datetime(2024,9,21), datetime(2024,9,28), datetime(2024,10,2), datetime(2024,10,6)]
boldrini = [11.8, 13.05, 16.07, 10.4, 10.04]

outlier_date = datetime(2024,9,17)
outlier_hugo, outlier_rolmar, outlier_boldrini = 25.81, 60.0, 14.18

labels = ["16/abr\nInst. Solução", "30/ago\nInst. Veritá", "21/set\nInove Consult.",
          "28/set\nIpopes", "02/out\nI9-Inove", "06/out\nResultado\noficial TSE"]

# Eixo X ordinal (uma posição por pesquisa, não por data real): as seis pesquisas
# não são igualmente espaçadas no tempo (quatro delas caem nas últimas 3 semanas),
# e um eixo de datas reais espremia demais os pontos de setembro/outubro.
x_main = list(range(6))
x_boldrini = x_main[1:]
x_outlier = 2.5  # entre 21/set (2) e 28/set (3), sem entrar na linha principal

fig, ax = plt.subplots(figsize=(11, 6.4))

ax.plot(x_main, hugo, color=BLUE, linewidth=2.8, marker='o', markersize=8, zorder=5, label='Hugo Luiz')
ax.plot(x_main, rolmar, color=RED, linewidth=2.2, marker='o', markersize=7, zorder=4, label='Rolmar Botecchia')
ax.plot(x_boldrini, boldrini, color=GOLD, linewidth=1.8, marker='o', markersize=6, zorder=3, linestyle='--', label='Boldrini')

# outlier de 17/set, plotado à parte, sem conectar a linha principal
ax.scatter([x_outlier], [outlier_hugo], marker='D', s=70, color=BLUE, alpha=0.35, zorder=6, edgecolor=INK, linewidth=0.8)
ax.scatter([x_outlier], [outlier_rolmar], marker='D', s=70, color=RED, alpha=0.35, zorder=6, edgecolor=INK, linewidth=0.8)
ax.annotate("pesquisa de\n17/set\n(atípica)", xy=(x_outlier, outlier_rolmar), xytext=(x_outlier, 72),
            ha='center', fontsize=8, color=GREY, fontweight='bold', fontfamily='Anton',
            arrowprops=dict(arrowstyle='-', color=GREY, linewidth=0.9, shrinkA=2, shrinkB=8))

for i, (x, v) in enumerate(zip(x_main, hugo)):
    dy = 2.6 if i % 2 == 0 else 4.6
    ax.text(x, v + dy, f"{v:.1f}%", ha='center', fontsize=10, fontfamily='Bricolage Grotesque', color=BLUE)
for i, (x, v) in enumerate(zip(x_main, rolmar)):
    ax.text(x, v + 3.6, f"{v:.1f}%", ha='center', fontsize=8.8, fontfamily='Bricolage Grotesque', color=RED)

ax.set_xlim(-0.4, 5.4)
ax.set_xticks(x_main)
ax.set_xticklabels(labels, fontsize=8.6)
ax.set_ylim(0, 80)
ax.set_ylabel('% estimulada, normalizada entre os citados', fontsize=10)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
ax.legend(loc='lower left', frameon=False, fontsize=9.5, ncol=3)
ax.set_title("SEIS PESQUISAS REAIS, ABRIL A OUTUBRO: HUGO LUIZ NUNCA SAIU DA LIDERANÇA", fontsize=12.5, fontweight='bold', fontfamily='Anton', pad=14)
plt.tight_layout()
b64 = fig_to_b64(fig)
with open(os.path.join(OUT, "chart_pesquisas_evolucao.b64"), 'w') as f:
    f.write(b64)
print("Chart gerado: pesquisas_evolucao (6 pontos reais + outlier + resultado)")
