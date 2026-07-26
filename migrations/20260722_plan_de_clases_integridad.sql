-- Ejecutar en cada schema tenant antes de habilitar el flujo de revision.
-- La migracion es deliberadamente no destructiva: si detecta registros
-- incompletos o duplicados, se detiene para permitir una revision manual.

DO $$
DECLARE
    registros_invalidos INTEGER;
    grupos_duplicados INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO registros_invalidos
    FROM plan_de_clases
    WHERE asignacion_id IS NULL OR fecha IS NULL;

    IF registros_invalidos > 0 THEN
        RAISE EXCEPTION
            'plan_de_clases contiene % registro(s) sin asignacion_id o fecha; se requiere revision manual',
            registros_invalidos;
    END IF;

    SELECT COUNT(*)
    INTO grupos_duplicados
    FROM (
        SELECT asignacion_id, fecha
        FROM plan_de_clases
        GROUP BY asignacion_id, fecha
        HAVING COUNT(*) > 1
    ) duplicados;

    IF grupos_duplicados > 0 THEN
        RAISE EXCEPTION
            'plan_de_clases contiene % grupo(s) duplicado(s) por asignacion y fecha; se requiere revision manual',
            grupos_duplicados;
    END IF;
END
$$;

ALTER TABLE plan_de_clases
    ALTER COLUMN asignacion_id SET NOT NULL,
    ALTER COLUMN fecha SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_de_clases_asignacion_fecha
    ON plan_de_clases(asignacion_id, fecha);

DROP INDEX IF EXISTS idx_plan_de_clases_asignacion_fecha;
