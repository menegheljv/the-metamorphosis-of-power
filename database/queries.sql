-- Média por região e indicador no período mais recente.
SELECT r.name AS regiao, i.name AS indicador, o.value, o.period
FROM observations o
JOIN regions r ON r.id = o.region_id
JOIN indicators i ON i.id = o.indicator_id
WHERE o.period = (SELECT MAX(period) FROM observations)
ORDER BY i.name, o.value DESC;

-- Evolução semestral de um indicador.
SELECT o.period, AVG(o.value)::numeric(10,2) AS media
FROM observations o JOIN indicators i ON i.id = o.indicator_id
WHERE i.slug = 'participacao'
GROUP BY o.period ORDER BY o.period;

-- Variação do último período contra o primeiro por região.
WITH ranked AS (
  SELECT region_id, value, period,
         FIRST_VALUE(value) OVER (PARTITION BY region_id ORDER BY period) AS inicial,
         ROW_NUMBER() OVER (PARTITION BY region_id ORDER BY period DESC) AS rn
  FROM observations o JOIN indicators i ON i.id = o.indicator_id
  WHERE i.slug = 'participacao'
)
SELECT r.name, (value - inicial)::numeric(10,2) AS variacao
FROM ranked JOIN regions r ON r.id = ranked.region_id WHERE rn = 1
ORDER BY variacao DESC;

