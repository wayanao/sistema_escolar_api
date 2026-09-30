# Funcionalidad: Año lectivo — Backend

## Control

- Estado: **Diseñado, nada implementado.** Ninguna fase iniciada.
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
13. **Desactivar una materia no borra la historia.** En un año que no es el
    activo, el boletín muestra las materias que se dictaron ese año aunque
    hoy estén inactivas. La regla de ocultar inactivas queda solo para el año
    activo. Propuesto por el asistente y sin objeción del usuario; la fase 0
    comprueba que en 2026 nadie desactivó una materia justamente para sacarla
    del boletín.
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
 ├── matriculas (estudiante, curso, año)     ← en qué curso estuvo cada estudiante cada año
 ├── pagos.anio_lectivo_id                   ← a qué año pertenece cada pago
 ├── observador_anotaciones.anio_lectivo_id  ← no cuelga de un curso
 └── tipos_pagos_estudiantes.anio_lectivo_id ← valores especiales por año (fase 5)
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
- `tipos_de_pagos`: es el concepto (nombre, tipo de cobro, meses). Su precio
  por año ya queda en `tipos_pagos_cursos`, porque cada año tiene sus
  cursos.
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

### `tipos_pagos_estudiantes.anio_lectivo_id` (fase 5, no fase 1)

Se agrega en la fase 5 junto con la copia "en espera" de la decisión 8. La
restricción única pasa de `(tipo_pago_id, estudiante_id)` a `(tipo_pago_id,
estudiante_id, anio_lectivo_id)`. Hasta entonces se comportan como hoy.

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

   Si la última consulta devuelve filas, se le pregunta al usuario si esas
   materias se desactivaron para sacarlas del boletín de 2026. Si es así, la
   decisión 13 necesita un ajuste antes de la fase 3.

   Además, se le pregunta al usuario si ya registró en el sistema algún
   estudiante o pago **para 2027**. Si hay alguno, se lista aquí para que la
   fase 1 lo asigne a 2027 y no a 2026.
2. **Pruebas de caracterización** (fijan cómo funciona hoy, antes de
   cambiar nada):
   - Cobros dentro del año activo: estado de cuenta, cuotas vencidas,
     adelantos disponibles y cartera, con `hoy` fijo en 2026. La fase 2 debe
     dejarlas iguales.
   - El cambio de año: los casos A y B del diagnóstico, escritos como
     pruebas que documentan el error actual. En la fase 2 se invierten para
     exigir el resultado correcto.
   - Listados que la fase 3 va a tocar: cursos, estudiantes, boletín,
     asignaciones del profesor. Deben devolver lo mismo después de la fase 3
     cuando se pide el año activo.
3. Terminado cuando: las pruebas nuevas pasan, `python scripts/verify.py`
   pasa y los números están pegados aquí.

### Fase 1 — Fundación de datos (invisible)

Nada cambia en pantalla ni en ninguna respuesta de la API.

1. **Migración A** `migrations/AAAAMMDD_anios_lectivos.sql`: crea
   `anios_lectivos`, inserta 2026 como `activo`, agrega las columnas de
   `cursos`, `matriculas`, `pagos` y `observador_anotaciones` **admitiendo
   nulos**, las rellena con 2026, llena `matriculas` y rehace el índice único
   de cursos. El año va escrito como `2026`, no calculado con la fecha del
   día: dice "todo lo existente es de 2026" aunque la migración se aplique
   tarde.
2. **Código que escribe el año** en toda fila nueva: crear curso
   (`curso_controller.py:71`), crear pago (`pagos_repository.py:23` y `:37`),
   crear anotación (`observador_repository.py:187`), crear y editar
   estudiante (matrícula del año activo + `sincronizar_curso_vigente`). Más
   el alta de colegios nuevos. Nuevo: `app/services/anio_lectivo.py` con
   `obtener_anio_activo` y `sincronizar_curso_vigente`, más sus pruebas.
3. **Migración B** `migrations/AAAAMMDD_anios_lectivos_obligatorio.sql`:
   vuelve a rellenar lo que se haya creado entre la migración A y el
   despliegue del código, y pone `NOT NULL` en las columnas nuevas.
4. Orden seguro, el de `docs/MIGRACIONES.md`: probar en rama de Neon →
   `apply_migration.py --dry-run` → aplicar A → regenerar el esquema base
   desde `tenant_colegio_1` → desplegar el código → aplicar B → regenerar el
   esquema base otra vez. Migración y esquema base se commitean juntos
   (`tests/test_esquema_base.py` lo exige).
5. Terminado cuando: la consulta de control del curso vigente da 0 filas en
   los dos tenants, todas las pruebas de la fase 0 siguen iguales,
   `verify.py` pasa y el usuario confirma en local que no cambió nada
   visible.

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
4. El precio sale del curso de la **matrícula de ese año**, no de
   `estudiantes.curso_id`. Así 2027 cobra con los precios de los cursos de
   2027.
5. Concepto **único** (decisión 7): se calcula por año como el anual, con el
   curso de ese año. Lo que quede sin pagar pasa a "deuda de años
   anteriores" y sigue ahí hasta que se pague. Si el admin lo reactiva en
   otro año, se cobra de nuevo en ese año. Límite conocido, igual que hoy:
   reactivarlo dentro del **mismo** año no genera un cobro nuevo.
6. **Deuda de años anteriores** (decisión 2): la respuesta de deudas del
   estudiante y la de cartera ganan un campo **nuevo** con la deuda de cada
   año anterior en que el estudiante tuvo matrícula, calculada con la misma
   función. Es un campo agregado: el frontend actual lo ignora sin romperse.
7. Registrar pago: el cuerpo acepta `anio_lectivo_id` opcional; si no llega,
   el año activo. Se valida que el año exista; el admin puede usar un año
   cerrado (decisión 6). `_periodos_programados` ofrece los meses del año
   del pago, lo que habilita adelantos de 2027 en diciembre.
8. Terminado cuando: las caracterizaciones de la fase 0 siguen iguales; los
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
     conteo), `asignaciones_repository.py:181` y `:238`,
     `listas_seguimiento_repository.py:211` y `:226`,
     `reportes_repository.py:6` y `:28`.
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
     arregla el punto 3 del diagnóstico. Además, el filtro de materias
     inactivas (`boletin_repository.py:198` y `:352`) se aplica solo cuando
     el año pedido es el activo (decisión 13).
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
   asignaciones, cursos, precios por curso. El inventario exacto de rutas se
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
3. **Matricular**:
   - Promoción por curso: el admin elige "Primero A 2026 → Segundo A 2027",
     ve la lista y desmarca a quien no pasa con ese grupo.
   - Estudiantes nuevos: se crean con un curso del año en preparación; solo
     reciben matrícula, con `curso_id = NULL` hasta activar (ver regla del
     curso vigente).
4. **Valores especiales en espera** (decisión 8): migración que agrega
   `anio_lectivo_id` a `tipos_pagos_estudiantes`, con los existentes en
   2026. Al crear la matrícula de 2027 de un estudiante, se copian sus
   valores de 2026 a 2027 y la respuesta los devuelve marcados "copiados,
   revisar". Si no se matricula, no se copia nada.
5. **Pagos al año en preparación**: ya habilitados por la fase 2; aquí se
   prueba el flujo completo de una matrícula 2027 pagada en noviembre de
   2026.
6. Terminado cuando: en una rama de Neon con copia de producción se puede
   preparar 2027 completo sin que ninguna pantalla del año activo cambie.

### Fase 6 — Activar el año nuevo, cerrar y reabrir (antes de iniciar clases 2027)

1. Migración: marca "no continúa" en `matriculas` (decisión 9).
2. **Vista previa de activación**: cuántos estudiantes pasan, cuántos
   quedan retirados por "no continúa" y **cuántos están sin decidir**. Si
   hay alguno sin decidir, la activación se rechaza con la lista.
3. **Activar**, en una sola transacción: el año activo pasa a `cerrado`,
   el de preparación a `activo`; `sincronizar_curso_vigente` para todos; los
   marcados "no continúa" pasan a retirados. Se guarda `activado_en` y
   `cerrado_en`.
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

## Preguntas abiertas

- Ninguna bloquea la fase 0.
- Antes de la fase 1: ¿ya se registró en el sistema algún estudiante o pago
  para 2027? (Se pregunta en la fase 0.) Si hay alguno, la fase 1 lo asigna
  a 2027 en vez de a 2026.
- Antes de la fase 2: ¿se corrige primero el hallazgo de conceptos
  desactivados que ocultan deuda?
- Antes de la fase 6: ¿un estudiante del último grado que termina se marca
  "no continúa" (retirado) o hace falta un estado distinto como "egresado"?

## Entrega para el siguiente chat

- Última acción terminada: **diseño y documentación**, 2026-09-29,
  ampliado el 2026-09-30 con las materias (decisiones 12 y 13) y la fase 7
  (decisiones 14 a 16). Ninguna fase iniciada; no hay código ni migraciones
  de esta funcionalidad.
- Siguiente acción exacta: **fase 0, punto 1**. El usuario corre las
  consultas de solo lectura en los dos tenants y pega los números aquí. En
  paralelo se pueden escribir las pruebas de caracterización (punto 2), que
  no necesitan producción.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_ANIO_LECTIVO.md`.
