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
import math
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
prefs = pd.read_csv(OUT / "prefeitos_todos.csv")
dcand = pd.read_csv(OUT / "distritos_votos_cand.csv")

posts["data"] = pd.to_datetime(posts["data"])
posts["eng"] = posts["likes"] + posts["comentarios"] + posts["compartilhamentos"]
posts = posts.sort_values("data").reset_index(drop=True)

# Principal candidatura de oposicao ao grupo em cada eleicao: quem venceu (2004-2020) e,
# em 2024, quando o grupo venceu, o segundo colocado (resultado oficial do TSE: 31,91%).
OPOSICAO_2024 = ("Rolmar Boteccia", 31.9)


# --------------------------------------------------------------------------
# Mapa dos distritos: limites do IBGE (Censo 2022) projetados para SVG
# --------------------------------------------------------------------------
DISTRITO_NOME = {"Alfredo Chaves": "Sede", "Urânia": "São Bento de Urânia"}


def _rdp(points, tol):
    if len(points) < 3:
        return points
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-12
    idx, dmax = 0, 0.0
    for i in range(1, len(points) - 1):
        d = abs(dy * points[i][0] - dx * points[i][1] + x2 * y1 - y2 * x1) / norm
        if d > dmax:
            idx, dmax = i, d
    if dmax > tol:
        return _rdp(points[: idx + 1], tol)[:-1] + _rdp(points[idx:], tol)
    return [points[0], points[-1]]


def _inside(x, y, ring):
    ins = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def _dist_to_ring(x, y, ring):
    best = 1e18
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        dx, dy = x2 - x1, y2 - y1
        t = 0 if dx == dy == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return best


def _label_point(ring, step=5):
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    best, bx, by = -1, sum(xs) / len(xs), sum(ys) / len(ys)
    y = min(ys)
    while y <= max(ys):
        x = min(xs)
        while x <= max(xs):
            if _inside(x, y, ring):
                d = _dist_to_ring(x, y, ring)
                if d > best:
                    best, bx, by = d, x, y
            x += step
        y += step
    return bx, by


def district_shapes(width=1000):
    geo = json.loads((DATA / "ibge" / "malha_distritos_alfredo_chaves.geojson").read_text(encoding="utf-8"))
    rings = {DISTRITO_NOME.get(f["properties"]["nome"], f["properties"]["nome"]): f["geometry"]["coordinates"][0] for f in geo["features"]}
    lat0 = sum(y for r in rings.values() for _, y in r) / sum(len(r) for r in rings.values())
    k = math.cos(math.radians(lat0))
    proj = {n: [(x * k, -y) for x, y in r] for n, r in rings.items()}
    minx = min(x for r in proj.values() for x, _ in r)
    maxx = max(x for r in proj.values() for x, _ in r)
    miny = min(y for r in proj.values() for _, y in r)
    maxy = max(y for r in proj.values() for _, y in r)
    sc = (width - 20) / (maxx - minx)
    height = round((maxy - miny) * sc + 20)
    out = {}
    for n, r in proj.items():
        pts = [((x - minx) * sc + 10, (y - miny) * sc + 10) for x, y in r]
        if pts[0] == pts[-1]:
            pts = pts[:-1]
        far = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
        pts = _rdp(pts[: far + 1], 0.45)[:-1] + _rdp(pts[far:] + [pts[0]], 0.45)[:-1]  # anel fechado: simplifica cada metade
        lx, ly = _label_point(pts)
        out[n] = {"path": "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z", "lx": round(lx, 1), "ly": round(ly, 1)}
    return width, height, out


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

    # ---- todos os candidatos a prefeito (prefeitos_todos.csv): legenda, tooltip e paineis ----------
    def party(r):
        return r.partido.title() if len(r.partido) > 5 else r.partido

    cands_by_year = {str(int(y)): [{"n": r.nome, "p": party(r), "side": r.lado, "pct": float(r.pct), "win": r.resultado == "Eleito"}
                                   for r in g.itertuples()] for y, g in prefs.groupby("ano")}

    def all_note(y):
        return " · ".join(f"{c['n']} ({c['p']}) {dec(c['pct'])}%" + (L(" · eleito", " · elected") if c["win"] else "") for c in cands_by_year[str(y)])

    def terceiros(y):
        return [c for c in cands_by_year[str(y)] if c["side"] == "terceiro"]

    def cand_label(r):
        return f"{r.nome} ({party(r)}" + (L(", eleito", ", elected") if r.resultado == "Eleito" else "") + ")"

    def pref_panels(col, skip_zero_years=True):
        out = []
        for y, g in prefs.groupby("ano"):
            g = g.dropna(subset=[col]).sort_values(col, ascending=False)
            if len(g):
                out.append({"title": str(int(y)), "rows": [{"label": cand_label(r), "value": float(getattr(r, col)), "side": r.lado} for r in g.itertuples()]})
        return out

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
            "outro1": terceiros(ano)[0]["pct"] if len(terceiros(ano)) > 0 else None,
            "outro2": terceiros(ano)[1]["pct"] if len(terceiros(ano)) > 1 else None,
            "note": all_note(ano),
        })
    g = {int(r.ano): float(r.pct_candidato_do_grupo) for r in resumo.itertuples()}
    charts.append(spec(
        "historical_arc", "0.1",
        L("CINCO DERROTAS E A VIRADA", "FIVE LOSSES AND THE TURNAROUND"),
        L("% dos votos válidos de todos os candidatos a prefeito, 2004–2024",
          "% of valid votes for every mayoral candidate, 2004–2024"),
        "cartesian",
        layers=[
            {"type": "line", "key": "oposicao", "label": L("Oposição", "Opposition"), "color": "adversario"},
            {"type": "line", "key": "grupo", "label": L("Grupo", "Group"), "color": "grupo"},
            {"type": "line", "key": "outro1", "label": L("Outros candidatos", "Other candidates"), "color": "terceiro", "dotsOnly": True},
            {"type": "line", "key": "outro2", "label": L("Outros candidatos", "Other candidates"), "color": "terceiro", "dotsOnly": True, "legend": False},
        ],
        rows=rows, unit="pct", yDomain=[0, 80], cands=cands_by_year,
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
            "a oposição fica acima do grupo até 2020 (de 66,9% a 56,4%) e cai a 31,9% em 2024. Pontos azuis mostram os demais candidatos "
            "(Luiz Teixeira e Nelsão Togneri em 2004, Armando Zanata em 2020 e Boldrini em 2024), e uma lista nomeia todos os candidatos de cada eleição.",
            "Line chart with the mayoral vote share of the group and of the main opposition candidacy in six elections, "
            "from 2004 to 2024. The group goes from 26.4% in 2004 to 48.0% in 2016, falls to 40.0% in 2020 and reaches 58.1% "
            "in 2024; the opposition stays above the group through 2020 (from 66.9% to 56.4%) and drops to 31.9% in 2024. Blue dots show the other candidates "
            "(Luiz Teixeira and Nelsão Togneri in 2004, Armando Zanata in 2020 and Boldrini in 2024), and a list names every candidate of each election."),
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

    mw, mh, shapes = district_shapes()
    order_ = ["Sede", "Crubixá", "Ibitiruí", "Matilde", "Ribeirão do Cristo", "Sagrada Família", "São Bento de Urânia"]
    anos = sorted(int(a) for a in dist_votos["ano"].unique())
    dmap = []
    for d in order_:
        sub = dist_votos[dist_votos["distrito"] == d]
        cv = {}
        for a in anos:
            byname = dict(zip(*[dcand[(dcand["distrito"] == d) & (dcand["ano"] == a)][c] for c in ("nome", "votos")]))
            cv[str(a)] = [int(byname.get(c["n"], 0)) for c in cands_by_year[str(a)]]
        dmap.append({"name": d, **shapes[d], "cv": cv,
                     "values": {str(int(r.ano)): [int(r.votos_grupo), int(r.votos_validos)] for r in sub.itertuples()}})
    charts.append(spec(
        "distritos_heatmap", "6", L("ONDE O GRUPO ERA FORTE", "WHERE THE GROUP WAS STRONG"),
        L("% do candidato do grupo para prefeito, por distrito: escolha a eleição (a lista mostra todos os candidatos)",
          "% for the group's mayoral candidate, by district: choose the election (the list shows every candidate)"),
        "districtmap", viewBox=f"0 0 {mw} {mh}", years=anos, districts=dmap, cands=cands_by_year,
        alt=L("Mapa dos sete distritos de Alfredo Chaves, cada um colorido entre vermelho e verde conforme o percentual dos votos para prefeito "
              "recebido pelo candidato do grupo, com um botão para cada eleição de 2004 a 2024, e uma tabela com os mesmos percentuais. "
              "Em 2024 o grupo passa de 47% em todos os distritos e de 50% em seis dos sete; em 2020 só Ribeirão do Cristo ficou acima de 50%.",
              "Map of the seven districts of Alfredo Chaves, each colored between red and green according to the share of mayoral votes "
              "won by the group's candidate, with one button per election from 2004 to 2024, and a table with the same percentages. "
              "In 2024 the group is above 47% in every district and above 50% in six of seven; in 2020 only Ribeirão do Cristo was above 50%.")))

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
        prows = []
        for a_ in sorted(int(x) for x in dcand["ano"].unique()):
            sub = dcand[(dcand["distrito"] == d) & (dcand["ano"] == a_)]
            tot_d = int(sub["votos_validos"].iloc[0])
            byname = dict(zip(sub["nome"], sub["votos"]))
            cs = cands_by_year[str(a_)]
            grp = next(c for c in cs if c["side"] == "grupo")
            opp = next(c for c in cs if c["side"] == "adversario")
            ter = [c for c in cs if c["side"] == "terceiro"]
            v = lambda c: int(byname.get(c["n"], 0))
            prows.append({"x": str(a_), "grupo": v(grp), "oposicao": v(opp),
                          "outro1": v(ter[0]) if len(ter) > 0 else None, "outro2": v(ter[1]) if len(ter) > 1 else None, "total": tot_d,
                          "note": " · ".join(f"{c['n']} ({c['p']}) {thou(v(c))} ({dec(v(c) / tot_d * 100)}%)" for c in cs)})
            gv[(d, a_)] = v(grp)
            base_v = dist_votos[(dist_votos["distrito"] == d) & (dist_votos["ano"] == a_)]["votos_grupo"].iloc[0]
            assert int(base_v) == v(grp), (d, a_, base_v, v(grp))
        panels.append({"title": d, "rows": prows})
    tot = {a: sum(gv[(d, a)] for d in order) for a in (2004, 2008, 2012, 2016, 2020, 2024)}
    assert all(gv[(d, 2024)] == max(gv[(d, a)] for a in tot) for d in order), "2024 deixou de ser o pico em algum distrito"
    fora20, fora24 = tot[2020] - gv[("Sede", 2020)], tot[2024] - gv[("Sede", 2024)]
    charts.append(spec(
        "distritos_votos", "6.2", L("VOTOS POR DISTRITO, ELEIÇÃO A ELEIÇÃO", "VOTES BY DISTRICT, ELECTION BY ELECTION"),
        L("votos totais de cada candidato a prefeito, 2004–2024 (cada distrito tem escala própria; a lista acima nomeia todos os candidatos)",
          "total votes for each mayoral candidate, 2004–2024 (each district has its own scale; the list above names every candidate)"),
        "multiples",
        layers=[
            {"type": "line", "key": "grupo", "label": L("Candidato do grupo", "Group's candidate"), "color": "grupo"},
            {"type": "line", "key": "oposicao", "label": L("Principal oposição", "Main opposition"), "color": "adversario"},
            {"type": "line", "key": "outro1", "label": L("Outros candidatos", "Other candidates"), "color": "terceiro", "dotsOnly": True},
            {"type": "line", "key": "outro2", "label": L("Outros candidatos", "Other candidates"), "color": "terceiro", "dotsOnly": True, "legend": False},
        ],
        panels=panels, unit="int", cands=cands_by_year,
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
        alt=L("Sete gráficos de linhas, um por distrito, com os votos totais de cada candidato a prefeito em cada eleição de 2004 a 2024: "
              "uma linha para o candidato do grupo, outra para a principal oposição e pontos para os demais candidatos.",
              "Seven line charts, one per district, with the total votes for each mayoral candidate in each election from 2004 to 2024: "
              "one line for the group's candidate, another for the main opposition and dots for the other candidates.")))

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
    charts.append(spec("financeiro_chapa", "12", L("RECEITA DECLARADA", "DECLARED CAMPAIGN REVENUE"),
                       L("todos os candidatos a prefeito, 2004–2024, em reais", "every mayoral candidate, 2004–2024, in reais"), "panels", unit="brl",
                       panels=pref_panels("receita")))
    charts.append(spec("custo_por_voto", "13", L("CUSTO POR VOTO", "COST PER VOTE"),
                       L("reais gastos por voto, todos os candidatos a prefeito, 2004–2024", "reais spent per vote, every mayoral candidate, 2004–2024"), "panels",
                       unit="brl2", panels=pref_panels("custo_por_voto")))

    origem = [("Partido político", "Political party", 57460.0, 166372.43), ("Recursos próprios", "Own funds", 22030.8, 34547.11),
              ("Pessoas físicas", "Individual donors", 14440.2, 18648.65), ("Outros candidatos", "Other candidates", 2625.0, 7000.0)]
    charts.append(spec(
        "origem_receitas", "14", L("ORIGEM DAS RECEITAS DA CHAPA", "WHERE THE SLATE'S MONEY CAME FROM"),
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
        L("% de mulheres na população, no eleitorado e entre os candidatos a vereador", "% women in the population, the electorate and among council candidates"),
        "cartesian",
        layers=[{"type": "bar", "key": "v", "label": L("% de mulheres", "% women"), "color": "neutro", "colorBySide": True}],
        rows=[{"x": L("População 2022", "Population 2022"), "v": 49.3, "side": "neutro"},
              {"x": L("Eleitorado 2024", "Electorate 2024"), "v": 50.0, "side": "neutro"},
              {"x": L("Vereador 2020", "Council 2020"), "v": 37.7, "side": "adversario"},
              {"x": L("Vereador 2024", "Council 2024"), "v": 32.9, "side": "grupo"}],
        unit="pct", yDomain=[0, 60]))

    charts.append(spec(
        "raca_candidatos", "19", L("RAÇA OU COR", "RACE OR COLOR"),
        L("% da população (IBGE 2022) e dos candidatos a vereador", "% of the population (IBGE 2022) and of council candidates"), "cartesian",
        layers=[{"type": "bar", "key": "pop", "label": L("População (IBGE 2022)", "Population (IBGE 2022)"), "color": "neutro"},
                {"type": "bar", "key": "c20", "label": L("Candidatos a vereador 2020", "Council candidates 2020"), "color": "adversario"},
                {"type": "bar", "key": "c24", "label": L("Candidatos a vereador 2024", "Council candidates 2024"), "color": "grupo"}],
        rows=[{"x": L("Branca", "White"), "pop": 61.4, "c20": 59.4, "c24": 68.6},
              {"x": L("Parda", "Mixed-race (pardo)"), "pop": 34.3, "c20": 30.4, "c24": 22.9},
              {"x": L("Preta", "Black"), "pop": 4.2, "c20": 7.2, "c24": 8.6}],
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
    charts.append(spec(
        "idade_candidatos", "23", L("IDADE DOS CANDIDATOS A PREFEITO", "AGE OF MAYORAL CANDIDATES"),
        L("todos os candidatos, em anos, na data da eleição, 2004–2024", "every candidate, in years, on election day, 2004–2024"), "panels", unit="yr",
        panels=pref_panels("idade")))
    charts.append(spec(
        "patrimonio_candidatos", "24", L("PATRIMÔNIO DECLARADO", "DECLARED ASSETS"),
        L("todos os candidatos a prefeito, em reais, 2008–2024 (a base de 2004 não traz bens)", "every mayoral candidate, in reais, 2008–2024 (the 2004 dataset has no assets)"),
        "panels", unit="brl", panels=pref_panels("patrimonio")))

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

    # ---- 11 Cenarios para 2028 (numeros calculados em R: analysis/cenarios_2028.R) ------------
    r_eleit = pd.read_csv(OUT / "r_cenarios_2028_eleitorado.csv").set_index("cenario")
    r_serie = pd.read_csv(OUT / "r_cenarios_2028_serie.csv")
    r_grade = pd.read_csv(OUT / "r_cenarios_2028_grade.csv")
    r_virada = pd.read_csv(OUT / "r_cenarios_2028_virada.csv")
    r_dist = pd.read_csv(OUT / "r_cenarios_2028_distritos.csv")
    base, lo, hi = int(r_eleit.loc["base", "votos_validos"]), int(r_eleit.loc["baixo", "votos_validos"]), int(r_eleit.loc["alto", "votos_validos"])
    aptos_b = int(r_eleit.loc["base", "aptos"])
    vir = r_virada.set_index("terceiro")["oscilacao_maxima"]
    assert -10 < vir[0] < -5 and vir[10] < -13, "texto da Figura 28 desatualizado em relacao ao R"

    rows27 = []
    for r in r_serie.itertuples():
        proj = int(r.ano) == 2028
        rows27.append({"x": str(int(r.ano)), "v": int(r.votos_validos), "side": "info" if proj else "neutro",
                       **({"note": L(f"Cenário base. Faixa de {thou(lo)} a {thou(hi)} votos válidos; eleitores aptos projetados: {thou(aptos_b)} "
                                     f"(faixa de 80%: {thou(r_eleit.loc['baixo', 'aptos'])} a {thou(r_eleit.loc['alto', 'aptos'])}).",
                                     f"Base scenario. Range of {thou(lo)} to {thou(hi)} valid votes; projected registered voters: {thou(aptos_b)} "
                                     f"(80% range: {thou(r_eleit.loc['baixo', 'aptos'])} to {thou(r_eleit.loc['alto', 'aptos'])}).")} if proj else {})})
    charts.append(spec(
        "cenario_eleitorado", "27", L("VOTOS VÁLIDOS EM 2028: CENÁRIO BASE", "VALID VOTES IN 2028: BASE SCENARIO"),
        L("votos válidos para prefeito: dados de 2004 a 2024 e cenário de 2028 (em azul)",
          "valid votes for mayor: data for 2004 to 2024 and the 2028 scenario (in blue)"),
        "cartesian",
        layers=[{"type": "bar", "key": "v", "label": L("Votos válidos", "Valid votes"), "color": "neutro", "colorBySide": True}],
        rows=rows27, unit="int",
        sideLegend={"neutro": L("Dados do TSE, 2004–2024", "TSE data, 2004–2024"), "info": L("Cenário para 2028 (R)", "2028 scenario (R)")},
        cap=L("Votos válidos: série histórica e cenário base para 2028", "Valid votes: historical series and base scenario for 2028"),
        caption=L(f"Estendendo em linha reta o crescimento do eleitorado de 2004 a 2024, o cenário base para 2028 é de {thou(aptos_b)} eleitores aptos e "
                  f"{thou(base)} votos válidos (de {thou(lo)} a {thou(hi)}), contra {thou(9955)} em 2024. É uma hipótese de tendência, não uma previsão.",
                  f"Extending the 2004 to 2024 growth of the electorate in a straight line, the 2028 base scenario is {thou(aptos_b)} registered voters and "
                  f"{thou(base)} valid votes ({thou(lo)} to {thou(hi)}), against {thou(9955)} in 2024. It is a trend assumption, not a forecast."),
        alt=L(f"Gráfico de barras dos votos válidos para prefeito de 2004 a 2024 e do cenário base de 2028, com {thou(base)} votos válidos.",
              f"Bar chart of valid votes for mayor from 2004 to 2024 and the 2028 base scenario, with {thou(base)} valid votes.")))

    osc = sorted(int(o) for o in r_grade["oscilacao"].unique())
    minus = "\u2212"

    def olabel(o):
        return "0" if o == 0 else (f"+{o}" if o > 0 else f"{minus}{abs(o)}")

    rows28 = []
    for o in osc:
        row = {"x": olabel(o)}
        for t in (0, 5, 10):
            row[f"m{t}"] = int(r_grade[(r_grade["oscilacao"] == o) & (r_grade["terceiro"] == t)]["margem_votos"].iloc[0])
        g5 = r_grade[(r_grade["oscilacao"] == o) & (r_grade["terceiro"] == 5)].iloc[0]
        row["note"] = L(f"Com terceiro em 5%: grupo {dec(g5.share_grupo)}% ({thou(g5.votos_grupo)} votos) × oposição {dec(g5.share_oposicao)}% ({thou(g5.votos_oposicao)}).",
                        f"With a 5% third candidate: group {dec(g5.share_grupo)}% ({thou(g5.votos_grupo)} votes) × opposition {dec(g5.share_oposicao)}% ({thou(g5.votos_oposicao)}).")
        rows28.append(row)
    charts.append(spec(
        "cenario_margem", "28", L("MARGEM DE VOTOS SE O DESEMPENHO OSCILAR", "VOTE MARGIN IF PERFORMANCE SWINGS"),
        L(f"votos do grupo menos votos da principal oposição em 2028 ({thou(base)} votos válidos), conforme o % do grupo suba ou caia em relação aos 58,1% de 2024, em pontos percentuais",
          f"group votes minus main opposition votes in 2028 ({thou(base)} valid votes), as the group's share rises or falls from 2024's 58.1%, in percentage points"),
        "cartesian",
        layers=[
            {"type": "line", "key": "m0", "label": L("Sem terceiro candidato", "No third candidate"), "color": "grupo"},
            {"type": "line", "key": "m5", "label": L("Terceiro com 5% dos votos", "Third candidate at 5%"), "color": "terceiro"},
            {"type": "line", "key": "m10", "label": L("Terceiro com 10% (como em 2024)", "Third candidate at 10% (as in 2024)"), "color": "info"},
        ],
        rows=rows28, unit="int", refY=0,
        cap=L("Margem de votos do grupo sobre a principal oposição, por cenário de oscilação", "Group's vote margin over the main opposition, by swing scenario"),
        caption=L("Acima da linha zero, o grupo lidera. Sem terceiro candidato, o grupo perde a liderança entre −5 e −10 pontos; com um terceiro em 10%, como em 2024, "
                  "aguenta uma queda de mais de 13 pontos.",
                  "Above the zero line, the group leads. With no third candidate, the group loses the lead between −5 and −10 points; with a third candidate at 10%, as in 2024, "
                  "it withstands a drop of more than 13 points."),
        alt=L("Gráfico de linhas com a margem de votos do grupo sobre a oposição em 2028 para oscilações de −20 a +5 pontos, em três cenários de terceiro candidato.",
              "Line chart with the group's vote margin over the opposition in 2028 for swings from −20 to +5 points, under three third-candidate scenarios.")))

    dnames = ["Sede", "Crubixá", "Ibitiruí", "Matilde", "Ribeirão do Cristo", "Sagrada Família", "São Bento de Urânia"]
    dvals = []
    for d in dnames:
        vals = {}
        for o in osc:
            sh = float(r_dist[(r_dist["oscilacao"] == o) & (r_dist["distrito"] == d)]["share"].iloc[0])
            vals[str(o)] = [int(round(sh * 10)), 1000]
        dvals.append({"name": d, **shapes[d], "values": vals})
    count = {o: int((r_dist[r_dist["oscilacao"] == o]["share"] > 50).sum()) for o in osc}
    charts.append(spec(
        "cenario_distritos", "29", L("OS DISTRITOS SOB CADA CENÁRIO", "THE DISTRICTS UNDER EACH SCENARIO"),
        L("% do grupo em cada distrito se o resultado de 2024 subir ou cair o mesmo número de pontos em todos, escolha a oscilação",
          "the group's share in each district if the 2024 result rises or falls by the same number of points in all of them, choose the swing"),
        "districtmap", viewBox=f"0 0 {mw} {mh}", years=osc, defaultYear=-10, printYears=[-10, 0], pctOnly=True, districts=dvals,
        labels={str(o): (L("Como em 2024", "As in 2024") if o == 0 else f"{olabel(o)} p.p.") for o in osc},
        strings={"hint": L("Escolha a oscilação nos botões. Toque ou passe o mouse em um distrito para ver o percentual no cenário.",
                           "Choose the swing with the buttons. Tap or hover over a district to see its share in the scenario."),
                 "aria": L("Escolha a oscilação", "Choose the swing"),
                 "suffix": L("dos votos válidos no cenário", "of the valid votes in the scenario"),
                 "tableTitle": L("Todas as oscilações, por distrito", "All swings, by district")},
        cap=L("% do grupo por distrito sob oscilação uniforme, a partir do resultado de 2024", "Group's share by district under a uniform swing, starting from the 2024 result"),
        caption=L(f"Com uma oscilação de −5 pontos em todos os distritos, o grupo mantém mais de 50% em {count[-5]} dos sete; com −10, em {count[-10]}. "
                  "Como a Sede reúne cerca de dois terços dos votos válidos, é nela que a liderança se decide.",
                  f"With a −5 point swing in every district, the group keeps more than 50% in {count[-5]} of the seven; with −10, in {count[-10]}. "
                  "Since Sede holds about two thirds of the valid votes, that is where the lead is decided."),
        alt=L("Mapa dos sete distritos coloridos entre vermelho e verde pelo percentual do grupo em cada cenário de oscilação, com um botão por oscilação de −20 a +5 pontos.",
              "Map of the seven districts colored between red and green by the group's share in each swing scenario, with one button per swing from −20 to +5 points.")))

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
