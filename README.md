# A Metamorfose do Poder em Alfredo Chaves (2004–2024)

> **Uma base política que perdeu cinco eleições seguidas para prefeito venceu as 42 seções de 2024 (58,1% dos votos válidos) sem que o comparecimento mudasse: os dados indicam que a virada veio de eleitores que já votavam, em todo o território. Feita só com dados abertos, a reconstrução serve de método para qualquer município brasileiro.**

Estudo de caso com dados eleitorais reais: seis eleições municipais (2004 a 2024) em Alfredo Chaves (ES), construído com dados abertos do TSE e do IBGE. Todos os gráficos são interativos; há também PDF e versão em inglês.

- **Estudo (português):** https://menegheljv.github.io/the-metamorphosis-of-power/
- **Study (English):** https://menegheljv.github.io/the-metamorphosis-of-power/en/
- **PDF:** [português](https://menegheljv.github.io/the-metamorphosis-of-power/a-metamorfose-do-poder-em-alfredo-chaves.pdf) · [English](https://menegheljv.github.io/the-metamorphosis-of-power/en/the-metamorphosis-of-power-in-alfredo-chaves.pdf)
- Limites do estudo e a posição do autor: seção 12 ("Limitações e viés").

## O que este estudo demonstra

| Habilidade | O que foi feito | Onde ver |
|---|---|---|
| **SQL** | Banco SQLite com as seis eleições (5 tabelas e 2 views) e cinco consultas com CTEs, funções de janela e junções, conferidas automaticamente contra o pipeline em pandas. | [`sql/`](sql/), [`scripts/build_database.py`](scripts/build_database.py), [`scripts/sql_estudo.py`](scripts/sql_estudo.py) |
| **Pipeline e qualidade dos dados** | Ingestão de extratos do TSE e do IBGE que mudam de formato entre 2004 e 2024, regras de limpeza explícitas e cobertura declarada (Tabela 3.1). A conferência entre SQL e pandas apontou e corrigiu um erro de base nos percentuais por seção: brancos e nulos estavam dentro do total. | [`scripts/pipeline.py`](scripts/pipeline.py), [`scripts/prefeitos_todos.py`](scripts/prefeitos_todos.py) |
| **Visualização** | Gráficos interativos em TypeScript, React e Recharts, mapa dos distritos com polígonos do IBGE, texto alternativo nos gráficos, leitura em celular e PDF gerado da própria página. | [`frontend/src/charts.tsx`](frontend/src/charts.tsx), [`scripts/build_pdf.py`](scripts/build_pdf.py) |
| **Estatística** | Variações em pontos percentuais por seção e distrito, coerência entre o voto para prefeito e para vereador em cada seção, cenários de sensibilidade para 2028 em R com hipóteses declaradas e limites de inferência explícitos (seção 12 do estudo). | [`scripts/coerencia_voto.py`](scripts/coerencia_voto.py), [`analysis/cenarios_2028.R`](analysis/cenarios_2028.R) |
| **Narrativa com dados** | Arco de vinte anos (cinco derrotas, a virada, o território, o financiamento, os cenários), figuras numeradas com legenda que dá a conclusão, versões em português e inglês e conflito de interesse declarado. | [`output/template.html`](output/template.html), [`output/template_en.html`](output/template_en.html) |
| **Reprodutibilidade** | Cada número liga a um extrato público do TSE ou do IBGE; os passos de execução estão abaixo e os resultados desfavoráveis ao grupo foram mantidos. | [`data/`](data/), seção "How to run" abaixo e seção 12 do estudo |

> Este repositório também guarda um **dashboard demonstrativo com dados sintéticos** (abaixo, "Dashboard demonstrativo"). Ele é independente do estudo, e nenhum dado dele descreve eleições reais. A documentação do estudo, com as fontes de dados e os passos para reproduzi-lo, está na seção "The Metamorphosis of Power (2004–2024)" mais abaixo.

---

## Dashboard demonstrativo: Public Data Intelligence (dados sintéticos)

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
python scripts/prefeitos_todos.py               # -> output/prefeitos_todos.csv e distritos_votos_cand.csv (16 candidatos a prefeito, 2004-2024)
python scripts/export_frontend_data.py          # -> frontend/src/studyData.ts (PT e EN)
python scripts/build_artifact.py && python scripts/build_artifact_en.py   # -> output/case_study*.html
(cd frontend && npm ci && npm run build)        # -> frontend/dist/assets/study-charts.{js,css}
python scripts/build_pages_site.py              # -> site/ (o que o GitHub Pages publica)
```

Paleta semântica: verde `#1f9d63` é o grupo, vermelho `#c8433a` o adversário, azul
`#3d7fc4` o terceiro colocado. Fonte única: Bricolage Grotesque.

### Cenários para 2028 (R)

A seção 11 do estudo traz cenários de "e se" para 2028, calculados em **R base** (sem pacotes extras) por
`analysis/cenarios_2028.R`. Não é previsão: são hipóteses declaradas (tendência do eleitorado, oscilação uniforme do
percentual do grupo, terceiro candidato de 0, 5 ou 10%). O script grava `output/r_cenarios_2028_*.csv`, que
`scripts/export_frontend_data.py` lê para os gráficos das Figuras 27 a 29. Para rodar (requer o R instalado):

```bash
Rscript analysis/cenarios_2028.R
python scripts/export_frontend_data.py
```

### SQL sobre as seis eleições

O SQL cobre 2004, 2008, 2012, 2016, 2020 e 2024. `scripts/build_database.py` carrega os extratos do TSE em
`output/eleicoes_alfredo_chaves.db` (SQLite, não versionado) com o esquema de `sql/00_schema.sql`: `votos_secao`,
`candidatos`, `detalhe_votacao`, `local_secao`, `grupo_eleicao` e as views `v_votos_prefeito` e `v_prefeito_secao`.
Votos válidos excluem branco (`nr_votavel` 95) e nulo (96), como em todo o estudo. As consultas:

| Arquivo | Pergunta | Onde aparece no estudo |
|---|---|---|
| `sql/01_resultado_prefeito.sql` | Quem disputou cada eleição, com quantos votos válidos e de que lado (`RANK()` e subconsulta) | Tabela 0.1, Figura 0.1 |
| `sql/02_secoes_vencidas.sql` | Em quantas seções o grupo teve mais votos que qualquer outro | "1 de 36" em 2020, "42 de 42" em 2024 |
| `sql/03_virada_2020_2024.sql` | Quanto o grupo ganhou em cada uma das 36 seções presentes nas duas eleições | Figuras 3 e 4 |
| `sql/04_comparecimento.sql` | Comparecimento, abstenção, brancos e nulos por eleição | Figura de comparecimento |
| `sql/05_distritos.sql` | Votos do grupo por distrito e eleição (junção seção, local e distrito) | Figuras 6 e 6.2 |

`scripts/sql_estudo.py` reconstrói o banco, roda as cinco consultas (resultados em `output/sql/`) e **confere cada uma
contra os CSVs do pipeline em pandas**; qualquer divergência encerra com erro:

```bash
python scripts/sql_estudo.py
```

Foi essa conferência que apontou um erro antigo: `scripts/pipeline.py` somava os votos brancos e nulos ao total de cada
seção. O total agora exclui 95 e 96, e os números por seção do estudo foram corrigidos (31 das 36 seções comparáveis
passaram de minoria para maioria, com 17,9 p.p. em média nessas seções; antes o texto dizia 28 e 20,9).

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

**Estudo interativo (português):** https://menegheljv.github.io/the-metamorphosis-of-power/

**Interactive study (English):** https://menegheljv.github.io/the-metamorphosis-of-power/en/

There is one page per language, and both are the same full case study (same sections, charts and interactive map), kept in sync with each other. The old `/study/` addresses only redirect to them.

## Context

Between 2004 and 2020, the political group behind this project lost five mayoral elections in a row in Alfredo Chaves, ES. In 2024, the same group elected Hugo Luiz, 25 at the time, the youngest mayor in the history of Espírito Santo. This repository documents the data pipeline used to analyze that turnaround, from raw TSE data to the final case study.

**Full disclosure**: Jorge Gabriel Meneghel (2004 candidate) is my father, and Hugo Luiz (2024 winner) is my brother. This started as campaign work. The data pipeline came after, to understand what actually moved the result.

## What's here

- **`scripts/`**: the Python (pandas) pipeline. Ingestion, cleaning, normalization and joins, chart generation, and the final HTML build. Covers both the 2020 vs 2024 comparison and the full 2004-2024 historical arc, cross-referenced with IBGE population estimates.
- **`sql/`**: the SQL layer. A SQLite database with all six elections and five analytical queries (results by candidate, precincts won, the 2020-2024 swing, turnout, districts), run and cross-checked against the pandas results by `scripts/sql_estudo.py`.
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
| Declared assets | Declared wealth of candidates | 2008, 2012, 2016, 2020, 2024 (not published for 2004) |
| Candidate profile | Gender, age, education, occupation (race/color only from 2016) | 2004, 2008, 2012, 2016, 2020, 2024 |
| Party-line votes | Votes for the party label, without naming a candidate | 2020, 2024 only |
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

Ingestion and cleaning in `pandas`, joins and aggregations in `SQLite` (all six elections, checked against pandas), static charts in `matplotlib`, interactive charts in `TypeScript` (React + Recharts) styled with `CSS`, final build as static HTML. Every finding in the case study traces back to a public TSE dataset. When a number wasn't publicly available, that's stated in the text instead of estimated.

## How to run

```bash
python scripts/pipeline.py
python scripts/sql_estudo.py        # SQL over the six elections, cross-checked against pandas
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
