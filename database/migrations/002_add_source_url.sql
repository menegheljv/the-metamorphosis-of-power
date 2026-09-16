-- v002: provenance can be attached when replacing synthetic data with a
-- documented public source in a future exercise.
ALTER TABLE observations ADD COLUMN IF NOT EXISTS source_url TEXT;

