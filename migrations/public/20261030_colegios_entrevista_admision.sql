-- Entrevista de admisión solo en los colegios que la usan (2026-10-30).
-- Ver docs/funcionalidades/ENTREVISTA_ADMISION.md, "Solo en los colegios que
-- la usan".
--
-- Un colegio nuevo empieza sin entrevista: sus estudiantes nuevos del año en
-- preparación entran con "Crear estudiante". Los dos colegios que ya existen
-- la usan hoy y la conservan, así que para ellos no cambia nada.
--
-- Hay que aplicarla ANTES de publicar el backend que la lee: sin la columna,
-- las escrituras de Admisiones y `GET /tenant/status` fallarían.

ALTER TABLE public.colegios
    ADD COLUMN IF NOT EXISTS usa_entrevista_admision BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE public.colegios
SET usa_entrevista_admision = TRUE
WHERE esquema_db IN ('tenant_2005', 'tenant_colegio_1');
