# -*- coding: utf-8 -*-
import pandas as pd
import os, json
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")

def load(name):
    df = pd.read_csv(os.path.join(DATA, name), sep=';', encoding='utf-8', dtype=str, on_bad_lines='skip', engine='python')
    df.columns = [c.strip().upper() for c in df.columns]
    for c in df.select_dtypes(include='object').columns:
        df[c] = df[c].str.strip()
    return df

def brl(s):
    return pd.to_numeric(s.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)

NOSSOS_2020 = {'PTB', 'REPUBLICANOS', 'PATRIOTA'}
NOSSOS_2024 = {'REPUBLICANOS', 'PP', 'PSDB'}

# ---------------------------------------------------------------------
# PERFIL DOS CANDIDATOS (idade, escolaridade, ocupacao, genero, raca)
# ---------------------------------------------------------------------
perfil2020 = load("perfil_candidatos_2020_alfredo_chaves.csv")
perfil2024 = load("perfil_candidatos_2024_alfredo_chaves.csv")

def calc_idade(dt_nasc_str, dt_eleicao):
    try:
        dt = datetime.strptime(dt_nasc_str.strip('"'), "%d/%m/%Y")
        return (dt_eleicao - dt).days // 365
    except Exception:
        return None

perfil2020['IDADE'] = perfil2020['DT_NASCIMENTO'].apply(lambda s: calc_idade(s, datetime(2020,11,15)))
perfil2024['IDADE'] = perfil2024['DT_NASCIMENTO'].apply(lambda s: calc_idade(s, datetime(2024,10,6)))

print("=== IDADE MEDIA DOS CANDIDATOS ===")
print("2020:", perfil2020['IDADE'].mean().round(1), "anos | mediana", perfil2020['IDADE'].median())
print("2024:", perfil2024['IDADE'].mean().round(1), "anos | mediana", perfil2024['IDADE'].median())

print("\n=== HUGO LUIZ - PERFIL COMPLETO (2024, candidato a prefeito) ===")
hugo = perfil2024[perfil2024['NM_URNA_CANDIDATO'].str.contains('HUGO LUIZ', case=False, na=False)]
print(hugo[['NM_CANDIDATO','IDADE','DS_GRAU_INSTRUCAO','DS_OCUPACAO','DS_ESTADO_CIVIL','DS_COR_RACA','DS_GENERO']].to_string(index=False))

print("\n=== CANDIDATOS A PREFEITO - PERFIL COMPARATIVO ===")
for df, ano in [(perfil2020, 2020), (perfil2024, 2024)]:
    pref = df[df['DS_CARGO']=='PREFEITO']
    print(f"--- {ano} ---")
    print(pref[['NM_URNA_CANDIDATO','SG_PARTIDO','IDADE','DS_GRAU_INSTRUCAO','DS_OCUPACAO','DS_COR_RACA']].to_string(index=False))

print("\n=== ESCOLARIDADE (todos os candidatos) ===")
print("2020:"); print(perfil2020['DS_GRAU_INSTRUCAO'].value_counts().to_string())
print("2024:"); print(perfil2024['DS_GRAU_INSTRUCAO'].value_counts().to_string())

print("\n=== GENERO DOS CANDIDATOS ===")
print("2020:", perfil2020['DS_GENERO'].value_counts().to_dict())
print("2024:", perfil2024['DS_GENERO'].value_counts().to_dict())

print("\n=== RACA/COR DOS CANDIDATOS ===")
print("2020:", perfil2020['DS_COR_RACA'].value_counts().to_dict())
print("2024:", perfil2024['DS_COR_RACA'].value_counts().to_dict())

# ---------------------------------------------------------------------
# BENS DECLARADOS (patrimonio)
# ---------------------------------------------------------------------
bens2020 = load("bens_candidatos_2020_alfredo_chaves.csv")
bens2024 = load("bens_candidatos_2024_alfredo_chaves.csv")
bens2020['VR'] = brl(bens2020['VR_BEM_CANDIDATO'])
bens2024['VR'] = brl(bens2024['VR_BEM_CANDIDATO'])

pat2020 = bens2020.groupby('SQ_CANDIDATO')['VR'].sum()
pat2024 = bens2024.groupby('SQ_CANDIDATO')['VR'].sum()

# mapear SQ_CANDIDATO -> nome via perfil
map2020 = perfil2020.set_index('SQ_CANDIDATO')['NM_URNA_CANDIDATO']
map2024 = perfil2024.set_index('SQ_CANDIDATO')['NM_URNA_CANDIDATO']

print("\n=== PATRIMONIO DECLARADO - CANDIDATOS A PREFEITO ===")
pref_ids_2020 = perfil2020[perfil2020['DS_CARGO']=='PREFEITO'].set_index('SQ_CANDIDATO')['NM_URNA_CANDIDATO']
pref_ids_2024 = perfil2024[perfil2024['DS_CARGO']=='PREFEITO'].set_index('SQ_CANDIDATO')['NM_URNA_CANDIDATO']
print("--- 2020 ---")
for sq, nome in pref_ids_2020.items():
    print(f"{nome}: R$ {pat2020.get(sq, 0):,.2f}")
print("--- 2024 ---")
for sq, nome in pref_ids_2024.items():
    print(f"{nome}: R$ {pat2024.get(sq, 0):,.2f}")

# patrimonio total da chapa vereador (nossos vs adversarios)
def lado_map(perfil_df, nossos_set):
    return perfil_df.set_index('SQ_CANDIDATO')['SG_PARTIDO'].apply(lambda p: 'nossos' if p in nossos_set else 'adversarios')

lado2020 = lado_map(perfil2020, NOSSOS_2020)
lado2024 = lado_map(perfil2024, NOSSOS_2024)

pat2020_lado = pat2020.to_frame('VR').join(lado2020.rename('LADO'), how='inner').groupby('LADO')['VR'].sum()
pat2024_lado = pat2024.to_frame('VR').join(lado2024.rename('LADO'), how='inner').groupby('LADO')['VR'].sum()
print("\n=== PATRIMONIO TOTAL DECLARADO, TODOS OS CANDIDATOS, POR LADO ===")
print("2020:", pat2020_lado.to_dict())
print("2024:", pat2024_lado.to_dict())

# resumo
summary = {
    'idade_media_2020': round(float(perfil2020['IDADE'].mean()), 1),
    'idade_media_2024': round(float(perfil2024['IDADE'].mean()), 1),
    'hugo_idade_2024': int(hugo['IDADE'].iloc[0]) if len(hugo) else None,
    'hugo_ocupacao': hugo['DS_OCUPACAO'].iloc[0] if len(hugo) else None,
    'hugo_escolaridade': hugo['DS_GRAU_INSTRUCAO'].iloc[0] if len(hugo) else None,
    'patrimonio_prefeito_2020': {nome: round(float(pat2020.get(sq,0)),2) for sq, nome in pref_ids_2020.items()},
    'patrimonio_prefeito_2024': {nome: round(float(pat2024.get(sq,0)),2) for sq, nome in pref_ids_2024.items()},
    'patrimonio_chapa_2020': {k: round(float(v),2) for k,v in pat2020_lado.to_dict().items()},
    'patrimonio_chapa_2024': {k: round(float(v),2) for k,v in pat2024_lado.to_dict().items()},
}
with open(os.path.join(OUT, "candidate_profile_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("\nResumo salvo em candidate_profile_summary.json")
