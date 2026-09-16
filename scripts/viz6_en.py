# -*- coding: utf-8 -*-
"""English twin of viz6.py. Same data, translated chart text."""
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
import os, base64, io
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
OUT_EN = os.path.join(OUT, "en")
os.makedirs(OUT_EN, exist_ok=True)

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

# The original poll documents don't share one base: Aug 30 and the official result
# sum to 100% among the named candidates, but Sep 21, Sep 28 and Oct 2 (the three
# 3-way polls with a gap) leave 9.6 to 23.75 p.p. unassigned (undecided / no answer),
# a sign those polls report the share of the total sample, not the share among named
# candidates. We normalize those three to sum to 100% among the names polled. Apr 16
# is different: it only had 2 names (Boldrini wasn't a candidate yet), so normalizing
# it would artificially inflate both existing names - we keep that one as reported.
main_dates = [datetime(2024,4,16), datetime(2024,8,30), datetime(2024,9,21),
              datetime(2024,9,28), datetime(2024,10,2), datetime(2024,10,6)]
hugo   = [54.8, 57.4, 58.12, 62.62, 56.97, 58.05]
rolmar = [21.6, 30.8, 28.83, 21.31, 32.63, 31.91]
boldrini_dates = [datetime(2024,8,30), datetime(2024,9,21), datetime(2024,9,28), datetime(2024,10,2), datetime(2024,10,6)]
boldrini = [11.8, 13.05, 16.07, 10.4, 10.04]

outlier_date = datetime(2024,9,17)
outlier_hugo, outlier_rolmar, outlier_boldrini = 25.81, 60.0, 14.18

labels = ["Apr 16\nInst. Solução", "Aug 30\nInst. Veritá", "Sep 21\nInove Consult.",
          "Sep 28\nIpopes", "Oct 2\nI9-Inove", "Oct 6\nOfficial\nTSE result"]

# Ordinal x-axis (one slot per poll, not per real date): the six polls aren't
# evenly spaced in time (four fall within the last 3 weeks), and a real date
# axis crowded the September/October points together.
x_main = list(range(6))
x_boldrini = x_main[1:]
x_outlier = 2.5  # between Sep 21 (2) and Sep 28 (3), kept off the main lines

fig, ax = plt.subplots(figsize=(11, 6.4))

ax.plot(x_main, hugo, color=BLUE, linewidth=2.8, marker='o', markersize=8, zorder=5, label='Hugo Luiz')
ax.plot(x_main, rolmar, color=RED, linewidth=2.2, marker='o', markersize=7, zorder=4, label='Rolmar Botecchia')
ax.plot(x_boldrini, boldrini, color=GOLD, linewidth=1.8, marker='o', markersize=6, zorder=3, linestyle='--', label='Boldrini')

ax.scatter([x_outlier], [outlier_hugo], marker='D', s=70, color=BLUE, alpha=0.35, zorder=6, edgecolor=INK, linewidth=0.8)
ax.scatter([x_outlier], [outlier_rolmar], marker='D', s=70, color=RED, alpha=0.35, zorder=6, edgecolor=INK, linewidth=0.8)
ax.annotate("poll from\nSep 17\n(outlier)", xy=(x_outlier, outlier_rolmar), xytext=(x_outlier, 72),
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
ax.set_ylabel('% prompted, normalized among those named', fontsize=10)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
ax.legend(loc='lower left', frameon=False, fontsize=9.5, ncol=3)
ax.set_title("SIX REAL POLLS, APRIL TO OCTOBER: HUGO LUIZ NEVER LOST THE LEAD", fontsize=12.5, fontweight='bold', fontfamily='Anton', pad=14)
plt.tight_layout()
b64 = fig_to_b64(fig)
with open(os.path.join(OUT_EN, "chart_pesquisas_evolucao.b64"), 'w') as f:
    f.write(b64)
print("Chart generated: pesquisas_evolucao")
