# -*- coding: utf-8 -*-
"""Votos totais para prefeito por distrito e eleicao (numeros absolutos).

Usa a mesma atribuicao secao -> local de votacao (2024) -> distrito de
distritos_analysis.py, entao os totais aqui reproduzem os percentuais da Figura 6.

Produz output/distritos_votos_abs.csv com:
  distrito, ano, votos_grupo, votos_validos
(votos_validos exclui brancos e nulos, como no restante do estudo).
"""
import os

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")

comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
comp["local_votacao"] = comp["local_votacao"].str.strip()
secao_local = dict(zip(comp["NR_SECAO"], comp["local_votacao"]))

dist_map = pd.read_csv(os.path.join(DATA, "distritos_mapping.csv"), sep=";", encoding="utf-8")
dist_map["local_votacao"] = dist_map["local_votacao"].str.strip()
local_distrito = dict(zip(dist_map["local_votacao"], dist_map["distrito"]))

YEARS = [2004, 2008, 2012, 2016, 2020, 2024]
GROUP_CANDIDATE = {
    2004: "JORGE GABRIEL MENEGHEL", 2008: "DANIEL ORLANDI", 2012: "SERGIO BIANCHI",
    2016: "RONALDO BIANCHI", 2020: "RONALDO BIANCHI", 2024: "HUGO LUIZ PICOLI MENEGHEL",
}

rows = []
for year in YEARS:
    df = pd.read_csv(os.path.join(DATA, f"secao_{year}_alfredo_chaves.csv"), sep=";", encoding="utf-8", dtype=str, quotechar='"')
    df.columns = [c.strip().upper() for c in df.columns]
    pref = df[df["DS_CARGO"].str.strip().str.upper() == "PREFEITO"].copy()
    pref["QT_VOTOS"] = pd.to_numeric(pref["QT_VOTOS"], errors="coerce").fillna(0).astype(int)
    pref["NR_SECAO"] = pd.to_numeric(pref["NR_SECAO"], errors="coerce")
    pref = pref.dropna(subset=["NR_SECAO"])
    pref["NR_SECAO"] = pref["NR_SECAO"].astype(int)
    pref = pref[~pref["NM_VOTAVEL"].str.upper().isin(["VOTO BRANCO", "VOTO NULO"])]
    pref["distrito"] = pref["NR_SECAO"].map(lambda s: local_distrito.get(secao_local.get(s)))
    pref["is_grupo"] = pref["NM_VOTAVEL"].str.upper() == GROUP_CANDIDATE[year]

    for distrito, g in pref.dropna(subset=["distrito"]).groupby("distrito"):
        rows.append({
            "distrito": distrito,
            "ano": year,
            "votos_grupo": int(g.loc[g["is_grupo"], "QT_VOTOS"].sum()),
            "votos_validos": int(g["QT_VOTOS"].sum()),
        })
    lost = int(pref[pref["distrito"].isna()]["QT_VOTOS"].sum())
    if lost:
        print(f"AVISO {year}: {lost} votos em secoes sem distrito identificado")

out = pd.DataFrame(rows)
ORDER = ["Sede", "Crubixá", "Ibitiruí", "Matilde", "Ribeirão do Cristo", "Sagrada Família", "São Bento de Urânia"]
out["distrito"] = pd.Categorical(out["distrito"], ORDER, ordered=True)
out = out.sort_values(["distrito", "ano"]).reset_index(drop=True)
out.to_csv(os.path.join(OUT, "distritos_votos_abs.csv"), index=False, encoding="utf-8")

tot = out.groupby("ano")[["votos_grupo", "votos_validos"]].sum()
print(tot.to_string())
print(out.pivot(index="distrito", columns="ano", values="votos_grupo").to_string())
