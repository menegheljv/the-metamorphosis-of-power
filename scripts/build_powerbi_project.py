# -*- coding: utf-8 -*-
"""Projeto do Power BI (PBIP) de "A Metamorfose do Poder em Alfredo Chaves".

Gera dashboards/powerbi/AMetamorfoseDoPoder.pbip + .SemanticModel (TMDL) + .Report (PBIR) a partir de dashboards/data/*.csv.
Os dados vao embutidos no modelo (tabelas #table em Power Query), entao o projeto abre em qualquer maquina, sem caminho de arquivo.

Rode antes: python scripts/build_dashboards_data.py
"""
import json
import os
import random
import shutil
import uuid

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "dashboards", "data")
ROOT = os.path.join(BASE, "dashboards", "powerbi")
NAME = "AMetamorfoseDoPoder"
SM = os.path.join(ROOT, f"{NAME}.SemanticModel")
RP = os.path.join(ROOT, f"{NAME}.Report")
THEME_SRC = os.path.join(BASE, "dashboards", "powerbi_assets", "Fluent2-CY26SU08.json")

GRP, OPP, OTH, INK, MUTED, BG, CARD, LINE = "#1F9D63", "#C8433A", "#3D7FC4", "#17171A", "#6B6F76", "#FAF9F6", "#FFFFFF", "#E2E0DA"
CAND_COLOR = {
    "Jorge Meneghel": "#0F7A4A", "Daniel Orlandi": "#2FB37A", "Sergio Bianchi": "#66C79E", "Ronaldo Bianchi": "#1F9D63", "Hugo Luiz": "#0B5E38",
    "Dr. Fernando": "#C8433A", "Roberto Fiorin": "#E07B72", "Rolmar Boteccia": "#8F2A23",
    "Luiz Teixeira": "#3D7FC4", "Nelsão Togneri": "#7FB0E0", "Armando Zanata": "#2A5C94", "Boldrini": "#5E96CF",
}
LADO_COLOR = {"Grupo": GRP, "Principal oposição": OPP, "Demais candidatos": OTH}


_RNG = random.Random(2004)  # ids deterministicos: o projeto gerado nao muda entre execucoes (bom para o git)


def rid():
    return uuid.UUID(int=_RNG.getrandbits(128)).hex[:20]


def tag():
    return str(uuid.UUID(int=_RNG.getrandbits(128), version=4))


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def wj(path, obj):
    w(path, json.dumps(obj, ensure_ascii=False, indent=2))


# ====================================================================== modelo semantico (TMDL)
def m_literal(v, kind):
    if pd.isna(v):
        return "null"
    if kind == "text":
        return '"' + str(v).replace('"', '""') + '"'
    if kind == "int":
        return str(int(v))
    if kind == "date":
        d = pd.Timestamp(v)
        return f"#date({d.year}, {d.month}, {d.day})"
    return repr(float(v))


TABLES = {
    # tabela: (arquivo, {coluna: (tipo, formato)}, chave de ordenacao {coluna: coluna})
    "eleicoes": ("eleicoes.csv", {
        "Ano": ("int", "0"), "Eleitores_Aptos": ("int", "#,0"), "Comparecimento": ("int", "#,0"), "Pct_Comparecimento": ("num", '0.0"%"'),
        "Votos_Validos": ("int", "#,0"), "Candidatos_Prefeito": ("int", "0"), "Vencedor": ("text", None), "Partido_Vencedor": ("text", None),
        "Pct_Vencedor": ("num", '0.0"%"'), "Candidato_Grupo": ("text", None), "Partido_Grupo": ("text", None), "Pct_Grupo": ("num", '0.0"%"'),
        "Candidato_Oposicao": ("text", None), "Partido_Oposicao": ("text", None), "Pct_Oposicao": ("num", '0.0"%"'),
        "Pct_Demais": ("num", '0.0"%"'), "Resultado_Grupo": ("text", None)}, {}),
    "candidatos": ("candidatos.csv", {
        "Ano": ("int", "0"), "Candidato": ("text", None), "Nome_Completo": ("text", None), "Partido": ("text", None), "Lado": ("text", None),
        "Votos": ("int", "#,0"), "Pct_Votos_Validos": ("num", '0.0"%"'), "Resultado": ("text", None), "Idade": ("int", "0"),
        "Genero": ("text", None), "Escolaridade": ("text", None), "Ocupacao": ("text", None),
        "Patrimonio_Declarado": ("num", '"R$" #,0'), "Receita_Declarada": ("num", '"R$" #,0'), "Despesa_Paga": ("num", '"R$" #,0'),
        "Custo_Por_Voto": ("num", '"R$" #,0.00'), "Eleicao_Candidato": ("text", None), "Ordem": ("int", "0")}, {"Eleicao_Candidato": "Ordem"}),
    "votos_distrito": ("votos_distrito.csv", {
        "Distrito": ("text", None), "Ano": ("int", "0"), "Candidato": ("text", None), "Partido": ("text", None), "Lado": ("text", None),
        "Votos": ("int", "#,0"), "Votos_Validos_Distrito": ("int", "#,0"), "Pct_No_Distrito": ("num", '0.0"%"')}, {}),
    "camara": ("camara.csv", {"Ano": ("int", "0"), "Lado": ("text", None), "Cadeiras": ("int", "0")}, {}),
    "vereadores_eleitos": ("vereadores_eleitos.csv", {
        "Ano": ("int", "0"), "Nome": ("text", None), "Partido": ("text", None), "Votos": ("int", "#,0"), "Lado": ("text", None)}, {}),
    "campanha_digital": ("campanha_digital.csv", {
        "Data": ("date", "dd/mm/yyyy"), "Fase": ("text", None), "Categoria": ("text", None), "Tema": ("text", None),
        "Visualizacoes": ("int", "#,0"), "Curtidas": ("int", "#,0"), "Comentarios": ("int", "#,0"), "Compartilhamentos": ("int", "#,0"),
        "Engajamento": ("int", "#,0")}, {}),
    "secoes": ("secoes.csv", {
        "Secao": ("int", "0"), "Votos_2020": ("num", "#,0"), "Total_2020": ("num", "#,0"), "Votos_2024": ("int", "#,0"), "Total_2024": ("int", "#,0"),
        "Pct_2020": ("num", '0.0"%"'), "Pct_2024": ("num", '0.0"%"'), "Variacao_pp": ("num", '0.0" p.p."'), "Vencedor_2020": ("text", None),
        "Vencedor_2024": ("text", None), "Local_Votacao": ("text", None), "Endereco": ("text", None), "Virou": ("text", None)}, {}),
}

MEASURES = {
    "eleicoes": [
        ("Derrotas do grupo", 'COUNTROWS(FILTER(ALL(eleicoes), eleicoes[Resultado_Grupo] = "Derrota"))', "0"),
        ("Pct do grupo", "MAX(eleicoes[Pct_Grupo])", '0.0"%"'),
        ("Pct da oposição", "MAX(eleicoes[Pct_Oposicao])", '0.0"%"'),
        ("Grupo em 2004", "CALCULATE(MAX(eleicoes[Pct_Grupo]), eleicoes[Ano] = 2004)", '0.0"%"'),
        ("Grupo em 2024", "CALCULATE(MAX(eleicoes[Pct_Grupo]), eleicoes[Ano] = 2024)", '0.0"%"'),
    ],
    "secoes": [
        ("Seções vencidas 2020", 'COUNTROWS(FILTER(secoes, secoes[Vencedor_2020] = "Hugo Luiz Picoli Meneghel" || secoes[Vencedor_2020] = "Ronaldo Bianchi"))', "0"),
        ("Seções vencidas 2024", 'COUNTROWS(FILTER(secoes, secoes[Vencedor_2024] = "Hugo Luiz Picoli Meneghel"))', "0"),
        ("Total de seções 2024", "COUNTROWS(secoes)", "0"),
    ],
    "votos_distrito": [
        ("Pct dos votos", "DIVIDE(SUM(votos_distrito[Votos]), CALCULATE(SUM(votos_distrito[Votos]), REMOVEFILTERS(votos_distrito[Lado]), REMOVEFILTERS(votos_distrito[Candidato]), REMOVEFILTERS(votos_distrito[Partido]))) * 100", '0.0"%"'),
    ],
    "camara": [
        ("Cadeiras do grupo 2020", 'CALCULATE(SUM(camara[Cadeiras]), camara[Ano] = 2020, camara[Lado] = "Grupo")', "0"),
        ("Cadeiras do grupo 2024", 'CALCULATE(SUM(camara[Cadeiras]), camara[Ano] = 2024, camara[Lado] = "Grupo")', "0"),
    ],
    "campanha_digital": [
        ("Posts", "COUNTROWS(campanha_digital)", "#,0"),
        ("Visualizações totais", "SUM(campanha_digital[Visualizacoes])", "#,0"),
    ],
}

RELATIONSHIPS = [
    ("candidatos", "Ano", "eleicoes", "Ano"),
    ("votos_distrito", "Ano", "eleicoes", "Ano"),
    ("camara", "Ano", "eleicoes", "Ano"),
    ("vereadores_eleitos", "Ano", "eleicoes", "Ano"),
]


def table_tmdl(name):
    fname, cols, sortby = TABLES[name]
    df = pd.read_csv(os.path.join(DATA, fname))
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"])
    mtype = {"int": "Int64.Type", "num": "nullable number", "text": "text", "date": "date"}
    if name == "secoes":
        pass
    header = ", ".join(f"{c} = {'nullable number' if t == 'num' else mtype[t]}" for c, (t, _) in cols.items())
    rows = []
    for r in df.itertuples(index=False):
        vals = [m_literal(getattr(r, c), t if t != "num" else "num") for c, (t, _) in cols.items()]
        rows.append("{" + ", ".join(vals) + "}")
    body = ",\n\t\t\t\t\t".join(rows)
    out = [f"table {name}", f"\tlineageTag: {tag()}", ""]
    for c, (t, fmt) in cols.items():
        dtype = {"int": "int64", "num": "double", "text": "string", "date": "dateTime"}[t]
        out.append(f"\tcolumn {c}")
        out.append(f"\t\tdataType: {dtype}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {tag()}")
        out.append("\t\tsummarizeBy: " + ("sum" if t in ("num", "int") and c not in ("Ano", "Ordem", "Secao", "Idade") else "none"))
        out.append(f"\t\tsourceColumn: {c}")
        if c in sortby:
            out.append(f"\t\tsortByColumn: {sortby[c]}")
        out.append("")
    for mname, expr, fmt in MEASURES.get(name, []):
        out.append(f"\tmeasure '{mname}' = {expr}")
        out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {tag()}")
        out.append("")
    out += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
            f"\t\t\t\t\tFonte = #table(type table [{header}], {{",
            f"\t\t\t\t\t{body}", "\t\t\t\t\t})", "\t\t\t\tin", "\t\t\t\t\tFonte", ""]
    return "\n".join(out)


def build_model():
    shutil.rmtree(SM, ignore_errors=True)
    wj(os.path.join(SM, "definition.pbism"), {"version": "4.2", "settings": {}})
    w(os.path.join(SM, "definition", "database.tmdl"), "database\n\tcompatibilityLevel: 1600\n")
    order = list(TABLES)
    model = ["model Model", "\tculture: pt-BR", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
             "\tsourceQueryCulture: pt-BR", "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
             "annotation PBI_QueryOrder = " + json.dumps(order), "annotation __PBI_TimeIntelligenceEnabled = 0", ""]
    model += [f"ref table {t}" for t in order] + [""]
    w(os.path.join(SM, "definition", "model.tmdl"), "\n".join(model))
    for t in order:
        w(os.path.join(SM, "definition", "tables", f"{t}.tmdl"), table_tmdl(t))
    rel = []
    for frm, fc, to, tc in RELATIONSHIPS:
        rel += [f"relationship {tag()}", f"\tfromColumn: {frm}.{fc}", f"\ttoColumn: {to}.{tc}", ""]
    w(os.path.join(SM, "definition", "relationships.tmdl"), "\n".join(rel))


# ====================================================================== relatorio (PBIR)
def lit(v):
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, (int, float)):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": "'" + str(v).replace("'", "''") + "'"}}}


def solid(color):
    return {"solid": {"color": lit(color)}}


def col(ent, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}}


def measure(ent, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}}


def agg(ent, prop, fn=0):
    return {"Aggregation": {"Expression": col(ent, prop), "Function": fn}}


FN_NAME = {0: "Sum", 1: "Avg", 2: "Count", 3: "Min", 4: "Max"}


def proj(kind, ent, prop, fn=0, active=None, name=None):
    if kind == "col":
        field, ref = col(ent, prop), f"{ent}.{prop}"
    elif kind == "measure":
        field, ref = measure(ent, prop), f"{ent}.{prop}"
    else:
        field, ref = agg(ent, prop, fn), f"{FN_NAME[fn]}({ent}.{prop})"
    p = {"field": field, "queryRef": ref, "nativeQueryRef": prop}
    if active:
        p["active"] = True
    if name:
        p["displayName"] = name
    return p


def container(vtype, x, y, wd, ht, query=None, objects=None, title=None, z=0, tab=0, card=True):
    vis = {"visualType": vtype}
    if query:
        vis["query"] = {"queryState": query}
    if objects:
        vis["objects"] = objects
    vco = {}
    if title:
        vco["title"] = [{"properties": {"show": lit(True), "text": lit(title), "fontSize": lit(13), "fontColor": solid(INK), "bold": lit(True)}}]
    else:
        vco["title"] = [{"properties": {"show": lit(False)}}]
    vco["subTitle"] = [{"properties": {"show": lit(False)}}]
    if card:
        vco["background"] = [{"properties": {"show": lit(True), "color": solid(CARD), "transparency": lit(0)}}]
        vco["border"] = [{"properties": {"show": lit(True), "color": solid(LINE), "radius": lit(8)}}]
    vis["visualContainerObjects"] = vco
    vis["drillFilterOtherVisuals"] = True
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json",
            "name": rid(), "position": {"x": x, "y": y, "z": z, "height": ht, "width": wd, "tabOrder": tab}, "visual": vis}


def textbox(x, y, wd, ht, text, size=12, color=INK, bold=False, z=0, tab=0):
    run = {"value": text, "textStyle": {"fontSize": f"{size}pt", "color": color, **({"fontWeight": "bold"} if bold else {})}}
    v = container("textbox", x, y, wd, ht, objects={"general": [{"properties": {"paragraphs": [{"textRuns": [run], "horizontalTextAlignment": "Left"}]}}]}, z=z, tab=tab, card=False)
    return v


def datapoints(field_col, colors):
    """Cores por valor de uma coluna de serie/legenda."""
    out = []
    for value, color in colors.items():
        out.append({"properties": {"fill": solid(color)},
                    "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": field_col, "Right": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}}}]}})
    return out


def axis_objs(show_val_axis=True, label_fmt=None, labels=True, font=10):
    o = {
        "categoryAxis": [{"properties": {"axisType": lit("Categorical"), "fontSize": lit(font), "labelColor": solid(INK)}}],
        "valueAxis": [{"properties": {"show": lit(show_val_axis), "fontSize": lit(font), "labelColor": solid(MUTED), "gridlineColor": solid(LINE)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Bottom"), "fontSize": lit(10), "labelColor": solid(INK)}}],
        "labels": [{"properties": {"show": lit(labels), "fontSize": lit(10), "color": solid(INK)}}],
    }
    return o


def slicer(x, y, wd, ht, title="Ano", default=None):
    q = {"Values": {"projections": [proj("col", "eleicoes", "Ano", active=True)]}}
    obj = {"data": [{"properties": {"mode": lit("Basic")}}],
           "selection": [{"properties": {"selectAllCheckboxEnabled": lit(True), "singleSelect": lit(False)}}],
           "header": [{"properties": {"show": lit(False)}}],
           "items": [{"properties": {"fontSize": lit(11), "fontColor": solid(INK)}}]}
    c = container("slicer", x, y, wd, ht, q, obj, title=title)
    if default is not None:  # selecao padrao do segmentador (fica em objects.general.filter)
        c["visual"]["objects"]["general"] = [{"properties": {"filter": {"filter": {
            "Version": 2, "From": [{"Name": "e", "Entity": "eleicoes", "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "e"}}, "Property": "Ano"}}],
                                            "Values": [[{"Literal": {"Value": f"{default}L"}}]]}}}]}}}}]
    return c


def card(x, y, wd, ht, ent, meas, title, color=INK):
    q = {"Values": {"projections": [proj("measure", ent, meas)]}}
    obj = {"labels": [{"properties": {"fontSize": lit(28), "color": solid(color), "fontFamily": lit("Segoe UI Semibold")}}],
           "categoryLabels": [{"properties": {"show": lit(False)}}]}
    return container("card", x, y, wd, ht, q, obj, title=title)


def page(display, visuals, height=720):
    pid = rid()
    return pid, {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
                 "name": pid, "displayName": display, "displayOption": "FitToPage", "height": height, "width": 1280,
                 "objects": {"background": [{"properties": {"color": solid(BG), "transparency": lit(0)}}]}}, visuals


def header(title, subtitle):
    return [textbox(24, 12, 1232, 40, title, size=22, bold=True), textbox(24, 50, 1232, 26, subtitle, size=11, color=MUTED, z=1)]


def bar_by_candidate(x, y, wd, ht, value_prop, title, kind="barChart", fn=0, labels=False):
    q = {"Category": {"projections": [proj("col", "candidatos", "Eleicao_Candidato", active=True)]},
         "Series": {"projections": [proj("col", "candidatos", "Lado")]},
         "Y": {"projections": [proj("agg", "candidatos", value_prop, fn)]}}
    o = axis_objs(labels=labels or kind == "columnChart")
    o["dataPoint"] = datapoints(col("candidatos", "Lado"), LADO_COLOR)
    return container(kind, x, y, wd, ht, q, o, title=title)


def build_report():
    shutil.rmtree(RP, ignore_errors=True)
    wj(os.path.join(RP, "definition.pbir"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
                                              "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    theme_dst = os.path.join(RP, "StaticResources", "SharedResources", "BaseThemes")
    os.makedirs(theme_dst, exist_ok=True)
    shutil.copy(THEME_SRC, theme_dst)
    wj(os.path.join(RP, "definition", "version.json"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    wj(os.path.join(RP, "definition", "report.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "Fluent2-CY26SU08", "reportVersionAtImport": {"visual": "2.12.0", "report": "3.4.0", "page": "2.3.1"}, "type": "SharedResources"}},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [{"name": "Fluent2-CY26SU08", "path": "BaseThemes/Fluent2-CY26SU08.json", "type": "BaseTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}})

    pages = []

    # ---- 1. Cinco derrotas e a virada
    v = header("A Metamorfose do Poder em Alfredo Chaves", "Cinco derrotas e a virada · prefeito, seis eleições, 2004 a 2024 · dados abertos do TSE")
    v += [card(24, 90, 296, 96, "eleicoes", "Derrotas do grupo", "Derrotas seguidas (2004–2020)", OPP),
          card(336, 90, 296, 96, "eleicoes", "Grupo em 2004", "Grupo em 2004 (% dos válidos)", INK),
          card(648, 90, 296, 96, "eleicoes", "Grupo em 2024", "Grupo em 2024 (% dos válidos)", GRP),
          card(960, 90, 296, 96, "secoes", "Seções vencidas 2024", "Seções vencidas em 2024 (de 42)", GRP)]
    q = {"Category": {"projections": [proj("col", "eleicoes", "Ano", active=True)]},
         "Y": {"projections": [proj("agg", "eleicoes", "Pct_Grupo", 4, name="Grupo"), proj("agg", "eleicoes", "Pct_Oposicao", 4, name="Principal oposição")]}}
    o = axis_objs()
    o["dataPoint"] = [{"properties": {"fill": solid(GRP)}}]
    o["categoryAxis"] = [{"properties": {"axisType": lit("Categorical"), "fontSize": lit(10), "labelColor": solid(INK)}}]
    o["lineStyles"] = [{"properties": {"strokeWidth": lit(3), "showMarker": lit(True)}}]
    line = container("lineChart", 24, 202, 500, 496, q, o, title="Grupo e principal oposição, % dos votos válidos")
    # cores das series de linha (uma por medida)
    line["visual"]["objects"]["dataPoint"] = [
        {"properties": {"fill": solid(GRP)}, "selector": {"metadata": "Max(eleicoes.Pct_Grupo)"}},
        {"properties": {"fill": solid(OPP)}, "selector": {"metadata": "Max(eleicoes.Pct_Oposicao)"}}]
    v += [line, bar_by_candidate(540, 202, 716, 496, "Pct_Votos_Validos", "Todos os candidatos a prefeito, % dos votos válidos")]
    pages.append(page("Cinco derrotas e a virada", v))

    # ---- 2. Todos os candidatos
    v = header("Todos os candidatos a prefeito", "Os 16 candidatos das seis eleições · o lado é definido em relação ao grupo (verde), à principal oposição (vermelho) e aos demais (azul)")
    v += [slicer(24, 90, 120, 240, "Eleição")]
    cols = [("Ano", "col", "Ano"), ("Candidato", "col", "Candidato"), ("Partido", "col", "Partido"), ("Lado", "col", "Lado"), ("Votos", "agg", "Votos"),
            ("Pct_Votos_Validos", "agg", "% dos válidos"), ("Resultado", "col", "Resultado"), ("Idade", "col", "Idade"), ("Escolaridade", "col", "Escolaridade"),
            ("Ocupacao", "col", "Ocupação")]
    q = {"Values": {"projections": [proj(k, "candidatos", c, 0, name=n) for c, k, n in cols]}}
    o = {"total": [{"properties": {"totals": lit(False)}}],
         "grid": [{"properties": {"textSize": lit(11), "rowPadding": lit(4), "outlineColor": solid(LINE)}}],
         "columnHeaders": [{"properties": {"fontSize": lit(11), "fontColor": solid(INK), "bold": lit(True), "backColor": solid("#F0EEE8")}}]}
    v += [container("tableEx", 160, 90, 1096, 430, q, o, title="Resultado e perfil de cada candidatura")]
    v += [bar_by_candidate(160, 536, 1096, 344, "Votos", "Votos de cada candidato", kind="columnChart")]
    v[-1]["visual"]["query"]["queryState"]["Category"]["projections"][0] = proj("col", "candidatos", "Eleicao_Candidato", active=True)
    pages.append(page("Todos os candidatos", v, height=900))

    # ---- 3. Distritos
    v = header("Votos por distrito", "Como cada distrito votou para prefeito · escolha a eleição à esquerda (marque várias para somar)")
    v += [slicer(24, 90, 120, 240, "Eleição", default=2024)]
    q = {"Category": {"projections": [proj("col", "votos_distrito", "Distrito", active=True)]},
         "Series": {"projections": [proj("col", "votos_distrito", "Candidato")]},
         "Y": {"projections": [proj("agg", "votos_distrito", "Votos", 0)]}}
    o = axis_objs()
    o["dataPoint"] = datapoints(col("votos_distrito", "Candidato"), CAND_COLOR)
    v += [container("hundredPercentStackedBarChart", 160, 90, 560, 608, q, o, title="Como cada distrito votou (% dos votos válidos)")]
    q = {"Rows": {"projections": [proj("col", "votos_distrito", "Distrito", active=True)]},
         "Columns": {"projections": [proj("col", "votos_distrito", "Lado", active=True)]},
         "Values": {"projections": [proj("measure", "votos_distrito", "Pct dos votos")]}}
    o = {"columnHeaders": [{"properties": {"fontSize": lit(10), "fontColor": solid(INK)}}], "rowHeaders": [{"properties": {"fontSize": lit(11), "fontColor": solid(INK)}}],
         "values": [{"properties": {"fontSize": lit(11)}}],
         "columnTotals": [{"properties": {"show": lit(False)}}]}
    v += [container("pivotTable", 736, 90, 520, 608, q, o, title="% dos votos válidos, por lado")]
    pages.append(page("Distritos", v))

    # ---- 4. Dinheiro e perfil
    v = header("Dinheiro e perfil dos candidatos", "Receita declarada, custo por voto, idade e patrimônio de todos os candidatos a prefeito, 2004–2024")
    v += [slicer(24, 90, 120, 240, "Eleição")]
    v += [bar_by_candidate(160, 90, 546, 470, "Receita_Declarada", "Receita declarada (R$)"),
          bar_by_candidate(722, 90, 534, 470, "Custo_Por_Voto", "Custo por voto (R$ pagos por voto)"),
          bar_by_candidate(160, 576, 546, 440, "Idade", "Idade no dia da eleição (anos)"),
          bar_by_candidate(722, 576, 534, 440, "Patrimonio_Declarado", "Patrimônio declarado (R$; a base de 2004 não traz bens)")]
    pages.append(page("Dinheiro e perfil", v, height=1040))

    # ---- 5. Câmara e campanha digital
    v = header("Câmara Municipal e campanha digital", "Vereadores eleitos em 2020 e 2024 · posts do Instagram da candidatura em 2024")
    v += [card(24, 90, 296, 96, "camara", "Cadeiras do grupo 2020", "Cadeiras do grupo em 2020 (de 9)", OPP),
          card(336, 90, 296, 96, "camara", "Cadeiras do grupo 2024", "Cadeiras do grupo em 2024 (de 9)", GRP),
          card(648, 90, 296, 96, "campanha_digital", "Posts", "Posts analisados", INK),
          card(960, 90, 296, 96, "campanha_digital", "Visualizações totais", "Visualizações somadas", INK)]
    q = {"Category": {"projections": [proj("col", "camara", "Ano", active=True)]}, "Series": {"projections": [proj("col", "camara", "Lado")]},
         "Y": {"projections": [proj("agg", "camara", "Cadeiras", 0)]}}
    o = axis_objs()
    o["dataPoint"] = datapoints(col("camara", "Lado"), {"Grupo": GRP, "Adversários": OPP})
    v += [container("columnChart", 24, 202, 400, 496, q, o, title="Cadeiras na Câmara (9), por lado")]
    q = {"Category": {"projections": [proj("col", "campanha_digital", "Fase", active=True)]}, "Y": {"projections": [proj("agg", "campanha_digital", "Engajamento", 1)]}}
    o = axis_objs()
    o["dataPoint"] = [{"properties": {"fill": solid(GRP)}}]
    v += [container("clusteredColumnChart", 440, 202, 400, 496, q, o, title="Engajamento médio por fase da campanha")]
    q = {"Category": {"projections": [proj("col", "campanha_digital", "Categoria", active=True)]}, "Y": {"projections": [proj("agg", "campanha_digital", "Visualizacoes", 0)]}}
    o = axis_objs()
    o["dataPoint"] = [{"properties": {"fill": solid(GRP)}}]
    v += [container("clusteredBarChart", 856, 202, 400, 496, q, o, title="Visualizações por tipo de conteúdo")]
    pages.append(page("Câmara e campanha digital", v))

    order = []
    for display_name_page in pages:
        pid, pjson, visuals = display_name_page
        order.append(pid)
        wj(os.path.join(RP, "definition", "pages", pid, "page.json"), pjson)
        for i, vis in enumerate(visuals):
            vis["position"]["tabOrder"] = i
            vis["position"]["z"] = i
            wj(os.path.join(RP, "definition", "pages", pid, "visuals", vis["name"], "visual.json"), vis)
    wj(os.path.join(RP, "definition", "pages", "pages.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": order, "activePageName": order[0]})


def main():
    os.makedirs(ROOT, exist_ok=True)
    if not os.path.exists(THEME_SRC):
        raise SystemExit(f"Falta o tema base: {THEME_SRC}")
    build_model()
    build_report()
    wj(os.path.join(ROOT, f"{NAME}.pbip"), {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}})
    print("Projeto gerado em", ROOT)


if __name__ == "__main__":
    main()
