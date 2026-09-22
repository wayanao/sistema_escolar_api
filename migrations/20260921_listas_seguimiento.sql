-- Listas de Seguimiento por Curso. Registro libre del administrador: por curso
-- define columnas con el nombre que quiera ("Asistio a la cumbre", "Compro el
-- libro") y marca a cada alumno con un check mas una nota corta opcional.
-- Ver docs/funcionalidades/LISTAS_SEGUIMIENTO.md.
--
-- Tablas enteramente nuevas. Ningun endpoint actual las lee ni las escribe, asi
-- que esta migracion no puede romper nada existente: no toca notas_detalle,
-- asistencia, tipos_de_pagos ni ninguna tabla en uso. Si el codigo se
-- desplegara antes de aplicarla, solo fallarian los endpoints nuevos de
-- /listas-seguimiento con "relation does not exist".
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - curso_id directo, sin tabla puente: una columna pertenece a un solo curso
--     y no se comparte entre cursos. Tipos de pago si necesita
--     tipos_pagos_cursos porque alli un concepto si se aplica a varios.
--
--   - ON DELETE CASCADE en los tres sentidos: aqui el borrado es definitivo, no
--     baja logica. A diferencia de tipos_de_pagos no hay historial financiero
--     que preservar, y tipos_pagos_estudiantes ya borra en cascada junto al
--     estudiante.
--
--   - UNIQUE (columna_id, estudiante_id): una sola celda por alumno y columna.
--     Es lo que habilita el upsert (ON CONFLICT ... DO UPDATE) al guardar el
--     lote de marcas, igual que en tipos_pagos_estudiantes.
--
--   - Sin nombre explicito para la PK, la UNIQUE y las foraneas: se dejan los
--     que PostgreSQL genera solo, que son los mismos que ya tiene
--     tipos_pagos_estudiantes en el esquema base.
--
--   - El CHECK de longitud de la nota va dentro del CREATE TABLE y no en un
--     ALTER TABLE aparte (como estaba en el borrador del documento), para que
--     el archivo completo se pueda reejecutar sin error.
--
-- Los indices SI se crean aqui, al contrario de
-- 20260908_observador_anotaciones.sql, que los dejo para
-- scripts/apply_tenant_indexes.py porque crearlos en ambos sitios los duplica.
-- Ese script lleva una lista fija (INDEXES) que no incluye estas tablas, asi
-- que no hay duplicado posible y no hay que tocarlo.

CREATE TABLE IF NOT EXISTS listas_seguimiento_columnas (
    id SERIAL PRIMARY KEY,
    curso_id integer NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
    nombre character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS listas_seguimiento_marcas (
    id SERIAL PRIMARY KEY,
    columna_id integer NOT NULL
        REFERENCES listas_seguimiento_columnas(id) ON DELETE CASCADE,
    estudiante_id integer NOT NULL
        REFERENCES estudiantes(id) ON DELETE CASCADE,
    marcado boolean DEFAULT false NOT NULL,
    nota text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (columna_id, estudiante_id),
    CONSTRAINT chk_listas_seguimiento_marcas_nota_longitud
        CHECK (nota IS NULL OR char_length(nota) <= 240)
);

-- Nombre unico por curso ignorando mayusculas y espacios de sobra. Mismo patron
-- ya probado en idx_cursos_nombre_jornada_unico
-- (20260623_admin_unicos_academicos.sql), sin la clausula WHERE que lleva
-- aquella: alli el nombre admite NULL y aqui es NOT NULL.
CREATE UNIQUE INDEX IF NOT EXISTS idx_listas_seguimiento_columnas_nombre_unico
ON listas_seguimiento_columnas (
    curso_id,
    (UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g')))
);

-- Las columnas de un curso: es la primera consulta que hace la pantalla.
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_columnas_curso
ON listas_seguimiento_columnas (curso_id);

-- Las marcas de una columna, y el borrado en cascada sin recorrer la tabla.
-- Lo cubriria el indice de la UNIQUE por ser columna_id su primera columna; se
-- deja igual que en tipos_pagos_estudiantes, que tambien tiene los dos.
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_marcas_columna
ON listas_seguimiento_marcas (columna_id);

-- Las marcas de un estudiante, y el borrado en cascada al darlo de baja.
CREATE INDEX IF NOT EXISTS idx_listas_seguimiento_marcas_estudiante
ON listas_seguimiento_marcas (estudiante_id);
