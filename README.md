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

O workflow `.github/workflows/deploy-pages.yml` publica automaticamente o
dashboard no GitHub Pages a cada push na branch `master`. Depois de enviar o
projeto para um repositório GitHub, habilite **Settings > Pages > GitHub
Actions** como fonte de build.

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

## Limitações e próximos passos

Este repositório não valida dados oficiais, identidade, causalidade ou
desigualdades reais. Em uma aplicação de produção, adicione revisão de
proveniência, autenticação, validação de esquema, observabilidade e testes
de acessibilidade antes de publicar qualquer indicador.
