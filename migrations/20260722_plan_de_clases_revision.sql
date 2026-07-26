-- Ejecutar en cada schema tenant despues de
-- 20260722_plan_de_clases_integridad.sql.
-- Agrega seguimiento versionado sin alterar el contenido de los planes.

ALTER TABLE plan_de_clases
    ADD COLUMN IF NOT EXISTS estado_revision VARCHAR(24) DEFAULT 'pendiente',
    ADD COLUMN IF NOT EXISTS version_revision INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS enviado_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS admin_visto_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS admin_visto_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS revisado_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS revisado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;

UPDATE plan_de_clases
SET
    estado_revision = COALESCE(estado_revision, 'pendiente'),
    version_revision = COALESCE(version_revision, 1),
    enviado_at = COALESCE(enviado_at, updated_at, created_at, CURRENT_TIMESTAMP);

ALTER TABLE plan_de_clases
    ALTER COLUMN estado_revision SET DEFAULT 'pendiente',
    ALTER COLUMN estado_revision SET NOT NULL,
    ALTER COLUMN version_revision SET DEFAULT 1,
    ALTER COLUMN version_revision SET NOT NULL,
    ALTER COLUMN enviado_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN enviado_at SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_plan_de_clases_estado_revision'
          AND conrelid = 'plan_de_clases'::regclass
    ) THEN
        ALTER TABLE plan_de_clases
            ADD CONSTRAINT ck_plan_de_clases_estado_revision
            CHECK (estado_revision IN ('pendiente', 'visto', 'con_observaciones', 'revisado'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_plan_de_clases_version_revision'
          AND conrelid = 'plan_de_clases'::regclass
    ) THEN
        ALTER TABLE plan_de_clases
            ADD CONSTRAINT ck_plan_de_clases_version_revision
            CHECK (version_revision >= 1);
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS plan_de_clases_observaciones (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES plan_de_clases(id) ON DELETE CASCADE,
    admin_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    plan_version INTEGER NOT NULL,
    observacion TEXT NOT NULL,
    creada_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vista_por_profesor_at TIMESTAMPTZ,
    CONSTRAINT ck_plan_observacion_version CHECK (plan_version >= 1),
    CONSTRAINT ck_plan_observacion_texto CHECK (
        LENGTH(BTRIM(observacion)) BETWEEN 1 AND 3000
    )
);

CREATE INDEX IF NOT EXISTS idx_plan_de_clases_estado_revision
    ON plan_de_clases(estado_revision, enviado_at DESC);

CREATE INDEX IF NOT EXISTS idx_plan_observaciones_plan
    ON plan_de_clases_observaciones(plan_id, creada_at DESC);

CREATE INDEX IF NOT EXISTS idx_plan_observaciones_profesor_pendientes
    ON plan_de_clases_observaciones(plan_id, creada_at DESC)
    WHERE vista_por_profesor_at IS NULL;
