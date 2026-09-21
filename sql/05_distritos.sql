-- Pergunta: como o grupo se saiu em cada um dos 7 distritos oficiais, eleicao por eleicao?
-- Reproduz a Figura 6 (mapa) e a Figura 6.2. A secao vai ao distrito pelo local de votacao de 2024.
SELECT l.distrito,
       s.ano,
       SUM(s.votos_grupo)                                          AS votos_grupo,
       SUM(s.votos_validos)                                        AS votos_validos,
       ROUND(100.0 * SUM(s.votos_grupo) / SUM(s.votos_validos), 1) AS pct_grupo
FROM v_prefeito_secao s
JOIN local_secao l ON l.secao = s.secao
WHERE l.distrito IS NOT NULL
GROUP BY l.distrito, s.ano
ORDER BY l.distrito, s.ano;
