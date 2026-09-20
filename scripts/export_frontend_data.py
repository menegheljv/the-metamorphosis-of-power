# -*- coding: utf-8 -*-
"""Exporta os dados do estudo para os graficos interativos (frontend/src/studyData.ts).

Cada figura do estudo vira uma especificacao tipada (tipo de grafico, series, cores
semanticas, unidade) em portugues e em ingles, e nao um dump cru de CSV. O titulo
de cada grafico e o texto alternativo (alt) sao lidos do proprio template do estudo,
para o grafico interativo nunca divergir do texto ao redor.

Uso:
  python scripts/distritos_votos_absolutos.py   # gera output/distritos_votos_abs.csv
  python scripts/export_frontend_data.py
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

MESES = {
    "pt": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}

FASES = {
    "pt": {"filiacao": "Filiação", "pre-campanha": "Pré-campanha", "lancamento": "Lançamento",
           "campanha": "Campanha", "reta-final": "Reta final", "resultado": "Resultado"},
    "en": {"filiacao": "Affiliation", "pre-campanha": "Pre-campaign", "lancamento": "Launch",
           "campanha": "Campaign", "reta-final": "Home stretch", "resultado": "Result"},
}
CATEGORIAS = {
    "pt": {"evento": "Evento", "proposta": "Proposta", "coligacao": "Coligação", "administrativo": "Administrativo",
           "testemunho": "Testemunho", "resposta-ataque": "Resposta a ataque", "contagem-regressiva": "Contagem regressiva",
           "pesquisa": "Pesquisa", "data-comemorativa": "Data comemorativa", "resultado": "Resultado", "marco": "Marco",
           "midia": "Mídia", "filiacao": "Filiação"},
    "en": {"evento": "Event / walk", "proposta": "Policy proposal", "coligacao": "Coalition / endorsement",
           "administrativo": "Administrative (council)", "testemunho": "Testimonial", "resposta-ataque": "Response to attack",
           "contagem-regressiva": "Countdown", "pesquisa": "Election poll", "data-comemorativa": "Commemorative date",
           "resultado": "Result", "marco": "Milestone", "midia": "Media", "filiacao": "Affiliation"},
}


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


def plain(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text).replace("%%", "%")
    return re.sub(r"\s+", " ", text).strip()


def read_study_text(template_path: Path, word: str) -> dict[str, dict[str, str]]:
    """Legenda (figcaption), cap e alt de cada figura numerada do estudo."""
    template = template_path.read_text(encoding="utf-8")
    found: dict[str, dict[str, str]] = {}
    for block in re.findall(r'<figure class="exhibit">(.*?)</figure>', template, re.S):
        tag = re.search(r'class="tag">([^<]*)<', block)
        cap = re.search(r'class="cap">([^<]*)<', block)
        alt = re.search(r'alt="([^"]*)"', block)
        fig = re.search(r"<figcaption>(.*?)</figcaption>", block, re.S)
        if not tag:
            continue
        found[tag.group(1).replace(word, "").strip()] = {
            "cap": plain(cap.group(1)) if cap else "",
            "alt": plain(alt.group(1)) if alt else "",
            "caption": plain(fig.group(1)) if fig else "",
        }
    return found


# --------------------------------------------------------------------------
# Dados (iguais nos dois idiomas)
# --------------------------------------------------------------------------
resumo = pd.read_csv(OUT / "resumo_prefeito_2004_2024.csv")
comp = pd.read_csv(OUT / "comparativo_candidato_prefeito_por_secao.csv").sort_values("NR_SECAO")
distritos = pd.read_csv(OUT / "distritos_resumo.csv")
dist_votos = pd.read_csv(OUT / "distritos_votos_abs.csv")
dist_ver = pd.read_csv(OUT / "votos_vereadores_grupo_por_distrito_pct.csv")
comparecimento = pd.read_csv(OUT / "comparecimento_historico.csv")
ibge = pd.read_csv(OUT / "ibge_cruzamento.csv")
coerencia = pd.read_csv(OUT / "coerencia_voto.csv")
campanha_fase = pd.read_csv(OUT / "campanha_digital_resumo.csv")
posts = pd.read_csv(DATA / "campanha_digital_posts.csv", sep=";")
ver_summary = json.loads((OUT / "vereadores_summary.json").read_text(encoding="utf-8"))
extra = json.loads((OUT / "extra_summary.json").read_text(encoding="utf-8"))
perfil = json.loads((OUT / "candidate_profile_summary.json").read_text(encoding="utf-8"))
fin = pd.read_csv(OUT / "powerbi" / "financiamento.csv")

posts["data"] = pd.to_datetime(posts["data"])
posts["eng"] = posts["likes"] + posts["comentarios"] + posts["compartilhamentos"]
posts = posts.sort_values("data").reset_index(drop=True)

# Principal candidatura de oposicao ao grupo em cada eleicao: quem venceu (2004-2020) e,
# em 2024, quando o grupo venceu, o segundo colocado (resultado oficial do TSE: 31,91%).
OPOSICAO_2024 = ("Rolmar Boteccia", 31.9)


def vereadores(year: int):
    df = pd.read_csv(OUT / f"vereadores_eleitos_{year}_com_lado.csv", dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    df["votos"] = pd.to_numeric(df["QT_VOTOS_NOMINAIS_VALIDOS"], errors="coerce")
    df = df.sort_values("votos", ascending=False)
    side = {"GRUPO": "grupo", "NOSSOS": "grupo"}
    return [
        {"label": title_case(r["NM_URNA_CANDIDATO"]), "value": int(r["votos"]),
         "side": side.get(str(r["LADO"]).strip().upper(), "adversario"), "note": r["SG_PARTIDO"]}
        for _, r in df.iterrows()
    ]


def build(lang: str) -> list[dict]:
    en = lang == "en"

    def L(pt, en_):
        return en_ if en else pt

    def dec(x: float, nd: int = 1) -> str:
        s = f"{x:.{nd}f}"
        return s if en else s.replace(".", ",")

    def thou(n: float) -> str:
        s = f"{int(round(n)):,}"
        return s if en else s.replace(",", ".")

    study_text = read_study_text(
        OUT / ("template_en.html" if en else "template.html"), "Figure " if en else "Figura ")

    def spec(slug, figure, title, subtitle, kind, **body):
        txt = study_text.get(figure, {})
        return {
            "slug": slug,
            "figure": (f"{L('Figura', 'Figure')} {figure}" if figure[:1].isdigit() else figure),
            "title": title, "subtitle": subtitle, "kind": kind,
            "cap": txt.get("cap", ""), "caption": txt.get("caption", ""), "alt": txt.get("alt", ""),
            **body,
        }

    charts: list[dict] = []

    # ---- 00.1 Vinte anos de dados: grupo x oposicao -------------------------------
    rows, opp_pct = [], {}
    for _, r in resumo.iterrows():
        ano = int(r["ano"])
        if ano == 2024:
            opp_name, opp = OPOSICAO_2024
        else:
            opp_name, opp = title_case(r["vencedor"]), float(r["pct_vencedor"])
        opp_pct[ano] = opp
        rows.append({
            "x": str(ano),
            "oposicao": clean(opp),
            "grupo": clean(r["pct_candidato_do_grupo"]),
            "note": f"{L('Grupo', 'Group')}: {title_case(r['candidato_do_grupo'])} · {L('Oposição', 'Opposition')}: {opp_name}",
        })
    g = {int(r.ano): float(r.pct_candidato_do_grupo) for r in resumo.itertuples()}
    charts.append(spec(
        "historical_arc", L("Arco histórico", "Historical arc"),
        L("CINCO DERROTAS E A VIRADA", "FIVE LOSSES AND THE TURNAROUND"),
        L("% dos votos válidos para prefeito: grupo vs. oposição, 2004–2024",
          "% of valid votes for mayor: group vs. opposition, 2004–2024"),
        "cartesian",
        layers=[
            {"type": "line", "key": "oposicao", "label": L("Oposição", "Opposition"), "color": "adversario"},
            {"type": "line", "key": "grupo", "label": L("Grupo", "Group"), "color": "grupo"},
        ],
        rows=rows, unit="pct", yDomain=[0, 80],
        cap=L("Votação do grupo e da principal candidatura de oposição, 2004–2024",
              "Vote share of the group and of the main opposition candidacy, 2004–2024"),
        caption=L(
            f"Em cinco eleições consecutivas a principal candidatura de oposição superou o grupo, com a distância caindo de "
            f"{dec(opp_pct[2004])}% a {dec(g[2004])}% em 2004 para {dec(opp_pct[2016])}% a {dec(g[2016])}% em 2016. "
            f"Em 2024 a relação se inverte: o candidato do grupo obtém {dec(g[2024])}% e a principal oposição, {dec(opp_pct[2024])}%.",
            f"In five consecutive elections the main opposition candidacy beat the group, with the gap narrowing from "
            f"{dec(opp_pct[2004])}% to {dec(g[2004])}% in 2004 to {dec(opp_pct[2016])}% to {dec(g[2016])}% in 2016. "
            f"In 2024 the relationship flips: the group's candidate gets {dec(g[2024])}% and the main opposition, {dec(opp_pct[2024])}%."),
        alt=L(
            "Gráfico de linhas com a votação para prefeito do grupo e da principal candidatura de oposição em seis eleições, "
            "de 2004 a 2024. O grupo vai de 26,4% em 2004 a 48,0% em 2016, cai a 40,0% em 2020 e chega a 58,1% em 2024; "
            "a oposição fica acima do grupo até 2020 (de 66,9% a 56,4%) e cai a 31,9% em 2024.",
            "Line chart with the mayoral vote share of the group and of the main opposition candidacy in six elections, "
            "from 2004 to 2024. The group goes from 26.4% in 2004 to 48.0% in 2016, falls to 40.0% in 2020 and reaches 58.1% "
            "in 2024; the opposition stays above the group through 2020 (from 66.9% to 56.4%) and drops to 31.9% in 2024."),
    ))

    # ---- 04 Da derrota generalizada a vitoria ------------------------------------------
    slope_rows = [{
        "secao": int(r["NR_SECAO"]),
        "local": str(r["local_votacao"]).strip() if pd.notna(r["local_votacao"]) else "",
        "a": clean(r["pct_2020"]), "b": clean(r["pct_2024"]),
    } for _, r in comp.iterrows()]
    charts.append(spec(
        "slope", "3", L("A VIRADA, SEÇÃO A SEÇÃO", "THE TURNAROUND, PRECINCT BY PRECINCT"),
        L("% de votos do candidato do grupo em cada seção, 2020 → 2024",
          "% of votes for the group's candidate in each precinct, 2020 → 2024"),
        "slope", rows=slope_rows, aLabel="2020", bLabel="2024"))

    tiles = []
    for _, r in comp.iterrows():
        cat = "nova" if pd.isna(r["vencedor_2020"]) else ("ja" if "BIANCHI" in str(r["vencedor_2020"]) else "virou")
        tiles.append({"secao": int(r["NR_SECAO"]), "cat": cat,
                      "local": str(r["local_votacao"]).strip() if pd.notna(r["local_votacao"]) else "",
                      "a": clean(r["pct_2020"]), "b": clean(r["pct_2024"])})
    charts.append(spec(
        "grid", "4", L("AS 42 SEÇÕES ELEITORAIS DE 2024", "ALL 42 VOTING PRECINCTS IN 2024"),
        L("Toque ou passe o mouse para ver o local de votação de cada seção",
          "Tap or hover to see the polling place of each precinct"),
        "grid", tiles=tiles))

    charts.append(spec(
        "municipio", "5", L("RESULTADO AGREGADO DO MUNICÍPIO", "CITYWIDE RESULT"),
        L("total de votos do candidato do grupo a prefeito, 2020 vs. 2024",
          "total votes for the group's mayoral candidate, 2020 vs. 2024"),
        "cartesian",
        layers=[{"type": "bar", "key": "votos", "label": L("Votos do candidato do grupo", "Votes for the group's candidate"),
                 "color": "grupo", "colorBySide": True}],
        rows=[{"x": "2020", "votos": 3681, "side": "adversario", "note": L("37,8% da votação", "37.8% of the vote")},
              {"x": "2024", "votos": 5779, "side": "grupo", "note": L("56,4% da votação", "56.4% of the vote")}],
        unit="int",
        caption=L("Em 2024, o candidato do grupo somou 5.779 votos (56,4%), contra 3.681 (37,8%) em 2020: mais de 2.000 votos a mais no mesmo município.",
                  "In 2024 the group's candidate totaled 5,779 votes (56.4%), against 3,681 (37.8%) in 2020: more than 2,000 additional votes in the same city."),
        alt=L("Gráfico de barras: 3.681 votos (37,8%) em 2020 e 5.779 votos (56,4%) em 2024.",
              "Bar chart: 3,681 votes (37.8%) in 2020 and 5,779 votes (56.4%) in 2024.")))

    charts.append(spec(
        "distritos_heatmap", "6", L("ONDE O GRUPO ERA FORTE", "WHERE THE GROUP WAS STRONG"),
        L("% do candidato do grupo para prefeito, por distrito, 2004–2024",
          "% for the group's mayoral candidate, by district, 2004–2024"),
        "heatmap", columns=[str(c) for c in distritos.columns[1:]],
        rows=[{"label": r["distrito"], "values": [clean(round(float(r[c]), 1)) for c in distritos.columns[1:]]}
              for _, r in distritos.iterrows()]))

    charts.append(spec(
        "distritos_vereadores_heatmap", "6.1", L("ONDE A CHAPA DE VEREADOR ERA FORTE", "WHERE THE COUNCIL SLATE WAS STRONG"),
        L("% dos votos para vereador na chapa do grupo, por distrito, 2020 e 2024",
          "% of council votes for the group's slate, by district, 2020 and 2024"),
        "heatmap", columns=[str(c) for c in dist_ver.columns[1:]],
        rows=[{"label": r["distrito"], "values": [clean(float(r[c])) for c in dist_ver.columns[1:]]}
              for _, r in dist_ver.iterrows()]))

    # ---- 6.2 Votos totais por distrito (novo) ---------------------------------------------
    order = ["Sede", "Crubixá", "Ibitiruí", "Matilde", "Ribeirão do Cristo", "Sagrada Família", "São Bento de Urânia"]
    panels, gv = [], {}
    for d in order:
        sub = dist_votos[dist_votos["distrito"] == d].sort_values("ano")
        prows = []
        for r in sub.itertuples():
            outros = int(r.votos_validos) - int(r.votos_grupo)
            prows.append({"x": str(int(r.ano)), "grupo": int(r.votos_grupo), "outros": outros, "total": int(r.votos_validos),
                          "note": L(f"{dec(r.votos_grupo / r.votos_validos * 100)}% dos votos válidos do distrito",
                                    f"{dec(r.votos_grupo / r.votos_validos * 100)}% of the district's valid votes")})
            gv[(d, int(r.ano))] = int(r.votos_grupo)
        panels.append({"title": d, "rows": prows})
    tot = {a: sum(gv[(d, a)] for d in order) for a in (2004, 2008, 2012, 2016, 2020, 2024)}
    assert all(gv[(d, 2024)] == max(gv[(d, a)] for a in tot) for d in order), "2024 deixou de ser o pico em algum distrito"
    fora20, fora24 = tot[2020] - gv[("Sede", 2020)], tot[2024] - gv[("Sede", 2024)]
    charts.append(spec(
        "distritos_votos", "6.2", L("VOTOS POR DISTRITO, ELEIÇÃO A ELEIÇÃO", "VOTES BY DISTRICT, ELECTION BY ELECTION"),
        L("votos totais para prefeito: candidato do grupo e demais candidatos, 2004–2024 (cada distrito tem escala própria)",
          "total mayoral votes: the group's candidate and all other candidates, 2004–2024 (each district has its own scale)"),
        "multiples",
        layers=[
            {"type": "bar", "key": "grupo", "label": L("Candidato do grupo", "Group's candidate"), "color": "grupo", "stackId": "v"},
            {"type": "bar", "key": "outros", "label": L("Demais candidatos", "All other candidates"), "color": "muted", "stackId": "v"},
        ],
        panels=panels, unit="int",
        cap=L("Votos totais para prefeito por distrito, 2004–2024", "Total mayoral votes by district, 2004–2024"),
        caption=L(
            f"A Sede concentra a maior parte dos votos em todas as eleições: {thou(gv[('Sede', 2024)])} dos {thou(tot[2024])} votos do "
            f"candidato do grupo em 2024 ({dec(gv[('Sede', 2024)] / tot[2024] * 100)}%). Nos seis outros distritos somados, o grupo passa de "
            f"{thou(fora20)} votos em 2020 para {thou(fora24)} em 2024 (+{dec((fora24 / fora20 - 1) * 100, 0)}%), e em todos os sete "
            f"distritos 2024 é a eleição com mais votos do grupo em toda a série.",
            f"Sede holds most of the votes in every election: {thou(gv[('Sede', 2024)])} of the group candidate's {thou(tot[2024])} votes in "
            f"2024 ({dec(gv[('Sede', 2024)] / tot[2024] * 100)}%). Across the other six districts combined, the group goes from "
            f"{thou(fora20)} votes in 2020 to {thou(fora24)} in 2024 (+{dec((fora24 / fora20 - 1) * 100, 0)}%), and in all seven "
            f"districts 2024 is the election with the group's highest vote count in the whole series."),
        alt=L("Sete pequenos gráficos de barras empilhadas, um por distrito, com os votos totais para prefeito em cada eleição de 2004 a 2024, "
              "separando o candidato do grupo dos demais candidatos.",
              "Seven small stacked bar charts, one per district, with total mayoral votes in each election from 2004 to 2024, "
              "separating the group's candidate from all other candidates.")))

    # ---- 05 Camara Municipal ------------------------------------------------------------------
    charts.append(spec(
        "camara", "7", L("COMPOSIÇÃO DA CÂMARA MUNICIPAL", "CITY COUNCIL COMPOSITION"),
        L("cadeiras por lado, 2020 vs. 2024", "seats by side, 2020 vs. 2024"), "cartesian",
        layers=[{"type": "bar", "key": "adversarios", "label": L("Adversários", "Opponents"), "color": "adversario"},
                {"type": "bar", "key": "grupo", "label": L("Chapa do grupo", "Group's slate"), "color": "grupo"}],
        rows=[{"x": "2020", "adversarios": 6, "grupo": 3}, {"x": "2024", "adversarios": 4, "grupo": 5}],
        unit="int", yDomain=[0, 9]))

    v20, v24 = ver_summary["votos_2020_nossos"], ver_summary["votos_2024_nossos"]
    t20, t24 = ver_summary["votos_2020_total"], ver_summary["votos_2024_total"]
    charts.append(spec(
        "votos_vereadores", "8", L("VOTAÇÃO TOTAL DA CHAPA DE VEREADOR", "TOTAL VOTES FOR THE COUNCIL SLATE"),
        L("soma de votos nominais dos candidatos a vereador da chapa", "sum of nominal votes for the slate's council candidates"),
        "cartesian",
        layers=[{"type": "bar", "key": "votos", "label": L("Votos da chapa", "Slate votes"), "color": "grupo", "colorBySide": True}],
        rows=[{"x": "2020", "votos": v20, "side": "adversario", "note": L(f"{dec(v20 / t20 * 100)}% do pleito", f"{dec(v20 / t20 * 100)}% of the vote")},
              {"x": "2024", "votos": v24, "side": "grupo", "note": L(f"{dec(v24 / t24 * 100)}% do pleito", f"{dec(v24 / t24 * 100)}% of the vote")}],
        unit="int"))

    charts.append(spec("vereadores_2020", "9", L("VEREADORES ELEITOS EM 2020", "COUNCIL MEMBERS ELECTED IN 2020"),
                       L("votos nominais, por lado", "nominal votes, by side"), "panels", unit="int",
                       panels=[{"rows": vereadores(2020)}]))
    charts.append(spec("vereadores_2024", "10", L("VEREADORES ELEITOS EM 2024", "COUNCIL MEMBERS ELECTED IN 2024"),
                       L("votos nominais, por lado", "nominal votes, by side"), "panels", unit="int",
                       panels=[{"rows": vereadores(2024)}]))

    charts.append(spec(
        "coerencia_voto", "11", L("PREFEITO × VEREADOR, SEÇÃO A SEÇÃO", "MAYOR × COUNCIL, PRECINCT BY PRECINCT"),
        L("% do grupo para prefeito (x) e para vereador (y) em cada seção",
          "% for the group in the mayoral race (x) and the council race (y), per precinct"),
        "scatter",
        series=[{"key": str(ano), "label": str(ano), "color": "adversario" if ano == 2020 else "grupo",
                 "points": [{"x": clean(r.pct_prefeito_nosso), "y": clean(r.pct_vereador_nosso), "secao": int(r.secao)}
                            for r in coerencia[coerencia["ano"] == ano].itertuples()]} for ano in (2020, 2024)]))

    # ---- 06 Financiamento e participacao --------------------------------------------------
    side_of = {"Fernando (PSB, eleito)": "adversario", "Bianchi (Republicanos, grupo)": "grupo", "Zanata (PDT)": "terceiro",
               "Hugo Luiz (PP, grupo, eleito)": "grupo", "Boldrini (PL)": "terceiro", "Boteccia (PSB)": "adversario"}
    short = {"Bianchi (Republicanos, grupo)": "Bianchi (Republicanos)",
             "Hugo Luiz (PP, grupo, eleito)": L("Hugo Luiz (PP, eleito)", "Hugo Luiz (PP, elected)"),
             "Fernando (PSB, eleito)": L("Fernando (PSB, eleito)", "Fernando (PSB, elected)")}

    def fin_panels(col):
        return [{"title": str(ano), "rows": [
            {"label": short.get(r["Candidato"], r["Candidato"]), "value": float(r[col]), "side": side_of[r["Candidato"]]}
            for _, r in fin[fin["Ano"] == ano].sort_values(col, ascending=False).iterrows()]} for ano in (2020, 2024)]

    charts.append(spec("financeiro_chapa", "12", L("RECEITA DECLARADA", "DECLARED REVENUE"),
                       L("candidatos a prefeito, em reais", "mayoral candidates, in reais"), "panels", unit="brl",
                       panels=fin_panels("Receita")))
    charts.append(spec("custo_por_voto", "13", L("CUSTO POR VOTO", "COST PER VOTE"),
                       L("reais gastos por voto, candidatos a prefeito", "reais spent per vote, mayoral candidates"), "panels",
                       unit="brl2", panels=fin_panels("Custo_Por_Voto")))

    origem = [("Partido político", "Political party", 57460.0, 166372.43), ("Recursos próprios", "Own funds", 22030.8, 34547.11),
              ("Pessoas físicas", "Individual donors", 14440.2, 18648.65), ("Outros candidatos", "Other candidates", 2625.0, 7000.0)]
    charts.append(spec(
        "origem_receitas", "14", L("ORIGEM DAS RECEITAS DA CHAPA", "WHERE THE TICKET'S MONEY CAME FROM"),
        L("em reais, 2020 vs. 2024", "in reais, 2020 vs. 2024"), "cartesian",
        layers=[{"type": "bar", "key": "y2020", "label": "2020", "color": "adversario"},
                {"type": "bar", "key": "y2024", "label": "2024", "color": "grupo"}],
        rows=[{"x": L(pt, en_), "y2020": a, "y2024": b} for pt, en_, a, b in origem], unit="brl"))

    t = extra["turnout"]
    charts.append(spec(
        "comparecimento", "15", L("COMPARECIMENTO VS. ABSTENÇÃO", "TURNOUT VS. ABSTENTION"),
        L("eleitores aptos, 2020 e 2024", "registered voters, 2020 and 2024"), "cartesian",
        layers=[{"type": "bar", "key": "comparecimento", "label": L("Compareceram", "Voted"), "color": "info", "stackId": "a"},
                {"type": "bar", "key": "abstencao", "label": L("Abstenções", "Abstentions"), "color": "muted", "stackId": "a"}],
        rows=[{"x": "2020", "comparecimento": t["comparecimento_2020"], "abstencao": t["abstencoes_2020"],
               "note": L(f"{dec(t['pct_comparecimento_2020'], 2)}% de comparecimento", f"{dec(t['pct_comparecimento_2020'], 2)}% turnout")},
              {"x": "2024", "comparecimento": t["comparecimento_2024"], "abstencao": t["abstencoes_2024"],
               "note": L(f"{dec(t['pct_comparecimento_2024'], 2)}% de comparecimento", f"{dec(t['pct_comparecimento_2024'], 2)}% turnout")}],
        unit="int"))

    charts.append(spec(
        "comparecimento_historico", "16", L("COMPARECIMENTO EM QUEDA", "TURNOUT DOWN"),
        L("eleitores aptos (barras) e % de comparecimento (linha), 2004–2024",
          "registered voters (bars) and turnout % (line), 2004–2024"), "cartesian",
        layers=[{"type": "bar", "key": "aptos", "label": L("Eleitores aptos", "Registered voters"), "color": "muted", "axis": "left"},
                {"type": "line", "key": "pct", "label": L("% de comparecimento", "Turnout %"), "color": "info", "axis": "right"}],
        rows=[{"x": str(int(r.ano)), "aptos": int(r.aptos), "pct": clean(r.pct_comparecimento)} for r in comparecimento.itertuples()],
        unit="int", rightUnit="pct", rightDomain=[70, 100]))

    charts.append(spec(
        "ibge_eleitorado", "17", L("ELEITORES APTOS / POPULAÇÃO", "REGISTERED VOTERS / POPULATION"),
        L("% da população estimada (IBGE) registrada para votar", "% of the estimated population (IBGE) registered to vote"),
        "cartesian",
        layers=[{"type": "line", "key": "pct", "label": L("Eleitores aptos como % da população", "Registered voters as % of population"), "color": "info"}],
        rows=[{"x": str(int(r.ano)), "pct": clean(r.pct_populacao_registrada),
               "note": L(f"{thou(r.eleitores_aptos)} aptos · {thou(r.populacao_estimada_ibge)} habitantes",
                         f"{thou(r.eleitores_aptos)} registered · {thou(r.populacao_estimada_ibge)} inhabitants")}
              for r in ibge.itertuples()],
        unit="pct", yDomain=[50, 100]))

    charts.append(spec(
        "genero_candidatos", "18", L("PARTICIPAÇÃO FEMININA", "FEMALE PARTICIPATION"),
        L("% de mulheres na população, no eleitorado e entre os candidatos", "% women in the population, the electorate and among candidates"),
        "cartesian",
        layers=[{"type": "bar", "key": "v", "label": L("% de mulheres", "% women"), "color": "neutro", "colorBySide": True}],
        rows=[{"x": L("População (IBGE 2022)", "Population (IBGE 2022)"), "v": 49.3, "side": "neutro"},
              {"x": L("Eleitorado (2024)", "Electorate (2024)"), "v": 50.0, "side": "neutro"},
              {"x": L("Candidatas 2020", "Female candidates 2020"), "v": 37.3, "side": "adversario"},
              {"x": L("Candidatas 2024", "Female candidates 2024"), "v": 31.6, "side": "grupo"}],
        unit="pct", yDomain=[0, 60]))

    charts.append(spec(
        "raca_candidatos", "19", L("RAÇA OU COR", "RACE OR COLOR"),
        L("% da população (IBGE 2022) e dos candidatos", "% of the population (IBGE 2022) and of candidates"), "cartesian",
        layers=[{"type": "bar", "key": "pop", "label": L("População (IBGE 2022)", "Population (IBGE 2022)"), "color": "neutro"},
                {"type": "bar", "key": "c20", "label": L("Candidatos 2020", "Candidates 2020"), "color": "adversario"},
                {"type": "bar", "key": "c24", "label": L("Candidatos 2024", "Candidates 2024"), "color": "grupo"}],
        rows=[{"x": L("Branca", "White"), "pop": 61.4, "c20": 61.3, "c24": 69.7},
              {"x": L("Parda", "Brown"), "pop": 34.3, "c20": 29.3, "c24": 22.4},
              {"x": L("Preta", "Black"), "pop": 4.2, "c20": 6.7, "c24": 7.9}],
        unit="pct"))

    # ---- 07 Campanha digital -----------------------------------------------------------------
    meses = MESES[lang]

    def day(d):
        return f"{meses[d.month - 1]} {d.day}" if en else f"{d.day:02d} {meses[d.month - 1]}"

    charts.append(spec(
        "campanha_visualizacoes", "20", L("VISUALIZAÇÕES POR POST", "VIEWS PER POST"),
        L("cada barra é um post, da filiação à vitória, 2024", "each bar is one post, from affiliation to the win, 2024"), "cartesian",
        layers=[{"type": "bar", "key": "views", "label": L("Visualizações", "Views"), "color": "grupo"}],
        rows=[{"x": day(d), "views": int(v), "note": str(tema)} for d, v, tema in zip(posts["data"], posts["views"], posts["tema"])],
        unit="int", denseX=True))

    charts.append(spec(
        "campanha_engajamento", "21", L("ENGAJAMENTO MÉDIO POR FASE", "AVERAGE ENGAGEMENT BY PHASE"),
        L("curtidas + comentários + compartilhamentos por post", "likes + comments + shares per post"), "cartesian",
        layers=[{"type": "bar", "key": "eng", "label": L("Engajamento médio", "Average engagement"), "color": "grupo"}],
        rows=[{"x": FASES[lang][r.fase], "eng": round(float(r.engajamento_medio), 1), "note": L(f"{int(r.posts)} posts", f"{int(r.posts)} posts")}
              for r in campanha_fase.itertuples()],
        unit="int"))

    cat = posts.groupby("categoria").agg(n=("data", "count"), eng=("eng", "mean")).sort_values("n", ascending=False)
    charts.append(spec(
        "campanha_categorias", "22", L("VOLUME E ENGAJAMENTO POR TIPO DE CONTEÚDO", "VOLUME AND ENGAGEMENT BY CONTENT TYPE"),
        L("posts publicados (barras) e engajamento médio por post (pontos)", "posts published (bars) and average engagement per post (dots)"),
        "cartesian",
        layers=[{"type": "bar", "key": "posts", "label": "Posts", "color": "muted", "axis": "left"},
                {"type": "line", "key": "eng", "label": L("Engajamento médio", "Average engagement"), "color": "grupo", "axis": "right", "dotsOnly": True}],
        rows=[{"x": CATEGORIAS[lang].get(name, name), "posts": int(r.n), "eng": round(float(r.eng), 0)} for name, r in cat.iterrows()],
        unit="int", rightUnit="int", tiltX=True))

    # ---- 08 Perfil dos candidatos ---------------------------------------------------------------
    pat20, pat24 = perfil["patrimonio_prefeito_2020"], perfil["patrimonio_prefeito_2024"]
    charts.append(spec(
        "idade_candidatos", "23", L("IDADE DOS CANDIDATOS A PREFEITO", "AGE OF MAYORAL CANDIDATES"),
        L("em anos, na data da eleição", "in years, on election day"), "panels", unit="yr",
        panels=[{"title": "2020", "rows": [{"label": "Fernando", "value": 73, "side": "adversario"},
                                          {"label": "Armando Zanata", "value": 64, "side": "terceiro"},
                                          {"label": "Ronaldo Bianchi", "value": 58, "side": "grupo"}]},
                {"title": "2024", "rows": [{"label": "Rolmar Boteccia", "value": 71, "side": "adversario"},
                                          {"label": "Boldrini", "value": 61, "side": "terceiro"},
                                          {"label": "Hugo Luiz", "value": 25, "side": "grupo"}]}]))
    charts.append(spec(
        "patrimonio_candidatos", "24", L("PATRIMÔNIO DECLARADO", "DECLARED NET WORTH"),
        L("candidatos a prefeito, em reais", "mayoral candidates, in reais"), "panels", unit="brl",
        panels=[{"title": "2020", "rows": [{"label": "Armando Zanata", "value": pat20["ARMANDO ZANATA"], "side": "terceiro"},
                                          {"label": "Fernando", "value": pat20["DR FERNANDO"], "side": "adversario"},
                                          {"label": "Ronaldo Bianchi", "value": pat20["RONALDO BIANCHI"], "side": "grupo"}]},
                {"title": "2024", "rows": [{"label": "Rolmar Boteccia", "value": pat24["ROLMAR BOTECCHIA"], "side": "adversario"},
                                          {"label": "Hugo Luiz", "value": pat24["HUGO LUIZ"], "side": "grupo"},
                                          {"label": "Boldrini", "value": pat24["BOLDRINI"], "side": "terceiro"}]}]))

    polls = [("ES-09808/2024", "Solução Treinamento Mkt e Pesquisas", "2024-04-19"), ("ES-03038/2024", "I9 - Inove Consultoria", "2024-06-20"),
             ("ES-03088/2024", "Direta Propaganda e Eventos", "2024-08-13"), ("ES-08806/2024", "Instituto Verita", "2024-08-29"),
             ("ES-08536/2024", "Direta Propaganda e Eventos", "2024-09-11"), ("ES-04825/2024", "I9 - Inove Consultoria", "2024-09-18"),
             ("ES-08726/2024", "Direta Propaganda e Eventos", "2024-09-26"), ("ES-00808/2024", "Ipopes Pesquisa de Opinião", "2024-09-26"),
             ("ES-06358/2024", "I9 - Inove Consultoria", "2024-09-27")]
    charts.append(spec(
        "pesquisas_timeline", "25", L("REGISTRO DAS 9 PESQUISAS ELEITORAIS", "REGISTRATION OF THE 9 ELECTION POLLS"),
        L("linha do tempo dos registros no TSE, 2024", "timeline of registrations with the TSE, 2024"), "timeline",
        polls=[{"registro": a, "instituto": b, "data": c} for a, b, c in polls], election="2024-10-06"))

    tse = L("Resultado TSE", "TSE result")
    charts.append(spec(
        "pesquisas_evolucao", "26", L("INTENÇÃO DE VOTO ATÉ O RESULTADO", "VOTING INTENTION THROUGH TO THE RESULT"),
        L("% estimulada entre os candidatos citados; último ponto é o resultado oficial",
          "% prompted among named candidates; the last point is the official result"), "cartesian",
        layers=[{"type": "line", "key": "hugo", "label": L("Hugo Luiz (grupo)", "Hugo Luiz (group)"), "color": "grupo"},
                {"type": "line", "key": "rolmar", "label": "Rolmar Boteccia", "color": "adversario"},
                {"type": "line", "key": "boldrini", "label": "Boldrini", "color": "terceiro"}],
        rows=[{"x": L("16/abr · Solução", "Apr 16 · Solução"), "hugo": 54.8, "rolmar": 21.6, "boldrini": None},
              {"x": L("30/ago · Veritá", "Aug 30 · Veritá"), "hugo": 57.4, "rolmar": 30.8, "boldrini": 11.8},
              {"x": L("21/set · Inove", "Sep 21 · Inove"), "hugo": 58.12, "rolmar": 28.83, "boldrini": 13.05},
              {"x": L("28/set · Ipopes", "Sep 28 · Ipopes"), "hugo": 62.62, "rolmar": 21.31, "boldrini": 16.07},
              {"x": L("02/out · I9-Inove", "Oct 2 · I9-Inove"), "hugo": 56.97, "rolmar": 32.63, "boldrini": 10.4},
              {"x": L("06/out · ", "Oct 6 · ") + tse, "hugo": 58.05, "rolmar": 31.91, "boldrini": 10.04}],
        unit="pct", yDomain=[0, 70]))

    return charts


pt, en = build("pt"), build("en")
missing = [f'{c["slug"]}/{lang}' for lang, lst in (("pt", pt), ("en", en)) for c in lst if not c["caption"] and c["slug"] != "distritos_votos"]
TARGET.write_text(
    "// Gerado por scripts/export_frontend_data.py: nao edite a mao.\n"
    "/* eslint-disable */\n"
    "import type { ChartSpec } from \"./types\";\n"
    f"export const studyChartsPt: ChartSpec[] = {json.dumps(pt, ensure_ascii=False)};\n"
    f"export const studyChartsEn: ChartSpec[] = {json.dumps(en, ensure_ascii=False)};\n",
    encoding="utf-8",
)
print(f"Escrito {TARGET} ({len(pt)} graficos x 2 idiomas)")
print("Sem legenda extraida do estudo:", missing)
