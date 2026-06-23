-- Normaliza nombres administrativos a mayusculas en cada tenant.
-- No modifica correos, documentos, jornadas ni estados.

UPDATE profesor
SET
    nombre = CASE
        WHEN nombre IS NULL THEN NULL
        ELSE UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))
    END,
    apellido = CASE
        WHEN apellido IS NULL THEN NULL
        ELSE UPPER(REGEXP_REPLACE(TRIM(apellido), '[[:space:]]+', ' ', 'g'))
    END;

UPDATE materias
SET nombre = CASE
    WHEN nombre IS NULL THEN NULL
    ELSE UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))
END;

UPDATE cursos
SET nombre = CASE
    WHEN nombre IS NULL THEN NULL
    ELSE UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))
END;
