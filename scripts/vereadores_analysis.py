# -*- coding: utf-8 -*-
import pandas as pd
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")

def load(year):
    df = pd.read_csv(os.path.join(DATA, f"candidatos_{year}_alfredo_chaves.csv"), sep=';', encoding='utf-8', dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    df['QT_VOTOS_NOMINAIS_VALIDOS'] = pd.to_numeric(df['QT_VOTOS_NOMINAIS_VALIDOS'])
    return df

c2020 = load(2020)
c2024 = load(2024)

# Partidos da chapa de Hugo Luiz em cada eleicao (mesma base politica)
NOSSOS_2020 = {'PTB', 'REPUBLICANOS', 'PATRIOTA'}   # coligacao de Ronaldo Bianchi p/ prefeito ("Mudanca com Transparencia")
NOSSOS_2024 = {'REPUBLICANOS', 'PP', 'PSDB'}        # coligacao de Hugo Luiz p/ prefeito ("Renovacao e Juventude"; MDB/Cidadania nao lancaram vereador)

def tag_side(df, nossos):
    df = df.copy()
    df['LADO'] = df['SG_PARTIDO'].apply(lambda p: 'nossos' if p in nossos else 'adversarios')
    return df

v2020 = tag_side(c2020[c2020['DS_CARGO']=='Vereador'], NOSSOS_2020)
v2024 = tag_side(c2024[c2024['DS_CARGO']=='Vereador'], NOSSOS_2024)

def eleitos(df):
    mask = df['DS_SIT_TOT_TURNO'].isin(['ELEITO POR QP', 'ELEITO POR MÉDIA', 'ELEITO'])
    return df[mask].sort_values('QT_VOTOS_NOMINAIS_VALIDOS', ascending=False)

el2020 = eleitos(v2020)
el2024 = eleitos(v2024)

el2020.to_csv(os.path.join(OUT, "vereadores_eleitos_2020_com_lado.csv"), index=False)
el2024.to_csv(os.path.join(OUT, "vereadores_eleitos_2024_com_lado.csv"), index=False)

print("=== CAMARA MUNICIPAL - CADEIRAS POR LADO ===")
print("2020:", el2020['LADO'].value_counts().to_dict(), "de", len(el2020), "vagas")
print("2024:", el2024['LADO'].value_counts().to_dict(), "de", len(el2024), "vagas")

print("\n=== VEREADORES ELEITOS 2020 (com lado) ===")
print(el2020[['NM_URNA_CANDIDATO','SG_PARTIDO','QT_VOTOS_NOMINAIS_VALIDOS','LADO']].to_string(index=False))
print("\n=== VEREADORES ELEITOS 2024 (com lado) ===")
print(el2024[['NM_URNA_CANDIDATO','SG_PARTIDO','QT_VOTOS_NOMINAIS_VALIDOS','LADO']].to_string(index=False))

# Totais de votos - todos os candidatos a vereador "nossos" vs total do pleito
tot2020_nossos = v2020[v2020['LADO']=='nossos']['QT_VOTOS_NOMINAIS_VALIDOS'].sum()
tot2020_total  = v2020['QT_VOTOS_NOMINAIS_VALIDOS'].sum()
tot2024_nossos = v2024[v2024['LADO']=='nossos']['QT_VOTOS_NOMINAIS_VALIDOS'].sum()
tot2024_total  = v2024['QT_VOTOS_NOMINAIS_VALIDOS'].sum()

n2020_cand = (v2020['LADO']=='nossos').sum()
n2024_cand = (v2024['LADO']=='nossos').sum()

print(f"\n=== TOTAL DE VOTOS - CANDIDATOS A VEREADOR DA CHAPA (PTB/REPUBLICANOS/PATRIOTA em 2020; REPUBLICANOS/PP/PSDB em 2024) ===")
print(f"2020: {tot2020_nossos} votos ({n2020_cand} candidatos) de {tot2020_total} votos totais no pleito de vereador = {tot2020_nossos/tot2020_total*100:.1f}%")
print(f"2024: {tot2024_nossos} votos ({n2024_cand} candidatos) de {tot2024_total} votos totais no pleito de vereador = {tot2024_nossos/tot2024_total*100:.1f}%")
print(f"Crescimento absoluto de votos: {tot2024_nossos - tot2020_nossos} (+{(tot2024_nossos/tot2020_nossos-1)*100:.1f}%)")

print(f"\nCadeiras: 2020 = {len(el2020[el2020['LADO']=='nossos'])}/{len(el2020)} (minoria)  ->  2024 = {len(el2024[el2024['LADO']=='nossos'])}/{len(el2024)} (maioria)")

# salva resumo para o template
summary = {
    'cadeiras_2020_nossos': int((el2020['LADO']=='nossos').sum()),
    'cadeiras_2020_total': int(len(el2020)),
    'cadeiras_2024_nossos': int((el2024['LADO']=='nossos').sum()),
    'cadeiras_2024_total': int(len(el2024)),
    'votos_2020_nossos': int(tot2020_nossos),
    'votos_2020_total': int(tot2020_total),
    'votos_2024_nossos': int(tot2024_nossos),
    'votos_2024_total': int(tot2024_total),
}
import json
with open(os.path.join(OUT, "vereadores_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print("\nResumo salvo em vereadores_summary.json:", summary)
