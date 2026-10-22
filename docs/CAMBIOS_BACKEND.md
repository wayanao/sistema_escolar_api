# Cambios Backend

Ultima revision documental: 2026-10-22.

## Proposito

Bitacora de cambios documentales y tecnicos observables del backend.

## 2026-10-22 - Porcentajes por tipo de nota, pasos B2a, B2b y B2c

Primeros pasos con código de la parte B de
`docs/funcionalidades/SUBNOTAS_PLANILLA.md`. **Ninguna nota cambia todavía en
la práctica**: solo cambia en clases con porcentajes completos, y ninguna los
tiene (la tabla ni siquiera está aplicada y la pantalla para ponerlos llega
en B4). El reporte parcial, el boletín del admin y los rankings se conectan
en B2d. Nada de esto está publicado.

### B2c: la definitiva del boletín (PB5)

- Con porcentajes activos, `POST /boletines/guardar` guarda la definitiva que
  calcula el servidor, no la que manda la pantalla, y `GET
  /boletines/referencia/...` la agrega a cada estudiante con notas. Sin
  porcentajes activos, todo igual (lo fija el paso B1).
- Coste: una consulta más en cada una sin porcentajes; dos con porcentajes
  incompletos; tres con porcentajes activos. Ninguna conexión de más.

### Qué cambia

- `app/core/nota_periodo.py` (B2a): cuándo están activos los porcentajes
  (todos los tipos con el suyo y suma de 100), la suma y la nota ponderada en
  primaria y preescolar, con redondeo mitad hacia arriba. Nadie lo usa para
  calcular notas todavía.
- Migración `20261022_planilla_tipos_porcentaje.sql` (B2b): tabla nueva
  `planilla_tipos_porcentaje`. **Escrita, sin aplicar**; se prueba en una rama
  de Neon en B3.
- Ruta nueva `PUT /planilla/tipos/porcentaje` (`app/routes/porcentajes_planilla.py`):
  guarda, cambia o quita (`null`) el porcentaje de un tipo, con la clase
  bloqueada para que la suma no pase de 100.
- `GET /planilla-excel/...?con_porcentajes=true` agrega `porcentajes` y
  `porcentajes_activos`. Sin el parámetro, la respuesta y las consultas son
  las de siempre.
- `DELETE /planilla/tipo` quita también el porcentaje del tipo.
- Contrato en `docs/API_ENDPOINTS.md`, sección "Planilla".

### Lo que cuesta (medido con pruebas)

| Ruta | Antes (admin / profesor) | Después |
|---|---|---|
| `GET /planilla-excel` sin parámetro | 2 / 3 consultas | igual |
| `GET /planilla-excel?con_porcentajes=true` | — | 3 / 4 |
| `DELETE /planilla/tipo` | 4 / 5 | 5 / 6 |
| `PUT /planilla/tipos/porcentaje` | — | 6 / 7 |

Ninguna crece con el número de estudiantes ni de tipos. Ninguna abre una
conexión de más.

### Publicación

**El backend no se sube hasta que la migración esté en producción** (paso B3
y el orden de publicación de la parte B): si saliera antes, `DELETE
/planilla/tipo` fallaría para todos los profesores.

## 2026-10-21 - Subnotas de la planilla, paso A1

Primer paso con código de `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, parte
A (subnotas). La parte B (porcentajes por tipo de nota) no ha empezado.

### Qué cambia

- Migración `20261021_planilla_subnotas.sql`: dos tablas nuevas,
  `planilla_subnotas` y `planilla_subnotas_valores`. Probada en una rama de
  Neon y con el esquema base regenerado (paso A2). **Aplicada en producción
  y publicada el 2026-10-21** (commit `e36f976`, Render Live).
- Cuatro rutas nuevas en `app/routes/subnotas_planilla.py`: crear, renombrar
  y borrar una subnota, y guardar las calificaciones de un estudiante en un
  tipo de nota. El servidor calcula la celda (promedio, dos decimales mitad
  hacia arriba; en preescolar, la carita más cercana) y la guarda en
  `notas_detalle` en la misma transacción.
- `GET /planilla-excel/...?con_subnotas=true` agrega las subnotas. Sin el
  parámetro, la respuesta y las consultas son las de siempre.
- `POST /planilla/nota` responde `409` si la celda tiene subnotas calificadas,
  y `DELETE /planilla/tipo` borra también las subnotas del tipo.
- `app/core/valoraciones_desarrollo.py`: la escala de caritas, copia de la del
  frontend con prueba gemela. `app/core/subnotas_planilla.py`: el cálculo.
- Contrato en `docs/API_ENDPOINTS.md`, sección "Planilla".

### Lo que cuesta (medido con pruebas)

| Ruta | Antes (admin / profesor) | Después |
|---|---|---|
| `GET /planilla-excel` sin parámetro | 2 / 3 consultas | igual |
| `GET /planilla-excel?con_subnotas=true` | — | 3 / 4 |
| `POST /planilla/nota` | 6 / 7 | 7 / 8 |
| `DELETE /planilla/tipo` | 3 / 4 | 4 / 5 |

Las conexiones no cambian en ninguna (1 el admin, 2 el profesor). Las rutas
nuevas usan **una sola conexión**, también para el profesor, porque su
permiso se comprueba con el cursor ya abierto. Su número de consultas no
crece con los estudiantes del curso.

### Por qué así

- Las subnotas no van en `notas_detalle`: el boletín, el reporte parcial, los
  tableros y la ficha promedian todas sus filas y cambiarían sin aviso.
- El servidor calcula la celda: si la calculara la pantalla, un navegador
  cerrado a mitad podría dejar la celda distinta de sus subnotas.
- La migración se aplica antes del push (ver `docs/MIGRACIONES.md`).

## 2026-10-19 - SISBÉN y lugar de residencia, paso S1

Primer paso con código de `docs/funcionalidades/SISBEN_RESIDENCIA.md`.

### Qué cambia

- Migración `20261019_estudiantes_sisben_residencia.sql`: ocho columnas
  opcionales en `estudiantes` (SISBÉN con grupo, subgrupo y nivel; barrio,
  municipio, zona y punto de referencia) y cinco reglas `CHECK`. No rellena
  ni cambia datos. **Sin aplicar todavía** en ninguna base.
- `EstudianteCreate` acepta los ocho campos, con un validador que explica en
  español por qué rechaza un subgrupo o una clasificación sin SISBÉN.
- `estudiantes_repository.guardar_sisben_y_residencia` y
  `estudiante_controller.guardar_sisben_y_residencia_si_llegaron`: los ocho
  datos se guardan aparte, en la misma transacción, solo si el cuerpo trae
  alguno. La tupla de 34 datos de `insertar_estudiante` y
  `actualizar_estudiante` no cambia. Se usa al crear, al editar y al
  matricular desde una admisión (aspirante nuevo y exalumno).
- Contrato en `docs/API_ENDPOINTS.md`, sección "Estudiantes".

### Por qué así

- Mientras el frontend viejo siga publicado, ninguna petición manda los campos
  nuevos y ninguna toca las columnas nuevas: se puede subir este código antes
  de aplicar la migración en producción.
- Una pestaña abierta antes del cambio no borra los datos nuevos.

## 2026-10-14 - Entrevista de admisión E10: las preguntas del anexo en la API

Segundo paso con código de la ampliación "Preguntas del anexo" de
`docs/funcionalidades/ENTREVISTA_ADMISION.md`. Usa la columna del E9.

### Qué cambia

- `app/core/cuestionario_admision.py` (nuevo): la lista de 13 secciones y 55
  preguntas, con su tipo, opciones, detalle, "Otro", rangos y límites, y
  `limpiar_cuestionario`, que revisa y limpia el bloque de respuestas.
- `GET /admisiones/cuestionario` (nueva, solo admin): la lista, para que el
  frontend arme el formulario. Declarada antes de `/admisiones/{admision_id}`.
- `GET /estudiantes/{estudiante_id}/admision` (nueva, solo admin, en el
  router de admisiones): las respuestas de la admisión de un estudiante;
  vacío si no tiene.
- `GET /admisiones/{id}` y las respuestas de `POST` y `PUT` traen
  `cuestionario`. `PUT /admisiones/{id}` lo acepta: si no llega o llega
  `null`, queda como estaba (excepción a propósito al reemplazo completo); si
  llega, se revisa (`422` con mensaje) y reemplaza el bloque.
- No cambia: la lista de admisiones, registrar, el resultado, borrar ni
  matricular (el bloque no se copia a `estudiantes`). Contrato en
  `docs/API_ENDPOINTS.md`, "Preguntas del anexo (paso E10)". Sin migración.

### Pruebas

98 nuevas, escritas antes (fallaron todas): `tests/test_cuestionario_admision.py`
(nuevo: la lista del documento y cada regla de revisión) y ampliaciones de
`test_admisiones_esquema.py`, `test_admisiones_controller.py` y
`test_admisiones_routes.py`. Ajustadas a propósito: las que fijan los campos
de `AdmisionUpdate` y las rutas del router (un campo y dos rutas más).
`scripts/verify.py`: 2533 pasan, 0 fallan; Ruff y `pip check` limpios.

## 2026-10-14 - Entrevista de admisión E9: columna para las preguntas del anexo

Primer paso con código de la ampliación "Preguntas del anexo" de
`docs/funcionalidades/ENTREVISTA_ADMISION.md` (diseño en el E8).

### Qué cambia

- Migración nueva `migrations/20261014_admisiones_cuestionario.sql`:
  `admisiones.cuestionario JSONB NOT NULL DEFAULT '{}'::jsonb`, con la regla
  `chk_admisiones_cuestionario_objeto` (siempre un objeto JSON). Las
  admisiones existentes quedan con el bloque vacío. Detalle en
  `docs/MIGRACIONES.md`.
- No cambia ninguna ruta ni respuesta. Ningún código usa la columna todavía
  (paso E10).
- Esquema base regenerado desde la rama de Neon `prueba-cuestionario`: 36
  tablas. Los colegios nuevos nacerán con la columna.
- Commits `9547721` (migración) y `3728dcb` (esquema base), subidos juntos.
  El usuario la aplicó en producción el mismo día.

### Pruebas

`tests/test_migracion_admisiones_cuestionario.py`, 6 pruebas sobre el texto
del SQL, escritas antes (fallaron las 6). En la rama de Neon, una consulta
intentó 8 altas buenas y malas, deshechas al instante: las 8 dieron lo
esperado. `scripts/verify.py`: 2435 pasan, 0 fallan; Ruff y `pip check`
limpios.

## 2026-10-14 - Entrevista de admisión E7: cerrar el alta directa en preparación

Último paso de `docs/funcionalidades/ENTREVISTA_ADMISION.md`. Según el
usuario, E1 a E6 ya estaban en producción (el frontend dejó de usar esta ruta
en el E5).

### Qué cambia

- `POST /anios-lectivos/{id}/estudiantes` (alta directa del paso 5.5 del año
  lectivo): con el año en preparación responde `409` "Un estudiante nuevo en
  2027 se matricula desde su entrevista aprobada (Admisiones)." y no escribe
  nada. Con un año que no está en preparación, el `409` de siempre. La ruta
  se conserva para que una pestaña vieja reciba un mensaje claro.
- Lo que creaba ficha y matrícula sigue en
  `_crear_estudiante_en_preparacion`, que usa la matrícula desde una
  admisión. `POST /estudiantes` (año activo) no cambia.
- Sin migración.

### Pruebas

`tests/test_anio_lectivo_matriculacion_preparacion.py`: la prueba del alta
directa se reescribió a propósito como prueba de
`_crear_estudiante_en_preparacion`; 3 nuevas (cerrada sin escribir, mensaje de
siempre fuera de preparación, `409` en la ruta), de las que fallaban antes
las dos que dependían del cambio. `scripts/verify.py`: 2429 pasan, 0
fallan; Ruff y `pip check` limpios.

## 2026-10-13 - Entrevista de admisión E3: resultado y matricular desde la admisión

Tercer paso con código de `docs/funcionalidades/ENTREVISTA_ADMISION.md`. El
usuario decidió que un exalumno que vuelve usa su mismo registro (decisión
11).

### Qué cambia

- `PUT /admisiones/{id}/resultado`: aprobado, no aprobado (exige motivo) o
  de vuelta a pendiente; guarda `decidido_en`.
- `POST /admisiones/{id}/matricular` (`201`): con la ficha del estudiante
  (cuerpo de `POST /estudiantes`), solo un aprobado y una vez. En una
  transacción crea la ficha y la matrícula del año en preparación (o usa la
  del exalumno), copia lo que pasó a la entrevista sin borrar lo que ya
  había y enlaza la admisión. El estudiante queda `activo`. Contrato en
  `docs/API_ENDPOINTS.md`, "Admisiones".
- `anios_lectivos_controller`: lo que crea ficha y matrícula en el alta
  directa (paso 5.5) pasó a `_crear_estudiante_en_preparacion`, sin cambiar
  su comportamiento; la nueva `matricular_aspirante_en_preparacion` lo
  reutiliza. `anios_lectivos_repository.leer_estudiante_para_reingreso`
  busca al exalumno con sus matrículas de los dos años, bloqueado.
- No cambia ninguna ruta ni respuesta existente. Sin migración.

### Pruebas

52 nuevas, escritas antes: `tests/test_admisiones_matricular.py` (nuevo) y
ampliaciones de `test_admisiones_esquema.py`, `test_admisiones_controller.py`
y `test_admisiones_routes.py`. Las 19 del alta directa
(`test_anio_lectivo_matriculacion_preparacion.py`) siguen pasando sin
cambios. `scripts/verify.py`: 2426 pasan, 0 fallan; Ruff y `pip check`
limpios.

## 2026-10-13 - Entrevista de admisión E2: registrar, ver, editar y borrar aspirantes

Segundo paso con código de `docs/funcionalidades/ENTREVISTA_ADMISION.md`.

### Qué cambia

- Router nuevo `app/routes/admisiones.py`, **solo admin** a nivel de router:
  `GET` y `POST /anios-lectivos/{id}/admisiones`, y `GET`, `PUT` y `DELETE
  /admisiones/{id}`. Contrato en `docs/API_ENDPOINTS.md`, "Admisiones".
- Se consulta cualquier año; registrar, editar y borrar solo con el año en
  `preparacion` (`409`). Una admisión matriculada es de solo consulta. El
  curso debe ser un curso activo del mismo año y el documento no se repite
  entre los aspirantes de un año (`409`, también si dos altas llegan a la
  vez). Si el documento ya es de un estudiante, la respuesta trae
  `aviso_documento`, sin impedir el registro.
- Capas: `app/schemas/admision.py`, `app/repositories/admisiones_repository.py`
  y `app/controllers/admisiones_controller.py`. El resultado y la matrícula
  son del paso E3.
- No cambia ninguna ruta ni respuesta existente. Sin migración.

### Pruebas

`tests/test_admisiones_esquema.py`, `tests/test_admisiones_controller.py` y
`tests/test_admisiones_routes.py`, 80 pruebas escritas antes (los tres
archivos fallaron al importar). Ajustadas a propósito: las cinco guardias que
enumeran todos los repositorios reconocen `admisiones_repository` (la de
asistencia, también su total: de 19 a 20). `scripts/verify.py`: 2374 pasan,
0 fallan; Ruff y `pip check` limpios.

## 2026-10-13 - Entrevista de admisión E1: tabla de admisiones

Primer paso con código de `docs/funcionalidades/ENTREVISTA_ADMISION.md`. El
usuario confirmó el reparto de campos entre la ficha del estudiante y la
entrevista, las decisiones 7 a 9 y que quien entrevista se escribe a mano.

### Qué cambia

- Migración nueva `migrations/20261013_admisiones.sql`: tabla `admisiones`
  (aspirante, entrevista y resultado en una fila por año), con las reglas de
  autorización de datos, resultado, motivo de "no aprobado", enlace único a
  un estudiante aprobado y curso del mismo año, y dos índices. Detalle en
  `docs/MIGRACIONES.md`.
- Esquema base regenerado desde la rama de Neon `prueba-entrevista`: 36
  tablas. Los colegios nuevos nacerán con la tabla.
- No cambia ninguna tabla, ruta ni respuesta existente. Ningún código la usa
  todavía. Commit `4db1f15`; con Render en **Live**, el usuario la aplicó en
  producción el mismo día.

### Pruebas

`tests/test_migracion_admisiones.py`, 15 pruebas sobre el texto del SQL,
escritas antes (fallaron las 15). Una de ellas compara los tamaños de los
datos que se copiarán al matricular con los de `estudiantes` en el esquema
base. En la rama de Neon, una consulta intentó 15 altas buenas y malas,
deshechas al instante: las 15 dieron lo esperado. `scripts/verify.py`: 2294
pasan, 0 fallan; Ruff y `pip check` limpios.

## 2026-10-12 - Año lectivo: valores de pago de un estudiante en un año

Pedido del usuario: en la sección de matricular del frontend, ver lo que se le
cobrará a cada estudiante en el año siguiente y personalizarlo. Ver
`docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Ruta nueva, solo de lectura y solo admin:
  `GET /estudiantes/{estudiante_id}/valores-pago?anio_lectivo_id=`. Devuelve
  cada concepto que se le cobra en ese año con `precio_curso`,
  `valor_personalizado`, `motivo` y `valor_a_pagar`. Contrato en
  `docs/API_ENDPOINTS.md`, "Tipos de pagos".
- Hacía falta porque `GET /estudiantes/{id}/deudas` solo trae conceptos con
  deuda: en noviembre de 2026 la mensualidad de 2027 no debe nada y no sale
  (comprobado con `calcular_deuda_concepto`).
- `app/services/cobros.py`: `obtener_valores_pago_estudiante`, que usa la
  misma regla de precios de los cobros (`_valor_unitario_concepto`), y
  `obtener_motivos_personalizados_estudiante`, que solo corre si el
  estudiante tiene algún valor personalizado.
- No cambia ningún cálculo, ninguna ruta existente ni ninguna escritura.
  Guardar y quitar valores siguen por `PUT` y `DELETE` de
  `valores-pago-personalizados`. Sin migración, sin acceso a una base real.

### Pruebas

`tests/test_anio_lectivo_valores_pago.py`, 14 pruebas, escritas antes del
código (fallaron las 14). Comprueban los conceptos que salen y los que no
(opcional, inactivo, sin precio en el curso), el precio base cuando el curso lo
tiene en `0`, una beca completa en `0`, que coincide con el cálculo de deudas,
el año activo sin parámetro, el error sin matrícula, que la conexión siempre se
cierra y la ruta (solo admin, año opcional, `404`). Ajustada a propósito:
`test_pagos_escrituras_caracterizacion.py` fija las rutas del dominio, de 19 a
20. `scripts/verify.py`: 2279 pruebas, Ruff y `pip check` limpios.

## 2026-10-10 - Año lectivo 7.2: usar un plan de clases del año pasado

Segundo paso de la fase 7 de `docs/funcionalidades/ANIO_LECTIVO.md`
(decisiones 15 y 16). Con él queda completo el backend de la fase 7.

### Qué cambia

- Rutas nuevas, solo de lectura: `GET /plan-de-clases/{asignacion_id}/anio-anterior`
  (la lista de planes del año pasado de esa clase: id, fecha, periodo, unidad y
  tema) y `GET /plan-de-clases/{asignacion_id}/anio-anterior/{plan_id}` (el
  texto de uno, sin fecha, evidencias ni periodo). Contrato en
  `docs/API_ENDPOINTS.md`, "Plan de clases".
- El origen es el mismo del paso 7.1 (`CLASES_DE_ORIGEN_SQL`): la misma
  materia en el curso del que se copió el de la clase, de cualquier profesor.
- Un plan que no es del origen de la clase recibe `403`. Las dos rutas pasan
  por la guardia del año de la clase.
- No se crea nada: el plan nuevo se guarda por `POST /plan-de-clases`, que no
  cambió. Sin migración, sin acceso a una base real.

### Pruebas

`tests/test_anio_lectivo_planes_anterior.py`, 22 pruebas, escritas antes del
código, con las consultas corriendo en SQLite. Catorce versiones dañadas del
código hacen fallar alguna. Se ampliaron, a propósito, las cuatro pruebas de
`test_plan_de_clases_caracterizacion.py` que fijan el inventario del módulo
(rutas, consultas, conexiones y total de líneas). `scripts/verify.py` pasó con
2265 pruebas, Ruff y `pip check` limpios, usando una base ficticia.

## 2026-10-10 - Año lectivo 7.1: traer el planeador del año pasado

Primer paso de la fase 7 de `docs/funcionalidades/ANIO_LECTIVO.md`
(decisiones 14 y 15).

### Qué cambia

- Rutas nuevas `GET` y `POST /planeador-anual/{asignacion_id}/anio-anterior`.
  El `GET` dice si se puede traer el planeador del año pasado
  (`puede_traer`, decidido aquí); el `POST` lo copia, sin fechas, y nunca
  sobrescribe: con cualquier fila ya escrita responde `409`. Contrato en
  `docs/API_ENDPOINTS.md`, "Planeador anual".
- El origen sale de la clase de este año: la misma materia en el curso del que
  se copió su curso (`cursos.curso_origen_id`), de cualquier profesor. La regla
  vive en `CLASES_DE_ORIGEN_SQL` (`anios_lectivos_repository.py`), para que
  los planes de clase del paso 7.2 usen la misma.
- Decisión del usuario del 2026-10-10: si la materia cambió de profesor a
  mitad de año, cada periodo se trae del último que escribió algo en él.
- Nuevo `puede_guardar_en_anio` en `app/services/anio_lectivo.py`: la regla de
  la guardia sin lanzar, para que el botón y el guardado no se contradigan.
- Las rutas del planeador de siempre no cambian. Sin migración, sin acceso a
  una base real.

### Pruebas

`tests/test_anio_lectivo_planeador_anterior.py`, 32 pruebas, escritas antes del
código. Sus consultas corren de verdad en SQLite (viene con Python), además de
leerse como texto. Veintiuna versiones dañadas del código hacen fallar alguna.
Se ampliaron, a propósito, las cuatro pruebas de
`test_planeador_anual_caracterizacion.py` que fijan el inventario exacto del
módulo. `scripts/verify.py` pasó con 2243 pruebas, Ruff y `pip check` limpios,
usando una base ficticia.

## 2026-10-09 - Año lectivo 6.5: la marca de salida en los candidatos

Primer paso de la fase 6 del frontend (`docs/funcionalidades/ANIO_LECTIVO.md`),
que necesita un cambio pequeño aquí.

### Qué cambia

- `GET /anios-lectivos/{anio_lectivo_id}/matriculas/candidatos` agrega a cada
  candidato `estado_salida` (`"retirado"`, `"egresado"` o `null`). El usuario
  decidió marcar la salida en la pantalla de promoción, y esa pantalla
  necesita saber quién ya está marcado. Los demás campos no cambian.
- Sin migración, sin acceso a una base real.

### Pruebas

La prueba del 6.2b que exigía la respuesta sin cambios se reemplazó por una
que exige el campo nuevo; falló antes del cambio. `scripts/verify.py` pasó con
2211 pruebas, Ruff y `pip check` limpios, usando una base ficticia.

## 2026-10-09 - Año lectivo 6.4b: listas de seguimiento por matrícula

Segunda parte del paso 6.4 de la fase 6 de
`docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- `leer_estudiantes_del_curso` (`listas_seguimiento_repository.py`) toma a los
  alumnos de su matrícula en el curso, no de `estudiantes.curso_id`. La usan
  la lista de un curso y la validación de sus marcas.
- Efecto: la lista de un curso de 2026 ya no sale vacía después de activar
  2027, y el admin puede marcarla si reabre el año. En un curso del año activo
  la lista es la misma, porque la consulta de control garantiza que la copia
  coincide con la matrícula. Misma cantidad de consultas.
- Sin migración, sin frontend, sin acceso a una base real.

### Pruebas

Se reemplazó la prueba que fijaba `FROM estudiantes ... WHERE curso_id` por
una que exige la matrícula; las 2 fallaron antes del cambio. Se actualizó el
guion de la base falsa de `test_anio_lectivo_guardia.py` y
`test_anio_lectivo_guardia_conteos.py`, que reconocía la consulta por su
comienzo. `scripts/verify.py` pasó con 2211 pruebas, Ruff y `pip check`
limpios, usando una base ficticia.

## 2026-10-09 - Año lectivo 6.4a: reabrir y volver a cerrar

Primera parte del paso 6.4 de la fase 6 de
`docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Nuevos `POST /anios-lectivos/{anio_lectivo_id}/reabrir` y `/cerrar`, solo
  para admin, con `{"confirmar_anio": 2026}`. Pasan un año de `cerrado` a
  `reabierto` y de vuelta. Solo un año reabierto a la vez.
- Solo cambia el estado del año: ni estudiantes, ni cursos, ni la foto de
  materias, ni las fechas de activación y cierre.
- El esquema de la confirmación se llama ahora `ConfirmacionAnioLectivo`;
  `ActivarAnioLectivo` lo hereda sin cambios. El error del año mal escrito se
  renombró a `ConfirmacionAnioInvalidaError`; la respuesta de activar no
  cambió.
- Ninguna ruta existente cambió de comportamiento. Sin migración, sin
  frontend, sin acceso a una base real.

### Pruebas

30 pruebas nuevas en `tests/test_anio_lectivo_reabrir.py`, que fallaron al
cargar porque las rutas no existían; las de activación se actualizaron solo en
el nombre del error. `scripts/verify.py` pasó con 2210 pruebas, Ruff y
`pip check` limpios, usando una base ficticia.

## 2026-10-08 - Año lectivo 6.3b: boletín de un año cerrado

Segunda parte del paso 6.3 de la fase 6 de
`docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- El boletín y el reporte parcial de admin, al mirar un año `cerrado` o
  `reabierto`, ocultan las materias de su foto al cerrarse
  (`anios_lectivos_materias_ocultas`) en vez de las inactivas de hoy
  (decisión 13). En el año activo y en el de preparación nada cambia.
- Sin `anio_lectivo_id`, o con el del año activo, las dos consultas son
  idénticas a las de antes, texto y parámetros (comparado contra el commit
  anterior).
- Hoy no hay ningún año cerrado, así que ninguna respuesta cambia.
- Sin migración, sin frontend, sin acceso a una base real.

### Pruebas

6 pruebas nuevas en `tests/test_anio_lectivo_boletin_materias_ocultas.py`; las
4 que describen el cambio fallaron primero y las 2 que protegen el texto de
hoy pasaban antes y después. Se ajustaron 2 pruebas existentes que fijaban el
texto y los parámetros: `test_boletin_caracterizacion.py` (el filtro llega
ahora por un hueco, y sin año sigue siendo exactamente el de hoy) y
`test_anio_lectivo_lecturas.py` (con año, las dos consultas repiten el año al
final). `scripts/verify.py` pasó con 2180 pruebas, Ruff y `pip check` limpios,
usando una base ficticia.

## 2026-10-08 - Año lectivo 6.3a: activar el año siguiente

Primera parte del paso 6.3 de la fase 6 de
`docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Nuevo `POST /anios-lectivos/{anio_lectivo_id}/activar`, solo para admin,
  con `{"confirmar_anio": 2027}`. En una sola transacción cierra el año activo,
  activa el siguiente, aplica las marcas de salida, guarda las materias
  inactivas como ocultas del año que cierra y copia a cada estudiante el curso
  del año nuevo. Si queda alguien sin decidir, responde `409` con la lista.
- `sincronizar_curso_vigente` comparte ahora su consulta con
  `sincronizar_curso_vigente_de_todos`; sigue siendo el único lugar que escribe
  `estudiantes.curso_id`. Su comportamiento para un estudiante no cambió.
- Ninguna ruta existente cambió. Subirlo no activa nada: la ruta solo actúa
  sobre un año en preparación y ningún botón del frontend la llama todavía.
- Sin migración nueva, sin cambio de frontend, sin acceso a una base real.

### Pruebas

Las 27 pruebas nuevas fallaron primero porque la activación no existía.
Antes del cambio pasaban 645 pruebas de año lectivo y estudiantes; después
pasan 672. `scripts/verify.py` pasó con 2174 pruebas, Ruff y `pip check`
limpios, usando una base ficticia.

## 2026-10-08 - Año lectivo 6.2b: marcar quién no sigue

Segunda parte del paso 6.2 de la fase 6 de
`docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Nuevo `PUT /anios-lectivos/{anio_lectivo_id}/matriculas/salida`, solo para
  admin. Guarda `retirado` o `egresado`, o quita la marca con `null`, en la
  matrícula del año activo de los estudiantes indicados. Todo o nada.
- Rechaza con `409` a quien no tiene matrícula en el año activo y, al marcar,
  a quien ya tiene matrícula en el siguiente año.
- La promoción del paso 5.5 rechaza con `409` a quien tenga una marca de
  salida. Su respuesta y la de candidatos no cambian. Hoy ninguna matrícula
  tiene marca, así que nada de lo que existe cambia de comportamiento.
- No cambia `estudiantes.curso_id` ni el estado de ningún estudiante: eso
  ocurrirá al activar (paso 6.3).
- No hay migración nueva (usa la columna del 6.1, ya en producción), cambio de
  frontend, acceso a una base real ni creación de 2027.

### Pruebas

Las 27 pruebas nuevas que describen el cambio fallaron primero; una más, que
confirma que la respuesta de candidatos no cambia, pasaba antes y después.
Antes del cambio pasaban 612 pruebas de año lectivo; después pasan 640.
`scripts/verify.py` pasó con 2147 pruebas, Ruff y `pip check` limpios, usando
una base ficticia.

## 2026-10-08 - Año lectivo 6.2a: vista previa de activación

Primera parte del paso 6.2 de la fase 6 de
`docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Nuevo `GET /anios-lectivos/{anio_lectivo_id}/activacion/vista-previa`, solo
  para admin y limitado al siguiente año en preparación. Cuenta quién continúa,
  quién llega nuevo, quién sale como retirado o egresado, y lista quién falta
  por decidir. Devuelve `puede_activar`, calculado en el backend.
- Solo lee: no bloquea filas, no activa el año ni cambia estudiantes o
  matrículas. Ninguna ruta existente cambió su respuesta.
- No hay migración nueva, cambio de frontend, acceso a una base real ni
  creación de 2027.

### Pruebas

Las 14 pruebas nuevas fallaron primero porque la ruta no existía. Antes del
cambio pasaban 598 pruebas de año lectivo; después pasan 612.
`scripts/verify.py` pasó con 2119 pruebas, Ruff y `pip check` limpios, usando
una base ficticia.

## 2026-10-06 - Año lectivo 5.6: resumen y recorrido financiero

Sexto paso de la fase 5 de `docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Nuevo `GET /anios-lectivos/{anio_lectivo_id}/resumen`, solo para admin y
  limitado al siguiente año en preparación. Devuelve conteos de cursos,
  conceptos, matrículas, valores especiales y pagos no anulados, con el total
  pagado de ese año.
- El listado de valores personalizados acepta `anio_lectivo_id` opcional. Sin
  él conserva el año activo; con él limita conceptos, matrícula y precio por
  curso al año pedido.
- Guardar un valor personalizado toma el curso desde la matrícula del año del
  concepto. Ya no usa `estudiantes.curso_id`, que es únicamente la copia del
  curso del año activo.
- Se comprobó el recorrido completo de una matrícula 2027 con valor especial
  pagada en noviembre de 2026. La deuda 2027 queda saldada y 2026 no cambia.
  No se modificaron fórmulas de cobro, mora, deuda ni cartera.
- No hay migración, cambio de frontend, acceso a una base real ni creación de
  2027.

### Pruebas

Las 10 pruebas iniciales fallaron primero contra el código anterior; después se
añadió una de compatibilidad. Al final pasaron 436 pruebas específicas.
`scripts/verify.py` pasó con 2096 pruebas,
Ruff y `pip check` limpios, usando una base ficticia.

## 2026-10-06 - Año lectivo 5.5: matricular el año en preparación

Quinto paso de la fase 5 de `docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Tres rutas nuevas, solo para admin, consultan candidatos de un curso del año
  activo, promueven una selección explícita al curso de `N+1` en preparación y
  crean un estudiante nuevo directamente en ese destino.
- Los candidatos salen de `matriculas`, no de la copia
  `estudiantes.curso_id`. La respuesta indica quién ya tiene matrícula en el
  destino y la promoción rechaza estudiantes ajenos, repetidos o ya
  matriculados.
- Al matricular un estudiante existente se copian sus valores especiales a
  los conceptos equivalentes del destino mediante `tipo_pago_origen_id`. La
  respuesta los marca `revisar`; una equivalencia ausente revierte toda la
  selección.
- Promover no escribe el curso vigente. El alta directa crea solo la matrícula
  del año en preparación y mantiene `estudiantes.curso_id` en `NULL` hasta la
  activación.
- Cada alta o promoción se confirma como una sola transacción. No hay
  migración, no se crean pagos y no cambian cartera ni cálculos de deuda. No se
  accedió a una base real ni se creó 2027.

### Pruebas

Antes del cambio pasaron 135 pruebas de caracterización. Las pruebas nuevas
fallaron primero por las rutas y funciones ausentes; al final son 16 y cubren
permisos, selección, referencias de año, copia de valores, alta directa y
choques concurrentes. Pasan 151 pruebas específicas. `scripts/verify.py` pasó
con 2085 pruebas, Ruff y `pip check` limpios, usando una base ficticia.

## 2026-10-06 - Año lectivo 5.4: copiar la configuración al año siguiente

Cuarto paso de la fase 5 de `docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- Nuevo `POST /anios-lectivos/{anio_lectivo_id}/copiar-configuracion`, solo
  para admin. El servidor exige que el destino sea exactamente el año posterior
  al activo y que esté en preparación.
- Copia siempre los cursos activos, que nacen activos con
  `curso_origen_id`, y todos los conceptos de pago, incluso inactivos, con su
  configuración completa y `tipo_pago_origen_id`.
- Tres opciones, apagadas por defecto, controlan precios por curso, carga
  académica y directores de grupo. Los precios se enlazan al curso y concepto
  nuevos. La carga conserva profesor, materia, horario, estado y orden de
  boletín, y reconstruye `asignacion_academica_id` solo con ids nuevos.
- La operación completa usa una sola transacción. Un curso o concepto
  repetido se identifica en un `409`; cualquier choque o referencia inválida
  revierte también todo lo copiado antes.
- No cambia pagos, deudas ni cálculos financieros. No hay migración y no se
  accedió a una base real.

### Pruebas

Antes del cambio pasaron 329 pruebas de caracterización. Las 16 pruebas
iniciales fallaron porque no existían ruta, controlador ni repositorio; la red
se amplió a 20 pruebas nuevas para cubrir permisos, carreras y solo cursos
activos. Al final pasaron 349 pruebas específicas. `scripts/verify.py` pasó con
2069 pruebas, Ruff y `pip check` limpios.

## 2026-10-06 - Año lectivo 5.3: crear y preparar el año siguiente

Tercer paso de la fase 5 de `docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- `POST /anios-lectivos`, solo para admin y sin cuerpo, calcula el año activo
  `N` y crea exactamente `N+1` en estado `preparacion`. No permite que el
  frontend elija el número.
- La creación es transaccional, bloquea el activo y responde `409` si ya hay
  otro año en preparación, si no existe un activo o si `N+1` ya existe.
- `POST /cursos` y `POST /tipos-pagos` aceptan `anio_lectivo_id` positivo y
  opcional. Con él, validan que el año exista y sea editable para el admin;
  sin él, conservan el camino, SQL, parámetros y respuestas del año activo.
- Los cuerpos de edición no reciben el campo: un curso o concepto existente no
  se puede mover de año por accidente.
- No hay migración, copia automática ni acceso a una base real. Este paso no
  crea 2027 por sí mismo; deja listo el endpoint para que el usuario lo haga
  más adelante desde la pantalla de la fase 5.7.

### Pruebas

Antes del cambio pasaron 258 pruebas de caracterización. Las primeras 14
pruebas nuevas fallaron porque el contrato aún no existía; después se sumaron 3
comprobaciones de regresión de las rutas. Al final pasaron 275 pruebas
específicas, incluidas las 17 nuevas, sin cambiar el comportamiento del año
activo. `scripts/verify.py` pasó con 2049 pruebas, Ruff y `pip check` limpios.

## 2026-10-06 - Año lectivo 5.2: orígenes para las copias entre años

Segundo paso de la fase 5 de `docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué queda listo

- `migrations/20261006_anios_lectivos_origenes.sql` agrega dos columnas
  opcionales y autorreferentes: `cursos.curso_origen_id` y
  `tipos_de_pagos.tipo_pago_origen_id`.
- Cada columna tiene su clave foránea y su índice. No se rellena ninguna fila,
  no se borra ni cambia información existente y no hay borrado en cascada.
- Siete pruebas nuevas fijan el alcance, la nulabilidad, las referencias, los
  índices, la reejecución y la ausencia de cambios de datos. Se escribieron
  primero y fallaron las siete antes de crear el SQL.

### Prueba y estado

El usuario probó la migración en una rama de Neon con endpoint directo. Los dos
tenants pasaron por `PENDIENTE`, `OK` y después `OMITIDA (ya aplicada)`. Regeneró
el esquema base desde `tenant_colegio_1`; conservó 34 tablas, 1 función y 1
disparador, y el diff solo incorporó las dos columnas, claves e índices más la
cabecera de la migración. Pasan 41 pruebas específicas y 2032 globales; Ruff,
`pip check` y `git diff --check` están limpios. La migración y la base quedaron
en `a6f3cc0`; el usuario confirmó el despliegue `Live` en Render y después la
aplicó en producción. En `tenant_colegio_1` y `tenant_2005`, la secuencia fue
`PENDIENTE` → `OK` → `OMITIDA (ya aplicada)`. No se rellenó ni borró ningún
dato existente.

## 2026-10-05 - Año lectivo 5.1: la matrícula manda sobre el curso vigente

Primer paso de la fase 5 de `docs/funcionalidades/ANIO_LECTIVO.md`.

### Qué cambia

- El cuerpo y la respuesta de `POST /estudiantes` y
  `PUT /estudiantes/{id}` se conservan para el año activo.
- El curso enviado se guarda primero en la matrícula activa mediante un upsert
  y luego `sincronizar_curso_vigente` lo copia a
  `estudiantes.curso_id`. Esa función es la única escritura de la copia.
- Un curso inexistente o de otro año devuelve `409`; la transacción revierte
  también los cambios globales del estudiante.
- Si en el futuro un estudiante solo tiene matrícula en un año en preparación,
  la sincronización deja `curso_id = NULL` hasta que ese año sea el activo.
- No hay migración ni cambio de esquema en este paso.

### Pruebas

Se caracterizaron primero 27 pruebas existentes. Las 8 pruebas nuevas fallaron
contra el código anterior por las funciones y el flujo ausentes; después, 36
pruebas específicas cubren SQL, orden transaccional, rechazo y traducción HTTP.
`scripts/verify.py` pasó con 2025 pruebas, Ruff y `pip check` limpios usando un
`DATABASE_URL` ficticio; `git diff --check` también quedó limpio. Una primera
ejecución aislada no pudo abrir la carpeta temporal de pytest; al repetirla sin
esa restricción, la verificación pasó completa. El detalle queda registrado en
el documento principal de la funcionalidad.

## 2026-10-02 - Año lectivo: guardia de escritura en las rutas de solo admin

Fase 3, paso 3.7b, de `docs/funcionalidades/ANIO_LECTIVO.md`. Con este paso la
fase 3 queda completa.

### Que cambia

- Las 19 rutas de escritura de solo admin (asignaciones, cursos, listas de
  seguimiento, revision y observaciones de planes, conceptos de pago y
  valores por estudiante) responden `409` si lo que se guarda es de un año
  cerrado. Con el año activo, en preparacion o reabierto, todo igual. Lista
  en `docs/API_ENDPOINTS.md`, "Guardia de escritura".
- Servicio `anio_lectivo`: `exigir_anio_editable_para_admin` y sus variantes
  para cursos, clases, planes y conceptos (sin pasar el usuario por las
  capas: el router ya exige admin). Repositorio del año:
  `leer_anios_de_cursos` (uno o varios cursos en una consulta; editar una
  clase mira su curso de antes y el nuevo) y `leer_anio_de_concepto`.
- Conceptos y valores por estudiante dejan pasar el `409` antes de su
  `except Exception`, para que no salga como "error interno".
- "Columna en todos los cursos" con `?anio_lectivo_id=` usa el estado que ya
  leia al validar el año: ninguna consulta mas.
- Costo, el aceptado por el usuario: una consulta mas por guardado, ninguna
  conexion nueva.

### Pruebas

`tests/test_anio_lectivo_guardia_conteos.py`: 19 rutas mas, medidas antes del
cambio (pasaron contra el codigo anterior) y despues: +1 consulta, 0
conexiones (+0 en "todos los cursos"). `tests/test_anio_lectivo_guardia.py`:
103 nuevas (la regla del admin, las dos lecturas, y por HTTP cada ruta: año
cerrado 409 sin escribir, preparacion y reabierto guardan, activo como
siempre, y lo que mira cada guardia). Ajustadas a proposito 64 pruebas de 10
archivos que fijan llamadas y consultas de esos guardados, con el criterio
del 3.7a. Treinta versiones dañadas del codigo hacen fallar alguna.
`scripts/verify.py`: 2016 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: guardia de escritura en las rutas del profesor

Fase 3, paso 3.7a, de `docs/funcionalidades/ANIO_LECTIVO.md`.

### Que cambia

- Las 11 rutas de escritura que usa el profesor (mas el borrado de imagen del
  admin, que comparte el guardado) miran el año de lo que se guarda antes de
  escribir: `cerrado` responde 409 para todos; `preparacion` y `reabierto`,
  403 para el profesor. Con el año activo, todo igual. Lista y mensajes en
  `docs/API_ENDPOINTS.md`, "Guardia de escritura".
- Servicio `anio_lectivo`: `exigir_anio_editable` (la regla),
  `exigir_asignacion_editable`, `exigir_plan_editable`,
  `exigir_anotacion_editable` y `AnioLectivoNoEditableError`, una
  `HTTPException`. Repositorio del año: `leer_anio_de_asignacion`,
  `leer_anio_de_plan` y `leer_anio_de_anotacion`.
- Los guardados reciben `usuario` (argumento obligatorio, por nombre) desde
  la ruta hasta la transaccion. Boletin y planeador reenvian
  `HTTPException` antes de su `except Exception`, para no responder 500.
- `DELETE /admin/plan-de-clases/{plan_id}/imagen`: la proteccion de admin
  pasa del decorador a un parametro (`current_user`), como en sus rutas
  hermanas del admin. Misma dependencia, una sola vez.
- Costo, aceptado por el usuario: una consulta mas por guardado, ninguna
  conexion nueva.

### Pruebas

`tests/test_anio_lectivo_guardia_conteos.py` (21): cada ruta y rol, conexiones
y consultas medidas antes (escrita y pasada contra el codigo anterior) y
despues: +1 consulta, 0 conexiones. `tests/test_anio_lectivo_guardia.py`
(126): la regla, las tres lecturas, y por HTTP en cada ruta y rol: año
cerrado (409, nada escrito, ningun `commit`), en preparacion y reabierto (403
el profesor; el admin guarda), activo (como siempre), el id que mira la
guardia y la limpieza de la evidencia subida. Ajustadas a proposito 111
pruebas de 15 archivos que fijan llamadas y consultas de esos guardados: donde
el archivo dobla los ayudantes, se dobla la guardia; donde cuenta consultas
reales, la guardia corre y se cuenta (+1). Veintitres versiones dañadas del
codigo hacen fallar alguna. `scripts/verify.py`: 1894 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: aviso al renombrar una materia de otro año

Fase 3, paso 3.6, de `docs/funcionalidades/ANIO_LECTIVO.md` (decision 12).

### Que cambia

- `PUT /materias/{materia_id}`: si el nombre guardado cambia y la materia se
  dicta en mas de un año, o en uno cerrado o reabierto, no guarda y responde
  `409` con `detail = {"codigo": "materia_usada_en_otro_anio", "mensaje":
  ...}`. Con `"confirmar_cambio_nombre": true` en el cuerpo guarda como
  siempre. Con un solo año, como hoy, nunca avisa.
- Consulta nueva `leer_nombre_y_anios_de_materia` (repositorio del año) y la
  regla `anios_a_avisar_al_renombrar` con su mensaje (servicio del año).
  Cuenta tambien las clases inactivas: ante la duda, avisa.
- Costo: editar una materia hace 3 consultas en vez de 2 (aceptado por el
  usuario). Con la confirmacion, las 2 de siempre.

### Pruebas

`tests/test_materias_caracterizacion.py` (12), escrita antes del cambio:
editar una materia no tenia ninguna prueba. Ajustada a proposito despues: el
doble conoce la consulta nueva y el conteo pasa de 2 a 3; las dos consultas de
antes conservan texto, parametros y orden. `tests/test_anio_lectivo_renombrar_materia.py`
(30): la regla, el mensaje, la consulta, el controlador con dos años y la ruta
por HTTP. Trece versiones dañadas del codigo hacen fallar alguna.
`scripts/verify.py`: 1747 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: observador, expediente y planes del admin por año

Fase 3, paso 3.5b, de `docs/funcionalidades/ANIO_LECTIVO.md`. Con esto, todas
las lecturas de la fase 3 quedan por año.

### Que cambia

- `GET /observador/{estudiante_id}`: las anotaciones del año activo (filtro
  en el `ON`, como el del periodo). El admin puede pedir otro año; un
  profesor que lo intente recibe 403 (decision 4). Es la primera ruta que usa
  la regla del profesor de `app/services/anio_lectivo.py`.
- `GET /estudiantes/{id}/detalles?anio_lectivo_id=`: notas, faltas,
  observaciones y deuda del año. Las faltas sin clase registrada se siguen
  contando en el año activo, para que nada cambie hoy.
- `GET /admin/plan-de-clases?anio_lectivo_id=`: los planes del año (sin
  validar que exista: abre su propia conexion).
- Sin año, mismos parametros y mismo numero de consultas en las tres.

### Pruebas

18 nuevas en `tests/test_anio_lectivo_lecturas.py`, con bases simuladas de dos
años (bitacora, faltas con una sin clase). Ajustadas a proposito: el contador
de consultas de `test_observaciones_caracterizacion.py` (como el del boletin),
la prueba que partia la bitacora en su primer `WHERE` (ahora en el del
estudiante), el total de lineas del dominio de planes (1382 -> 1395) y el doble
de la ruta de planes. Catorce versiones dañadas del codigo hacen fallar las
nuevas. `scripts/verify.py`: 1705 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: boletin, reporte parcial y puesto por año

Fase 3, paso 3.5a, de `docs/funcionalidades/ANIO_LECTIVO.md`. El paso 3.5 se
partio en dos para revisarlo mejor; este es el boletin.

### Que cambia

- `GET /boletines/admin/generar/...` y `/admin/reporte-parcial/...` aceptan
  `?anio_lectivo_id=`. Sin el, o con el activo, las consultas son las de
  siempre, letra por letra (comparadas con el commit anterior). Con otro año,
  el curso es el de la matricula de ese año. Año inexistente: 404.
- **Puesto en el curso**: solo cuentan las definitivas de cursos del año que
  se mira, tambien sin año. Sin este filtro, con 2027 activo, el periodo 1
  de 2027 se promediaria con el periodo 1 de 2026. Con un solo año, el mismo
  resultado; mismos parametros.
- Servicio `anio_lectivo`: `anio_distinto_del_activo` (la regla "con el
  activo, el camino de siempre", que ahora comparte la lista de estudiantes)
  y `AnioLectivoInexistenteError`, un `ValueError` que el boletin atrapa por
  su nombre para no convertir otros fallos en 404.
- Materias ocultas de un año cerrado: quedan para la fase 6 (decidido por el
  usuario el 2026-10-02).

### Pruebas

24 nuevas en `tests/test_anio_lectivo_lecturas.py`, entre ellas el puesto con
dos años (con 2027 activo, Ana es primera; mezclando, seria segunda). En
`test_boletin_caracterizacion.py` el contador de consultas ahora reconoce las
cinco que llevan un hueco para el curso (siguen siendo 11), y dos dobles de
ruta reciben el año, igual que en `test_boletines_reporte_parcial.py`. Once
versiones dañadas del codigo hacen fallar las nuevas. `scripts/verify.py`:
1687 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: estudiantes y cartera desde las matriculas

Fase 3, paso 3.4, de `docs/funcionalidades/ANIO_LECTIVO.md`. Zona de dinero.
Mientras haya un solo año, ninguna respuesta cambia.

### Que cambia

- `GET /estudiantes?anio_lectivo_id=`: sin año o con el activo, la lista de
  siempre (su SQL no cambia); con otro año, sus matriculados con el curso de
  ese año.
- `GET /cartera/mora` y `/cartera/mora/resumen` con `?anio_lectivo_id=`. Los
  estudiantes salen de las matriculas del año. Mirando otro año que no es el
  activo, salen tambien los que se retiraron debiendo (decision 18) y no salen
  ventas (decision 19), las dos decididas por el usuario el 2026-10-02.
- El estado de cuenta por curso (`/estado-cuenta/curso/{id}` y
  `/reportes/estado-cuenta/{id}`, sin pantalla hoy) calcula en el año del
  curso, con sus estudiantes desde las matriculas.

### Consultas (medidas en pruebas)

Sin año, iguales: lista de estudiantes 1 y 2 (paginada), cartera 5/13/13,
estado de cuenta 1/13/37. Con año, una mas para validarlo (cartera de otro año:
la validacion suma una y las ventas restan una). `/reportes/estado-cuenta`
pasa de 6/15/15 a 7/16/16, aceptado por el usuario.

### Pruebas

22 nuevas en `tests/test_anio_lectivo_lecturas.py`, con bases simuladas de dos
años (estudiantes, cartera con un retirado que debe y una venta, y estado de
cuenta de un curso de cada año), y 6 en `tests/test_reportes_query_counts.py`
que fijan los conteos de cartera con año. Ajustadas a proposito: los dobles de la ruta
de estudiantes, y las bases simuladas de estado de cuenta en
`test_reportes_query_counts.py`, `test_reportes_estado_cuenta.py` y
`test_pagos_adelantados.py`, que no conocian las consultas nuevas; el conteo
aceptado del reporte. Diecinueve versiones dañadas del codigo las hacen
fallar. `scripts/verify.py`: 1663 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: cursos y conceptos por año

Fase 3, paso 3.3, de `docs/funcionalidades/ANIO_LECTIVO.md`. Mientras haya un
solo año, ninguna respuesta cambia y ninguna consulta se agrega.

### Que cambia

- `GET /cursos`, `GET /tipos-pagos` y `GET /tipos-pagos/detallado` aceptan
  `?anio_lectivo_id=` (sin el, el activo; año inexistente, 404).
- El nombre repetido de cursos y de conceptos se compara solo dentro del año,
  como ya lo permite la base desde la migracion A. Sin esto, la copia de
  cursos y conceptos a 2027 (fase 5) fallaria como "repetido".
- `PUT /tipos-pagos/{id}/cursos` rechaza con 400 un curso de otro año que el
  concepto, en la misma consulta que ya confirmaba que el concepto existe.
- "Crear la columna en todos los cursos" de listas de seguimiento actua sobre
  los cursos de un año (`?anio_lectivo_id=`, por defecto el activo).
- `GET /reportes/general`: `total_cursos` y `estudiantes_por_curso`, solo del
  año activo.

### Pruebas

32 nuevas en `tests/test_anio_lectivo_lecturas.py`, con bases simuladas de
dos años para el nombre repetido de cursos y conceptos y para los precios por
curso. Se ajustaron a proposito, sin cambiar la respuesta que comprueban: tres
pruebas de la fase 0 y la del reporte general que fijan el texto de la
consulta, dos dobles de la ruta de cursos, el doble del repositorio de listas
y dos bases simuladas que no conocian la consulta nueva de precios. Diecisiete
versiones dañadas del codigo hacen fallar las nuevas. `scripts/verify.py`:
1635 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: el profesor y los horarios, solo del año

Fase 3, paso 3.2, de `docs/funcionalidades/ANIO_LECTIVO.md`. Mientras haya un
solo año, ninguna respuesta cambia y ninguna consulta se agrega.

### Que cambia

- "Mis clases", los cursos del profesor y las faltas del inicio del profesor
  muestran solo el año activo.
- `GET /asignaciones/lista`, `GET /hora/horarios-admin` y `GET
  /profesores/{id}/disponibilidad` aceptan `?anio_lectivo_id=` (sin el, el
  activo; año inexistente, 404).
- El cruce de horario de un profesor al crear o editar una asignacion solo
  mira clases del mismo año que el curso. Sin esto, la carga academica de
  2027 chocaria con los horarios de 2026.
- `anios_lectivos_repository.condicion_anio`: el filtro por año que usaran
  todos los listados.

### Pruebas

34 nuevas en `tests/test_anio_lectivo_lecturas.py`, entre ellas una base
simulada con clases de 2026 y 2027 del mismo profesor. Se ajustaron dos dobles
de ruta en `tests/test_asignaciones_pagination.py` por el argumento nuevo del
controlador. Las demas pruebas existentes, incluidas las que cuentan
consultas, pasaron sin cambios. Catorce versiones dañadas del codigo hacen
fallar las nuevas. `scripts/verify.py`: 1603 pasan, 0 fallan.

## 2026-10-02 - Año lectivo: lista de años y regla del año pedido

Fase 3, paso 3.1, de `docs/funcionalidades/ANIO_LECTIVO.md`. Primer paso de
las lecturas por año. Ninguna respuesta existente cambia: todo es nuevo.

### Que cambia

- Ruta nueva `GET /anios-lectivos`, para admin y profesor: el admin recibe
  todos los años (`id`, `anio`, `estado`, el mas reciente primero) y el
  profesor solo el activo.
- `app/services/anio_lectivo.py` gana `listar_anios_visibles` y
  `resolver_anio_pedido`, la regla comun que usaran los listados por año:
  sin año, el activo y ninguna consulta extra; año inexistente, error; un
  profesor que pide otro año, `AnioLectivoNoPermitidoError` (403).
- Archivos nuevos: `app/routes/anios_lectivos.py` y
  `app/controllers/anios_lectivos_controller.py`. El repositorio del año
  suma `listar_anios_lectivos` y `leer_anio_activo`.

### Pruebas

21 nuevas en `tests/test_anio_lectivo_lecturas.py`. Cinco versiones dañadas
del codigo (orden, rol desconocido, consulta sin año, profesor con otro año,
router sin proteccion) las hacen fallar. `scripts/verify.py`: 1569 pasan, 0
fallan.

## 2026-10-01 - Año lectivo: la deuda de años anteriores se ve aparte

Fase 2, paso 2.4, de `docs/funcionalidades/ANIO_LECTIVO.md`. Con el, el
codigo de la fase 2 queda completo: cuando 2027 este activo, lo que se deba de
2026 no desaparece y se muestra separado de lo de 2027.

### Que cambia

- `GET /estudiantes/{id}/deudas` y cada estudiante de `GET /cartera/mora`
  traen `deuda_anios_anteriores`: la deuda de cada año anterior en que el
  estudiante tuvo matricula, con la misma regla de siempre. Un estudiante que
  solo debe de años anteriores tambien aparece en cartera, y el resumen suma
  `total_anios_anteriores`.
- `cobros.calcular_deudas_anios_anteriores` calcula todos los estudiantes y
  años de una vez.

### Consultas (medidas, el usuario acepto el costo antes de escribirlo)

Mientras haya un solo año: una mas en cada pantalla (deudas 11 -> 12, cartera
12 -> 13). Con años anteriores: deudas 19 y cartera 17, sin crecer con los
estudiantes. Fijado en pruebas.

### Pruebas

10 nuevas en `tests/test_anio_lectivo_cobros_por_anio.py`, entre ellas los
casos A y B completos con dos años. Se ajustaron el conteo de cartera y dos
pruebas que fijan la respuesta de deudas. `scripts/verify.py`: 1548 pasan, 0
fallan.

## 2026-10-01 - Año lectivo: pagar en otro año y adelantar meses del siguiente

Fase 2, paso 2.3, de `docs/funcionalidades/ANIO_LECTIVO.md`. Prepara el cobro
de la matricula 2027 en noviembre y los adelantos de 2027 en diciembre.

### Que cambia

- `POST /pagos` y `POST /pagos/adelanto` aceptan `anio_lectivo_id` opcional:
  el pago se guarda en ese año, y la deuda y los meses se calculan con sus
  conceptos y el curso de su matricula. Cualquier estado del año vale (un
  pago se registra en el año de la deuda que salda); un año que no existe da
  400.
- `GET /estudiantes/{id}/deudas`, `/pagos/vencidos/opciones/{id}` y
  `/pagos/adelanto/opciones/{id}` aceptan `?anio_lectivo_id=` opcional.
- Nuevo `app/services/anio_lectivo.py` (`exigir_anio_lectivo`) y
  `leer_anio_lectivo` en el repositorio del año lectivo.

Sin el año, todo es identico: la misma sentencia, los mismos parametros y las
mismas llamadas. Las 1516 pruebas que ya existian pasaron sin tocarse. El
frontend no cambia todavia; el selector "Año del pago" es de su fase 5.

### Pruebas

22 nuevas en `tests/test_anio_lectivo_cobros_por_anio.py` (pago a un año
cerrado y a uno en preparacion, año inexistente, precio del curso de 2027,
adelantos de 2027 en diciembre, rutas y esquemas). Se invirtio la ultima
prueba de error de la caracterizacion, la de los adelantos de diciembre.
`scripts/verify.py`: 1538 pasan, 0 fallan.

## 2026-10-01 - Año lectivo: cada año cuenta solo sus pagos

Fase 2, paso 2.2, de `docs/funcionalidades/ANIO_LECTIVO.md`. Prepara el
cobro de la matricula 2027 en noviembre: sin esto, ese pago se sumaria a la
matricula de 2026.

### Que cambia

- `cobros.py`: lo pagado por concepto cuenta solo los pagos del año activo, y
  las aplicaciones solo de conceptos de ese año. El curso que fija los precios
  sale de la matricula del año activo.
- `estado_cuenta_controller.py` y `reportes_repository.py`: lo pagado en el
  estado de cuenta cuenta solo el año activo.

El año va como la subconsulta `ANIO_ACTIVO_ID_SQL`: sin parametros ni
consultas nuevas, y los conteos de `tests/test_reportes_query_counts.py`
siguen iguales. Con un solo año, nada cambia: todo pago tiene año y la
matricula del año activo es el curso del estudiante.

### Pruebas

Cuatro pruebas nuevas en `tests/test_anio_lectivo_cobros_por_anio.py`. En
`tests/test_anio_lectivo_cobros_caracterizacion.py` se invirtieron la
matricula del año siguiente, el caso A y los meses vencidos de 2027, con una
base de pagos simulada que filtra por año como la real. Dos simulaciones de la
consulta del curso se ajustaron a su forma nueva. `scripts/verify.py`: 1516
pasan, 0 fallan.

## 2026-10-01 - Año lectivo: las cuotas se cuentan en el año del concepto

Fase 2, paso 2.1, de `docs/funcionalidades/ANIO_LECTIVO.md`. Arregla el error
que llegaba el 1 de enero de 2027: el calculo usaba el año del calendario, asi
que ese dia solo existian cuotas de 2027 y la deuda de 2026 desaparecia.

### Que cambia

- `cartera.py`: el calculo de cuotas recibe el año (`anio`); sin el, el de
  `hoy`, como antes. Un año que termino tiene todas sus cuotas vencidas, y
  uno que no ha empezado, ninguna.
- `cobros.py`: `obtener_tipos_pago` trae los conceptos del año activo, cada
  uno con su año, en la misma consulta de siempre. Deudas, cartera y meses
  vencidos cuentan las cuotas en ese año.
- `pagos_controller.py`: los adelantos ofrecen meses del año del concepto.

Ningun cambio visible mientras el año activo sea el del calendario. Ninguna
ruta, esquema ni respuesta cambia, y no hay consultas nuevas: los conteos de
`tests/test_reportes_query_counts.py` siguen iguales.

### Pruebas

`tests/test_anio_lectivo_cobros_por_anio.py` (12), dos de ellas comparan con
una copia literal del codigo anterior en miles de combinaciones. Se
invirtieron el caso B y los meses vencidos de enero en
`tests/test_anio_lectivo_cobros_caracterizacion.py`. Tres pruebas que simulan
la consulta de conceptos se ajustaron a su forma nueva. `scripts/verify.py`:
1512 pasan, 0 fallan.

## 2026-10-01 - Año lectivo: el año pasa a ser obligatorio (migracion B)

Fase 1, punto 3, de `docs/funcionalidades/ANIO_LECTIVO.md`. Con ella termina
la fase 1. Invisible: ninguna pantalla ni respuesta de la API cambia.

### Que se aplico

`migrations/20261001_anios_lectivos_obligatorio.sql`, aplicada en produccion
a `tenant_colegio_1` y `tenant_2005` despues de probarla en una rama de Neon,
tambien con la app local. Rellena con el año activo lo que quedo sin año
entre la migracion A y el despliegue del codigo (no habia nada), pone al dia
las matriculas del año activo con el curso de cada estudiante y vuelve
obligatorio `anio_lectivo_id` en `cursos`, `tipos_de_pagos`, `matriculas`,
`pagos` y `observador_anotaciones`. Tres frenos revierten el tenant si algo
no cuadra; ninguno salto. No borra nada. Esquema base regenerado.

### Pruebas

`tests/test_migracion_anios_lectivos_obligatorio.py` (12), incluida una que
exige que todo `INSERT` de `app/` en esas tablas escriba el año. Se
comprobaron con 16 versiones dañadas de la migracion y del codigo.
`scripts/verify.py`: 1500 pasan, 0 fallan.

### Orden de despliegue

Se aplico despues de confirmar en Render el despliegue del codigo que escribe
el año (`67b2d4b`, Live). El detalle de la prueba en la rama y en produccion
esta en el documento de la funcionalidad, fase 1.

## 2026-09-30 - La deuda se calcula con la fecha de Colombia

El usuario vio a las 22:50 de Bogota una deuda en el backend local y otra en
produccion, que ya contaba vencida la cuota de octubre. Render corre en UTC:
alli ya era 2026-10-01 03:50.

### Causa

`cartera.py` (dos sitios) y `cobros.py` (dos sitios) tomaban "hoy" de
`date.today()`, la fecha del servidor. Cada noche, desde las 7 p. m. de
Bogota, produccion calculaba deudas, cartera, mora y meses vencidos como si ya
fuera el dia siguiente. Pagos si usaba la hora de Bogota, asi que las dos
partes del sistema no coincidian.

### Cambio

- `app/core/fechas.py` (nuevo): `hoy_en_colombia()`, la unica fuente de "hoy"
  para reglas del colegio. El reloj va en `_ahora_utc()` para poder fijarlo
  en pruebas.
- `cartera.py` y `cobros.py` lo usan en los cuatro sitios. Quien pasa `hoy`
  explicito (pagos, pruebas) no cambia.
- El alta de colegios usa la misma funcion para el año activo inicial.

Fuera de este cambio, anotados en `docs/funcionalidades/ANIO_LECTIVO.md`: la
fecha por defecto de egresos y prestamos, el estado SaaS del colegio y los
`CURRENT_DATE` de la base.

### Pruebas

`tests/test_fechas_colombia.py` (10) fija el reloj a las 11 p. m. del 30 de
septiembre en Bogota y exige 3 cuotas, no 4. Ademas cubre el cambio de dia a
medianoche, el 31 de diciembre y una guardia para que cobros y cartera no
vuelvan a usar el reloj del servidor. Se comprobo que la prueba falla con el
comportamiento viejo. `scripts/verify.py`: 1488 pasan, 0 fallan.

## 2026-09-30 - Año lectivo: lo nuevo nace con su año

Fase 1, punto 2, de `docs/funcionalidades/ANIO_LECTIVO.md`. Cierra la ventana
abierta por la migracion A. Invisible: ninguna respuesta de la API cambia.

### Que cambia

- Crear un curso, un concepto de pago, un pago (normal o adelantado) o una
  anotacion del observador escribe `anio_lectivo_id` con el año activo,
  dentro del mismo `INSERT`, con la subconsulta
  `ANIO_ACTIVO_ID_SQL` de `app/repositories/anios_lectivos_repository.py`.
  Sin consultas ni parametros nuevos.
- Crear o editar un estudiante deja su matricula del año activo igual a su
  curso, en la misma transaccion (`sincronizar_matricula_del_anio_activo`).
- Un colegio nuevo nace con el año en curso como activo (hora de Bogota).

### Pruebas

`scripts/verify.py`: 1478 pasan, 0 fallan; ruff y `pip check` limpios. Nuevo
`tests/test_anio_lectivo_escrituras.py` (10). Nueve pruebas de
caracterizacion se ajustaron a proposito: cinco listas exactas de
repositorios, los dos `INSERT` de pagos y dos del alta de colegios (13 → 14
operaciones; lineas del controlador 330 → 337).

### Orden de despliegue

Este codigo va **antes** de la migracion B, que vuelve obligatorio el año: el
codigo anterior no lo escribe y fallaria con `NOT NULL`.

## 2026-09-30 - Año lectivo: fundacion en la base de datos (migracion A)

Primer paso de la funcionalidad "Año lectivo"
(`docs/funcionalidades/ANIO_LECTIVO.md`, fase 1). Invisible: ninguna pantalla
ni respuesta de la API cambia.

### Que se aplico

`migrations/20260930_anios_lectivos.sql`, aplicada en produccion a
`tenant_colegio_1` y `tenant_2005` despues de probarla en una rama de Neon:

- tabla `anios_lectivos`, con 2026 como año activo;
- `anio_lectivo_id` en `cursos`, `tipos_de_pagos`, `matriculas`, `pagos` y
  `observador_anotaciones`, relleno con 2026 y todavia nullable;
- 174 matriculas de 2026 en `tenant_2005`, una por estudiante con curso;
- las reglas de nombre unico de cursos y conceptos de pago pasan a ser por
  año.

Esquema base regenerado desde `tenant_colegio_1` (34 tablas).

### Por que asi

El año cuelga del curso: notas, asistencia, boletines y horarios ya dependen
de un curso, asi que no se tocan. Llevan año solo los cursos y lo que no
depende de un curso. Detalle de cada decision en el documento de la
funcionalidad y en `docs/MIGRACIONES.md`.

### Ventana abierta hasta desplegar el codigo de la fase 1

El codigo actual no escribe el año. Hasta desplegar el codigo nuevo, los
cursos, conceptos, pagos y anotaciones que se creen quedan sin año, y crear un
estudiante o cambiarle el curso no actualiza su matricula. No se nota en
pantalla, porque nada lee esas columnas todavia. La migracion B los corrige
antes de volver obligatorio el año.

### Pruebas

`scripts/verify.py`: 1468 pasan, 0 fallan; ruff y `pip check` limpios.
Nuevas: `tests/test_migracion_anios_lectivos.py` (17, sobre el texto del SQL)
y, de la fase 0, `test_anio_lectivo_cobros_caracterizacion.py` (11) y
`test_anio_lectivo_listados_caracterizacion.py` (6).

## 2026-09-24 - Una asignatura inactiva ya no aparece en el boletin

El administrador desactivo unas asignaturas y siguieron saliendo en Gestion
Boletines. Desaparecian de todas las demas pantallas, pero no de esa.

### Un filtro que llego tarde a dos consultas

`materias.estado` se anadio en `20260604_materias_estado.sql`. Las **ocho**
consultas de `asignaciones_repository` adoptaron entonces el filtro
`COALESCE(LOWER(m.estado), 'activo') = 'activo'`. Las dos del boletin se
quedaron sin el:

- `leer_materias_del_estudiante` -el boletin oficial del admin-,
- `leer_planilla_vigente` -el reporte parcial-.

Las dos si filtraban por `a.activo`, la marca de la **asignacion**. Por eso el
sintoma solo aparecia al desactivar la **asignatura**: son dos interruptores
distintos y el boletin solo miraba uno.

### Desaparece tambien de los periodos ya calificados

Decision explicita del usuario, sobre la alternativa de conservar la materia
donde ya hubiera notas. El motivo: es exactamente lo que ya hacia desactivar la
asignacion, y tener dos interruptores con dos comportamientos distintos es peor
que la perdida de historico.

Quedan fuera de este cambio otras tres consultas que unen `materias` sin el
filtro -el dashboard de rendimiento y dos de la ficha del estudiante-, no
revisadas todavia.

## 2026-09-24 - Preparar una conexion pasa de tres idas a dos

Toda conexion del pool ejecutaba `SET search_path` y luego los timeouts en dos
`execute` separados. Ahora viajan juntos en uno solo. Lo que se ejecuta es
identico, y en el mismo orden.

### Medido contra la base real, no estimado

| | Antes | Ahora |
|---|---|---|
| `get_connection()` completo | 180 ms | **113 ms** |
| Autenticar una peticion (2 conexiones + 2 consultas) | 480 ms | **346 ms** |
| Guardar una nota (4 conexiones) | ~1,26 s | **~1,0 s** |

Lo cobra **cada** conexion de toda la API, no un endpoint concreto.

### De donde salian los 180 ms

Una ida y vuelta a la base cuesta ~60 ms (Neon, otro continente). Preparar una
conexion gastaba tres:

1. el `BEGIN` implicito que psycopg2 manda con `autocommit = False`,
2. el `SET search_path`,
3. el `SELECT set_config` de los timeouts.

El `BEGIN` no se puede quitar: los timeouts se fijan con `set_config(..., TRUE)`,
que es local a la transaccion y por tanto la necesita. Las otras dos si podian
viajar juntas.

Esto corrige de paso el comentario de `app/dependencies.py`, que decia "cada
ida y vuelta cuesta ~180 ms": son ~60 ms por ida; los 180 eran el precio de una
conexion entera.

### El esquema sigue sin interpolarse a mano

`build_tenant_search_path_statement` devuelve la sentencia sin ejecutarla, con
el esquema como `sql.Identifier` y validado por `get_current_tenant_schema`,
igual que antes. Se comprobo contra la base real que la sesion queda con el
`search_path` del tenant y los tres timeouts aplicados.

### Se borraron dos funciones que quedaron huerfanas

`set_tenant_search_path` y `apply_session_timeouts` eran los dos envoltorios que
`get_connection` llamaba uno detras de otro. Su trabajo no se perdio -es lo que
hace ahora `apply_session_setup` en una sola sentencia-, pero sin llamadores
`set_tenant_search_path` era una trampa: un nombre convincente en el archivo del
tenant que habria dejado una conexion con el esquema puesto y **sin timeouts**,
a medio preparar y sin avisar.

Con ellas se fue `test_apply_session_timeouts_no_consulta_si_no_hay_nada_que_fijar`.
Lo que protegia -que sin timeouts configurados no se ejecute nada de timeouts-
lo cubre `test_sin_timeouts_configurados_solo_se_fija_el_tenant`, que ademas lo
comprueba sobre el camino que de verdad se usa.

## 2026-09-24 - Guardar una nota deja de pedir una conexion de mas

`POST /planilla/nota` pedia al pool una conexion entera solo para comprobar que
el estudiante pertenece a la asignacion, y justo despues abria otra para hacer
el trabajo. Ahora esa comprobacion viaja en el cursor que el controlador ya
abre.

| | Antes | Ahora |
|---|---|---|
| Conexiones (admin) | 2 | **1** |
| Conexiones (profesor) | 3 | **2** |
| Consultas | 6 | 6 |

Las consultas **no bajan**: se hacen las mismas preguntas. Lo que desaparece
son los dos viajes de preparacion (`SET search_path` y los timeouts) que paga
cada conexion antes de consultar nada. Contra Neon eso es lo caro.

### El patron ya estaba en el repo

`validar_estudiante_asignacion` gana un `cursor=None` opcional, calcado del que
ya aceptan las tres funciones de `app/core/permissions.py`, con su mismo
contrato: con cursor lo usa, sin cursor abre el suyo. Ningun otro llamador
existe, y quien llame sin cursor se comporta como siempre.

### Lo que NO se movio, y por que

El permiso de la asignacion **sigue comprobandose en la ruta**. Moverlo al
controlador ahorraria otra conexion, pero
`test_las_tres_entradas_delegan_el_mismo_permiso_y_su_controlador` fija a
proposito que las tres entradas del router comprueban igual, y romper esa
simetria deja al POST pareciendo que se olvido el permiso. Ademas hoy no hay
prueba de extremo a extremo del 403 del POST -solo la del GET-, asi que se
moveria sin red. Queda para una decision propia.

### El rechazo cambia por dentro, no por fuera

"El estudiante no pertenece" ahora ocurre dentro del bloque transaccional, asi
que se pide un cursor donde antes se pedian dos conexiones. Sigue sin ejecutar
ningun DELETE ni INSERT y responde lo mismo, 200 con `{"error": ...}`. Las dos
pruebas que lo fijaban se actualizaron con esa explicacion.

## 2026-09-23 - Planilla: columnas en orden de creacion, no alfabetico

El profesor pidio que, al agregar un tipo de nota nuevo en Planilla, la
columna aparezca en el orden en que la fue creando, no reordenada
alfabeticamente.

`planilla_excel_controller` guardaba las columnas en un `set()` y las
devolvia con `sorted(...)`, por lo que el orden visible no tenia relacion con
el orden de creacion. Se agrego `nd.id` a la consulta de
`leer_filas_de_planilla` (unica excepcion a "las cinco cadenas SQL conservan
su texto original" que documenta ese repositorio) y el controlador ahora
ordena las columnas por el `id` minimo con el que aparece cada descripcion,
que equivale a su orden real de creacion.

## 2026-09-22 - Crear una columna de seguimiento en todos los cursos

Ampliacion de la funcionalidad de abajo. El administrador pidio poder crear la
misma columna en todos sus cursos sin teclearla una por una. Se aclaro primero
el alcance -sus cursos, no los dos colegios de la plataforma- y eligio copiar
al crear frente a una columna compartida de verdad.

### Sin migracion, y eso no es casualidad

Se crean N columnas **independientes**, una por curso, en la tabla que ya
existe. Ninguna tabla cambia. Importaba el doble porque
`20260921_listas_seguimiento.sql` ya estaba aplicada y su checksum guardado,
asi que no se podia editar.

Esto matiza, sin romperla, la decision "cada curso tiene su propia lista
independiente": lo que se crea son copias, no una fila compartida.

### Una sentencia, no un bucle

`INSERT ... SELECT ... WHERE NOT EXISTS` sobre `cursos`. Medido:
`tenant_colegio_1` tiene 25 cursos, asi que el camino ingenuo -leerlos,
preguntar por cada uno si ya la tiene, insertar- serian 51 idas y vueltas,
unos 9 s contra Neon.

### El detalle que decide el comportamiento

**Los cursos que ya la tienen se saltan en silencio.** Eso vuelve repetible el
boton, y con eso se cubre el caso del curso creado despues: se vuelve a pulsar
con el mismo nombre y solo se crea donde falta. De ahi salen dos consecuencias:

- que no se cree ninguna **no es un error**: es el resultado normal de volver a
  pulsar, y el endpoint responde 200;
- el `409` de este endpoint no es "ya existe" sino la carrera entre dos
  peticiones, con mensaje propio que invita a reintentar.

### "Activo" se copio, no se invento

`COALESCE(LOWER(estado), 'activo') = 'activo'`, la misma expresion que decide
que devuelve `GET /cursos`. Ojo al detalle: `cursos.estado` admite nulos y un
**NULL cuenta como activo**. Hay prueba que lee `curso_controller.py` y falla
si las dos reglas se separan.

### Ensayado contra PostgreSQL real

En `tenant_colegio_1`, con una transaccion que termina en ROLLBACK y no deja
ninguna fila. Once comprobaciones. Tres no las puede dar ninguna prueba con
dobles: repetir el alta no duplica nada, una variante con otras mayusculas y
espacios tampoco crea nada, y rellenar un solo hueco crea exactamente una.

## 2026-09-22 - Listas de Seguimiento por Curso

El administrador no tenia donde llevar registros propios por curso -quien fue a
un evento, quien compro el libro- fuera de notas y pagos. Se investigo primero
si el dato ya existia en otra forma: `notas_detalle` tiene columnas de nombre
libre pero atadas a una asignacion y solo existen cuando ya tienen una fila;
`asistencia` no tiene entidad de columna, su columna es una fecha; y en todo el
esquema no hay ningun mecanismo generico de campo personalizado. Detalle y
decisiones de producto en `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`.

### Tablas nuevas, ninguna existente modificada

`listas_seguimiento_columnas` y `listas_seguimiento_marcas`, migracion
`20260921_listas_seguimiento.sql`, aplicada a los dos tenants operativos. No se
toca `notas_detalle`, `asistencia` ni `tipos_de_pagos`. Un curso sin columnas se
comporta exactamente igual que antes.

### Endpoints nuevos

Cuatro, admin-only a nivel de router, bajo el prefijo `/listas-seguimiento`. Ver
`docs/API_ENDPOINTS.md`.

### Lo que hay que saber para tocarlo

- **El lote de marcas se escribe en una sola sentencia** con `UNNEST` y
  `ON CONFLICT`, no una por celda. Marcar una columna de 30 alumnos serian 30
  idas y vueltas -~5,4 s contra Neon- con el patron por fila que todavia tiene
  `asistencia_repository`. De ahi sale una consecuencia que no es evidente:
  PostgreSQL **aborta la sentencia entera** si el lote trae la misma celda dos
  veces, asi que el 422 por celdas repetidas no es cosmetico, es lo que evita
  un 500. La guarda vive en `LoteDeMarcas`, en el esquema.
- **El nombre duplicado se comprueba dos veces.** La consulta previa da el 409
  legible; el `except IntegrityError` recoge la carrera que rechaza el indice
  unico. La consulta normaliza en SQL con la misma expresion del indice, y hay
  prueba que lo verifica leyendo el propio archivo de migracion.
- **Coste fijo en consultas**: 4 el GET, 3 crear, 1 borrar, 3 guardar. Ninguno
  crece con la cantidad de alumnos ni de columnas.

### Frontend

Pendiente. La pantalla es una propuesta aparte, documentada en
`frontend-react/docs/funcionalidades/LISTAS_SEGUIMIENTO.md`; el backend no
depende de ella.

## 2026-09-15 - Director de grupo en el boletin

El boletin impreso solo tenia "Director de Grupo" como una etiqueta fija de
firma a mano, sin nombre real. El usuario pidio que el nombre apareciera
tambien como dato informativo aparte, sin tocar esa firma.

### Sin dato previo, ni forma de derivarlo

`cursos` no tenia ningun campo de profesor. Se penso primero en derivarlo de
`asignaciones`, pero esa tabla es materia-profesor-curso-horario, simetrica:
ninguna fila marca "este es el encargado del grupo", y adivinarlo (el primer
profesor asignado, o el de alguna materia en particular) no tiene sentido
semantico. Se opto por agregar una columna nueva a `cursos`, mismo patron ya
usado para `nivel` (`docs/funcionalidades/NIVEL_ACADEMICO.md`).

### Columna nueva

`cursos.director_grupo_id` (nullable, `REFERENCES profesor(id) ON DELETE SET
NULL`), migracion `20260915_cursos_director_grupo.sql`. Un curso sin director
de grupo se comporta exactamente igual que hoy.

### Boletin: mismo dato, dos caminos

`obtener_boletin_admin_controller` y `obtener_reporte_parcial_admin_controller`
usan lecturas de estudiante independientes
(`leer_datos_del_estudiante`/`leer_datos_basicos_del_estudiante`, con SQL
distinto a proposito, ver el docstring de `boletin_repository.py`). Se agrego
el mismo `LEFT JOIN profesor` a ambas, sin crear una consulta compartida
nueva. Cero consultas adicionales: es el mismo query con un JOIN mas.

### Detalle completo

`docs/funcionalidades/DIRECTOR_GRUPO.md` — diseño de datos, decisiones,
invariantes y el orden de despliegue obligatorio (la migracion debe aplicarse
a todos los tenants antes de publicar este codigo, igual que nivel
academico).

### Pruebas

`scripts/verify.py`: **1307 pasan** (subio de 1297; +11 nuevas: 7 en
`tests/test_curso_controlador.py`, 4 en `tests/test_boletin_caracterizacion.py`).
Ruff y `pip check` en verde. Una falla esperada:
`test_esquema_base.py::test_la_base_incorpora_todas_las_migraciones_de_tenant`,
la compuerta que exige aplicar la migracion real y regenerar el esquema base
antes de que quede en verde — no se fuerza a mano.

Nada commiteado ni publicado. La migracion no se aplico a Neon ni a ningun
tenant: queda pendiente para el usuario, siguiendo el mismo orden de
despliegue documentado para nivel academico.

## 2026-09-13 - Las evidencias del plan de clases aceptan PDF

Hasta hoy `POST /plan-de-clases` solo admitia imagenes. Un taller escaneado o
una guia en PDF rebotaban con `400`, y el profesor no tenia donde adjuntarlos.

### Sin columna nueva ni migracion

`imagen1` e `imagen2` no guardan una imagen: guardan la ruta de un archivo. El
almacenamiento ya es indiferente al tipo -`save_bytes` conserva el content type
y `/uploads` lo devuelve igual-, y el permiso se resuelve por ruta. Un PDF queda
tan protegido como una imagen sin tocar base de datos ni rutas.

Lo unico que lo impedia era la lista blanca de
`plan_de_clases_controller.guardar_imagen_plan`.

### Limites distintos por tipo

Imagen hasta 5MB, como siempre. PDF hasta 15MB, porque un taller escaneado pasa
de cinco con facilidad. El tope se elige segun el tipo declarado, no un unico
maximo para todo.

### Se verifica el contenido, no el nombre

Ampliar la puerta a PDF pide una defensa que antes no hacia falta: el archivo
debe empezar por `%PDF-`, la firma real del formato. Renombrar cualquier cosa a
`.pdf` ya no alcanza. Son cuatro lineas y cierran el hueco que abre el cambio.

### Mensajes de error

Decian "imagen" cuando ya no es solo imagen. Ahora dicen archivo:
`Tipo de archivo no permitido. Use imagen o PDF`,
`Extension de archivo no permitida` y `Archivo demasiado grande (max NMB)`.
El frontend los muestra tal cual, no los interpreta, asi que el cambio no rompe
ningun consumidor.

### Pruebas

`1297 pasan`, cuatro nuevas: PDF valido guardado bajo el directorio del tenant,
PDF con extension equivocada, PDF sobre el tope y archivo que miente sobre ser
PDF. `ruff` y `pip check`, en verde.

El conteo de lineas del dominio en `test_plan_de_clases_caracterizacion.py` sube
de 1365 a 1382 por las lineas nuevas del controlador.

## 2026-09-10 - Mes final configurable para mensualidades

Los conceptos mensuales dejan de tener diciembre codificado como cierre
obligatorio. `mes_final` fija el ultimo mes que puede generar deuda, aparecer
como cuota vencida o aceptarse como adelanto dentro del año lectivo.

### Capacidad para todos, calendario intacto por defecto

La migracion tenant `20260910_tipos_pagos_mes_final.sql` agrega
`mes_final SMALLINT NOT NULL DEFAULT 12` a `tipos_de_pagos`, rellena con `12`
las filas existentes y crea dos defensas en PostgreSQL: rango `1..12` y
`mes_final >= mes_inicial` cuando hay inicio y el concepto es `mensual`. Los
tipos `unico`, `anual` y `opcional` conservan sus reglas anteriores.

Esto **no pone noviembre en todos los colegios**. Los tenants operativos
recibiran la capacidad conservando diciembre cuando se aplique la migracion, y
el esquema base queda actualizado para que cualquier tenant nuevo nazca igual.
El cierre en noviembre de `tenant_2005` es un dato posterior: el administrador
debe guardar final `11` en su concepto de mensualidad y conservar el inicio y la
frecuencia institucionales que realmente correspondan.

### Una regla compartida por cartera y pagos

El servicio central de cobros transporta `mes_final` con fallback `12`. El
cálculo de deuda y cuotas vencidas se detiene al llegar al límite, incluida la
próxima fecha prevista. Las opciones de adelanto enumeran solo periodos
posteriores al actual y no mayores que el final; el registro vuelve a calcular
la misma lista dentro de su transacción, así que no confía en periodos del
cliente.

Cambiar el límite no elimina pagos ni aplicaciones históricas. Solo cambia qué
cuotas del calendario se calculan en adelante.

### Contrato y validación

`GET /tipos-pagos/detallado` y `GET /tipos-pagos/{id}/detalle` incluyen el
campo. `PUT /tipos-pagos/{id}/configuracion` acepta enteros `1..12` y comprueba
la pareja mensual enviada y la configuración efectiva con los valores ya
guardados. Para evitar carreras, bloquea la fila mientras combina tipo, inicio
y final; esto cubre también convertir un concepto existente a `mensual`. Un
rango incompatible responde `400` con
`El mes final no puede ser anterior al mes inicial.` cuando llega al dominio;
los valores fuera de `1..12` siguen la validación `422` de FastAPI.

Si el cliente intenta guardar el campo antes de aplicar la migración, recibe
`409` con el comando exacto de `apply_migration.py`; no se acepta el guardado en
silencio. Las lecturas sí usan diciembre como fallback para permitir un
despliegue gradual.

### Operación pendiente

Orden seguro: probar en una copia, revisar el `--dry-run`, aplicar por el
endpoint directo, repetir el `--dry-run`, desplegar backend, desplegar frontend
y solo entonces configurar `tenant_2005`. La guía y los comandos exactos están
en `docs/MIGRACIONES.md` y `migrations/README.md`.

En este cambio **no se ejecutó la migración**, no se abrió una conexión a Neon
y no se modificó ningún dato de un tenant. La actualización de `mes_final` a
noviembre en `tenant_2005` permanece como paso operativo posterior al
despliegue.

### Pruebas locales

Pasaron 128 pruebas enfocadas del dominio —configuración, cartera, cuotas
vencidas, adelantos y consumidores de reportes—. La compuerta completa terminó
con **1293 pruebas aprobadas** y 6 warnings preexistentes. Estas pruebas usan
dobles o bases locales de test; no constituyen evidencia de que la migración se
haya ejecutado en Neon o en producción.

## 2026-09-09 - Observador: la marca de positiva o negativa deja de pedirse

Decidido por el usuario. **Revierte la decision 8** de este documento, que era
una de las que pedia no reabrir; las tomo el y las puede cambiar. **Sin
migracion: la base de datos no se toca.**

### La columna se jubila, no se elimina

Igual que `materia`:

* sigue en la tabla y `GET /observador/{estudiante_id}` la sigue devolviendo, asi
  que volver atras seria cambiar solo la pantalla;
* `POST` ya no la acepta ni la escribe: la fila nace con `NULL`;
* **`PUT` ya no la toca.** Antes la sobrescribia en cada edicion, asi que
  corregir una tilde de una anotacion heredada obligaba a ponerle una marca que
  nunca tuvo. Ahora la fila conserva la suya.

En produccion hay **cuatro filas con marca**, todas de las pruebas del usuario, y
se quedan como estan.

### Un cliente sin actualizar no rompe nada

Pydantic ignora los campos que no declara, igual que con `profesor_id`. Un
frontend que siga mandando `positiva` recibe un `201` normal y el campo se
descarta. **Eso es lo que permite publicar el backend antes que la pantalla**,
que es el orden obligatorio en este proyecto. Hay prueba que lo fija.

### Un hueco de las pruebas, tapado

Las pruebas de escritura **construian** el esquema con `positiva` pero nunca
fijaron que fuera obligatoria ni que llegara a la base. Al quitarla, las 1275
siguieron pasando sin enterarse. Se anadieron tres que si fijan el
comportamiento nuevo, y se verificaron con mutaciones.

### Pruebas

`1278 pasan`, tres nuevas. `ruff` y `pip check`, en verde.

## 2026-09-09 - Observador: la lista de alumnos de un profesor

`GET /observador/mis-estudiantes`. **Solo lectura, sin migracion y sin tocar la
base de datos.** Autorizado por el usuario.

### Por que existe

La pantalla del observador exigia tener una asignacion elegida. El usuario
pregunto por que, si el observador no depende de la materia, y tenia razon en la
premisa: la anotacion no guarda nada de la materia. La asignacion solo servia
para **saber a que alumnos listar**, porque el unico endpoint que lo hacia era
`GET /planilla/{asignacion_id}`, que pide una clase.

Las dos salidas sin backend estaban descartadas:

* **Pedir las clases y luego los alumnos de cada una.** Con 6 cursos son 7 idas
  y vueltas, a ~180 ms cada una: reconstruir el N+1 justo en la pantalla que
  existe para matarlo.
* **`GET /estudiantes`.** Devuelve todos los ninos del colegio, sin filtrar por
  profesor.

### La misma regla que el guard, y no por casualidad

La consulta es el mismo `JOIN` que `_SQL_PROFESOR_COMPARTE_CURSO` de
`app/core/permissions.py`, el que decide si un profesor puede abrir la bitacora
de un nino. Si fueran distintas, la lista mentiria: mas ancha listaria alumnos
que al abrirlos dan 403, mas estrecha esconderia alumnos que si se pueden ver.
Hay prueba que compara las dos.

Consecuencia coherente: un alumno **sin curso** no aparece, porque el `JOIN` no
encuentra pareja. Tampoco se podria abrir su bitacora por esta puerta.

### El `DISTINCT` no es cosmetico

Un profesor puede tener varias asignaciones en el mismo curso -medido: el 73% de
los pares profesor-curso dan mas de una materia, y una profesora da 9 en
PRIMERO-A-. Sin `DISTINCT`, su curso entero saldria nueve veces.

Verificado contra la base real: EDGAR VILLANUEVA devuelve **81 alumnos y 81 ids
distintos**.

### El admin no tiene lista, y es deliberado

Su `id` sale de `usuarios`, no de `profesor`. Devolverle una lista no daria
error: daria los alumnos del profesor que por casualidad tenga ese mismo numero.
Es la misma trampa que ya documentaba `_profesor_que_escribe`, y en
`tenant_colegio_1` es real.

**No se le quita nada**: el admin sigue leyendo cualquier bitacora. Comprobado
contra el servidor real: `403` en la lista, `200` en `GET /observador/531`.

### La trampa del orden de las rutas

`/observador/mis-estudiantes` encaja tambien en el patron
`/observador/{estudiante_id}`, y Starlette prueba las rutas en el orden en que
se declaran. Declarada despues, FastAPI intenta convertir `"mis-estudiantes"` en
`int` y responde un **422** incomprensible.

No es teorico: se movio la ruta a proposito para comprobarlo y el 422 salio. Lo
fijan dos pruebas, una estructural y otra que pide la URL real por HTTP.

### Medido contra la base real, no estimado

Servidor local contra Neon (`us-east-1`), token acunado para EDGAR VILLANUEVA
-6 cursos, el peor caso de `tenant_2005`-:

| Peticion | Que devuelve | Tiempo |
|---|---|---|
| `GET /observador/mis-estudiantes` | **81 alumnos, 6 cursos** | **1,35 s** |
| `GET /planilla/212` (lo de hoy) | los de **una** clase | 2,0 - 3,3 s |

La lista nueva es **mas rapida que la que reemplaza y trae seis veces mas**. El
motivo es el numero de idas y vueltas: `/planilla` resuelve la asignacion
academica, corre su guard y calcula promedios; esta hace **una consulta y abre
una conexion**, porque el profesor sale del token y no hay nada que validar
contra la URL.

La consulta en si tarda 69 ms sobre 81 filas. Lo que se paga es el viaje, no la
consulta.

### Lo que sigue costando lo mismo

El sobrecoste de autenticacion -6 idas y vueltas por peticion- sigue ahi y sigue
fuera de alcance. Es lo que explica que 69 ms de consulta se conviertan en 1,35 s
de respuesta.

### Pruebas

`1275 pasan`. Doce nuevas en `tests/test_observador_mis_estudiantes.py`,
verificadas con mutaciones: quitar el `DISTINCT`, dar al admin el atajo de
siempre, y declarar la ruta estatica despues de la parametrizada. Las tres
rompen pruebas. `ruff` y `pip check`, en verde.

## 2026-09-08 - Observador unificado, fase 4: copiar lo viejo

Autorizada por el usuario. `scripts/copiar_observaciones_al_observador.py` lleva
las observaciones de la tabla vieja a la bitacora nueva. **`observaciones` no se
toca ni se borra**: el script solo lee de ella, y hay prueba que lo impide.

### Lo que se recupera y lo que no

De la fila vieja, a traves de su `asignacion_id`, se rescatan el **profesor** y
la **materia**. No quedan anonimas, y la materia es dato real que se habria
perdido: la pantalla no la muestra, pero capturarla ahora cuesta cero.

Dos cosas **no existen** en el modelo viejo y no se inventan:

* **La fecha.** `observaciones` nunca la guardo -sus columnas son id,
  estudiante_id, asignacion_id, periodo y los tres textos, comprobado en los dos
  tenants-. Va `NULL`, «no se sabe», y el `ORDER BY ... NULLS LAST` que la
  lectura ya tenia las manda al final, que es su sitio por ser las mas antiguas.
  Poner la fecha de la copia las haria parecer escritas hoy y las mezclaria
  arriba con las nuevas.
* **Si era positiva o negativa.** El modelo viejo no distinguia. Decidido con el
  usuario: **no se les inventa una marca**. Van con `positiva` en `NULL`. Solo
  las anotaciones nuevas la llevan, y ahi la sigue exigiendo el esquema de la
  API, asi que ningun registro nuevo puede nacer sin ella.

Por eso `20260908_observador_anotaciones_historicas.sql` quita el `NOT NULL` de
esas dos columnas. Las de identidad -estudiante, profesor, periodo- siguen
intactas.

### Repetir la copia no duplica

Cada anotacion heredada guarda de que fila salio, en `observacion_origen_id`,
con un `UNIQUE`. El `INSERT` lleva `ON CONFLICT DO NOTHING`. Era el riesgo que
el documento tenia anotado desde el diseno: ejecutar la copia dos veces
duplicaria el historial de un alumno.

Sirve ademas para reconocer una heredada sin adivinarlo por el hueco de la
fecha.

### Ensayado contra la base real, con rollback

| | `tenant_2005` | `tenant_colegio_1` |
|---|---|---|
| Observaciones viejas | 63 | 5 |
| Copiables | **63** | **5** |
| Descartadas | **0** | **0** |
| Materia recuperada | 63 | 5 |
| Profesores distintos | 7 | 1 |
| Al repetir la copia | 0 filas | 0 filas |

**Las 68 entran enteras**, ninguna se queda fuera. El endpoint las devuelve bien:
`SADAY JIMENEZ JULIO | PRE-ESCRITURA | P3 | positiva=None | creada_en=None`.
Tras el rollback, bitacora vacia y las viejas intactas.

El script informa de cada descarte por separado -sin estudiante, sin profesor,
periodo fuera de 1-4, las tres dimensiones vacias- para que 68 no puedan
convertirse en 60 en silencio.

### El texto heredado se copia tal cual

Sin pasarlo por la correccion de mayusculas. Lo que escribio una profesora hace
meses es historico: no se reescribe.

### Pruebas

`1262 pasan`. Diez nuevas. Una existente cambio de significado y se corrigio en
vez de dejarla mentir: `test_las_columnas_de_identidad_no_admiten_nulos`
incluia `positiva`, que nacio `NOT NULL` y dejo de serlo hoy. Se saco de la
lista con el motivo escrito, y se anadio la prueba que fija el cambio.

## 2026-09-08 - Observador unificado, fase 3: escribir y editar

`POST /observador` y `PUT /observador/{anotacion_id}`. Con esto **el backend de
la funcionalidad esta completo**. Sigue sin haber pantalla, asi que la bitacora
esta vacia y los profesores siguen usando la vieja: el fallo original sigue
vivo y lo cierra el frontend, no esto.

### El admin no crea, y esto corrigio una contradiccion del diseno

El documento decia dos cosas: su tabla de permisos daba a crear el mismo alcance
que a leer -lo que incluye al admin- y su tabla de API decia «profesor del
alumno». Se resolvio a favor de la segunda, con motivo:

**el `id` de un admin sale de la tabla `usuarios`, no de `profesor`.** Usarlo
como autor firmaria la anotacion con el profesor que por casualidad tenga ese
mismo numero. Se comprobo antes de decidir: en `tenant_colegio_1` la
administradora **maristella polo** tiene `usuarios.id = 1` y el profesor 1 es
**SINDY PAOLA VERGARA**. La anotacion habria quedado a nombre de Sindy Paola,
sin error, sin aviso y sin forma de notarlo despues.

Una bitacora que atribuye a alguien lo que no escribio no sirve para lo unico
que justifica su existencia. Lo impide `_profesor_que_escribe`, con prueba.

Se suma al invariante 3, que ya prohibia al admin **editar** lo de un profesor.
Ese sigue siendo una excepcion deliberada a la norma del proyecto -casi todos
los guards empiezan con `if rol == "admin": return`- y tiene su propia prueba,
que el documento pedia explicitamente.

### La autoria se comprueba en la sentencia que escribe

`UPDATE ... WHERE id = %s AND profesor_id = %s`. No hay un `SELECT` previo que
compruebe y luego un `UPDATE` que escriba: es la misma sentencia, sin ventana
entre las dos cosas, y el camino normal cuesta **una sola consulta**.

Cuando no actualiza nada se paga una segunda, **solo en el camino de error**,
para no decir «no es tuya» de algo que no existe ni «no existe» de algo que si.
De ahi que haya `403` y `404` distintos.

`editada_en` y `editada_por` se fijan en esa misma sentencia, no en el codigo
que la llama: el rastro no depende de que alguien se acuerde. Es el invariante 2.

### El texto se guarda ya corregido

Decidido con el usuario. `app/core/texto_observador.py` pone mayuscula en la
primera letra y despues de `.`, `?` y `!` -no despues de `,`, `;` ni `:`-,
colapsa espacios y anade el que falta tras el punto.

Vive en el servidor **ademas de** en el frontend: alli es comodidad, aqui es la
garantia. La profesora ve la correccion al salir del campo y puede rehacerla,
asi que lo que aprueba con los ojos es lo que queda escrito y lo que se imprime.

Dos detalles que costaron una vuelta:

- **`¿por que?` se quedaba en minuscula.** La primera letra no siempre es el
  primer caracter: en castellano la frase abre con `¿` o `¡`. Se corrigio
  buscando la primera letra, no el primer caracter, y lo mismo tras cada punto.
- **`mide 1.75 metros` no se toca.** El espacio tras el punto solo se anade si
  lo que sigue empieza frase de verdad, no si es un digito.

Defecto conocido y aceptado: `etc. y luego` -> `etc. Y luego`. Es raro en una
observacion, todos los sistemas que hacen esto lo tienen, y se ve en pantalla
antes de guardar.

### Probado de extremo a extremo contra la base real

Dentro de una transaccion deshecha al final, con un caso real de `tenant_2005`
-MARIA VICTORIA, de TRANSICION-A, preescolar-:

| Comprobacion | Resultado |
|---|---|
| La profesora crea una anotacion | OK |
| El admin NO puede crear | `403` |
| **La misma profesora anota otra vez en el mismo periodo** | OK, y quedan las dos |
| Leer de vuelta | 2 anotaciones, la mas nueva primero, `nivel='preescolar'` |
| El texto quedo corregido | `Se para mucho. Hace desorden` |
| Filtrar por un periodo vacio | 0 anotaciones y **el nivel sigue llegando** |
| La autora edita la suya | OK |
| El ADMIN edita lo de la profesora | `403` |
| Otro profesor edita lo ajeno | `403` |
| Editar una que no existe | `404` |
| El rastro | `editada_en` con fecha, `editada_por = 40` |

Tras el rollback, cero filas en los dos tenants.

La tercera fila es la que cierra el motivo de todo esto: **la tabla vieja no
podia hacerlo**. Su `UNIQUE (estudiante_id, asignacion_id, periodo)` y su
`UPSERT` hacian que el segundo guardado borrara el primero.

### Pruebas

`1252 pasan`. Veintinueve nuevas en `tests/test_observador_escritura.py`,
verificadas con mutaciones: meter el atajo de admin, quitar el rastro de
edicion, sacar la autoria del `WHERE`, convertir el `INSERT` en `UPSERT`, quitar
la correccion de mayusculas, quitar el rango del periodo, permitir la anotacion
vacia y confundir el `404` con el `403`. Todas cayeron.

Se borro `test_no_existe_ninguna_forma_de_borrar_una_anotacion` de
`test_observador_lectura.py`: afirmaba que el router era «solo lectura» y quedo
obsoleta al aparecer el `POST`. El invariante 1 -nadie borra- lo fija ahora
`test_no_existe_endpoint_de_borrado`, en el archivo de escritura, que ademas
comprueba que el repositorio no sabe borrar.

### Qué cambia para el cliente

Dos rutas nuevas. Ninguna existente cambia.

## 2026-09-08 - La materia del observador no se rellena, y el porque

Cambio de decision el mismo dia en que se creo la columna. Se registra entero
porque el recorrido vale mas que la conclusion, y porque deja una columna vacia
en la base que alguien podria confundir con un descuido.

**No lo es.** `observador_anotaciones.materia` existe, esta migrada en los dos
tenants y se queda **vacia a proposito**.

### Lo que la tumbo fue una medicion

Para etiquetar una anotacion con su materia hay que saber cual es. Se midio si
el servidor podia deducirla a partir del profesor y el alumno:

| Materias que da un profesor en un mismo curso | `tenant_2005` | `tenant_colegio_1` |
|---|---|---|
| Una sola, deducible | 9 casos, **27%** | 1 caso, **25%** |
| Varias, ambiguo | 24 casos, **73%** | 3 casos, **75%** |

LILIANA da **9** materias en PRIMERO-A. ANGELICA, **5** en JARDIN-B. No es un
caso de borde: es la norma. **El servidor no puede deducirla**, y no es cuestion
de programarlo mejor.

### Las dos salidas, y por que se descartaron las dos

- **Que la profesora elija** la materia al guardar: friccion en cada anotacion,
  para un dato secundario.
- **Deducirla de la asignacion desde la que entra** —su planilla de
  Matematicas—: sin friccion, pero **ata la pagina a una unica puerta de
  entrada**. El observador dejaria de poder abrirse desde un listado de alumnos,
  y esa puerta todavia no esta decidida.

Decision del usuario: **ninguna de las dos, por ahora**. La pantalla mostrara el
nivel del curso en el titulo -«Pepito · Primaria»- y las anotaciones iran solo
con profesora, fecha y periodo.

### Consecuencias, dichas claro

- **No queda registrado en que clase paso.** Se acepto a conciencia; el nombre
  de la profesora sigue diciendo quien observo.
- El `POST` de la fase 3 **no recibe `asignacion_id` ni `materia`**. Eso lo
  simplifica: le basta `require_estudiante_access`, el mismo guard de la
  lectura.
- La columna se conserva. Quitarla exigiria otra migracion y no gana nada;
  dejarla cuesta cero y queda lista si algun dia se decide usarla.
- `GET /observador/{estudiante_id}` **sigue devolviendo `materia`** en cada
  anotacion, con la cadena vacia. Es el valor real de la fila, no un adorno: la
  respuesta no miente sobre lo que hay guardado.
- Lo que **si** se aprovecha es el `nivel` anadido antes: ahora es lo unico que
  la pantalla pone tras el nombre del alumno, asi que aquel trabajo no se tira.

### Codigo

Ninguno. Nada que revertir: la escritura todavia no existe, asi que no habia una
sola linea que rellenara la columna. `1224 pasan`, sin cambios en pruebas.

## 2026-09-08 - La lectura del observador devuelve el nivel del curso

Añadido justo después de cerrar la fase 2, por una decisión de presentación: la
pantalla mostrará la materia **según el nivel** —preescolar la omite y dice el
nivel una vez en el título, primaria la lleva en cápsula, y un curso **sin
nivel** se comporta como primaria—. El detalle vive en el documento de frontend.

### La consulta arranca en `estudiantes`, y ese es todo el cambio

Antes arrancaba en `observador_anotaciones`. Ahora:

```sql
FROM estudiantes e
LEFT JOIN cursos c ON c.id = e.curso_id
LEFT JOIN observador_anotaciones a ON a.estudiante_id = e.id
                                  [AND a.periodo = %s]
LEFT JOIN profesor p ON p.id = a.profesor_id
WHERE e.id = %s
```

Tres trampas, las tres reales, las tres con prueba y mutación:

1. **Un alumno sin anotaciones.** Arrancando en las anotaciones devolvería cero
   filas y con ellas ningún nivel: la pantalla no podría ni escribir su título.
   No es un caso raro — **hoy es el caso de todos los alumnos**, porque la
   escritura no existe.
2. **`estudiantes.curso_id` es nulable**, comprobado en `information_schema`.
   Con unión interna a `cursos`, un alumno sin curso desaparecería de su propia
   bitácora: sin error y sin aviso.
3. **El filtro de periodo va en el `ON`, no en el `WHERE`.** En el `WHERE`
   descartaría también la fila del estudiante cuando ese periodo no tuviera
   anotaciones, y cambiar de periodo dejaría la pantalla sin nivel.

Las dos uniones nuevas **no cuestan idas y vueltas**: sigue siendo una sola
consulta, y hay prueba que cuenta las sentencias para que siga siéndolo.

### La respuesta cambia de forma, y el `404` es nuevo

De una lista a `{"nivel": ..., "anotaciones": [...]}`. El nivel va fuera porque
es del alumno, no de cada anotación, y sobre todo **porque tiene que llegar
aunque no haya ninguna**. No rompe a nadie: todavía no hay cliente.

Cero filas solo puede significar que el estudiante no existe, así que la ruta
responde `404`. Un alumno real sin anotaciones trae una fila de relleno con el
nivel y el resto en `NULL`, que la ruta descarta. La diferencia importa: en
pantalla, «no existe» y «todavía nadie le ha escrito» son mensajes distintos.

`leer_anotaciones` pasa a llamarse `leer_bitacora`: ya no devuelve solo
anotaciones.

### Medido contra la base real

Con casos reales de `tenant_2005`, ambos con la bitácora vacía:

| Caso | Tiempo | Resultado |
|---|---|---|
| Alumno de PARVULO (preescolar), todos los periodos | 1374 ms (abre conexión) | `nivel='preescolar'`, 0 anotaciones |
| El mismo, filtrando por periodo 3 | 618 ms | `nivel='preescolar'`, 0 anotaciones |
| Alumno de PRIMERO-A (primaria) | 607 ms | `nivel='primaria'`, 0 anotaciones |
| Estudiante inexistente, como admin | 529 ms | `404` |

La segunda fila es la que importa: **el nivel llega con el filtro de periodo
puesto y sin ninguna anotación**, que es justo lo que la trampa 3 rompía.

El camino del alumno **sin curso** no lo cubre ningún dato real —no hay ninguno
en ese tenant—, así que se protege fijando en una prueba que las uniones sean
`LEFT`. Es la regresión probable: alguien reordena la consulta y borra la
palabra.

### Pruebas

`1224 pasan`. Veintiuna en `tests/test_observador_lectura.py`, siete más que
antes. Verificadas con mutaciones: mover el filtro de periodo al `WHERE`, quitar
el `404`, dejar pasar la fila de relleno, perder el nivel y convertir cada
`LEFT JOIN` en interna. Todas cayeron.

## 2026-09-08 - Observador unificado, fase 2: la lectura

`GET /observador/{estudiante_id}` devuelve la bitácora completa de un alumno.
**Solo lectura**: no hay `POST` ni `PUT` todavía, y `DELETE` no existirá nunca.
La pantalla vieja no se toca y sigue siendo la única que los profesores usan.

### Una consulta y una conexión, que es el punto

La pantalla vieja hace **una petición HTTP por alumno**: con 12 tarda 16-20 s y
el frontend aborta a los 10 s. Aquí se abre **un** estudiante y su bitácora
entera sale de **una consulta**, con el guard corriendo sobre el mismo cursor
que después lee. El N+1 desaparece por diseño, no por optimización.

Hay dos pruebas que lo fijan por aserción y no por comentario: que se pide una
sola conexión al pool y que los guards no abren la suya. Si alguien vuelve a
partirlo en dos consultas, fallan.

### `require_estudiante_access` acepta `cursor=`

Replica lo que la optimización del 2026-09-03 hizo con `require_asignacion_access`
y `require_estudiante_in_asignacion`. Sin `cursor` conserva el comportamiento
histórico, así que los tres llamadores de `app/routes/notas.py` no cambian y sus
pruebas siguen pasando sin tocarlas.

Prestar el cursor **no relaja el permiso**: misma consulta, mismos parámetros,
mismo 403.

### La materia: una contradicción entre los dos documentos

El documento de frontend dibuja «Prof. Ana · Matemáticas · 20/mar». El de
backend había quitado la materia de la tabla. Nadie lo había cruzado. Decidido
con el usuario: la anotación **sí** dice de qué materia era.

`migrations/20260908_observador_anotaciones_materia.sql` añade la columna. Va
aparte porque la primera migración ya estaba aplicada y el runner bloquea un
archivo cuyo checksum cambie.

Es **texto copiado**, no una clave foránea a `materias(id)`: un vínculo
reintroduciría el defecto que esta tabla vino a corregir —quitar la materia del
horario se llevaría el dato— y además obligaría a una unión más en cada lectura.

Nadie la rellena todavía: eso es la fase 3, y **de dónde sale al guardar sigue
sin decidirse**. Queda como pregunta abierta que bloquea esa fase.

### Seis censos que había que actualizar a mano

El repositorio nuevo hizo fallar siete pruebas, y todas tenían razón:

- cinco enumeran el conjunto exacto de repositorios (`asistencia`, `dashboard`,
  `notas`, `planilla`, `ventas`), a propósito, para que ninguno se cuele sin
  reconocerse;
- una enumera los archivos que tocan la tabla `profesor` por SQL directo. El
  repositorio nuevo la une **solo** para el nombre que muestra la bitácora, en
  la misma consulta de lectura;
- `test_esquema_base` pide regenerar el archivo base tras la migración nueva.

Ninguna se relajó: todas se actualizaron declarando la pieza nueva.

### Pruebas

`1216 pasan` con la migración de `materia` aplicada. Catorce nuevas en
`tests/test_observador_lectura.py`, verificadas con mutaciones: quitar el
`except HTTPException`, dar al guard su propia conexión, filtrar el error de
PostgreSQL al cliente, quitar el desempate del orden y filtrar siempre por
periodo. Las cinco cayeron.

Una sexta mutación —aceptar la cadena vacía en el apellido— **no** cayó, y eso
destapó un hueco real: la prueba cubría el apellido nulo pero no el vacío. Se
amplió a los dos casos y entonces sí cae.

### Medido contra la base real, no estimado

Ejecutando la funcion de la ruta contra Neon con un caso real de `tenant_2005`
—profesor 40, estudiante 518—, con la bitacora todavia vacia:

| Llamada | Tiempo |
|---|---|
| Profesor del alumno, todos los periodos (primera, abre conexion) | 1147 ms |
| El mismo, filtrando por periodo | 593 ms |
| Admin, sin compartir curso | 445 ms |
| Rol no autorizado, `403` | 412 ms |

Los ~450-600 ms en caliente son el suelo de este proyecto: arranque de conexion
mas dos o tres idas y vueltas a ~180 ms cada una.

**La medicion NO incluye el sobrecoste de autenticacion**, porque llama a la
funcion de la ruta y no pasa por `get_current_user`. Una peticion HTTP real suma
las 6 idas y vueltas documentadas el 2026-09-03, o sea alrededor de 1,1 s mas.
Eso sigue siendo un defecto transversal, con su propio alcance, y esta
funcionalidad no lo toca.

Aun asi la comparacion decide: la pantalla vieja hace **12 peticiones** de ~2,8 s
para un curso y suma 16-20 s. Esta hace **una**. Lo que cambia no es el precio de
cada peticion sino cuantas hay, que era la conclusion de la medicion del
2026-09-03.

### El JOIN es interno a propósito

`profesor_id` es `NOT NULL` y su clave foránea no lleva `ON DELETE CASCADE` ni
`SET NULL`, así que PostgreSQL **impide** borrar un profesor con anotaciones. La
fila siempre existe. Dar de baja a un profesor en esta aplicación es cambiarle
el `estado`, no borrarlo, y eso no afecta a nada de aquí.

### Qué cambia para el cliente

Una ruta nueva. Ninguna existente cambia de comportamiento, código de estado ni
cuerpo.

## 2026-09-08 - Observador unificado, fase 1: la tabla existe y nadie la usa

Estructura y nada más. Se crea `observador_anotaciones` en los dos tenants
operativos. **No hay endpoint ni pantalla**: nada lee ni escribe esa tabla, y la
pantalla vieja del observador sigue siendo la única que los profesores usan. El
fallo «No pudimos recuperar la observación guardada» **sigue vivo**: lo cierra la
fase 2, no esta.

Diseño completo y decisiones en `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`.

### Qué se creó

`migrations/20260908_observador_anotaciones.sql`, aplicada con el runner:

| Tenant | Migración | Índice | Filas | `observaciones` (vieja) |
|---|---|---|---|---|
| `tenant_colegio_1` | OK | OK | 0 | 5, intacta |
| `tenant_2005` | OK | OK | 0 | 63, intacta |

La tabla vieja no se tocó y **no se toca**: se jubila cuando lo nuevo funcione,
y ni entonces se borra.

### El índice va en el script, no en la migración

El plan decía crearlo en la migración **y** en `scripts/apply_tenant_indexes.py`.
Se comprobó contra la base antes de hacerlo y habría creado un duplicado en cada
tenant: el script antepone el nombre del schema (`f"{schema}_{index_name}"`), así
que no habría reconocido el `idx_...` de la migración —`CREATE INDEX IF NOT
EXISTS` compara por **nombre**, no por definición— y habría creado otro idéntico
al lado.

No es hipotético. `tenant_2005` ya arrastra tres pares duplicados por esa causa:

```
asistencia_estudiante_id_fecha_idx      +  tenant_2005_idx_asistencia_estudiante_fecha
asistencia_asignacion_id_periodo_idx    +  tenant_2005_idx_asistencia_asignacion_periodo
estudiantes_curso_id_idx                +  tenant_2005_idx_estudiantes_curso_id
```

Decidido con el usuario: el índice lo crea **solo** `apply_tenant_indexes.py`, y
el archivo base lo hereda al regenerarse. La tabla nueva queda con exactamente
dos índices por tenant —su clave primaria y el suyo—, sin duplicados.

Queda anotado como **deuda, sin prisa**: el prefijo por schema de
`apply_tenant_indexes.py` es lo que produce esos duplicados, y los tres pares de
`tenant_2005` siguen ahí. Limpiarlos exige su propio alcance.

### Lo que se midió antes de tocar producción

Ensayo en los dos tenants: crear tabla e índice dentro de una transacción y
deshacerla. Confirmó que las claves foráneas resuelven contra `estudiantes` y
`profesor`, que no hay `CASCADE` ni `UNIQUE`, y que un `periodo = 99` rebota. Al
terminar, la tabla no existía en ningún schema.

No se usó una rama de Neon, que es lo que pide `docs/MIGRACIONES.md` paso 2. Para
una migración puramente aditiva el ensayo transaccional cubrió lo mismo. Si
alguna vez la migración altera datos, la rama deja de ser opcional.

### Pruebas

`1199 pasan`. Nueve nuevas en `tests/test_migracion_observador_anotaciones.py`,
verificadas con mutaciones —meter `CASCADE`, quitar un `NOT NULL`, aflojar el
`CHECK`, meter `UNIQUE`, meter `asignacion_id`, meter el índice en la
migración—: las seis cayeron, cada una en una sola prueba.

Una existente cambió: `test_ddl_fija_unicidad_estado_y_tres_referencias_externas`
contaba las referencias a `profesor(id)` en el archivo base y exigía 3. La tabla
nueva añade dos —el autor y quien editó—, así que son 5. Se actualizó declarando
las dos nuevas explícitamente, no solo subiendo el número, porque el valor de esa
prueba no es el número sino obligar a mirar cada referencia nueva y decidir a
propósito si arrastra borrados. Las dos nuevas **no** llevan `ON DELETE CASCADE`.
Renombrada a `test_ddl_fija_unicidad_estado_y_las_referencias_externas`, que no
envejece con la siguiente tabla.

### Tropiezo operativo, por si vuelve

`apply_migration.py` **se niega** sobre el endpoint agrupado de Neon
(`-pooler`), que es justo el que trae `.env`: allí su cerrojo de sesión no impide
dos ejecuciones simultáneas. Hay que apuntar `DATABASE_URL` al endpoint directo
—el mismo host sin `-pooler`— solo para ese comando. Está en
`docs/MIGRACIONES.md`, pero se olvida.

### Qué cambia para el cliente

**Nada.** Ni una ruta, ni un código de estado, ni un cuerpo de respuesta. La
tabla nace vacía y ningún camino de código la menciona.

## 2026-09-03 - Lectura de observaciones: una conexión en vez de tres, y caché de columnas

Trabajo previo al arreglo del observador del estudiante. **No lo cierra**, y el
apartado final explica por qué se registra igual.

Origen: el observador mostraba «No pudimos recuperar la observación guardada» en
el perfil de profesor. El mensaje viene del frontend, que aborta la petición a
los **10 segundos** (`useObservacionEstudiante.js`), así que no indicaba un
fallo del backend sino una respuesta que llegaba tarde.

### Lo que se midió, antes de tocar nada

Contra la base real (Neon, `us-east-1`) desde un backend local, y contra el
endpoint autenticado real con un token acuñado para el caso reportado
—`PARVULO`/`ARTÍSTICA`, asignación 131, 12 estudiantes, periodo 3—:

| Medición | Resultado |
|---|---|
| Abrir una conexión nueva (TLS + auth) | **1329 ms** |
| Una ida y vuelta cualquiera (`SELECT 1`) | **~180 ms** |
| `information_schema.columns` | **178 ms** |
| `GET /observaciones/...` una sola | **2,4 – 2,8 s** |
| Las 12 del curso **en paralelo** | **14,4 – 20,3 s**, todas con `http=200` |
| Las 12 **en una sola consulta** | **162 ms** |

Tres conclusiones, todas con evidencia:

1. **El endpoint no falla: llega tarde.** Las doce respuestas fueron `200`. El
   frontend se rinde a los 10 s y muestra el aviso.
2. **El coste no está en las consultas sino en su número.** Una lectura hacía
   **17 idas y vueltas** y solo **2** leían datos del dominio. Las otras 15 son
   validación de identidad y arranque de conexión. A ~180 ms cada una, el suelo
   eran ~3 s por estudiante.
3. **Ninguna consulta es lenta por sí misma.** `information_schema.columns`
   tarda lo mismo que `SELECT 1`. Lo que pesa es la distancia a la base, no el
   plan de ejecución.

El reparto de las 17 idas y vueltas, por si vuelve a hacer falta:

| Paso | Conexiones | Consultas |
|---|---|---|
| `ensure_tenant_allowed_for_app` | 1 | 3 |
| `_validar_usuario_en_bd` | 1 | 4 |
| `require_asignacion_access` | 1 | 3 |
| `require_estudiante_in_asignacion` | 1 | 3 |
| `get_cursor` + resolver + lectura | 1 | 4 |
| **Total** | **5** | **17** |

Cada apertura de conexión cuesta además dos consultas de arranque —`SET
search_path` y `set_config` de los timeouts— antes de la útil.

### Lo que cambió

- **`app/dependencies.py`**: `_columnas_tabla` cachea el resultado por
  `(schema del tenant, tabla)`. Se ejecutaba en **cada petición autenticada de
  toda la API**. La clave incluye el tenant porque dos colegios pueden ir con
  distinto nivel de migraciones; sin eso, el primero en pasar decidiría qué
  columnas cree tener el otro. Ahorra **una ida y vuelta (~180 ms) por
  petición**, no más: el comentario del módulo deja escrita la medición porque
  su primera versión afirmaba que esa vista era «de las lecturas más caras de
  PostgreSQL», que sonaba plausible y era **falso**. Se añade
  `limpiar_cache_columnas()` para migraciones en caliente; un despliegue
  reinicia el proceso y vacía el caché solo.
- **`app/core/permissions.py`**: `require_estudiante_in_asignacion` acepta
  `cursor=` opcional, replicando el que `require_asignacion_access` ya tenía.
  Sin él conserva el comportamiento histórico, así que los demás llamadores
  —`app/routes/boletines.py` y el `POST` de observaciones— no cambian.
- **`app/routes/observaciones.py`**: el `GET` corre los dos guards sobre el
  cursor que ya abre para leer. Pasa de **3 conexiones y 10 consultas a 1 y 6**.

### Qué cambia para el cliente

Nada observable. Mismos códigos de estado, mismo cuerpo, mismos mensajes. Lo
único que cambia es cuántas conexiones pide el proceso al pool.

Un matiz registrado: los guards ahora viven **dentro** del `try`, así que lo que
lancen y no sea `HTTPException` sale como 500 con su constante en vez de subir
crudo. Los guards reales solo lanzan `HTTPException` —y sigue saliendo con su
propio status, hay prueba—, así que en producción no cambia nada; un fallo de
base dentro de un guard ahora sale mejor formado, con `{"detail": ...}` y su
traza en el log.

Segundo matiz: si un guard deniega, el cursor **sí** se abre antes. No cuesta una
conexión de más, porque antes el propio guard abría la suya para consultar.

### Pruebas

`1190 pasan`. Tres se reescribieron a propósito y conviene saber por qué:

- `test_los_guards_se_evaluan_antes_de_abrir_el_cursor_en_la_lectura` fijaba el
  **orden textual** del código. Ese alambre hizo su trabajo: obligó a verificar
  qué protegía de verdad. No era el orden de las líneas sino dos garantías, y
  las dos se fijan ahora **por comportamiento**: que nada del dominio se lee sin
  permiso, y que **un 403 de un guard no se convierte en 500**. Comprobar el
  orden del texto ya no serviría: las tres llamadas viven en el mismo bloque.
- `test_obtener_observacion_no_consulta_si_el_guard_rechaza` usaba
  `PermissionError` como doble. Ningún guard lanza eso; los reales lanzan
  `HTTPException`. Se cambió al tipo real.
- Se añaden cuatro pruebas del caché, verificadas con una mutación —desactivando
  el caché a mano— para confirmar que fallan cuando deben y no pasan por vacías.

### Lo que NO se arregló, y es lo importante

**El aviso sigue saliendo.** Medido después del cambio: una lectura baja de
~3,1 s a ~2,8 s, un 10%. Con 12 alumnos en paralelo sigue en **16-20 s**.

La causa raíz no es el precio de cada petición sino **su cantidad**: el
observador hace **una petición HTTP por estudiante**. Es un N+1 sobre HTTP, y no
se corrige optimizando el 1.

Peor aún, el sistema quedó **justo encima de la raya de los 10 s**, y de qué lado
cae depende de la red en ese instante. Medido:

| En paralelo | Tiempo | ¿Pasa el límite de 10 s? |
|---|---|---|
| 1 | 2,8 s | sí |
| 2 | 8,1 – 9,7 s | sí, **por 0,3 s** |
| 3 | 11,2 – 14,7 s | no |
| 4 | 6,3 – 8,0 s | sí |
| 6 | 10,3 – 12,4 s | no |
| 12 | 16,2 – 20,1 s | no |

Que **4 en paralelo salga más rápido que 2** es el dato que más importa de esa
tabla: significa que manda la variación de la red, no la concurrencia. Un fallo
intermitente se da por cerrado y vuelve.

**No subir el timeout del frontend.** Cambiaría «sale un error» por «la página
tarda 20 segundos», que es peor: el profesor no sabe si está rota.

### Trabajo pendiente, no autorizado

- **Endpoint por asignación y periodo** que devuelva el curso entero:
  `GET /observaciones/{asignacion_id}/{periodo}`. Medido: **162 ms** la consulta.
  De 12 peticiones a 1, de ~20 s a ~2 s, y deja de crecer con el número de
  alumnos. No choca con la ruta actual: esa tiene tres segmentos, esta dos.
  Exige cambio de frontend a la vez —subir la carga a `ObservacionesPage`— y su
  propia orden. **Antes de diseñarlo hay que saber si el cambio previsto en
  observaciones altera qué dimensiones existen**; hoy son tres columnas fijas.
- **Sobrecoste de autenticación, que paga toda la API**: `ensure_tenant_allowed_for_app`
  y `_validar_usuario_en_bd` gastan **6 idas y vueltas y 2 conexiones por
  petición** solo en confirmar identidad. Es un defecto propio, ajeno a este
  dominio, y tocar autenticación exige su propio alcance.
- **`DB_POOL_MIN_CONNECTIONS` está en 1** y abrir una conexión cuesta 1329 ms,
  así que la primera ráfaga paga ese peaje en cascada. Subirlo es una línea, pero
  cambia el consumo de conexiones en Neon y merece decidirse aparte.

## 2026-08-27 - Endpoint de salud para monitoreo externo

- Se agregó `GET /health`, público y sin autenticación, porque un monitor
  externo no puede iniciar sesión. Es la única ruta abierta además de `login`.
- Responde `200` con `{"status": "ok", "database": "ok"}` cuando la API vive y
  PostgreSQL contesta, y `503` con `{"status": "degraded", "database": "error"}`
  cuando la base falla. Un monitor alerta ante cualquier código distinto de
  `200`, así que el aviso no necesita configuración adicional.
- El chequeo abre una conexión del pool, fija el tenant en `public` y ejecuta
  `SELECT 1`. No toca ningún schema de colegio ni cuenta filas.
- Cubre de una vez los dos fallos que dejan el sistema inservible aunque el
  proceso siga vivo: base inaccesible y pool agotado. `ThreadedConnectionPool`
  lanza `PoolError` en vez de esperar, así que `connection pool exhausted` —el
  incidente ya documentado en producción— llega al chequeo como excepción y
  activa la alerta.
- La respuesta no incluye versión, host ni detalle del error. El mensaje de
  `psycopg2` revela DSN y nombres internos, así que va solo al log del servidor
  con `logger.exception`.
- La ruta lleva límite explícito de `60/minute`. Es necesario porque el
  `default_limits=["100/minute"]` del limitador de `app/main.py` **no se está
  aplicando**: `slowapi` lo exige a través de `SlowAPIMiddleware`, que la app no
  monta, de modo que hoy solo quedan limitados los endpoints decorados. Ver el
  riesgo registrado más abajo.
- Archivos nuevos: `app/core/health.py` con el chequeo y `app/routes/health.py`
  con la ruta. El router se registra primero en `app/main.py` por ser
  infraestructura y no un dominio del colegio.
- No se agregaron columnas, tablas ni migraciones. No se modificó ningún
  endpoint existente.

Aviso operativo:

- **No usar `/health` como `Health Check Path` de Render.** Render reinicia el
  servicio cuando ese chequeo falla, así que un bache de la base provocaría
  reinicios en cadena y agravaría la caída. La ruta es para el monitor externo;
  el chequeo de la plataforma debe quedar vacío.

Riesgo detectado y no corregido:

- `default_limits=["100/minute"]` en `app/main.py` es inerte por falta de
  `SlowAPIMiddleware`. Hoy solo `POST /login` (`5/minute`) y `GET /health`
  (`60/minute`) están limitados de verdad; el resto de la API no tiene límite.
  No se corrigió aquí porque cambia el comportamiento observable de 139
  endpoints y excede el alcance de este cambio.

Verificación:

- 12 pruebas nuevas en `tests/test_health.py`, correctas. Cubren los dos status
  codes, el pool agotado, la ausencia de dependencias de autenticación, que el
  detalle del error no llegue al cuerpo pero sí al log, que la conexión vuelva
  al pool aunque la consulta falle y que el `ContextVar` del tenant quede
  restaurado.
- Compuerta global `python scripts/verify.py`: **1141 pruebas correctas**, Ruff
  correcto y `pip check` correcto, exit 0.
- `git diff --check` correcto.
- Sin PostgreSQL real: como el resto de la suite, la capa de datos va con
  dobles. La verificación contra la base queda para el despliegue.

## 2026-08-03 - Reporte académico parcial desde la planilla vigente

- Se agregó `GET /boletines/admin/reporte-parcial/{estudiante_id}/{periodo}`
  bajo la misma protección de administrador activo de los certificados.
- El endpoint consulta directamente `notas_detalle`; no usa ni prioriza
  `boletin_cabecera`, por lo que refleja cambios de la planilla incluso después
  de un envío anterior del boletín.
- Cada detalle conserva `descripcion`, nota, tipo de evaluación y valoración.
  La definitiva informativa se calcula únicamente con notas numéricas mayores
  que cero.
- No se modificó `/boletines/admin/generar`: el certificado y boletín oficial
  conservan su contrato anterior.
- No se agregaron tablas ni migraciones.

Verificación:

- 3 pruebas nuevas del controlador y la ruta correctas.
- Ruff correcto en controlador, ruta y pruebas.
- Suite completa fuera del sandbox: 189 pruebas correctas y 3 fallos
  preexistentes de Super Admin, cuyas fechas fijas de junio/julio de 2026 se
  evalúan como suspendidas frente a la fecha actual. No corresponden a
  boletines ni a este cambio.

## 2026-07-25 - Control de versión en el guardado del profesor

- `POST /plan-de-clases` acepta `version_esperada` en el multipart: `0` indica
  que el profesor abrió una fecha sin plan y un valor mayor que cero identifica
  la `version_revision` que cargó antes de editar.
- La versión se comprueba con bloqueo de fila dentro de la misma transacción
  del `UPSERT`. Si otra pestaña o dispositivo guardó primero, no se modifica el
  plan y se responde `409` con `version_actual`.
- La condición del `ON CONFLICT` también protege dos creaciones simultáneas
  para la misma asignación y fecha, incluso cuando ambas consultas iniciales
  todavía observaban la fecha vacía.
- Los clientes antiguos pueden omitir temporalmente `version_esperada` para
  mantener compatibilidad; el frontend del profesor ya lo envía siempre.
- Si el guardado es rechazado o falla después de subir imágenes nuevas, esos
  archivos se eliminan para no dejar evidencias huérfanas.
- El mensaje de éxito de planes ya revisados aclara que los cambios se
  guardaron conservando la revisión.
- No se agregaron columnas, tablas ni migraciones.

Verificación:

- Ruff correcto en rutas, controlador, servicio, repositorio, esquema y
  pruebas modificadas.
- 26 pruebas enfocadas de integridad y revisión correctas.

## 2026-07-24 - Ediciones de planes revisados no reabren la bandeja

- Cuando una planeación ya está en `revisado`, un nuevo guardado del profesor
  mantiene ese estado tenga o no observaciones administrativas.
- La misma regla se aplica si el profesor elimina una evidencia de imagen de
  esa planeación.
- La edición aumenta `version_revision`, conserva las fechas y responsables de
  seguimiento, pero no crea otra notificación administrativa ni devuelve el
  plan a la bandeja `pendiente`.
- Las correcciones en estado técnico `con_observaciones` mantienen el
  comportamiento existente.
- Solo los planes que administración todavía no ha revisado continúan en
  `pendiente` cuando el profesor los modifica.
- No se agregaron estados, tablas ni migraciones.

Verificación:

- Ruff correcto en el repositorio y las pruebas modificadas.
- 22 pruebas enfocadas de integridad y revisión correctas.

## 2026-07-24 - Paginación opcional del historial de planeaciones

- `GET /plan-de-clases/{asignacion_id}` acepta `limit` entre 1 y 50 y `offset`
  mayor o igual que cero cuando se consulta el historial.
- El límite y el desplazamiento se aplican en la base de datos después del
  orden descendente por fecha y creación.
- Omitir `limit` conserva la respuesta completa anterior para mantener
  compatibilidad con otros consumidores.
- La consulta exacta mediante `fecha` conserva su comportamiento y no aplica
  paginación.
- No se agregaron tablas ni migraciones.

Verificación:

- Ruff correcto en rutas, controlador, servicio, repositorio y prueba
  modificados.
- 20 pruebas enfocadas de integridad y revisión correctas.

## 2026-07-24 - Notificaciones administrativas resumidas por profesor

- `GET /notificaciones/planeadores` agrupa para administración todos los envíos
  pendientes de cada profesor directamente en la consulta.
- Cada elemento administrativo devuelve `profesor_id`, nombre, cantidad total
  de planeaciones pendientes y fecha del envío más reciente.
- `total_no_leidas` conserva el número total de planeaciones y
  `total_profesores` informa cuántos docentes tienen envíos pendientes.
- El perfil profesor conserva sin cambios sus notificaciones individuales de
  comentarios administrativos.
- No se agregaron tablas ni migraciones.

Verificación:

- 19 pruebas enfocadas de integridad, revisión y notificaciones correctas.

## 2026-07-23 - Revisión administrativa consolidada

- El listado administrativo agrupa los estados internos en dos decisiones
  visibles: `pendiente` incluye registros antiguos en `visto`, mientras
  `revisado` incluye también `con_observaciones`.
- Una planeación a la que administración solicitó ajustes conserva
  internamente `con_observaciones` cuando el profesor guarda la corrección.
- Esa corrección aumenta `version_revision` y conserva el historial, pero no
  crea otra notificación administrativa ni vuelve a la bandeja pendiente.
- El mismo criterio se aplica cuando el profesor elimina una evidencia como
  parte de la corrección.
- Los demás guardados continúan pasando a `pendiente` y generan la notificación
  administrativa habitual.
- No se agregaron estados, tablas ni migraciones.

Verificación:

- 19 pruebas enfocadas de integridad y revisión correctas.
- Suite completa: 179 de 182 pruebas correctas. Las 3 restantes siguen siendo
  los casos de Super Admin dependientes de la fecha fija `2026-07-01`.

## 2026-07-22 - Aprobación con comentario opcional

- `PATCH /admin/plan-de-clases/{plan_id}/revision` acepta `comentario` cuando
  la decisión es `revisado`.
- El comentario se normaliza, admite hasta 3000 caracteres y no se acepta para
  la apertura simple con estado `visto`.
- Cuando existe comentario, el historial y el estado `revisado` se guardan en
  una sola transacción protegida por la versión del plan.
- El profesor recibe el comentario mediante el flujo existente de
  notificaciones, sin agregar tablas ni aplicar otra migración.

Verificación:

- 16 pruebas enfocadas de integridad, revisión, comentarios y notificaciones
  correctas.
- Suite completa: 176 de 179 pruebas correctas. Las 3 restantes siguen siendo
  los casos de Super Admin dependientes de la fecha fija `2026-07-01`.

## 2026-07-22 - Notificaciones de planeadores por rol

Tercera subcapa del seguimiento administrativo. Agrega eventos persistentes
para administracion y reutiliza la lectura historica de observaciones para el
profesor.

- Cada guardado o nueva version del profesor crea un evento administrativo
  unico por `plan_id + plan_version`.
- Abrir, observar o revisar una version marca sus eventos administrativos
  pendientes como leidos dentro de la misma transaccion.
- El profesor recibe solamente observaciones propias cuyo
  `vista_por_profesor_at` sigue vacio; abrir el historial confirma la lectura.
- `GET /notificaciones/planeadores` entrega el contador total y hasta 20
  elementos recientes, adaptados al rol autenticado.
- `20260722_plan_de_clases_notificaciones.sql` crea la tabla de eventos sin
  poblar planes historicos y fue aplicada en los 4 schemas operativos.
- Los scripts de auditoria ahora abren una transaccion explicita de solo
  lectura y la revierten al finalizar, evitando que el modo de lectura quede
  adherido a conexiones reutilizadas por el proxy.

Verificacion:

- 14 pruebas enfocadas de integridad, revision y notificaciones correctas.
- Suite completa: 174 de 177 pruebas correctas. Las 3 restantes son los casos
  ya documentados de Super Admin dependientes de la fecha fija `2026-07-01`.
- `scripts/auditar_plan_de_clases_revision.py` confirma columnas, historial,
  tabla de eventos y estados validos en los 4 schemas.
- La simulacion posterior confirma la migracion como ya aplicada en todos los
  destinos.

## 2026-07-22 - Seguimiento versionado del plan de clases

Segunda subcapa del flujo de seguimiento administrativo. Prepara el contrato
que usaran las vistas y notificaciones, sin cambiar aun el frontend.

- Cada plan expone `estado_revision`, `version_revision`, fechas de seguimiento
  y contadores de observaciones.
- Los estados persistidos son `pendiente`, `visto`, `con_observaciones` y
  `revisado`.
- Administracion puede consultar un plan por id, marcar la version como vista
  o revisada y registrar observaciones historicas.
- Toda accion administrativa incluye la version leida. Si el profesor guardo
  cambios entretanto, se devuelve `409` y no se aplica una revision obsoleta.
- Un nuevo guardado o la eliminacion de una evidencia por el profesor aumenta
  la version y devuelve el plan a `pendiente`.
- El profesor propietario puede consultar las observaciones y confirmar su
  lectura; ese dato servira para las notificaciones de la siguiente capa.
- `20260722_plan_de_clases_revision.sql` agrega las columnas de seguimiento y
  la tabla `plan_de_clases_observaciones` sin borrar planes existentes.

Verificacion:

- 25 pruebas enfocadas de integridad, revision y permisos correctas.
- Suite completa: 171 de 174 pruebas correctas. Las 3 restantes son los casos
  ya documentados de Super Admin dependientes de la fecha fija `2026-07-01`.
- La migracion se aplico y registro correctamente en los 4 schemas operativos.
- `scripts/auditar_plan_de_clases_revision.py` confirmo en modo de solo lectura
  que la estructura y los datos inicializados no tienen inconsistencias.

## 2026-07-22 - Integridad atomica del plan de clases

Primera subcapa del nuevo flujo de seguimiento administrativo. No agrega aun
estados de revision, observaciones ni notificaciones.

- `guardar_plan_de_clases` reemplaza la secuencia `UPDATE` seguido de `INSERT`
  por un unico `INSERT ... ON CONFLICT DO UPDATE`.
- El contrato HTTP y el identificador retornado se conservan.
- Si no llegan imagenes nuevas, el upsert mantiene las evidencias existentes.
- `20260722_plan_de_clases_integridad.sql` valida datos incompletos y grupos
  duplicados antes de exigir `asignacion_id`, `fecha` y su unicidad.
- La migracion no borra ni fusiona registros; falla de forma transaccional si
  se requiere intervencion manual.
- `scripts/auditar_plan_de_clases_integridad.py` permite revisar todos los
  tenants y el schema plantilla mediante una conexion de solo lectura.

Orden de despliegue:

1. Auditoria de integridad.
2. Migracion por tenant.
3. Despliegue del nuevo repositorio.

Verificacion:

- 4 pruebas nuevas de upsert, conservacion de evidencias, seguridad de la
  migracion y auditoria de solo lectura.
- 18 pruebas enfocadas de integridad y permisos correctas.
- Suite completa: 164 de 167 pruebas correctas. Las 3 restantes pertenecen a
  `test_super_admin.py` y usan `2026-07-01` como fecha futura fija; al ejecutar
  la suite el 2026-07-22, el estado calculado es `suspendido`. Ese modulo no se
  modifico en esta subcapa para mantener el alcance aislado.
- La auditoria productiva de solo lectura finalizo sin inconsistencias en los
  4 schemas operativos.
- La migracion se aplico correctamente en los 4 schemas el 2026-07-22 y la
  verificacion posterior confirmo su registro e integridad.

## 2026-07-21 - Sesion ampliada a cuatro horas

- `ACCESS_TOKEN_EXPIRE_MINUTES` cambia de `120` a `240` minutos por defecto.
- El JWT y la cookie `token` conservan la misma expiracion absoluta de cuatro
  horas desde el inicio de sesion.
- `.env.example` y la documentacion operativa reflejan el nuevo valor.
- Una variable `ACCESS_TOKEN_EXPIRE_MINUTES` configurada en el proveedor de
  despliegue sigue teniendo prioridad sobre el valor predeterminado.

## 2026-07-16 - Distribucion parcial de subsidios en adelantos

- `PagoAdelantadoCreate` admite exactamente una de dos modalidades:
  `cantidad_meses` o `monto_distribuir`.
- Los meses futuros se consultan por saldo, de modo que un periodo con abono
  parcial permanece disponible para completar.
- Un monto se distribuye cronologicamente, cubriendo cuotas completas y
  aplicando el remanente al siguiente mes.
- El backend rechaza valores que excedan la capacidad disponible hasta
  diciembre y exige que los metodos sumen el total recibido.
- El recibo y la respuesta detallan el monto aplicado y saldo restante de cada
  periodo; la anulacion existente revierte todas las aplicaciones.
- No se requirio una nueva migracion: se reutiliza
  `20260716_pagos_aplicaciones_parciales.sql`, ya aplicada.

Verificacion:

- 39 pruebas enfocadas de pagos, subsidios, meses, anulaciones, paginacion y
  permisos.

## 2026-07-16 - Seleccion auditable de meses vencidos

Se amplio el pago pendiente mensual para identificar una o varias cuotas sin
reemplazar el contrato anterior de `POST /pagos`.

Archivos principales:

- `app/services/cartera.py`
- `app/services/cobros.py`
- `app/schemas/pago.py`
- `app/controllers/pagos_controller.py`
- `app/routes/pagos.py`
- `migrations/20260716_pagos_aplicaciones_parciales.sql`
- `tests/test_pagos_meses_vencidos.py`

Cambios:

- El calendario central expone los periodos vencidos con su fecha limite.
- Las opciones aplican pagos historicos sin periodo al saldo mas antiguo por
  FIFO y respetan aplicaciones explicitas o adelantos que ya maduraron.
- `POST /pagos` acepta `aplicaciones` opcionales y conserva el flujo anterior
  cuando no se envian.
- La validacion y la distribucion por metodos son transaccionales; un bloqueo
  asesor por estudiante y concepto evita cobros simultaneos sobre el mismo
  saldo.
- La descripcion de recibo incluye los meses y la anulacion desactiva sus
  aplicaciones como en el flujo de adelantos.

Migracion aplicada:

- `20260716_pagos_aplicaciones_parciales.sql` reemplaza el indice estricto por
  uno auditable por pago y periodo, sin modificar filas existentes.
- Se aplico y verifico en los 4 tenants operativos el 2026-07-16.

Verificacion:

- 34 pruebas enfocadas de pagos, meses, anulaciones, paginacion y permisos.
- Suite completa: 155 aprobadas; persisten 3 pruebas antiguas de Super Admin
  dependientes de la fecha fija `2026-07-01`.

## 2026-07-16 - Pagos de mensualidades adelantadas

Se agrego un flujo optativo para cubrir meses futuros sin modificar el contrato
de los pagos pendientes existentes.

Archivos modificados:

- `app/schemas/pago.py`
- `app/routes/pagos.py`
- `app/controllers/pagos_controller.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/reportes_controller.py`
- `app/services/cobros.py`
- `migrations/20260716_pagos_adelantados.sql`
- `tests/test_pagos_adelantados.py`
- `tests/test_anulaciones_financieras.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/CAMBIOS_BACKEND.md`
- `docs/MIGRACIONES.md`

Cambios:

- `POST /pagos` conserva su schema, validacion y comportamiento.
- Un endpoint de opciones devuelve solo conceptos mensuales asignados y sus
  proximos meses disponibles dentro del año actual.
- El endpoint de registro calcula el total con el valor vigente, exige que los
  metodos sumen exactamente ese total y crea un unico pago/recibo.
- Cada mes queda en `pagos_aplicaciones` con indice unico activo para impedir
  cobros adelantados duplicados.
- El ingreso aparece en caja desde la fecha del pago, pero cartera incorpora la
  aplicacion solo cuando llega el mes correspondiente.
- Los calculos individual y masivo de cartera comparten la misma separacion
  entre pagos normales y aplicaciones de adelantos.
- El estado de cuenta por curso reconoce solo aplicaciones cuyo mes ya llego y
  evita mostrar el mismo adelanto como `Otros Pagos`.
- Al anular, las aplicaciones quedan inactivas y esos meses vuelven a estar
  disponibles sin borrar la huella del pago.
- La operacion de registro es transaccional y un conflicto revierte tanto el
  pago como sus aplicaciones.

Migracion requerida:

- `migrations/20260716_pagos_adelantados.sql` debe ejecutarse por tenant con
  `apply_migration.py`; es aditiva y no modifica registros de pagos existentes.

Verificacion:

- 29 pruebas enfocadas de adelantos, anulaciones, reportes, paginacion y permisos.
- Ruff sobre schemas, rutas, controladores y servicios modificados.

## 2026-07-15 - Fecha limite obligatoria en Malla Curricular

Se formalizo el contrato de las filas del planeador anual y se corrigio el
guardado por lote.

Archivos modificados:

- `app/schemas/planeador_anual.py`
- `app/controllers/planeador_anual_controller.py`
- `tests/test_planeador_anual_validaciones.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- Los cuatro campos de contenido son opcionales entre si y se normalizan con
  `strip()`.
- Toda fila con al menos un contenido exige `fecha` como fecha limite.
- Una fecha sin contenido es invalida y una fila completamente vacia se
  acepta, normalizando `fecha` vacia a `null`.
- El guardado por lote conserva el indice como `slot`, actualiza las filas con
  contenido y elimina el registro de un `slot` que el profesor dejo vacio.
- La operacion se ejecuta en una transaccion con rollback y cierre garantizado
  de conexion.
- No cambia la estructura de la base de datos y no requiere migracion.

Verificacion:

- 19 pruebas enfocadas de Malla Curricular y permisos.
- Ruff sobre schema, controlador y pruebas.

## 2026-07-15 - Observaciones permiten dimensiones parciales

Se formalizo el contrato del observador para aceptar una o varias dimensiones.

Archivos modificados:

- `app/schemas/observacion.py`
- `app/routes/observaciones.py`
- `app/controllers/observacion_controller.py`
- `tests/test_observaciones_validaciones.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `conductual`, `cognitivo` y `lenguaje` tienen texto vacio como valor por
  defecto.
- El backend exige que al menos una dimension tenga contenido real.
- Los textos se normalizan con `strip()` antes de guardar.
- La ruta usa `ObservacionCreate` en lugar de recibir un diccionario sin tipo.
- El guardado usa rollback explicito y cierre garantizado de cursor/conexion.
- No cambia la estructura de la base de datos y no requiere migracion.

Verificacion:

- 18 pruebas enfocadas de observaciones y permisos.
- Ruff sobre schema, ruta, controlador y pruebas.

## 2026-07-15 - Actualizacion segura de asistencia por lote

Se reforzo el contrato que crea y modifica la asistencia del profesor.

Archivos modificados:

- `app/schemas/asistencia.py`
- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`
- `tests/test_asistencia_validaciones.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `estado` solo acepta `presente` o `ausente`.
- El lote no puede estar vacio, mezclar asignacion/fecha/periodo ni repetir
  estudiantes.
- La actualizacion elimina y reemplaza solamente los estudiantes enviados;
  conserva registros historicos de estudiantes que ya no estan activos.
- El reemplazo se ejecuta en una transaccion con rollback explicito ante error.
- Se mantienen el endpoint y la estructura de base de datos existentes; no se
  requiere migracion.

Verificacion:

- 21 pruebas enfocadas de asistencia y permisos.
- Ruff sobre schema, ruta, controlador y pruebas de asistencia.

## 2026-07-15 - Jornada incluida en las clases del profesor

Se amplio de forma compatible el contrato usado por el dashboard del profesor.

Archivos modificados:

- `app/routes/asignaciones.py`
- `tests/test_asignaciones_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `GET /mis-clases/{profesor_id}` incluye `jornada`, tomada directamente de
  `cursos.jornada`.
- No se cambian IDs academicos, permisos, horarios ni asignaciones existentes.
- Se actualizaron expectativas antiguas de pruebas para los rangos
  institucionales vigentes: mañana `06:30-12:30` y tarde `12:30-18:30`.

Verificacion:

- Pruebas enfocadas de asignaciones.
- Revision de sintaxis de la ruta y su prueba de contrato.

## 2026-07-15 - Limpieza operativa de tenant plantilla

Se limpio la informacion registrada por uso en `tenant_colegio_1`, conservando el schema, las tablas, el usuario admin y la configuracion base del tenant ejemplo.

Alcance:

- Se conservaron `usuarios`, `institucion_branding`, `plantilla_impresion`, `cursos`, `materias`, `tipos_de_pagos` y `tipos_pagos_cursos`.
- Se vaciaron datos operativos como estudiantes, profesores, asignaciones, asistencia, notas, pagos, ventas, inventario, boletines, planes de clase, planeadores, nomina, prestamos y egresos.
- No se ejecuto `DROP SCHEMA`, no se eliminaron tablas y no se tocaron otros tenants.
- Se genero un respaldo temporal antes de limpiar; se descarto posteriormente
  porque contenia exclusivamente datos artificiales de una prueba de carga.

Verificacion:

- `tenant_colegio_1.usuarios` conserva el admin `admin@sabiduria.com`.
- Las tablas operativas verificadas quedaron en 0 registros.
- `tenant_2005` conserva datos activos; verificacion posterior mostro estudiantes, profesores, asignaciones, pagos y asistencia con registros.
## 2026-07-15 - Reparacion segura de asignaciones academicas

Se corrigieron referencias `asignacion_academica_id` inconsistentes que podian hacer que un profesor abriera el ID academico de otro profesor, curso o materia.

Archivos modificados:

- `app/services/asignacion_academica.py`
- `app/routes/asignaciones.py`
- `migrations/20260715_reparar_asignacion_academica_invalida.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- La migracion no borra datos; solo actualiza `asignaciones.asignacion_academica_id` cuando apunta a una asignacion de otro profesor, curso o materia.
- El resolver central de asignacion academica valida que el ID apuntado pertenezca a la misma combinacion `profesor_id`, `curso_id` y `materia_id`; si no coincide, usa el ID original.
- `GET /mis-clases/{profesor_id}` queda protegido para no entregar IDs academicos que pertenezcan a otro docente.

Verificacion:

- Auditoria previa en tenants activos: solo `tenant_2005` tenia 8 asignaciones activas inconsistentes.
- Despues de aplicar la migracion, la auditoria queda en 0 inconsistencias en todos los tenants activos.
- `tenant_2005`: Matematicas Tercero de Edgar Villanueva Mercado queda con `292 -> 292` y `328 -> 292`.
- Se ejecuto `python -m py_compile app/services/asignacion_academica.py app/routes/asignaciones.py`.
## 2026-07-15 - Plan de clases permite textos largos

Se amplio el soporte de textos largos en plan de clases para que ninguna caja usada por el profesor bloquee el guardado por longitud.

Archivos modificados:

- `migrations/20260715_plan_de_clases_textos_largos.sql`
- `migrations/20260715_plan_de_clases_estandar_dba_text.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- La primera migracion convierte `plan_de_clases.unidad` y `plan_de_clases.tema` a `TEXT`.
- La migracion complementaria convierte `plan_de_clases.estandar` y `plan_de_clases.dba` a `TEXT`, que seguian limitadas a `VARCHAR(255)` en los tenants existentes.
- `actividad_casa` ya estaba soportada como texto largo.
- El contrato de API queda documentado como cajas opcionales con texto largo.

Verificacion:

- Revision estatica de migraciones y repositorio de plan de clases.
- Consulta a `information_schema.columns` confirmando `estandar` y `dba` como `text` en los tenants activos.

## 2026-07-15 - Plan de clases permite cajas de texto vacias

Se ajusto el contrato backend de plan de clases para que los docentes puedan guardar el plan aunque no usen todas las cajas de texto.

Archivos modificados:

- `app/routes/plan_de_clases.py`
- `app/schemas/plan_de_clases.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `POST /plan-de-clases` mantiene obligatorios `asignacion_id`, `periodo` y `fecha`.
- Las cajas de texto del plan (`unidad`, `proposito`, `clase`, `estandar`, `dba`, `competencias`, `actividad_casa` y `tema`) tienen valor por defecto `""`.
- El schema de creacion y respuesta tolera textos vacios para no bloquear planes incompletos por decision pedagogica.

Verificacion:

- Se ejecuto `python -m py_compile app/routes/plan_de_clases.py app/schemas/plan_de_clases.py`.

## 2026-07-15 - Documentacion backend sincronizada con codigo actual

Se actualizo la documentacion operativa del backend para alinear el mapa de endpoints, base de datos, migraciones y plan de ejecucion con el codigo vigente.

Archivos modificados:

- `docs/README.md`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/SEGURIDAD.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/MULTITENANT.md`
- `docs/ARQUITECTURA_BACKEND.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- Se agregaron al mapa API los endpoints de valores personalizados por estudiante.
- Se documentaron filtros actuales de rendimiento en dashboard profesor.
- Se agrego `tipos_pagos_estudiantes` a la referencia de base de datos y migraciones.
- Se alineo el plan de ejecucion para usar lenguaje propio de backend en seguridad, roles, modulos y despliegue.
- Se actualizaron fechas de revision en documentos backend revisados.

Verificacion:

- Se contrasto `docs/API_ENDPOINTS.md` contra decorators reales en `app/routes/`.
- Se contrasto la documentacion de valores personalizados contra `app/routes/tipos_pagos.py`, `app/controllers/tipos_pagos_controller.py`, `app/services/cobros.py` y `migrations/20260713_tipos_pagos_estudiantes.sql`.

## 2026-07-13 - Valores personalizados de pago por estudiante

Se agrego soporte para que un estudiante tenga un valor distinto al valor del
curso en un concepto de cartera, sin modificar el curso ni el tipo de pago.

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/tipos_pagos_controller.py`
- `app/routes/tipos_pagos.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/reportes_controller.py`
- `migrations/20260713_tipos_pagos_estudiantes.sql`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Nueva tabla tenant `tipos_pagos_estudiantes`.
- Nueva regla central de valor: estudiante activo > curso > valor base.
- `GET /estudiantes/{estudiante_id}/deudas` respeta el valor personalizado.
- Cartera vencida y estado de cuenta por curso usan la misma regla.
- Se agregaron endpoints admin para listar, guardar y quitar valores
  personalizados por estudiante.
- El backend valida que el concepto este asignado al curso del estudiante antes
  de aceptar una excepcion individual.

## 2026-06-30 - Sesion de 2 horas

Se amplio la duracion por defecto de la sesion autenticada.

Archivos modificados:

- `app/config.py`
- `.env.example`
- `docs/SEGURIDAD.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- `ACCESS_TOKEN_EXPIRE_MINUTES` pasa de `30` a `120` minutos por defecto.
- El JWT y la cookie `token` usan el mismo valor, por lo que la sesion queda
  activa hasta 2 horas si no existe una variable de entorno externa que lo
  sobrescriba.

## 2026-06-24 - Orden configurable de materias en boletin

Se agrego soporte backend para ordenar materias del boletin por curso.

Archivos modificados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `app/schemas/asignacion.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/notas_controller.py`
- `migrations/20260624_asignaciones_orden_boletin.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Se agrego `asignaciones.orden_boletin` con default `100`.
- Se agregaron `GET` y `PUT /cursos/{curso_id}/orden-boletin` para consultar
  y guardar el orden de materias por curso.
- El guardado actualiza todos los horarios activos de la materia en el curso.
- Los boletines administrativos ordenan por `orden_boletin` y luego por nombre
  de materia como respaldo.
- Las consultas legacy de boletin de estudiante tambien respetan el nuevo
  orden.

## 2026-06-23 - Horarios multiples por asignacion academica

Se ajusto la regla de asignaciones academicas:

- Un curso y una materia solo pueden tener un profesor responsable activo.
- Ese mismo profesor puede tener varios horarios/dias para esa materia.
- Los horarios comparten `asignacion_academica_id`, para que notas,
  boletines, asistencia, observaciones y planeadores apunten a un solo historial.
- Se retiro el indice estricto por `profesor_id`, `curso_id`, `materia_id`.
- Se agrego indice unico por horario exacto y trigger para impedir otro profesor
  en la misma materia del mismo curso.
- Se resolvio de forma canonica cualquier `asignacion_id` de horario antes de
  consultar o guardar historial academico.

Archivos modificados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `app/services/asignacion_academica.py`
- `migrations/20260623_asignaciones_horarios_historial_unico.sql`

## 2026-06-23 - Asignaciones activas unicas

Se corrigieron asignaciones duplicadas activas por profesor, curso y materia, y
se agrego proteccion para evitar que vuelvan a generarse.

Archivos modificados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260623_asignaciones_unicas_activas.sql`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- La migracion conserva activa la asignacion con mas historial academico.
- Si las duplicadas no tienen historial, conserva la asignacion mas reciente.
- Las duplicadas restantes quedan `activo = FALSE`, preservando historial.
- Se crea un indice unico parcial para impedir mas de una asignacion activa con
  el mismo `profesor_id`, `curso_id` y `materia_id`.
- El API responde `409 Conflict` con un mensaje claro cuando se intenta crear o
  editar una asignacion duplicada.

Alcance:

- No borra notas, boletines, asistencias, observaciones ni planes.
- Corrige el caso donde el perfil profesor podia mostrar una asignacion vacia
  en lugar de la asignacion con notas.

## 2026-06-23 - Validaciones de duplicados academicos

Se blindaron los modulos administrativos de profesores, materias y cursos
contra duplicados.

Archivos modificados:

- `app/controllers/profesor_controller.py`
- `app/controllers/materia_controller.py`
- `app/controllers/curso_controller.py`
- `app/routes/profesores.py`
- `app/routes/materias.py`
- `app/routes/cursos.py`
- `migrations/20260623_admin_unicos_academicos.sql`
- `docs/API_ENDPOINTS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Profesores no permiten repetir `documento_identidad` ni `email`.
- Materias no permiten repetir `nombre`.
- Cursos no permiten repetir la combinacion `nombre + jornada`.
- El backend responde `409 Conflict` con un mensaje claro cuando detecta un
  duplicado.
- La base de datos agrega indices unicos por tenant para cubrir tambien casos
  concurrentes o llamadas directas al API.

Alcance:

- No bloquea profesores por nombre, porque pueden existir homonimos reales.
- No modifica correos de estudiantes ni usuarios.
- Requiere auditoria previa limpia y ejecucion de migracion tenant.

## 2026-06-23 - Nombres administrativos en mayuscula

Se normalizo el guardado de nombres administrativos para profesores, materias y
cursos.

Archivos modificados:

- `app/controllers/profesor_controller.py`
- `app/controllers/materia_controller.py`
- `app/controllers/curso_controller.py`
- `migrations/20260623_admin_nombres_mayuscula.sql`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Profesores se guardan con `nombre` y `apellido` en mayuscula.
- Materias se guardan con `nombre` en mayuscula.
- Cursos se guardan con `nombre` en mayuscula.
- La migracion convierte los registros existentes y limpia espacios duplicados.

Alcance:

- No modifica correos, documentos, jornadas ni estados.
- Requiere ejecutar la migracion tenant para actualizar datos ya guardados.

## 2026-06-23 - Codigo DANE en identidad institucional

Se agrego el campo institucional `codigo_dane` para que cada colegio pueda
guardarlo desde su configuracion de impresos.

Archivos modificados:

- `app/controllers/branding_controller.py`
- `app/schemas/branding.py`
- `migrations/20260623_institucion_branding_codigo_dane.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- `GET /branding` devuelve `codigo_dane`.
- `PUT /branding` permite guardar `codigo_dane`.
- La migracion agrega `institucion_branding.codigo_dane` como `VARCHAR(20)`.

Alcance:

- Requiere ejecutar la migracion tenant antes o junto al despliegue backend.
- No cambia logos ni plantillas de impresion.

## 2026-06-23 - Endpoint dedicado para deudas de estudiante

Se agrego un endpoint especifico para consultar deudas academicas pendientes
de un estudiante sin depender del resumen amplio de detalle.

Archivos modificados:

- `app/controllers/estudiante_controller.py`
- `app/routes/estudiantes.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Nuevo endpoint `GET /estudiantes/{estudiante_id}/deudas`.
- Reutiliza `calcular_deudas_estudiante` del servicio central de cobros.
- Devuelve `estudiante_id`, `curso_id`, `deudas` y `total_deuda`.
- Usa `get_cursor()` para cerrar cursor/conexion automaticamente.
- El endpoint existente `/estudiantes/{estudiante_id}/detalles` ahora carga notas,
  asistencia, observaciones, deudas e inventario por secciones independientes:
  si una seccion falla, registra el error y conserva las demas respuestas.

Alcance:

- No cambia cartera vencida ni el endpoint existente
  `/estudiantes/{estudiante_id}/detalles` a nivel de contrato de respuesta.
- No requiere migraciones.

## 2026-06-17 - Cumpleanos de estudiantes en dashboards

Se agregaron endpoints de dashboard para consultar solamente los estudiantes
activos que cumplen anos en la semana actual/proximos dias, usando la fecha
local de Colombia.

Archivos modificados:

- `app/controllers/dashboard_controller.py`
- `app/routes/dashboard.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- `GET /dashboard/cumpleanos/admin?dias=7` devuelve los cumpleaños de
  estudiantes activos para el perfil admin.
- `GET /dashboard/cumpleanos/profesor/{profesor_id}?dias=7` devuelve solo
  estudiantes activos de cursos asignados al profesor autenticado.
- `dias` es opcional, por defecto `7`, y se valida entre `0` y `31`.
- Las consultas filtran por mes y dia de `fecha_nacimiento` en base de datos
  usando `America/Bogota`, incluso si el rango cruza de diciembre a enero,
  evitando cargar listas completas de estudiantes en el frontend.
- Las conexiones y cursores se cierran en `finally`.

Alcance:

- No se crearon tablas ni migraciones.
- No cambia el contrato de `/estudiantes`, `/mis-clases` ni
  `/planilla-excel`.
- El cambio es aditivo y queda protegido por permisos existentes de admin y
  scope de profesor.

## 2026-06-13 - Documentacion backend de produccion, pool y endpoints

Se actualizo la carpeta `docs/` del backend para reflejar el estado operativo
actual despues del despliegue en produccion.

Archivos documentales modificados/agregados:

- `docs/README.md`
- `docs/API_ENDPOINTS.md`
- `docs/ARQUITECTURA_BACKEND.md`
- `docs/BASE_DATOS.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/ESCALABILIDAD.md`
- `docs/MIGRACIONES.md`
- `docs/MULTITENANT.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/SEGURIDAD.md`

Cambio:

- Se agrego indice general de documentacion backend.
- Se documento respuesta operativa ante
  `psycopg2.pool.PoolError: connection pool exhausted`.
- Se dejo como regla que todo `get_connection()` debe cerrar cursor/conexion en
  `finally`, y que codigo nuevo deberia preferir `get_cursor()`.
- Se agrego checklist de Render/Neon, pool, cookies moviles/cross-site y
  post-deploy.
- Se corrigio `API_ENDPOINTS.md`: ventas queda bajo `/api/ventas` y super admin
  queda bajo `/super-admin`.
- Se actualizo la lista de migraciones tenant/public observadas.

Alcance:

- Solo documentacion.
- No se modifico codigo backend en esta actualizacion documental.

Contexto:

- En produccion se observo un error de pool agotado que bloqueo login.
- El login ya habia sido revisado para cerrar conexiones en
  `app/controllers/auth_controller.py`; esta sesion dejo esa regla reflejada en
  los documentos operativos.

## 2026-06-10 - Bloqueo backend de eliminaciones no auditables

Se cerro el acceso backend a endpoints `DELETE` que no deben eliminar registros
operativos o contables.

Archivos modificados:

- `app/routes/tipos_pagos.py`
- `app/controllers/tipos_pagos_controller.py`
- `app/routes/inventario.py`
- `app/controllers/inventario_controller.py`
- `tests/test_catalogos_pagination.py`
- `tests/test_inventario_pagination.py`

Cambio:

- `DELETE /tipos-pagos/{id}` responde `405 Method Not Allowed`.
- `DELETE /inventario/{item_id}` responde `405 Method Not Allowed`.
- Los controladores asociados ya no ejecutan SQL de borrado ni desactivacion por
  metodo `DELETE`.
- Para tipos de pago se debe usar la configuracion `activo/inactivo`.
- Para inventario se debe usar `PATCH /inventario/{item_id}/estado`.
- Egresos y prestamos ya estaban bloqueados con `405`; se mantienen igual.

Motivo:

- Alinear backend con la politica de no eliminar registros que afectan auditoria,
  historial financiero, cobros, ventas o trazabilidad operativa.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m pytest tests\test_egresos_fechas.py tests\test_prestamos_validaciones.py tests\test_inventario_pagination.py tests\test_catalogos_pagination.py -q
.\venv\Scripts\python.exe -m pytest -q
```

Resultado:

- Pruebas especificas OK.
- Suite completa OK.

## Cambio documentado

Fecha: 2026-05-25

Cambio:

- Se actualiza carpeta `docs/` para documentar el estado real actual del backend.

Archivos documentales actualizados:

- `docs/ARQUITECTURA_BACKEND.md`
- `docs/MULTITENANT.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/BASE_DATOS.md`
- `docs/API_ENDPOINTS.md`
- `docs/SEGURIDAD.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Alcance:

- estructura de `app/`;
- rutas y controladores;
- servicios y repositorios;
- autenticacion JWT;
- roles y permisos;
- multi-tenant por schema PostgreSQL;
- uso de `search_path`;
- conexion a base de datos;
- endpoints existentes;
- migraciones y scripts existentes;
- riesgos pendientes;
- variables `.env`;
- estado de preparacion para produccion.

Restricciones aplicadas:

- No se modifico logica del backend.
- No se propusieron cambios nuevos en estos documentos.
- Se documento solo lo observado en el codigo actual.

## 2026-05-25 - Seguridad multi-tenant consolidada

Se consolida en este archivo la bitacora detallada que estaba en README_SEGURIDAD_MULTITENANT.md.

Motivo:

- Evitar documentacion duplicada en la raiz del backend.
- Dejar docs/CAMBIOS_BACKEND.md como bitacora oficial de cambios.
- Conservar pruebas, comandos, decisiones y pendientes de la auditoria multi-tenant.

Resultado:

- README_SEGURIDAD_MULTITENANT.md fue eliminado de la raiz.
- docs/HISTORIAL_SEGURIDAD_MULTITENANT.md fue eliminado porque quedaba duplicado.
- La bitacora historica queda integrada abajo en este mismo archivo.

### Bitacora historica integrada

# Seguimiento de seguridad multi-tenant

Fecha: 2026-05-19

Este documento resume los cambios realizados para endurecer la seguridad
multi-tenant del backend antes de produccion, y deja una lista clara de
pendientes para continuar mas adelante.

## Cambios realizados hoy

### 1. Nomina protegida solo para admin

Archivo:
- `app/routes/nomina.py`

Cambio:
- El router de nomina ahora usa `get_current_active_admin`.
- Antes cualquier request podia acceder a endpoints de nomina si conocia la URL.

Impacto:
- Sin token responde `401`.
- Profesor responde `403`.
- Admin puede operar normalmente.

### 2. Eliminado fallback a tenant por defecto

Archivos:
- `app/globals.py`
- `app/db/tenant.py`
- `app/dependencies.py`
- `app/main.py`

Cambio:
- El `ContextVar` de tenant ya no inicia en `tenant_colegio_1`.
- Si una request no tiene tenant valido, falla en vez de apuntar a un colegio real.
- El JWT debe traer `tenant` valido.

Impacto:
- Evita que requests mal formadas o sin tenant caigan accidentalmente sobre datos reales.

### 3. `public` ya no es tenant valido para usuarios

Archivo:
- `app/db/tenant.py`

Cambio:
- `TENANT_SCHEMA_PATTERN` ya no acepta `public`.
- Se agrego `INTERNAL_SCHEMA_PATTERN` para permitir `public` solo en operaciones internas, como login.

Impacto:
- Un JWT de usuario con `tenant = public` ya no debe ser aceptado.
- El login sigue pudiendo consultar `public.colegios`.

### 4. Usuarios administrativos solo para admin

Archivos:
- `app/routes/usuario.py`
- `app/controllers/usuario_controller.py`

Cambio:
- `/usuarios` ahora requiere `get_current_active_admin`.
- Al crear o actualizar usuarios, la password se guarda con `get_password_hash`.

Impacto:
- Profesor no puede crear, editar, listar ni eliminar usuarios internos.
- Nuevas passwords ya no se guardan en texto plano.

### 5. Inventario solo para admin

Archivo:
- `app/routes/inventario.py`

Cambio:
- Todo el modulo de inventario ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede consultar ni modificar inventario desde API.

### 6. Tipos de pagos solo para admin

Archivo:
- `app/routes/tipos_pagos.py`

Cambio:
- Todo el modulo de tipos de pagos ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede cambiar conceptos, valores, mora ni asignaciones por curso.

### 7. Reportes solo para admin

Archivo:
- `app/routes/reportes.py`

Cambio:
- Todo el modulo de reportes ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede acceder a reportes financieros o resumenes globales.

### 8. Asignaciones separadas por permisos

Archivos:
- `app/routes/asignaciones.py`
- `src/pages/DashboardProfesor.jsx` en frontend

Cambio:
- Crear, editar, eliminar y listar todas las asignaciones ahora es admin-only.
- Profesor puede consultar solo sus propias clases.
- Se agrego validacion de ownership por `profesor_id`.
- El dashboard del profesor ya no consume `/asignaciones/lista`; usa `/mis-clases/{profesor_id}`.
- `/mis-clases/{profesor_id}` ahora devuelve tambien `dia`, `hora_inicio` y `hora_fin`.

Impacto:
- Profesor ya no puede consultar la lista global de asignaciones.
- Profesor conserva su horario y sus clases.

### 9. Dashboard de profesor con ownership

Archivo:
- `app/routes/dashboard.py`

Cambio:
- Endpoints por `profesor_id` validan que el profesor solo consulte su propio ID.
- Endpoints por `asignacion_id` validan que la asignacion pertenezca al profesor.
- Admin puede consultar todo.

Impacto:
- Evita que un profesor cambie IDs para ver datos academicos de otro profesor.

### 10. Plan de clases con ownership

Archivo:
- `app/routes/plan_de_clases.py`

Cambio:
- `POST /plan-de-clases` valida que la asignacion pertenezca al profesor.
- `GET /plan-de-clases/{asignacion_id}` valida ownership.
- Admin mantiene acceso global por `/admin/plan-de-clases`.

Impacto:
- Profesor no puede crear ni consultar planeadores de una asignacion ajena.

### 11. Planilla y notas con ownership por asignacion

Archivos:
- `app/routes/planilla.py`
- `app/routes/notas.py`

Cambio:
- `POST /planilla/nota` valida ownership de `data.asignacion_id`.
- `GET /planilla-excel/{asignacion_id}/{periodo}` valida ownership.
- `DELETE /planilla/tipo` valida ownership.
- `POST /notas` valida ownership de `nota.asignacion_id`.
- `GET /planilla/{asignacion_id}` valida ownership.
- `POST /boletin/guardar` validaba ownership de cada `materia.asignacion_id`;
  esta ruta legacy fue retirada el 2026-05-30 y el flujo actual usa
  `/boletines/guardar`.

Impacto:
- Profesor no puede registrar, borrar o consultar planillas/notas de asignaciones ajenas.

### 12. Revalidacion de usuario/rol contra DB

Archivo:
- `app/dependencies.py`

Cambio:
- `get_current_user` ya no confia solamente en el JWT.
- Despues de validar firma, tenant y rol del token, consulta la base del tenant.
- Si el rol es `profesor`, confirma que exista en la tabla `profesor`.
- Si el rol no es `profesor`, confirma que exista en `usuarios` y que el rol actual en DB coincida con el rol del token.
- Si en alguna tabla existen columnas `estado` o `activo`, tambien las respeta.

Impacto:
- Si un usuario se elimina o cambia de rol, un token viejo deja de servir.
- Si mas adelante se agregan columnas `estado` o `activo` a `usuarios`/`profesor`, la validacion queda lista para bloquear cuentas inactivas.

### 13. Boletines con permisos separados

Archivo:
- `app/routes/boletines.py`

Cambio:
- `POST /boletines/guardar` valida que la asignacion pertenezca al profesor o que el usuario sea admin.
- `POST /boletines/guardar` tambien valida que el estudiante pertenezca al curso de esa asignacion.
- `GET /boletines/referencia/{asignacion_id}/{periodo}` valida ownership por asignacion.
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede guardar ni consultar boletines de asignaciones ajenas.
- Profesor no puede guardar boletin cruzando un estudiante que no pertenece a la asignacion.
- La generacion global de boletines queda limitada a admin.

### 14. Asistencia con ownership por asignacion

Archivos:
- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`

Cambio:
- `POST /asistencia` valida que cada asignacion enviada pertenezca al profesor o que el usuario sea admin.
- `POST /asistencia` valida que cada estudiante pertenezca al curso de su asignacion.
- `GET /asistencia/historial/{asignacion_id}/{periodo}` valida ownership por asignacion.
- Se removieron `print` con datos de asistencia recibida para no exponer informacion en logs.

Impacto:
- Profesor no puede registrar ni consultar asistencia de asignaciones ajenas.
- Profesor no puede registrar asistencia cruzando estudiantes fuera del curso de la asignacion.

### 15. Estudiantes, pagos, cuentas y cartera solo para admin

Archivos:
- `app/routes/estudiantes.py`
- `app/routes/pagos.py`
- `app/routes/cuentas.py`
- `app/routes/cartera.py`

Cambio:
- Estos routers ahora usan `get_current_active_admin`.
- Se confirmo que el flujo del profesor para observaciones usa `/planilla/{asignacion_id}`, no `/estudiantes`.

Impacto:
- Profesor no puede listar ni modificar estudiantes desde endpoints administrativos.
- Profesor no puede consultar ni registrar pagos.
- Profesor no puede consultar estados de cuenta ni cartera vencida.
- Las pantallas admin existentes siguen siendo las consumidoras naturales de estos endpoints.

### 16. Cursos, materias y profesores solo para admin

Archivos:
- `app/routes/cursos.py`
- `app/routes/materias.py`
- `app/routes/profesores.py`

Cambio:
- Estos routers ahora usan `get_current_active_admin`.
- Se revisaron usos en frontend y aparecen ligados a pantallas administrativas como crear cursos, crear materias, crear profesores, asignar clases, planeadores admin y boletin admin.
- Los flujos del profesor continúan usando rutas ya acotadas como `/mis-clases/{profesor_id}`, `/planilla/{asignacion_id}` y rutas por asignacion con ownership.

Impacto:
- Profesor no puede crear, editar ni listar catalogos academicos globales desde API.
- La estructura academica queda bajo control del admin.

### 17. `/uploads` protegido por autenticacion y tenant

Archivos:
- `app/main.py`
- `app/dependencies.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/controllers/branding_controller.py`

Cambio:
- Se elimino el `app.mount("/uploads", StaticFiles(...))` publico.
- Se agrego `GET /uploads/{file_path:path}` como endpoint autenticado.
- `get_current_user` ahora tambien puede leer el token desde cookie `token`, necesario para que etiquetas `<img>` puedan cargar logos/imagenes.
- El endpoint valida que la ruta real quede dentro de la carpeta `uploads`.
- El endpoint valida tenant:
  - `uploads/branding/{tenant}/...` solo se sirve a usuarios autenticados de ese tenant.
  - `uploads/{tenant}/plan_de_clases/...` solo se sirve al admin del tenant o al profesor propietario de la asignacion asociada a esa imagen.
- Las imagenes de plan de clases ahora se guardan con UUID, no con el nombre original del archivo.
- Las imagenes de plan de clases validan extension, content-type y tamano maximo.
- Los nuevos logos ya no permiten SVG; solo PNG, JPG/JPEG y WEBP.
- El borrado de logos valida que el archivo real este dentro de `uploads`.

Impacto:
- Un usuario sin token ya no puede abrir archivos de `/uploads`.
- Un usuario de otro tenant no puede abrir archivos de otro colegio por URL.
- Un profesor no puede abrir imagenes de planeadores ajenos si adivina la URL.
- Se reduce riesgo de path traversal y de XSS por SVG en nuevos logos.

Nota:
- En produccion, si frontend y backend viven en dominios/subdominios distintos, revisar configuracion de cookie `token` para que las imagenes autenticadas se carguen correctamente desde `<img>`.

### 18. Script legacy de admin eliminado

Archivos:
- `insert_admin.sql`

Cambio:
- Se elimino `insert_admin.sql` de la raiz del backend.
- Tambien se elimino la copia legacy que habia quedado como referencia.

Impacto:
- Elimina el riesgo de ejecutar por accidente un script que crea un admin con password en texto plano.
- Actualizacion 2026-06-02: el flujo recomendado para crear tenants y admin
  inicial es `/super-admin` -> `Crear colegio`. `crear_cliente.py` paso a
  `scripts/legacy/crear_cliente.py`.

### 19. Prueba base de permiso por estudiante

Archivos:
- `app/core/permissions.py`
- `tests/test_permissions.py`
- `tests/test_notas_permissions.py`

Cambio:
- Se agregaron pruebas unitarias para `require_estudiante_access`.
- Las pruebas validan:
  - admin pasa sin consultar DB;
  - profesor duenio del estudiante pasa;
  - profesor no duenio recibe `403`;
  - rol no autorizado recibe `403`.
- Se agregaron pruebas de cableado para confirmar que las rutas antiguas de
  `notas.py` llaman el permiso antes de devolver datos:
  - `GET /notas/{estudiante_id}`;
  - `GET /boletin/{estudiante_id}`;
  - `GET /boletin/detallado/{estudiante_id}`.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py`
- Resultado: 8 pruebas pasaron.

Pendiente manual:
- Probar funcionalmente en la app con usuarios reales:
  - profesor duenio del estudiante;
  - profesor no duenio;
  - admin;
  - request sin token.

Prueba manual realizada:
- Se intento consultar un estudiante no autorizado desde URL directa y el backend respondio `{"detail":"No autorizado"}`.

### 20. Pruebas base de auth, tenant y uploads

Archivos:
- `tests/test_auth_tenant.py`
- `tests/test_uploads_permissions.py`

Cambio:
- Se agregaron pruebas unitarias para `get_current_user`:
  - sin token responde `401`;
  - token invalido responde `401`;
  - token con `tenant=public` responde `401`;
  - token valido fija el tenant y revalida usuario contra DB;
  - usuario eliminado o rol cambiado invalida el token.
- Se agregaron pruebas unitarias para la validacion de `/uploads`:
  - branding del mismo tenant se permite;
  - branding de otro tenant se bloquea;
  - path traversal se bloquea;
  - admin del tenant puede abrir imagen de plan de clases;
  - profesor duenio puede abrir imagen de su plan de clases;
  - profesor no duenio recibe `403`.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 19 pruebas pasaron.

Nota:
- Aparecieron advertencias de dependencias/Pydantic, pero no errores de pruebas.

### 21. Runner de migraciones con historial

Archivos:
- `apply_migration.py`
- `migrations/README.md`
- `tests/test_apply_migration.py`

Cambio:
- Se mejoro `apply_migration.py` para registrar historial en `public.schema_migrations`.
- Se agrega checksum SHA-256 por migracion.
- Si una migracion ya fue aplicada en un tenant con el mismo checksum, se omite.
- Si existe el mismo nombre de migracion con checksum diferente, se bloquea.
- Se agrego modo `--dry-run` para simular antes de aplicar cambios.
- Se reemplazo el `SET search_path` construido manualmente por `psycopg2.sql.Identifier`.

Uso recomendado:
- `python apply_migration.py migrations/<archivo>.sql --dry-run`
- `python apply_migration.py migrations/<archivo>.sql`

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 24 pruebas pasaron.

Pendiente:
- Probar el runner contra una copia de la base real antes de usarlo en produccion.
- Decidir mas adelante si se migra completamente a Alembic.

### 22. Script de indices por tenant actualizado

Archivos:
- `scripts/apply_tenant_indexes.py`
- `tests/test_apply_tenant_indexes.py`

Cambio:
- Se completo la lista de indices recomendados para consultas frecuentes.
- Se agrego modo `--dry-run` para simular sin crear indices.
- El script ahora valida que la tabla exista antes de crear el indice.
- El script ahora valida que las columnas existan antes de crear el indice.
- Si una tabla o columna falta en un tenant, se omite sin romper todo el proceso.

Indices incluidos:
- `estudiantes(curso_id)`
- `asignaciones(profesor_id)`
- `asignaciones(curso_id)`
- `notas_detalle(estudiante_id, asignacion_id, periodo)`
- `boletin_cabecera(estudiante_id, asignacion_id, periodo)`
- `asistencia(asignacion_id, periodo)`
- `asistencia(estudiante_id, fecha)`
- `pagos(estudiante_id)`
- `ventas(estudiante_id, estado)`
- `plan_de_clases(asignacion_id, fecha)`

Uso recomendado:
- Simular: `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py --dry-run`
- Aplicar: `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py`

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 28 pruebas pasaron.
- Se ejecuto `--dry-run` y encontro 2 tenants activos: `tenant_3333` y `tenant_colegio_1`.
- No se crearon indices durante la simulacion.
- Se ejecuto el script real y los indices quedaron verificados en `tenant_3333` y `tenant_colegio_1`.

Pendiente:
- Despues de aplicar, revisar consultas pesadas con `EXPLAIN ANALYZE`.

### 23. Paginacion compatible en estudiantes

Archivos:
- `app/routes/estudiantes.py`
- `app/controllers/estudiante_controller.py`
- `tests/test_estudiantes_pagination.py`

Cambio:
- `GET /estudiantes` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /estudiantes?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agrego `busqueda` opcional:
  - `GET /estudiantes?limit=50&offset=0&busqueda=ana`
- El limite maximo permitido por request es `200`.

Motivo:
- Evita romper las pantallas actuales que consumen `/estudiantes` como lista.
- Permite migrar el frontend a paginacion pantalla por pantalla.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_estudiantes_pagination.py tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 30 pruebas pasaron.

Pruebas manuales recomendadas:
- `GET /estudiantes`
- `GET /estudiantes?limit=20&offset=0`
- `GET /estudiantes?limit=20&offset=0&busqueda=<texto>`

### 24. Paginacion compatible en ventas

Archivos:
- `app/routes/ventas.py`
- `app/controllers/venta_controller.py`
- `tests/test_ventas_pagination.py`

Cambio:
- `GET /api/ventas/` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /api/ventas/?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `busqueda`;
  - `estudiante_id`;
  - `estado`.
- El limite maximo permitido por request es `200`.
- En modo paginado, el backend solo carga los detalles de las ventas de esa pagina, no todos los detalles historicos.

Motivo:
- Evita cargar todas las ventas y todos sus detalles cuando el historial crezca.
- Mantiene intacta la pantalla actual mientras se migra el frontend con calma.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`

Pruebas manuales recomendadas:
- `GET /api/ventas/`
- `GET /api/ventas/?limit=20&offset=0`
- `GET /api/ventas/?limit=20&offset=0&estado=Pendiente`
- `GET /api/ventas/?limit=20&offset=0&busqueda=<texto>`

### 25. Paginacion compatible en pagos por estudiante

Archivos:
- `app/routes/pagos.py`
- `app/controllers/pagos_controller.py`
- `tests/test_pagos_pagination.py`

Cambio:
- `GET /pagos/{estudiante_id}` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /pagos/{estudiante_id}?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.

Motivo:
- El historial de pagos puede crecer mucho por estudiante.
- Permite migrar la pantalla de pagos a paginacion sin romper el flujo actual de facturacion/recibos.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /pagos/<estudiante_id>`
- `GET /pagos/<estudiante_id>?limit=20&offset=0`
- `GET /pagos/<estudiante_id>?limit=20&offset=20`

### 26. Paginacion compatible en inventario

Archivos:
- `app/routes/inventario.py`
- `app/controllers/inventario_controller.py`
- `tests/test_inventario_pagination.py`

Cambio:
- `GET /inventario` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /inventario?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `busqueda`;
  - `solo_con_stock`.
- El limite maximo permitido por request es `200`.

Motivo:
- Inventario se usa en administracion y en punto de venta.
- Al crecer el catalogo, permite cargar productos por paginas sin romper las pantallas actuales.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /inventario`
- `GET /inventario?limit=20&offset=0`
- `GET /inventario?limit=20&offset=0&busqueda=<texto>`
- `GET /inventario?limit=20&offset=0&solo_con_stock=true`

### 27. Paginacion compatible en reportes de ingresos

Archivos:
- `app/routes/reportes.py`
- `app/controllers/reportes_controller.py`
- `scripts/apply_tenant_indexes.py`
- `tests/test_reportes_pagination.py`
- `tests/test_apply_tenant_indexes.py`

Cambio:
- `GET /reportes/ingresos-mes/{mes}` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /reportes/ingresos-rango?inicio=<fecha>&fin=<fecha>` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- Ambos endpoints aceptan ahora `limit` y `offset`.
- Con paginacion devuelven:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.
- Se agregaron al script de indices:
  - `pagos(fecha)`;
  - `pagos(fecha_pago)`.

Motivo:
- Los reportes financieros por mes/rango pueden crecer mucho y devolver demasiados pagos.
- La pantalla actual de reportes sigue funcionando sin cambios.
- Los indices por fecha preparan mejor la base para consultas historicas grandes.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_reportes_pagination.py tests\test_apply_tenant_indexes.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /reportes/ingresos-mes/2026-05`
- `GET /reportes/ingresos-mes/2026-05?limit=20&offset=0`
- `GET /reportes/ingresos-rango?inicio=2026-05-01&fin=2026-05-31`
- `GET /reportes/ingresos-rango?inicio=2026-05-01&fin=2026-05-31&limit=20&offset=0`

Pendiente operativo:
- Se ejecuto `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py --dry-run` y encontro los indices nuevos pendientes de verificacion en `tenant_3333` y `tenant_colegio_1`.
- Si la simulacion se ve bien, ejecutar `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py` para verificar/crear los indices nuevos.

### 28. Paginacion compatible en asignaciones administrativas

Archivos:
- `app/routes/asignaciones.py`
- `app/controllers/asignacion_controller.py`
- `tests/test_asignaciones_pagination.py`

Cambio:
- `GET /asignaciones/lista` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /asignaciones/lista?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `profesor_id`;
  - `curso_id`;
  - `materia_id`;
  - `busqueda`.
- El limite maximo permitido por request es `200`.

Motivo:
- La grilla de asignacion de clases necesita seguir cargando todas las asignaciones como hoy para validar cruces visuales y materias duplicadas.
- La paginacion queda disponible para futuras vistas administrativas o busquedas mas livianas.
- Es un listado sensible porque cruza profesor, curso, materia y horario.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_asignaciones_pagination.py tests\test_reportes_pagination.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /asignaciones/lista`
- `GET /asignaciones/lista?limit=20&offset=0`
- `GET /asignaciones/lista?limit=20&offset=0&profesor_id=<id>`
- `GET /asignaciones/lista?limit=20&offset=0&curso_id=<id>`
- `GET /asignaciones/lista?limit=20&offset=0&busqueda=<texto>`

### 29. Paginacion compatible en catalogos administrativos

Archivos:
- `app/routes/profesores.py`
- `app/controllers/profesor_controller.py`
- `app/routes/cursos.py`
- `app/controllers/curso_controller.py`
- `app/routes/materias.py`
- `app/controllers/materia_controller.py`
- `app/routes/usuario.py`
- `app/controllers/usuario_controller.py`
- `tests/test_catalogos_pagination.py`

Cambio:
- `GET /profesores`, `GET /cursos`, `GET /materias` y `GET /usuarios` conservan el comportamiento anterior si no se envian parametros: devuelven listas simples.
- Todos aceptan ahora `limit` y `offset`.
- `profesores`, `cursos`, `materias` y `usuarios` aceptan `busqueda`.
- `usuarios` acepta ademas filtro `rol`.
- Con paginacion devuelven:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.

Motivo:
- Son catalogos normalmente pequenos, pero dejarlos con paginacion opcional completa el patron del backend.
- Permite crear futuras pantallas administrativas con busqueda/paginacion sin cambiar contratos existentes.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_catalogos_pagination.py tests\test_asignaciones_pagination.py tests\test_reportes_pagination.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /profesores`
- `GET /profesores?limit=20&offset=0&busqueda=<texto>`
- `GET /cursos`
- `GET /cursos?limit=20&offset=0&busqueda=<texto>`
- `GET /materias`
- `GET /materias?limit=20&offset=0&busqueda=<texto>`
- `GET /usuarios`
- `GET /usuarios?limit=20&offset=0&busqueda=<texto>&rol=admin`

### 30. Permisos repetidos centralizados

Archivos:
- `app/core/permissions.py`
- `app/routes/notas.py`
- `app/routes/planilla.py`
- `app/routes/asistencia.py`
- `app/routes/boletines.py`
- `app/routes/dashboard.py`
- `app/routes/asignaciones.py`
- `app/routes/plan_de_clases.py`
- `tests/test_permissions.py`

Cambio:
- Se consolido `app/core/permissions.py` como modulo unico para permisos reutilizables.
- Se agregaron funciones centrales:
  - `require_profesor_scope`;
  - `require_asignacion_access`;
  - `require_estudiante_access`;
  - `require_estudiante_in_asignacion`;
  - `require_plan_de_clases_access`.
- Se reemplazaron validaciones locales repetidas en rutas criticas:
  - notas;
  - planilla;
  - asistencia;
  - boletines;
  - dashboard;
  - asignaciones;
  - plan de clases.

Motivo:
- Evita que cada ruta tenga su propia version de permisos.
- Reduce riesgo de que una ruta quede mas permisiva que otra por error.
- Hace mas facil auditar y endurecer reglas multi-tenant/profesor/admin en un solo lugar.

Decision tecnica:
- Se mantuvo el modulo en `app/core/permissions.py`.
- No se creo `app/security/permissions.py` porque ya existe `app/security.py`; crear una carpeta con el mismo nombre podria causar conflictos de importacion en Python.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_asignaciones_pagination.py`
- Resultado: 25 pruebas pasaron.

Pruebas manuales recomendadas:
- Profesor debe poder ver sus propias clases en `/mis-clases/<profesor_id>`.
- Profesor no debe poder ver clases de otro profesor cambiando el ID.
- Profesor debe poder abrir planilla/notas/asistencia de sus asignaciones.
- Profesor debe recibir `403` al intentar una asignacion ajena.
- Admin debe conservar acceso administrativo normal.

## Verificaciones realizadas

- Validacion de sintaxis con `ast.parse` en los archivos Python modificados.
- Build de frontend con `pnpm run build` despues de corregir el horario del profesor.
- El build de frontend termino correctamente.
- Validacion de sintaxis de `app/dependencies.py` despues de agregar revalidacion contra DB.
- Validacion de sintaxis de `app/routes/boletines.py` despues de agregar permisos por asignacion/admin.
- Validacion de sintaxis de `app/routes/asistencia.py` y `app/controllers/asistencia_controller.py`.
- Validacion de sintaxis de `app/routes/estudiantes.py`, `app/routes/pagos.py`, `app/routes/cuentas.py` y `app/routes/cartera.py`.
- Validacion de sintaxis de `app/routes/cursos.py`, `app/routes/materias.py` y `app/routes/profesores.py`.
- Validacion de sintaxis de `app/main.py`, `app/dependencies.py`, `app/controllers/plan_de_clases_controller.py` y `app/controllers/branding_controller.py`.

## Pendientes importantes

### 1. Revisar scripts antiguos

Archivo:
- `insert_admin.sql`

Estado:
- Hecho. El script fue eliminado por completo.

Riesgo residual:
- Ninguno desde el repositorio, mientras no se recree un script similar con password en texto plano.

### 2. Provisionamiento de tenants

Archivo:
- `scripts/legacy/crear_cliente.py`

Estado:
- Actualmente el alta de tenant se hace por terminal.
- Este flujo hashea la password del admin inicial.

Pendiente:
- Mas adelante crear panel o comando superadmin mas robusto.
- Asegurar migraciones completas para cada tenant nuevo.

## Recomendacion de siguiente sesion

Orden sugerido:

1. Revisar scripts antiguos y provisionamiento de tenants.
2. Probar en entorno real que logos e imagenes de planeadores cargan correctamente con el nuevo `/uploads` autenticado.

## Hoja de ruta de auditoria para produccion

Esta seccion resume el paso a paso recomendado despues de la auditoria general
del sistema. El objetivo es seguir endureciendo seguridad, escalabilidad y
mantenibilidad sin romper funcionalidades existentes.

### 1. Seguridad inmediata: cerrar endpoints por `estudiante_id`

Archivo principal:
- `app/routes/notas.py`

Endpoints a cerrar:
- `GET /notas/{estudiante_id}`
- `GET /boletin/{estudiante_id}`
- `GET /boletin/detallado/{estudiante_id}`

Riesgo:
- Aunque el usuario este autenticado, hoy un profesor podria cambiar el
  `estudiante_id` en la URL e intentar consultar notas o boletines de un
  estudiante que no pertenece a sus asignaciones dentro del mismo tenant.

Accion recomendada:
- Crear una validacion de acceso por estudiante.
- Admin: puede consultar estudiantes dentro de su tenant.
- Profesor: solo puede consultar estudiantes cuyo curso tenga una asignacion
  perteneciente a ese profesor.
- Si no cumple, responder `403`.

Pruebas necesarias:
- Profesor duenio del estudiante recibe `200`.
- Profesor no duenio recibe `403`.
- Admin recibe `200` dentro de su tenant.
- Sin token recibe `401`.
- Token de otro tenant no debe ver datos fuera de su schema.

### 2. Scripts peligrosos

Archivo:
- `insert_admin.sql`

Riesgo:
- Crea un usuario admin con password plano (`admin123`).

Accion recomendada:
- Hecho: fue eliminado por completo porque no era necesario para el funcionamiento del sistema.
- Actualizacion 2026-06-02: el flujo oficial ahora es `/super-admin` ->
  `Crear colegio`. `crear_cliente.py` paso a `scripts/legacy/crear_cliente.py`.

### 3. Pruebas base de seguridad

Objetivo:
- Montar pruebas automatizadas minimas antes de produccion.

Casos obligatorios:
- Login correcto por tenant.
- Login falla con colegio inactivo o inexistente.
- Token viejo falla si el usuario se elimina o cambia de rol.
- Profesor no puede consultar asignaciones ajenas.
- Profesor no puede consultar estudiantes ajenos.
- Admin puede operar dentro de su tenant.
- `/uploads` exige autenticacion.
- `/uploads` bloquea archivos de otro tenant.
- Passwords nuevas siempre quedan hasheadas.

Estado:
- Iniciado. Ya existen pruebas para:
  - regla de acceso por estudiante;
  - rutas antiguas de notas;
  - auth/JWT/tenant;
  - validacion de uploads protegidos.
- Falta ampliar pruebas a flujos completos con DB de prueba e integracion de endpoints reales.

### 4. Migraciones

Estado actual:
- Existen scripts sueltos y una carpeta `migrations`.
- Alembic aun no esta inicializado como fuente formal de verdad.
- `apply_migration.py` ya tiene historial por tenant con checksum y `--dry-run`.

Accion recomendada:
- Usar `apply_migration.py` como runner temporal seguro.
- Ejecutar siempre primero con `--dry-run`.
- Inicializar Alembic mas adelante, o consolidar este runner propio como flujo oficial.
- Distinguir entre:
  - cambios globales en `public`;
  - cambios repetidos en schemas `tenant_*`;
  - indices y constraints por tenant.

Riesgo si no se hace:
- Un tenant nuevo puede quedar con tablas o columnas distintas.
- Un cambio aplicado manualmente puede no llegar a todos los colegios.

### 5. Indices y revision con `EXPLAIN ANALYZE`

Accion recomendada:
- Usar `scripts/apply_tenant_indexes.py` para aplicar indices por tenant.
- Ejecutar primero `--dry-run`.
- Revisar reportes con `EXPLAIN ANALYZE`.

Prioridad de indices:
- `estudiantes(curso_id)`
- `asignaciones(profesor_id)`
- `asignaciones(curso_id)`
- `notas_detalle(estudiante_id, asignacion_id, periodo)`
- `boletin_cabecera(estudiante_id, asignacion_id, periodo)`
- `asistencia(asignacion_id, periodo)`
- `asistencia(estudiante_id, fecha)`
- `pagos(estudiante_id)`
- `ventas(estudiante_id, estado)`
- `plan_de_clases(asignacion_id, fecha)`

Estado:
- Script actualizado con modo seguro `--dry-run`.
- Pruebas unitarias agregadas.
- Simulacion ejecutada correctamente.
- Indices reales aplicados/verificados en los tenants activos.
- Falta medir consultas pesadas con `EXPLAIN ANALYZE`.

### 6. Paginacion

Problema:
- Varios endpoints devuelven listas completas. Esto funciona con pocos datos,
  pero puede afectar memoria, tiempos de respuesta y experiencia de usuario.

Empezar por:
- `GET /estudiantes` (iniciado con paginacion compatible)
- ventas
- pagos por estudiante
- reportes de ingresos por rango
- inventario
- asignaciones/listados administrativos

Accion recomendada:
- Agregar `limit` y `offset` con limites maximos razonables.
- Mantener compatibilidad con el frontend actual mientras se migra pantalla por pantalla.

Estado:
- `GET /estudiantes` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /api/ventas/` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /pagos/{estudiante_id}` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /inventario` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /reportes/ingresos-mes/{mes}` y `GET /reportes/ingresos-rango` ya soportan paginacion opcional sin romper el contrato anterior.
- `GET /asignaciones/lista` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /profesores`, `GET /cursos`, `GET /materias` y `GET /usuarios` ya soportan paginacion opcional sin romper el contrato anterior.
- La fase de paginacion compatible queda cubierta en los listados administrativos principales.

### 7. Refactor de permisos

Problema:
- Las validaciones de permisos estan repetidas en varios routers.

Accion escalable recomendada:
- Crear un archivo central, por ejemplo:
  - `app/security/permissions.py`

Funciones sugeridas:
- `require_admin(current_user)`
- `require_asignacion_access(asignacion_id, current_user)`
- `require_estudiante_access(estudiante_id, current_user)`
- `require_estudiante_in_asignacion(estudiante_id, asignacion_id)`

Estrategia segura:
- No mover todo de una vez.
- Primero crear funciones centrales.
- Migrar una ruta critica.
- Probar.
- Continuar modulo por modulo.

Estado:
- Iniciado y aplicado en rutas criticas de profesor/asignacion/estudiante/plan de clases.
- Falta una segunda pasada mas adelante para revisar otros permisos especiales y simplificar imports/casos no cubiertos por estas funciones.

### 8. Refactor de modulos grandes

Archivos backend que conviene dividir:
- `app/controllers/estudiante_controller.py`
- `app/controllers/reportes_controller.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/asignacion_controller.py`
- `app/controllers/tipos_pagos_controller.py`

Archivos frontend que conviene dividir:
- `src/components/cartera/AdministrarTiposPago.jsx`
- `src/pages/EstudiantesAdmin.jsx`
- `src/components/AsignarClaseGrid.jsx`
- `src/pages/CarteraVencidaAdmin.jsx`
- `src/pages/PagosAdmin.jsx`

Objetivo:
- Separar UI, llamadas API, helpers de formato, validaciones y componentes hijos.
- Reducir riesgo de romper una pantalla completa por cambios pequenos.

### 9. Endurecer sesion

Estado actual:
- El frontend guarda token en cookie creada por JavaScript y conserva datos en
  `localStorage`.

Riesgo:
- Si algun dia aparece XSS, el token podria quedar expuesto.

Accion recomendada para produccion:
- Mover el token a cookie `HttpOnly`, `Secure`, `SameSite`.
- El backend debe emitir y limpiar la cookie.
- El frontend no deberia necesitar leer el token directamente.

### 10. Provisionamiento de tenants

Archivo legacy:
- `scripts/legacy/crear_cliente.py`

Estado:
- Antes el tenant se creaba desde terminal.
- El flujo actual crea colegios desde `/super-admin`.

Accion recomendada:
- Mantener el script solo como referencia historica.
- Validar que cada tenant nuevo reciba todas las tablas, datos iniciales,
  plantillas, branding vacio, indices y migraciones.
- A mediano plazo crear flujo superadmin o comando CLI mas robusto.

Checklist minimo de tenant nuevo:
- Registro en `public.colegios`.
- Schema creado con nombre valido.
- Tablas completas.
- Indices aplicados.
- Plantillas predefinidas copiadas.
- Branding inicial creado.
- Admin inicial con password hasheada.
- Login probado.
- Build/frontend apuntando al backend correcto.

## Lectura general de estado

El sistema ya avanzo bastante en seguridad multi-tenant: se elimino el fallback
a tenant real, se protegio gran parte de los modulos administrativos, se
revalida usuario contra DB, y `/uploads` ya no es publico.

Aun asi, no se considera listo para produccion masiva hasta cerrar tres frentes:

1. Ownership por `estudiante_id` en rutas antiguas de `notas.py`.
2. Pruebas automatizadas de acceso cruzado, autenticacion, tenants y uploads.
3. Migraciones confiables para que todos los tenants tengan el mismo schema.

La base ya es seria, pero falta la parte menos visible y mas importante:
pruebas, permisos centralizados, migraciones, paginacion e indices.

importante: cuando se modifique cada paso pedir probar lo que se acctualizo



## 2026-05-26 - Cierre incremental de ownership en rutas de profesor

Se continuo la fase critica de seguridad backend enfocada en rutas con IDs directos manipulables desde el navegador.

### Observaciones protegidas por asignacion y estudiante

Archivo modificado:

- `app/routes/observaciones.py`

Cambio:

- `POST /observaciones` ahora valida `asignacion_id` con `require_asignacion_access`.
- `POST /observaciones` ahora valida que `estudiante_id` pertenezca a la asignacion con `require_estudiante_in_asignacion`.
- `GET /observaciones/{estudiante_id}/{asignacion_id}/{periodo}` aplica las mismas validaciones antes de consultar.

Riesgo cerrado:

- Un profesor autenticado podia intentar cambiar manualmente `estudiante_id` o `asignacion_id` para leer o guardar observaciones de una asignacion ajena.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m py_compile app\routes\observaciones.py
.\venv\Scripts\python.exe -m pytest tests\test_permissions.py
```

Resultado:

- `tests/test_permissions.py`: 14 pruebas pasaron.

Pruebas manuales recomendadas:

- Profesor duenio debe poder guardar y consultar observaciones de su asignacion.
- Profesor no duenio debe recibir `403` al cambiar `asignacion_id` por una asignacion ajena.
- Profesor debe recibir `403` si intenta cruzar un estudiante que no pertenece a la asignacion.
- Admin debe conservar acceso normal dentro del tenant.
- Request sin token debe responder `401`.

### Planeador anual protegido por asignacion

Archivo modificado:

- `app/routes/planeador_anual.py`

Cambio:

- `GET /planeador-anual/{asignacion_id}/{periodo}` ahora valida `asignacion_id` con `require_asignacion_access`.
- `PUT /planeador-anual/{asignacion_id}/{periodo}` aplica la misma validacion antes de actualizar.

Riesgo cerrado:

- Un profesor autenticado podia intentar cambiar manualmente `asignacion_id` para consultar o actualizar el planeador anual de otro profesor.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m py_compile app\routes\planeador_anual.py
.\venv\Scripts\python.exe -m pytest tests\test_permissions.py
```

Resultado:

- `tests/test_permissions.py`: 14 pruebas pasaron.

Pruebas manuales recomendadas:

- Profesor duenio debe poder consultar y actualizar su planeador anual.
- Profesor no duenio debe recibir `403` al usar una `asignacion_id` ajena.
- Admin debe conservar acceso normal dentro del tenant.
- Request sin token debe responder `401`.

Nota de entorno:

- Durante las ejecuciones de PowerShell aparecieron mensajes locales de `fnm`/perfil de PowerShell por permisos en `AppData`; no afectaron las pruebas de backend.

## 2026-05-26 - Verificacion de rutas criticas ya protegidas

Se continuo la fase critica de seguridad backend y se verificaron modulos sensibles sin requerir cambios de codigo adicionales.

### Plan de clases

Archivos revisados:

- `app/routes/plan_de_clases.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/core/permissions.py`

Estado:

- `POST /plan-de-clases` ya valida `require_asignacion_access`.
- `GET /plan-de-clases/{asignacion_id}` ya valida `require_asignacion_access`.
- `DELETE /plan-de-clases/{plan_id}/imagen` ya valida `require_plan_de_clases_access`.
- Rutas admin de plan de clases ya usan `get_current_active_admin`.

Resultado:

- No se modifico codigo.
- Se valido sintaxis con `py_compile`.
- `tests/test_permissions.py` paso, pero `tests/test_uploads_permissions.py` no pudo completarse por permisos locales de pytest creando temporales en Windows.

### Asistencia

Archivos revisados:

- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`
- `app/schemas/asistencia.py`

Estado:

- `POST /asistencia` ya valida cada item con `require_asignacion_access` y `require_estudiante_in_asignacion`.
- `GET /asistencia/historial/{asignacion_id}/{periodo}` ya valida `require_asignacion_access`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py`: 14 pruebas pasaron.

### Boletines

Archivos revisados:

- `app/routes/boletines.py`
- `app/controllers/boletin_controller.py`
- `app/schemas/boletin.py`

Estado:

- `POST /boletines/guardar` ya valida `require_asignacion_access` y `require_estudiante_in_asignacion`.
- `GET /boletines/referencia/{asignacion_id}/{periodo}` ya valida `require_asignacion_access`.
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` ya exige `get_current_active_admin`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py tests/test_notas_permissions.py`: 18 pruebas pasaron.

### Dashboard

Archivos revisados:

- `app/routes/dashboard.py`
- `app/controllers/dashboard_controller.py`

Estado:

- Endpoints por `profesor_id` ya usan `require_profesor_scope`.
- Endpoints por `asignacion_id` ya usan `require_asignacion_access`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py`: 14 pruebas pasaron.

### Rutas admin-only

Archivos revisados:

- `app/routes/estudiantes.py`
- `app/routes/pagos.py`
- `app/routes/cursos.py`
- `app/routes/profesores.py`
- `app/routes/materias.py`
- `app/routes/usuario.py`
- `app/routes/reportes.py`
- `app/routes/inventario.py`
- `app/routes/tipos_pagos.py`
- `app/routes/cartera.py`
- `app/routes/nomina.py`

Estado:

- Todos los routers revisados usan `get_current_active_admin` a nivel de router.

Resultado:

- No se modifico codigo.
- `py_compile` correcto para todos los archivos revisados.

Conclusion:

- La fase de revision de ownership/admin-only queda avanzada.
- Los cambios reales de codigo hechos hoy fueron en `observaciones.py` y `planeador_anual.py`.
- Los demas modulos listados quedaron verificados como ya protegidos.

## 2026-05-26 - Configuracion base para produccion

Se avanzo en la preparacion de variables y comportamiento de sesion/CORS para despliegue.

Archivos modificados:

- `app/config.py`
- `app/main.py`
- `app/routes/auth.py`
- `.env.example`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- Se agrego `ALLOW_DEV_CORS_ORIGINS` a configuracion.
- CORS ahora incluye `localhost` y `127.0.0.1` solo si `ALLOW_DEV_CORS_ORIGINS=true`.
- `.env.example` ahora documenta `ALLOW_DEV_CORS_ORIGINS`.
- `.env.example` ahora documenta `SESSION_COOKIE_SECURE`.
- `.env.example` ahora documenta `SESSION_COOKIE_SAMESITE`.
- `POST /logout` borra la cookie `token` usando `httponly`, `secure` y `samesite` segun configuracion.

Valores recomendados para produccion:

- `ENVIRONMENT=production`
- `FRONTEND_URL=https://<dominio-frontend-real>`
- `ALLOW_DEV_CORS_ORIGINS=false`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=lax` o el valor requerido segun dominio/subdominio real.
- `SECRET_KEY` largo, aleatorio y privado.

Verificacion:

```powershell
.\venv\Scripts\python.exe -m py_compile app\config.py app\main.py app\routes\auth.py
.\venv\Scripts\python.exe -m pytest tests\test_auth_tenant.py
```

Resultado:

- `tests/test_auth_tenant.py`: 5 pruebas pasaron.

Pruebas manuales recomendadas:

- Iniciar sesion como admin y profesor.
- Revisar en DevTools que la cookie `token` sea HttpOnly.
- En entorno HTTPS/productivo, confirmar que `SESSION_COOKIE_SECURE=true` marca cookie Secure.
- Ejecutar logout y confirmar que la cookie `token` desaparece.
- Con `ALLOW_DEV_CORS_ORIGINS=false`, confirmar que solo el dominio `FRONTEND_URL` puede consumir la API.

## 2026-05-26 - Migraciones e indices verificados en tenants activos

Se aplicaron las migraciones SQL pendientes usando el runner oficial `apply_migration.py`.

Tenants activos verificados:

- `tenant_colegio_1` - Colegio Demo
- `tenant_3333` - milagro

Migraciones aplicadas en ambos tenants:

- `20260429_pagos_tipo_pago_largo.sql`
- `20260429_plan_de_clases_reportes.sql`
- `20260509_branding_plantillas_impresion.sql`
- `20260517_tipos_pagos_avanzado.sql`

Comandos ejecutados:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260429_pagos_tipo_pago_largo.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260429_plan_de_clases_reportes.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260509_branding_plantillas_impresion.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260517_tipos_pagos_avanzado.sql
```

Resultado:

- Las 4 migraciones respondieron `OK` en los 2 tenants activos.
- `public.schema_migrations` quedo con historial para las 4 migraciones por cada tenant activo.
- La verificacion posterior mostro `MIGRACIONES_TODAS_OK: True`.

Indices:

- Se verificaron los indices principales por tenant.
- La verificacion posterior mostro `INDICES_TODOS_OK: True`.

Estado del bloque de base de datos:

```text
Base de datos
[x] migraciones aplicadas en todos los tenants activos
[x] indices aplicados
[x] revisar public.schema_migrations
[ ] backup antes de salir
```

Pendiente:

- Hacer backup antes de cualquier salida real a produccion.
- Probar flujo principal de admin/profesor despues de migraciones.

## 2026-05-26 - Inicio centralizacion de cobros en tipos de pago

Se inicio la transicion para que la logica financiera dependa de `tipos_de_pagos`
y `tipos_pagos_cursos`, dejando los valores financieros de `cursos` como fallback
legacy temporal para matricula/mensualidad.

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/pagos_controller.py`
- `app/controllers/estudiante_controller.py`

Cambio:

- Se creo `app/services/cobros.py` como servicio central para:
  - cargar tipos de pago;
  - leer asignaciones por curso desde `tipos_pagos_cursos`;
  - aplicar fallback legacy de `cursos.matricula`, `cursos.mensualidad` y `cursos.meses`;
  - calcular deudas por estudiante usando `app/services/cartera.py`;
  - obtener saldo pendiente por concepto.
- `pagos_controller.py` ya no calcula saldos con una copia local de la logica de matricula/mensualidad.
- `pagos_controller.py` valida el monto del pago contra `obtener_saldo_concepto` del servicio central.
- `estudiante_controller.py` usa `calcular_deudas_estudiante` para poblar `deudas` y `total_deuda`.

Objetivo:

- Evitar logica financiera duplicada en pagos, estudiante, cartera y reportes.
- Preparar el sistema para que antes de produccion los cobros se administren desde Tipos de Pago.
- Mantener compatibilidad mientras se retiran gradualmente los campos financieros del formulario de curso.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\pagos_controller.py', r'app\controllers\estudiante_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Nota:

- `py_compile` no pudo usarse porque Windows nego permisos al escribir `__pycache__`.
- La validacion con `ast.parse` no escribe bytecode y paso correctamente.

Pruebas manuales recomendadas antes de continuar:

- Abrir detalle de un estudiante con deuda y confirmar que `deudas` y `total_deuda` se ven igual o correctamente.
- Registrar un pago parcial de un concepto configurado en Tipos de Pago.
- Intentar registrar un pago mayor al saldo pendiente: debe bloquear.
- Registrar pago de matricula/mensualidad legacy y confirmar que respeta descuento del estudiante.
- Confirmar que conceptos opcionales no generen deuda automatica.

Pendiente:

- Migrar `cartera_mora_controller.py` al servicio central sin perder eficiencia en listados grandes.
- Migrar reportes financieros al mismo servicio.
- Ajustar frontend de Crear Curso para dejar matricula/mensualidad/meses como legacy o retirarlos del flujo principal.

### Cartera vencida conectada al servicio central

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`

Cambio:

- Se agrego `calcular_deudas_desde_contexto` en `app/services/cobros.py`.
- Esta funcion permite calcular deudas usando datos ya precargados para evitar consultas repetidas por estudiante.
- `cartera_mora_controller.py` ahora usa esa funcion para calcular deuda academica, mora y cuotas vencidas.
- Se conserva la carga agrupada de estudiantes, pagos, ventas y asignaciones para mantener eficiencia en listados grandes.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\cartera_mora_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Abrir cartera vencida general.
- Confirmar que los estudiantes con deuda aparecen con total correcto.
- Filtrar cartera vencida por curso si la pantalla lo permite.
- Confirmar que deuda academica, deuda inventario, mora y total se ven coherentes.
- Confirmar que conceptos opcionales no aparecen como deuda automatica.
- Confirmar que un concepto asignado desde Tipos de Pago a un curso aparece en los estudiantes de ese curso.

Pendiente actualizado:

- Migrar reportes financieros al servicio central.
- Revisar `estado_cuenta_controller.py`, que todavia calcula deuda usando directamente `cursos.matricula`, `cursos.mensualidad` y `cursos.meses`.
- Ajustar frontend de Crear Curso para dejar los campos financieros como legacy/fallback.

### Reporte de estado de cuenta por curso conectado al servicio central

Archivo modificado:

- `app/controllers/reportes_controller.py`

Cambio:

- `reporte_estado_cuenta_curso_controller` ahora usa:
  - `obtener_tipos_pago`;
  - `obtener_asignaciones_cobro_por_curso`;
  - `calcular_deudas_desde_contexto`.
- Se elimino de ese reporte la logica repetida que detectaba manualmente conceptos legacy y calculaba deuda por matricula/mensualidad.
- Se conserva compatibilidad con pagos por `concepto_id`, `tipo_pago` y el formato actual de respuesta.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\reportes_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Abrir el reporte de estado de cuenta por curso.
- Confirmar que cada estudiante conserva `pagado`, `total`, `deuda` y `deudas_detalle`.
- Confirmar que conceptos asignados desde Tipos de Pago aparecen en el curso correcto.
- Confirmar que matricula/mensualidad legacy siguen funcionando como fallback.
- Registrar un pago y volver a abrir el reporte para verificar que baja la deuda.

Pendiente actualizado:

- Revisar `estado_cuenta_controller.py`, que todavia contiene consultas directas antiguas.
- Ajustar frontend de Crear Curso para que cobros queden en Tipos de Pago y los campos financieros del curso dejen de ser el flujo principal.

### Estado de cuenta conectado al servicio central

Archivo modificado:

- `app/controllers/estado_cuenta_controller.py`

Cambio:

- `estado_cuenta_curso_controller` ya no calcula deuda con la formula fija:
  `cursos.matricula + cursos.mensualidad * cursos.meses`.
- `estado_cuenta_estudiante_controller` tambien usa el servicio central.
- Ambos controladores llaman `calcular_deudas_estudiante`.
- Se conserva el formato de respuesta:
  - `id`;
  - `nombre`;
  - `apellido`;
  - `pagado`;
  - `total`;
  - `deuda`;
  - `tipos_pagos`.

Motivo:

- Hacer que estado de cuenta respete conceptos configurados desde Tipos de Pago.
- Mantener los campos financieros de curso solo como fallback legacy.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\controllers\estado_cuenta_controller.py', r'app\services\cobros.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.
- No queda la formula directa de `cursos.matricula`, `cursos.mensualidad` y `cursos.meses` en `estado_cuenta_controller.py`.

Pruebas manuales recomendadas:

- Abrir estado de cuenta por curso.
- Abrir estado de cuenta de un estudiante.
- Confirmar que los conceptos de Tipos de Pago afectan deuda/total.
- Confirmar que un pago registrado reduce la deuda.
- Confirmar que matricula/mensualidad legacy siguen funcionando como fallback mientras se ajusta Crear Curso.

### Ajuste de fallback para conceptos asignados con valor 0

Archivo modificado:

- `app/services/cobros.py`

Cambio:

- Si un tipo de pago esta asignado a un curso en `tipos_pagos_cursos` con valor `0`, ya no se toma ese `0` como deuda final automaticamente.
- Nueva regla:
  - si el valor asignado al curso es mayor que `0`, se usa ese valor;
  - si el valor asignado es `0`, se usa el valor global de `tipos_de_pagos`;
  - si tambien es `0` y el concepto es matricula/mensualidad legacy, se usa el valor del curso como fallback.

Motivo:

- Evitar que una asignacion en cero bloquee pagos de matricula o mensualidad.
- Mantener Tipos de Pago como fuente principal sin romper colegios que todavia usan valores financieros en Crear Curso.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; ast.parse(pathlib.Path(r'app\services\cobros.py').read_text(encoding='utf-8')); print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Revisar un curso con `matricula` configurada en Crear Curso.
- En Tipos de Pago, confirmar que el concepto Matricula exista y este activo.
- Si Matricula esta asignada al curso con valor `0`, intentar registrar el pago.
- Debe tomar el valor global del tipo de pago o, si es `0`, el valor de matricula del curso.

## 2026-05-26 - Curso queda solo academico y Tipos de Pago queda como fuente unica de deuda

Se cerro la transicion financiera para que los cobros academicos dependan de
`tipos_de_pagos` y `tipos_pagos_cursos`, no de columnas financieras en `cursos`.

Archivos modificados:

- `app/schemas/curso.py`
- `app/controllers/curso_controller.py`
- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/reportes_controller.py`
- `scripts/legacy/crear_cliente.py`
- `migrations/20260526_cursos_solo_academicos.sql`

Cambios:

- `CursoCreate` ya no exige:
  - `matricula`;
  - `mensualidad`;
  - `meses`.
- `crear_curso_controller` solo inserta:
  - `nombre`;
  - `jornada`.
- `actualizar_curso_controller` solo actualiza:
  - `nombre`;
  - `jornada`.
- Los listados de cursos ya no retornan campos financieros.
- `app/services/cobros.py` ya no usa fallback legacy contra `cursos.matricula`, `cursos.mensualidad` ni `cursos.meses`.
- `cartera_mora_controller.py` y `reportes_controller.py` ya no seleccionan ni pasan esos campos al servicio de cobros.
- `scripts/legacy/crear_cliente.py` se habia actualizado para que el SQL base de `cursos` no incluyera columnas financieras.

Migracion aplicada:

- `migrations/20260526_cursos_solo_academicos.sql`

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260526_cursos_solo_academicos.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.
- Verificacion posterior:
  - `tenant_colegio_1`: cursos sin columnas financieras.
  - `tenant_3333`: cursos sin columnas financieras.

Estado nuevo:

```text
Tipos de Pago = fuente unica de deuda academica
Curso = entidad academica
```

Pruebas manuales recomendadas:

- Crear curso nuevo.
- Editar curso existente.
- Crear/asignar un tipo de pago al curso.
- Ver cartera vencida.
- Ver detalle del estudiante.
- Registrar pago de un concepto asignado.
- Confirmar que si un tipo de pago no esta asignado al curso, no genera deuda.

## 2026-05-26 - Nomina expone sueldo del profesor

Se ajusto la consulta de empleados de nomina para devolver el sueldo asignado al
profesor.

Archivo modificado:

- `app/controllers/nomina_controller.py`

Cambio:

- `obtener_estado_cuenta_profesores()` ahora selecciona `COALESCE(p.sueldo, 0) AS sueldo`.
- La respuesta de `/api/nomina/empleados` incluye:
  - `sueldo`;
  - `saldo_prestamos`.

Motivo:

- Permitir que el frontend precargue el campo `Salario Base` en el modal de pago
  de nomina con el sueldo real configurado en el profesor.

Verificacion:

- Sintaxis de `app/controllers/nomina_controller.py`: OK.

Pruebas manuales recomendadas:

- Crear o editar un profesor con sueldo.
- Consultar nomina desde Admin.
- Abrir `Realizar Pago`.
- Confirmar que el salario base coincide con el sueldo del profesor.

## 2026-05-26 - Mensaje claro para tipos de pago duplicados

Se ajusto la creacion/edicion de tipos de pago para devolver una causa clara
cuando el nombre ya existe.

Archivos modificados:

- `app/controllers/tipos_pagos_controller.py`
- `app/routes/tipos_pagos.py`

Cambio:

- Se agrego `TipoPagoDuplicadoError`.
- Antes de crear un tipo de pago se valida si ya existe otro con el mismo nombre,
  ignorando mayusculas/minusculas y espacios al inicio/final.
- Antes de editar un tipo de pago se valida que el nuevo nombre no exista en otro
  registro.
- La API responde `409 Conflict` con un mensaje legible cuando hay duplicado.

Motivo:

- Evitar que el frontend muestre un error generico de servidor cuando el problema
  real es que el concepto ya existe.

Verificacion:

- Sintaxis de `app/controllers/tipos_pagos_controller.py` y `app/routes/tipos_pagos.py`: OK.

Pruebas manuales recomendadas:

- Crear un tipo de pago con un nombre existente.
- Confirmar que responde una alerta de concepto duplicado.
- Editar un tipo de pago y ponerle el nombre de otro existente.
- Confirmar que tambien se bloquea con mensaje claro.

## 2026-05-26 - Normalizacion de nombres academicos en backend

Se agrego normalizacion en backend para guardar nombres con iniciales en
mayuscula en entidades academicas y profesores.

Archivos modificados:

- `app/controllers/profesor_controller.py`
- `app/controllers/curso_controller.py`
- `app/controllers/materia_controller.py`

Cambio:

- Al crear o editar profesor:
  - `nombre` se guarda en formato titulo;
  - `apellido` se guarda en formato titulo;
  - `email` se guarda en minusculas.
- Al crear o editar curso:
  - `nombre` se guarda en formato titulo.
- Al crear o editar materia:
  - `nombre` se guarda en formato titulo.

Motivo:

- Mantener datos consistentes aunque se envie informacion directa por API.
- Evitar listados, boletines, reportes e impresos con nombres en minusculas o
  mayusculas mezcladas.

Verificacion:

- Sintaxis de controladores de profesor, curso y materia: OK.

Pruebas manuales recomendadas:

- Crear profesor con nombre/apellido en minusculas.
- Crear curso con nombre en minusculas.
- Crear materia con nombre en minusculas.
- Confirmar que se listan con iniciales en mayuscula.

## 2026-05-27 - Anulacion auditada de pagos

Se implemento anulacion de pagos sin eliminacion fisica, empezando desde el
historial de pagos del estudiante.

Archivos modificados:

- `migrations/20260527_pagos_anulacion.sql`
- `app/schemas/pago.py`
- `app/controllers/pagos_controller.py`
- `app/routes/pagos.py`
- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/estado_cuenta_controller.py`
- `app/controllers/reportes_controller.py`
- `scripts/legacy/crear_cliente.py`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agregaron columnas a `pagos`:
  - `estado`;
  - `motivo_anulacion`;
  - `fecha_anulacion`;
  - `anulado_por`.
- Se agrego endpoint admin:
  - `POST /pagos/{pago_id}/anular`
- La anulacion exige motivo.
- Los pagos anulados quedan visibles en historial y reportes.
- Cartera, estado de cuenta y calculo de deudas ignoran pagos con `estado = 'Anulado'`.
- Reportes de ingresos mensuales/rango incluyen la huella del pago anulado, pero
  lo devuelven con `monto_valido = 0`.
- Totales generales e ingresos mensuales suman solo pagos validos.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_pagos_anulacion.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Registrar un pago academico.
- Anularlo desde historial de pagos del estudiante con motivo.
- Confirmar que aparece marcado como `Anulado`.
- Confirmar que la deuda vuelve a subir.
- Abrir Reportes > Ingresos Mensuales.
- Confirmar que el pago anulado aparece como huella, pero no suma al total valido.

### Anulacion segura de pagos de inventario

Se amplio la anulacion para cubrir pagos asociados a ventas de inventario.

Archivos modificados:

- `migrations/20260527_pagos_venta_id.sql`
- `app/controllers/pagos_controller.py`
- `scripts/legacy/crear_cliente.py`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agrego `pagos.venta_id`.
- Al registrar un pago de inventario, se guarda el `venta_id`.
- Al anular un pago con `venta_id`, se resta el monto anulado de `ventas.pagado`.
- Si despues de la anulacion la venta vuelve a tener saldo pendiente, `ventas.estado`
  queda en `Pendiente`.
- Para pagos antiguos sin `venta_id`, el backend intenta inferirlo desde la
  descripcion con formato `Cargo #ID`.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_pagos_venta_id.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Crear una venta de inventario a credito.
- Registrar un abono desde pagos del estudiante.
- Confirmar que la venta aumenta `pagado`.
- Anular ese pago desde historial.
- Confirmar que el pago queda anulado.
- Confirmar que la venta vuelve a `Pendiente` y el saldo vuelve a aparecer.

## 2026-05-27 - Anulacion de ventas de inventario

Se agrego anulacion transaccional de ventas de inventario.

Archivos modificados:

- `migrations/20260527_ventas_anulacion.sql`
- `app/controllers/venta_controller.py`
- `app/routes/ventas.py`
- `docs/API_ENDPOINTS.md`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agregaron columnas a `ventas`:
  - `motivo_anulacion`;
  - `fecha_anulacion`;
  - `anulado_por`.
- Se agrego endpoint admin:
  - `POST /api/ventas/{venta_id}/anular`
- Al anular una venta:
  - la venta queda con `estado = 'Anulada'`;
  - se devuelve el stock de cada item al inventario;
  - se anulan pagos asociados por `venta_id`;
  - se intenta cubrir pagos antiguos asociados por descripcion `Cargo #ID`;
  - `ventas.pagado` vuelve a `0`.

Motivo:

- Evitar eliminacion fisica de ventas.
- Mantener trazabilidad financiera y de inventario.
- Evitar que cartera siga cobrando cargos anulados.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_ventas_anulacion.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Crear una venta/cargo de inventario.
- Confirmar que baja el stock.
- Anular la venta desde el listado de cargos recientes.
- Confirmar que la venta queda `Anulada`.
- Confirmar que el stock vuelve.
- Si tenia pagos asociados, confirmar que quedan anulados y no suman en reportes.

## 2026-05-27 - Ingresos Hoy usa fecha local Colombia

Se ajusto el calculo de `ingresos_hoy` del reporte general para comparar contra
la fecha local de Colombia.

Archivo modificado:

- `app/controllers/reportes_controller.py`

Cambio:

- Antes usaba `CURRENT_DATE` de PostgreSQL.
- Ahora usa `(NOW() AT TIME ZONE 'America/Bogota')::date`.
- Se mantiene la regla de no sumar pagos con `estado = 'Anulado'`.

Motivo:

- Evitar que Neon/PostgreSQL calcule "hoy" con una zona horaria distinta a la
  fecha local con la que se registran los pagos.

Pruebas manuales recomendadas:

- Registrar un pago con fecha de hoy.
- Abrir Admin > Reportes y Estadisticas.
- Confirmar que `Ingresos Hoy` suma el pago.
- Anular ese pago y confirmar que `Ingresos Hoy` deja de sumarlo.

## 2026-05-27 - Bloqueo de eliminacion fisica de ventas

Se bloqueo el endpoint legacy de eliminacion fisica de ventas.

Archivo modificado:

- `app/routes/ventas.py`

Cambio:

- `DELETE /api/ventas/{venta_id}` ya no elimina la venta.
- Ahora responde `405` con mensaje indicando usar:
  - `POST /api/ventas/{venta_id}/anular`

Motivo:

- Evitar perdida de trazabilidad financiera e inventario.
- Forzar el flujo seguro de anulacion con motivo, devolucion de stock y anulacion
  de pagos asociados.

Pruebas manuales recomendadas:

- Intentar llamar `DELETE /api/ventas/{venta_id}`.
- Confirmar que responde bloqueado.
- Anular una venta desde el frontend y confirmar que usa el endpoint de anulacion.

## 2026-05-27 - Pruebas de anulaciones financieras

Se agregaron pruebas unitarias para blindar los flujos de anulacion financiera.

Archivo agregado:

- `tests/test_anulaciones_financieras.py`

Casos cubiertos:

- Anular pago academico sin tocar ventas.
- Anular pago de inventario descontando el abono de la venta asociada.
- Anular venta con devolucion de stock.
- Anular venta dejando pagos asociados en estado `Anulado`.
- Reporte general excluyendo pagos anulados de ingresos y de ingresos de hoy.
- Formato de ingresos marcando `monto_valido = 0` cuando el pago esta anulado.

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q tests\test_anulaciones_financieras.py -p no:cacheprovider
```

Resultado:

- 5 pruebas pasaron correctamente.

Motivo:

- Evitar regresiones en anulaciones de pagos academicos, pagos de inventario,
  ventas, reportes y devolucion de stock antes de produccion.

## 2026-05-28 - Soporte Cloudflare R2 para uploads

Se agrego una capa de almacenamiento para que logos e imagenes del plan diario puedan guardarse en Cloudflare R2 sin romper las URLs actuales.

Archivos modificados/agregados:

- `app/services/storage.py`
- `app/config.py`
- `app/main.py`
- `app/controllers/branding_controller.py`
- `app/controllers/plan_de_clases_controller.py`
- `.env.example`
- `requirements.txt`
- `docs/PRODUCCION_BACKEND.md`
- `docs/SEGURIDAD.md`

Cambio:

- `STORAGE_PROVIDER=local` mantiene `uploads/` local.
- `STORAGE_PROVIDER=r2` usa Cloudflare R2 compatible con S3.
- `/uploads/...` sigue siendo el endpoint de lectura protegido.
- Se agrego dependencia `boto3`.

Comandos ejecutados:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\config.py app\services\storage.py app\controllers\plan_de_clases_controller.py app\controllers\branding_controller.py app\main.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_uploads_permissions.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- Pruebas de permisos de uploads: 6 pasaron.

Pendiente para activar R2 real:

- Crear bucket en Cloudflare R2.
- Crear Access Key/Secret con permiso sobre el bucket.
- Configurar variables R2 en produccion.
- Reiniciar backend.
- Probar subida/visualizacion/eliminacion de logo y plan diario.

## 2026-05-28 - Carga demo para pruebas SQL de rendimiento

Se agrego script para cargar datos demo de rendimiento en un tenant.

Archivo agregado:

- `scripts/seed_tenant_performance.py`

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe scripts\seed_tenant_performance.py --tenant tenant_colegio_1 --reset
```

Datos cargados en `tenant_colegio_1`:

- 20 cursos `PERF_DEMO`.
- 30 profesores `PERF_DEMO`.
- 12 materias `PERF_DEMO`.
- 80 asignaciones.
- 500 estudiantes.
- 10.000 pagos.
- 20.000 notas detalle.
- 3.000 asistencias.
- 50 productos de inventario.
- 1.000 ventas.
- 1.000 ventas detalle.

Comando para limpiar estos datos:

```powershell
.\venv\Scripts\python.exe scripts\seed_tenant_performance.py --tenant tenant_colegio_1 --clean
```

Primeros resultados de `EXPLAIN ANALYZE`:

- `reporte_general_ingresos_hoy`: usa `Seq Scan` sobre `pagos`, ~5 ms con 10.000 pagos.
- `reporte_ingresos_mes`: usa `Seq Scan` por `TO_CHAR(COALESCE(...))`, ~3.7 ms con 10.000 pagos.
- `reporte_ingresos_rango`: usa `Seq Scan`, ~0.94 ms con 10.000 pagos.
- `ventas_paginado`: usa `Seq Scan` + sort sobre `ventas`, ~0.32 ms con 1.000 ventas.
- `cartera_estudiantes`: usa `Seq Scan` en estudiantes activos y nested loop con cursos, ~1 ms con 500 estudiantes.

Lectura tecnica:

- Con datos demo actuales el sistema responde rapido.
- El primer riesgo de crecimiento esta en reportes de pagos por fecha porque usan funciones sobre fecha (`DATE`, `TO_CHAR`, `COALESCE`) que no aprovechan bien indices simples.
- Siguiente paso recomendado: optimizar reportes de pagos con rangos de fecha e indices de expresion o columna normalizada para fecha efectiva.

## 2026-05-28 - Dashboard profesor: filtros seguros por curso

Se ajustaron endpoints del dashboard profesor para soportar ranking de inasistencias por curso y filtro de notas por curso.

Archivos modificados:

- `app/controllers/dashboard_controller.py`
- `app/routes/dashboard.py`
- `app/routes/asignaciones.py`

Cambio:

- `/dashboard/inasistencias/{profesor_id}` ahora devuelve ranking por curso.
- `/dashboard/notas-bajas/{profesor_id}` acepta `curso_id` opcional.
- `/dashboard/notas-altas/{profesor_id}` acepta `curso_id` opcional.
- `/mis-clases/{profesor_id}` incluye `curso_id` para que el frontend pueda filtrar por cursos asignados.

Seguridad:

- Se mantiene `require_profesor_scope` para evitar consultar datos de otro profesor.
- Si llega `curso_id`, el backend valida que ese curso pertenezca a una asignacion del profesor.
- Si el profesor intenta cambiar el `curso_id` manualmente por uno no asignado, debe responder `403`.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\dashboard_controller.py app\routes\dashboard.py app\routes\asignaciones.py
```

Pruebas manuales recomendadas:

- Entrar como profesor y abrir el dashboard.
- Probar notas bajas/altas seleccionando un curso y luego `Todas las materias` o una materia especifica.
- Probar manualmente un `curso_id` no asignado en `/dashboard/notas-bajas/{profesor_id}?curso_id=ID` y confirmar `403`.
- Confirmar que `/dashboard/inasistencias/{profesor_id}` lista ranking por curso.

Correccion del dashboard profesor:

- El filtro final de notas bajas/altas exige `curso_id`.
- Opcionalmente acepta `asignacion_id` para filtrar una materia especifica dentro de ese curso.
- Si no se envia `asignacion_id`, calcula `Todas las materias` que ese profesor dicta en el curso seleccionado.
- El backend valida que el curso pertenezca al profesor.
- Si se envia asignacion, valida que la asignacion pertenezca al profesor y al curso seleccionado.

## 2026-05-28 - Tests de uploads aislados de R2

Se ajustaron las pruebas de permisos de uploads para que no dependan del `.env`
real ni del bucket Cloudflare R2 configurado en desarrollo/produccion.

Archivo modificado:

- `tests/test_uploads_permissions.py`

Cambio:

- Cada prueba que crea archivos temporales locales fuerza
  `using_remote_storage()` a `False` mediante `monkeypatch`.
- Esto permite probar permisos de branding, plan de clases, tenant y path
  traversal usando archivos temporales locales.
- La aplicacion real puede seguir usando `STORAGE_PROVIDER=r2` sin que estas
  pruebas intenten consultar el bucket.

Motivo:

- Con `STORAGE_PROVIDER=r2`, el backend busca archivos en R2.
- Estas pruebas no suben objetos al bucket; crean archivos temporales locales.
- Sin aislar el storage, las pruebas fallaban con `404` aunque la logica de
  permisos pudiera estar correcta.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q tests\test_uploads_permissions.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- 6 pruebas pasaron correctamente.
- Se elimino la carpeta temporal `.pytest_tmp` despues de la verificacion.

## 2026-05-30 - Retiro de endpoint legacy de boletin

Se retiro la ruta legacy `POST /boletin/guardar` del router de notas.

Archivos modificados:

- `app/routes/notas.py`
- `app/controllers/notas_controller.py`
- `app/schemas/nota.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Motivo:

- El frontend actual y el build generado usan `POST /boletines/guardar`.
- La ruta nueva valida `require_asignacion_access` y
  `require_estudiante_in_asignacion`.
- La ruta legacy no aparecia usada por el frontend actual y quedaba como
  superficie innecesaria antes de produccion.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q tests\test_auth_tenant.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- 34 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-05-30 - Estados SaaS iniciales por tenant

Se agrego soporte backend para controlar el estado operativo inicial de cada
tenant desde `public.colegios.estado`.

Estados reconocidos:

- `activo`
- `en_mora`
- `suspendido`
- `cancelado`

Archivos modificados/agregados:

- `app/core/tenant_status.py`
- `app/controllers/auth_controller.py`
- `app/dependencies.py`
- `app/routes/auth.py`
- `app/routes/tenant.py`
- `app/main.py`
- `apply_migration.py`
- `scripts/check_tenant_schemas.py`
- `scripts/apply_tenant_indexes.py`
- scripts historicos de migracion puntual en `scripts/`
- `tests/test_auth_tenant.py`
- `tests/test_apply_migration.py`
- `docs/API_ENDPOINTS.md`
- `docs/MULTITENANT.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/SEGURIDAD.md`

Cambio:

- `POST /login` permite tenants `activo` y `en_mora`.
- `POST /login` rechaza tenants `suspendido` y `cancelado`.
- `get_current_user` revalida el estado del tenant en cada peticion
  autenticada.
- Estados vacios o desconocidos se normalizan como `suspendido` para bloquear
  por defecto.
- Se agrego `GET /tenant/status` para que el frontend pueda mostrar avisos
  cuando el tenant este `en_mora`.
- La respuesta de login incluye `tenant_estado` como dato informativo.
- Los scripts operativos de migraciones, comparacion de schemas e indices ahora
  incluyen tenants `activo` y `en_mora`.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\core\tenant_status.py app\controllers\auth_controller.py app\dependencies.py app\routes\auth.py app\routes\tenant.py app\main.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 44 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-05-30 - Rol super admin inicial

Se agrego el primer control de plataforma para administrar tenants desde la app.

Archivos modificados/agregados:

- `app/core/super_admin.py`
- `app/controllers/super_admin_controller.py`
- `app/routes/super_admin.py`
- `app/controllers/auth_controller.py`
- `app/main.py`
- `migrations/public/20260530_super_admins.sql`
- `scripts/create_super_admin.py`
- `tests/test_super_admin.py`
- `docs/API_ENDPOINTS.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- `super_admin` inicia sesion por el mismo `POST /login` usando codigo
  `super_admin`.
- `super_admin` usa `tenant = public` en el JWT, pero solo lo acepta
  `get_current_super_admin`.
- `get_current_user` sigue rechazando `public` para usuarios de colegios.
- Se agregaron endpoints `GET /super-admin/tenants` y
  `PATCH /super-admin/tenants/{tenant_id}/estado`.
- Se agrego script para crear/actualizar el primer super admin con password
  hasheada.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\core\super_admin.py app\controllers\super_admin_controller.py app\routes\super_admin.py app\controllers\auth_controller.py app\main.py scripts\create_super_admin.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 50 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-06-01 - Mensaje claro para tenants suspendidos/cancelados

Se separo el error de login por credenciales del error por estado SaaS del
colegio.

Archivos modificados:

- `app/core/tenant_status.py`
- `app/controllers/auth_controller.py`
- `app/routes/auth.py`
- `tests/test_auth_tenant.py`
- `docs/SEGURIDAD.md`

Cambio:

- Si el colegio no existe o las credenciales no validan, `POST /login` sigue
  respondiendo `401`.
- Si el colegio existe pero esta `suspendido` o `cancelado`, `POST /login`
  responde `403` con `detail.code = tenant_blocked`, `estado` y mensaje
  especifico.
- Esto evita mostrar "credenciales incorrectas" cuando en realidad el servicio
  esta bloqueado por estado del tenant.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\core\tenant_status.py app\controllers\auth_controller.py app\routes\auth.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 52 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-06-01 - Auditoria de cambios de estado de tenant

Se agrego trazabilidad para cambios de estado SaaS realizados por super admin.

Archivos modificados/agregados:

- `app/controllers/super_admin_controller.py`
- `app/routes/super_admin.py`
- `migrations/public/20260601_tenant_estado_auditoria.sql`
- `tests/test_super_admin.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`

Cambio:

- Al cambiar estado de tenant se registra auditoria en
  `public.tenant_estado_auditoria`.
- La auditoria guarda estado anterior, estado nuevo, motivo, super admin y
  fecha.
- Se agrego `GET /super-admin/tenants/{tenant_id}/estado-auditoria` para
  consultar los ultimos 50 cambios.
- Si el estado solicitado es igual al actual, no se crea registro de auditoria.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\super_admin_controller.py app\routes\super_admin.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 8 pruebas de super admin pasaron correctamente.

## 2026-06-01 - Creacion de colegios desde super admin

Se agrego el flujo backend para crear nuevos colegios desde el panel de
plataforma.

Archivos modificados/agregados:

- `app/controllers/super_admin_controller.py`
- `app/routes/super_admin.py`
- `migrations/public/20260601_tenant_suscripciones.sql`
- `tests/test_super_admin.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`

Cambio:

- Se agrego `POST /super-admin/tenants`.
- El endpoint crea `public.colegios`, schema `tenant_<codigo>`, tablas desde
  `DEFAULT_TENANT_SCHEMA`, branding inicial, plantillas iniciales y admin
  inicial con password hasheada.
- Se agrego `public.tenant_suscripciones` para guardar fecha de inicio,
  proximo pago y dias de gracia.
- El listado de tenants ahora devuelve datos basicos de suscripcion.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\super_admin_controller.py app\routes\super_admin.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 58 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

Actualizacion posterior:

- `app/core/tenant_status.py` calcula el estado efectivo usando
  `public.tenant_suscripciones`.
- Si vencio `fecha_proximo_pago` pero esta dentro de `dias_gracia`, el estado
  efectivo es `en_mora`.
- Si vencieron tambien los dias de gracia, el estado efectivo es `suspendido`.
- Esto se usa en login y en revalidacion de sesiones existentes.

## 2026-06-01 - Cierre fase SaaS super admin

Se cerraron endurecimientos previos a produccion para la operacion SaaS.

Archivos modificados/agregados:

- `app/controllers/auth_controller.py`
- `app/controllers/super_admin_controller.py`
- `app/routes/auth.py`
- `app/routes/super_admin.py`
- `app/core/tenant_status.py`
- `app/security.py`
- `apply_migration.py`
- `migrations/public/20260601_tenant_eventos_auditoria.sql`
- `migrations/20260601_usuarios_password_obligatorio.sql`
- `tests/test_super_admin.py`
- `tests/test_auth_tenant.py`
- `tests/test_apply_migration.py`

Cambio:

- El listado de tenants devuelve `estado` efectivo por fecha de pago y
  `estado_manual` como estado administrativo guardado.
- Se quito la creacion automatica de tablas publicas desde consultas normales.
  Las tablas publicas deben existir por migracion antes del deploy.
- `apply_migration.py` detecta archivos dentro de `migrations/public/` y los
  aplica contra `public`, incluso si no hay tenants registrados.
- Al crear colegio se exige password temporal fuerte para el admin inicial.
- El admin inicial se crea con `debe_cambiar_password = TRUE`.
- Se agrego `POST /auth/cambiar-password` para que el admin cambie la password
  temporal y apague `debe_cambiar_password`.
- Crear colegio registra evento en `public.tenant_eventos_auditoria`.
- `crear_cliente.py` y `setup_saas.py` se movieron a `scripts/legacy/` para
  evitar usarlos por error; el flujo oficial queda en el panel super admin.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\auth_controller.py app\controllers\super_admin_controller.py app\routes\auth.py app\routes\super_admin.py app\core\tenant_status.py app\security.py apply_migration.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py --basetemp=.pytest_tmp
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260530_super_admins.sql
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260601_tenant_estado_auditoria.sql
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260601_tenant_suscripciones.sql
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260601_tenant_eventos_auditoria.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260601_usuarios_password_obligatorio.sql
```

Resultado:

- Sintaxis OK.
- 33 pruebas enfocadas pasaron correctamente.
- Migraciones publicas SaaS registradas/aplicadas en local.
- `debe_cambiar_password` aplicado en `tenant_colegio_1` y `tenant_3333`.
- `listar_tenants_controller()` devolvio los colegios locales con `estado` y
  `estado_manual`.

## 2026-06-02 - Asignaciones activas y asignador unico

Se reestructuro el flujo de asignacion de clases para proteger historial
academico y dejar un solo asignador administrativo.

Archivos modificados/agregados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260602_asignaciones_activo.sql`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- `asignaciones` ahora usa `activo = TRUE/FALSE`.
- `DELETE /asignaciones/{asignacion_id}` desactiva la asignacion y conserva
  planes de clase, asistencia, notas, boletines y observaciones.
- Los listados actuales, horarios, clases del profesor y validaciones de cruce
  solo consideran asignaciones activas.
- Se agrego `GET /profesores/{profesor_id}/disponibilidad?dia=<dia>` para
  calcular rangos libres del profesor.
- El backend valida que las horas queden dentro de `06:30-12:30` o
  `12:30-18:30`.
- Si una asignacion ya tiene historial academico, no se permite cambiar
  profesor, curso o materia; se debe desactivar y crear una nueva.

Frontend relacionado:

- `src/components/AsignarClase.jsx` queda como unico asignador tipo formulario.
- `src/components/AsignarClaseGrid.jsx` se retiro porque ya no forma parte del
  flujo oficial.
- El admin selecciona primero curso, luego profesor/materia/dia/horas, ve
  disponibilidad del profesor y abajo el horario activo del curso.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\asignacion_controller.py app\routes\asignaciones.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_asignaciones_activo.py tests\test_asignaciones_pagination.py --basetemp=.pytest_tmp
python apply_migration.py migrations\20260602_asignaciones_activo.sql --dry-run
python apply_migration.py migrations\20260602_asignaciones_activo.sql
```

Resultado:

- Sintaxis backend OK.
- 5 pruebas enfocadas de asignaciones pasaron correctamente.
- Build frontend `pnpm run build` OK.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.

## 2026-06-04 - Reportes con egresos y balance

Se amplio el modulo de reportes para mostrar egresos y balance financiero.

Archivos modificados/agregados:

- `app/controllers/reportes_controller.py`
- `app/routes/reportes.py`
- `tests/test_reportes_pagination.py`
- `tests/test_anulaciones_financieras.py`
- `docs/API_ENDPOINTS.md`

Cambio:

- `GET /reportes/general` ahora incluye:
  - `total_egresos`;
  - `egresos_hoy`;
  - `balance_general`;
  - `balance_hoy`;
  - `egresos_mensuales`.
- Se agrego `GET /reportes/egresos-rango?inicio=YYYY-MM-DD&fin=YYYY-MM-DD`.
- El endpoint de egresos por rango conserva compatibilidad con respuesta lista
  simple si no se envia `limit`, y respuesta paginada si se envia `limit`.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest tests\test_reportes_pagination.py tests\test_anulaciones_financieras.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_reportes
```

Resultado:

- Ruff OK.
- 12 pruebas enfocadas de reportes/anulaciones pasaron correctamente.
- 127 pruebas completas pasaron correctamente.

## 2026-06-04 - Prestamos sin eliminacion y filtro por profesor

Se ajusto el modulo de prestamos para conservar trazabilidad financiera y
evitar borrado fisico.

Archivos modificados/agregados:

- `app/controllers/prestamo_controller.py`
- `app/routes/prestamos.py`
- `tests/test_prestamos_validaciones.py`
- `docs/API_ENDPOINTS.md`

Cambio:

- `GET /api/prestamos/` permite filtrar por `profesor_id`.
- `POST /api/prestamos/` valida profesor, monto mayor que 0 y estado inicial
  `Pendiente`.
- La fecha faltante se completa con el dia actual y las notas se normalizan con
  `strip()`.
- `PUT /api/prestamos/{prestamo_id}/estado` solo permite saldar con estado
  `Pagado`.
- `DELETE /api/prestamos/{prestamo_id}` queda bloqueado con `405`; los
  prestamos no se eliminan fisicamente.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest tests\test_prestamos_validaciones.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_prestamos
```

Resultado:

- Ruff OK.
- 9 pruebas enfocadas de prestamos pasaron correctamente.
- 125 pruebas completas pasaron correctamente.

## 2026-06-04 - Estados operativos de estudiantes y profesores

Se implemento manejo por estado para estudiantes y profesores, manteniendo
historial y evitando borrado fisico antes de produccion.

Archivos modificados/agregados:

- `app/schemas/estudiante.py`
- `app/controllers/estudiante_controller.py`
- `app/routes/estudiantes.py`
- `app/schemas/profesor.py`
- `app/controllers/profesor_controller.py`
- `app/routes/profesores.py`
- `app/controllers/auth_controller.py`
- `app/controllers/asignacion_controller.py`
- `app/controllers/planilla_excel_controller.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/notas_controller.py`
- `migrations/20260604_profesor_estado.sql`
- `tests/test_estudiantes_pagination.py`
- `tests/test_catalogos_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Estudiantes soportan estados `activo`, `retirado`, `egresado`, `inactivo`.
- Profesores soportan estados `activo`, `inactivo`.
- `GET /estudiantes` y `GET /profesores` filtran `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agregaron `PATCH /estudiantes/{estudiante_id}/estado` y
  `PATCH /profesores/{profesor_id}/estado`.
- Estudiantes que no estan `activo` quedan fuera de planillas, asistencia y
  boletines del flujo operativo del profesor, sin perder historial.
- Profesores `inactivo` no pueden iniciar sesion ni ser asignados/actualizados
  en asignaciones activas.
- El login ya no devuelve `access_token` ni `token_type` en JSON; la sesion
  queda por cookie `HttpOnly`.
- La migracion `20260604_profesor_estado.sql` agrega `profesor.estado`,
  normaliza profesores existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_profesor_estado.sql
```

Resultado:

- Ruff OK.
- 96 pruebas pasaron correctamente.
- Migracion aplicada en `tenant_colegio_1`, `tenant_3333` y `tenant_4444`.
- Frontend relacionado probado con `pnpm run build` y `pnpm run lint`.

## 2026-06-04 - Estado operativo de cursos

Se implemento manejo por estado para cursos, manteniendo historial academico y
evitando borrado fisico.

Archivos modificados/agregados:

- `app/schemas/curso.py`
- `app/controllers/curso_controller.py`
- `app/routes/cursos.py`
- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260604_cursos_estado.sql`
- `tests/test_catalogos_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Cursos soportan estados `activo` e `inactivo`.
- `GET /cursos` filtra `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agrego `PATCH /cursos/{curso_id}/estado`.
- Cursos `inactivo` no pueden usarse en nuevas asignaciones ni en ediciones de
  asignaciones activas.
- Las vistas operativas de asignaciones, horarios y clases del profesor filtran
  cursos activos para no seguir usando cursos cerrados.
- La migracion `20260604_cursos_estado.sql` agrega `cursos.estado`, normaliza
  cursos existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_cursos_estado.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_cursos_estado.sql
```

Resultado:

- Ruff OK.
- 99 pruebas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.
- Un dry-run posterior mostro la migracion como omitida por ya aplicada.

## 2026-06-04 - Estado operativo de materias

Se implemento manejo por estado para materias, manteniendo historial academico
y evitando borrado fisico.

Archivos modificados/agregados:

- `app/schemas/materia.py`
- `app/controllers/materia_controller.py`
- `app/routes/materias.py`
- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260604_materias_estado.sql`
- `tests/test_catalogos_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Materias soportan estados `activo` e `inactivo`.
- `GET /materias` filtra `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agrego `PATCH /materias/{materia_id}/estado`.
- Materias `inactivo` no pueden usarse en nuevas asignaciones ni en ediciones
  de asignaciones activas.
- Las vistas operativas de asignaciones, horarios y clases del profesor filtran
  materias activas para no seguir usando materias cerradas.
- La migracion `20260604_materias_estado.sql` agrega `materias.estado`,
  normaliza materias existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_materias
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_materias_estado.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_materias_estado.sql
```

Resultado:

- Ruff OK.
- 102 pruebas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.
- Un dry-run posterior mostro la migracion como omitida por ya aplicada.

## 2026-06-04 - Estado operativo de productos de inventario

Se implemento manejo por estado para productos de inventario, manteniendo
historial de ventas y evitando borrado fisico.

Archivos modificados/agregados:

- `app/schemas/inventario.py`
- `app/controllers/inventario_controller.py`
- `app/routes/inventario.py`
- `app/controllers/venta_controller.py`
- `app/routes/ventas.py`
- `migrations/20260604_inventario_estado.sql`
- `tests/test_inventario_pagination.py`
- `tests/test_anulaciones_financieras.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Productos de inventario soportan estados `activo` e `inactivo`.
- `GET /inventario` filtra `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agrego `PATCH /inventario/{item_id}/estado`.
- `DELETE /inventario/{item_id}` ahora desactiva el producto y conserva
  historial de ventas.
- Productos `inactivo` no aparecen para nuevas ventas y el backend rechaza
  intentos de venderlos por API.
- La migracion `20260604_inventario_estado.sql` agrega `inventario.estado`,
  normaliza productos existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_inventario
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_inventario_estado.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_inventario_estado.sql
```

Resultado:

- Ruff OK.
- 105 pruebas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.
- Un dry-run posterior mostro la migracion como omitida por ya aplicada.

## 2026-06-04 - Egresos filtrados por fecha y sin eliminacion fisica

Se ajusto el modulo de egresos para consultar por fechas y conservar
trazabilidad contable.

Archivos modificados/agregados:

- `app/controllers/egreso_controller.py`
- `app/controllers/nomina_controller.py`
- `app/routes/egresos.py`
- `migrations/20260604_egresos_origen.sql`
- `tests/test_egresos_fechas.py`
- `docs/API_ENDPOINTS.md`

Cambio:

- `GET /api/egresos/` devuelve por defecto solo los egresos del dia actual.
- Se agregaron filtros `fecha_desde` y `fecha_hasta`.
- Si se envia solo `fecha_desde`, se consulta ese dia.
- Si se envia rango, se valida que `fecha_desde <= fecha_hasta`.
- `POST /api/egresos/` valida concepto obligatorio, categoria obligatoria y
  monto mayor que 0 antes de insertar en base de datos.
- Los datos de texto del egreso se normalizan con `strip()` y la fecha faltante
  se completa con el dia actual.
- Se agrego `egresos.origen` para diferenciar egresos `manual` de egresos
  automaticos.
- Los egresos creados desde este modulo quedan con `origen = manual`.
- Los egresos creados por nomina quedan con `origen = nomina`.
- Se agrego `PUT /api/egresos/{egreso_id}` para editar solo egresos manuales.
- Si se intenta editar un egreso automatico, el backend responde `403`.
- `DELETE /api/egresos/{egreso_id}` queda bloqueado con `405`; los egresos no
  se eliminan fisicamente.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest tests\test_egresos_fechas.py
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_egresos_origen.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_egresos_origen.sql
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_egresos_edit
```

Resultado:

- Ruff OK.
- 11 pruebas enfocadas de egresos pasaron correctamente.
- 116 pruebas completas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.

## 2026-06-04 - Certificados usan notas de planilla como respaldo

Se ajusto la generacion administrativa de boletines/certificados para que las
notas se reflejen aunque todavia no exista una cabecera de boletin guardada.

Archivos modificados:

- `app/controllers/boletin_controller.py`

Cambio:

- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` mantiene primero la
  definitiva guardada en `boletin_cabecera`.
- Si esa definitiva no existe, calcula un promedio desde `notas_detalle` para
  el mismo estudiante, asignacion y periodo.
- Si la definitiva guardada es `0`, se trata como ausencia de definitiva y se
  permite usar el promedio real de planilla, porque las notas numericas validas
  del sistema van de 1 a 5.
- El promedio de respaldo solo considera `notas_detalle.nota > 0`.
- Las notas `0` guardadas en detalles de boletin no se devuelven como notas
  numericas validas por periodo.
- Se excluyen valoraciones de desarrollo del promedio numerico.

Motivo:

- Certificados y boletines administrativos deben poder mostrar notas ya
  registradas en planilla, incluso antes de que el profesor guarde el resumen
  final del boletin.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -c "import ast, pathlib; ast.parse(pathlib.Path('app/controllers/boletin_controller.py').read_text(encoding='utf-8'))"
```

Resultado:

- Sintaxis OK.

