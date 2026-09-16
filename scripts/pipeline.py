"""
Pipeline de tratamento de dados eleitorais - TSE Dados Abertos
Alfredo Chaves-ES | Eleicoes Municipais 2020 vs 2024
Etapas: Ingestao -> Limpeza -> Normalizacao -> Carga em SQLite -> Analise comparativa
"""
import pandas as pd
import sqlite3
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. INGESTAO: leitura dos CSVs brutos (extraidos do TSE, ; delimitado, UTF-8)
# ---------------------------------------------------------------------------
def read_tse_csv(path):
    df = pd.read_csv(path, sep=';', encoding='utf-8', dtype=str, quotechar='"')
    df.columns = [c.strip().upper() for c in df.columns]
    return df

secao_2020 = read_tse_csv(os.path.join(DATA, "secao_2020_alfredo_chaves.csv"))
secao_2024 = read_tse_csv(os.path.join(DATA, "secao_2024_alfredo_chaves.csv"))
cand_2020 = read_tse_csv(os.path.join(DATA, "candidatos_2020_alfredo_chaves.csv"))
cand_2024 = read_tse_csv(os.path.join(DATA, "candidatos_2024_alfredo_chaves.csv"))

print("=== INGESTAO ===")
print(f"secao_2020: {secao_2020.shape}")
print(f"secao_2024: {secao_2024.shape}")
print(f"cand_2020:  {cand_2020.shape}")
print(f"cand_2024:  {cand_2024.shape}")

# ---------------------------------------------------------------------------
# 2. LIMPEZA E NORMALIZACAO
# ---------------------------------------------------------------------------
def clean_secao(df, ano):
    keep = ['NR_ZONA', 'NR_SECAO', 'CD_CARGO', 'DS_CARGO', 'NR_VOTAVEL',
            'NM_VOTAVEL', 'QT_VOTOS', 'NR_LOCAL_VOTACAO', 'NM_LOCAL_VOTACAO']
    df = df[keep].copy()
    df['NR_ZONA'] = pd.to_numeric(df['NR_ZONA'], errors='coerce').astype('Int64')
    df['NR_SECAO'] = pd.to_numeric(df['NR_SECAO'], errors='coerce').astype('Int64')
    df['QT_VOTOS'] = pd.to_numeric(df['QT_VOTOS'], errors='coerce').fillna(0).astype(int)
    df['NM_VOTAVEL'] = df['NM_VOTAVEL'].str.strip().str.upper()
    df['DS_CARGO'] = df['DS_CARGO'].str.strip()
    df['ANO'] = ano
    return df.dropna(subset=['NR_SECAO'])

def clean_cand(df, ano):
    keep = ['CD_CARGO', 'DS_CARGO', 'NR_CANDIDATO', 'NM_CANDIDATO', 'NM_URNA_CANDIDATO',
            'SG_PARTIDO', 'NM_PARTIDO', 'NM_COLIGACAO', 'DS_COMPOSICAO_COLIGACAO',
            'QT_VOTOS_NOMINAIS_VALIDOS', 'DS_SIT_TOT_TURNO', 'DS_SITUACAO_CANDIDATURA']
    df = df[keep].copy()
    df['QT_VOTOS_NOMINAIS_VALIDOS'] = pd.to_numeric(df['QT_VOTOS_NOMINAIS_VALIDOS'], errors='coerce').fillna(0).astype(int)
    df['NM_URNA_CANDIDATO'] = df['NM_URNA_CANDIDATO'].str.strip().str.upper()
    df['DS_CARGO'] = df['DS_CARGO'].str.strip()
    df['ANO'] = ano
    # remove linhas de suplente sem candidatura a cargo majoritario/proporcional real (mantem todas - suplentes tb concorrem a vaga)
    return df

secao_2020c = clean_secao(secao_2020, 2020)
secao_2024c = clean_secao(secao_2024, 2024)
cand_2020c = clean_cand(cand_2020, 2020)
cand_2024c = clean_cand(cand_2024, 2024)

print("\n=== LIMPEZA CONCLUIDA ===")
print(f"secao_2020c: {secao_2020c.shape} | secoes unicas: {secao_2020c['NR_SECAO'].nunique()}")
print(f"secao_2024c: {secao_2024c.shape} | secoes unicas: {secao_2024c['NR_SECAO'].nunique()}")

# ---------------------------------------------------------------------------
# 3. CARGA EM SQLITE (para consultas SQL)
# ---------------------------------------------------------------------------
db_path = os.path.join(OUT, "alfredo_chaves.db")
if os.path.exists(db_path):
    os.remove(db_path)
conn = sqlite3.connect(db_path)
secao_2020c.to_sql('secao_2020', conn, index=False)
secao_2024c.to_sql('secao_2024', conn, index=False)
cand_2020c.to_sql('candidatos_2020', conn, index=False)
cand_2024c.to_sql('candidatos_2024', conn, index=False)
conn.commit()
print(f"\n=== SQLITE CARREGADO: {db_path} ===")

# ---------------------------------------------------------------------------
# 4. ANALISE COMPARATIVA - PREFEITO POR SECAO (SQL)
# ---------------------------------------------------------------------------

sql_prefeito_2020 = """
SELECT NR_SECAO, NM_VOTAVEL, SUM(QT_VOTOS) as votos
FROM secao_2020
WHERE DS_CARGO = 'Prefeito' AND NR_VOTAVEL > 0
GROUP BY NR_SECAO, NM_VOTAVEL
"""
sql_prefeito_2024 = sql_prefeito_2020.replace('secao_2020', 'secao_2024')

pref2020 = pd.read_sql(sql_prefeito_2020, conn)
pref2024 = pd.read_sql(sql_prefeito_2024, conn)

# vencedor por secao em cada ano (maior numero de votos nominais)
def winner_by_secao(df):
    idx = df.groupby('NR_SECAO')['votos'].idxmax()
    return df.loc[idx].reset_index(drop=True)

win2020 = winner_by_secao(pref2020).rename(columns={'NM_VOTAVEL': 'vencedor_2020', 'votos': 'votos_2020'})
win2024 = winner_by_secao(pref2024).rename(columns={'NM_VOTAVEL': 'vencedor_2024', 'votos': 'votos_2024'})

merged = pd.merge(win2020, win2024, on='NR_SECAO', how='outer')
merged.to_csv(os.path.join(OUT, "vencedor_por_secao.csv"), index=False)

print("\n=== VENCEDOR DO CARGO DE PREFEITO POR SECAO ===")
print(merged.sort_values('NR_SECAO').to_string(index=False))

# ---------------------------------------------------------------------------
# 5. IDENTIFICAR O CANDIDATO/CAMPANHA (2020 perdedor -> 2024 vencedor) via nome do vencedor 2024
# ---------------------------------------------------------------------------
vencedor_2024_nome = merged['vencedor_2024'].mode().iloc[0]
print(f"\nCandidato vencedor 2024 (agregado): {vencedor_2024_nome}")

# candidato 2020 que teve votos desse "grupo" (procura por Hugo/Bianchi conforme coligacao)
top2020 = cand_2020c[cand_2020c['DS_CARGO']=='Prefeito'].sort_values('QT_VOTOS_NOMINAIS_VALIDOS', ascending=False)
top2024 = cand_2024c[cand_2024c['DS_CARGO']=='Prefeito'].sort_values('QT_VOTOS_NOMINAIS_VALIDOS', ascending=False)
print("\n=== CANDIDATOS A PREFEITO 2020 ===")
print(top2020[['NM_URNA_CANDIDATO','SG_PARTIDO','NM_COLIGACAO','QT_VOTOS_NOMINAIS_VALIDOS','DS_SIT_TOT_TURNO']].to_string(index=False))
print("\n=== CANDIDATOS A PREFEITO 2024 ===")
print(top2024[['NM_URNA_CANDIDATO','SG_PARTIDO','NM_COLIGACAO','QT_VOTOS_NOMINAIS_VALIDOS','DS_SIT_TOT_TURNO']].to_string(index=False))

# ---------------------------------------------------------------------------
# 6. VOTOS TOTAIS DO CANDIDATO DA CAMPANHA (Ronaldo Bianchi 2020 -> Hugo Luiz 2024) POR SECAO
# ---------------------------------------------------------------------------
# candidato foco 2020: aquele cujo numero eh 10 (Ronaldo Bianchi) - segundo colocado, ligado ao PTB (mesma base de Hugo Luiz)
foco_2020_num = '10'
foco_2024_num = '11'

foco2020_secao = secao_2020c[(secao_2020c['DS_CARGO']=='Prefeito') & (secao_2020c['NR_VOTAVEL'].astype(str)==foco_2020_num)]
foco2024_secao = secao_2024c[(secao_2024c['DS_CARGO']=='Prefeito') & (secao_2024c['NR_VOTAVEL'].astype(str)==foco_2024_num)]

foco2020_agg = foco2020_secao.groupby('NR_SECAO')['QT_VOTOS'].sum().rename('votos_candidato_2020')
foco2024_agg = foco2024_secao.groupby('NR_SECAO')['QT_VOTOS'].sum().rename('votos_candidato_2024')

# total de votos validos ao cargo por secao (para % )
total2020 = pref2020.groupby('NR_SECAO')['votos'].sum().rename('total_secao_2020')
total2024 = pref2024.groupby('NR_SECAO')['votos'].sum().rename('total_secao_2024')

comp = pd.concat([foco2020_agg, total2020, foco2024_agg, total2024], axis=1).reset_index()
comp['pct_2020'] = (comp['votos_candidato_2020'] / comp['total_secao_2020'] * 100).round(1)
comp['pct_2024'] = (comp['votos_candidato_2024'] / comp['total_secao_2024'] * 100).round(1)
comp['variacao_pp'] = (comp['pct_2024'] - comp['pct_2020']).round(1)
comp = comp.merge(merged[['NR_SECAO','vencedor_2020','vencedor_2024']], on='NR_SECAO', how='left')
comp['virou_de_derrota_para_vitoria'] = comp.apply(
    lambda r: (r['pct_2020'] < 50) and (r['pct_2024'] >= 50) if pd.notna(r['pct_2020']) and pd.notna(r['pct_2024']) else None, axis=1)
comp = comp.sort_values('NR_SECAO')
comp.to_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"), index=False)

print("\n=== COMPARATIVO DO CANDIDATO PRINCIPAL POR SECAO (2020 vs 2024) ===")
print(comp.to_string(index=False))

secoes_viraram = comp['virou_de_derrota_para_vitoria'].sum()
total_secoes = comp['NR_SECAO'].nunique()
print(f"\nSecoes que viraram de derrota (<50%) para vitoria (>=50%): {secoes_viraram} de {total_secoes}")

# ---------------------------------------------------------------------------
# 7. VEREADORES ELEITOS 2024 (coordenados pelo usuario) - desempenho nas mesmas secoes
# ---------------------------------------------------------------------------
verea_2024 = cand_2024c[cand_2024c['DS_CARGO']=='Vereador'].copy()
verea_2024_eleitos = verea_2024[verea_2024['DS_SIT_TOT_TURNO'].isin(['ELEITO POR QP','ELEITO POR MÉDIA','ELEITO'])].sort_values(
    'QT_VOTOS_NOMINAIS_VALIDOS', ascending=False)
verea_2024_eleitos.to_csv(os.path.join(OUT, "vereadores_eleitos_2024.csv"), index=False)
print(f"\n=== VEREADORES ELEITOS 2024: {len(verea_2024_eleitos)} ===")
print(verea_2024_eleitos[['NM_URNA_CANDIDATO','SG_PARTIDO','QT_VOTOS_NOMINAIS_VALIDOS','DS_SIT_TOT_TURNO']].to_string(index=False))

# total geral de votos validos prefeito 2020 vs 2024 (crescimento do eleitorado/participacao)
print(f"\nTotal votos validos prefeito 2020: {total2020.sum()}")
print(f"Total votos validos prefeito 2024: {total2024.sum()}")

conn.close()
print("\n=== PIPELINE CONCLUIDO ===")
