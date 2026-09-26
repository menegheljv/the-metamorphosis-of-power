# -*- coding: utf-8 -*-
"""Pasta de trabalho do Tableau (.twbx) de "A Metamorfose do Poder em Alfredo Chaves".

Gera dashboards/tableau/AMetamorfoseDoPoder.twb e o pacote .twbx (com os CSVs de dashboards/data dentro).
Nove planilhas e quatro paineis, com as cores do estudo: verde = grupo, vermelho = principal oposicao, azul = demais candidatos.

Rode antes: python scripts/build_dashboards_data.py
"""
import os
import shutil
import uuid
import zipfile
from xml.sax.saxutils import escape

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "dashboards", "data")
OUT = os.path.join(BASE, "dashboards", "tableau")
NAME = "AMetamorfoseDoPoder"

GRP, OPP, OTH = "#1f9d63", "#c8433a", "#3d7fc4"
LADO_PAL = {"Grupo": GRP, "Principal oposição": OPP, "Demais candidatos": OTH}
CAM_PAL = {"Grupo": GRP, "Adversários": OPP}
CAND_PAL = {
    "Jorge Meneghel": "#0f7a4a", "Daniel Orlandi": "#2fb37a", "Sergio Bianchi": "#66c79e", "Ronaldo Bianchi": "#1f9d63", "Hugo Luiz": "#0b5e38",
    "Dr. Fernando": "#c8433a", "Roberto Fiorin": "#e07b72", "Rolmar Boteccia": "#8f2a23",
    "Luiz Teixeira": "#3d7fc4", "Nelsão Togneri": "#7fb0e0", "Armando Zanata": "#2a5c94", "Boldrini": "#5e96cf",
}

_n = [0]
SHEETS_META = []   # (planilha, referencia da cor)
DASH_META = []


def uid():
    _n[0] += 1
    return "{" + str(uuid.UUID(int=(0xA1B2C3D4 << 96) + _n[0])).upper() + "}"


def q(v):  # valor de texto para atributo (aspas duplas escapadas)
    return escape(f'"{v}"', {'"': "&quot;", "'": "&apos;"})


# ------------------------------------------------------------------ fontes de dados (CSV texto)
SOURCES = {}


def load_source(key, csv, measures=(), dates=()):
    df = pd.read_csv(os.path.join(DATA, csv))
    cols = []
    for i, (c, dt) in enumerate(df.dtypes.items()):
        if c in dates:
            t = "date"
        elif str(dt).startswith("int"):
            t = "integer"
        elif str(dt).startswith("float"):
            t = "real"
        else:
            t = "string"
        cols.append((c, t))
    SOURCES[key] = {"id": f"federated.{uuid.uuid5(uuid.NAMESPACE_DNS, key).hex[:26]}", "csv": csv, "cols": cols, "measures": set(measures)}


load_source("candidatos", "candidatos.csv", measures={"Votos", "Pct_Votos_Validos", "Idade", "Patrimonio_Declarado", "Receita_Declarada", "Despesa_Paga", "Custo_Por_Voto", "Ordem"})
load_source("votos_distrito", "votos_distrito.csv", measures={"Votos", "Votos_Validos_Distrito", "Pct_No_Distrito"})
load_source("camara", "camara.csv", measures={"Cadeiras"})
load_source("campanha", "campanha_digital.csv", measures={"Visualizacoes", "Curtidas", "Comentarios", "Compartilhamentos", "Engajamento"}, dates={"Data"})

PALETTES = {"candidatos": ("Lado", LADO_PAL), "votos_distrito": ("Candidato", CAND_PAL), "camara": ("Lado", CAM_PAL)}
REMOTE = {"integer": 20, "real": 5, "string": 129, "date": 133}


def col_role(src, name, dt):
    if name in src["measures"]:
        return "measure", "quantitative"
    if dt in ("integer",):
        return "dimension", "ordinal"
    if dt == "real":
        return "measure", "quantitative"
    return "dimension", "nominal"


def extract_xml(key, obj):
    s = SOURCES[key]
    csv = s["csv"]
    recs = []
    for i, (c, t) in enumerate(s["cols"]):
        agg = "Sum" if t in ("integer", "real") else "Count"
        extra = "<collation flag='0' name='LEN_RUS' />\n              " if t == "string" else ""
        recs.append(f"""            <metadata-record class='column'>
              <remote-name>{escape(c)}</remote-name>
              <remote-type>{REMOTE[t]}</remote-type>
              <local-name>[{escape(c)}]</local-name>
              <parent-name>[Extract]</parent-name>
              <remote-alias>{escape(c)}</remote-alias>
              <ordinal>{i}</ordinal>
              <family>{csv}</family>
              <local-type>{t}</local-type>
              <aggregation>{agg}</aggregation>
              <approx-count>1</approx-count>
              <contains-null>true</contains-null>
              {extra}<object-id>{obj}</object-id>
            </metadata-record>""")
    return f"""      <extract count='-1' enabled='true' object-id='' units='records'>
        <connection access_mode='readonly' author-locale='pt_BR' class='hyper' dbname='Data/Extracts/{key}.hyper' default-settings='hyper' schema='Extract' sslmode='' tablename='Extract' update-time='09/20/2026 06:00:00 PM' username='tableau_internal_user'>
          <relation name='Extract' table='[Extract].[Extract]' type='table' />
          <metadata-records>
{chr(10).join(recs)}
          </metadata-records>
        </connection>
      </extract>"""


def palette_style(key):
    """Cores fixas por valor (ficam na fonte de dados, como o Tableau grava as cores atribuidas a mao)."""
    if key not in PALETTES:
        return ""
    col, pal = PALETTES[key]
    maps = "\n".join(f"          <map to='{v}'>\n            <bucket>{q(k)}</bucket>\n          </map>" for k, v in pal.items())
    return f"""      <style>
        <style-rule element='mark'>
          <encoding attr='color' field='[none:{col}:nk]' type='palette'>
{maps}
          </encoding>
        </style-rule>
      </style>
"""


def datasource_xml(key):
    s = SOURCES[key]
    sid, csv = s["id"], s["csv"]
    named = f"textscan.{sid[-24:]}"
    obj = f"[{csv}_{uuid.uuid5(uuid.NAMESPACE_DNS, csv).hex.upper()}]"
    cols = "\n".join(f"            <column datatype='{t}' name='{escape(c)}' ordinal='{i}' />" for i, (c, t) in enumerate(s["cols"]))
    recs = []
    for i, (c, t) in enumerate(s["cols"]):
        agg = "Sum" if t in ("integer", "real") else "Count"
        extra = "<scale>1</scale>\n            <width>1073741823</width>\n            " if t == "string" else ""
        coll = "<collation flag='0' name='LEN_RUS' />\n            " if t == "string" else ""
        recs.append(f"""          <metadata-record class='column'>
            <remote-name>{escape(c)}</remote-name>
            <remote-type>{REMOTE[t]}</remote-type>
            <local-name>[{escape(c)}]</local-name>
            <parent-name>[{csv}]</parent-name>
            <remote-alias>{escape(c)}</remote-alias>
            <ordinal>{i}</ordinal>
            <local-type>{t}</local-type>
            <aggregation>{agg}</aggregation>
            {extra}<contains-null>true</contains-null>
            {coll}<object-id>{obj}</object-id>
          </metadata-record>""")
    return f"""    <datasource caption='{key}' inline='true' name='{sid}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='{key}' name='{named}'>
            <connection class='textscan' directory='Data/Datasources' filename='{csv}' password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection='{named}' name='{csv}' table='[{csv.replace('.', '#')}]' type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
{cols}
          </columns>
        </relation>
        <metadata-records>
          <metadata-record class='capability'>
            <remote-name />
            <remote-type>0</remote-type>
            <parent-name>[{csv}]</parent-name>
            <remote-alias />
            <aggregation>Count</aggregation>
            <contains-null>true</contains-null>
            <attributes>
              <attribute datatype='string' name='character-set'>&quot;UTF-8&quot;</attribute>
              <attribute datatype='string' name='collation'>&quot;en_US&quot;</attribute>
              <attribute datatype='string' name='field-delimiter'>&quot;,&quot;</attribute>
              <attribute datatype='string' name='header-row'>&quot;true&quot;</attribute>
              <attribute datatype='string' name='locale'>&quot;en_US&quot;</attribute>
              <attribute datatype='string' name='single-char'>&quot;&quot;</attribute>
            </attributes>
          </metadata-record>
{chr(10).join(recs)}
        </metadata-records>
      </connection>
      <aliases enabled='yes' />
      <column caption='{csv}' datatype='table' name='[__tableau_internal_object_id__].{obj}' role='measure' type='quantitative' />
{extract_xml(key, obj)}
      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />
{palette_style(key)}      <semantic-values>
        <semantic-value key='[Country].[Name]' value='&quot;Brasil&quot;' />
      </semantic-values>
    </datasource>"""


# ------------------------------------------------------------------ planilhas
def inst_name(col, deriv, dt):
    if deriv == "none":
        return f"[none:{col}:{'ok' if dt == 'integer' else 'nk'}]"
    return f"[{deriv}:{col}:qk]"


def sheet_xml(name, key, rows, cols, color=None, text=None, mark="Automatic", palette=None, filters=(), filter_fields=(), sort=None, title=None, size=None):
    """rows/cols/color/text: tuples (coluna, derivacao). filters: lista de xml prontos. sort: (dimensao, medida-de-ordem)."""
    src = SOURCES[key]
    sid = src["id"]
    dts = dict(src["cols"])
    used = {}
    order = []

    def use(field):
        if field is None:
            return None
        c, d = field
        n = inst_name(c, d, dts[c])
        if (c, d) not in used:
            used[(c, d)] = n
            order.append((c, d))
        return f"[{sid}].{n}"

    r = " / ".join(use(f) for f in rows) if rows else ""
    c_ = " / ".join(use(f) for f in cols) if cols else ""
    col_ref = use(color)
    SHEETS_META.append((name, col_ref))
    txt_ref = use(text)
    sort_xml = ""
    if sort:
        dim, order_field = sort
        sort_xml = f"          <sort class='computed' column='{use(dim)}' direction='ASC' using='{use(order_field)}' />\n"
    for f in filter_fields:  # filtros precisam das instancias declaradas
        use(f)
    decl = []
    seen_cols = set()
    for (c, d) in order:
        if c not in seen_cols:
            seen_cols.add(c)
            role, typ = col_role(src, c, dts[c])
            decl.append(f"            <column datatype='{dts[c]}' name='[{c}]' role='{role}' type='{typ}' />")
    for (c, d) in order:
        role, typ = col_role(src, c, dts[c])
        it = "quantitative" if d != "none" else ("ordinal" if dts[c] == "integer" and c not in src["measures"] else "nominal")
        if d != "none":
            it = "quantitative"
        decl.append(f"            <column-instance column='[{c}]' derivation='{'None' if d == 'none' else {'sum': 'Sum', 'avg': 'Avg', 'min': 'Min', 'max': 'Max'}[d]}' name='{used[(c, d)]}' pivot='key' type='{it}' />")
    pal_rule = ""
    style_enc = ""
    if palette and color:
        maps = "\n".join(f"              <map to='{v}'>\n                <bucket>{q(k)}</bucket>\n              </map>" for k, v in palette.items())
        pal_rule = f"""              <style-rule element='mark'>
                <encoding attr='color' field='{col_ref}' type='palette'>
{maps}
                </encoding>
              </style-rule>
"""
    elif color is None:
        style_enc = f"""          <style-rule element='mark'>
            <format attr='mark-color' value='{GRP}' />
          </style-rule>
"""
    encs = []
    if color:
        encs.append(f"              <color column='{col_ref}' />")
    if txt_ref:
        encs.append(f"              <text column='{txt_ref}' />")
    enc_xml = "            <encodings>\n" + "\n".join(encs) + "\n            </encodings>\n" if encs else ""
    label_style = ("            <style>\n              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='true' />\n"
                   "                <format attr='mark-labels-cull' value='true' />\n              </style-rule>\n            </style>\n") if txt_ref else ""
    pane_style = label_style  # as cores por valor ficam na fonte de dados (palette_style), como o Tableau grava
    title_xml = ""
    if title:
        title_xml = f"      <layout-options>\n        <title>\n          <formatted-text>\n            <run fontcolor='#17171a' fontname='Tableau Bold' fontsize='14'>{escape(title)}</run>\n          </formatted-text>\n        </title>\n      </layout-options>\n"
    filt = "\n".join(filters)
    return f"""    <worksheet name='{escape(name)}'>
{title_xml}      <table>
        <view>
          <datasources>
            <datasource caption='{key}' name='{sid}' />
          </datasources>
          <datasource-dependencies datasource='{sid}'>
{chr(10).join(decl)}
          </datasource-dependencies>
{filt}
{sort_xml}          <aggregation value='true' />
        </view>
        <style>
{style_enc}        </style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />
{enc_xml}{pane_style}          </pane>
        </panes>
        <rows>{r}</rows>
        <cols>{c_}</cols>
      </table>
      <simple-id uuid='{uid()}' />
    </worksheet>"""


def f_except(key, col, dt, member):
    sid = SOURCES[key]["id"]
    inst = inst_name(col, "none", dt)
    return f"""          <filter class='categorical' column='[{sid}].{inst}'>
            <groupfilter function='except' user:ui-domain='database' user:ui-enumeration='exclusive' user:ui-marker='enumerate'>
              <groupfilter function='level-members' level='{inst}' />
              <groupfilter function='member' level='{inst}' member='{q(member)}' />
            </groupfilter>
          </filter>"""


def f_member(key, col, dt, member):
    sid = SOURCES[key]["id"]
    inst = inst_name(col, "none", dt)
    val = str(member) if dt == "integer" else q(member)
    return f"""          <filter class='categorical' column='[{sid}].{inst}'>
            <groupfilter function='member' level='{inst}' member='{val}' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />
          </filter>"""


def build_sheets():
    S = []
    S.append(sheet_xml("Arco histórico", "candidatos", rows=[("Pct_Votos_Validos", "avg")], cols=[("Ano", "none")], color=("Lado", "none"),
                       text=("Pct_Votos_Validos", "avg"), mark="Line", palette=LADO_PAL, filters=[f_except("candidatos", "Lado", "string", "Demais candidatos")], filter_fields=[("Lado", "none")],
                       title="GRUPO E PRINCIPAL OPOSIÇÃO, % DOS VOTOS VÁLIDOS"))
    S.append(sheet_xml("Todos os candidatos", "candidatos", rows=[("Eleicao_Candidato", "none")], cols=[("Pct_Votos_Validos", "sum")], color=("Lado", "none"),
                       text=("Pct_Votos_Validos", "sum"), mark="Bar", palette=LADO_PAL, sort=(("Eleicao_Candidato", "none"), ("Ordem", "min")),
                       title="TODOS OS CANDIDATOS A PREFEITO, % DOS VOTOS VÁLIDOS"))
    S.append(sheet_xml("Votos por distrito", "votos_distrito", rows=[("Distrito", "none")], cols=[("Pct_No_Distrito", "sum")], color=("Candidato", "none"),
                       text=("Pct_No_Distrito", "sum"), mark="Bar", palette=CAND_PAL, filters=[f_member("votos_distrito", "Ano", "integer", 2024)], filter_fields=[("Ano", "none")],
                       title="COMO CADA DISTRITO VOTOU, % DOS VOTOS VÁLIDOS"))
    for nm, field, ttl in (("Receita declarada", "Receita_Declarada", "RECEITA DECLARADA (R$)"), ("Eficiência de investimento", "Custo_Por_Voto", "EFICIÊNCIA DE INVESTIMENTO: R$ PAGOS POR VOTO (MENOR = MAIS EFICIENTE)"),
                           ("Idade", "Idade", "IDADE NO DIA DA ELEIÇÃO (ANOS)"), ("Patrimônio declarado", "Patrimonio_Declarado", "PATRIMÔNIO DECLARADO (R$, 2008–2024)")):
        S.append(sheet_xml(nm, "candidatos", rows=[("Eleicao_Candidato", "none")], cols=[(field, "sum")], color=("Lado", "none"), text=(field, "sum"), mark="Bar",
                           palette=LADO_PAL, sort=(("Eleicao_Candidato", "none"), ("Ordem", "min")), title=ttl))
    S.append(sheet_xml("Câmara Municipal", "camara", rows=[("Cadeiras", "sum")], cols=[("Ano", "none")], color=("Lado", "none"), text=("Cadeiras", "sum"), mark="Bar",
                       palette=CAM_PAL, title="CADEIRAS NA CÂMARA (9), POR LADO"))
    S.append(sheet_xml("Engajamento por fase", "campanha", rows=[("Engajamento", "avg")], cols=[("Fase", "none")], text=("Engajamento", "avg"), mark="Bar",
                       title="ENGAJAMENTO MÉDIO POR FASE DA CAMPANHA"))
    return "\n".join(S)


# ------------------------------------------------------------------ paineis
def dash_xml(name, w, h, rows):
    """Painel em fluxo (como o Tableau grava): rows = [(altura_em_px, [(planilha, largura_em_px), ...]), ...]. Nomes de planilha ou None."""
    DASH_META.append((name, [sheet for _, cells in rows for sheet, _ in cells]))
    zid = [10]

    def nid():
        zid[0] += 1
        return zid[0]

    total_h = sum(r[0] for r in rows)
    out = []
    for rh, cells in rows:
        tw = sum(c[1] for c in cells)
        inner = []
        for sheet, cw in cells:
            inner.append(f"            <zone h='100000' id='{nid()}' name='{escape(sheet)}' w='{int(cw / tw * 100000)}' x='0' y='0' />")
        out.append(f"          <zone h='{int(rh / total_h * 100000)}' id='{nid()}' param='horz' type-v2='layout-flow' w='100000' x='0' y='0'>" + chr(10) + chr(10).join(inner) + chr(10) + "          </zone>")
    return f"""    <dashboard name='{escape(name)}'>
      <style />
      <size maxheight='{h}' maxwidth='{w}' minheight='{h}' minwidth='{w}' sizing-mode='fixed' />
      <zones>
        <zone h='100000' id='2' type-v2='layout-basic' w='100000' x='0' y='0'>
        <zone h='98000' id='3' param='vert' type-v2='layout-flow' w='98400' x='800' y='1000'>
{chr(10).join(out)}
        </zone>
          <zone-style>
            <format attr='border-color' value='#000000' />
            <format attr='border-style' value='none' />
            <format attr='border-width' value='0' />
            <format attr='margin' value='8' />
          </zone-style>
        </zone>
      </zones>
      <simple-id uuid='{uid()}' />
    </dashboard>"""


def build_dashboards():
    D = []
    D.append(dash_xml("Cinco derrotas e a virada", 1280, 900, [(900, [("Arco histórico", 500), ("Todos os candidatos", 780)])]))
    D.append(dash_xml("Distritos", 1280, 720, [(720, [("Votos por distrito", 1280)])]))
    D.append(dash_xml("Dinheiro e perfil", 1280, 1500, [(750, [("Receita declarada", 640), ("Eficiência de investimento", 640)]), (750, [("Idade", 640), ("Patrimônio declarado", 640)])]))
    D.append(dash_xml("Câmara e campanha digital", 1280, 640, [(640, [("Câmara Municipal", 640), ("Engajamento por fase", 640)])]))
    return "\n".join(D)


def windows_xml():
    out = []
    for name, col_ref in SHEETS_META:
        right = (f"        <edge name='right'>\n          <strip size='160'>\n            <card pane-specification-id='0' param='{col_ref}' type='color' />\n          </strip>\n        </edge>\n"
                 if col_ref else "")
        out.append(f"""    <window class='worksheet' name='{escape(name)}'>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='2147483647'>
            <card type='title' />
          </strip>
        </edge>
{right}      </cards>
      <simple-id uuid='{uid()}' />
    </window>""")
    for i, (name, sheets) in enumerate(DASH_META):
        vps = "".join(f"""        <viewpoint name='{escape(sh)}'>
          <zoom type='entire-view' />
        </viewpoint>
""" for sh in sheets)
        out.append(f"""    <window class='dashboard'{" maximized='true'" if i == 0 else ""} name='{escape(name)}'>
      <viewpoints>
{vps}      </viewpoints>
      <active id='-1' />
      <simple-id uuid='{uid()}' />
    </window>""")
    return "\n".join(out)


def workbook_xml():
    ds = "\n".join(datasource_xml(k) for k in SOURCES)
    return f"""<?xml version='1.0' encoding='utf-8' ?>

<workbook original-version='18.1' source-build='2026.2.2 (20262.26.0819.2015)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <AccessibleZoneTabOrder />
    <AnimationOnByDefault />
    <MarkAnimation />
    <ObjectModelEncapsulateLegacy />
    <ObjectModelExtractV2 />
    <ObjectModelTableType />
    <SchemaViewerObjectModel />
    <SetMembershipControl />
    <SheetIdentifierTracking />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{ds}
  </datasources>
  <worksheets>
{build_sheets()}
  </worksheets>
  <dashboards>
{build_dashboards()}
  </dashboards>
  <windows saved-dpi-scale-factor='1' source-height='30'>
{windows_xml()}
  </windows>
</workbook>
"""


def write_hyper(key, path):
    """Cria a extracao (.hyper) da fonte: tabela "Extract"."Extract" com os mesmos tipos do CSV."""
    from tableauhyperapi import Connection, CreateMode, HyperProcess, Inserter, SqlType, TableDefinition, TableName, Telemetry
    src = SOURCES[key]
    df = pd.read_csv(os.path.join(DATA, src["csv"]))
    types = {"integer": SqlType.big_int(), "real": SqlType.double(), "string": SqlType.text(), "date": SqlType.date()}
    if os.path.exists(path):
        os.remove(path)
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint, path, CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema("Extract")
            td = TableDefinition(TableName("Extract", "Extract"), [TableDefinition.Column(c, types[t]) for c, t in src["cols"]])
            conn.catalog.create_table(td)
            with Inserter(conn, td) as ins:
                for row in df.itertuples(index=False):
                    vals = []
                    for (c, t), v in zip(src["cols"], row):
                        if pd.isna(v):
                            vals.append(None)
                        elif t == "integer":
                            vals.append(int(v))
                        elif t == "real":
                            vals.append(float(v))
                        elif t == "date":
                            from tableauhyperapi import Date
                            d = pd.Timestamp(v)
                            vals.append(Date(d.year, d.month, d.day))
                        else:
                            vals.append(str(v))
                    ins.add_row(vals)
                ins.execute()


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "_hyper")
    os.makedirs(tmp, exist_ok=True)
    for key in SOURCES:
        write_hyper(key, os.path.join(tmp, f"{key}.hyper"))
    twb = workbook_xml()
    twb_path = os.path.join(OUT, f"{NAME}.twb")
    with open(twb_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(twb)
    twbx = os.path.join(OUT, f"{NAME}.twbx")
    with zipfile.ZipFile(twbx, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(twb_path, f"{NAME}.twb")
        for key, s in SOURCES.items():
            z.write(os.path.join(DATA, s["csv"]), f"Data/Datasources/{s['csv']}")
            z.write(os.path.join(tmp, f"{key}.hyper"), f"Data/Extracts/{key}.hyper")
    os.remove(twb_path)
    shutil.rmtree(tmp, ignore_errors=True)
    print("Gerado", twbx)


if __name__ == "__main__":
    main()
