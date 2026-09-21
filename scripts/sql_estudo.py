# -*- coding: utf-8 -*-
"""Roda as consultas SQL do estudo sobre o banco das SEIS eleicoes e confere o resultado.

1. Constroi o banco (scripts/build_database.py).
2. Executa sql/01_*.sql ... sql/05_*.sql e grava cada resultado em output/sql/<consulta>.csv.
3. Reconcilia o SQL com os CSVs produzidos pelo pipeline em pandas (prefeitos_todos.csv,
   comparecimento_historico.csv, distritos_votos_abs.csv). Qualquer divergencia encerra com erro.

Uso:  python scripts/sql_estudo.py
"""
import glob
import os
import sqlite3
import sys

import pandas as pd

import build_database

BASE = build_database.BASE
OUT = build_database.OUT
SQL = build_database.SQL
OUT_SQL = os.path.join(OUT, "sql")

falhas = []


def confere(ok, mensagem):
    print(("  ok    " if ok else "  FALHA ") + mensagem)
    if not ok:
        falhas.append(mensagem)


def main():
    build_database.main()
    os.makedirs(OUT_SQL, exist_ok=True)
    conn = sqlite3.connect(build_database.DB_PATH)

    res = {}
    for path in sorted(glob.glob(os.path.join(SQL, "0[1-9]_*.sql"))):
        nome = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            res[nome] = pd.read_sql(f.read(), conn)
        res[nome].to_csv(os.path.join(OUT_SQL, nome + ".csv"), index=False, encoding="utf-8")
        print(f"\n== {nome}: {len(res[nome])} linhas")
        print(res[nome].to_string(index=False, max_rows=20))

    print("\n=== CONFERENCIA CONTRA O PIPELINE EM PANDAS ===")

    # 1. Tabela 0.1: todos os candidatos a prefeito
    sql = res["01_resultado_prefeito"]
    pd_ref = pd.read_csv(os.path.join(OUT, "prefeitos_todos.csv"))
    m = sql.merge(pd_ref, left_on=["ano", "numero"], right_on=["ano", "numero"], how="outer",
                  suffixes=("_sql", "_pd"), indicator=True)
    confere((m["_merge"] == "both").all() and len(sql) == len(pd_ref) == 16,
            f"01: {len(sql)} candidaturas a prefeito nas duas fontes (esperado 16)")
    both = m[m["_merge"] == "both"]
    confere((both["votos_sql"] == both["votos_pd"]).all(), "01: votos de cada candidato iguais")
    confere((both["votos_validos_sql"] == both["votos_validos_pd"]).all(), "01: votos validos iguais")
    confere(((both["pct_sql"] - both["pct_pd"]).abs() < 0.051).all(), "01: percentuais iguais (arredondamento de 0,1)")
    confere((both["lado_sql"] == both["lado_pd"]).all(), "01: lado (grupo/adversario/terceiro) igual")
    confere(((both["resultado_sql"] == "Eleito") == (both["resultado_pd"] == "Eleito")).all(), "01: quem foi eleito igual")

    # 2. Secoes vencidas (Figura de secoes e texto do estudo)
    sv = res["02_secoes_vencidas"].set_index("ano")
    confere(int(sv.loc[2020, "secoes"]) == 36 and int(sv.loc[2020, "secoes_vencidas"]) == 1, "02: 2020 = 1 de 36 secoes")
    confere(int(sv.loc[2024, "secoes"]) == 42 and int(sv.loc[2024, "secoes_vencidas"]) == 42, "02: 2024 = 42 de 42 secoes")

    # 4. Comparecimento
    cp = res["04_comparecimento"].merge(pd.read_csv(os.path.join(OUT, "comparecimento_historico.csv")), on="ano", suffixes=("_sql", "_pd"))
    confere(len(cp) == 6 and (cp["aptos_sql"] == cp["aptos_pd"]).all() and (cp["comparecimento_sql"] == cp["comparecimento_pd"]).all()
            and ((cp["pct_comparecimento_sql"] - cp["pct_comparecimento_pd"]).abs() < 0.006).all(),
            "04: aptos, comparecimento e % de comparecimento iguais nas 6 eleicoes")

    # 5. Distritos
    ds = res["05_distritos"].merge(pd.read_csv(os.path.join(OUT, "distritos_votos_abs.csv")), on=["distrito", "ano"], how="outer",
                                   suffixes=("_sql", "_pd"), indicator=True)
    ok = (ds["_merge"] == "both").all() and (ds["votos_grupo_sql"] == ds["votos_grupo_pd"]).all() \
        and (ds["votos_validos_sql"] == ds["votos_validos_pd"]).all()
    confere(ok, f"05: votos do grupo e validos por distrito e ano iguais ({len(ds)} pares distrito-ano)")

    # 3. Virada 2020 -> 2024, secao a secao (36 secoes existem nas duas eleicoes)
    v = res["03_virada_2020_2024"]
    cs = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv")).dropna(subset=["pct_2020", "pct_2024"])
    j = v.merge(cs, left_on="secao", right_on="NR_SECAO", suffixes=("_sql", "_pd"))
    confere(len(v) == len(cs) == len(j) == 36, f"03: {len(v)} secoes comparaveis nas duas fontes (esperado 36)")
    confere(((j["pct_2020_sql"] - j["pct_2020_pd"]).abs() < 0.051).all() and ((j["pct_2024_sql"] - j["pct_2024_pd"]).abs() < 0.051).all(),
            "03: % do grupo por secao em 2020 e 2024 iguais")
    confere((j["virou_para_maioria"] == j["virou_de_derrota_para_vitoria"].astype(int)).all(), "03: secoes que viraram para maioria iguais")
    print(f"\n  info  03: {len(v)} secoes comparaveis; {int(v['virou_para_maioria'].sum())} viraram para maioria; "
          f"variacao media nas que viraram = {v.loc[v['virou_para_maioria'] == 1, 'variacao_pp'].mean():.1f} p.p.; "
          f"em todas = {v['variacao_pp'].mean():.1f} p.p.")

    conn.close()
    if falhas:
        print(f"\n{len(falhas)} conferencia(s) falharam.")
        sys.exit(1)
    print("\nTodas as conferencias passaram.")


if __name__ == "__main__":
    main()
