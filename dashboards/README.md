# Painéis de Power BI e Tableau

Os mesmos dados do estudo *A Metamorfose do Poder em Alfredo Chaves* (seis eleições municipais, 2004 a 2024) em painéis interativos.
Cores do estudo: **verde = grupo**, **vermelho = principal oposição**, **azul = demais candidatos**.

| Pasta | O que tem |
|---|---|
| `data/` | CSVs de base (UTF-8, uma tabela por assunto). Gerados por `scripts/build_dashboards_data.py` a partir de `output/prefeitos_todos.csv` e das demais saídas do estudo. |
| `powerbi/` | `AMetamorfoseDoPoder.pbix` (abre direto, com os dados dentro) e o projeto `AMetamorfoseDoPoder.pbip` (texto: TMDL + PBIR, bom para o git). `imagens/` traz uma captura de cada página. |

## Power BI (5 páginas)

1. **Cinco derrotas e a virada:** linha do grupo e da principal oposição, 2004–2024, e barras com **todos os 16 candidatos a prefeito**.
2. **Todos os candidatos:** tabela com resultado e perfil de cada candidatura e votos de cada candidato.
3. **Votos por distrito:** como cada um dos sete distritos votou (escolha a eleição no segmentador; abre em 2024).
4. **Dinheiro e perfil:** receita declarada, custo por voto, idade e patrimônio de todos os candidatos.
5. **Câmara e campanha digital:** cadeiras por lado (2020 × 2024) e engajamento dos 166 posts.

Para abrir o **projeto (.pbip)** no Power BI Desktop, copie a pasta para um caminho curto (por exemplo `C:\pbi\`; o Windows limita caminhos longos) e, ao abrir, clique em **Atualizar agora**. Se aparecer "referência cíclica", clique em Atualizar mais uma vez. O `.pbix` já vem atualizado.

Para gerar de novo: `python scripts/prefeitos_todos.py && python scripts/build_dashboards_data.py && python scripts/build_powerbi_project.py`.

## Tableau

Em preparação: o Tableau Public só abre pastas de trabalho com extrações (`.hyper`), e a pasta de trabalho será gerada a partir dos mesmos CSVs de `data/`.
