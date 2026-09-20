# -*- coding: utf-8 -*-
"""Todos os candidatos a prefeito de Alfredo Chaves, 2004-2024: resultado, perfil, patrimonio e financas.

Fontes (todas em data/, extratos do TSE): candidatos_ANO, perfil_candidatos_ANO (2020 e 2024),
secao_ANO (votos), bens_candidatos_ANO (2008 a 2024), receitas_candidatos_ANO, despesas_pagas_ANO.

Produz:
  output/prefeitos_todos.csv          uma linha por candidato a prefeito por eleicao (16 linhas)
  output/distritos_votos_cand.csv     votos de cada candidato a prefeito em cada distrito e eleicao

Regras: "votos validos" excluem brancos e nulos; "lado" = grupo (candidato do grupo), adversario (a principal
candidatura de oposicao: o vencedor, ou o segundo colocado quando o grupo vence) ou terceiro (os demais).
O custo por voto usa as despesas pagas / votos nominais, o mesmo calculo das Figuras 12 e 13 originais.
"""
import os
import unicodedata
from datetime import datetime

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")

YEARS = [2004, 2008, 2012, 2016, 2020, 2024]
ELECTION_DAY = {2004: (2004, 10, 3), 2008: (2008, 10, 5), 2012: (2012, 10, 7), 2016: (2016, 10, 2), 2020: (2020, 11, 15), 2024: (2024, 10, 6)}
GROUP_CANDIDATE = {
    2004: "JORGE GABRIEL MENEGHEL", 2008: "DANIEL ORLANDI", 2012: "SERGIO BIANCHI",
    2016: "RONALDO BIANCHI", 2020: "RONALDO BIANCHI", 2024: "HUGO LUIZ PICOLI MENEGHEL",
}
DISPLAY = {
    "LUIZ ROBERTO TEIXEIRA DE SIQUEIRA": "Luiz Teixeira", "NELSON TOGNERI ANDREATI": "Nelsão Togneri",
    "JORGE GABRIEL MENEGHEL": "Jorge Meneghel", "FERNANDO VIDEIRA LAFAYETTE": "Dr. Fernando",
    "DANIEL ORLANDI": "Daniel Orlandi", "ROBERTO FORTUNATO FIORIN": "Roberto Fiorin", "SERGIO BIANCHI": "Sergio Bianchi",
    "RONALDO BIANCHI": "Ronaldo Bianchi", "ARMANDO NOLASCO RIBEIRO": "Armando Zanata", "LUIZ CLAUDIO BOLDRINI": "Boldrini",
    "ROLMAR BOTECCHIA": "Rolmar Boteccia", "HUGO LUIZ PICOLI MENEGHEL": "Hugo Luiz",
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return " ".join(s.replace(".", " ").replace(",", " ").split())


def rd(name):
    path = os.path.join(DATA, name)
    for enc in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(path, sep=";", dtype=str, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def read_bens(path):
    """Soma o patrimonio declarado por SQ_CANDIDATO. Le linha a linha: em alguns anos a descricao do bem
    contem ';' e desloca as colunas, entao o valor e lido pela posicao contada do fim da linha."""
    raw = open(path, "rb").read()
    text = raw.decode("utf-8") if _is_utf8(raw) else raw.decode("latin-1")
    lines = [l for l in text.splitlines() if l.strip()]
    head = [h.strip().strip('"').upper() for h in lines[0].split(";")]
    i_sq, i_vr = head.index("SQ_CANDIDATO"), head.index("VR_BEM_CANDIDATO")
    from_end = len(head) - i_vr
    tot = {}
    for l in lines[1:]:
        f = [x.strip().strip('"') for x in l.split(";")]
        v = f[len(f) - from_end].replace(".", "").replace(",", ".")
        tot[f[i_sq]] = tot.get(f[i_sq], 0.0) + float(v)
    return pd.Series(tot)


def _is_utf8(b):
    try:
        b.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def money(series):
    return pd.to_numeric(series.str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce").fillna(0.0)


def first_col(df, *names):
    for n in names:
        if n in df.columns:
            return n
    raise KeyError(names)


# secao -> distrito (mesma atribuicao da Figura 6)
comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
comp["local_votacao"] = comp["local_votacao"].str.strip()
secao_local = dict(zip(comp["NR_SECAO"], comp["local_votacao"]))
dist_map = pd.read_csv(os.path.join(DATA, "distritos_mapping.csv"), sep=";", encoding="utf-8")
dist_map["local_votacao"] = dist_map["local_votacao"].str.strip()
local_distrito = dict(zip(dist_map["local_votacao"], dist_map["distrito"]))
ORDER = ["Sede", "Crubixá", "Ibitiruí", "Matilde", "Ribeirão do Cristo", "Sagrada Família", "São Bento de Urânia"]

rows, drows = [], []
for year in YEARS:
    cand = rd(f"candidatos_{year}_alfredo_chaves.csv")
    cand = cand[cand["DS_CARGO"].str.upper() == "PREFEITO"].copy()
    cand["KEY"] = cand["NM_CANDIDATO"].map(norm)
    prof = cand
    if year in (2020, 2024):
        p = rd(f"perfil_candidatos_{year}_alfredo_chaves.csv")
        prof = p[p["DS_CARGO"].str.upper() == "PREFEITO"].copy()
        prof["KEY"] = prof["NM_CANDIDATO"].map(norm)
    prof = prof.set_index("KEY")

    sec = rd(f"secao_{year}_alfredo_chaves.csv")
    sec = sec[sec["DS_CARGO"].str.strip().str.upper() == "PREFEITO"].copy()
    sec["QT_VOTOS"] = pd.to_numeric(sec["QT_VOTOS"], errors="coerce").fillna(0).astype(int)
    sec["NR_SECAO"] = pd.to_numeric(sec["NR_SECAO"], errors="coerce")
    sec = sec.dropna(subset=["NR_SECAO"])
    sec["NR_SECAO"] = sec["NR_SECAO"].astype(int)
    sec = sec[~sec["NM_VOTAVEL"].str.upper().isin(["VOTO BRANCO", "VOTO NULO"])]
    sec["KEY"] = sec["NM_VOTAVEL"].map(norm)
    votes = sec.groupby("KEY")["QT_VOTOS"].sum()
    total = int(votes.sum())
    assert set(votes.index) == set(cand["KEY"]), (year, set(votes.index) ^ set(cand["KEY"]))

    # bens (patrimonio)
    bens = None
    bpath = os.path.join(DATA, f"bens_candidatos_{year}_alfredo_chaves.csv")
    if os.path.exists(bpath):
        bens = read_bens(bpath)

    # receitas e despesas pagas (por numero do candidato; despesas 2020/2024 via SQ_PRESTADOR_CONTAS)
    rec = rd(f"receitas_candidatos_{year}_alfredo_chaves.csv")
    rcargo = first_col(rec, "DS_CARGO", "CARGO")
    rec = rec[rec[rcargo].str.upper() == "PREFEITO"].copy()
    rnum = first_col(rec, "NR_CAND", "NR_CANDIDATO", "NUMERO CANDIDATO")
    rec["V"] = money(rec[first_col(rec, "VR_RECEITA", "VALOR RECEITA")])
    receita = rec.groupby(rec[rnum].astype(str).str.strip())["V"].sum()
    desp = rd(f"despesas_pagas_{year}_alfredo_chaves.csv")
    if "SQ_PRESTADOR_CONTAS" in desp.columns:
        m = dict(zip(rec["SQ_PRESTADOR_CONTAS"], rec[rnum].astype(str).str.strip()))
        desp["NUM"] = desp["SQ_PRESTADOR_CONTAS"].map(m)
        desp["V"] = money(desp["VR_PAGTO_DESPESA"])
        despesa = desp.dropna(subset=["NUM"]).groupby("NUM")["V"].sum()
    else:
        dcargo = first_col(desp, "DS_CARGO", "CARGO")
        desp = desp[desp[dcargo].str.upper() == "PREFEITO"].copy()
        desp["V"] = money(desp[first_col(desp, "VR_DESPESA", "VALOR DESPESA")])
        dnum = next((c for c in ("NR_CAND", "NR_CANDIDATO", "NUMERO CANDIDATO") if c in desp.columns), None)
        if dnum:
            despesa = desp.groupby(desp[dnum].astype(str).str.strip())["V"].sum()
        else:  # 2012 e 2016: so o nome do candidato
            desp["KEY"] = desp[first_col(desp, "NOME CANDIDATO", "NM_CANDIDATO", "NO_CAND")].map(norm)
            by_name = desp.groupby("KEY")["V"].sum()
            despesa = pd.Series({str(n).strip(): by_name.get(k, float("nan")) for n, k in zip(cand["NR_CANDIDATO"], cand["KEY"])})

    ranked = sorted(cand["KEY"], key=lambda k: -votes[k])
    winner = ranked[0]
    group = norm(GROUP_CANDIDATE[year])
    opposition = winner if winner != group else ranked[1]
    born = datetime(*ELECTION_DAY[year])
    for k in ranked:
        c = cand[cand["KEY"] == k].iloc[0]
        pr = prof.loc[k]
        nasc = datetime.strptime(str(pr["DT_NASCIMENTO"]).strip('"'), "%d/%m/%Y")
        idade = born.year - nasc.year - ((born.month, born.day) < (nasc.month, nasc.day))
        num = str(c["NR_CANDIDATO"]).strip()
        pat = float(bens.get(c["SQ_CANDIDATO"], 0.0)) if bens is not None else None
        rc = float(receita.get(num, float("nan")))
        dp = float(despesa.get(num, float("nan")))
        side = "grupo" if k == group else ("adversario" if k == opposition else "terceiro")
        rows.append({
            "ano": year, "nome_completo": c["NM_CANDIDATO"].title(), "nome": DISPLAY[k], "partido": c["SG_PARTIDO"], "numero": num,
            "votos": int(votes[k]), "votos_validos": total, "pct": round(votes[k] / total * 100, 1),
            "resultado": "Eleito" if k == winner else "Não eleito", "lado": side, "idade": idade,
            "genero": pr["DS_GENERO"].title(), "cor_raca": pr["DS_COR_RACA"].title(), "escolaridade": pr["DS_GRAU_INSTRUCAO"].title(),
            "ocupacao": pr["DS_OCUPACAO"].title(), "estado_civil": pr["DS_ESTADO_CIVIL"].title(),
            "patrimonio": pat, "receita": None if pd.isna(rc) else round(rc, 2), "despesa_paga": None if pd.isna(dp) else round(dp, 2),
            "custo_por_voto": None if pd.isna(dp) else round(dp / votes[k], 2),
        })

    # votos por distrito e candidato
    sec["distrito"] = sec["NR_SECAO"].map(lambda s: local_distrito.get(secao_local.get(s)))
    lost = int(sec[sec["distrito"].isna()]["QT_VOTOS"].sum())
    if lost:
        print(f"AVISO {year}: {lost} votos em secoes sem distrito")
    dv = sec.dropna(subset=["distrito"])
    tot_d = dv.groupby("distrito")["QT_VOTOS"].sum()
    for (d, k), v in dv.groupby(["distrito", "KEY"])["QT_VOTOS"].sum().items():
        drows.append({"distrito": d, "ano": year, "nome": DISPLAY[[n for n in DISPLAY if norm(n) == k][0]], "votos": int(v), "votos_validos": int(tot_d[d])})

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "prefeitos_todos.csv"), index=False, encoding="utf-8")
dd = pd.DataFrame(drows)
dd["distrito"] = pd.Categorical(dd["distrito"], ORDER, ordered=True)
dd.sort_values(["distrito", "ano", "votos"], ascending=[True, True, False]).to_csv(os.path.join(OUT, "distritos_votos_cand.csv"), index=False, encoding="utf-8")
print(df[["ano", "nome", "partido", "votos", "pct", "resultado", "lado", "idade", "escolaridade", "patrimonio", "receita", "despesa_paga", "custo_por_voto"]].to_string(index=False))
print(len(df), "candidaturas;", len(dd), "linhas por distrito")
