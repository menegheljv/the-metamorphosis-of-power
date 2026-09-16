INSERT INTO regions (name, code) VALUES
  ('Aurora', 'AU'), ('Brisa', 'BR'), ('Cerrado', 'CE'), ('Dourado', 'DO'), ('Estrela', 'ES')
ON CONFLICT (code) DO NOTHING;

INSERT INTO indicators (slug, name, unit, description) VALUES
  ('participacao', 'Participação cívica', '%', 'Índice sintético de participação em consultas locais'),
  ('acesso_digital', 'Acesso digital', '%', 'Domicílios com acesso regular à internet'),
  ('transparencia', 'Transparência', 'pontos', 'Pontuação didática de transparência ativa (0–100)')
ON CONFLICT (slug) DO NOTHING;

-- Deterministic sample observations (not real election or government claims).
INSERT INTO observations (region_id, indicator_id, period, value)
SELECT r.id, i.id, x.period::date, x.value
FROM (VALUES
  ('AU','participacao','2024-01-01',62.0), ('AU','participacao','2024-07-01',68.0),
  ('BR','participacao','2024-01-01',55.0), ('BR','participacao','2024-07-01',59.0),
  ('CE','participacao','2024-01-01',71.0), ('CE','participacao','2024-07-01',73.0),
  ('DO','participacao','2024-01-01',48.0), ('DO','participacao','2024-07-01',54.0),
  ('ES','participacao','2024-01-01',64.0), ('ES','participacao','2024-07-01',69.0),
  ('AU','acesso_digital','2024-01-01',76.0), ('AU','acesso_digital','2024-07-01',79.0),
  ('BR','acesso_digital','2024-01-01',68.0), ('BR','acesso_digital','2024-07-01',72.0),
  ('CE','acesso_digital','2024-01-01',81.0), ('CE','acesso_digital','2024-07-01',84.0),
  ('DO','acesso_digital','2024-01-01',61.0), ('DO','acesso_digital','2024-07-01',66.0),
  ('ES','acesso_digital','2024-01-01',73.0), ('ES','acesso_digital','2024-07-01',78.0),
  ('AU','transparencia','2024-01-01',74.0), ('AU','transparencia','2024-07-01',77.0),
  ('BR','transparencia','2024-01-01',63.0), ('BR','transparencia','2024-07-01',68.0),
  ('CE','transparencia','2024-01-01',82.0), ('CE','transparencia','2024-07-01',85.0),
  ('DO','transparencia','2024-01-01',58.0), ('DO','transparencia','2024-07-01',64.0),
  ('ES','transparencia','2024-01-01',70.0), ('ES','transparencia','2024-07-01',75.0)
) AS x(code, slug, period, value)
JOIN regions r ON r.code = x.code
JOIN indicators i ON i.slug = x.slug
ON CONFLICT (region_id, indicator_id, period) DO NOTHING;
