-- Pergunta: quem disputou a prefeitura em cada eleicao, com quantos votos validos, e de que lado?
-- Reproduz a Tabela 0.1 e a Figura 1 do estudo (percentual sobre votos validos, sem brancos e nulos).
-- "lado": grupo = candidato da base politica do autor; adversario = a principal candidatura de
-- oposicao (o vencedor, ou o segundo colocado quando o grupo vence); terceiro = os demais.
WITH votos AS (
    SELECT ano, nr_votavel, nm_votavel, e_grupo, SUM(qt_votos) AS votos
    FROM v_votos_prefeito
    GROUP BY ano, nr_votavel, nm_votavel, e_grupo
),
total AS (
    SELECT ano, SUM(votos) AS votos_validos FROM votos GROUP BY ano
),
ranking AS (
    SELECT v.ano, v.nr_votavel, v.nm_votavel, v.e_grupo, v.votos, t.votos_validos,
           ROUND(100.0 * v.votos / t.votos_validos, 1)             AS pct,
           RANK() OVER (PARTITION BY v.ano ORDER BY v.votos DESC)  AS posicao
    FROM votos v
    JOIN total t ON t.ano = v.ano
)
SELECT r.ano,
       r.nm_votavel                                                  AS candidato,
       (SELECT c.sg_partido FROM candidatos c
         WHERE c.ano = r.ano AND c.cargo = 'Prefeito' AND c.nr_candidato = r.nr_votavel
         LIMIT 1)                                                    AS partido,
       r.nr_votavel                                                  AS numero,
       r.votos,
       r.votos_validos,
       r.pct,
       r.posicao,
       CASE WHEN r.posicao = 1 THEN 'Eleito' ELSE 'Nao eleito' END   AS resultado,
       CASE
           WHEN r.e_grupo = 1 THEN 'grupo'
           WHEN r.posicao = 1 THEN 'adversario'
           WHEN r.posicao = 2 AND (SELECT e_grupo FROM ranking w
                                    WHERE w.ano = r.ano AND w.posicao = 1) = 1 THEN 'adversario'
           ELSE 'terceiro'
       END                                                           AS lado
FROM ranking r
ORDER BY r.ano, r.posicao;
