-- Agrega el codigo DANE a la identidad institucional de cada tenant.
-- Se guarda como texto para conservar ceros a la izquierda.

ALTER TABLE institucion_branding
ADD COLUMN IF NOT EXISTS codigo_dane VARCHAR(20) DEFAULT '';

UPDATE institucion_branding
SET codigo_dane = ''
WHERE codigo_dane IS NULL;
