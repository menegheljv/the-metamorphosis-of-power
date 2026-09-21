-- Pergunta: em quantas secoes o candidato do grupo teve mais votos que qualquer outro, em cada eleicao?
-- Reproduz "1 de 36 secoes em 2020" e "42 de 42 secoes em 2024" (secao 1 de 2020 e a unica vencida).
-- Empates nao ocorrem nessa serie; se ocorressem, ambos contariam como vencedores.
SELECT ano,
       COUNT(*)                                                                   AS secoes,
       SUM(CASE WHEN votos_grupo > 0 AND votos_grupo = max_secao THEN 1 ELSE 0 END) AS secoes_vencidas,
       SUM(votos_grupo)                                                           AS votos_grupo,
       SUM(votos_validos)                                                         AS votos_validos,
       ROUND(100.0 * SUM(votos_grupo) / SUM(votos_validos), 1)                    AS pct_grupo
FROM v_prefeito_secao
GROUP BY ano
ORDER BY ano;
