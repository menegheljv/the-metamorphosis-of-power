# -*- coding: utf-8 -*-
"""English twin of viz2.py. Same data, translated chart text."""
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
OUT_EN = os.path.join(OUT, "en")
os.makedirs(OUT_EN, exist_ok=True)

comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
merged = pd.read_csv(os.path.join(OUT, "vencedor_por_secao.csv"))
el2020 = pd.read_csv(os.path.join(OUT, "vereadores_eleitos_2020_com_lado.csv"))
el2024 = pd.read_csv(os.path.join(OUT, "vereadores_eleitos_2024_com_lado.csv"))
with open(os.path.join(OUT, "vereadores_summary.json")) as f:
    summ = json.load(f)

BLUE = "#5fd996"
BLUE_SOFT = "#9df0c0"
RED = "#e2554c"
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
# CHART 1 - Slope
# =====================================================================
c = comp.dropna(subset=['pct_2020', 'pct_2024']).sort_values('NR_SECAO')
fig, ax = plt.subplots(figsize=(10, 6))
for _, row in c.iterrows():
    color = BLUE if row['pct_2024'] >= 50 else "#ef8f87"
    ax.plot([0, 1], [row['pct_2020'], row['pct_2024']], color=color, alpha=0.55, linewidth=1.6, zorder=2)
ax.scatter([0]*len(c), c['pct_2020'], color=RED, s=26, zorder=3, label='2020')
ax.scatter([1]*len(c), c['pct_2024'], color=BLUE, s=26, zorder=3, label='2024')
ax.axhline(50, color=GREY, linestyle='--', linewidth=1, alpha=0.7)
ax.text(1.02, 50, '50%', color=GREY, va='center', fontsize=9)
ax.set_xlim(-0.15, 1.15)
ax.set_xticks([0, 1])
ax.set_xticklabels(['2020\n(loss, 37.8% citywide)', '2024\n(win, 56.4% citywide)'], fontsize=10)
ax.set_ylabel('% of valid votes for Mayor, by precinct', fontsize=10)
ax.set_title('MAYORAL CANDIDATE BY VOTING PRECINCT — 2020 VS 2024\nALFREDO CHAVES, BRAZIL · 36 COMPARABLE PRECINCTS', fontsize=12, fontweight='bold', fontfamily='Anton', pad=14)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='y', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
plt.tight_layout()
charts['slope'] = fig_to_b64(fig)

# =====================================================================
# CHART 2 - Grid of precincts
# =====================================================================
m = merged.copy().sort_values('NR_SECAO')
def categoria(row):
    if pd.isna(row['vencedor_2020']):
        return 'New precinct in 2024'
    if row['vencedor_2020'] == 'RONALDO BIANCHI' or 'HUGO' in str(row['vencedor_2020']).upper():
        return 'Already won in 2020'
    return 'Flipped: loss → win'
m['categoria'] = m.apply(categoria, axis=1)

cat_colors = {
    'Flipped: loss → win': BLUE,
    'Already won in 2020': BLUE_SOFT,
    'New precinct in 2024': GREY,
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
ax.set_title('ALL 42 VOTING PRECINCTS IN ALFREDO CHAVES IN 2024 — WON BY THE GROUP\'S CANDIDATE IN 100%\n(NUMBER = OFFICIAL TSE PRECINCT NUMBER)',
             fontsize=11, fontweight='bold', fontfamily='Anton', pad=10)
plt.tight_layout()
charts['grid'] = fig_to_b64(fig)

# =====================================================================
# CHART 3 - Citywide mayoral result
# =====================================================================
fig, ax = plt.subplots(figsize=(6.4, 5.6))
anos = ['2020\nRonaldo Bianchi', '2024\nHugo Luiz']
votos = [3681, 5779]
pcts = [37.8, 56.4]
bars = ax.bar(anos, votos, color=[RED, BLUE], width=0.55)
for bar, v_, p_ in zip(bars, votos, pcts):
    ax.text(bar.get_x()+bar.get_width()/2, v_+80, f"{v_} votes\n({p_}%)", ha='center', fontsize=10, fontfamily='Bricolage Grotesque', color=INK)
ax.set_ylabel('Valid nominal votes for Mayor', fontsize=10)
ax.set_title('CITYWIDE RESULT — MAYORAL CANDIDATE\nALFREDO CHAVES, BRAZIL, 2020 VS 2024', fontsize=12, fontweight='bold', fontfamily='Anton', pad=12)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='y', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
ax.set_ylim(0, 6600)
plt.tight_layout()
charts['municipio'] = fig_to_b64(fig)

# =====================================================================
# CHART 4 - Council members elected, by side
# =====================================================================
def verea_chart(df, ano, cadeiras_nossos, total):
    d = df.sort_values('QT_VOTOS_NOMINAIS_VALIDOS', ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5.0))
    colors = [BLUE if lado == 'nossos' else RED for lado in d['LADO']]
    bars = ax.barh(d['NM_URNA_CANDIDATO'] + '  (' + d['SG_PARTIDO'] + ')', d['QT_VOTOS_NOMINAIS_VALIDOS'], color=colors, height=0.62)
    for bar, val in zip(bars, d['QT_VOTOS_NOMINAIS_VALIDOS']):
        ax.text(val + 6, bar.get_y() + bar.get_height()/2, str(val), va='center', fontsize=9, color=INK)
    ax.set_xlabel('Valid nominal votes', fontsize=10)
    ax.set_title(f'COUNCIL MEMBERS ELECTED IN {ano} — ALFREDO CHAVES CITY COUNCIL\n{cadeiras_nossos} OF {total} SEATS WITH THE GROUP\'S TICKET (GREEN) · {total-cadeiras_nossos} WITH OPPONENTS (RED)',
                 fontsize=11.5, fontfamily='Bricolage Grotesque', pad=12)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    handles = [mpatches.Patch(color=BLUE, label="The group's ticket (Hugo Luiz)"),
               mpatches.Patch(color=RED, label='Opponents')]
    ax.legend(handles=handles, loc='lower right', frameon=False, fontsize=8.5)
    plt.tight_layout()
    return fig_to_b64(fig)

charts['vereadores_2020'] = verea_chart(el2020, 2020, summ['cadeiras_2020_nossos'], summ['cadeiras_2020_total'])
charts['vereadores_2024'] = verea_chart(el2024, 2024, summ['cadeiras_2024_nossos'], summ['cadeiras_2024_total'])

# =====================================================================
# CHART 5 - City Council composition, 2020 vs 2024
# =====================================================================
fig, ax = plt.subplots(figsize=(7.5, 3.6))
anos = ['2020', '2024']
nossos = [summ['cadeiras_2020_nossos'], summ['cadeiras_2024_nossos']]
advers = [summ['cadeiras_2020_total']-summ['cadeiras_2020_nossos'], summ['cadeiras_2024_total']-summ['cadeiras_2024_nossos']]
y = range(len(anos))
ax.barh(y, nossos, color=BLUE, height=0.5, label="Group's ticket")
ax.barh(y, advers, left=nossos, color=RED, height=0.5, label='Opponents')
for i, (n_, a_) in enumerate(zip(nossos, advers)):
    ax.text(n_/2, i, f"{n_}", va='center', ha='center', color='white', fontsize=13, fontfamily='Bricolage Grotesque')
    ax.text(n_ + a_/2, i, f"{a_}", va='center', ha='center', color='white', fontsize=13, fontfamily='Bricolage Grotesque')
tot = summ['cadeiras_2020_total']
ax.axvline(tot/2, color=INK, linestyle=':', linewidth=1.2, alpha=0.6)
ax.text(tot/2, 1.42, 'simple majority', ha='center', fontsize=8.5, color=GREY)
ax.set_yticks(list(y))
ax.set_yticklabels(['2020\n(minority)', '2024\n(majority)'], fontsize=11)
ax.set_xlim(0, tot + 0.6)
ax.set_xlabel('City Council seats (9 total)', fontsize=10)
ax.set_title("THE POLITICAL FLIP IN ALFREDO CHAVES' CITY COUNCIL", fontsize=13, fontweight='bold', fontfamily='Anton', pad=14)
ax.spines[['top', 'right', 'left']].set_visible(False)
ax.tick_params(left=False)
handles = [mpatches.Patch(color=BLUE, label="Group's ticket (Hugo Luiz)"),
           mpatches.Patch(color=RED, label='Opponents')]
ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False, fontsize=9.5)
plt.tight_layout()
charts['camara'] = fig_to_b64(fig)

# =====================================================================
# CHART 6 - Total council-ticket votes, 2020 vs 2024
# =====================================================================
fig, ax = plt.subplots(figsize=(6.4, 5.6))
anos = ['2020', '2024']
votos = [summ['votos_2020_nossos'], summ['votos_2024_nossos']]
pcts = [summ['votos_2020_nossos']/summ['votos_2020_total']*100, summ['votos_2024_nossos']/summ['votos_2024_total']*100]
bars = ax.bar(anos, votos, color=[RED, BLUE], width=0.5)
for bar, v_, p_ in zip(bars, votos, pcts):
    ax.text(bar.get_x()+bar.get_width()/2, v_+60, f"{v_} votes\n({p_:.1f}% of the race)", ha='center', fontsize=10, fontfamily='Bricolage Grotesque', color=INK)
ax.set_ylabel("Sum of nominal votes — the ticket's council candidates", fontsize=10)
ax.set_title("TOTAL VOTES FOR THE TICKET'S COUNCIL CANDIDATES\nALFREDO CHAVES, BRAZIL, 2020 VS 2024", fontsize=12.5, fontweight='bold', fontfamily='Anton', pad=12)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='y', color=GRID, linewidth=0.7)
ax.set_axisbelow(True)
ax.set_ylim(0, max(votos)*1.25)
plt.tight_layout()
charts['votos_vereadores'] = fig_to_b64(fig)

for k, b64 in charts.items():
    with open(os.path.join(OUT_EN, f"chart_{k}.b64"), 'w') as f:
        f.write(b64)

print("Charts generated:", list(charts.keys()))
