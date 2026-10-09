-- Año lectivo, fase 6.1: decisiones de salida y materias ocultas al cerrar.
--
-- estado_salida queda en NULL mientras el estudiante no tenga una matricula
-- en el año siguiente ni una decision explicita. "retirado" significa que no
-- continua; "egresado", que termino el ultimo grado. La fase 6.2 usara esta
-- diferencia para mostrar los pendientes y la fase 6.3 para cambiar el estado
-- global del estudiante al activar el año nuevo.
--
-- La tabla de materias ocultas es la fotografia minima del cierre: guarda las
-- materias que estaban inactivas en ese momento. No duplica nombres ni datos de
-- la materia. Asi un boletin historico puede ocultar exactamente las mismas
-- materias aunque su estado cambie en años posteriores.
--
-- No se rellenan ni cambian datos existentes. Todas las matriculas actuales
-- quedan con estado_salida NULL hasta que el administrador tome una decision.

ALTER TABLE matriculas
    ADD COLUMN IF NOT EXISTS estado_salida VARCHAR(20);

-- PostgreSQL no ofrece ADD CONSTRAINT IF NOT EXISTS. La comprobacion permite
-- repetir con seguridad una ejecucion manual que hubiera quedado incompleta.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_matriculas_estado_salida'
          AND conrelid = 'matriculas'::regclass
    ) THEN
        ALTER TABLE matriculas
            ADD CONSTRAINT chk_matriculas_estado_salida
            CHECK (estado_salida IN ('retirado', 'egresado'));
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS anios_lectivos_materias_ocultas (
    anio_lectivo_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    CONSTRAINT anios_lectivos_materias_ocultas_pkey
        PRIMARY KEY (anio_lectivo_id, materia_id),
    CONSTRAINT anios_lectivos_materias_ocultas_anio_fkey
        FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos (id),
    CONSTRAINT anios_lectivos_materias_ocultas_materia_fkey
        FOREIGN KEY (materia_id) REFERENCES materias (id)
);

CREATE INDEX IF NOT EXISTS idx_anios_lectivos_materias_ocultas_materia
ON anios_lectivos_materias_ocultas (materia_id);
