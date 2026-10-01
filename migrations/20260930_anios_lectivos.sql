-- Año lectivo, migracion A (fundacion). Fase 1 de
-- docs/funcionalidades/ANIO_LECTIVO.md.
--
-- Crea la tabla de años lectivos, registra 2026 como el año activo y marca con
-- 2026 todo lo que ya existe. Es invisible: ningun endpoint actual lee las
-- columnas nuevas, y la respuesta de tipos de pago (el unico SELECT * sobre una
-- tabla tocada) arma su JSON solo con columnas conocidas.
--
-- No borra ni modifica ningun dato existente. Solo agrega una tabla, columnas,
-- indices y restricciones, y rellena las columnas nuevas. Lo unico que se quita
-- son dos reglas de unicidad que se reemplazan en el mismo paso por su version
-- con año (ver mas abajo).
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - El año va escrito como 2026, no calculado con la fecha del dia. Dice "todo
--     lo existente es de 2026" aunque la migracion se aplique en enero. La fase
--     0 lo confirmo con numeros de tenant_2005: el colegio empezo a usar el
--     sistema en julio de 2026 y no hay datos de un año anterior.
--
--   - Las columnas nuevas ADMITEN NULL a proposito. Entre aplicar esta
--     migracion y desplegar el codigo que escribe el año, el codigo viejo puede
--     crear filas sin año. La migracion B (anios_lectivos_obligatorio) vuelve a
--     rellenar esas y pone NOT NULL.
--
--   - El año cuelga del curso: en lo academico solo cambia `cursos`. Notas,
--     asistencia, boletines, horarios, planeador y plan de clases ya dependen de
--     un curso y quedan separados por año sin tocarlos. Ademas llevan año lo
--     que no cuelga de un curso: conceptos de pago (decision 17), matriculas,
--     pagos y anotaciones del observador.
--
--   - `estudiantes.curso_id` NO se toca. Sigue siendo el curso del año activo;
--     `matriculas` pasa a ser el historial.
--
--   - Idempotente, como 20260825_observaciones_claves_foraneas.sql: ADD COLUMN
--     IF NOT EXISTS, CREATE ... IF NOT EXISTS, rellenos solo donde falta y
--     restricciones dentro de DO con la comprobacion previa en pg_constraint
--     (no existe ADD CONSTRAINT IF NOT EXISTS). El runner ya impide repetirla;
--     esto cubre reejecutarla a mano tras un fallo.
--
--   - Los indices se crean aqui y no en scripts/apply_tenant_indexes.py: su
--     lista fija (INDEXES) no incluye estas columnas, asi que no hay duplicado.

-- ---------------------------------------------------------------------------
-- 0. Freno: matriculas debe estar vacia antes de rellenarla.
-- ---------------------------------------------------------------------------
-- La tabla existe desde el esquema original y ningun codigo de app/ la usa; la
-- fase 0 la midio vacia en tenant_2005. Si un tenant tuviera filas viejas, sin
-- año, se detiene con el recuento y no toca nada: decidir que hacer con ellas
-- es del usuario, no de esta migracion. En una reejecucion todas tienen año y
-- el freno no salta.

DO $$
DECLARE
    tiene_columna_anio BOOLEAN;
    matriculas_sin_anio INTEGER;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'matriculas'
          AND column_name = 'anio_lectivo_id'
    ) INTO tiene_columna_anio;

    IF tiene_columna_anio THEN
        EXECUTE 'SELECT COUNT(*) FROM matriculas WHERE anio_lectivo_id IS NULL'
            INTO matriculas_sin_anio;
    ELSE
        SELECT COUNT(*) INTO matriculas_sin_anio FROM matriculas;
    END IF;

    IF matriculas_sin_anio > 0 THEN
        RAISE EXCEPTION
            'matriculas tiene % fila(s) antiguas sin año lectivo; se requiere revision manual antes de crear los años lectivos',
            matriculas_sin_anio;
    END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 1. La tabla de años lectivos, con 2026 activo.
-- ---------------------------------------------------------------------------
-- preparacion: se arma el año siguiente. activo: el año en que se trabaja.
-- cerrado: solo consulta. reabierto: año pasado abierto a proposito por el
-- admin para corregir. `reabierto` se declara desde ya para no necesitar otra
-- migracion cuando se use (fase 6).

CREATE TABLE IF NOT EXISTS anios_lectivos (
    id SERIAL PRIMARY KEY,
    anio smallint NOT NULL,
    estado character varying(20) DEFAULT 'preparacion' NOT NULL,
    creado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    activado_en timestamp without time zone,
    cerrado_en timestamp without time zone,
    CONSTRAINT anios_lectivos_anio_key UNIQUE (anio),
    CONSTRAINT chk_anios_lectivos_anio CHECK (anio BETWEEN 2000 AND 2100),
    CONSTRAINT chk_anios_lectivos_estado
        CHECK (estado IN ('preparacion', 'activo', 'cerrado', 'reabierto'))
);

-- La base de datos misma impide dos años activos, o dos en preparacion.
CREATE UNIQUE INDEX IF NOT EXISTS idx_anios_lectivos_un_activo
ON anios_lectivos (estado) WHERE estado = 'activo';

CREATE UNIQUE INDEX IF NOT EXISTS idx_anios_lectivos_una_preparacion
ON anios_lectivos (estado) WHERE estado = 'preparacion';

INSERT INTO anios_lectivos (anio, estado, activado_en)
VALUES (2026, 'activo', CURRENT_TIMESTAMP)
ON CONFLICT (anio) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 2. Columnas nuevas, rellenas con 2026.
-- ---------------------------------------------------------------------------

ALTER TABLE cursos
    ADD COLUMN IF NOT EXISTS anio_lectivo_id integer REFERENCES anios_lectivos(id);
ALTER TABLE tipos_de_pagos
    ADD COLUMN IF NOT EXISTS anio_lectivo_id integer REFERENCES anios_lectivos(id);
ALTER TABLE matriculas
    ADD COLUMN IF NOT EXISTS anio_lectivo_id integer REFERENCES anios_lectivos(id);
ALTER TABLE pagos
    ADD COLUMN IF NOT EXISTS anio_lectivo_id integer REFERENCES anios_lectivos(id);
ALTER TABLE observador_anotaciones
    ADD COLUMN IF NOT EXISTS anio_lectivo_id integer REFERENCES anios_lectivos(id);

UPDATE cursos
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE anio = 2026)
WHERE anio_lectivo_id IS NULL;

UPDATE tipos_de_pagos
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE anio = 2026)
WHERE anio_lectivo_id IS NULL;

-- Todos los pagos, incluidos los de ventas y el de fecha mal digitada (año 8)
-- que la fase 0 encontro en tenant_2005: la regla es "todo pago tiene año".
UPDATE pagos
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE anio = 2026)
WHERE anio_lectivo_id IS NULL;

UPDATE observador_anotaciones
SET anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE anio = 2026)
WHERE anio_lectivo_id IS NULL;

-- ---------------------------------------------------------------------------
-- 3. Unicidad con año: cursos y conceptos pueden repetirse, uno por año.
-- ---------------------------------------------------------------------------
-- Se reemplazan, en la misma transaccion, las dos reglas que hoy impiden
-- repetir un nombre en todo el colegio. Ningun codigo usa sus nombres: los
-- duplicados se detectan antes de insertar (`_validar_curso_unico`,
-- `crear_tipo_pago`), asi que el cambio de nombre no rompe nada.

-- Misma expresion que idx_cursos_nombre_jornada_unico
-- (20260623_admin_unicos_academicos.sql), con el año delante.
DROP INDEX IF EXISTS idx_cursos_nombre_jornada_unico;
CREATE UNIQUE INDEX IF NOT EXISTS idx_cursos_anio_nombre_jornada_unico
ON cursos (
    anio_lectivo_id,
    (UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))),
    (LOWER(COALESCE(NULLIF(TRIM(jornada), ''), 'Mañana')))
)
WHERE NULLIF(TRIM(COALESCE(nombre, '')), '') IS NOT NULL;

ALTER TABLE tipos_de_pagos DROP CONSTRAINT IF EXISTS tipos_de_pagos_nombre_key;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'tipos_de_pagos_anio_nombre_key'
          AND conrelid = 'tipos_de_pagos'::regclass
    ) THEN
        ALTER TABLE tipos_de_pagos
            ADD CONSTRAINT tipos_de_pagos_anio_nombre_key UNIQUE (anio_lectivo_id, nombre);
    END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 4. Matriculas: un curso por estudiante y por año, y el curso de ese año.
-- ---------------------------------------------------------------------------
-- La clave foranea compuesta hace que la base de datos misma impida matricular
-- a alguien en 2027 con un curso de 2026. Para poder apuntar a
-- (id, anio_lectivo_id), `cursos` necesita esa pareja como unica.

CREATE UNIQUE INDEX IF NOT EXISTS idx_matriculas_estudiante_anio_unico
ON matriculas (estudiante_id, anio_lectivo_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'cursos_id_anio_lectivo_key'
          AND conrelid = 'cursos'::regclass
    ) THEN
        ALTER TABLE cursos
            ADD CONSTRAINT cursos_id_anio_lectivo_key UNIQUE (id, anio_lectivo_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'matriculas_curso_anio_lectivo_fkey'
          AND conrelid = 'matriculas'::regclass
    ) THEN
        ALTER TABLE matriculas
            ADD CONSTRAINT matriculas_curso_anio_lectivo_fkey
            FOREIGN KEY (curso_id, anio_lectivo_id)
            REFERENCES cursos (id, anio_lectivo_id);
    END IF;
END
$$;

-- Una matricula de 2026 por cada estudiante que hoy tiene curso, retirados
-- incluidos: su historial tambien es de 2026. El año sale del curso, no se
-- repite el 2026, para que coincida siempre con la clave foranea compuesta.
-- La columna vieja `matriculas.anio` queda como esta, sin uso.
INSERT INTO matriculas (estudiante_id, curso_id, anio_lectivo_id)
SELECT e.id, e.curso_id, c.anio_lectivo_id
FROM estudiantes e
JOIN cursos c ON c.id = e.curso_id
WHERE NOT EXISTS (
    SELECT 1 FROM matriculas m
    WHERE m.estudiante_id = e.id
      AND m.anio_lectivo_id = c.anio_lectivo_id
);

-- ---------------------------------------------------------------------------
-- 5. Indices para leer por año.
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_cursos_anio_lectivo
ON cursos (anio_lectivo_id);

CREATE INDEX IF NOT EXISTS idx_tipos_de_pagos_anio_lectivo
ON tipos_de_pagos (anio_lectivo_id);

-- Los pagos de un estudiante en un año: es la consulta de cobros de la fase 2.
CREATE INDEX IF NOT EXISTS idx_pagos_estudiante_anio_lectivo
ON pagos (estudiante_id, anio_lectivo_id);

CREATE INDEX IF NOT EXISTS idx_observador_anotaciones_estudiante_anio
ON observador_anotaciones (estudiante_id, anio_lectivo_id);

-- ---------------------------------------------------------------------------
-- 6. Freno final: no puede quedar una regla de unicidad sin año.
-- ---------------------------------------------------------------------------
-- Los DROP de la seccion 3 usan los nombres del esquema base. Si un tenant
-- viejo tuviera la regla con otro nombre, el DROP no la encontraria y seguiria
-- impidiendo crear "MENSUALIDAD" o "PRIMERO A" en 2027, sin avisar. Aqui se
-- detiene con el nombre de la regla y el runner revierte ese tenant entero.

DO $$
DECLARE
    reglas_sin_anio TEXT;
BEGIN
    SELECT string_agg(indice.relname, ', ')
    INTO reglas_sin_anio
    FROM pg_index i
    JOIN pg_class indice ON indice.oid = i.indexrelid
    JOIN pg_attribute columna_anio
      ON columna_anio.attrelid = i.indrelid
     AND columna_anio.attname = 'anio_lectivo_id'
    WHERE i.indrelid IN ('cursos'::regclass, 'tipos_de_pagos'::regclass)
      AND i.indisunique
      AND NOT i.indisprimary
      AND NOT (columna_anio.attnum = ANY (i.indkey));

    IF reglas_sin_anio IS NOT NULL THEN
        RAISE EXCEPTION
            'quedan reglas de unicidad sin año lectivo en cursos o tipos_de_pagos: %; se requiere revision manual',
            reglas_sin_anio;
    END IF;
END
$$;
