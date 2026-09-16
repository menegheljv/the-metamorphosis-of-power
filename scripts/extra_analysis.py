# -*- coding: utf-8 -*-
import pandas as pd
import os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")

def brl(series):
    return pd.to_numeric(series.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)

def load(name):
    df = pd.read_csv(os.path.join(DATA, name), sep=';', encoding='utf-8', dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    return df

NOSSOS_2020 = {'PTB', 'REPUBLICANOS', 'PATRIOTA'}
NOSSOS_2024 = {'REPUBLICANOS', 'PP', 'PSDB'}

# ---------------------------------------------------------------------
# 1. FINANCEIRO: receitas e despesas
# ---------------------------------------------------------------------
rec2020 = load("receitas_candidatos_2020_alfredo_chaves.csv")
rec2024 = load("receitas_candidatos_2024_alfredo_chaves.csv")
desp2020 = load("despesas_pagas_2020_alfredo_chaves.csv")
desp2024 = load("despesas_pagas_2024_alfredo_chaves.csv")

rec2020['VR_RECEITA_NUM'] = brl(rec2020['VR_RECEITA'])
rec2024['VR_RECEITA_NUM'] = brl(rec2024['VR_RECEITA'])
desp2020['VR_PAGTO_DESPESA_NUM'] = brl(desp2020['VR_PAGTO_DESPESA'])
desp2024['VR_PAGTO_DESPESA_NUM'] = brl(desp2024['VR_PAGTO_DESPESA'])

rec2020['LADO'] = rec2020['SG_PARTIDO'].apply(lambda p: 'nossos' if p in NOSSOS_2020 else 'adversarios')
rec2024['LADO'] = rec2024['SG_PARTIDO'].apply(lambda p: 'nossos' if p in NOSSOS_2024 else 'adversarios')

print("=== RECEITAS DECLARADAS (TODOS OS CANDIDATOS DE ALFREDO CHAVES) ===")
print(f"2020: R$ {rec2020['VR_RECEITA_NUM'].sum():,.2f} total | {rec2020.groupby('LADO')['VR_RECEITA_NUM'].sum().to_dict()}")
print(f"2024: R$ {rec2024['VR_RECEITA_NUM'].sum():,.2f} total | {rec2024.groupby('LADO')['VR_RECEITA_NUM'].sum().to_dict()}")

# receitas so da chapa (nossos) - prefeito + vereadores
rec2020_nossos = rec2020[rec2020['LADO']=='nossos']
rec2024_nossos = rec2024[rec2024['LADO']=='nossos']
tot_rec_2020 = rec2020_nossos['VR_RECEITA_NUM'].sum()
tot_rec_2024 = rec2024_nossos['VR_RECEITA_NUM'].sum()

desp2020_ids = set(rec2020_nossos['SQ_PRESTADOR_CONTAS'].unique())
desp2024_ids = set(rec2024_nossos['SQ_PRESTADOR_CONTAS'].unique())
desp2020_nossos = desp2020[desp2020['SQ_PRESTADOR_CONTAS'].isin(desp2020_ids)]
desp2024_nossos = desp2024[desp2024['SQ_PRESTADOR_CONTAS'].isin(desp2024_ids)]
tot_desp_2020 = desp2020_nossos['VR_PAGTO_DESPESA_NUM'].sum()
tot_desp_2024 = desp2024_nossos['VR_PAGTO_DESPESA_NUM'].sum()

print(f"\n=== RECEITAS E DESPESAS DA CHAPA (nossos candidatos, prefeito+vereadores) ===")
print(f"2020: Receita R$ {tot_rec_2020:,.2f} | Despesa paga R$ {tot_desp_2020:,.2f}")
print(f"2024: Receita R$ {tot_rec_2024:,.2f} | Despesa paga R$ {tot_desp_2024:,.2f}")

# custo por voto (prefeito): usa despesa do prefeito especificamente
pref_id_2020 = rec2020[(rec2020['DS_CARGO']=='Prefeito') & (rec2020['LADO']=='nossos')]['SQ_PRESTADOR_CONTAS'].unique()
pref_id_2024 = rec2024[(rec2024['DS_CARGO']=='Prefeito') & (rec2024['LADO']=='nossos')]['SQ_PRESTADOR_CONTAS'].unique()
desp_pref_2020 = desp2020[desp2020['SQ_PRESTADOR_CONTAS'].isin(pref_id_2020)]['VR_PAGTO_DESPESA_NUM'].sum()
desp_pref_2024 = desp2024[desp2024['SQ_PRESTADOR_CONTAS'].isin(pref_id_2024)]['VR_PAGTO_DESPESA_NUM'].sum()
rec_pref_2020 = rec2020[(rec2020['DS_CARGO']=='Prefeito') & (rec2020['LADO']=='nossos')]['VR_RECEITA_NUM'].sum()
rec_pref_2024 = rec2024[(rec2024['DS_CARGO']=='Prefeito') & (rec2024['LADO']=='nossos')]['VR_RECEITA_NUM'].sum()

votos_pref_2020 = 3681
votos_pref_2024 = 5779
custo_voto_2020 = desp_pref_2020 / votos_pref_2020 if votos_pref_2020 else 0
custo_voto_2024 = desp_pref_2024 / votos_pref_2024 if votos_pref_2024 else 0

print(f"\n=== CAMPANHA A PREFEITO: RECEITA, DESPESA E CUSTO POR VOTO ===")
print(f"2020 (Ronaldo Bianchi): receita R$ {rec_pref_2020:,.2f} | despesa paga R$ {desp_pref_2020:,.2f} | {votos_pref_2020} votos | R$ {custo_voto_2020:.2f}/voto")
print(f"2024 (Hugo Luiz): receita R$ {rec_pref_2024:,.2f} | despesa paga R$ {desp_pref_2024:,.2f} | {votos_pref_2024} votos | R$ {custo_voto_2024:.2f}/voto")

# categorias de despesa (natureza)
print("\n=== DESPESAS DA CHAPA POR NATUREZA (2024) ===")
print(desp2024_nossos.groupby('DS_NATUREZA_DESPESA')['VR_PAGTO_DESPESA_NUM'].sum().sort_values(ascending=False).to_string())
print("\n=== DESPESAS DA CHAPA POR NATUREZA (2020) ===")
print(desp2020_nossos.groupby('DS_NATUREZA_DESPESA')['VR_PAGTO_DESPESA_NUM'].sum().sort_values(ascending=False).to_string())

# origem da receita
print("\n=== ORIGEM DAS RECEITAS DA CHAPA (2024) ===")
print(rec2024_nossos.groupby('DS_ORIGEM_RECEITA')['VR_RECEITA_NUM'].sum().sort_values(ascending=False).to_string())
print("\n=== ORIGEM DAS RECEITAS DA CHAPA (2020) ===")
print(rec2020_nossos.groupby('DS_ORIGEM_RECEITA')['VR_RECEITA_NUM'].sum().sort_values(ascending=False).to_string())

# ---------------------------------------------------------------------
# 2. COMPARECIMENTO / ABSTENCAO (ja extraido, so ler)
# ---------------------------------------------------------------------
det2020 = load("detalhe_votacao_2020_alfredo_chaves.csv")
det2024 = load("detalhe_votacao_2024_alfredo_chaves.csv")
det2020_pref = det2020[det2020['DS_CARGO']=='Prefeito'].iloc[0]
det2024_pref = det2024[det2024['DS_CARGO']=='Prefeito'].iloc[0]

turnout = {
    'aptos_2020': int(det2020_pref['QT_APTOS']), 'aptos_2024': int(det2024_pref['QT_APTOS']),
    'comparecimento_2020': int(det2020_pref['QT_COMPARECIMENTO']), 'comparecimento_2024': int(det2024_pref['QT_COMPARECIMENTO']),
    'abstencoes_2020': int(det2020_pref['QT_ABSTENCOES']), 'abstencoes_2024': int(det2024_pref['QT_ABSTENCOES']),
    'brancos_2020': int(det2020_pref['QT_VOTOS_BRANCOS']), 'brancos_2024': int(det2024_pref['QT_VOTOS_BRANCOS']),
    'nulos_2020': int(det2020_pref['QT_VOTOS_NULOS']), 'nulos_2024': int(det2024_pref['QT_VOTOS_NULOS']),
}
turnout['pct_comparecimento_2020'] = round(turnout['comparecimento_2020']/turnout['aptos_2020']*100, 2)
turnout['pct_comparecimento_2024'] = round(turnout['comparecimento_2024']/turnout['aptos_2024']*100, 2)

print("\n=== COMPARECIMENTO / ABSTENCAO ===")
print(json.dumps(turnout, indent=2))

# ---------------------------------------------------------------------
# 3. PERFIL DO ELEITORADO (idade, genero)
# ---------------------------------------------------------------------
perfil2020 = load("perfil_eleitorado_2020_alfredo_chaves.csv")
perfil2024 = load("perfil_eleitorado_2024_alfredo_chaves.csv")
perfil2020['QT'] = pd.to_numeric(perfil2020['QT_ELEITORES_PERFIL'], errors='coerce').fillna(0)
perfil2024['QT'] = pd.to_numeric(perfil2024['QT_ELEITORES_PERFIL'], errors='coerce').fillna(0)
perfil2020['DS_FAIXA_ETARIA'] = perfil2020['DS_FAIXA_ETARIA'].str.strip()
perfil2024['DS_FAIXA_ETARIA'] = perfil2024['DS_FAIXA_ETARIA'].str.strip()
perfil2020['DS_GENERO'] = perfil2020['DS_GENERO'].str.strip()
perfil2024['DS_GENERO'] = perfil2024['DS_GENERO'].str.strip()

print("\n=== ELEITORADO POR GENERO ===")
g2020 = perfil2020.groupby('DS_GENERO')['QT'].sum()
g2024 = perfil2024.groupby('DS_GENERO')['QT'].sum()
print("2020:", g2020.to_dict(), "total", g2020.sum())
print("2024:", g2024.to_dict(), "total", g2024.sum())

print("\n=== ELEITORADO POR FAIXA ETARIA (2020) ===")
print(perfil2020.groupby('DS_FAIXA_ETARIA')['QT'].sum().sort_index().to_string())
print("\n=== ELEITORADO POR FAIXA ETARIA (2024) ===")
print(perfil2024.groupby('DS_FAIXA_ETARIA')['QT'].sum().sort_index().to_string())

# jovens (16-24) especificamente
def jovens(df):
    faixas_jovens = ['16 anos','17 anos','18 anos','19 anos','20 anos','21 a 24 anos']
    return df[df['DS_FAIXA_ETARIA'].isin(faixas_jovens)]['QT'].sum()

jov2020 = jovens(perfil2020)
jov2024 = jovens(perfil2024)
print(f"\nEleitores 16-24 anos: 2020={jov2020} 2024={jov2024} (variacao {(jov2024/jov2020-1)*100:.1f}%)" if jov2020 else "")

# salva resumo consolidado
summary = {
    'financeiro': {
        'receita_chapa_2020': round(tot_rec_2020,2), 'receita_chapa_2024': round(tot_rec_2024,2),
        'despesa_chapa_2020': round(tot_desp_2020,2), 'despesa_chapa_2024': round(tot_desp_2024,2),
        'receita_prefeito_2020': round(rec_pref_2020,2), 'receita_prefeito_2024': round(rec_pref_2024,2),
        'despesa_prefeito_2020': round(desp_pref_2020,2), 'despesa_prefeito_2024': round(desp_pref_2024,2),
        'custo_voto_2020': round(custo_voto_2020,2), 'custo_voto_2024': round(custo_voto_2024,2),
    },
    'turnout': turnout,
    'eleitorado': {
        'jovens_16_24_2020': int(jov2020), 'jovens_16_24_2024': int(jov2024),
        'genero_2020': {k:int(v) for k,v in g2020.to_dict().items()},
        'genero_2024': {k:int(v) for k,v in g2024.to_dict().items()},
    }
}
with open(os.path.join(OUT, "extra_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("\n\nResumo salvo em extra_summary.json")
