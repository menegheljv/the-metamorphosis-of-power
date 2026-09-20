# Public Data Intelligence Dashboard

Projeto demonstrativo, pequeno e reproduzível, para explorar um fluxo de
inteligência de dados públicos: banco PostgreSQL, consultas analíticas,
API em Node/TypeScript, dashboard Vite/React e uma análise alternativa em R.

> **Importante:** todos os dados são sintéticos, inventados para fins
> educacionais. Eles não descrevem eleições, pessoas, municípios ou governos
> reais e não devem ser usados para sustentar alegações públicas.

## Começar rapidamente

### Dashboard e API

Requer Node.js 20+.

```bash
cp .env.example .env
cd api && npm install && npm test
cd ../frontend && npm install && npm run build
```

Em terminais separados, execute `npm run dev` em `api` (porta 3001) e em
`frontend` (Vite, geralmente porta 5173). O dashboard funciona mesmo sem a API, usando um fallback embutido equivalente ao
CSV sintético; com a API, busca `/api/observations`.

O workflow `.github/workflows/deploy-pages.yml` publica o site no GitHub Pages a
cada push na branch `main` (habilite **Settings > Pages > GitHub Actions** como
fonte). O site é **uma página única e interativa**: o próprio estudo, com todos os
gráficos montados no navegador (Recharts), em português (`/`) e em inglês (`/en/`).
Os endereços antigos `/study/` e `/study/en/` redirecionam para elas.

### Gráficos interativos do estudo

Cada figura do estudo (`output/template.html` e `template_en.html`) tem um ponto de
montagem `<div class="ichart" data-chart="slug">`; o bundle `frontend/src/study.tsx`
o encontra e desenha o gráfico. Os dados e o texto dos gráficos vêm do pipeline:

```bash
python scripts/distritos_votos_absolutos.py     # votos totais por distrito (Figura 6.2)
python scripts/export_frontend_data.py          # -> frontend/src/studyData.ts (PT e EN)
python scripts/build_artifact.py && python scripts/build_artifact_en.py   # -> output/case_study*.html
(cd frontend && npm ci && npm run build)        # -> frontend/dist/assets/study-charts.{js,css}
python scripts/build_pages_site.py              # -> site/ (o que o GitHub Pages publica)
```

Paleta semântica: verde `#1f9d63` é o grupo, vermelho `#c8433a` o adversário, azul
`#3d7fc4` o terceiro colocado. Fonte única: Bricolage Grotesque.

### Baixar o estudo em PDF

O botão **Baixar estudo em PDF** baixa um arquivo estático (`a-metamorfose-do-poder-em-alfredo-chaves.pdf`
em português, `the-metamorphosis-of-power-in-alfredo-chaves.pdf` em inglês) com os gráficos no
mesmo estilo dos interativos. Ele é gerado imprimindo a própria página (`?print`, sem
animação, todos os gráficos montados) no Chrome/Edge headless:

```bash
python scripts/build_pages_site.py
python scripts/build_pdf.py
```

Os PDFs ficam em `output/` e são versionados; regenere-os antes de publicar uma nova versão.

### PostgreSQL

```bash
docker compose up -d
```

`schema.sql` cria as tabelas; `seed.sql` carrega os indicadores. Migrações
versionadas ficam em `database/migrations/` e podem ser aplicadas por uma
ferramenta como `psql` ou um migration runner. Consultas documentadas estão
em `database/queries.sql`.

## Análise em R

Com R e os pacotes `tidyverse`, `ggplot2` e `shiny` instalados:

```r
source("analysis/analysis.R") # resumo + gráfico
shiny::runApp("analysis")     # app interativo mínimo
```

O app lê `data/synthetic_public_data.csv`, não depende do PostgreSQL e permite
trocar o indicador. O esquema também mantém uma nota de fonte sintética em
cada observação para deixar a proveniência explícita.

## Estrutura

* `database/`: schema, seed, migrações e consultas.
* `api/`: serviço HTTP pequeno e teste nativo do Node.
* `frontend/`: componentes React, filtros, cards e gráfico Recharts. O build
  TypeScript/Vite é a validação do frontend; os testes automatizados mínimos
  ficam na API.
* `analysis/`: script tidyverse/ggplot2 e Shiny.
* `data/`: CSV sintético compartilhado entre as camadas.

## Public Data Intelligence Dashboard (demo educacional)

Esta pasta também contém um projeto demonstrativo independente, com dados
sintéticos e arquitetura didática. Consulte o arquivo histórico abaixo para
o estudo principal deste repositório; para executar o dashboard:

```bash
cd api && npm install && npm test
cd ../frontend && npm install && npm run dev
```

O dashboard usa `data/synthetic_public_data.csv` como referência, possui API
Node/TypeScript, scripts R, schema/seed/migrações PostgreSQL e deploy
automatizado no GitHub Pages em `.github/workflows/deploy-pages.yml`.

## Limitações e próximos passos

Este dashboard não valida dados oficiais, identidade, causalidade ou
desigualdades reais. Em uma aplicação de produção, adicione revisão de
proveniência, autenticação, validação de esquema, observabilidade e testes
de acessibilidade antes de publicar qualquer indicador.

# The Metamorphosis of Power (2004–2024)

*"A metamorfose do poder em Alfredo Chaves: não vivemos mais como nossos pais"* (a nod to Belchior's "Como Nossos Pais"). A case study analyzing municipal election data in Alfredo Chaves, ES (Brazil), built entirely from official public data from the TSE (Brazil's Superior Electoral Court) and cross-referenced with IBGE population, sex, race/color and income data.

**Visualização pública principal:** https://menegheljv.github.io/the-metamorphosis-of-power/

**Estudo editorial:** https://menegheljv.github.io/the-metamorphosis-of-power/study/

The public landing page includes the interactive dashboard; the original
editorial study is preserved at `/study/`.

Both are the same full case study — same sections, charts, and interactive map — kept in sync with each other.

## Context

Between 2004 and 2020, the political group behind this project lost five mayoral elections in a row in Alfredo Chaves, ES. In 2024, the same group elected Hugo Luiz, 25 at the time, the youngest mayor in the history of Espírito Santo. This repository documents the data pipeline used to analyze that turnaround, from raw TSE data to the final case study.

**Full disclosure**: Jorge Gabriel Meneghel (2004 candidate) is my father, and Hugo Luiz (2024 winner) is my brother. This started as campaign work. The data pipeline came after, to understand what actually moved the result.

## What's here

- **`scripts/`**: the Python (pandas) and SQL pipeline. Ingestion, cleaning, normalization and joins, chart generation, and the final HTML build. Covers both the 2020 vs 2024 comparison and the full 2004-2024 historical arc, cross-referenced with IBGE population estimates.
- **`data/`**: raw CSVs pulled from [dadosabertos.tse.jus.br](https://dadosabertos.tse.jus.br), filtered down to Alfredo Chaves, ES, covering every municipal election from 2004 to 2024: votes by section, results by candidate, campaign finance, turnout and abstention, electorate profile, and candidate profile and declared assets.
- **`output/`**: what the pipeline produces. Intermediate tables (CSV), the HTML template, and the final `case_study.html`.

## TSE datasets used

| Dataset | What it's for | Years covered |
|---|---|---|
| Votes by electoral section | Mapping the turnaround section by section | 2004, 2008, 2012, 2016, 2020, 2024 |
| Results by candidate (mayor and city council) | Comparing performance across the full ticket | 2004, 2008, 2012, 2016, 2020, 2024 |
| Campaign finance | Funding and spend efficiency per vote, for every candidate | 2004, 2008, 2012, 2016, 2020, 2024 |
| Turnout detail | Turnout and abstention | 2004, 2008, 2012, 2016, 2020, 2024 |
| Electorate profile | Age and gender composition | 2008, 2012, 2016, 2020, 2024 (not published for 2004) |
| Candidate profile and assets | Age, education, declared wealth | 2008, 2012, 2016, 2020, 2024 (asset data not published for 2004) |
| Registered election polls | Voting-intention trajectory during the 2024 campaign | 2024 only, out of scope for the historical arc |

## IBGE data used

Fetched from the [SIDRA API](https://sidra.ibge.gov.br), municipality code 3200300 (Alfredo Chaves, ES):

| SIDRA table | What it's for |
|---|---|
| 6579 | Annual population estimates, 2004-2024 (cross-referenced with registered voters) |
| 9514 | Population by sex, Census 2022 |
| 9605 | Population by race/color, Census 2022 |
| 10295 | Mean/median per-capita household income by sex and race/color, Census 2022 |

## Methodology

Ingestion and cleaning in `pandas`, joins and aggregations in `SQLite`, static charts in `matplotlib`, interactive charts in `TypeScript` (React + Recharts) styled with `CSS`, final build as static HTML. Every finding in the case study traces back to a public TSE dataset. When a number wasn't publicly available, that's stated in the text instead of estimated.

## How to run

```bash
python scripts/pipeline.py
python scripts/vereadores_analysis.py
python scripts/add_locations.py
python scripts/extra_analysis.py
python scripts/candidate_profile_analysis.py
python scripts/historical_arc.py
python scripts/ibge_cruzamento.py
python scripts/ibge_demografico.py
python scripts/geocode_locais.py
python scripts/fetch_basemap.py
python scripts/campanha_digital.py
python scripts/distritos_analysis.py
python scripts/coerencia_voto.py
python scripts/comparecimento_historico.py
python scripts/viz2.py && python scripts/viz3.py && python scripts/viz4.py && python scripts/viz5.py && python scripts/viz6.py
python scripts/build_artifact.py
```

Produces `output/case_study.html` (Portuguese).

`campanha_digital.py` reads `data/campanha_digital_posts.csv`, a manually-transcribed log of the candidacy's Instagram post history (not TSE data) - see the "Digital campaign" section of the case study for how it was built and its limits.

`distritos_analysis.py` cross-references each precinct's 2024 polling location - mapped to one of Alfredo Chaves' 7 official districts via `data/distritos_mapping.csv`, built from the city hall's own locality list - with the group's mayoral vote share in each of the six elections, to see how the turnaround played out across the territory.

`coerencia_voto.py` cross-references, per precinct, the group's mayoral vote share with the combined vote share of the group's council candidates (2020 and 2024), to measure how tightly the top-of-ticket and down-ballot votes moved together in each election.

`comparecimento_historico.py` reads `data/detalhe_votacao_{year}_alfredo_chaves.csv` for all six elections to chart turnout as a share of registered voters, 2004-2024.

### English build

`output/template_en.html` is a full hand-translation of `output/template.html`, and each `scripts/*_en.py` script is a twin of its Portuguese counterpart producing the same charts with translated titles, axis labels and legends (written to `output/en/`). Candidate, party and institution names are kept as-is (proper nouns); currency and number formatting switch from PT-BR (`1.234,56`) to EN-US (`1,234.56`) conventions.

```bash
python scripts/historical_arc_en.py
python scripts/ibge_cruzamento_en.py
python scripts/ibge_demografico_en.py
python scripts/campanha_digital_en.py
python scripts/distritos_analysis_en.py
python scripts/coerencia_voto_en.py
python scripts/comparecimento_historico_en.py
python scripts/viz2_en.py && python scripts/viz3_en.py && python scripts/viz4_en.py && python scripts/viz5_en.py && python scripts/viz6_en.py
python scripts/build_artifact_en.py
```

Produces `output/case_study_en.html`. Reuses `data/locais_votacao_geocoded.csv` and `output/basemap_alfredo_chaves.png` from the Portuguese build's map step (run that first) rather than re-fetching them.
