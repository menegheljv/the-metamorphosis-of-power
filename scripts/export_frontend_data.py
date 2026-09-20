# -*- coding: utf-8 -*-
"""Exporta os dados do estudo para a homepage interativa (frontend/src/studyData.ts).

Cada figura do estudo vira uma especificacao tipada (tipo de grafico, series, cores
semanticas, unidade), e nao um dump cru de CSV. Legendas e textos alternativos sao
lidos do proprio output/template.html, para a homepage nunca divergir do estudo.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "output"
DATA = BASE / "data"
TARGET = BASE / "frontend" / "src" / "studyData.ts"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def title_case(name: str) -> str:
    small = {"de", "da", "do", "das", "dos", "e"}
    words = str(name).strip().lower().split()
    return " ".join(w if (i and w in small) else w.capitalize() for i, w in enumerate(words))


def clean(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, float):
        return round(value, 2)
    return value


# --------------------------------------------------------------------------
# Textos que ja existem no estudo: legenda (figcaption), cap e alt de cada figura
# --------------------------------------------------------------------------
template = (OUT / "template.html").read_text(encoding="utf-8")


def plain(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text).replace("%%", "%")
    return re.sub(r"\s+", " ", text).strip()


study_text: dict[str, dict[str, str]] = {}
for block in re.findall(r'<figure class="exhibit">(.*?)</figure>', template, re.S):
    tag = re.search(r'class="tag">([^<]*)<', block)
    cap = re.search(r'class="cap">([^<]*)<', block)
    alt = re.search(r'alt="([^"]*)"', block)
    fig = re.search(r"<figcaption>(.*?)</figcaption>", block, re.S)
    if not tag:
        continue
    study_text[tag.group(1).replace("Figura ", "").strip()] = {
        "cap": plain(cap.group(1)) if cap else "",
        "alt": plain(alt.group(1)) if alt else "",
        "caption": plain(fig.group(1)) if fig else "",
    }

hist_block = re.search(r'<figure class="chart-block">(.*?)</figure>', template, re.S)
hist_alt = plain(re.search(r'alt="([^"]*)"', hist_block.group(1)).group(1)) if hist_block else ""

# --------------------------------------------------------------------------
# Dados
# --------------------------------------------------------------------------
resumo = pd.read_csv(OUT / "resumo_prefeito_2004_2024.csv")
comp = pd.read_csv(OUT / "comparativo_candidato_prefeito_por_secao.csv").sort_values("NR_SECAO")
distritos = pd.read_csv(OUT / "distritos_resumo.csv")
dist_ver = pd.read_csv(OUT / "votos_vereadores_grupo_por_distrito_pct.csv")
comparecimento = pd.read_csv(OUT / "comparecimento_historico.csv")
ibge = pd.read_csv(OUT / "ibge_cruzamento.csv")
coerencia = pd.read_csv(OUT / "coerencia_voto.csv")
campanha_fase = pd.read_csv(OUT / "campanha_digital_resumo.csv")
posts = pd.read_csv(DATA / "campanha_digital_posts.csv", sep=";")
ver_summary = json.loads((OUT / "vereadores_summary.json").read_text(encoding="utf-8"))
extra = json.loads((OUT / "extra_summary.json").read_text(encoding="utf-8"))
perfil = json.loads((OUT / "candidate_profile_summary.json").read_text(encoding="utf-8"))


def vereadores(year: int):
    df = pd.read_csv(OUT / f"vereadores_eleitos_{year}_com_lado.csv", dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    df["votos"] = pd.to_numeric(df["QT_VOTOS_NOMINAIS_VALIDOS"], errors="coerce")
    df = df.sort_values("votos", ascending=False)
    side = {"GRUPO": "grupo", "NOSSOS": "grupo"}
    return [
        {
            "label": title_case(r["NM_URNA_CANDIDATO"]),
            "value": int(r["votos"]),
            "side": side.get(str(r["LADO"]).strip().upper(), "adversario"),
            "note": r["SG_PARTIDO"],
        }
        for _, r in df.iterrows()
    ]


def spec(slug, figure, section, title, subtitle, kind, source, text_key=None, **body):
    txt = study_text.get(text_key or figure, {})
    return {
        "slug": slug,
        "figure": f"Figura {figure}" if figure and figure[0].isdigit() else figure,
        "section": section,
        "title": title,
        "subtitle": subtitle,
        "kind": kind,
        "source": source,
        "cap": txt.get("cap", ""),
        "caption": txt.get("caption", ""),
        "alt": txt.get("alt", ""),
        **body,
    }


charts = []

# ---- 00.1 Vinte anos de dados ------------------------------------------------
rows = []
for _, r in resumo.iterrows():
    rows.append({
        "x": str(int(r["ano"])),
        "grupo": clean(r["pct_candidato_do_grupo"]),
        "vencedor": clean(r["pct_vencedor"]),
        "note": f"Grupo: {title_case(r['candidato_do_grupo'])} · Vencedor: {title_case(r['vencedor'])}",
    })
charts.append(spec(
    "historical_arc", "Arco histórico", "arco", "CINCO DERROTAS E A VIRADA",
    "% dos votos válidos para prefeito: candidato do grupo vs. vencedor, 2004–2024", "cartesian",
    "TSE · resultado por eleição, 1º turno",
    layers=[
        {"type": "line", "key": "vencedor", "label": "Vencedor da eleição", "color": "adversario"},
        {"type": "line", "key": "grupo", "label": "Candidato do grupo", "color": "grupo"},
    ],
    rows=rows, unit="pct", yDomain=[0, 80],
    cap="Votação do candidato do grupo para prefeito, 2004–2024",
    caption=("Cinco eleições consecutivas sem vitória, com a votação do grupo subindo de 26,4% (2004) até 48,0% (2016), "
             "recuando em 2020 e chegando a 58,1% em 2024, quando o candidato do grupo passa a ser também o vencedor."),
    alt=hist_alt,
))

# ---- 04 Da derrota generalizada à vitória ---------------------------------------
slope_rows = []
for _, r in comp.iterrows():
    slope_rows.append({
        "secao": int(r["NR_SECAO"]),
        "local": str(r["local_votacao"]).strip() if pd.notna(r["local_votacao"]) else "",
        "a": clean(r["pct_2020"]),
        "b": clean(r["pct_2024"]),
        "flip": bool(r["virou_de_derrota_para_vitoria"]) if pd.notna(r["virou_de_derrota_para_vitoria"]) else False,
    })
charts.append(spec(
    "slope", "3", "achados", "A VIRADA, SEÇÃO A SEÇÃO",
    "% de votos do candidato do grupo em cada seção, 2020 → 2024", "slope",
    "TSE · votação por seção, prefeito 2020 e 2024",
    rows=slope_rows, aLabel="2020", bLabel="2024",
))

tiles = []
for _, r in comp.iterrows():
    if pd.isna(r["vencedor_2020"]):
        cat = "nova"
    elif "BIANCHI" in str(r["vencedor_2020"]):
        cat = "ja"
    else:
        cat = "virou"
    tiles.append({
        "secao": int(r["NR_SECAO"]), "cat": cat,
        "local": str(r["local_votacao"]).strip() if pd.notna(r["local_votacao"]) else "",
        "a": clean(r["pct_2020"]), "b": clean(r["pct_2024"]),
    })
charts.append(spec(
    "grid", "4", "achados", "AS 42 SEÇÕES ELEITORAIS DE 2024",
    "Passe o mouse (ou use o teclado) para ver o local de votação de cada seção", "grid",
    "TSE · votação por seção, prefeito 2020 e 2024", tiles=tiles,
))

charts.append(spec(
    "municipio", "5", "achados", "RESULTADO AGREGADO DO MUNICÍPIO",
    "total de votos do candidato do grupo a prefeito, 2020 vs. 2024", "cartesian",
    "TSE · votação por seção, prefeito",
    layers=[{"type": "bar", "key": "votos", "label": "Votos do candidato do grupo", "color": "grupo", "colorBySide": True}],
    rows=[
        {"x": "2020", "votos": 3681, "side": "adversario", "note": "37,8% da votação"},
        {"x": "2024", "votos": 5779, "side": "grupo", "note": "56,4% da votação"},
    ],
    unit="int",
    caption="Em 2024, o candidato do grupo somou 5.779 votos (56,4%), contra 3.681 (37,8%) em 2020: mais de 2.000 votos a mais no mesmo município.",
))

charts.append(spec(
    "distritos_heatmap", "6", "achados", "ONDE O GRUPO ERA FORTE",
    "% do candidato do grupo para prefeito, por distrito, 2004–2024", "heatmap",
    "TSE · votação por seção, agregada por distrito",
    columns=[str(c) for c in distritos.columns[1:]],
    rows=[{"label": r["distrito"], "values": [clean(round(float(r[c]), 1)) for c in distritos.columns[1:]]}
          for _, r in distritos.iterrows()],
))

charts.append(spec(
    "distritos_vereadores_heatmap", "6.1", "achados", "ONDE A CHAPA DE VEREADOR ERA FORTE",
    "% dos votos para vereador na chapa do grupo, por distrito, 2020 e 2024", "heatmap",
    "TSE · votação por seção e registro de candidaturas (SQ_CANDIDATO)",
    columns=[str(c) for c in dist_ver.columns[1:]],
    rows=[{"label": r["distrito"], "values": [clean(float(r[c])) for c in dist_ver.columns[1:]]}
          for _, r in dist_ver.iterrows()],
))

# ---- 05 Câmara Municipal ----------------------------------------------------------
charts.append(spec(
    "camara", "7", "camara", "COMPOSIÇÃO DA CÂMARA MUNICIPAL",
    "cadeiras por lado, 2020 vs. 2024", "cartesian", "TSE · vereadores eleitos",
    layers=[
        {"type": "bar", "key": "adversarios", "label": "Adversários", "color": "adversario"},
        {"type": "bar", "key": "grupo", "label": "Chapa do grupo", "color": "grupo"},
    ],
    rows=[{"x": "2020", "adversarios": 6, "grupo": 3}, {"x": "2024", "adversarios": 4, "grupo": 5}],
    unit="int", yDomain=[0, 9],
))

v20, v24 = ver_summary["votos_2020_nossos"], ver_summary["votos_2024_nossos"]
t20, t24 = ver_summary["votos_2020_total"], ver_summary["votos_2024_total"]
charts.append(spec(
    "votos_vereadores", "8", "camara", "VOTAÇÃO TOTAL DA CHAPA DE VEREADOR",
    "soma de votos nominais dos candidatos a vereador da chapa", "cartesian", "TSE · votos nominais, vereador",
    layers=[{"type": "bar", "key": "votos", "label": "Votos da chapa", "color": "grupo", "colorBySide": True}],
    rows=[
        {"x": "2020", "votos": v20, "side": "adversario", "note": f"{v20 / t20 * 100:.1f}% do pleito".replace(".", ",")},
        {"x": "2024", "votos": v24, "side": "grupo", "note": f"{v24 / t24 * 100:.1f}% do pleito".replace(".", ",")},
    ],
    unit="int",
))

charts.append(spec(
    "vereadores_2020", "9", "camara", "VEREADORES ELEITOS EM 2020",
    "votos nominais, por lado", "panels", "TSE · vereadores eleitos, 2020", unit="int",
    panels=[{"rows": vereadores(2020)}],
))
charts.append(spec(
    "vereadores_2024", "10", "camara", "VEREADORES ELEITOS EM 2024",
    "votos nominais, por lado", "panels", "TSE · vereadores eleitos, 2024", unit="int",
    panels=[{"rows": vereadores(2024)}],
))

charts.append(spec(
    "coerencia_voto", "11", "camara", "PREFEITO × VEREADOR, SEÇÃO A SEÇÃO",
    "% do grupo para prefeito (x) e para vereador (y) em cada seção", "scatter",
    "TSE · coerencia_voto.csv",
    series=[
        {"key": "2020", "label": "2020", "color": "adversario",
         "points": [{"x": clean(r.pct_prefeito_nosso), "y": clean(r.pct_vereador_nosso), "secao": int(r.secao)}
                    for r in coerencia[coerencia["ano"] == 2020].itertuples()]},
        {"key": "2024", "label": "2024", "color": "grupo",
         "points": [{"x": clean(r.pct_prefeito_nosso), "y": clean(r.pct_vereador_nosso), "secao": int(r.secao)}
                    for r in coerencia[coerencia["ano"] == 2024].itertuples()]},
    ],
))

# ---- 06 Financiamento e participação ---------------------------------------------------
fin = pd.read_csv(OUT / "powerbi" / "financiamento.csv")
side_of = {"Fernando (PSB, eleito)": "adversario", "Bianchi (Republicanos, grupo)": "grupo", "Zanata (PDT)": "terceiro",
           "Hugo Luiz (PP, grupo, eleito)": "grupo", "Boldrini (PL)": "terceiro", "Boteccia (PSB)": "adversario"}


short_label = {"Bianchi (Republicanos, grupo)": "Bianchi (Republicanos)", "Hugo Luiz (PP, grupo, eleito)": "Hugo Luiz (PP, eleito)"}


def fin_panels(col):
    return [{"title": str(ano), "rows": [
        {"label": short_label.get(r["Candidato"], r["Candidato"]), "value": float(r[col]), "side": side_of[r["Candidato"]]}
        for _, r in fin[fin["Ano"] == ano].sort_values(col, ascending=False).iterrows()
    ]} for ano in (2020, 2024)]


charts.append(spec(
    "financeiro_chapa", "12", "financiamento", "RECEITA DECLARADA",
    "candidatos a prefeito, em reais", "panels", "TSE · prestação de contas", unit="brl",
    panels=fin_panels("Receita"),
))
charts.append(spec(
    "custo_por_voto", "13", "financiamento", "CUSTO POR VOTO",
    "reais gastos por voto, candidatos a prefeito", "panels", "TSE · prestação de contas e votação", unit="brl2",
    panels=fin_panels("Custo_Por_Voto"),
))

origem = {"Partido político": (57460.0, 166372.43), "Recursos próprios": (22030.8, 34547.11),
          "Pessoas físicas": (14440.2, 18648.65), "Outros candidatos": (2625.0, 7000.0)}
charts.append(spec(
    "origem_receitas", "14", "financiamento", "ORIGEM DAS RECEITAS DA CHAPA",
    "em reais, 2020 vs. 2024", "cartesian", "TSE · receitas de candidatos",
    layers=[
        {"type": "bar", "key": "y2020", "label": "2020", "color": "adversario"},
        {"type": "bar", "key": "y2024", "label": "2024", "color": "grupo"},
    ],
    rows=[{"x": k, "y2020": v[0], "y2024": v[1]} for k, v in origem.items()], unit="brl",
))

t = extra["turnout"]
charts.append(spec(
    "comparecimento", "15", "financiamento", "COMPARECIMENTO VS. ABSTENÇÃO",
    "eleitores aptos, 2020 e 2024", "cartesian", "TSE · detalhe da votação",
    layers=[
        {"type": "bar", "key": "comparecimento", "label": "Compareceram", "color": "info", "stackId": "a"},
        {"type": "bar", "key": "abstencao", "label": "Abstenções", "color": "muted", "stackId": "a"},
    ],
    rows=[
        {"x": "2020", "comparecimento": t["comparecimento_2020"], "abstencao": t["abstencoes_2020"],
         "note": f"{t['pct_comparecimento_2020']:.2f}% de comparecimento".replace(".", ",")},
        {"x": "2024", "comparecimento": t["comparecimento_2024"], "abstencao": t["abstencoes_2024"],
         "note": f"{t['pct_comparecimento_2024']:.2f}% de comparecimento".replace(".", ",")},
    ],
    unit="int",
))

charts.append(spec(
    "comparecimento_historico", "16", "financiamento", "COMPARECIMENTO EM QUEDA",
    "eleitores aptos (barras) e % de comparecimento (linha), 2004–2024", "cartesian", "TSE · detalhe da votação",
    layers=[
        {"type": "bar", "key": "aptos", "label": "Eleitores aptos", "color": "muted", "axis": "left"},
        {"type": "line", "key": "pct", "label": "% de comparecimento", "color": "info", "axis": "right"},
    ],
    rows=[{"x": str(int(r.ano)), "aptos": int(r.aptos), "pct": clean(r.pct_comparecimento)}
          for r in comparecimento.itertuples()],
    unit="int", rightUnit="pct", rightDomain=[70, 100],
))

charts.append(spec(
    "ibge_eleitorado", "17", "financiamento", "ELEITORES APTOS / POPULAÇÃO",
    "% da população estimada (IBGE) registrada para votar", "cartesian", "IBGE/TSE · ibge_cruzamento.csv",
    layers=[{"type": "line", "key": "pct", "label": "Eleitores aptos como % da população", "color": "info"}],
    rows=[{"x": str(int(r.ano)), "pct": clean(r.pct_populacao_registrada),
           "note": f"{int(r.eleitores_aptos):,} aptos · {int(r.populacao_estimada_ibge):,} habitantes".replace(",", ".")}
          for r in ibge.itertuples()],
    unit="pct", yDomain=[50, 100],
))

charts.append(spec(
    "genero_candidatos", "18", "financiamento", "PARTICIPAÇÃO FEMININA",
    "% de mulheres na população, no eleitorado e entre os candidatos", "cartesian", "IBGE/TSE · perfil do eleitorado e candidaturas",
    layers=[{"type": "bar", "key": "v", "label": "% de mulheres", "color": "neutro", "colorBySide": True}],
    rows=[
        {"x": "População (IBGE 2022)", "v": 49.3, "side": "neutro"},
        {"x": "Eleitorado (2024)", "v": 50.0, "side": "neutro"},
        {"x": "Candidatas 2020", "v": 37.3, "side": "adversario"},
        {"x": "Candidatas 2024", "v": 31.6, "side": "grupo"},
    ],
    unit="pct", yDomain=[0, 60],
))

charts.append(spec(
    "raca_candidatos", "19", "financiamento", "RAÇA OU COR",
    "% da população (IBGE 2022) e dos candidatos a vereador e prefeito", "cartesian", "IBGE · Censo 2022; TSE · candidaturas",
    layers=[
        {"type": "bar", "key": "pop", "label": "População (IBGE 2022)", "color": "neutro"},
        {"type": "bar", "key": "c20", "label": "Candidatos 2020", "color": "adversario"},
        {"type": "bar", "key": "c24", "label": "Candidatos 2024", "color": "grupo"},
    ],
    rows=[
        {"x": "Branca", "pop": 61.4, "c20": 61.3, "c24": 69.7},
        {"x": "Parda", "pop": 34.3, "c20": 29.3, "c24": 22.4},
        {"x": "Preta", "pop": 4.2, "c20": 6.7, "c24": 7.9},
    ],
    unit="pct",
))

# ---- 07 Campanha digital ---------------------------------------------------------------
posts["data"] = pd.to_datetime(posts["data"])
posts["eng"] = posts["likes"] + posts["comentarios"] + posts["compartilhamentos"]
posts = posts.sort_values("data").reset_index(drop=True)
charts.append(spec(
    "campanha_visualizacoes", "20", "campanha", "VISUALIZAÇÕES POR POST",
    "cada barra é um post, da filiação à vitória, 2024", "cartesian", "Registro da campanha digital",
    layers=[{"type": "bar", "key": "views", "label": "Visualizações", "color": "grupo"}],
    rows=[{"x": f"{d.day:02d} {MESES[d.month - 1]}", "views": int(v), "note": str(tema)}
          for d, v, tema in zip(posts["data"], posts["views"], posts["tema"])],
    unit="int", denseX=True,
))

FASES = {"filiacao": "Filiação", "pre-campanha": "Pré-campanha", "lancamento": "Lançamento",
         "campanha": "Campanha", "reta-final": "Reta final", "resultado": "Resultado"}
charts.append(spec(
    "campanha_engajamento", "21", "campanha", "ENGAJAMENTO MÉDIO POR FASE",
    "curtidas + comentários + compartilhamentos por post", "cartesian", "Registro da campanha digital",
    layers=[{"type": "bar", "key": "eng", "label": "Engajamento médio", "color": "grupo"}],
    rows=[{"x": FASES[r.fase], "eng": round(float(r.engajamento_medio), 1), "note": f"{int(r.posts)} posts"}
          for r in campanha_fase.itertuples()],
    unit="int",
))

cat = posts.groupby("categoria").agg(posts=("data", "count"), eng=("eng", "mean")).sort_values("posts", ascending=False)
charts.append(spec(
    "campanha_categorias", "22", "campanha", "VOLUME E ENGAJAMENTO POR TIPO DE CONTEÚDO",
    "posts publicados (barras) e engajamento médio por post (linha)", "cartesian", "Registro da campanha digital",
    layers=[
        {"type": "bar", "key": "posts", "label": "Posts", "color": "muted", "axis": "left"},
        {"type": "line", "key": "eng", "label": "Engajamento médio", "color": "grupo", "axis": "right", "dotsOnly": True},
    ],
    rows=[{"x": str(name).replace("-", " ").capitalize(), "posts": int(r.posts), "eng": round(float(r.eng), 0)}
          for name, r in cat.iterrows()],
    unit="int", rightUnit="int", tiltX=True,
))

# ---- 08 Perfil dos candidatos ---------------------------------------------------------
pat20, pat24 = perfil["patrimonio_prefeito_2020"], perfil["patrimonio_prefeito_2024"]
charts.append(spec(
    "idade_candidatos", "23", "candidatos", "IDADE DOS CANDIDATOS A PREFEITO",
    "em anos, na data da eleição", "panels", "TSE · registro de candidaturas", unit="yr",
    panels=[
        {"title": "2020", "rows": [
            {"label": "Fernando", "value": 73, "side": "adversario"},
            {"label": "Armando Zanata", "value": 64, "side": "terceiro"},
            {"label": "Ronaldo Bianchi", "value": 58, "side": "grupo"},
        ]},
        {"title": "2024", "rows": [
            {"label": "Rolmar Boteccia", "value": 71, "side": "adversario"},
            {"label": "Boldrini", "value": 61, "side": "terceiro"},
            {"label": "Hugo Luiz", "value": 25, "side": "grupo"},
        ]},
    ],
))
charts.append(spec(
    "patrimonio_candidatos", "24", "candidatos", "PATRIMÔNIO DECLARADO",
    "candidatos a prefeito, em reais", "panels", "TSE · bens declarados", unit="brl",
    panels=[
        {"title": "2020", "rows": [
            {"label": "Armando Zanata", "value": pat20["ARMANDO ZANATA"], "side": "terceiro"},
            {"label": "Fernando", "value": pat20["DR FERNANDO"], "side": "adversario"},
            {"label": "Ronaldo Bianchi", "value": pat20["RONALDO BIANCHI"], "side": "grupo"},
        ]},
        {"title": "2024", "rows": [
            {"label": "Rolmar Boteccia", "value": pat24["ROLMAR BOTECCHIA"], "side": "adversario"},
            {"label": "Hugo Luiz", "value": pat24["HUGO LUIZ"], "side": "grupo"},
            {"label": "Boldrini", "value": pat24["BOLDRINI"], "side": "terceiro"},
        ]},
    ],
))

polls = [
    ("ES-09808/2024", "Solução Treinamento Mkt e Pesquisas", "2024-04-19"),
    ("ES-03038/2024", "I9 - Inove Consultoria", "2024-06-20"),
    ("ES-03088/2024", "Direta Propaganda e Eventos", "2024-08-13"),
    ("ES-08806/2024", "Instituto Verita", "2024-08-29"),
    ("ES-08536/2024", "Direta Propaganda e Eventos", "2024-09-11"),
    ("ES-04825/2024", "I9 - Inove Consultoria", "2024-09-18"),
    ("ES-08726/2024", "Direta Propaganda e Eventos", "2024-09-26"),
    ("ES-00808/2024", "Ipopes Pesquisa de Opinião", "2024-09-26"),
    ("ES-06358/2024", "I9 - Inove Consultoria", "2024-09-27"),
]
charts.append(spec(
    "pesquisas_timeline", "25", "candidatos", "REGISTRO DAS 9 PESQUISAS ELEITORAIS",
    "linha do tempo dos registros no TSE, 2024", "timeline", "TSE · PesqEle",
    polls=[{"registro": a, "instituto": b, "data": c} for a, b, c in polls], election="2024-10-06",
))

charts.append(spec(
    "pesquisas_evolucao", "26", "candidatos", "INTENÇÃO DE VOTO ATÉ O RESULTADO",
    "% estimulada entre os candidatos citados; último ponto é o resultado oficial", "cartesian",
    "TSE · PesqEle e resultado oficial",
    layers=[
        {"type": "line", "key": "hugo", "label": "Hugo Luiz (grupo)", "color": "grupo"},
        {"type": "line", "key": "rolmar", "label": "Rolmar Boteccia", "color": "adversario"},
        {"type": "line", "key": "boldrini", "label": "Boldrini", "color": "terceiro"},
    ],
    rows=[
        {"x": "16/abr · Solução", "hugo": 54.8, "rolmar": 21.6, "boldrini": None},
        {"x": "30/ago · Veritá", "hugo": 57.4, "rolmar": 30.8, "boldrini": 11.8},
        {"x": "21/set · Inove", "hugo": 58.12, "rolmar": 28.83, "boldrini": 13.05},
        {"x": "28/set · Ipopes", "hugo": 62.62, "rolmar": 21.31, "boldrini": 16.07},
        {"x": "02/out · I9-Inove", "hugo": 56.97, "rolmar": 32.63, "boldrini": 10.4},
        {"x": "06/out · Resultado TSE", "hugo": 58.05, "rolmar": 31.91, "boldrini": 10.04},
    ],
    unit="pct", yDomain=[0, 70],
))

# --------------------------------------------------------------------------
sections = [
    {"id": "arco", "study": "arco-historico", "eyebrow": "00.1 · Vinte anos de dados", "title": "Cinco derrotas e a virada",
     "short": "Vinte anos"},
    {"id": "achados", "study": "achados", "eyebrow": "04 · Principais achados", "title": "Da derrota generalizada à vitória em todas as urnas",
     "short": "Território"},
    {"id": "camara", "study": "vereadores", "eyebrow": "05 · Desempenho legislativo", "title": "A virada política na Câmara Municipal",
     "short": "Câmara"},
    {"id": "financiamento", "study": "financiamento", "eyebrow": "06 · Financiamento e participação", "title": "Quanto custou, e quem foi votar",
     "short": "Financiamento"},
    {"id": "campanha", "study": "campanha-digital", "eyebrow": "07 · Campanha digital", "title": "O que os posts mostram sobre a corrida",
     "short": "Campanha"},
    {"id": "candidatos", "study": "candidatos", "eyebrow": "08 · Perfil dos candidatos", "title": "Quem eram os candidatos, além dos votos",
     "short": "Candidatos"},
]

masthead = template[: template.index('id="belchior"')]
dek = plain(re.search(r'<p class="dek">(.*?)</p>', masthead, re.S).group(1))
ribbon = []
for n_html, l_html in re.findall(r'<div class="n">(.*?)</div>\s*<div class="l">(.*?)</div>', masthead, re.S):
    after = re.search(r'<span class="after">(.*?)</span>', n_html, re.S)
    before = re.sub(r'<span class="after">.*?</span>', "", n_html, flags=re.S)
    ribbon.append({"before": plain(before), "after": plain(after.group(1)) if after else "", "label": plain(l_html)})
meta = {"dek": dek, "ribbon": ribbon}

TARGET.write_text(
    "// Gerado por scripts/export_frontend_data.py: nao edite a mao.\n"
    "/* eslint-disable */\n"
    "import type { ChartSpec, SectionSpec, MetaSpec } from \"./types\";\n"
    f"export const studyMeta: MetaSpec = {json.dumps(meta, ensure_ascii=False)};\n"
    f"export const studySections: SectionSpec[] = {json.dumps(sections, ensure_ascii=False)};\n"
    f"export const studyCharts: ChartSpec[] = {json.dumps(charts, ensure_ascii=False)};\n",
    encoding="utf-8",
)
print(f"Escrito {TARGET} ({len(charts)} graficos)")
missing = [c["slug"] for c in charts if not c["caption"]]
print("Sem legenda extraida do estudo:", missing)
