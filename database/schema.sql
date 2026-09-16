-- Schema for a deliberately synthetic public-data observatory.
CREATE TABLE IF NOT EXISTS regions (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  code CHAR(2) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS indicators (
  id SERIAL PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  unit TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS observations (
  id BIGSERIAL PRIMARY KEY,
  region_id INTEGER NOT NULL REFERENCES regions(id),
  indicator_id INTEGER NOT NULL REFERENCES indicators(id),
  period DATE NOT NULL,
  value NUMERIC(12,2) NOT NULL CHECK (value >= 0),
  source_note TEXT NOT NULL DEFAULT 'Dado sintético para demonstração',
  UNIQUE (region_id, indicator_id, period)
);

CREATE INDEX IF NOT EXISTS observations_period_idx ON observations(period);
CREATE INDEX IF NOT EXISTS observations_indicator_region_idx ON observations(indicator_id, region_id);

