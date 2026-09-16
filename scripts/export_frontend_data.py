"""Export real study CSVs into a small typed JSON module for the web layer."""
from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "output"
DATA = BASE / "data"
TARGET = BASE / "frontend" / "src" / "studyData.ts"

CHARTS = [
    ("historical_arc", "Vinte anos de dados", "output/resumo_prefeito_2004_2024.csv", "TSE · resumo_prefeito_2004_2024.csv"),
    ("comparecimento_historico", "Comparecimento eleitoral", "output/comparecimento_historico.csv", "TSE · comparecimento_historico.csv"),
    ("ibge_eleitorado", "Eleitorado e população", "output/ibge_cruzamento.csv", "IBGE/TSE · ibge_cruzamento.csv"),
    ("comparecimento", "Comparecimento por eleição", "output/comparecimento_historico.csv", "TSE · comparecimento_historico.csv"),
    ("campanha_visualizacoes", "Visualizações da campanha digital", "output/campanha_digital_resumo.csv", "Registro de campanha · campanha_digital_resumo.csv"),
    ("campanha_engajamento", "Engajamento da campanha digital", "output/campanha_digital_resumo.csv", "Registro de campanha · campanha_digital_resumo.csv"),
    ("campanha_categorias", "Categorias de conteúdo", "output/campanha_digital_resumo.csv", "Registro de campanha · campanha_digital_resumo.csv"),
    ("coerencia_voto", "Coerência entre votos", "output/coerencia_voto.csv", "TSE · coerencia_voto.csv"),
    ("slope", "Virada seção a seção", "output/comparativo_candidato_prefeito_por_secao.csv", "TSE · comparativo_candidato_prefeito_por_secao.csv"),
    ("distritos_heatmap", "Desempenho por distrito", "output/distritos_resumo.csv", "TSE/Prefeitura · distritos_resumo.csv"),
    ("municipio", "Resultado municipal", "output/resumo_prefeito_2004_2024.csv", "TSE · resumo_prefeito_2004_2024.csv"),
    ("financeiro_chapa", "Financiamento da chapa", "data/receitas_candidatos_2024_alfredo_chaves.csv", "TSE · receitas_candidatos_2024_alfredo_chaves.csv"),
    ("origem_receitas", "Origem das receitas", "data/receitas_candidatos_2024_alfredo_chaves.csv", "TSE · receitas_candidatos_2024_alfredo_chaves.csv"),
    ("custo_por_voto", "Custo por voto", "data/despesas_pagas_2024_alfredo_chaves.csv", "TSE · despesas_pagas_2024_alfredo_chaves.csv"),
    ("camara", "Cadeiras na Câmara", "output/votos_vereadores_total_por_distrito.csv", "TSE · votos_vereadores_total_por_distrito.csv"),
    ("vereadores", "Vereadores eleitos", "output/votos_vereadores_total_por_distrito.csv", "TSE · votos_vereadores_total_por_distrito.csv"),
    ("vereadores_2020", "Vereadores em 2020", "output/vereadores_eleitos_2020_com_lado.csv", "TSE · vereadores_eleitos_2020_com_lado.csv"),
    ("vereadores_2024", "Vereadores em 2024", "output/vereadores_eleitos_2024_com_lado.csv", "TSE · vereadores_eleitos_2024_com_lado.csv"),
    ("votos_vereadores", "Votos para vereador por distrito", "output/votos_vereadores_grupo_por_distrito_pct.csv", "TSE · votos_vereadores_grupo_por_distrito_pct.csv"),
    ("pesquisas_timeline", "Linha do tempo das pesquisas", "output/resumo_prefeito_2004_2024.csv", "TSE · resumo_prefeito_2004_2024.csv"),
    ("pesquisas_evolucao", "Evolução eleitoral", "output/resumo_prefeito_2004_2024.csv", "TSE · resumo_prefeito_2004_2024.csv"),
    ("idade_candidatos", "Idade dos candidatos", "output/raca_candidatos.csv", "TSE · raca_candidatos.csv"),
    ("patrimonio_candidatos", "Patrimônio dos candidatos", "data/bens_candidatos_2024_alfredo_chaves.csv", "TSE · bens_candidatos_2024_alfredo_chaves.csv"),
    ("genero_candidatos", "Gênero dos candidatos", "output/genero_por_ano.csv", "TSE · genero_por_ano.csv"),
    ("raca_candidatos", "Raça/cor dos candidatos", "output/raca_candidatos.csv", "TSE · raca_candidatos.csv"),
]

def read_rows(path: Path) -> list[dict[str, object]]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.DictReader(text.splitlines()))
    result = []
    for row in rows[:120]:
        clean: dict[str, object] = {}
        for key, value in row.items():
            if value is None:
                continue
            if not isinstance(value, str):
                value = str(value)
            value = value.strip()
            try:
                clean[key] = float(value.replace(",", ".")) if "." in value or value.isdigit() else value
            except ValueError:
                clean[key] = value
        result.append(clean)
    return result

catalog = []
for slug, title, relative, source in CHARTS:
    path = BASE / relative
    catalog.append({"slug": slug, "title": title, "source": source, "rows": read_rows(path)})

TARGET.write_text(
    "export type StudyChart = { slug: string; title: string; source: string; rows: Record<string, string | number>[] };\n"
    f"export const studyCharts: StudyChart[] = {json.dumps(catalog, ensure_ascii=False)};\n",
    encoding="utf-8",
)
print(f"Wrote {TARGET} ({len(catalog)} charts)")
