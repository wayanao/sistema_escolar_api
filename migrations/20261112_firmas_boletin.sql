-- Firmas guardadas para el boletin: la del rector(a) y la de cada profesor.
-- Ver docs/funcionalidades/FIRMAS_BOLETIN.md.
--
-- Hasta hoy el boletin impreso salia con dos rayas vacias, "Director(a)" y
-- "Director de Grupo", para firmar a mano hoja por hoja. Con estas tablas cada
-- firma se guarda una vez y el boletin del admin sale con ella encima de su
-- raya. La del rector(a) la sube el admin; la de cada profesor la pone el
-- mismo profesor desde «Mi curso» (decidido con el usuario el 2026-11-12).
--
-- Dos tablas enteramente nuevas. Ninguna tabla existente se modifica, y
-- mientras nadie guarde una firma los boletines salen igual que antes.
--
-- Van aparte, y no en columnas de institucion_branding ni de profesor, a
-- proposito: la identidad institucional la lee cualquier usuario en cada
-- impreso, y la ficha del profesor sale en otras pantallas. Una columna con la
-- imagen viajaria en esas lecturas, al alcance de quien no debe verla. Aparte,
-- la firma solo sale por las rutas que la protegen.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - firma_institucional tiene una sola fila (id = 1, con CHECK): el colegio
--     tiene una sola firma de rector(a). Guardar de nuevo la reemplaza.
--
--   - actualizado_por_id es el admin (tabla usuarios) que la subio, SIN clave
--     foranea, igual que boletin_observacion_general: borrar un usuario no
--     debe quedar bloqueado por esto. Sirve para saber quien la cambio.
--
--   - firmas_profesores: una por profesor, con profesor_id como clave.
--     ON DELETE CASCADE: la firma es de la persona; si un profesor llegara a
--     borrarse fisicamente, su firma se va con el. Darlo de baja (estado) no
--     borra nada.
--
--   - Imagen PNG de 1 a 102400 bytes (100 KB), el mismo limite de la firma del
--     acudiente: el servidor ya lo valida; el CHECK es la ultima defensa si
--     alguien escribe sin pasar por la API.
--
--   - Reejecutable: IF NOT EXISTS. El runner ya impide repetirla; esto cubre
--     reejecutarla a mano tras un fallo.
--
-- Orden de publicacion: esta migracion se aplica ANTES del push del backend.
-- El codigo viejo no lee estas tablas, asi que aplicarla antes no cambia nada
-- para los colegios. El backend nuevo las lee en el boletin del admin: si
-- llegara antes que ellas, el boletin del admin fallaria en todos los colegios.

CREATE TABLE IF NOT EXISTS firma_institucional (
    id smallint DEFAULT 1 NOT NULL,
    imagen_png bytea NOT NULL,
    actualizado_en timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actualizado_por_id integer NOT NULL,
    CONSTRAINT firma_institucional_pkey PRIMARY KEY (id),
    CONSTRAINT chk_firma_institucional_una_sola CHECK (id = 1),
    CONSTRAINT chk_firma_institucional_imagen
        CHECK (octet_length(imagen_png) BETWEEN 1 AND 102400)
);

CREATE TABLE IF NOT EXISTS firmas_profesores (
    profesor_id integer NOT NULL,
    imagen_png bytea NOT NULL,
    actualizado_en timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT firmas_profesores_pkey PRIMARY KEY (profesor_id),
    CONSTRAINT firmas_profesores_profesor_id_fkey
        FOREIGN KEY (profesor_id) REFERENCES profesor(id) ON DELETE CASCADE,
    CONSTRAINT chk_firmas_profesores_imagen
        CHECK (octet_length(imagen_png) BETWEEN 1 AND 102400)
);
