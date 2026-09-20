# -*- coding: utf-8 -*-
"""Base de dados dos paineis de Power BI e Tableau (dashboards/data/*.csv).

Uma tabela por assunto, em formato "arrumado" (uma linha por fato), com nomes de coluna em portugues sem espacos.
Todas derivam do que ja alimenta o estudo: output/prefeitos_todos.csv, output/distritos_votos_cand.csv,
output/resumo_prefeito_2004_2024.csv, output/comparecimento_historico.csv, dashboards/fontes/* e data/campanha_digital_posts.csv.

Rode antes: python scripts/prefeitos_todos.py
"""
import os

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
DATA = os.path.join(BASE, "data")
DEST = os.path.join(BASE, "dashboards", "data")
FONTES = os.path.join(BASE, "dashboards", "fontes")  # Camara e secoes (2020/2024) ja apurados no estudo
os.makedirs(DEST, exist_ok=True)

LADO = {"grupo": "Grupo", "adversario": "Principal oposição", "terceiro": "Demais candidatos"}
LADO_ORDEM = {"Grupo": 1, "Principal oposição": 2, "Demais candidatos": 3}


def title_party(p):
    return p.title() if len(p) > 5 else p


def save(df, name):
    df.to_csv(os.path.join(DEST, name), index=False, encoding="utf-8")
    print(f"{name}: {len(df)} linhas, {len(df.columns)} colunas")


# ---------------------------------------------------------------- candidatos (16 candidaturas a prefeito)
p = pd.read_csv(os.path.join(OUT, "prefeitos_todos.csv"))
p["Partido"] = p["partido"].map(title_party)
cand = pd.DataFrame({
    "Ano": p["ano"],
    "Candidato": p["nome"],
    "Nome_Completo": p["nome_completo"],
    "Partido": p["Partido"],
    "Lado": p["lado"].map(LADO),
    "Votos": p["votos"],
    "Pct_Votos_Validos": p["pct"],
    "Resultado": p["resultado"].map({"Eleito": "Eleito", "Não eleito": "Não eleito"}),
    "Idade": p["idade"],
    "Genero": p["genero"],
    "Escolaridade": p["escolaridade"],
    "Ocupacao": p["ocupacao"],
    "Patrimonio_Declarado": p["patrimonio"],
    "Receita_Declarada": p["receita"],
    "Despesa_Paga": p["despesa_paga"],
    "Custo_Por_Voto": p["custo_por_voto"],
})
import unicodedata

_OCC = {"medico": "Médico", "professor de ensino de primeiro e segundo graus": "Professor de 1º e 2º graus", "advogado": "Advogado",
        "tecnico em edificacoes": "Técnico em edificações", "agricultor": "Agricultor", "servidor publico federal": "Servidor público federal",
        "vereador": "Vereador", "empresario": "Empresário", "prefeito": "Prefeito", "pecuarista": "Pecuarista", "comerciante": "Comerciante"}
_EDU = {"superior completo": "Superior completo", "ensino medio completo": "Médio completo", "medio completo": "Médio completo",
        "ensino medio incompleto": "Médio incompleto", "medio incompleto": "Médio incompleto",
        "ensino fundamental incompleto": "Fundamental incompleto", "fundamental incompleto": "Fundamental incompleto"}


def _k(x):
    return unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().lower().strip()


cand["Ocupacao"] = cand["Ocupacao"].map(lambda x: _OCC[_k(x)])
cand["Escolaridade"] = cand["Escolaridade"].map(lambda x: _EDU[_k(x)])
cand["Eleicao_Candidato"] = cand["Ano"].astype(str) + " · " + cand["Candidato"] + " (" + cand["Partido"] + ")"
cand["Ordem"] = range(1, len(cand) + 1)  # ano, depois votos (ordem do arquivo de origem)
save(cand, "candidatos.csv")

# ---------------------------------------------------------------- votos por distrito e candidato
d = pd.read_csv(os.path.join(OUT, "distritos_votos_cand.csv"))
info = p.set_index(["ano", "nome"])[["Partido", "lado"]]
d["Partido"] = [info.loc[(a, n), "Partido"] for a, n in zip(d["ano"], d["nome"])]
d["Lado"] = [LADO[info.loc[(a, n), "lado"]] for a, n in zip(d["ano"], d["nome"])]
dist = pd.DataFrame({
    "Distrito": d["distrito"], "Ano": d["ano"], "Candidato": d["nome"], "Partido": d["Partido"], "Lado": d["Lado"],
    "Votos": d["votos"], "Votos_Validos_Distrito": d["votos_validos"],
})
dist["Pct_No_Distrito"] = (dist["Votos"] / dist["Votos_Validos_Distrito"] * 100).round(1)
save(dist, "votos_distrito.csv")

# ---------------------------------------------------------------- eleicoes (uma linha por ano)
comp = pd.read_csv(os.path.join(OUT, "comparecimento_historico.csv")).rename(columns={"ano": "Ano"})
rows = []
for ano, g in p.groupby("ano"):
    grp = g[g["lado"] == "grupo"].iloc[0]
    opp = g[g["lado"] == "adversario"].iloc[0]
    win = g[g["resultado"] == "Eleito"].iloc[0]
    c = comp[comp["Ano"] == ano].iloc[0]
    rows.append({
        "Ano": ano, "Eleitores_Aptos": int(c["aptos"]), "Comparecimento": int(c["comparecimento"]), "Pct_Comparecimento": c["pct_comparecimento"],
        "Votos_Validos": int(g["votos_validos"].iloc[0]), "Candidatos_Prefeito": len(g),
        "Vencedor": win["nome"], "Partido_Vencedor": win["Partido"], "Pct_Vencedor": win["pct"],
        "Candidato_Grupo": grp["nome"], "Partido_Grupo": grp["Partido"], "Pct_Grupo": grp["pct"],
        "Candidato_Oposicao": opp["nome"], "Partido_Oposicao": opp["Partido"], "Pct_Oposicao": opp["pct"],
        "Pct_Demais": round(float(g[g["lado"] == "terceiro"]["pct"].sum()), 1),
        "Resultado_Grupo": "Vitória" if grp["resultado"] == "Eleito" else "Derrota",
    })
save(pd.DataFrame(rows), "eleicoes.csv")

# ---------------------------------------------------------------- Camara Municipal
cam = pd.read_csv(os.path.join(FONTES, "camara_composicao.csv")).replace({"Adversarios": "Adversários"})
save(cam, "camara.csv")
ver = pd.read_csv(os.path.join(FONTES, "vereadores_eleitos.csv")).replace({"Adversarios": "Adversários"})
ver["Nome"] = ver["Nome"].str.title()
ver["Partido"] = ver["Partido"].map(title_party)
save(ver, "vereadores_eleitos.csv")

# ---------------------------------------------------------------- campanha digital (166 posts)
posts = pd.read_csv(os.path.join(DATA, "campanha_digital_posts.csv"), sep=";")
posts = posts.rename(columns={"data": "Data", "fase": "Fase", "views": "Visualizacoes", "likes": "Curtidas", "comentarios": "Comentarios",
                              "compartilhamentos": "Compartilhamentos", "tema": "Tema", "categoria": "Categoria"})
posts["Engajamento"] = posts["Curtidas"] + posts["Comentarios"] + posts["Compartilhamentos"]
keep = ["Data", "Fase", "Categoria", "Tema", "Visualizacoes", "Curtidas", "Comentarios", "Compartilhamentos", "Engajamento"]
save(posts[keep].sort_values("Data"), "campanha_digital.csv")

# ---------------------------------------------------------------- secoes 2020 x 2024
sec = pd.read_csv(os.path.join(FONTES, "secoes_detalhe.csv"))
sec["Virou"] = sec["Virou_Derrota_Para_Vitoria"].map({True: "Virou para o grupo", False: "Não virou"})
sec["Vencedor_2020"] = sec["Vencedor_2020"].str.title()
sec["Vencedor_2024"] = sec["Vencedor_2024"].str.title()
save(sec.drop(columns=["Virou_Derrota_Para_Vitoria"]), "secoes.csv")
