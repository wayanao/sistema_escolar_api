# Funcionalidad: Año lectivo — Backend

## Control

- Estado: **Fase 1 en curso.** Fase 0 terminada el 2026-09-30. Migración A
  **aplicada en producción** el 2026-09-30, tras probarla en una rama de
  Neon; esquema base regenerado. Código que escribe el año (punto 2)
  **escrito y probado el 2026-09-30, sin desplegar**. Falta desplegarlo y la
  migración B. Ningún cambio de comportamiento visible.
- Tipo: Función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/ANIO_LECTIVO.md`, que cubre
  las pantallas.
- Riesgo: **Alto.** Toca migraciones de todos los tenants, el cálculo de
  cobros y cartera (dinero) y la forma en que se leen los datos académicos.
  Hay un colegio real en producción: `tenant_2005` (centro educativo la
  sabiduría de galapa), además de `tenant_colegio_1` (Colegio Demo).
- Fechas límite (reales, no estimadas):
  - **Principios de noviembre de 2026**: el colegio empieza a cobrar la
    matrícula 2027 en noviembre/diciembre. Para entonces tiene que existir
    el año 2027 "en preparación" y los pagos tienen que saber a qué año
    pertenecen (fases 0 a 5).
  - **1 de enero de 2027**: ese día el cálculo de deudas actual empieza a
    dar resultados falsos aunque no se toque nada (ver Diagnóstico, punto 2).
    La fase 2 tiene que estar en producción antes.
  - **Inicio de clases 2027** (febrero): fase 7, reutilizar el planeador
    anual y los planes de clase del año anterior.
- Regla operativa mientras tanto: **no registrar en el sistema matrículas
  ni pagos de 2027 hasta que la fase 5 esté en producción.** Antes de la
  fase 1, el relleno los marcaría como 2026; entre la fase 1 y la 5 no existe
  todavía un año 2027 donde ponerlos. Al 2026-09-30 no hay ninguno
  registrado (confirmado por el usuario).
- Última actualización: 2026-09-30.

## Objetivo

Que el sistema entienda qué es un año lectivo, sin que el colegio en
producción note nada hasta que exista un segundo año:

1. Cada año tiene sus propios cursos, matrículas, notas, asistencia,
   boletines y cobros, sin mezclarse con los de otros años.
2. El administrador puede consultar e imprimir años pasados (solo lectura).
3. Los cobros y la cartera calculan por año y muestran aparte la deuda de
   años anteriores.
4. Preparar el año siguiente (copiar cursos, matricular, cobrar matrícula)
   y activarlo es un flujo guiado, no un trabajo manual en la base de datos.

## Diagnóstico (verificado en el código el 2026-09-29)

### 1. Hoy no existe la dimensión "año"

- `notas`, `notas_detalle`, `boletin_cabecera`, `observaciones`,
  `asistencia`, `planeador_anual` y `observador_anotaciones` guardan
  `periodo` (1 a 4) **sin año**.
- Varias restricciones únicas asumen un solo año: `boletin_cabecera
  (estudiante_id, asignacion_id, periodo)`, `observaciones (estudiante_id,
  asignacion_id, periodo)`, `planeador_anual (asignacion_id, periodo,
  slot)`. Si un curso se reutilizara de un año a otro, el boletín de un
  estudiante que repite el año **sobrescribiría** el del año anterior.
- Cada estudiante tiene un único curso: `estudiantes.curso_id`.
- Restos sin uso: la columna `estudiantes.anio_escolar` (ningún código de
  `app/` la lee ni la escribe; solo `scripts/seed_tenant_performance.py`) y
  la tabla `matriculas (estudiante_id, curso_id, anio)`, que ningún código de
  `app/` usa (solo `scripts/limpiar_tenant_colegio_1_operativo.py` la
  vacía).

### 2. Los cobros mezclan años: error que llega solo el 1 de enero de 2027

Dos causas, en `app/services/cobros.py` y `app/services/cartera.py`:

- `obtener_pagos_por_concepto_estudiantes` (`cobros.py:170`) suma **todos
  los pagos de la historia** de un concepto, sin mirar el año.
- `listar_cuotas_vencidas` (`cartera.py:42`) arma las cuotas con
  `hoy.year`: solo existen las cuotas del año calendario en curso.

Simulación hecha el 2026-09-29 con `calcular_deudas_desde_contexto` y las
reglas reales (matrícula anual de $300.000, mensualidad de $200.000 de
febrero a noviembre, día límite 5):

| Caso | Fecha | Lo que dice el sistema | Lo correcto |
|---|---|---|---|
| A. Pagó todo 2026; nada de 2027 | 15-mar-2027 | Debe **$0** | Debe matrícula 2027 + febrero y marzo |
| B. Quedó debiendo oct y nov de 2026 ($400.000) | 15-ene-2027 | Debe **$0** | Debe $400.000 de 2026 |

En el caso A el sistema usa lo pagado en 2026 como si fuera de 2027. En el
caso B la deuda de 2026 desaparece porque ya no existen cuotas de 2026.

Efectos relacionados:

- `_periodos_programados` (`app/controllers/pagos_controller.py:123`) solo
  ofrece adelantos de meses del año en curso: en diciembre de 2026 no se
  pueden recibir adelantos de 2027.
- Una matrícula 2027 pagada en noviembre de 2026 se sumaría a la matrícula
  2026.

### 3. El boletín depende del curso actual del estudiante

`app/repositories/boletin_repository.py` une `e.curso_id = a.curso_id` con
`a.activo = TRUE` (líneas 103, 181, 261, 343). Si un estudiante pasa de
Primero a Segundo, su boletín de Primero ya no se puede generar. Lo mismo
pasa con cualquier consulta que llegue a los datos académicos a través de
`estudiantes.curso_id` (35 usos en `app/`, ver inventario en fase 3).

### 4. Las materias son una sola lista para todos los años

`materias` no lleva año, y no debe llevarlo: "Matemáticas" es la misma
materia siempre. Pero dos cosas que se hagan sobre una materia en 2027
alcanzarían a 2026:

- **Cambiarle el nombre**: el boletín y los certificados toman el nombre en
  el momento de imprimir (`JOIN materias`), así que un boletín de 2026
  reimpreso saldría con el nombre nuevo.
- **Desactivarla**: `leer_materias_del_estudiante`
  (`boletin_repository.py:153` y `:198`) oculta a propósito las materias
  inactivas, "tampoco en los periodos ya calificados". Desactivar en 2027 una
  materia que ya no se dicta la borraría de los boletines de 2026.

Cambiar asignaciones o agregar materias en 2027 **no** alcanza a 2026: las
asignaciones cuelgan de los cursos de cada año. Ver decisiones 12 y 13.

### 5. Cómo se consultó

Lectura del esquema base (`migrations/base/20260813_esquema_base_tenant.sql`)
y de los archivos citados. La simulación del punto 2 se corrió con el
`venv` del repo, sin base de datos, contra las funciones reales. En la fase 0
se convierte en prueba.

## Decisiones ya tomadas (con el usuario, 2026-09-29)

1. **Los cursos se crean nuevos cada año** ("Primero A 2026" y "Primero A
   2027" son filas distintas), copiados del año anterior con un botón.
2. **La deuda de años anteriores se sigue viendo**, separada de la del año,
   en estado de cuenta y cartera. Nada se pierde ni se mezcla.
3. **Años cerrados: solo el admin los ve, y solo para consultar.** Nadie
   edita datos académicos de un año cerrado. Si hay que corregir algo, el
   admin reabre el año a propósito.
4. **Los profesores solo ven el año activo.** Consecuencia directa de la 3.
5. **La matrícula del año siguiente se cobra en noviembre/diciembre**, así
   que el año siguiente tiene que poder existir "en preparación" y recibir
   pagos mientras el año actual sigue activo.
6. **Un pago se registra en el año de la deuda que salda**, aunque ese año
   esté cerrado. Es la única excepción a "solo consulta": recibir o anular
   dinero sí, editar notas no.
7. **Concepto "único"** (palabras del usuario): "se paga una vez y sí se
   puede volver a usar más adelante; es un pago para una actividad
   específica: la pagan, se desactiva y se activa cuando quiera; si el
   estudiante debe, la deuda le queda hasta que la pague". Ver cómo se
   traduce en la fase 2 y el hallazgo relacionado en "Hallazgos fuera de
   alcance".
8. **Becas, descuentos y valores especiales por estudiante**: se copian al
   año nuevo, pero **quedan en espera hasta que el estudiante se matricule**
   en ese año; al matricularlo se asignan a su nuevo grado y el admin los
   revisa. Cambiar el de 2027 no altera lo cobrado en 2026.
9. **No se activa el año nuevo hasta decidir por cada estudiante.** Todo
   estudiante activo del año que termina tiene que quedar matriculado en el
   año nuevo o marcado explícitamente como "no continúa". Si falta alguno,
   el sistema no deja activar.
10. **Calendario A** (febrero a noviembre): año lectivo = año calendario.
    Supuesto planteado al usuario y no objetado; se apoya en que
    `tenant_2005` usa noviembre como último mes de mensualidad. Un colegio de
    calendario B necesitaría rediseñar la fase 2 (ver "Fuera de alcance").
11. El frontend nunca decide qué año es editable ni qué se cobra: lo decide
    el backend (regla del proyecto).

Agregadas el 2026-09-30:

12. **Renombrar una materia que se usa en otro año: avisar y dejar
    elegir.** El sistema avisa que el nombre también cambiará en los
    boletines y certificados de ese otro año, y ofrece dos caminos: cambiarlo
    igual (sirve para corregir un error de escritura) o crear una materia
    nueva para el año nuevo.
13. **Un año cerrado se ve como se veía el día que se cerró.** *Reemplazada
    el 2026-09-30* tras los números de la fase 0. La versión anterior
    ("en años cerrados mostrar todas las materias dictadas") habría hecho
    reaparecer en los boletines de 2026 tres materias que el colegio ocultó
    a propósito (ver resultados de la fase 0). Regla nueva: al cerrar un año
    por primera vez, el sistema guarda qué materias estaban inactivas en ese
    momento. Los boletines de ese año ocultan exactamente esas, sin importar
    lo que se active o desactive después. En el año activo y en el de
    preparación sigue la regla de hoy: se ocultan las inactivas.
14. **Planeador anual: lo trae el profesor, con un botón.** En su planeador
    de 2027, si está vacío, aparece "Traer el planeador del año pasado".
    Nunca sobrescribe lo que ya haya escrito.
15. **El planeador y los planes siguen al curso y la materia, no a la
    persona.** Si en 2027 cambió el profesor, el profesor nuevo puede traer
    lo de 2026 de esa materia en ese curso.
16. **Planes de clase: usar uno viejo como base.** Al crear un plan en 2027,
    el profesor elige uno de 2026, el formulario se llena con su texto, lo
    ajusta, pone la fecha nueva y lo envía a revisión como un plan nuevo.
    Las evidencias (imágenes o PDF) **no** se copian: se borran del
    almacenamiento al reemplazarse o al borrar el plan
    (`app/services/storage.py: delete_file`), y compartirlas entre dos planes
    rompería uno al tocar el otro.

Las decisiones 14 a 16 son la única excepción a la decisión 4: el profesor
recibe contenido de 2026, pero no navega 2026. El backend deduce el origen a
partir de la asignación de 2027 del profesor; el profesor nunca manda ids de
2026 para listar.

17. **Los conceptos de pago también son por año, copiados como los
    cursos.** Agregada el 2026-09-30 tras los números de la fase 0: en
    `tenant_2005` la mensualidad va de julio a noviembre (empezaron a usar el
    sistema en julio) y la matrícula está desactivada. Para 2027 se querrá
    la mensualidad desde febrero y la matrícula activa. Con un concepto
    único para todos los años, cambiar el mes inicial habría creado en 2026
    cinco cuotas falsas (febrero a junio) para 174 estudiantes, y activar la
    matrícula habría puesto a todos a "deber" la de 2026. Al preparar 2027
    se copian los conceptos de 2026 con toda su configuración, y se ajustan
    en 2027 sin tocar 2026.

## La idea central: el año cuelga del curso

Casi todo lo académico ya depende de un curso. Si el curso pertenece a un
año, todo lo que cuelga de él queda separado por año **sin tocar esas
tablas**:

```text
anios_lectivos            (2026 activo, 2027 en preparación...)
 ├── cursos.anio_lectivo_id                  ← la única columna nueva en lo académico
 │    ├── asignaciones → notas, notas_detalle, boletin_cabecera/detalles,
 │    │                  asistencia, observaciones, planeador_anual, plan_de_clases
 │    ├── tipos_pagos_cursos (precios por curso: cada año tiene los suyos)
 │    ├── listas_seguimiento_columnas → marcas
 │    └── director_grupo_id (cada año tiene su director)
 ├── tipos_de_pagos.anio_lectivo_id          ← conceptos de pago por año (decisión 17)
 │    ├── tipos_pagos_cursos (también cuelga del curso del mismo año)
 │    ├── tipos_pagos_estudiantes (becas y valores especiales: por año sin columna nueva)
 │    └── pagos_aplicaciones.tipo_pago_id
 ├── matriculas (estudiante, curso, año)     ← en qué curso estuvo cada estudiante cada año
 ├── pagos.anio_lectivo_id                   ← a qué año pertenece cada pago
 └── observador_anotaciones.anio_lectivo_id  ← no cuelga de un curso
```

Por qué así:

- Las restricciones únicas actuales (boletín, observaciones, planeador,
  horarios, el disparador `validar_profesor_responsable_materia_curso`)
  siguen siendo correctas: una asignación de 2027 es otra fila, sobre otro
  curso, y no choca con la de 2026.
- Es el cambio más pequeño posible: en lo académico se agrega una sola
  columna (`cursos.anio_lectivo_id`), no una por tabla.

No llevan año, a propósito:

- `estudiantes`, `profesor`, `usuarios`, `materias`: son personas o
  catálogos que viven a través de los años. Para que editar una materia no
  altere la historia, ver decisiones 12 y 13.
- `inventario`, `ventas`, `egresos`, `nomina`, `prestamos`: se rigen por
  fecha, no por año lectivo; los reportes financieros ya filtran por fechas.

## La regla del "curso vigente"

`estudiantes.curso_id` **se conserva** y pasa a significar: *el curso del
estudiante en el año activo*, o `NULL` si no está matriculado en el año
activo.

- Por qué: 35 consultas de `app/` la usan (permisos de profesor, planilla,
  asistencia, notas, observador, dashboard). Como los profesores solo
  trabajan en el año activo, todas siguen siendo correctas **sin tocarlas**.
  Eso deja fuera de riesgo todo el flujo del profesor y la capa de permisos
  (`app/core/permissions.py`).
- La fuente de verdad del historial es `matriculas`. `estudiantes.curso_id`
  es una copia de la matrícula del año activo.
- **Un solo lugar escribe esa copia**: la función
  `sincronizar_curso_vigente(cursor, estudiante_id)` del servicio nuevo
  `app/services/anio_lectivo.py`. La llaman crear y editar estudiante,
  matricular y activar el año. Ningún otro código hace
  `UPDATE estudiantes SET curso_id`.
- **Mientras no exista un segundo año (fases 1 a 4), la copia va al revés**,
  y así quedó implementado el 2026-09-30: el formulario de estudiantes sigue
  editando `estudiantes.curso_id`, y
  `sincronizar_matricula_del_anio_activo`
  (`app/repositories/anios_lectivos_repository.py`) deja la matrícula del
  año activo igual a ese curso. Con un solo año las dos direcciones dan lo
  mismo. La dirección definitiva (matrícula → `estudiantes.curso_id`, con
  `sincronizar_curso_vigente`) entra en la fase 5, cuando se pueda
  matricular en un año distinto del activo.
- Un estudiante nuevo matriculado solo en el año en preparación queda con
  `curso_id = NULL` hasta que ese año se active. Así no aparece en las
  pantallas de los profesores del año actual, y un profesor con clases
  preparadas para el año siguiente no gana acceso a él antes de tiempo.
- Consulta de control, debe devolver **0 filas** en todo momento:

```sql
SELECT e.id
FROM estudiantes e
LEFT JOIN matriculas m
       ON m.estudiante_id = e.id
      AND m.anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
WHERE e.curso_id IS DISTINCT FROM m.curso_id;
```

## Diseño de datos

### Tabla nueva `anios_lectivos`

```sql
CREATE TABLE IF NOT EXISTS anios_lectivos (
    id SERIAL PRIMARY KEY,
    anio SMALLINT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'preparacion',
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activado_en TIMESTAMP,
    cerrado_en TIMESTAMP,
    CONSTRAINT anios_lectivos_anio_key UNIQUE (anio),
    CONSTRAINT chk_anios_lectivos_anio CHECK (anio BETWEEN 2000 AND 2100),
    CONSTRAINT chk_anios_lectivos_estado
        CHECK (estado IN ('preparacion', 'activo', 'cerrado', 'reabierto'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_anios_lectivos_un_activo
    ON anios_lectivos (estado) WHERE estado = 'activo';
CREATE UNIQUE INDEX IF NOT EXISTS idx_anios_lectivos_una_preparacion
    ON anios_lectivos (estado) WHERE estado = 'preparacion';
```

Estados:

| Estado | Qué significa | Quién escribe datos académicos |
|---|---|---|
| `preparacion` | Se arma el año siguiente: cursos, precios, carga académica, matrículas, pagos de matrícula | Solo admin |
| `activo` | El año en que se trabaja. Exactamente uno | Admin y profesores |
| `cerrado` | Año terminado. Solo consulta | Nadie (pagos: ver decisión 6) |
| `reabierto` | Año pasado abierto a propósito por el admin para corregir | Solo admin |

Los dos índices únicos parciales hacen que la base de datos misma impida
tener dos años activos o dos en preparación a la vez. `reabierto` se declara
desde la primera migración para no necesitar otra más adelante; su uso se
implementa en la fase 6.

No se agregan fechas de inicio y fin: en calendario A el año lectivo es el
año calendario y los meses de cobro ya viven en `tipos_de_pagos`
(`mes_inicial`, `mes_final`).

### `cursos.anio_lectivo_id`

- Columna nueva, clave foránea a `anios_lectivos(id)`, con índice.
- Los cursos existentes se asignan a 2026.
- El índice único `idx_cursos_nombre_jornada_unico` se rehace incluyendo
  `anio_lectivo_id`: "Primero A / Mañana" puede existir una vez **por año**.
- Se agrega `UNIQUE (id, anio_lectivo_id)` en `cursos`, necesario para la
  clave foránea compuesta de `matriculas`.

### `matriculas` (tabla existente, se reutiliza)

- Se verifica en la fase 0 que esté vacía en los dos tenants.
- Columna nueva `anio_lectivo_id`, con `UNIQUE (estudiante_id,
  anio_lectivo_id)`: un estudiante, un curso por año.
- Clave foránea compuesta `(curso_id, anio_lectivo_id) REFERENCES cursos (id,
  anio_lectivo_id)`: la base de datos misma impide matricular a alguien en
  2027 con un curso de 2026.
- Se rellena con una fila por estudiante que hoy tiene curso:
  `(e.id, e.curso_id, <id de 2026>)`.
- La columna vieja `anio` queda como está, sin uso. No se borra sin
  permiso del usuario (regla del proyecto).
- La marca "no continúa" (decisión 9) se agrega en la fase 6, no antes.

### `pagos.anio_lectivo_id`

- Columna nueva, clave foránea, índice `(estudiante_id, anio_lectivo_id)`.
- Todos los pagos existentes se asignan a 2026. Correcto también para una
  matrícula 2026 pagada en diciembre de 2025: pertenece al año 2026. La
  fase 0 confirma con números que no hay datos de un año lectivo anterior.
- Los pagos de ventas (`venta_id` no nulo) también llevan año, el activo al
  momento de la venta. Así la regla es simple: todo pago tiene año.
- `pagos_aplicaciones.periodo` ya es una fecha (primer día del mes), así que
  ya lleva su año. En la fase 2 se valida que los meses aplicados
  pertenezcan al año del pago.

### `observador_anotaciones.anio_lectivo_id`

No cuelga de un curso (es estudiante + profesor + periodo), así que necesita
su propio año. Columna nueva, clave foránea, índice `(estudiante_id,
anio_lectivo_id)`; las existentes se asignan a 2026.

### `tipos_de_pagos.anio_lectivo_id` (decisión 17)

- Columna nueva, clave foránea, índice. Los conceptos existentes se asignan
  a 2026.
- La restricción `tipos_de_pagos_nombre_key UNIQUE (nombre)` se reemplaza
  por `UNIQUE (nombre, anio_lectivo_id)`: "MENSUALIDAD" puede existir una vez
  **por año**.
- Los pagos guardan el **nombre** del concepto como texto (`pagos.tipo_pago`)
  y `cobros.py` los empareja por nombre. Dentro de un año el nombre sigue
  siendo único, así que con `pagos.anio_lectivo_id` ese emparejamiento sigue
  funcionando sin cambiar cómo se guarda un pago.
- Lo que cuelga del concepto queda por año sin columnas nuevas:
  - `tipos_pagos_cursos` (precio por curso): concepto y curso tienen que ser
    del mismo año, y el código lo valida al guardar.
  - `tipos_pagos_estudiantes` (becas y valores especiales): la copia "en
    espera" de la decisión 8 pasa las filas del concepto de 2026 a su copia
    de 2027 cuando el estudiante se matricula.
  - `pagos_aplicaciones.tipo_pago_id`: el concepto debe ser del año del pago
    (se valida en la fase 2).
- Para saber de qué concepto de 2026 salió cada uno de 2027, la fase 5
  agrega `tipos_de_pagos.tipo_pago_origen_id`, igual que
  `cursos.curso_origen_id`.

### `anios_lectivos_materias_ocultas` (fase 6, decisión 13)

Tabla nueva `(anio_lectivo_id, materia_id)`, con clave primaria compuesta.
Se llena al cerrar un año **por primera vez** con las materias inactivas en
ese momento. Reabrir y volver a cerrar no la cambia. El boletín de un año
cerrado o reabierto oculta las materias de esta lista, en vez de mirar el
estado actual de la materia.

### Lo que no se toca

- `estudiantes.anio_escolar`: legado sin uso. No se borra sin permiso.
- `estudiantes.descuento_matricula` y `descuento_mensualidad`: se guardan en
  la ficha, pero `cobros.py` no los usa. Fuera de alcance.

### Colegios nuevos

`crear_tenant_controller` (`app/controllers/super_admin_controller.py:174`)
aplica el esquema base y siembra filas iniciales
(`app/repositories/super_admin_repository.py:170`, `institucion_branding`).
Ahí mismo se inserta el año actual como `activo`. Prueba en
`tests/test_tenant_provisioning.py`.

## Cómo viaja el año entre frontend y backend

- Los **listados** (cursos, estudiantes, asignaciones del admin, cartera,
  reportes académicos, dashboard admin, observador) aceptan un parámetro
  opcional `anio_lectivo_id`. **Si no llega, se usa el año activo.** Así el
  frontend actual sigue funcionando igual, sin cambios, mientras se
  despliegan las fases.
- Los endpoints que reciben un `curso_id` o un `asignacion_id` **no
  necesitan año**: el id ya lo implica.
- El profesor no puede pedir otro año: si un profesor manda un
  `anio_lectivo_id` distinto del activo, 403.
- El año **no** viaja en una cabecera ni en el JWT ni en la cookie. Es una
  elección de lo que se está mirando, no parte de la identidad. Si estuviera
  en la sesión, una pestaña vieja podría escribir en el año equivocado sin
  que nadie lo note.

## La guardia de escritura (una sola regla, un solo lugar)

`app/services/anio_lectivo.py` expone `exigir_anio_editable(cursor,
anio_lectivo_id, usuario)` y dos ayudas para averiguar el año:
`anio_de_curso(cursor, curso_id)` y `anio_de_asignacion(cursor,
asignacion_id)`.

| Estado del año | Admin | Profesor |
|---|---|---|
| `activo` | Sí | Sí |
| `preparacion` | Sí | No (403) |
| `reabierto` | Sí | No (403) |
| `cerrado` | No (409) | No (409) |

- Mensaje del 409, en español y listo para mostrar: `El año lectivo 2026
  está cerrado. Solo se puede consultar.`
- Excepción de dinero (decisión 6): registrar o anular un pago en un año
  cerrado está permitido al admin.
- Efecto práctico al activar el año nuevo: si un profesor tenía abierta la
  planilla de 2026, su siguiente guardado recibe el 409 con ese mensaje, en
  vez de escribir en un año cerrado.

## Plan de fases

Un paso a la vez, con el visto bueno del usuario antes de empezar cada uno.
Cada fase deja producción funcionando igual que antes o mejor, nunca a
medias. El orden importa: está puesto para que ninguna fase dependa de algo
que no exista todavía.

### Fase 0 — Medir y blindar (sin cambios de comportamiento)

1. **Números reales de los dos tenants** (solo lectura). Los corre el
   usuario, en producción en modo lectura o en una rama de Neon, y pega el
   resultado en este documento. El asistente no se conecta a producción.

   ```sql
   SELECT COUNT(*) FROM matriculas;                               -- se espera 0
   SELECT COUNT(*) FROM estudiantes WHERE anio_escolar IS NOT NULL;
   SELECT COUNT(*), COUNT(curso_id) FROM estudiantes;
   SELECT COALESCE(LOWER(estado), 'activo'), COUNT(*) FROM estudiantes GROUP BY 1;
   SELECT COUNT(*) FROM cursos;
   SELECT COUNT(*) FROM asignaciones;
   SELECT EXTRACT(YEAR FROM COALESCE(fecha, fecha_pago::timestamp)) AS anio,
          COUNT(*), SUM(monto)
   FROM pagos GROUP BY 1 ORDER BY 1;
   SELECT MIN(fecha), MAX(fecha) FROM asistencia;
   SELECT MIN(fecha), MAX(fecha) FROM notas_detalle;
   SELECT MIN(creada_en), MAX(creada_en) FROM observador_anotaciones;
   SELECT MIN(periodo), MAX(periodo) FROM pagos_aplicaciones;
   SELECT id, nombre, tipo_cobro, activo, mes_inicial, mes_final FROM tipos_de_pagos;
   -- Materias inactivas que ya tienen notas o boletines (decisión 13):
   SELECT m.id, m.nombre,
          COUNT(DISTINCT nd.id) AS notas, COUNT(DISTINCT bc.id) AS boletines
   FROM materias m
   JOIN asignaciones a ON a.materia_id = m.id
   LEFT JOIN notas_detalle nd ON nd.asignacion_id = a.id
   LEFT JOIN boletin_cabecera bc ON bc.asignacion_id = a.id
   WHERE COALESCE(LOWER(m.estado), 'activo') <> 'activo'
   GROUP BY m.id, m.nombre;
   ```

   Si aparece un año lectivo anterior a 2026 con datos, **se detiene el
   plan** y se diseña su relleno aparte: la fase 1 asume que todo lo
   existente es de 2026.

   ¿Hay estudiantes o pagos registrados **para 2027**? **Respondida el
   2026-09-30: no**, todavía no se ha registrado ninguna matrícula para 2027.
   Si antes de la fase 1 se registra alguna (contra la regla operativa del
   Control), se lista aquí para que la fase 1 la asigne a 2027.

   **Resultados del 2026-09-30, `tenant_2005`** (corridos por el usuario en el
   SQL Editor de Neon, en una sola consulta equivalente, sin montos):

   | Dato | Valor |
   |---|---|
   | `matriculas` | 0 |
   | Estudiantes con `anio_escolar` | 0 |
   | Estudiantes total / con curso | 174 / 174 |
   | Estudiantes por estado | activo: 170, retirado: 4 |
   | Cursos | 12 |
   | Asignaciones | 267 |
   | Pagos por año (cantidad) | año 8: 1; 2026: 545 |
   | Asistencia (primera / última) | 2026-07-13 / 2026-09-30 |
   | `notas_detalle.fecha` (primera / última) | vacía (`NULL`): las notas existen pero no guardan fecha |
   | Observador (primera / última) | 2026-09-11 / 2026-09-28 |
   | Adelantos (primer / último mes) | 2026-07-01 / 2026-11-01 |
   | Conceptos de pago | MENSUALIDAD (mensual, activo, meses 7–11); MATRICULA (anual, **inactivo**, meses 2–12) |
   | Materias inactivas con notas | GEOMETRÍA (103 notas, 34 boletines); ORTOCALIGRAFÍA (58, 15); PROYECTO (11, 0) |

   Qué se concluyó:

   - **Todo es de 2026.** El colegio empezó a usar el sistema en julio de
     2026. No hay año lectivo anterior: el plan sigue, y la fase 1 puede
     asignar todo a 2026.
   - El pago del "año 8" es un error de digitación de fecha, no un año
     lectivo. La fase 1 lo asigna a 2026 como al resto. El usuario decidió
     **dejarlo así** (ver "Hallazgos fuera de alcance").
   - La fase 1 creará 174 matrículas de 2026, una por estudiante (los 4
     retirados incluidos, con su curso actual).
   - Mensualidad de julio a noviembre y matrícula inactiva → **decisión 17**
     (conceptos por año).
   - Las tres materias inactivas se ocultaron a propósito (commit `add69c1`
     del 2026-09-24, "no mostrar asignaturas inactivas") → **decisión 13
     reemplazada** ("como se veía al cerrar").
   - No hay conceptos de tipo "único" hoy.
   - `tenant_colegio_1` (demo, sin usuarios reales) no se midió: no hace
     falta para decidir. La migración se le aplica igual.
2. **Pruebas de caracterización** (fijan cómo funciona hoy, antes de
   cambiar nada):
   - Cobros dentro del año activo: estado de cuenta, cuotas vencidas,
     adelantos disponibles y cartera, con `hoy` fijo en 2026. La fase 2 debe
     dejarlas iguales.
   - El cambio de año: los casos A y B del diagnóstico, escritos como
     pruebas que documentan el error actual. En la fase 2 se invierten para
     exigir el resultado correcto.
   - Listados que la fase 3 va a tocar: cursos, estudiantes, boletín,
     asignaciones del profesor y conceptos de pago. Deben devolver lo mismo
     después de la fase 3 cuando se pide el año activo.
3. Terminado cuando: las pruebas nuevas pasan, `python scripts/verify.py`
   pasa y los números están pegados aquí.

**Avance del 2026-09-30 — cobros (los dos primeros puntos de 2):**

- Archivo nuevo `tests/test_anio_lectivo_cobros_caracterizacion.py`, 11
  pruebas, sin base de datos (funciones puras y `monkeypatch`, como el resto
  de pruebas de cobros):
  - **Dentro del año** (la fase 2 debe dejarlas iguales): deuda sin pagos
    por tipo de concepto (anual, mensual, único; opcional no genera deuda),
    pagos restados por concepto, diciembre cuenta las 10 cuotas hasta
    noviembre, concepto sin precio en el curso no genera deuda, y concepto
    inactivo no genera deuda (fija el hallazgo fuera de alcance).
  - **Error actual al cambiar de año** (prefijo `test_error_actual_`; la fase
    2 las invierte): caso A, caso B, segunda matrícula sumada a la del año en
    curso, meses vencidos de 2026 que desaparecen en enero, meses vencidos de
    2027 cubiertos con pagos de 2026, y adelantos de diciembre sin meses del
    año siguiente.
- Ya existían, y también sirven de red para la fase 2:
  `test_pagos_meses_vencidos.py`, `test_pagos_adelantados.py`,
  `test_tipos_pagos_mes_final.py` y `test_reportes_estado_cuenta.py`.
- Verificación: `python scripts/verify.py` → **1445 pruebas pasan** (antes
  1434), ruff y `pip check` limpios. `git diff --check` limpio.

**Avance del 2026-09-30 — listados (tercer punto de 2). Con esto la fase 0
queda terminada:**

- Revisión previa de lo que ya existía. Estos listados ya tenían fijada la
  respuesta completa y sus parámetros, y sirven tal cual para la fase 3:
  estudiantes (`test_asignaciones_estudiantes_caracterizacion.py`), "mis
  clases" del profesor (`test_asignaciones_pagination.py`), boletín
  (`test_boletin_caracterizacion.py`, que además fija el conjunto exacto de
  SQL del dominio y fallará a propósito cuando la fase 3 lo cambie) y el
  conteo y alta de listas de seguimiento en todos los cursos
  (`test_listas_seguimiento_repositorio.py`).
- Archivo nuevo `tests/test_anio_lectivo_listados_caracterizacion.py`, 6
  pruebas, solo para lo que faltaba:
  - Cursos: respuesta completa del listado (con el filtro `activo` por
    defecto y con `todos`) y del paginado, con el orden exacto de los
    parámetros. Antes solo se revisaban campos sueltos.
  - Conceptos de pago, que no tenían ninguna prueba: `/tipos-pagos`,
    `/tipos-pagos/detallado` (configuración completa y cursos por concepto)
    y `/tipos-pagos/{id}/cursos`. Los datos imitan a `tenant_2005`:
    mensualidad de julio a noviembre y matrícula inactiva.
- Límite conocido: son dobles de cursor, sin base de datos. Fijan el
  contrato de la respuesta, no que el SQL filtre bien por año; eso se
  comprueba en la fase 3 contra una rama de Neon.
- Corrección del inventario de la fase 3: `asignaciones_repository.py:181` y
  `:238` sí filtran por id (el `WHERE id = %s` está en otra línea y la
  búsqueda del 2026-09-29 no lo vio). No necesitan filtro por año y salen
  del inventario.
- Verificación: `python scripts/verify.py` → **1451 pruebas pasan** (antes
  1445), ruff y `pip check` limpios. `git diff --check` limpio.

### Fase 1 — Fundación de datos (invisible)

Nada cambia en pantalla ni en ninguna respuesta de la API.

1. **Migración A** `migrations/AAAAMMDD_anios_lectivos.sql`: crea
   `anios_lectivos`, inserta 2026 como `activo`, agrega las columnas de
   `cursos`, `tipos_de_pagos`, `matriculas`, `pagos` y
   `observador_anotaciones` **admitiendo nulos**, las rellena con 2026, llena
   `matriculas` y rehace los índices únicos de cursos (nombre + jornada) y de
   conceptos (nombre), ahora con el año incluido. El año va escrito como `2026`, no calculado con la fecha del
   día: dice "todo lo existente es de 2026" aunque la migración se aplique
   tarde.
2. **Código que escribe el año** en toda fila nueva: crear curso
   (`curso_controller.py:71`), crear concepto de pago
   (`tipos_pagos_controller.py:24`), crear pago (`pagos_repository.py:23` y `:37`),
   crear anotación (`observador_repository.py:187`), crear y editar
   estudiante (matrícula del año activo + `sincronizar_curso_vigente`). Más
   el alta de colegios nuevos. Nuevo: `app/services/anio_lectivo.py` con
   `obtener_anio_activo` y `sincronizar_curso_vigente`, más sus pruebas.
   **Hecho el 2026-09-30**, con un diseño más simple que este: ver el
   "Avance" del punto 2 más abajo.
3. **Migración B** `migrations/AAAAMMDD_anios_lectivos_obligatorio.sql`:
   vuelve a rellenar lo que se haya creado entre la migración A y el
   despliegue del código, y pone `NOT NULL` en las columnas nuevas. Debe
   cubrir también un colegio dado de alta en esa ventana: el esquema base
   trae la tabla pero no la fila del año (es solo estructura), así que B
   inserta el año activo si falta antes de rellenar. Y debe **re-sincronizar
   las matrículas del año activo** con `estudiantes.curso_id`: en la ventana,
   el código de hoy crea estudiantes sin matrícula y cambia cursos sin tocar
   la matrícula. B inserta las que faltan y corrige las que no coinciden
   (en esa ventana `estudiantes.curso_id` es la fuente de verdad). Al
   terminar, la consulta de control del curso vigente debe dar 0. **B se
   aplica después de desplegar el código del punto 2, nunca antes**: con
   `NOT NULL`, el código viejo, que no escribe el año, fallaría al crear
   cualquier curso, concepto, pago o anotación. Fuera de `app/` quedan dos
   scripts que insertan sin año y fallarían después de B:
   `scripts/copiar_observaciones_al_observador.py` (copia histórica ya
   hecha) y `scripts/seed_tenant_performance.py` (datos de prueba). No se
   tocan; si alguno se vuelve a usar, habrá que darle el año.
4. Orden seguro, el de `docs/MIGRACIONES.md`: probar en rama de Neon →
   `apply_migration.py --dry-run` → aplicar A → regenerar el esquema base
   desde `tenant_colegio_1` → desplegar el código → aplicar B → regenerar el
   esquema base otra vez. Migración y esquema base se commitean juntos
   (`tests/test_esquema_base.py` lo exige).
5. Terminado cuando: la consulta de control del curso vigente da 0 filas en
   los dos tenants, todas las pruebas de la fase 0 siguen iguales,
   `verify.py` pasa y el usuario confirma en local que no cambió nada
   visible.

**Avance del 2026-09-30 — migración A escrita (punto 1), no aplicada:**

- `migrations/20260930_anios_lectivos.sql`. Hace lo descrito en "Diseño de
  datos" para la fase 1, con dos frenos al estilo de
  `20260825_observaciones_claves_foraneas.sql`: al inicio, si `matriculas`
  tiene filas viejas sin año; al final, si queda en `cursos` o
  `tipos_de_pagos` una regla de unicidad sin año (por si un tenant viejo la
  tiene con otro nombre y el `DROP ... IF EXISTS` no la encuentra). En los
  dos casos el runner revierte ese tenant entero.
- Antes de escribirla se verificó en el código que nada depende de lo que
  cambia: ningún código usa por nombre los dos índices reemplazados; los
  `ON CONFLICT` son de otras tablas; el único `SELECT *` sobre una tabla
  tocada (`tipos_de_pagos`) arma su JSON solo con columnas conocidas.
- `tests/test_migracion_anios_lectivos.py`, 17 pruebas sobre el texto del
  SQL, una por decisión: año 2026 literal, las cinco tablas exactas, ninguna
  tabla académica tocada, `estudiantes.curso_id` intacto, columnas que
  admiten nulos, nada borrado, solo las dos reglas reemplazadas, la expresión
  original de cursos conservada, matrículas con clave compuesta, frenos y
  reejecución. Más una que confirma que la respuesta de tipos de pago no
  expone la columna nueva. Se comprobó que no son pruebas vacías:
  mutaciones del SQL (poner `NOT NULL`, calcular el año con la fecha, tocar
  `notas_detalle`) las hacen fallar.
- Límite: el SQL **no se ha ejecutado nunca**. En el equipo no hay
  PostgreSQL, y el `.env` apunta a una base remota. Su validez se comprueba
  en la rama de Neon (lista de abajo).
- Verificación: `scripts/verify.py` → **1467 pasan, 1 falla esperada**
  (`test_esquema_base.py`, hasta aplicar y regenerar la base, igual que en
  listas de seguimiento). Ruff y `pip check` limpios. Registrada en
  `docs/MIGRACIONES.md`.
- Encontrado de paso, para la fase 3: las validaciones de nombre repetido
  del código, `_validar_curso_unico` (`curso_controller.py:25`) y la de
  `crear_tipo_pago` (`tipos_pagos_controller.py:24`), buscan por nombre en
  todo el colegio, sin año. Con un solo año da igual. Hay que limitarlas al
  año antes de la fase 5, porque si no la copia de cursos y conceptos a 2027
  fallaría como "repetido".

**Lista de comprobación en una rama de Neon** (la hace el usuario; el
asistente no se conecta a Neon):

1. En console.neon.tech → Branches → **Create branch** desde la rama
   principal, con los datos actuales. Nombre sugerido: `prueba-anio-lectivo`.
2. En la rama nueva → **Connect**: copiar la cadena de conexión **directa**
   (con "Connection pooling" apagado; el host no debe tener `-pooler`).
   Comprobar que el host (`ep-...`) es distinto al de producción.
3. En una terminal de PowerShell, en la carpeta del backend. La variable
   solo vive en esa ventana y gana sobre el `.env`, porque `load_dotenv` no
   la pisa:

   ```powershell
   $env:DATABASE_URL = "<cadena directa de la rama>"
   .\venv\Scripts\python.exe apply_migration.py migrations/20260930_anios_lectivos.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/20260930_anios_lectivos.sql
   ```

   El `--dry-run` debe listar `tenant_colegio_1` y `tenant_2005` como
   pendientes. Al terminar, cerrar esa terminal.
4. En el SQL Editor de Neon, **con la rama de prueba elegida arriba**,
   correr esta consulta (y otra vez cambiando `tenant_2005` por
   `tenant_colegio_1`):

   ```sql
   SELECT 'años lectivos' AS dato, string_agg(anio || ' ' || estado, ', ') AS valor FROM tenant_2005.anios_lectivos
   UNION ALL SELECT 'cursos sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.cursos
   UNION ALL SELECT 'conceptos sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.tipos_de_pagos
   UNION ALL SELECT 'pagos sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.pagos
   UNION ALL SELECT 'observador sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.observador_anotaciones
   UNION ALL SELECT 'matrículas / estudiantes con curso', (SELECT COUNT(*) FROM tenant_2005.matriculas) || ' / ' || (SELECT COUNT(curso_id) FROM tenant_2005.estudiantes)
   UNION ALL SELECT 'control curso vigente (debe ser 0)', COUNT(*)::text FROM tenant_2005.estudiantes e LEFT JOIN tenant_2005.matriculas m ON m.estudiante_id = e.id AND m.anio_lectivo_id = (SELECT id FROM tenant_2005.anios_lectivos WHERE estado = 'activo') WHERE e.curso_id IS DISTINCT FROM m.curso_id
   UNION ALL SELECT 'reglas únicas en cursos', string_agg(indexname, ', ') FROM pg_indexes WHERE schemaname = 'tenant_2005' AND tablename = 'cursos' AND indexdef LIKE 'CREATE UNIQUE%'
   UNION ALL SELECT 'reglas únicas en conceptos', string_agg(indexname, ', ') FROM pg_indexes WHERE schemaname = 'tenant_2005' AND tablename = 'tipos_de_pagos' AND indexdef LIKE 'CREATE UNIQUE%'
   UNION ALL SELECT 'migración registrada en', string_agg(target_schema, ', ') FROM public.schema_migrations WHERE migration_name = '20260930_anios_lectivos.sql';
   ```

   Esperado en `tenant_2005`: `2026 activo`; `0 / 12` cursos, `0 / 2`
   conceptos, `0 / 546` pagos y `0 / <total>` observador; `174 / 174`
   matrículas; control `0`; en cursos `cursos_pkey`,
   `cursos_id_anio_lectivo_key` e `idx_cursos_anio_nombre_jornada_unico`
   (y **no** `idx_cursos_nombre_jornada_unico`); en conceptos
   `tipos_de_pagos_pkey` y `tipos_de_pagos_anio_nombre_key` (y **no**
   `tipos_de_pagos_nombre_key`); migración registrada en los dos tenants.
5. Recomendado: levantar el backend y el frontend **en local** apuntando a
   la rama (`$env:DATABASE_URL` igual que arriba, en la terminal del
   backend) y comprobar que Cursos, Tipos de pago, Pagos, Estudiantes y un
   boletín se ven igual que en producción, y que crear un curso de prueba
   funciona. Eso ensaya justo el estado intermedio de producción: migración
   A aplicada con el código de hoy.
6. Pegar el resultado del punto 4 en este documento. La rama se puede
   conservar para probar el código del punto 2, o borrarla.

**Prueba en la rama de Neon, 2026-09-30** (rama `prueba-anio-lectivo`, copia
de `production` con datos, borrado automático a 1 día; la corrió el
usuario):

- `--dry-run`: `tenant_colegio_1` y `tenant_2005` PENDIENTE. Aplicación: OK
  en los dos. Ningún freno saltó: `matriculas` estaba vacía en los dos y no
  quedó ninguna regla de unicidad sin año. Con esto el SQL quedó ejecutado y
  válido por primera vez.
- Consulta de comprobación en `tenant_2005`, todo igual a lo esperado:

  | Dato | Valor |
  |---|---|
  | Años lectivos | 2026 activo |
  | Cursos sin año / total | 0 / 12 |
  | Conceptos sin año / total | 0 / 2 |
  | Pagos sin año / total | 0 / 546 |
  | Observador sin año / total | 0 / 209 |
  | Matrículas / estudiantes con curso | 174 / 174 |
  | Control del curso vigente | 0 |
  | Reglas únicas en cursos | `idx_cursos_anio_nombre_jornada_unico`, `cursos_id_anio_lectivo_key`, `cursos_pkey` |
  | Reglas únicas en conceptos | `tipos_de_pagos_anio_nombre_key`, `tipos_de_pagos_pkey` |
  | Migración registrada en | `tenant_colegio_1`, `tenant_2005` |

- En `production`, la migración **no** quedó registrada (`COUNT(*)` = 0):
  la prueba solo tocó la rama.
- El punto 5 (la app en local contra la rama) **no se hizo, por decisión del
  usuario** (2026-09-30). Lo que lo cubre en parte: la revisión del código
  antes de escribir la migración (nada lee las columnas nuevas, el único
  `SELECT *` no las expone) y la prueba
  `test_la_respuesta_de_tipos_de_pago_no_expone_la_columna_nueva`. Lo que
  queda sin comprobar a ojo es que las pantallas se vean igual; si algo se
  viera distinto tras aplicar en producción, es la primera pista.

**Aplicada en producción el 2026-09-30** (la aplicó el usuario):

- `--dry-run`: PENDIENTE en los dos tenants (eso confirmó que la terminal
  apuntaba a producción y no a la rama, donde habría dicho "OMITIDA").
  Aplicación: OK en `tenant_colegio_1` y `tenant_2005`.
- Esquema base regenerado desde `tenant_colegio_1`: 34 tablas. Revisado el
  diff: coincide exactamente con la migración (tabla nueva, columna en las
  cinco tablas, reglas e índices nuevos, claves foráneas) y solo
  desaparecen las dos reglas viejas.
- `scripts/verify.py`: **1468 pasan, 0 fallan**. Se apagó la falla esperada
  de `test_esquema_base.py`. Ruff y `pip check` limpios.
- **Confirmado después** (2026-09-30, por el usuario en el SQL Editor de
  Neon con `production` elegido): `schema_migrations` registra la migración
  en los **2** tenants. Además, el servidor de la rama `production` es el
  mismo al que apunta el `.env` del backend. Ojo: eso quiere decir que el
  backend local escribe en la base real; las pruebas que crean datos se
  hacen en una rama.
- Desde aquí la migración A **no se puede editar** (el runner guarda su
  checksum). Se abre la ventana descrita en el punto 3: hasta desplegar el
  código del punto 2, lo nuevo queda sin año y las matrículas pueden
  desincronizarse. Conviene cerrarla pronto.

**Avance del 2026-09-30 — punto 2, código que escribe el año (sin
desplegar):**

- Diseño final, más simple que el planeado: en vez de un servicio que
  primero lee el año activo y luego lo escribe, cada `INSERT` lleva la
  subconsulta `(SELECT id FROM anios_lectivos WHERE estado = 'activo')`
  como valor de `anio_lectivo_id`. Ni una consulta ni un parámetro más:
  ninguna escritura hace un viaje extra a la base. Vive en una sola
  constante, `ANIO_ACTIVO_ID_SQL`, de
  `app/repositories/anios_lectivos_repository.py` (archivo nuevo), para no
  repetir la regla en cuatro sitios.
- Escrituras cambiadas: crear curso (`curso_controller.py`), crear concepto
  de pago (`tipos_pagos_controller.py`), los dos `INSERT` de pagos
  (`pagos_repository.py`, con nota en su docstring: la regla de "SQL
  intacto" era para la refactorización y esto es un cambio de
  comportamiento autorizado) y crear anotación del observador
  (`observador_repository.py`).
- Estudiantes: después de crear o editar (si existía),
  `sincronizar_matricula_del_anio_activo` crea o corrige la matrícula del
  año activo **en la misma transacción**. Es un solo `INSERT ... ON
  CONFLICT DO UPDATE`. Nunca borra: el curso es obligatorio en el
  formulario (`curso_id: int`). La dirección es estudiante → matrícula
  mientras haya un solo año (ver "La regla del curso vigente").
- Alta de colegios: `crear_anio_activo_inicial` siembra el año en curso como
  `activo`, justo después del branding inicial. El año sale de la hora de
  Bogotá, no de la del servidor (UTC).
- No se tocó: las validaciones de nombre repetido (van en la fase 3), el
  SQL del `INSERT`/`UPDATE` de `estudiantes` (la sincronización es una
  llamada aparte) ni ninguna lectura.
- Pruebas: archivo nuevo `tests/test_anio_lectivo_escrituras.py` (10). Se
  ajustaron a propósito 9 pruebas que fijan comportamiento: cinco listas
  exactas de repositorios (reconocen el archivo nuevo, como piden sus
  propios comentarios), los dos `INSERT` de pagos (ahora además comprueban
  la subconsulta y que los parámetros no cambiaron) y dos del alta de
  colegios (de 13 a 14 operaciones, con el año en la octava, y el número de
  líneas del controlador, de 330 a 337).
- Verificación: `scripts/verify.py` → **1478 pasan, 0 fallan**; ruff y
  `pip check` limpios; `git diff --check` limpio.
- Límite de las pruebas automáticas: usan dobles de cursor. Por eso se
  probó además contra una base real (siguiente punto).
- **Probado en la rama de Neon el 2026-09-30** (la probó el usuario): con
  el backend local apuntando a `prueba-anio-lectivo` (se comprobó que el
  servidor no era el del `.env`) y el frontend local, crear y guardar
  funcionó sin errores. Según el usuario, "está bien". No se pegó el
  resultado de la consulta de años y matrículas; si quedara alguna
  matrícula desincronizada, la migración B la corrige igual.

### Fase 2 — Cobros por año (dinero; antes del 1 de noviembre)

Zona sensible: pagos y reportes financieros. Se cambia solo lo necesario y
con las pruebas de la fase 0 como red.

1. `listar_cuotas_vencidas` y `calcular_cuotas_vencidas` (`cartera.py`)
   reciben un `anio` opcional. Si no llega, `hoy.year`, o sea exactamente
   como hoy.
2. Fecha de referencia por estado del año: activo → hoy; cerrado → 31 de
   diciembre de ese año (todas sus cuotas cuentan); en preparación → hoy
   (ninguna mensualidad vencida todavía; la matrícula sí se debe completa).
3. `pagado` solo suma pagos con `anio_lectivo_id` del año calculado; las
   aplicaciones, solo las de meses de ese año.
4. Conceptos del año (decisión 17): `obtener_tipos_pago` (`cobros.py`)
   devuelve solo los conceptos del año calculado, con su configuración de
   ese año (activo, meses, día límite, mora). Al registrar una aplicación se
   valida que su concepto sea del año del pago.
5. El precio sale del curso de la **matrícula de ese año**, no de
   `estudiantes.curso_id`. Así 2027 cobra con los precios de los cursos de
   2027.
6. Concepto **único** (decisión 7): se calcula por año como el anual, con el
   curso de ese año. Lo que quede sin pagar pasa a "deuda de años
   anteriores" y sigue ahí hasta que se pague. Si el admin lo reactiva en
   otro año, se cobra de nuevo en ese año. Límite conocido, igual que hoy:
   reactivarlo dentro del **mismo** año no genera un cobro nuevo.
7. **Deuda de años anteriores** (decisión 2): la respuesta de deudas del
   estudiante y la de cartera ganan un campo **nuevo** con la deuda de cada
   año anterior en que el estudiante tuvo matrícula, calculada con la misma
   función. Es un campo agregado: el frontend actual lo ignora sin romperse.
8. Registrar pago: el cuerpo acepta `anio_lectivo_id` opcional; si no llega,
   el año activo. Se valida que el año exista; el admin puede usar un año
   cerrado (decisión 6). `_periodos_programados` ofrece los meses del año
   del pago, lo que habilita adelantos de 2027 en diciembre.
9. Terminado cuando: las caracterizaciones de la fase 0 siguen iguales; los
   casos A y B dan el resultado correcto (A: debe matrícula 2027 + febrero y
   marzo; B: $400.000 de 2026 visibles como deuda anterior); hay pruebas de
   pago a año cerrado, pago a año en preparación y precio del curso de
   2027; `verify.py` pasa.

### Fase 3 — Lecturas por año y guardia de escritura

Tiene que estar en producción **antes de crear el primer curso de 2027**.
Si no, los listados mostrarían los cursos de los dos años mezclados y los
profesores verían las clases de 2027.

1. `GET` de años lectivos (lista con estado y cuál es el activo). Endpoint
   nuevo, propuesto como `/anios-lectivos`. Admin ve todos; profesor solo el
   activo.
2. Filtro por año, con el año activo por defecto, en todo listado que hoy
   recorre cursos, estudiantes o asignaciones sin partir de un id. Inventario
   del 2026-09-29 (volver a confirmar con `grep` al empezar):
   - `FROM cursos` sin `WHERE id =`: `curso_controller.py` (listado y
     conteo), `listas_seguimiento_repository.py:211` y `:226` (contar y
     crear una columna "en todos los cursos activos": debe limitarse a los
     cursos del año que se está mirando), `reportes_repository.py:6` y
     `:28`. (Corregido el 2026-09-30: `asignaciones_repository.py:181` y
     `:238` filtran por id y no van aquí.)
   - Asignaciones por profesor (mis clases, horarios, dashboard del
     profesor): `asignaciones_repository.py`, `dashboard_repository.py`,
     `profesor_controller.py`, `app/routes/asignaciones.py`. Se limitan al
     año activo con un `JOIN cursos` por año.
   - Estudiantes del admin: `estudiantes_repository.py` (listado y conteo)
     pasa a leer por `matriculas` del año pedido. Con el año activo debe
     devolver exactamente lo mismo que hoy, incluidos los estudiantes sin
     curso (lo exige la caracterización).
   - Boletín, certificados y puesto en el curso (`boletin_repository.py`):
     el curso sale de la matrícula del año pedido, no de `e.curso_id`. Esto
     arregla el punto 3 del diagnóstico. El filtro de materias inactivas
     (`boletin_repository.py:198` y `:352`) queda igual para el año activo y
     el de preparación. Para un año cerrado o reabierto oculta las materias
     de `anios_lectivos_materias_ocultas` de ese año (decisión 13). Mientras
     no exista ningún año cerrado, el resultado es idéntico al de hoy.
   - Conceptos de pago (decisión 17): `listar_tipos_pagos` y
     `listar_tipos_pagos_detallado` (`tipos_pagos_controller.py`) y los cursos
     ofrecidos para asignar precios, filtrados por año.
   - Validaciones de nombre repetido limitadas al año:
     `_validar_curso_unico` (`curso_controller.py:25`) y la de
     `crear_tipo_pago` (`tipos_pagos_controller.py:24`). Sin esto, la copia
     de la fase 5 fallaría como "repetido". La base de datos ya lo permite
     desde la migración A.
   - Observador: anotaciones filtradas por `anio_lectivo_id`.
3. **Aviso al renombrar una materia** (decisión 12). En
   `actualizar_materia_controller` (`materia_controller.py:151`): si cambia
   el nombre y la materia tiene asignaciones en más de un año, o en un año
   cerrado o reabierto, y la petición no trae una confirmación explícita,
   responde 409 con un código propio y el mensaje `Esta materia se usa en
   2026. Si cambias el nombre, también cambiará en los boletines y
   certificados de 2026.` Con la confirmación, guarda como hoy. Mientras
   haya un solo año, nunca avisa: se comporta exactamente como hoy.
4. Guardia `exigir_anio_editable` en toda ruta que escribe datos
   académicos: notas, planilla, boletín, asistencia, observador y
   observaciones, planeador anual, plan de clases, listas de seguimiento,
   asignaciones, cursos, conceptos de pago, precios por curso. El inventario exacto de rutas se
   hace al empezar la fase y se pega aquí. Una prueba por módulo: escribir
   en un año cerrado → 409.
5. Terminado cuando: con el año activo, todas las respuestas son idénticas a
   las de la fase 0; con otro año, devuelven solo lo de ese año; `verify.py`
   pasa.

### Fase 4 — Selector de año en el frontend

Ver `frontend-react/docs/funcionalidades/ANIO_LECTIVO.md`. En el backend no
hay trabajo nuevo: usa lo de la fase 3. Va antes de la fase 5 porque,
mientras se prepara 2027, el admin necesita las pantallas existentes
(Cursos, Tipos de pago, Estudiantes, Horarios) mirando 2027.

### Fase 5 — Preparar el año siguiente (meta: principios de noviembre)

Endpoints nuevos, todos solo para admin (`get_current_active_admin`),
propuestos bajo `/anios-lectivos`:

1. **Crear año** `N+1` en `preparacion`. Solo si no hay otro en preparación.
2. **Copiar cursos** del año activo: nombre, jornada, nivel y, a elección,
   precios (`tipos_pagos_cursos`), carga académica (asignaciones con sus
   horarios y orden de boletín) y director de grupo. Transaccional: o se
   copia todo o nada. Si un curso ya existe en el destino, el índice único
   lo impide y se informa cuál. Cada curso copiado guarda de qué curso vino
   en una columna nueva, `cursos.curso_origen_id` (clave foránea a `cursos`,
   admite nulos: un curso creado desde cero no tiene origen). La fase 7 la
   necesita para saber de dónde traer el planeador y los planes.
   **Los conceptos de pago se copian siempre** (decisión 17), con toda su
   configuración (tipo, activo, meses, día límite, gracia, mora, valor
   base), y cada copia guarda su origen en `tipos_de_pagos.tipo_pago_origen_id`.
   Los precios por curso copiados apuntan al concepto **y** al curso de
   2027. Después, el admin ajusta 2027 en la pantalla de Tipos de pago (por
   ejemplo, mensualidad desde febrero y matrícula activa) sin tocar 2026.
3. **Matricular**:
   - Promoción por curso: el admin elige "Primero A 2026 → Segundo A 2027",
     ve la lista y desmarca a quien no pasa con ese grupo.
   - Estudiantes nuevos: se crean con un curso del año en preparación; solo
     reciben matrícula, con `curso_id = NULL` hasta activar (ver regla del
     curso vigente).
4. **Valores especiales en espera** (decisión 8): al crear la matrícula de
   2027 de un estudiante, sus filas de `tipos_pagos_estudiantes` de los
   conceptos de 2026 se copian a las copias de esos conceptos en 2027
   (usando `tipo_pago_origen_id`). La respuesta las devuelve marcadas
   "copiados, revisar". Si no se matricula, no se copia nada. No hace falta
   columna nueva en `tipos_pagos_estudiantes`: el año viene del concepto.
5. **Pagos al año en preparación**: ya habilitados por la fase 2; aquí se
   prueba el flujo completo de una matrícula 2027 pagada en noviembre de
   2026.
6. Terminado cuando: en una rama de Neon con copia de producción se puede
   preparar 2027 completo sin que ninguna pantalla del año activo cambie.

### Fase 6 — Activar el año nuevo, cerrar y reabrir (antes de iniciar clases 2027)

1. Migración: marca "no continúa" en `matriculas` (decisión 9) y tabla
   `anios_lectivos_materias_ocultas` (decisión 13).
2. **Vista previa de activación**: cuántos estudiantes pasan, cuántos
   quedan retirados por "no continúa" y **cuántos están sin decidir**. Si
   hay alguno sin decidir, la activación se rechaza con la lista.
3. **Activar**, en una sola transacción: el año activo pasa a `cerrado`,
   el de preparación a `activo`; `sincronizar_curso_vigente` para todos; los
   marcados "no continúa" pasan a retirados; se guardan las materias
   inactivas en ese momento como ocultas del año que se cierra. Se guarda
   `activado_en` y `cerrado_en`.
4. **Reabrir / volver a cerrar** un año pasado (`cerrado` ↔ `reabierto`),
   solo admin, para correcciones puntuales.
5. Terminado cuando: el ensayo completo de activación en una rama de Neon
   con copia de producción deja la consulta de control en 0 filas, los
   profesores ven solo 2027 y el admin puede consultar e imprimir 2026.

### Fase 7 — Reutilizar el planeador anual y los planes de clase (antes de iniciar clases 2027)

Decisiones 14, 15 y 16. Solo tiene sentido después de activar 2027, que es
cuando los profesores empiezan a ver sus clases nuevas.

1. **Cómo se encuentra el origen**, siempre en el servidor: asignación de
   2027 del profesor → su curso → `cursos.curso_origen_id` → la asignación
   académica de la **misma materia** en ese curso de origen (la que resuelve
   `resolver_asignacion_academica_id_cursor`). No importa qué profesor la
   dictaba (decisión 15). Si el curso no tiene origen o la materia no se
   dictaba allí, no hay origen y el botón no aparece.
2. **Planeador anual**: endpoint para consultar si hay origen y si el
   planeador de destino está vacío, y endpoint para traerlo. Copia de
   `planeador_anual` los campos `periodo`, `slot`, `unidad_tematica`,
   `estandar_competencia`, `contenido` y `actividades_recursos`. **No copia
   `fecha`**: las de 2026 no sirven en 2027. Si el destino ya tiene
   cualquier fila, responde 409 y no copia nada (nunca sobrescribe).
3. **Planes de clase**: endpoint que lista los planes del origen (fecha,
   periodo, unidad, tema) y endpoint que devuelve el texto de uno. El
   profesor solo manda su asignación de 2027 y el id del plan elegido; el
   backend comprueba que el plan pertenezca al origen de esa asignación. No
   se crea nada: el frontend llena el formulario y el profesor guarda por
   la ruta normal de crear plan, con fecha nueva, estado `pendiente` y sin
   evidencias.
4. Permisos: profesor dueño de la asignación de 2027 (con
   `require_asignacion_access`) o admin; el año de destino debe ser
   editable (`exigir_anio_editable`).
5. Terminado cuando: hay pruebas de origen encontrado y no encontrado,
   profesor distinto al de 2026, planeador de destino no vacío (409), plan
   que no pertenece al origen (403), y de que la fecha y las evidencias no
   se copian; `verify.py` pasa.

## Pruebas

- Unitarias puras para `app/services/anio_lectivo.py` y para la nueva
  aritmética de cuotas por año en `cartera.py`.
- Caracterización antes de cada cambio de comportamiento (fase 0), con el
  estilo `test_<modulo>_caracterizacion.py` del repo.
- Migraciones: prueba de que el esquema base declara las migraciones nuevas
  (ya la hace `tests/test_esquema_base.py`) y de que el relleno es
  idempotente, es decir, que correrlo dos veces no duplica ni cambia nada.
- Nunca reportar una prueba como pasada si no se corrió.

## Fuera de alcance

- Calendario B (año lectivo que cruza dos años calendario). Obligaría a
  rediseñar la fase 2: hoy los meses de cobro son 1 a 12 del mismo año.
- Fechas de inicio y fin de cada periodo académico por año.
- Promoción automática según notas: el admin decide.
- Varios años visibles para profesores. La fase 7 no lo contradice: el
  profesor recibe contenido de 2026, pero no navega por 2026.
- Borrar columnas legado (`estudiantes.anio_escolar`, `matriculas.anio`):
  solo con permiso explícito.
- Nómina, egresos, préstamos, inventario y ventas: siguen por fecha.

## Hallazgos fuera de alcance (para decidir aparte)

- **Desactivar un concepto borra de la vista la deuda de quien no pagó.**
  `_calcular_deudas` (`cobros.py:409`) salta los conceptos con `activo =
  FALSE`. Esto choca con la decisión 7 ("si el estudiante debe, la deuda le
  queda hasta que la pague"): hoy, al desactivar una actividad "única"
  después de cobrarla, los que no pagaron dejan de aparecer como deudores.
  No lo causa ni lo arregla el año lectivo; conviene decidir si se corrige
  como cambio aparte, antes o después de la fase 2.
- **Reusar un concepto "único" dentro del mismo año** no genera un cobro
  nuevo: el sistema no distingue una activación de otra. Si hace falta,
  requiere su propio diseño (por ejemplo, "ocurrencias" de un cobro).
- **La deuda se calcula con la fecha del servidor (UTC), no con la de
  Colombia.** Lo vio el usuario el 2026-09-30 a las 22:50 de Bogotá: el
  backend local mostraba una deuda y producción otra, con la cuota de
  octubre ya vencida. En Render ya era 2026-10-01 03:50 UTC. `cartera.py`
  (líneas 54 y 103) y `cobros.py` (220 y 317) usan `date.today()`, que es
  la fecha del servidor, mientras `pagos_controller.py` usa la hora de
  Bogotá. Simulado con las funciones reales y la mensualidad de
  `tenant_2005` (julio a noviembre), suponiendo vencimiento el día 1: el
  30-sep da 3 cuotas ($600.000) y el 1-oct da 4 ($800.000). Efecto: **cada
  noche desde las 7 p. m. de Bogotá**, producción calcula deudas, cartera y
  mora como si ya fuera mañana. En el cambio de mes, la cuota siguiente
  aparece vencida unas 5 horas antes. Para el año lectivo importa más: el
  31 de diciembre desde las 7 p. m., producción calcularía como si fuera
  2027. La misma familia de errores, con menos impacto: la fecha por
  defecto de egresos y préstamos (`egreso_controller.py:54`,
  `prestamo_controller.py:46`, `routes/egresos.py:28`), el estado SaaS del
  colegio (`core/tenant_status.py:63`) y los `CURRENT_DATE` y
  `CURRENT_TIMESTAMP` de la base, que en Neon corren en UTC. **Corregido el
  2026-09-30, con el visto bueno del usuario, en cobros, cartera y alta de
  colegios** (`app/core/fechas.py: hoy_en_colombia`, con
  `tests/test_fechas_colombia.py`) y, en el frontend, en el plan de clases,
  préstamos, alta de colegio y nombre del CSV de cartera
  (`frontend-react/src/utils/fechaColombia.js`). Siguen pendientes, de
  menor impacto: la fecha por defecto de egresos y préstamos **en el
  backend**, `core/tenant_status.py` y los `CURRENT_DATE` de la base.
  Revisado también para profesores (2026-09-30): asistencia y planilla usan
  la fecha que elige el profesor; el inicio del profesor ya calcula en
  Bogotá (`dashboard_repository.py:34`); las horas de envío, revisión y
  observador son `timestamptz` y el navegador las muestra en hora local. Sí
  falla, en el frontend, **la fecha por defecto de un plan de clases nuevo**
  (`frontend-react/src/pages/PlanDeClases.jsx:74`, `new
  Date().toISOString()`): después de las 7 p. m. propone la fecha de mañana.
  Mismo patrón en admin: `utils/nominaEgresosPrestamos/prestamos.js:22`
  (fecha por defecto de un préstamo), `utils/dashboards/superAdmin.js:40` y
  el nombre del CSV de `CarteraVencidaAdmin.jsx:50`. Pagos, egresos y
  reportes ya calculan la fecha local bien (`utils/pagos/formatos.js`).
- **La fecha de un pago no se valida.** `PagoCreate.fecha`
  (`app/schemas/pago.py:22`) acepta cualquier fecha, y en `tenant_2005` hay
  un pago con fecha del año 8 (fase 0). Ese pago no aparece en los reportes
  que filtran por fecha. **El usuario decidió dejarlo así (2026-09-30).**
  Validar un rango razonable de fecha al registrar pagos sería un cambio
  aparte, pequeño, si se quiere evitar que se repita.

## Preguntas abiertas

- Ninguna bloquea la fase 0.
- ~~Antes de la fase 1: ¿ya se registró algún estudiante o pago para
  2027?~~ **Respondida el 2026-09-30: no.** Ver la regla operativa del
  Control.
- Antes de la fase 2: ¿se corrige primero el hallazgo de conceptos
  desactivados que ocultan deuda? Explicado al usuario el 2026-09-30, sin
  decidir todavía. **Trampa a tener en cuenta:** en `tenant_2005` la
  MATRICULA está inactiva y nadie la tiene pagada en el sistema (se cobró
  por fuera antes de julio). Si desactivar dejara de borrar la deuda, los
  174 estudiantes aparecerían debiendo la matrícula de 2026. Idea
  planteada: "desactivar" deja de cobrar desde ese día, lo ya vencido se
  conserva, y una acción aparte y explícita de "anular deuda" sirve para
  casos como esa matrícula.
- Antes de la fase 4 (frontend): en las pantallas que no dependen del año,
  ¿el selector se esconde o se muestra desactivado?
- Antes de la fase 6: ¿un estudiante del último grado que termina se marca
  "no continúa" (retirado) o hace falta un estado distinto como "egresado"?

## Entrega para el siguiente chat

Estado al 2026-09-30, al cerrar el chat de origen. Si `git status` o el
historial de git dicen otra cosa, gana lo que se pueda verificar.

- **Hecho:** fase 0 completa; fase 1, puntos 1 y 2 (migración A aplicada en
  producción en `tenant_colegio_1` y `tenant_2005`, esquema base
  regenerado, y el código que escribe el año en todo lo nuevo, commit
  `df53299`). Detalle y verificación de cada paso en los "Avance" de las
  fases 0 y 1.
- **Hecho aparte, misma noche:** el arreglo de la hora. Cobros, cartera y
  alta de colegios usan la fecha de Colombia (`app/core/fechas.py`), y el
  frontend propone fechas de Colombia (`src/utils/fechaColombia.js`). Ver
  el hallazgo correspondiente y `docs/CAMBIOS_BACKEND.md`. Quedó listo para
  commit en los dos repos.
- **Pendiente del usuario:** commit del arreglo de la hora y **push** de los
  dos repos. En el backend, el push despliega a producción los commits
  acumulados (fase 0, migración A, código del año, hora). Es seguro, porque
  la migración A ya está en producción. Además, **rotar la contraseña** de
  `neondb_owner` (ver el punto siguiente).
- Contraseña: la cadena de conexión de una rama, con su contraseña
  heredada de producción, quedó pegada en el chat de origen. La rama ya se
  borró, pero la contraseña de producción sigue siendo la misma: rotarla en
  Neon (Roles → Reset password) y enseguida actualizar `DATABASE_URL` en
  Render y en el `.env` local, a una hora tranquila.
- Ojo operativo: el `.env` del backend local apunta a la rama `production`
  de Neon. El backend local escribe en la base real. Las pruebas que crean
  datos, y las migraciones, se hacen en una rama de Neon, con
  `$env:DATABASE_URL` en esa terminal (gana sobre el `.env`). Para ver a
  dónde apunta sin mostrar la contraseña: `([uri]$env:DATABASE_URL).Host`.
  No pedirle al usuario que pegue cadenas de conexión.
- **Siguiente acción exacta:** cuando el push del backend esté funcionando
  en producción, **fase 1, punto 3: la migración B** (ver su descripción en
  la fase 1: rellenar lo que quedó sin año, insertar el año activo si falta,
  re-sincronizar matrículas y poner `NOT NULL`). Se escribe, se prueba en
  una rama de Neon nueva y se aplica **solo después** del despliegue.
  Luego, regenerar el esquema base.
- Después: fase 2 (antes del 1 de noviembre), con la pregunta abierta de
  conceptos desactivados resuelta antes de empezar.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_ANIO_LECTIVO.md`.
