# -*- coding: utf-8 -*-
"""Carrega as SEIS eleicoes municipais (2004-2024) de Alfredo Chaves num unico banco SQLite.

Le os extratos do TSE em data/ (votos por secao, candidatos, detalhe da votacao) e o mapa
local de votacao -> distrito, cria as tabelas de sql/00_schema.sql e grava:

    output/eleicoes_alfredo_chaves.db

As consultas do estudo ficam em sql/01_*.sql ... sql/05_*.sql e sao executadas por
scripts/sql_estudo.py, que tambem confere os resultados contra os CSVs do pipeline em pandas.
"""
import os
import sqlite3
import unicodedata

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")
SQL = os.path.join(BASE, "sql")
DB_PATH = os.path.join(OUT, "eleicoes_alfredo_chaves.db")

YEARS = [2004, 2008, 2012, 2016, 2020, 2024]
GROUP_CANDIDATE = {
    2004: "JORGE GABRIEL MENEGHEL", 2008: "DANIEL ORLANDI", 2012: "SERGIO BIANCHI",
    2016: "RONALDO BIANCHI", 2020: "RONALDO BIANCHI", 2024: "HUGO LUIZ PICOLI MENEGHEL",
}


def read_tse(name):
    """Le um CSV do TSE (delimitado por ';', UTF-8 ou Latin-1) com colunas em maiusculas."""
    path = os.path.join(DATA, name)
    for enc in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(path, sep=";", dtype=str, encoding=enc, quotechar='"')
            break
        except UnicodeDecodeError:
            continue
    df.columns = [c.strip().strip('"').upper() for c in df.columns]
    return df


def cargo(series):
    """'PREFEITO' (2016) e 'Prefeito' viram 'Prefeito'; idem para Vereador."""
    return series.str.strip().str.capitalize()


def to_int(series):
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def load_votos_secao():
    frames = []
    for year in YEARS:
        df = read_tse(f"secao_{year}_alfredo_chaves.csv")
        out = pd.DataFrame({
            "ano": year,
            "zona": to_int(df["NR_ZONA"]),
            "secao": to_int(df["NR_SECAO"]),
            "cargo": cargo(df["DS_CARGO"]),
            "nr_votavel": to_int(df["NR_VOTAVEL"]),
            "nm_votavel": df["NM_VOTAVEL"].str.strip().str.upper(),
            "qt_votos": to_int(df["QT_VOTOS"]),
            "nr_local_votacao": to_int(df["NR_LOCAL_VOTACAO"]),
        })
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def load_candidatos():
    frames = []
    for year in YEARS:
        df = read_tse(f"candidatos_{year}_alfredo_chaves.csv")
        col = lambda name: df[name].str.strip() if name in df.columns else None
        out = pd.DataFrame({
            "ano": year,
            "cargo": cargo(df["DS_CARGO"]),
            "sq_candidato": col("SQ_CANDIDATO"),
            "nr_candidato": to_int(df["NR_CANDIDATO"]),
            "nm_candidato": col("NM_CANDIDATO"),
            "nm_urna": col("NM_URNA_CANDIDATO"),
            "sg_partido": col("SG_PARTIDO"),
            "nm_coligacao": col("NM_COLIGACAO"),
            "ds_composicao": col("DS_COMPOSICAO_COLIGACAO"),
            "ds_situacao_turno": col("DS_SIT_TOT_TURNO"),
        })
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def load_detalhe():
    frames = []
    for year in YEARS:
        df = read_tse(f"detalhe_votacao_{year}_alfredo_chaves.csv")
        nulos = "QT_TOTAL_VOTOS_NULOS" if "QT_TOTAL_VOTOS_NULOS" in df.columns else "QT_VOTOS_NULOS"
        out = pd.DataFrame({
            "ano": year,
            "cargo": cargo(df["DS_CARGO"]),
            "qt_aptos": to_int(df["QT_APTOS"]),
            "qt_comparecimento": to_int(df["QT_COMPARECIMENTO"]),
            "qt_abstencoes": to_int(df["QT_ABSTENCOES"]),
            "qt_brancos": to_int(df["QT_VOTOS_BRANCOS"]),
            "qt_nulos": to_int(df[nulos]),
            "qt_secoes": to_int(df["QT_TOTAL_SECOES"]),
        })
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def load_local_secao():
    """Secao -> local de votacao (2024) -> distrito (data/distritos_mapping.csv)."""
    s24 = read_tse("secao_2024_alfredo_chaves.csv")
    s24 = s24[s24["DS_CARGO"].str.strip().str.upper() == "PREFEITO"]
    locais = pd.DataFrame({
        "secao": to_int(s24["NR_SECAO"]),
        "local_votacao": s24["NM_LOCAL_VOTACAO"].str.strip(),
    }).drop_duplicates("secao")
    mapa = pd.read_csv(os.path.join(DATA, "distritos_mapping.csv"), sep=";", encoding="utf-8")
    mapa["local_votacao"] = mapa["local_votacao"].str.strip()
    return locais.merge(mapa, on="local_votacao", how="left")


def main():
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(os.path.join(SQL, "00_schema.sql"), encoding="utf-8") as f:
        conn.executescript(f.read())

    tabelas = {
        "votos_secao": load_votos_secao(),
        "candidatos": load_candidatos(),
        "detalhe_votacao": load_detalhe(),
        "local_secao": load_local_secao(),
        "grupo_eleicao": pd.DataFrame({"ano": list(GROUP_CANDIDATE), "nm_votavel": list(GROUP_CANDIDATE.values())}),
    }
    for nome, df in tabelas.items():
        df.to_sql(nome, conn, if_exists="append", index=False)
        print(f"{nome:16s} {len(df):6d} linhas")
    conn.commit()
    conn.close()
    print(f"\nBanco gravado em {DB_PATH}")


if __name__ == "__main__":
    main()
