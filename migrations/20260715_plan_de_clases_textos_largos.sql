-- Permite textos largos en unidad y tema del plan de clases.
-- Desarrollo cognitivo (dba) y actividad en casa ya usan columnas TEXT.

ALTER TABLE plan_de_clases
    ALTER COLUMN unidad TYPE TEXT,
    ALTER COLUMN tema TYPE TEXT;