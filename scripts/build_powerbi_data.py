# -*- coding: utf-8 -*-
"""Builds a clean, Power-BI-ready data package under output/powerbi/,
consolidating everything already computed for the case study into small,
well-named CSVs (one grain per file, tidy/long format where it matters
for slicing and matrix visuals)."""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")
PBI = os.path.join(OUT, "powerbi")
os.makedirs(PBI, exist_ok=True)

# 1) Historico de votacao por ano ------------------------------------------
hist = pd.read_csv(os.path.join(OUT, "resumo_prefeito_2004_2024.csv"))
hist = hist.rename(columns={
    "ano": "Ano", "vencedor": "Vencedor", "pct_vencedor": "Pct_Vencedor",
    "candidato_do_grupo": "Candidato_Grupo", "pct_candidato_do_grupo": "Pct_Grupo",
    "resultado_do_grupo": "Resultado", "total_votos_validos": "Total_Votos_Validos",
})
hist["Resultado"] = hist["Resultado"].map({"won": "Vitoria", "lost": "Derrota"})
hist.to_csv(os.path.join(PBI, "historico_votacao.csv"), index=False)

# 2) Distritos, formato longo (Distrito, Ano, Percentual) -------------------
dist = pd.read_csv(os.path.join(OUT, "distritos_resumo.csv"))
dist_long = dist.melt(id_vars="distrito", var_name="Ano", value_name="Percentual")
dist_long = dist_long.rename(columns={"distrito": "Distrito"})
dist_long["Ano"] = dist_long["Ano"].astype(int)
dist_long["Percentual"] = dist_long["Percentual"].round(1)
dist_long.to_csv(os.path.join(PBI, "distritos_por_ano.csv"), index=False)

# 3) Secoes 2024 (detalhamento por seção / local de votação) ---------------
sec = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
sec = sec.rename(columns={
    "NR_SECAO": "Secao", "votos_candidato_2020": "Votos_2020", "total_secao_2020": "Total_2020",
    "votos_candidato_2024": "Votos_2024", "total_secao_2024": "Total_2024",
    "pct_2020": "Pct_2020", "pct_2024": "Pct_2024", "variacao_pp": "Variacao_pp",
    "vencedor_2020": "Vencedor_2020", "vencedor_2024": "Vencedor_2024",
    "virou_de_derrota_para_vitoria": "Virou_Derrota_Para_Vitoria",
    "local_votacao": "Local_Votacao", "endereco_votacao": "Endereco",
})
sec.to_csv(os.path.join(PBI, "secoes_detalhe.csv"), index=False)

# 4) Camara Municipal: composicao por ano e lado ----------------------------
camara_comp = pd.DataFrame([
    {"Ano": 2020, "Lado": "Nossos", "Cadeiras": 3},
    {"Ano": 2020, "Lado": "Adversarios", "Cadeiras": 6},
    {"Ano": 2024, "Lado": "Nossos", "Cadeiras": 5},
    {"Ano": 2024, "Lado": "Adversarios", "Cadeiras": 4},
])
camara_comp.to_csv(os.path.join(PBI, "camara_composicao.csv"), index=False)

# 5) Vereadores eleitos, detalhe (nome, partido, votos, lado) ---------------
def load_vereadores(path, ano):
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    keep = df[["NM_URNA_CANDIDATO", "SG_PARTIDO", "QT_VOTOS_NOMINAIS_VALIDOS", "LADO"]].copy()
    keep["QT_VOTOS_NOMINAIS_VALIDOS"] = pd.to_numeric(keep["QT_VOTOS_NOMINAIS_VALIDOS"], errors="coerce")
    keep["Ano"] = ano
    keep = keep.rename(columns={
        "NM_URNA_CANDIDATO": "Nome", "SG_PARTIDO": "Partido",
        "QT_VOTOS_NOMINAIS_VALIDOS": "Votos", "LADO": "Lado",
    })
    keep["Lado"] = keep["Lado"].str.title()
    return keep[["Ano", "Nome", "Partido", "Votos", "Lado"]]

ver2020 = load_vereadores(os.path.join(OUT, "vereadores_eleitos_2020_com_lado.csv"), 2020)
ver2024 = load_vereadores(os.path.join(OUT, "vereadores_eleitos_2024_com_lado.csv"), 2024)
vereadores = pd.concat([ver2020, ver2024], ignore_index=True).sort_values(["Ano", "Votos"], ascending=[True, False])
vereadores.to_csv(os.path.join(PBI, "vereadores_eleitos.csv"), index=False)

# 6) Partido do grupo por ano, com espectro e coligacao ---------------------
partido = pd.DataFrame([
    {"Ano": 2004, "Partido_Grupo": "PT", "Espectro": "Esquerda", "Num_Partidos_Coligacao": 5, "Resultado": "Derrota"},
    {"Ano": 2008, "Partido_Grupo": "PSDB", "Espectro": "Centro", "Num_Partidos_Coligacao": 5, "Resultado": "Derrota"},
    {"Ano": 2012, "Partido_Grupo": "PSD", "Espectro": "Centro", "Num_Partidos_Coligacao": 6, "Resultado": "Derrota"},
    {"Ano": 2016, "Partido_Grupo": "PMDB", "Espectro": "Centro", "Num_Partidos_Coligacao": 9, "Resultado": "Derrota"},
    {"Ano": 2020, "Partido_Grupo": "Republicanos", "Espectro": "Direita", "Num_Partidos_Coligacao": 3, "Resultado": "Derrota"},
    {"Ano": 2024, "Partido_Grupo": "PP", "Espectro": "Direita", "Num_Partidos_Coligacao": 5, "Resultado": "Vitoria"},
])
partido.to_csv(os.path.join(PBI, "partido_por_ano.csv"), index=False)

# 7) Financiamento: candidatos a prefeito, receita/eficiencia (2020 e 2024) -
financiamento = pd.DataFrame([
    {"Ano": 2020, "Candidato": "Fernando (PSB, eleito)", "Grupo": "Nao", "Receita": 108642, "Custo_Por_Voto": 19.70},
    {"Ano": 2020, "Candidato": "Bianchi (Republicanos, grupo)", "Grupo": "Sim", "Receita": 53120, "Custo_Por_Voto": 13.58},
    {"Ano": 2020, "Candidato": "Zanata (PDT)", "Grupo": "Nao", "Receita": 32722, "Custo_Por_Voto": 80.36},
    {"Ano": 2024, "Candidato": "Hugo Luiz (PP, grupo, eleito)", "Grupo": "Sim", "Receita": 155597, "Custo_Por_Voto": 26.69},
    {"Ano": 2024, "Candidato": "Boldrini (PL)", "Grupo": "Nao", "Receita": 141130, "Custo_Por_Voto": 141.27},
    {"Ano": 2024, "Candidato": "Boteccia (PSB)", "Grupo": "Nao", "Receita": 119400, "Custo_Por_Voto": 36.20},
])
financiamento.to_csv(os.path.join(PBI, "financiamento.csv"), index=False)

# 8) Campanha digital: posts ------------------------------------------------
posts = pd.read_csv(os.path.join(DATA, "campanha_digital_posts.csv"), sep=";")
posts["engajamento"] = posts["likes"] + posts["comentarios"] + posts["compartilhamentos"]
posts = posts.rename(columns={
    "data": "Data", "fase": "Fase", "views": "Visualizacoes", "likes": "Curtidas",
    "comentarios": "Comentarios", "compartilhamentos": "Compartilhamentos",
    "tema": "Tema", "categoria": "Categoria", "engajamento": "Engajamento",
})
posts.to_csv(os.path.join(PBI, "campanha_digital_posts.csv"), index=False)

# 9) KPIs de resumo (uma linha, para os cartoes do overview) ----------------
# Total_Posts e Total_Visualizacoes vem direto de campanha_digital_posts.csv,
# em vez de hardcoded, para nunca ficarem defasados de correcoes na base.
kpis = pd.DataFrame([{
    "Secoes_Vencidas_2020": 1, "Secoes_Vencidas_2024": 42, "Total_Secoes_2024": 42,
    "Pct_2020": 37.8, "Pct_2024": 56.4,
    "Cadeiras_Camara_2020": 3, "Cadeiras_Camara_2024": 5, "Total_Cadeiras_Camara": 9,
    "Comparecimento_2020": 79.15, "Comparecimento_2024": 79.74,
    "Total_Posts": int(len(posts)), "Total_Visualizacoes": int(posts["Visualizacoes"].sum()),
}])
kpis.to_csv(os.path.join(PBI, "kpis_overview.csv"), index=False)

print("Arquivos gerados em:", PBI)
for f in sorted(os.listdir(PBI)):
    print(" -", f)
