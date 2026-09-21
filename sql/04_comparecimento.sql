-- Pergunta: quanto do eleitorado compareceu, absteve-se ou votou em branco/nulo em cada eleicao?
-- Reproduz a Figura de comparecimento historico (base: eleitorado apto, cargo Prefeito).
SELECT ano,
       qt_aptos                                                         AS aptos,
       qt_comparecimento                                                AS comparecimento,
       qt_abstencoes                                                    AS abstencoes,
       qt_brancos                                                       AS brancos,
       qt_nulos                                                         AS nulos,
       ROUND(100.0 * qt_comparecimento / qt_aptos, 2)                   AS pct_comparecimento,
       ROUND(100.0 * qt_abstencoes / qt_aptos, 2)                       AS pct_abstencao,
       ROUND(100.0 * (qt_brancos + qt_nulos) / qt_comparecimento, 2)    AS pct_brancos_nulos
FROM detalhe_votacao
WHERE cargo = 'Prefeito'
ORDER BY ano;
