# Painéis de Power BI e Tableau

Os mesmos dados do estudo *A Metamorfose do Poder em Alfredo Chaves* (seis eleições municipais, 2004 a 2024) em painéis interativos.
Cores do estudo: **verde = grupo**, **vermelho = principal oposição**, **azul = demais candidatos**.

| Pasta | O que tem |
|---|---|
| `data/` | CSVs de base (UTF-8, uma tabela por assunto). Gerados por `scripts/build_dashboards_data.py` a partir de `output/prefeitos_todos.csv` e das demais saídas do estudo. |
| `powerbi/` | `AMetamorfoseDoPoder.pbix` (abre direto, com os dados dentro) e o projeto `AMetamorfoseDoPoder.pbip` (texto: TMDL + PBIR, bom para o git). `imagens/` traz uma captura de cada página. |
| `tableau/` | `AMetamorfoseDoPoder.twbx` (pasta de trabalho completa, com as extrações `.hyper` dentro; abre direto no Tableau Public ou Desktop). Gerado 100% por script (`scripts/build_tableau_workbook.py`), sem precisar abrir o Tableau. |

## Power BI (5 páginas)

1. **Cinco derrotas e a virada:** linha do grupo e da principal oposição, 2004–2024, e barras com **todos os 16 candidatos a prefeito**.
2. **Todos os candidatos:** tabela com resultado e perfil de cada candidatura e votos de cada candidato.
3. **Votos por distrito:** como cada um dos sete distritos votou (escolha a eleição no segmentador; abre em 2024).
4. **Dinheiro e perfil:** receita declarada, eficiência de investimento por voto, idade e patrimônio de todos os candidatos.
5. **Câmara e campanha digital:** cadeiras por lado (2020 × 2024) e engajamento dos 166 posts.

Para abrir o **projeto (.pbip)** no Power BI Desktop, copie a pasta para um caminho curto (por exemplo `C:\pbi\`; o Windows limita caminhos longos) e, ao abrir, clique em **Atualizar agora**. Se aparecer "referência cíclica", clique em Atualizar mais uma vez.

Para gerar de novo: `python scripts/prefeitos_todos.py && python scripts/build_dashboards_data.py && python scripts/build_powerbi_project.py`.

⚠️ **O `.pbix` é um binário e não se atualiza sozinho quando o `.pbip` muda.** Depois de qualquer mudança nos dados, abra o `.pbip` no Power BI Desktop e faça **Arquivo → Salvar como → Power BI (.pbix)**, sobrescrevendo `AMetamorfoseDoPoder.pbix` — só assim quem baixa o painel pelo site recebe os números novos.

## Tableau (4 painéis, 9 planilhas)

1. **Cinco derrotas e a virada** (planilha "Arco histórico" + "Todos os candidatos"): mesma leitura do Power BI, cores fixas por candidato/lado.
2. **Distritos** ("Votos por distrito"): resultado por distrito, com **filtro de Ano interativo** (abre em 2024; dá pra marcar mais de um ano ao mesmo tempo, que empilha os candidatos).
3. **Dinheiro e perfil** ("Receita declarada", "Eficiência de investimento", "Idade", "Patrimônio declarado").
4. **Câmara e campanha digital** ("Câmara Municipal", "Engajamento por fase").

Cores e legendas conferidas manualmente no Tableau Public, planilha por planilha, nos 4 painéis: verde = grupo, vermelho = principal oposição, azul = demais candidatos, e uma paleta própria por candidato — as mesmas do estudo e do Power BI (o Tableau Public não deixa fixar o hex exato pela interface; as cores usadas são as mais próximas disponíveis no seletor). O gerador (`build_tableau_workbook.py`) tinha deixado "Demais candidatos" sem cor própria (herdava o vermelho da oposição por engano) — corrigido manualmente depois de gerar; se o `.twbx` for regenerado do zero, conferir nas planilhas "Todos os candidatos" e "Votos por distrito" antes de publicar.

Para gerar de novo: `python scripts/build_dashboards_data.py && python scripts/build_tableau_workbook.py` (usa `tableauhyperapi`; não precisa do Tableau instalado) — mas isso **sobrescreve** as correções de cor e o filtro de ano feitos manualmente na interface, que não são gerados por código. Depois de regenerar, refazer os dois ajustes no Tableau antes de publicar.
