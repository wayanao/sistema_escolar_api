-- Subnotas de la planilla, paso A1. Ver docs/funcionalidades/SUBNOTAS_PLANILLA.md.
--
-- Cada tipo de nota de la planilla (una columna, como "Cognitivo") puede tener
-- subnotas ("Taller 1", "Quiz"), las mismas para todo el curso. El promedio de
-- las subnotas de un estudiante es su celda, que se sigue guardando en
-- notas_detalle como siempre. Las subnotas van en tablas propias a proposito:
-- el boletin, el reporte parcial, los tableros y la ficha promedian TODAS las
-- filas de notas_detalle, y meterlas alli cambiaria esas cifras.
--
-- Dos tablas enteramente nuevas. Ninguna tabla existente se modifica.
--
-- Decisiones que se ven en el SQL, cada una con su motivo:
--
--   - asignacion_id con ON DELETE CASCADE, igual que notas_detalle: si se borra
--     la asignacion se van sus notas y tambien sus subnotas. Siempre guarda la
--     asignacion academica ya resuelta, la misma que usa notas_detalle.
--
--   - tipo_nota es el mismo texto que notas_detalle.descripcion, sin clave
--     foranea: los tipos de nota no tienen tabla propia, existen porque hay
--     filas en notas_detalle con ese nombre. Se compara con LOWER(TRIM(...)),
--     igual que la planilla.
--
--   - Las calificaciones borran en cascada con su subnota (borrar "Taller 2"
--     borra lo calificado en ella), pero NO con el estudiante, igual que
--     notas_detalle: un estudiante con notas no desaparece sin aviso. Los
--     estudiantes no se borran en esta aplicacion; cambian de estado.
--
--   - Una calificacion es una nota (primaria) o una carita (preescolar), nunca
--     las dos ni ninguna: una subnota vacia no se guarda, se borra su fila.
--     La nota va de 1 a 5 con dos decimales, igual que notas_detalle.nota. Que
--     el codigo de la carita exista en la escala lo valida la API.
--
--   - Sin nombre explicito para la PK, la UNIQUE y las foraneas: se dejan los
--     que PostgreSQL genera solo, como en listas_seguimiento.
--
--   - Reejecutable: CREATE ... IF NOT EXISTS, con los CHECK dentro de cada
--     CREATE TABLE. El runner ya impide repetirla; esto cubre reejecutarla a
--     mano tras un fallo.
--
-- Indices: solo dos, y cada uno lo usa una consulta concreta.
--
--   - El unico de planilla_subnotas empieza por (asignacion_id, periodo), asi
--     que tambien sirve para leer las subnotas de una planilla: no hace falta
--     otro indice para eso.
--   - La UNIQUE (subnota_id, estudiante_id) de las calificaciones sirve para
--     el guardado (ON CONFLICT), para leer las de un estudiante y para el
--     borrado en cascada. No se crea uno por estudiante_id: ninguna consulta
--     filtra solo por estudiante.
--
-- scripts/apply_tenant_indexes.py no se toca: su lista fija no incluye estas
-- tablas, asi que los indices van aqui sin riesgo de duplicarse.
--
-- Orden de publicacion: esta migracion se aplica ANTES del push del backend.
-- El backend nuevo usa estas tablas al guardar una nota a mano y al borrar un
-- tipo de nota; si saliera primero, esas dos rutas fallarian.

CREATE TABLE IF NOT EXISTS planilla_subnotas (
    id SERIAL PRIMARY KEY,
    asignacion_id integer NOT NULL REFERENCES asignaciones(id) ON DELETE CASCADE,
    periodo integer NOT NULL,
    tipo_nota character varying(100) NOT NULL,
    nombre character varying(60) NOT NULL,
    creada_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_planilla_subnotas_nombre_no_vacio
        CHECK (char_length(TRIM(nombre)) > 0),
    CONSTRAINT chk_planilla_subnotas_tipo_nota_no_vacio
        CHECK (char_length(TRIM(tipo_nota)) > 0)
);

CREATE TABLE IF NOT EXISTS planilla_subnotas_valores (
    id SERIAL PRIMARY KEY,
    subnota_id integer NOT NULL
        REFERENCES planilla_subnotas(id) ON DELETE CASCADE,
    estudiante_id integer NOT NULL REFERENCES estudiantes(id),
    nota numeric(3,2),
    valoracion character varying(30),
    actualizada_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (subnota_id, estudiante_id),
    CONSTRAINT chk_planilla_subnotas_valores_nota_rango
        CHECK (nota IS NULL OR (nota >= 1 AND nota <= 5)),
    CONSTRAINT chk_planilla_subnotas_valores_un_solo_valor
        CHECK ((nota IS NULL) <> (valoracion IS NULL))
);

-- Un nombre por tipo de nota, sin distinguir mayusculas ni espacios en los
-- extremos. Es la garantia real contra nombres repetidos aunque lleguen dos
-- peticiones a la vez; el controlador da antes el 409 legible del caso normal.
CREATE UNIQUE INDEX IF NOT EXISTS idx_planilla_subnotas_nombre_unico
ON planilla_subnotas (
    asignacion_id,
    periodo,
    (LOWER(TRIM(tipo_nota))),
    (LOWER(TRIM(nombre)))
);
