# -*- coding: utf-8 -*-
"""Extrai os limites dos 7 distritos de Alfredo Chaves da malha de distritos do IBGE (Censo 2022).

Fonte: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/
       malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/distritos/shp/UF/ES_distritos_CD2022.zip
Saida: data/ibge/malha_distritos_alfredo_chaves.geojson   (requer: pip install pyshp)
"""
import io
import json
import urllib.request
import zipfile
from pathlib import Path

import shapefile

BASE = Path(__file__).resolve().parents[1]
URL = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__"
       "divisoes_intramunicipais/censo_2022/distritos/shp/UF/ES_distritos_CD2022.zip")
CD_MUN = "3200300"  # Alfredo Chaves

z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL, timeout=300).read()))
stem = next(n[:-4] for n in z.namelist() if n.endswith(".shp"))
r = shapefile.Reader(shp=io.BytesIO(z.read(stem + ".shp")), dbf=io.BytesIO(z.read(stem + ".dbf")))

features = []
for sr in r.iterShapeRecords():
    rec = sr.record.as_dict()
    if rec["CD_MUN"] != CD_MUN:
        continue
    pts = sr.shape.points
    parts = list(sr.shape.parts) + [len(pts)]
    rings = [[[round(x, 6), round(y, 6)] for x, y in pts[parts[i]:parts[i + 1]]] for i in range(len(parts) - 1)]
    features.append({"type": "Feature", "properties": {"codigo": rec["CD_DIST"], "nome": rec["NM_DIST"]},
                     "geometry": {"type": "Polygon", "coordinates": rings}})

out = BASE / "data" / "ibge" / "malha_distritos_alfredo_chaves.geojson"
out.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False), encoding="utf-8")
print(f"{len(features)} distritos -> {out} ({out.stat().st_size / 1e3:.0f} KB)")
