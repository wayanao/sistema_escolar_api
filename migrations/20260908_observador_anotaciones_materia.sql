-- La anotacion guarda de que materia era, como ETIQUETA COPIADA.
-- Ver docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md.
--
-- Migracion aparte porque 20260908_observador_anotaciones.sql ya esta aplicada
-- en produccion y no se edita: el runner bloquea un archivo cuyo checksum
-- cambia.
--
-- Es texto copiado, NO una clave foranea a materias(id), y eso es deliberado:
--   - Un vinculo reintroduciria el defecto que esta tabla vino a corregir. Si
--     manana borran esa materia del horario, la anotacion perderia el dato o
--     arrastraria la fila. Una etiqueta sobrevive a todo.
--   - Leer la bitacora no necesita entonces ninguna union extra con materias.
--     A ~180 ms por ida y vuelta contra Neon, lo que se paga es el numero de
--     consultas, no su complejidad.
--
-- Se rellena AL ESCRIBIR (fase 3). Hasta entonces la columna queda vacia, que
-- es lo correcto: las anotaciones que no existen no tienen materia.
--
-- Tipo y longitud calcados de materias.nombre, character varying(100).

ALTER TABLE observador_anotaciones
    ADD COLUMN IF NOT EXISTS materia character varying(100) NOT NULL DEFAULT '';
