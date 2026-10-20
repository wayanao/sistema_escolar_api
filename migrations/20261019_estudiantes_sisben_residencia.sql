-- SISBÉN y lugar de residencia, paso S1. Ver
-- docs/funcionalidades/SISBEN_RESIDENCIA.md.
--
-- Agrega a estudiantes ocho datos opcionales de la ficha:
--
--   - sisben: si la familia tiene SISBÉN. NULL es "sin dato", TRUE "sí" y
--     FALSE "no".
--   - sisben_grupo y sisben_subgrupo: la clasificación del SISBÉN IV (grupo A,
--     B, C o D; subgrupo como B4).
--   - sisben_nivel: el nivel del SISBÉN III (1, 2 o 3), para quien solo tenga
--     ese certificado.
--   - barrio, municipio, zona_residencia (urbana o rural) y punto_referencia:
--     dónde vive, por partes. La columna de la dirección no cambia: sigue
--     siendo la calle o carrera y el número, y lo ya escrito ahí no se toca.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - Todas opcionales, sin valor por defecto: los estudiantes que ya existen
--     quedan "sin dato", sin rellenar nada, y la tabla no se reescribe.
--
--   - Reglas en la base como defensa, por si algo salta la API: los valores
--     permitidos de grupo, nivel y zona; el subgrupo exige el grupo y empieza
--     por su letra; sin SISBÉN no hay grupo, subgrupo ni nivel. El rango exacto
--     de cada subgrupo (A1 a A5, B1 a B7, C1 a C18, D1 a D21) lo valida la API,
--     con un mensaje claro; aquí basta el formato.
--
--   - Sin índices: nadie busca ni filtra por estos datos todavía.
--
--   - Reejecutable: ADD COLUMN IF NOT EXISTS y cada regla solo si falta. El
--     runner ya impide repetirla; esto cubre reejecutarla a mano tras un fallo.

ALTER TABLE estudiantes
    ADD COLUMN IF NOT EXISTS sisben BOOLEAN,
    ADD COLUMN IF NOT EXISTS sisben_grupo VARCHAR(1),
    ADD COLUMN IF NOT EXISTS sisben_subgrupo VARCHAR(3),
    ADD COLUMN IF NOT EXISTS sisben_nivel SMALLINT,
    ADD COLUMN IF NOT EXISTS barrio VARCHAR(150),
    ADD COLUMN IF NOT EXISTS municipio VARCHAR(100),
    ADD COLUMN IF NOT EXISTS zona_residencia VARCHAR(10),
    ADD COLUMN IF NOT EXISTS punto_referencia VARCHAR(255);

-- PostgreSQL no ofrece ADD CONSTRAINT IF NOT EXISTS (mismo patrón que
-- 20261014_admisiones_cuestionario.sql).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_estudiantes_sisben_grupo'
          AND conrelid = 'estudiantes'::regclass
    ) THEN
        ALTER TABLE estudiantes
            ADD CONSTRAINT chk_estudiantes_sisben_grupo
            CHECK (sisben_grupo IN ('A', 'B', 'C', 'D'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_estudiantes_sisben_subgrupo'
          AND conrelid = 'estudiantes'::regclass
    ) THEN
        ALTER TABLE estudiantes
            ADD CONSTRAINT chk_estudiantes_sisben_subgrupo
            CHECK (sisben_subgrupo IS NULL OR (sisben_grupo IS NOT NULL
                AND left(sisben_subgrupo, 1) = sisben_grupo
                AND sisben_subgrupo ~ '^[A-D][1-9][0-9]?$'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_estudiantes_sisben_nivel'
          AND conrelid = 'estudiantes'::regclass
    ) THEN
        ALTER TABLE estudiantes
            ADD CONSTRAINT chk_estudiantes_sisben_nivel
            CHECK (sisben_nivel BETWEEN 1 AND 3);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_estudiantes_sisben_clasificacion'
          AND conrelid = 'estudiantes'::regclass
    ) THEN
        ALTER TABLE estudiantes
            ADD CONSTRAINT chk_estudiantes_sisben_clasificacion
            CHECK (sisben IS TRUE OR (sisben_grupo IS NULL
                AND sisben_subgrupo IS NULL AND sisben_nivel IS NULL));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_estudiantes_zona_residencia'
          AND conrelid = 'estudiantes'::regclass
    ) THEN
        ALTER TABLE estudiantes
            ADD CONSTRAINT chk_estudiantes_zona_residencia
            CHECK (zona_residencia IN ('urbana', 'rural'));
    END IF;
END
$$;
