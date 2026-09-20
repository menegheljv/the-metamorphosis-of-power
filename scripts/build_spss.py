# -*- coding: utf-8 -*-
"""Converte as tabelas de output/powerbi/*.csv para .sav (SPSS) nativo,
com labels de variavel e de valor, sem precisar do SPSS instalado."""
import pandas as pd
import pyreadstat
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "output", "powerbi")
DST = os.path.join(BASE, "output", "spss")
os.makedirs(DST, exist_ok=True)

# (arquivo_csv, titulo_do_dataset, {coluna: label_de_variavel}, {coluna: {valor: label}})
DATASETS = [
    ("historico_votacao", "Historico de votacao para prefeito, 2004-2024", {
        "Ano": "Ano da eleicao",
        "Vencedor": "Candidato vencedor",
        "Pct_Vencedor": "Percentual de votos validos do vencedor",
        "Candidato_Grupo": "Candidato do grupo (familia Meneghel/aliados) no ano",
        "Pct_Grupo": "Percentual de votos validos do candidato do grupo",
        "Resultado": "Resultado do candidato do grupo",
        "Total_Votos_Validos": "Total de votos validos no municipio",
    }, {}),
    ("secoes_detalhe", "Comparativo secao a secao, prefeito 2020 vs 2024", {
        "Secao": "Numero da secao eleitoral",
        "Votos_2020": "Votos do candidato do grupo em 2020",
        "Total_2020": "Total de votos validos na secao em 2020",
        "Votos_2024": "Votos do candidato do grupo em 2024",
        "Total_2024": "Total de votos validos na secao em 2024",
        "Pct_2020": "Percentual do grupo na secao em 2020",
        "Pct_2024": "Percentual do grupo na secao em 2024",
        "Variacao_pp": "Variacao em pontos percentuais, 2020 a 2024",
        "Vencedor_2020": "Candidato mais votado na secao em 2020",
        "Vencedor_2024": "Candidato mais votado na secao em 2024",
        "Virou_Derrota_Para_Vitoria": "Secao que era derrota em 2020 e virou vitoria em 2024",
        "Local_Votacao": "Local de votacao",
        "Endereco": "Endereco do local de votacao",
    }, {"Virou_Derrota_Para_Vitoria": {0: "Nao", 1: "Sim"}}),
    ("camara_composicao", "Composicao da Camara Municipal por ano e lado", {}, {}),
    ("partido_por_ano", "Partido do candidato do grupo, por ano", {}, {}),
    ("financiamento", "Financiamento de campanha por candidato", {}, {}),
    ("distritos_por_ano", "Percentual do grupo por distrito e ano (prefeito)", {}, {}),
    ("vereadores_eleitos", "Vereadores eleitos, votos e partido", {}, {}),
    ("campanha_digital_posts", "Posts de campanha digital: data, categoria, engajamento", {}, {}),
    ("genero_resumo_ptbr", "Perfil de genero de candidatos e eleitorado", {}, {}),
    ("raca_resumo_ptbr", "Perfil de raca/cor de candidatos e populacao (IBGE)", {}, {}),
    ("kpis_overview", "KPIs gerais do case (uma linha resumo)", {}, {}),
]

written = []
for fname, title, var_labels, val_labels in DATASETS:
    csv_path = os.path.join(SRC, f"{fname}.csv")
    if not os.path.exists(csv_path):
        print("PULEI (nao encontrado):", csv_path)
        continue
    df = pd.read_csv(csv_path)
    if len(df.columns) == 1 and ";" in df.columns[0]:
        df = pd.read_csv(csv_path, sep=";")

    # normaliza booleanos True/False -> 0/1 pra poder aplicar value label no SPSS
    for col, labels in val_labels.items():
        if col in df.columns and df[col].dtype == bool:
            df[col] = df[col].astype(int)

    sav_path = os.path.join(DST, f"{fname}.sav")
    pyreadstat.write_sav(
        df,
        sav_path,
        column_labels=[var_labels.get(c, c) for c in df.columns],
        variable_value_labels={k: v for k, v in val_labels.items() if k in df.columns},
        file_label=title[:80],
    )
    written.append((fname, len(df), len(df.columns)))
    print(f"OK: {sav_path}  ({len(df)} linhas x {len(df.columns)} colunas) - {title}")

print("\nTotal de arquivos .sav gerados:", len(written))
