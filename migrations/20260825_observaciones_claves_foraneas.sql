-- Repone las dos claves foraneas ausentes de `observaciones`.
--
-- Hallazgo 1 de la 7.0 de `observaciones`, auditado y confirmado el 2026-08-25:
-- `estudiante_id` y `asignacion_id` son `integer` sueltos y la tabla es **la
-- unica del esquema** con esas dos columnas y sin claves foraneas hacia ellas.
-- Las otras dieciseis tablas si las tienen.
--
-- Las definiciones copian **exactamente** las de `asistencia` y `notas_detalle`,
-- que son las gemelas estructurales de esta tabla —mismo trio
-- estudiante/asignacion/periodo— y que ya usan esta misma convencion:
--   asignacion_id -> asignaciones(id) ON DELETE CASCADE
--   estudiante_id -> estudiantes(id)  sin accion de borrado
--
-- La migracion es deliberadamente **no destructiva**, como
-- `20260722_plan_de_clases_integridad.sql`: si encuentra filas huerfanas se
-- detiene con el recuento y **no borra ni modifica ninguna**. Repararlas es una
-- decision del usuario, no de esta migracion.
--
-- No cambia la nulabilidad de las columnas. Una clave foranea **no restringe
-- NULL**, asi que una fila con `estudiante_id` nulo seguira siendo valida,
-- igual que hoy lo es en `asistencia`. Anadir `NOT NULL` seria otro cambio y
-- exige su propia decision.

DO $$
DECLARE
    estudiantes_huerfanos INTEGER;
    asignaciones_huerfanas INTEGER;
BEGIN
    -- Solo cuentan las filas con valor: una columna nula no viola una clave
    -- foranea y no debe impedir crearla.
    SELECT COUNT(*)
    INTO estudiantes_huerfanos
    FROM observaciones o
    WHERE o.estudiante_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM estudiantes e WHERE e.id = o.estudiante_id);

    SELECT COUNT(*)
    INTO asignaciones_huerfanas
    FROM observaciones o
    WHERE o.asignacion_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM asignaciones a WHERE a.id = o.asignacion_id);

    IF estudiantes_huerfanos > 0 OR asignaciones_huerfanas > 0 THEN
        RAISE EXCEPTION
            'observaciones tiene % fila(s) con estudiante_id inexistente y % con asignacion_id inexistente; se requiere revision manual antes de reponer las claves foraneas',
            estudiantes_huerfanos, asignaciones_huerfanas;
    END IF;
END
$$;

-- Idempotente: no existe `ADD CONSTRAINT IF NOT EXISTS`, asi que se comprueba
-- antes. Permite reejecutar la migracion sobre un tenant que ya la tenga.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'observaciones_estudiante_id_fkey'
          AND conrelid = 'observaciones'::regclass
    ) THEN
        ALTER TABLE observaciones
            ADD CONSTRAINT observaciones_estudiante_id_fkey
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'observaciones_asignacion_id_fkey'
          AND conrelid = 'observaciones'::regclass
    ) THEN
        ALTER TABLE observaciones
            ADD CONSTRAINT observaciones_asignacion_id_fkey
            FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE;
    END IF;
END
$$;
