-- Bitacora acumulativa del observador, por estudiante y no por materia.
-- Ver docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md.
--
-- Tabla nueva a proposito: la vieja `observaciones` no se toca ni se borra.
-- Mientras esta se llena, la pantalla actual sigue funcionando y se puede
-- volver atras.
--
-- Diferencias deliberadas frente a `observaciones`, cada una con su motivo:
--   - Sin UNIQUE: es una bitacora, varias filas por alumno son lo normal.
--   - Sin asignacion_id: el observador ya no depende de la materia.
--   - Sin ON DELETE CASCADE: ninguna baja administrativa debe borrar
--     historial de un alumno. En `observaciones`, borrar una asignacion
--     borra sus observaciones.
--   - NOT NULL en las columnas de identidad: una clave foranea no restringe
--     NULL, y en `observaciones` se podian colar filas sin estudiante.
--   - CHECK en periodo: hoy el esquema acepta periodo = 99.

CREATE TABLE IF NOT EXISTS observador_anotaciones (
    id SERIAL,
    estudiante_id integer NOT NULL,
    profesor_id integer NOT NULL,
    periodo integer NOT NULL,
    positiva boolean NOT NULL,
    conductual text NOT NULL DEFAULT '',
    cognitivo text NOT NULL DEFAULT '',
    lenguaje text NOT NULL DEFAULT '',
    creada_en timestamptz NOT NULL DEFAULT now(),
    editada_en timestamptz,
    editada_por integer,
    CONSTRAINT observador_anotaciones_pkey PRIMARY KEY (id),
    CONSTRAINT observador_anotaciones_estudiante_id_fkey
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    CONSTRAINT observador_anotaciones_profesor_id_fkey
        FOREIGN KEY (profesor_id) REFERENCES profesor(id),
    CONSTRAINT observador_anotaciones_editada_por_fkey
        FOREIGN KEY (editada_por) REFERENCES profesor(id),
    CONSTRAINT observador_anotaciones_periodo_check
        CHECK (periodo BETWEEN 1 AND 4)
);

-- EL INDICE NO SE CREA AQUI. Va en los dos sitios que fija
-- docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md:
--   scripts/apply_tenant_indexes.py            -> colegios que ya existen
--   migrations/base/20260813_esquema_base_tenant.sql -> colegios futuros
--
-- Crearlo tambien aqui lo duplicaria: apply_tenant_indexes.py antepone el
-- nombre del schema, asi que buscaria `tenant_x_idx_...`, no encontraria el
-- `idx_...` que hubiera dejado esta migracion, y crearia un segundo indice
-- identico. Eso ya paso: tenant_2005 tiene hoy duplicados en `asistencia`
-- (asistencia_estudiante_id_fecha_idx junto a
-- tenant_2005_idx_asistencia_estudiante_fecha) y en `estudiantes`.
--
-- Por eso, tras aplicar esta migracion hay que ejecutar:
--   python scripts/apply_tenant_indexes.py
