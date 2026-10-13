-- Entrevista de admisión, paso E1. Ver
-- docs/funcionalidades/ENTREVISTA_ADMISION.md.
--
-- Crea la tabla de admisiones: una fila por aspirante nuevo y año, con sus
-- datos, su entrevista y el resultado. Solo un aspirante aprobado se podrá
-- matricular (paso E3); al hacerlo, estudiante_id lo enlaza al estudiante
-- creado y la admisión queda de solo consulta.
--
-- Es invisible: ningún código la usa todavía. No toca ninguna tabla ni dato
-- existente; en particular, no quita columnas de estudiantes (los datos de
-- estudios anteriores y la ocupación de los padres se copiarán allí al
-- matricular).
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - Los tamaños de texto son los de las columnas equivalentes de
--     estudiantes, para que la copia al matricular nunca se corte.
--
--   - La base misma exige la autorización de datos (Ley 1581 de 2012), el
--     motivo de un "no aprobado" y que solo un aprobado quede enlazado a un
--     estudiante, y a uno solo. La API lo validará también, con mensajes
--     claros; estas reglas son la red por si algo se escapa.
--
--   - El curso es del mismo año que la admisión: clave foránea compuesta
--     contra cursos_id_anio_lectivo_key, igual que matriculas.
--
--   - Nada se borra en cascada. Hoy no hay ninguna ruta que borre años,
--     cursos ni estudiantes.
--
--   - Un documento se repite una sola vez por año. Si llega sin documento
--     (NULL), no cuenta.
--
--   - No se piden datos que puedan discriminar (religión, estado civil de los
--     padres, etc.).
--
--   - Reejecutable: CREATE ... IF NOT EXISTS. El runner ya impide repetirla;
--     esto cubre reejecutarla a mano tras un fallo.

CREATE TABLE IF NOT EXISTS admisiones (
    id SERIAL PRIMARY KEY,
    anio_lectivo_id INTEGER NOT NULL,
    -- Aspirante
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    tipo_documento VARCHAR(50),
    documento_identidad VARCHAR(20),
    fecha_nacimiento DATE,
    curso_id INTEGER,
    acudiente_nombre VARCHAR(150),
    acudiente_parentesco VARCHAR(50),
    acudiente_telefono VARCHAR(50),
    autoriza_datos BOOLEAN NOT NULL,
    autoriza_nombre VARCHAR(150) NOT NULL,
    -- Entrevista
    fecha_entrevista DATE,
    entrevistador VARCHAR(150),
    asistentes VARCHAR(250),
    colegio_anterior VARCHAR(150),
    anio_cursado_anterior VARCHAR(50),
    pre_escolar_anterior VARCHAR(50),
    ebp_anterior VARCHAR(50),
    motivo_retiro_anterior TEXT,
    paz_salvo_anterior VARCHAR(10),
    ocupacion_padre VARCHAR(100),
    ocupacion_madre VARCHAR(100),
    vive_con VARCHAR(250),
    expectativas TEXT,
    observaciones TEXT,
    -- Resultado
    resultado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    motivo_resultado TEXT,
    decidido_en TIMESTAMPTZ,
    estudiante_id INTEGER,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT admisiones_anio_lectivo_fkey
        FOREIGN KEY (anio_lectivo_id) REFERENCES anios_lectivos (id),
    CONSTRAINT admisiones_curso_anio_lectivo_fkey
        FOREIGN KEY (curso_id, anio_lectivo_id) REFERENCES cursos (id, anio_lectivo_id),
    CONSTRAINT admisiones_estudiante_id_key UNIQUE (estudiante_id),
    CONSTRAINT admisiones_estudiante_fkey
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id),
    CONSTRAINT chk_admisiones_resultado
        CHECK (resultado IN ('pendiente', 'aprobado', 'no_aprobado')),
    CONSTRAINT chk_admisiones_autoriza CHECK (autoriza_datos),
    CONSTRAINT chk_admisiones_motivo_no_aprobado
        CHECK (resultado <> 'no_aprobado' OR NULLIF(TRIM(motivo_resultado), '') IS NOT NULL),
    CONSTRAINT chk_admisiones_matricula_aprobada
        CHECK (estudiante_id IS NULL OR resultado = 'aprobado')
);

CREATE INDEX IF NOT EXISTS idx_admisiones_anio
ON admisiones (anio_lectivo_id, resultado);

CREATE UNIQUE INDEX IF NOT EXISTS idx_admisiones_documento_por_anio
ON admisiones (anio_lectivo_id, documento_identidad)
WHERE documento_identidad IS NOT NULL;
