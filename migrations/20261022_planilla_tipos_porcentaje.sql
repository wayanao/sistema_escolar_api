-- Porcentajes por tipo de nota, paso B2b. Ver docs/funcionalidades/SUBNOTAS_PLANILLA.md
-- (parte B, propuestas PB1 a PB3).
--
-- Cada tipo de nota de la planilla (una columna, como "Cognitivo") puede tener
-- un porcentaje. Cuando todos los tipos de una clase y un periodo tienen el
-- suyo y suman 100, la nota del periodo es el promedio ponderado; si no, el
-- promedio simple de siempre. Ese calculo vive en app/core/nota_periodo.py.
--
-- Una tabla enteramente nueva. Ninguna tabla existente se modifica.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - asignacion_id con ON DELETE CASCADE, igual que notas_detalle y las
--     subnotas: si se borra la asignacion se van sus porcentajes. Siempre
--     guarda la asignacion academica ya resuelta.
--
--   - periodo en la tabla: los tipos de nota son de un periodo (cada periodo
--     tiene sus columnas), asi que su porcentaje tambien.
--
--   - tipo_nota es el mismo texto que notas_detalle.descripcion, sin clave
--     foranea: los tipos de nota no tienen tabla propia. Se compara con
--     LOWER(TRIM(...)), igual que la planilla y las subnotas.
--
--   - porcentaje entero de 1 a 100 (PB2). Un tipo sin porcentaje no tiene
--     fila: quitarlo es borrarla. Que la suma de la clase no pase de 100 no
--     puede ser un CHECK, porque mira varias filas; lo cuida el controlador
--     con la clase bloqueada, para que dos guardados a la vez no lo salten.
--
--   - Sin nombre explicito para la PK y la foranea: se dejan los que
--     PostgreSQL genera solo, como en las subnotas.
--
--   - Reejecutable: CREATE ... IF NOT EXISTS, con los CHECK dentro del
--     CREATE TABLE. El runner ya impide repetirla; esto cubre reejecutarla a
--     mano tras un fallo.
--
-- Indice: solo el unico. Empieza por (asignacion_id, periodo), asi que tambien
-- sirve para leer los porcentajes de una planilla, y es el que nombra el
-- ON CONFLICT del guardado.
--
-- scripts/apply_tenant_indexes.py no se toca: su lista fija no incluye esta
-- tabla, asi que el indice va aqui sin riesgo de duplicarse.
--
-- Orden de publicacion: esta migracion se aplica ANTES del push del backend.
-- El backend nuevo usa esta tabla al borrar un tipo de nota; si saliera
-- primero, esa ruta fallaria a todos los profesores.

CREATE TABLE IF NOT EXISTS planilla_tipos_porcentaje (
    id SERIAL PRIMARY KEY,
    asignacion_id integer NOT NULL REFERENCES asignaciones(id) ON DELETE CASCADE,
    periodo integer NOT NULL,
    tipo_nota character varying(100) NOT NULL,
    porcentaje smallint NOT NULL,
    actualizado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_planilla_tipos_porcentaje_tipo_nota_no_vacio
        CHECK (char_length(TRIM(tipo_nota)) > 0),
    CONSTRAINT chk_planilla_tipos_porcentaje_rango
        CHECK (porcentaje >= 1 AND porcentaje <= 100)
);

-- Un porcentaje por tipo de nota, sin distinguir mayusculas ni espacios en los
-- extremos. Es tambien el indice que usa el ON CONFLICT del guardado.
CREATE UNIQUE INDEX IF NOT EXISTS idx_planilla_tipos_porcentaje_tipo_unico
ON planilla_tipos_porcentaje (
    asignacion_id,
    periodo,
    (LOWER(TRIM(tipo_nota)))
);
