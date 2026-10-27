-- Firma del acudiente en el observador: una fila por anotacion firmada.
-- Ver docs/funcionalidades/FIRMA_OBSERVADOR.md.
--
-- Solo anade una tabla: no cambia ninguna existente. Mientras nadie firme,
-- la bitacora se lee y se escribe exactamente igual que antes.
--
-- Va aparte, y no en columnas de `observador_anotaciones`, para que la imagen
-- no viaje en cada lectura de la bitacora.
--
-- Decisiones deliberadas, cada una con su motivo:
--   - UNIQUE en anotacion_id: como maximo una firma por anotacion
--     (decision 2). Ese UNIQUE crea su propio indice, que es el que usan la
--     bitacora y la impresion para unir; no hace falta otro, y por eso esta
--     migracion no toca scripts/apply_tenant_indexes.py.
--   - Sin ON DELETE CASCADE: nadie borra anotaciones ni firmas.
--   - Sin estudiante_id: sale de la anotacion, que nunca cambia de
--     estudiante.
--   - Dos columnas para quien toma la firma: profesores y admins viven en
--     tablas distintas, y asi cada una conserva su clave foranea. El CHECK
--     exige exactamente una.
--   - firmada_en sin DEFAULT: la pone el servidor en la misma transaccion en
--     que calcula la huella, que la incluye. Un DEFAULT dejaria escribir una
--     firma con una hora que la huella no cubre.
--   - Imagen de 1 a 102400 bytes (100 KB): el servidor ya lo valida; el CHECK
--     es la ultima defensa si alguien escribe sin pasar por la API.

CREATE TABLE IF NOT EXISTS observador_firmas (
    id SERIAL,
    anotacion_id integer NOT NULL,
    firmante_nombre character varying(150) NOT NULL,
    firmante_tipo_documento character varying(50) NOT NULL,
    firmante_documento character varying(50) NOT NULL,
    firmante_parentesco character varying(50) NOT NULL,
    imagen_png bytea NOT NULL,
    tomada_por_profesor_id integer,
    tomada_por_usuario_id integer,
    tomada_por_nombre character varying(150) NOT NULL,
    firmada_en timestamptz NOT NULL,
    huella character(64) NOT NULL,
    CONSTRAINT observador_firmas_pkey PRIMARY KEY (id),
    CONSTRAINT observador_firmas_anotacion_id_key UNIQUE (anotacion_id),
    CONSTRAINT observador_firmas_anotacion_id_fkey
        FOREIGN KEY (anotacion_id) REFERENCES observador_anotaciones(id),
    CONSTRAINT observador_firmas_tomada_por_profesor_id_fkey
        FOREIGN KEY (tomada_por_profesor_id) REFERENCES profesor(id),
    CONSTRAINT observador_firmas_tomada_por_usuario_id_fkey
        FOREIGN KEY (tomada_por_usuario_id) REFERENCES usuarios(id),
    CONSTRAINT observador_firmas_tomada_por_check
        CHECK ((tomada_por_profesor_id IS NULL) <> (tomada_por_usuario_id IS NULL)),
    CONSTRAINT observador_firmas_imagen_check
        CHECK (octet_length(imagen_png) BETWEEN 1 AND 102400)
);
