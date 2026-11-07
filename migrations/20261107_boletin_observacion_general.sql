-- «Mi curso» del director de grupo, paso 3: la observacion general del
-- boletin, guardada. Ver docs/funcionalidades/MI_CURSO_DIRECTOR.md.
--
-- Hasta hoy la caja "Observacion general" del boletin impreso solo existia en
-- pantalla: lo que se escribia se perdia al cerrar. Esta tabla la guarda, una
-- por estudiante, año lectivo y periodo. La escribe el director de grupo del
-- curso (o el admin) desde Boletin Final, y la lee el boletin impreso.
--
-- Una tabla enteramente nueva. Ninguna tabla existente se modifica.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - UNIQUE (estudiante_id, anio_lectivo_id, periodo): una observacion por
--     estudiante y periodo de cada año. Guardar de nuevo la reemplaza (UPSERT).
--
--   - texto de 1 a 500 caracteres (decidido con el usuario el 2026-11-07: lo
--     que cabe en los tres renglones de la caja impresa). Vacio no se guarda:
--     borrar el texto borra la fila. El backend revisa lo mismo antes, con
--     mensajes en español.
--
--   - estudiante_id con ON DELETE CASCADE, igual que boletin_cabecera: es
--     parte del boletin del estudiante y se va con el.
--
--   - anio_lectivo_id sin cascada, como cursos, matriculas y pagos.
--
--   - Quien la guardo, en actualizado_por_rol ('profesor' o 'admin') y
--     actualizado_por_id, SIN clave foranea: el id es de profesor o de
--     usuarios segun el rol, y una sola columna no puede apuntar a las dos.
--
--   - Indice por (anio_lectivo_id, periodo, estudiante_id): «Mi curso» lee las
--     de un curso en un periodo del año activo.
--
--   - Reejecutable: IF NOT EXISTS. El runner ya impide repetirla; esto cubre
--     reejecutarla a mano tras un fallo.
--
-- Orden de publicacion: esta migracion se aplica ANTES del push del backend.
-- El codigo viejo no lee esta tabla, asi que aplicarla antes no cambia nada
-- para los colegios; el backend nuevo la lee en «Mi curso» y en el boletin del
-- admin.

CREATE TABLE IF NOT EXISTS boletin_observacion_general (
    id SERIAL PRIMARY KEY,
    estudiante_id integer NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    anio_lectivo_id integer NOT NULL REFERENCES anios_lectivos(id),
    periodo smallint NOT NULL,
    texto text NOT NULL,
    actualizado_en timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actualizado_por_rol character varying(20) NOT NULL,
    actualizado_por_id integer NOT NULL,
    CONSTRAINT uq_boletin_observacion_general
        UNIQUE (estudiante_id, anio_lectivo_id, periodo),
    CONSTRAINT chk_boletin_observacion_general_periodo
        CHECK (periodo BETWEEN 1 AND 4),
    CONSTRAINT chk_boletin_observacion_general_texto
        CHECK (char_length(btrim(texto)) BETWEEN 1 AND 500),
    CONSTRAINT chk_boletin_observacion_general_rol
        CHECK (actualizado_por_rol IN ('profesor', 'admin'))
);

CREATE INDEX IF NOT EXISTS idx_boletin_observacion_general_periodo
    ON boletin_observacion_general (anio_lectivo_id, periodo, estudiante_id);
