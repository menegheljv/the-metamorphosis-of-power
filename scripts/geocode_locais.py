# -*- coding: utf-8 -*-
"""
Geocodes the 18 physical voting locations of Alfredo Chaves, ES using the
free Photon (komoot) geocoder, biased to the municipality's bounding box.
Produces data/locais_votacao_geocoded.csv (local, endereco, secoes, lat, lon, query_used).
"""
import pandas as pd
import urllib.request, json, time, os, csv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
DATA = os.path.join(BASE, "data")

comp = pd.read_csv(os.path.join(OUT, "comparativo_candidato_prefeito_por_secao.csv"))
locais = comp.dropna(subset=["local_votacao"]).groupby(["local_votacao", "endereco_votacao"])["NR_SECAO"].apply(
    lambda s: ", ".join(str(int(x)) for x in sorted(s))
).reset_index().sort_values("local_votacao")

# Alfredo Chaves bounding box (from Photon municipality lookup), with margin
BBOX = (-41.05, -20.75, -40.60, -20.38)  # lon_min, lat_min, lon_max, lat_max

UA = "alfredo-chaves-case-study-research/1.0"

def photon_search(query, limit=5):
    url = "https://photon.komoot.io/api/?" + urllib.parse.urlencode({"q": query, "limit": limit})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def pick_best(feats):
    """Prefer a feature whose city/state clearly is Alfredo Chaves, ES."""
    for f in feats:
        p = f.get("properties", {})
        if p.get("city") == "Alfredo Chaves" or p.get("name") == "Alfredo Chaves":
            return f
    for f in feats:
        p = f.get("properties", {})
        if p.get("state") == "Espírito Santo":
            return f
    return feats[0] if feats else None

import urllib.parse

# Clean venue name -> a short locality/query hint for rural votes
NAME_HINTS = {
    "CRECHE COMECINHO DE GENTE": "Alfredo Chaves centro",
    "CRECHE PEQUERRUCHOS": "Alfredo Chaves centro",
    "EEEF DE CRUBIXÁ": "Crubixá",
    "EEEFM CAMILA MOTA": "Alfredo Chaves centro",
    "EEUEF VILA NOVA DE MARAVILHA": "Vila Nova de Maravilha",
    "EMEF ANA ARAÚJO": "Alfredo Chaves centro",
    "EMEF ENGANO": "Engano, Alfredo Chaves",
    "EMEF FAZENDA APARECIDA": "Fazenda Aparecida, Alfredo Chaves",
    "EMEF FELIPE MODOLO": "Alfredo Chaves centro",
    "EMEF SAGRADA FAMÍLIA": "Alfredo Chaves centro",
    "EMUEF QUARTO TERRITÓRIO": "Quarto Território, Alfredo Chaves",
    "PRÉDIO DA ANTIGA ESCOLA ALMERINDA BRUNORO": "Alfredo Chaves centro",
    "SALÃO COMUNITÁRIO DE NOVA ESTRELA": "Nova Estrela, Alfredo Chaves",
    "SALÃO COMUNITÁRIO DE SÃO BENTO DE URÂNIA": "São Bento de Urânia, Alfredo Chaves",
    "SALÃO DA IGREJA CATÓLICA DE CACHOEIRA ALTA": "Cachoeira Alta, Alfredo Chaves",
    "SALÃO DA IGREJA CATÓLICA DE SÃO FRANCISCO DE BATATAL": "São Francisco do Batatal, Alfredo Chaves",
    "SALÃO DA IGREJA DE SÃO MARTINHO": "São Martinho, Alfredo Chaves",
    "SALÃO PAROQUIAL DA IGREJA DE NOSSA SENHORA DA CONCEIÇÃO": "Alfredo Chaves centro",
}

rows = []
for _, r in locais.iterrows():
    local = r["local_votacao"]
    endereco = r["endereco_votacao"]
    hint = NAME_HINTS.get(local, local)
    queries = [
        f"{hint}, Alfredo Chaves, ES, Brazil",
        f"{local}, Alfredo Chaves, ES, Brazil",
        f"{local}, {endereco}, Alfredo Chaves, ES, Brazil",
        f"Alfredo Chaves, ES, Brazil",  # last resort: municipality centroid
    ]
    lat = lon = None
    used_query = None
    for q in queries:
        try:
            data = photon_search(q)
            feats = data.get("features", [])
            best = pick_best(feats)
            if best:
                lon, lat = best["geometry"]["coordinates"]
                used_query = q
                break
        except Exception as e:
            print("ERROR", q, e)
        time.sleep(1.1)
    rows.append({
        "local_votacao": local, "endereco_votacao": endereco, "secoes": r["NR_SECAO"],
        "lat": lat, "lon": lon, "query_used": used_query,
    })
    print(local, "->", lat, lon, "|", used_query)
    time.sleep(1.1)

out_df = pd.DataFrame(rows)
out_path = os.path.join(DATA, "locais_votacao_geocoded.csv")
out_df.to_csv(out_path, index=False, encoding="utf-8")
print(f"\nSaved: {out_path}")
print(f"Geocoded: {out_df['lat'].notna().sum()} / {len(out_df)}")
