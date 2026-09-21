-- Pergunta: nas secoes que existem nas duas eleicoes, quanto o grupo ganhou de 2020 para 2024,
-- e em quantas passou de minoria (<50%) para maioria absoluta (>=50%) dos votos validos?
-- Base: votos validos da secao (sem brancos e nulos). Uma linha por secao comparavel.
WITH a AS (SELECT secao, votos_grupo, votos_validos FROM v_prefeito_secao WHERE ano = 2020),
     b AS (SELECT secao, votos_grupo, votos_validos FROM v_prefeito_secao WHERE ano = 2024)
SELECT a.secao,
       a.votos_grupo                                            AS votos_grupo_2020,
       a.votos_validos                                          AS votos_validos_2020,
       b.votos_grupo                                            AS votos_grupo_2024,
       b.votos_validos                                          AS votos_validos_2024,
       ROUND(100.0 * a.votos_grupo / a.votos_validos, 1)        AS pct_2020,
       ROUND(100.0 * b.votos_grupo / b.votos_validos, 1)        AS pct_2024,
       ROUND(100.0 * b.votos_grupo / b.votos_validos
           - 100.0 * a.votos_grupo / a.votos_validos, 1)        AS variacao_pp,
       CASE WHEN 100.0 * a.votos_grupo / a.votos_validos < 50
             AND 100.0 * b.votos_grupo / b.votos_validos >= 50
            THEN 1 ELSE 0 END                                   AS virou_para_maioria
FROM a
JOIN b ON b.secao = a.secao
ORDER BY a.secao;
