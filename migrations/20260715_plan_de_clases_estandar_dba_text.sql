-- Permite textos largos en Estandar / Lineamientos curriculares y Desarrollo cognitivo.
-- Ambos campos estaban limitados a VARCHAR(255) en los tenants existentes.

ALTER TABLE plan_de_clases
    ALTER COLUMN estandar TYPE TEXT,
    ALTER COLUMN dba TYPE TEXT;
