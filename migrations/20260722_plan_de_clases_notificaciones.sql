-- Ejecutar en cada schema tenant despues de
-- 20260722_plan_de_clases_revision.sql.
-- Los planes historicos no generan eventos: solo los guardados posteriores.

CREATE TABLE IF NOT EXISTS plan_de_clases_notificaciones_admin (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES plan_de_clases(id) ON DELETE CASCADE,
    plan_version INTEGER NOT NULL,
    creada_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    leida_at TIMESTAMPTZ,
    CONSTRAINT ck_plan_notificacion_admin_version CHECK (plan_version >= 1),
    CONSTRAINT uq_plan_notificacion_admin_version UNIQUE (plan_id, plan_version)
);

CREATE INDEX IF NOT EXISTS idx_plan_notificaciones_admin_pendientes
    ON plan_de_clases_notificaciones_admin(creada_at DESC)
    WHERE leida_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_plan_notificaciones_admin_plan
    ON plan_de_clases_notificaciones_admin(plan_id, plan_version DESC);
