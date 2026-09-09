-- Deja sitio para las anotaciones heredadas de la tabla vieja `observaciones`.
-- Ver docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md, fase 4.
--
-- Migracion aparte: las dos anteriores ya estan aplicadas en produccion y no se
-- editan, el runner bloquea un archivo cuyo checksum cambie.
--
-- Las 68 filas viejas NO tienen dos cosas, y ninguna se puede inventar:
--
--   * FECHA. La tabla `observaciones` nunca guardo cuando se escribio cada
--     una: sus columnas son id, estudiante_id, asignacion_id, periodo y los
--     tres textos. Poner la fecha de la copia las haria parecer escritas hoy y
--     las mezclaria con las nuevas. `creada_en` NULL significa «no se sabe», y
--     el ORDER BY ... NULLS LAST de la lectura las manda al final, que es su
--     sitio por ser las mas antiguas.
--
--   * POSITIVA O NEGATIVA. El modelo viejo no distinguia. Decidido con el
--     usuario el 2026-09-08: **no se les inventa una marca**. Solo las
--     anotaciones nuevas la llevan, y ahi la sigue exigiendo el esquema de la
--     API, asi que en la practica ningun registro nuevo puede nacer sin ella.
--
-- Lo que si se recupera de la fila vieja, a traves de su `asignacion_id`: el
-- profesor que la escribio y la materia. No quedan anonimas.

ALTER TABLE observador_anotaciones
    ALTER COLUMN positiva DROP NOT NULL;

ALTER TABLE observador_anotaciones
    ALTER COLUMN creada_en DROP NOT NULL;

-- De que fila de `observaciones` salio esta anotacion. NULL en todo lo que se
-- escriba desde la aplicacion.
--
-- Es lo que hace la copia REPETIBLE SIN DUPLICAR, que es el riesgo que el
-- documento ya tenia anotado: el script inserta solo lo que no este aqui, y
-- aunque alguien lo ejecute dos veces, la restriccion lo impide. En PostgreSQL
-- un UNIQUE admite tantos NULL como haga falta, asi que no estorba a las
-- anotaciones normales.
--
-- Sirve ademas para reconocer una anotacion heredada sin adivinarlo por el
-- hueco de la fecha.
ALTER TABLE observador_anotaciones
    ADD COLUMN IF NOT EXISTS observacion_origen_id integer;

ALTER TABLE observador_anotaciones
    DROP CONSTRAINT IF EXISTS observador_anotaciones_observacion_origen_id_key;

ALTER TABLE observador_anotaciones
    ADD CONSTRAINT observador_anotaciones_observacion_origen_id_key
        UNIQUE (observacion_origen_id);
