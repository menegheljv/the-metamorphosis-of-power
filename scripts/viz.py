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
import os, sqlite3, base64, io

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")

comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
merged = pd.read_csv(os.path.join(OUT, "vencedor_por_secao.csv"))
verea = pd.read_csv(os.path.join(OUT, "vereadores_eleitos_2024.csv"))

# --- palette (brand-neutral, per dataviz conventions) ---
NAVY = "#3fae78"
TEAL = "#caa0ac"
CORAL = "#e2554c"
GOLD = "#caa0ac"
GREY = "#8f8f8f"
BG = "#ffffff"
GRID = "#e2e2e2"
INK = "#161616"

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
# CHART 1 - Slope / % de votos do candidato principal por secao 2020 vs 2024
# =====================================================================
c = comp.dropna(subset=['pct_2020', 'pct_2024']).sort_values('NR_SECAO')
fig, ax = plt.subplots(figsize=(10, 6))
for _, row in c.iterrows():
    color = TEAL if row['pct_2024'] >= 50 else CORAL
    ax.plot([0, 1], [row['pct_2020'], row['pct_2024']], color=color, alpha=0.55, linewidth=1.6, zorder=2)
ax.scatter([0]*len(c), c['pct_2020'], color=CORAL, s=26, zorder=3, label='2020')
ax.scatter([1]*len(c), c['pct_2024'], color=TEAL, s=26, zorder=3, label='2024')
ax.axhline(50, color=GREY, linestyle='--', linewidth=1, alpha=0.7)
ax.text(1.02, 50, '50%', color=GREY, va='center', fontsize=9)
ax.set_xlim(-0.15, 1.15)
ax.set_xticks([0, 1])
ax.set_xticklabels(['2020\n(derrota, 37,8% no municipio)', '2024\n(vitoria, 56,4% no municipio)'], fontsize=10)
ax.set_ylabel('% dos votos validos ao cargo de Prefeito, por secao', fontsize=10)
ax.set_title('Evolucao do candidato a prefeito por secao eleitoral — 2020 vs 2024\nAlfredo Chaves (ES) · 36 secoes comparaveis', fontsize=12, fontweight='bold', fontfamily='Anton', pad=14)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='y', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
plt.tight_layout()
charts['slope'] = fig_to_b64(fig)

# =====================================================================
# CHART 2 - Grade de secoes: categoria de virada (heatmap-like grid)
# =====================================================================
m = merged.copy().sort_values('NR_SECAO')
def categoria(row):
    if pd.isna(row['vencedor_2020']):
        return 'Secao nova em 2024'
    if row['vencedor_2020'] == 'RONALDO BIANCHI' or 'HUGO' in str(row['vencedor_2020']).upper():
        return 'Ja vencida em 2020'
    return 'Virou: derrota -> vitoria'
m['categoria'] = m.apply(categoria, axis=1)

cat_colors = {
    'Virou: derrota -> vitoria': TEAL,
    'Ja vencida em 2020': GOLD,
    'Secao nova em 2024': GREY,
}

n = len(m)
ncols = 7
nrows = -(-n // ncols)
fig, ax = plt.subplots(figsize=(ncols*1.05, nrows*1.05))
for i, (_, row) in enumerate(m.iterrows()):
    r, cidx = divmod(i, ncols)
    color = cat_colors[row['categoria']]
    rect = mpatches.FancyBboxPatch((cidx, nrows-1-r), 0.9, 0.9, boxstyle="round,pad=0.02,rounding_size=0.08",
                                     linewidth=0, facecolor=color)
    ax.add_patch(rect)
    ax.text(cidx+0.45, nrows-1-r+0.45, str(int(row['NR_SECAO'])), ha='center', va='center',
            fontsize=9, color='white', fontweight='bold', fontfamily='Anton')
ax.set_xlim(0, ncols)
ax.set_ylim(0, nrows)
ax.set_aspect('equal')
ax.axis('off')
handles = [mpatches.Patch(color=v, label=k) for k, v in cat_colors.items()]
ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.03), ncol=3, frameon=False, fontsize=9)
ax.set_title('Todas as 42 secoes eleitorais de Alfredo Chaves em 2024 — vencedor: nosso candidato em 100%\n(numero = numero oficial da secao TSE)',
             fontsize=11, fontweight='bold', fontfamily='Anton', pad=10)
plt.tight_layout()
charts['grid'] = fig_to_b64(fig)

# =====================================================================
# CHART 3 - Vereadores eleitos 2024 (coordenados na campanha)
# =====================================================================
v = verea.sort_values('QT_VOTOS_NOMINAIS_VALIDOS', ascending=True)
fig, ax = plt.subplots(figsize=(9, 5.2))
colors = [TEAL if 'QP' in s else GOLD for s in v['DS_SIT_TOT_TURNO']]
bars = ax.barh(v['NM_URNA_CANDIDATO'], v['QT_VOTOS_NOMINAIS_VALIDOS'], color=colors, height=0.62)
for bar, val in zip(bars, v['QT_VOTOS_NOMINAIS_VALIDOS']):
    ax.text(val + 6, bar.get_y() + bar.get_height()/2, str(val), va='center', fontsize=9, color=NAVY)
ax.set_xlabel('Votos nominais validos', fontsize=10)
ax.set_title('Vereadores eleitos em 2024 — campanhas coordenadas pelo autor\n9 cadeiras conquistadas na Camara Municipal', fontsize=12, fontweight='bold', fontfamily='Anton', pad=12)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='x', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
handles = [mpatches.Patch(color=TEAL, label='Eleito por quociente partidario (QP)'),
           mpatches.Patch(color=GOLD, label='Eleito por media')]
ax.legend(handles=handles, loc='lower right', frameon=False, fontsize=8.5)
plt.tight_layout()
charts['vereadores'] = fig_to_b64(fig)

# =====================================================================
# CHART 4 - Comparativo agregado do municipio: votos totais do candidato principal
# =====================================================================
fig, ax = plt.subplots(figsize=(6.4, 5.6))
anos = ['2020\n(Ronaldo Bianchi)', '2024\n(Hugo Luiz)']
votos = [3681, 5779]
pcts = [37.8, 56.4]
bars = ax.bar(anos, votos, color=[CORAL, TEAL], width=0.55)
for bar, v_, p_ in zip(bars, votos, pcts):
    ax.text(bar.get_x()+bar.get_width()/2, v_+80, f"{v_} votos\n({p_}%)", ha='center', fontsize=10, fontfamily='Bricolage Grotesque', color=NAVY)
ax.set_ylabel('Votos validos nominais ao cargo de Prefeito', fontsize=10)
ax.set_title('Resultado municipal — candidato a prefeito\nAlfredo Chaves (ES), 2020 vs 2024', fontsize=12, fontweight='bold', fontfamily='Anton', pad=12)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='y', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
ax.set_ylim(0, 6600)
plt.tight_layout()
charts['municipio'] = fig_to_b64(fig)

# save all as files too + print stats needed for the narrative
for k, b64 in charts.items():
    with open(os.path.join(OUT, f"chart_{k}.b64"), 'w') as f:
        f.write(b64)

print("Secoes vencidas 2020 por Ronaldo Bianchi (dos 36 comparaveis):", (merged['vencedor_2020']=='RONALDO BIANCHI').sum())
print("Secoes vencidas 2024 por Hugo Luiz (das 42 totais):", (merged['vencedor_2024']=='HUGO LUIZ PICOLI MENEGHEL').sum())
print("Total secoes 2024:", len(merged))
print("Charts gerados:", list(charts.keys()))
