# -*- coding: utf-8 -*-
import pandas as pd
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")

s2024 = pd.read_csv(os.path.join(DATA, "secao_2024_alfredo_chaves.csv"), sep=';', encoding='utf-8', dtype=str)
s2024.columns = [c.strip().upper() for c in s2024.columns]
s2024['NR_SECAO'] = pd.to_numeric(s2024['NR_SECAO'])

loc = s2024[['NR_SECAO', 'NM_LOCAL_VOTACAO', 'DS_LOCAL_VOTACAO_ENDERECO']].drop_duplicates(subset=['NR_SECAO'])
loc.columns = ['NR_SECAO', 'local_votacao', 'endereco_votacao']

comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
comp = comp.merge(loc, on='NR_SECAO', how='left')
comp = comp.sort_values('NR_SECAO')
comp.to_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"), index=False)
print(comp[['NR_SECAO', 'local_votacao', 'endereco_votacao']].to_string(index=False))
print("\nLocais unicos de votacao no municipio:", loc['local_votacao'].nunique())
