-- Blindaje de duplicados en administracion academica por tenant.
-- Requiere auditoria previa limpia antes de aplicar.

UPDATE profesor
SET
    documento_identidad = TRIM(documento_identidad),
    email = LOWER(TRIM(email))
WHERE documento_identidad IS NOT NULL
   OR email IS NOT NULL;

UPDATE cursos
SET jornada = COALESCE(NULLIF(TRIM(jornada), ''), 'Mañana');

CREATE UNIQUE INDEX IF NOT EXISTS idx_profesor_documento_unico
ON profesor ((TRIM(documento_identidad)))
WHERE NULLIF(TRIM(COALESCE(documento_identidad, '')), '') IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_profesor_email_unico
ON profesor ((LOWER(TRIM(email))))
WHERE NULLIF(TRIM(COALESCE(email, '')), '') IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_materias_nombre_unico
ON materias ((UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))))
WHERE NULLIF(TRIM(COALESCE(nombre, '')), '') IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_cursos_nombre_jornada_unico
ON cursos (
    (UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))),
    (LOWER(COALESCE(NULLIF(TRIM(jornada), ''), 'Mañana')))
)
WHERE NULLIF(TRIM(COALESCE(nombre, '')), '') IS NOT NULL;
