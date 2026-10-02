# Funcionalidad: Año lectivo — Backend

## Control

- Estado: **Fase 3 en curso: inventario y plan del 2026-10-02; pasos 3.1,
  3.2 y 3.3 en los commits `fea2e83`, `43764f2` y `da4da87`; paso 3.4
  (estudiantes y cartera desde las matrículas) escrito y probado, sin
  commit.**
  **Fase 2 con el código completo el
  2026-10-01, sin desplegar.**
  Pasos 2.1 (las cuotas se cuentan en el año del concepto), 2.2 (cada año
  cuenta solo sus pagos), 2.3 (pagar en otro año) y 2.4 (deuda de años
  anteriores) en los commits `b2362f1`, `34712dd`, `b5f4099` y `f03b032`,
  sin subir a GitHub al 2026-10-02. Fase 1
  terminada el 2026-10-01: migración A (2026-09-30) y migración B
  (2026-10-01) aplicadas en producción, código que escribe el año
  desplegado en Render (`67b2d4b`, Live), esquema base regenerado. Fase 0
  terminada el 2026-09-30. Ningún cambio de comportamiento visible.
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
- Última actualización: 2026-10-02.

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

Agregadas el 2026-10-02 (paso 3.4, al leer cartera por año):

18. **Quien se retira debiendo se ve al mirar ese año.** En la Cartera de un
    año que no es el activo (por ejemplo, 2026 ya cerrado) salen todos los
    matriculados de ese año que deben, aunque después se hayan retirado. La
    Cartera del año activo queda como hoy: solo estudiantes activos. Así la
    deuda de un estudiante que no continúa no desaparece (decisión 2), sin
    meter retirados en la cartera del año.
19. **Las ventas de inventario solo en la Cartera del año activo.** No
    pertenecen a ningún año lectivo (van por fecha); mostrarlas al mirar otro
    año las repetiría.

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
   **Aplicada en producción el 2026-10-01**: ver el "Avance" del punto 3
   más abajo, con su lista de comprobación y los resultados.
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

**Avance del 2026-10-01 — punto 3, migración B escrita (sin aplicar):**

- Antes de escribirla se confirmó con `git fetch` que el código del punto 2
  ya está en `main` en GitHub (`df53299`, subido junto con `67b2d4b`). Que
  Render lo haya desplegado no se ve desde el repo: lo confirma el usuario
  antes de aplicar B en producción (punto 7 de la lista de abajo).
- `migrations/20261001_anios_lectivos_obligatorio.sql`, en este orden:
  1. Freno: si hay matrículas sin año, se detiene. Ningún camino del sistema
     las crea; si aparece una, no se adivina su año.
  2. Si el colegio no tiene año activo, inserta 2026 como activo (escrito,
     no calculado, como en A). Freno si aun así no queda ninguno activo.
  3. Rellena con el año activo lo que quedó sin año en `cursos`,
     `tipos_de_pagos`, `pagos` y `observador_anotaciones`. Usa la misma
     subconsulta que el código (`ANIO_ACTIVO_ID_SQL`): lo que el código
     nuevo habría escrito.
  4. Pone al día las matrículas del año activo con `estudiantes.curso_id`:
     la misma sentencia de `sincronizar_matricula_del_anio_activo`, para
     todos a la vez (retirados incluidos) y después de dar año a los cursos.
     Crea las que faltan y corrige las que no coinciden; no borra ninguna ni
     toca `estudiantes`.
  5. Freno final: la consulta de control del curso vigente debe dar 0.
  6. `SET NOT NULL` en `anio_lectivo_id` de las cinco tablas. Ninguna otra
     columna cambia, y no se crean tablas, índices ni reglas.
- Revisión previa del código, para que el `NOT NULL` no rompa nada: los
  seis `INSERT` de `app/` en esas tablas (curso, concepto, los dos de pagos,
  anotación y matrícula) ya escriben el año; `app/` nunca borra estudiantes,
  cursos, conceptos, pagos ni anotaciones (eliminar es cambiar de estado), y
  la app no aplica migraciones al arrancar.
- `tests/test_migracion_anios_lectivos_obligatorio.py`, 12 pruebas. Once
  leen el SQL, una por decisión: las cinco columnas y ninguna más, el mismo
  año que escribe el código, 2026 escrito, el orden de los pasos, la
  consulta de control como freno, nada borrado, ninguna estructura nueva y
  reejecución. La duodécima lee el código: **todo `INSERT` de `app/` en esas
  cinco tablas incluye `anio_lectivo_id`**. Es la que hace segura la
  migración: si mañana alguien agrega una inserción sin año, falla en CI y
  no en producción. Se comprobó que no son pruebas vacías: 16 versiones
  dañadas de la migración y del código las hacen fallar, y
  `pagos_aplicaciones` no se confunde con `pagos`.
- Verificación: `scripts/verify.py` → **1499 pasan, 1 falla esperada**
  (`test_esquema_base.py`, hasta aplicar B y regenerar la base, igual que
  con A). Ruff y `pip check` limpios. `git diff --check` limpio. Corrido con
  un `DATABASE_URL` inventado, como en CI, para que ninguna prueba pudiera
  tocar la base real.
- Límite: como con A, el SQL no se ha ejecutado nunca. Su validez se
  comprueba en una rama de Neon (lista de abajo).
- Bloqueo: `SET NOT NULL` bloquea cada tabla mientras revisa sus filas. Son
  tablas chicas (la mayor, `pagos`, con unas 550 filas en `tenant_2005`) y
  dura un momento, pero conviene aplicarla en producción a una hora en que
  nadie esté registrando pagos.

**Lista de comprobación de la migración B** (la hace el usuario; el
asistente no se conecta a Neon ni a producción). Las cadenas de conexión
llevan la contraseña: se escriben solo en la terminal, nunca en el chat.

En una rama de Neon:

1. En console.neon.tech → Branches → **Create branch** desde `production`,
   con los datos actuales. Nombre sugerido: `prueba-anio-lectivo-b`.
2. En la rama nueva → **Connect**: copiar la cadena de conexión **directa**
   (con "Connection pooling" apagado; el host no debe tener `-pooler`).
3. En el SQL Editor de Neon, **con la rama de prueba elegida**, correr la
   consulta de abajo. Es el "antes": cuenta lo que quedó sin año en la
   ventana. Para el colegio demo es opcional: la misma consulta cambiando
   `tenant_2005` por `tenant_colegio_1`.
4. En una terminal de PowerShell, en la carpeta del backend:

   ```powershell
   $env:DATABASE_URL = '<cadena directa de la rama>'
   ([uri]$env:DATABASE_URL).Host
   .\venv\Scripts\python.exe apply_migration.py migrations/20261001_anios_lectivos_obligatorio.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/20261001_anios_lectivos_obligatorio.sql
   ```

   Van comillas simples: con dobles, PowerShell alteraría un `$` de la
   contraseña. La segunda línea muestra el servidor sin la contraseña: debe
   ser el de la rama. El `--dry-run` debe listar `tenant_colegio_1` y `tenant_2005` como
   `PENDIENTE`, y la aplicación debe decir `OK` en los dos. Si un tenant
   dice `FALLO` con el mensaje de un freno, ese tenant quedó como estaba:
   copiar el mensaje aquí y no seguir.
5. La misma consulta del punto 3, otra vez en la rama. Es el "después".
6. Muy recomendado: probar la app local contra la rama. **Primero detener
   el backend local que ya esté corriendo** (Ctrl+C en su terminal): si
   sigue abierto, ocupa el puerto 8000, el nuevo no arranca y el frontend
   seguiría hablando con el viejo, que usa el `.env` y escribe en
   producción. Luego, en la terminal de la rama,
   `.\venv\Scripts\python.exe -m uvicorn app.main:app --reload`, y
   comprobar que dice `Uvicorn running on http://127.0.0.1:8000` sin
   errores. La variable de la terminal gana sobre el `.env`
   (`pydantic-settings` lee primero el entorno). En la app local: crear un
   curso, un concepto de pago y un pago, y crear y editar un estudiante; con
   un profesor de prueba, si lo hay, una anotación del observador (solo los
   profesores pueden crearlas). Todo debe funcionar sin errores. Es la
   única prueba real de que el código de hoy convive con la regla nueva. Al
   terminar, Ctrl+C y cerrar la terminal.

En producción, solo si todo lo anterior salió bien:

7. En Render, comprobar que el último despliegue del backend está **Live**
   con el commit `67b2d4b` o uno posterior. Si no, **no seguir**: con el
   código viejo, crear cursos, conceptos, pagos o anotaciones fallaría.
8. A una hora tranquila, en una terminal nueva, con la cadena **directa** de
   `production`: el mismo `--dry-run` (debe decir `PENDIENTE` en los dos
   tenants; si dijera `OMITIDA`, la terminal apunta a la rama) y luego la
   aplicación.
9. La consulta del punto 3 con `production` elegido en el SQL Editor.
10. En esa misma terminal, regenerar el esquema base:
    `.\venv\Scripts\python.exe scripts\generar_esquema_base.py --schema tenant_colegio_1`.
    En su diff solo deben cambiar las cinco columnas, que pasan a `NOT
    NULL`, y la lista de migraciones incorporadas, que suma la B. Luego
    `scripts/verify.py` debe dar **0 fallas**, y se hace un solo commit con
    migración, esquema base, pruebas y documentos.
11. Pegar aquí los resultados de los puntos 3, 5 y 9.

Consulta para los puntos 3, 5 y 9 (solo lectura):

```sql
SELECT 'años lectivos' AS dato, string_agg(anio || ' ' || estado, ', ') AS valor FROM tenant_2005.anios_lectivos
UNION ALL SELECT 'cursos sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.cursos
UNION ALL SELECT 'conceptos sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.tipos_de_pagos
UNION ALL SELECT 'pagos sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.pagos
UNION ALL SELECT 'observador sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.observador_anotaciones
UNION ALL SELECT 'matrículas sin año / total', COUNT(*) FILTER (WHERE anio_lectivo_id IS NULL) || ' / ' || COUNT(*) FROM tenant_2005.matriculas
UNION ALL SELECT 'estudiantes con curso', COUNT(curso_id)::text FROM tenant_2005.estudiantes
UNION ALL SELECT 'control curso vigente (debe ser 0)', COUNT(*)::text FROM tenant_2005.estudiantes e LEFT JOIN tenant_2005.matriculas m ON m.estudiante_id = e.id AND m.anio_lectivo_id = (SELECT id FROM tenant_2005.anios_lectivos WHERE estado = 'activo') WHERE e.curso_id IS DISTINCT FROM m.curso_id
UNION ALL SELECT 'columnas de año obligatorias', COUNT(*) FILTER (WHERE is_nullable = 'NO') || ' de 5' FROM information_schema.columns WHERE table_schema = 'tenant_2005' AND column_name = 'anio_lectivo_id' AND table_name IN ('cursos', 'tipos_de_pagos', 'matriculas', 'pagos', 'observador_anotaciones')
UNION ALL SELECT 'migración B registrada en', COALESCE(string_agg(target_schema, ', '), 'ninguno') FROM public.schema_migrations WHERE migration_name = '20261001_anios_lectivos_obligatorio.sql';
```

Esperado **después** de B, en cada tenant: `2026 activo`; `0 / <total>` en
cursos, conceptos, pagos, observador y matrículas; el total de matrículas
igual a "estudiantes con curso"; control `0`; columnas obligatorias
`5 de 5`; migración registrada en los dos tenants. **Antes** de B, lo normal
es `0 de 5` y `ninguno`; los "sin año" y el control pueden no ser 0 si en la
ventana se crearon cosas o se editaron estudiantes, y eso es justo lo que B
corrige.

**Probada y aplicada el 2026-10-01** (la corrió el usuario, paso a paso):

- Rama de Neon `prueba-anio-lectivo-b`, copia de `production` con datos.
  Su servidor (`ep-super-hall-...`) se comprobó distinto del de producción
  (`ep-late-smoke-aip41j6x`) y sin `-pooler`.
- "Antes", en la rama: nada sin año en ninguna tabla (12 cursos, 2
  conceptos, 552 pagos, 209 anotaciones, 174 matrículas para 174
  estudiantes con curso), control 0, `0 de 5`, B en `ninguno`. Los 6 pagos
  nuevos desde la migración A (546 → 552) ya tenían año: los escribió el
  código nuevo. La ventana no dejó nada que rellenar, y B solo volvió
  obligatorias las columnas.
- En la rama: `--dry-run` `PENDIENTE` en los dos tenants; aplicación `OK`
  en los dos, sin que saltara ningún freno. Fue la primera ejecución real
  del SQL. "Después": los mismos números, `5 de 5` y B registrada en
  `tenant_colegio_1` y `tenant_2005`.
- App local contra la rama, con el backend viejo detenido antes (se
  comprobó el puerto 8000 libre y luego ocupado por el nuevo): el usuario
  creó un curso, un concepto y un pago, y creó y editó un estudiante, sin
  errores. Consulta de comprobación: en la rama, `PRUEBA B` existe (1
  curso, 1 concepto, 1 estudiante en `tenant_2005`), los pagos pasaron a
  553 y el control siguió en 0 en los dos tenants. En `production`,
  `PRUEBA B` no existe y los pagos siguen en 552: nada de la prueba llegó
  a producción. La anotación del observador (opcional, necesita un
  profesor) no se comprobó con consulta.
- Render: el último despliegue es `67b2d4b`, Auto-Deploy, 1m01s, **Live**.
- Producción (`ep-late-smoke-aip41j6x`, endpoint directo): `--dry-run`
  `PENDIENTE` en los dos tenants; aplicación `OK` en los dos. Comprobación
  en `tenant_2005`: `2026 activo`, nada sin año (12 / 2 / 552 / 209 / 174),
  control 0, `5 de 5`, B registrada en los dos tenants.
- Esquema base regenerado desde `tenant_colegio_1`: 34 tablas, 1 función,
  1 disparador. Revisado el diff: solo las cinco columnas pasan a `NOT
  NULL`, la B entra en la lista de incorporadas (39 → 40) y cambia la
  fecha.
- `scripts/verify.py`: **1500 pasan, 0 fallan**. Se apagó la falla
  esperada de `test_esquema_base.py`. Ruff y `pip check` limpios; `git
  diff --check` limpio.
- Desde aquí la migración B **no se puede editar**: el runner guarda su
  checksum.
- Ojo: para aplicarla, el usuario cambió el `DATABASE_URL` del `.env` local
  al endpoint directo, sin `-pooler`. Conviene devolverlo a `-pooler`: así
  `apply_migration.py` se niega a correr si alguien olvida poner
  `$env:DATABASE_URL` en la terminal, en vez de aplicar directo en
  producción.

Con esto la **fase 1 queda terminada**:
- El control da 0 en los dos tenants: lo exige el freno final de B, que
  pasó en los dos, y lo confirma la consulta de `tenant_2005`.
- Las pruebas de la fase 0 siguen iguales y `verify.py` pasa.
- La app local se usó contra la rama con B aplicada, sin errores ni
  cambios visibles reportados.

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

**Plan por pasos (propuesto el 2026-10-01; cada paso, con el visto bueno
del usuario):**

Principios:

- Con un solo año, como hoy, cada respuesta queda idéntica. Las
  caracterizaciones de la fase 0 y las de conteo de consultas
  (`tests/test_reportes_query_counts.py`: estado de cuenta del curso en
  reportes 6/15/15, cartera 5/12/12, estado de cuenta por estudiante 12 por
  estudiante) no cambian. El año viaja como subconsulta o junto con los
  conceptos, sin idas extra a la base.
- La pieza clave ya existe: cada concepto es de un año (decisión 17).
  `obtener_tipos_pago` devuelve los conceptos de un año, cada uno con su
  `anio`, y de ahí salen las cuotas, los pagos que cuentan y los precios.
- El frontend no cambia en esta fase: sus peticiones no mandan año y
  obtienen el año activo.
- Supuesto: todo colegio operativo tiene las migraciones A y B (hoy, los
  dos).

Paso 2.1 — Las cuotas se cuentan en el año activo, no en el año del
calendario. Arregla el error del 1 de enero (caso B) aunque no se haga
nada más.

- `app/services/cartera.py`: `listar_cuotas_vencidas`,
  `calcular_cuotas_vencidas` y `calcular_deuda_concepto` reciben `anio`
  opcional, el año cuyas cuotas se listan; sin él, `hoy.year`, como hoy. El
  corte sigue siendo `hoy`: un año pasado tiene todas sus cuotas vencidas y
  uno futuro, ninguna. Reemplaza la regla del punto 2 ("cerrado → 31 de
  diciembre") por una equivalente y más simple, que además respeta los días
  de gracia que pasan de diciembre. Un concepto sin `mes_inicial` ("solo la
  cuota del mes actual") toma diciembre como mes de referencia en un año
  pasado.
- `app/services/cobros.py`: `obtener_tipos_pago` devuelve solo los
  conceptos del año activo, cada uno con su `anio` (JOIN a
  `anios_lectivos` en la misma consulta). `_calcular_deudas` y
  `obtener_cuotas_vencidas_estudiante` pasan el `anio` del concepto.
- `app/controllers/pagos_controller.py`: `_periodos_programados` usa el
  año del concepto. En el año en curso, los meses que faltan, como hoy; en
  un año futuro, todos sus meses; en uno pasado, ninguno.
- Alcance, sin cambio visible hoy: Pagos (deudas, meses vencidos,
  adelantos, registrar), detalle de Estudiantes, Cartera vencida y los
  indicadores del inicio del admin. También `/estado-cuenta/...` y
  `/reportes/estado-cuenta/{curso_id}`, que ninguna pantalla usa hoy.
- Pruebas: se invierten "caso B" y "meses vencidos de 2026 desaparecen en
  enero". Las demás de la fase 0 y las de conteo quedan iguales.

Paso 2.2 — Cada año cobra con sus propios pagos, precios y estudiantes.

- Pagos y aplicaciones filtrados por año en `obtener_pagos_por_concepto_estudiantes`
  (pagos del año; aplicaciones de conceptos del año), en el estado de
  cuenta (`estado_cuenta_controller.py`, `reportes_repository.py`) y en
  cartera.
- El curso del precio sale de la matrícula del año
  (`obtener_curso_estudiante`). Los estudiantes de cartera y del estado de
  cuenta por curso salen de las matrículas, y el estado de cuenta de un
  curso usa el año de ese curso. *Ajustado al hacerlo (2026-10-01):* lo de
  los estudiantes desde las matrículas pasó al 2.4, y el estado de cuenta
  por curso sigue con el año activo. Ver el "Avance" del paso 2.2.
- Hoy queda idéntico: un solo año y el control del curso vigente en 0.
- Pruebas: se invierte "la matrícula del año siguiente se suma a la del año
  en curso".

Paso 2.3 — Registrar un pago en otro año y adelantar meses del año
siguiente.

- `PagoCreate` y `PagoAdelantadoCreate` aceptan `anio_lectivo_id`
  opcional; sin él, el año activo. Se valida que exista, y cualquier estado
  vale (decisión 6; las rutas de pagos ya son solo de admin). El pago se
  guarda con ese año.
- La validación "no exceder la deuda", los meses vencidos y los adelantos
  se calculan con los conceptos de ese año. Una aplicación tiene que ser de
  un concepto de ese año.
- `GET /estudiantes/{id}/deudas`, `/pagos/vencidos/opciones/{id}` y
  `/pagos/adelanto/opciones/{id}` aceptan `?anio_lectivo_id=` opcional:
  lo necesita el selector "Año del pago" de la fase 5 del frontend.
- Pruebas: pago a un año cerrado, pago a uno en preparación, precio del
  curso de 2027, adelantos de 2027 en diciembre, y año inexistente → 400.
  Se invierte "adelantos de diciembre".

Paso 2.4 — Deuda de años anteriores (decisión 2).

- `GET /estudiantes/{id}/deudas` y `/cartera/mora` ganan un campo nuevo con
  la deuda de cada año anterior en que el estudiante tuvo matrícula,
  calculada con la misma función. Queda vacío mientras haya un solo año.
- Los estudiantes de cartera, y los de cada año anterior, salen de las
  matrículas (pasado aquí desde el 2.2). *Ajustado al hacerlo (2026-10-01):*
  los de cada año anterior sí; la lista de cartera del año pasó a la fase
  3, donde cartera recibe el año como parámetro. "Anterior" es anterior al
  año que se mira (por defecto, el activo).
- Antes de escribirlo se mide cuántas consultas agrega, y el usuario decide
  si se acepta.
- Pruebas: caso A completo con dos años (2027 activo: matrícula 2027 +
  febrero y marzo; 2026 en "años anteriores") y caso B después de activar
  2027.

En cada paso: caracterización primero, cambio mínimo, `verify.py`,
documento y mensaje de commit. El usuario aprueba el siguiente. Cada paso
se puede desplegar solo, porque con un año no cambia nada.

Orden por urgencia: 2.1 arregla el error del 1 de enero. 2.2 y 2.3 hacen
falta antes del primer pago de matrícula 2027 (fase 5). 2.4 hace falta
antes de activar 2027 (fase 6), y para entonces el frontend tiene que
mostrar ese campo.

**Avance del 2026-10-01 — paso 2.1, las cuotas se cuentan en el año del
concepto (sin desplegar):**

- Código:
  - `app/services/cartera.py`: `listar_cuotas_vencidas`,
    `calcular_cuotas_vencidas` y `calcular_deuda_concepto` reciben `anio`
    opcional; sin él, `hoy.year`. Nuevo `_mes_de_referencia` para los
    conceptos sin `mes_inicial`: el mes de hoy en el año en curso,
    diciembre en un año que terminó y enero en uno que no ha empezado.
  - `app/services/cobros.py`: `obtener_tipos_pago` trae solo los conceptos
    del año activo, cada uno con su `anio` (JOIN a `anios_lectivos` en la
    misma consulta, columnas con el alias `tp.`). `_calcular_deudas` y
    `obtener_cuotas_vencidas_estudiante` pasan ese `anio`.
  - `app/controllers/pagos_controller.py`: `_periodos_programados` ofrece
    meses del año del concepto.
- No cambió: pagos, aplicaciones, precios y cursos (paso 2.2), ni ninguna
  ruta, esquema o respuesta. El frontend no se tocó.
- Pruebas:
  - Nuevo `tests/test_anio_lectivo_cobros_por_anio.py` (12). Dos comparan
    el código nuevo con una copia literal del anterior en 10.368
    combinaciones de fecha de 2026 y configuración de cuotas, y en 2.700 de
    adelantos: con el año del calendario, el resultado es idéntico. Las
    otras diez fijan lo nuevo: año que terminó, año que no ha empezado,
    días de gracia que pasan de diciembre, concepto sin mes inicial,
    conceptos que traen su año, y adelantos de un año futuro y de uno
    pasado.
  - Invertidas en `test_anio_lectivo_cobros_caracterizacion.py`: el caso B
    y los meses vencidos de 2026 en enero. Las cinco de "dentro del año" y
    las otras cuatro de "error actual" siguen iguales.
  - Ajustadas a propósito, solo en la fila simulada (13 columnas) y el
    texto que reconocen (`order by tp.id`): `test_reportes_query_counts.py`,
    `test_pagos_escrituras_caracterizacion.py` y
    `test_tipos_pagos_mes_final.py`. Lo que vigilan no cambió: los conteos
    siguen en 6/15/15, 1/13/37 y 5/12/12.
  - Corridas contra una copia del código anterior, sacada de git a una
    carpeta temporal: las 12 que exigen lo nuevo fallan y las de "dentro
    del año" pasan. No son pruebas vacías.
- Verificación: `scripts/verify.py` → **1512 pasan, 0 fallan**; ruff y
  `pip check` limpios; `git diff --check` limpio.
- Efecto al desplegar: ninguno visible mientras el año activo sea el del
  calendario (2026). Desde el 1 de enero de 2027, mientras 2026 siga
  activo, sus cuotas siguen contando (caso B).
- Commit `b2362f1` (hecho por el usuario el 2026-10-01).

**Avance del 2026-10-01 — paso 2.2, cada año cuenta solo sus pagos (sin
desplegar):**

- Código:
  - `app/services/cobros.py`: `obtener_pagos_por_concepto_estudiantes`
    suma solo los pagos del año activo, y las aplicaciones solo de
    conceptos de ese año. `obtener_curso_estudiante` toma el curso de la
    matrícula del año activo, no de `estudiantes.curso_id`.
  - `app/controllers/estado_cuenta_controller.py` y
    `app/repositories/reportes_repository.py`: lo pagado en el estado de
    cuenta (las tres consultas de pagos) cuenta solo el año activo.
  - En todos, el año va como la subconsulta `ANIO_ACTIVO_ID_SQL` de la fase
    1: sin parámetros ni consultas nuevas.
- Ajuste del plan: sacar de las matrículas los estudiantes de cartera y del
  estado de cuenta por curso pasa al paso 2.4, donde hace falta para los
  años anteriores. Con el año activo, `estudiantes.curso_id` y la matrícula
  son lo mismo (control en 0), así que hacerlo ahora no cambiaba nada. El
  estado de cuenta por curso sigue calculando con el año activo: ninguna
  pantalla lo usa hoy, y la lectura por año de lo que parte de un curso es
  de la fase 3.
- Hoy queda idéntico: hay un solo año, todo pago tiene año (`NOT NULL`
  desde la migración B) y el control del curso vigente da 0.
- Pruebas:
  - `tests/test_anio_lectivo_cobros_por_anio.py`, 4 nuevas: el filtro del
    año en cada consulta de pagos y de aplicaciones (sin parámetros
    nuevos), el curso desde la matrícula, el estado de cuenta y sus
    reportes.
  - Invertidas en `test_anio_lectivo_cobros_caracterizacion.py`, con una
    base de pagos simulada que, como PostgreSQL, se queda con los pagos del
    año activo cuando la consulta trae el filtro: la matrícula del año
    siguiente, el caso A (con 2027 activo debe la matrícula, febrero, marzo
    y la salida pedagógica de 2027) y los meses vencidos de 2027. Solo
    queda sin invertir "adelantos de diciembre", que es del paso 2.3.
  - Ajustadas a propósito, solo en la consulta que reconocen (la del curso
    del estudiante): `test_pagos_escrituras_caracterizacion.py` y
    `test_reportes_query_counts.py`. Los conteos siguen en 6/15/15,
    1/13/37 y 5/12/12.
  - Corridas contra el código del paso 2.1: fallan exactamente las 7 del
    paso 2.2 y pasan las otras 20.
- Verificación: `scripts/verify.py` → **1516 pasan, 0 fallan**; ruff y
  `pip check` limpios; `git diff --check` limpio.
- Efecto al desplegar: ninguno visible con un solo año. Cuando exista 2027
  (fase 5), sus pagos no se mezclan con los de 2026.
- Commit `34712dd` (hecho por el usuario el 2026-10-01).

**Avance del 2026-10-01 — paso 2.3, pagar en otro año y adelantar meses del
año siguiente (sin desplegar):**

- Código:
  - `app/services/cobros.py`: `obtener_tipos_pago`,
    `obtener_curso_estudiante`, `obtener_pagos_por_concepto(_estudiantes)`,
    `obtener_conceptos_mensuales_estudiante`,
    `obtener_cuotas_vencidas_estudiante`, `calcular_deudas_estudiante` y
    `obtener_saldo_concepto` aceptan `anio_lectivo_id` opcional. Sin él, la
    consulta y los parámetros son los del paso 2.2; con él, el año va como
    un parámetro más. `con_anio()` solo pasa el año cuando se pidió, así que
    el camino del año activo hace exactamente las mismas llamadas que antes.
    Si el estudiante no tiene matrícula en el año pedido, el mensaje lo dice;
    sin año, sale el mensaje de siempre.
  - `app/repositories/pagos_repository.py`: `insertar_pago` e
    `insertar_pago_adelantado` aceptan el año; sin él, la sentencia de la
    fase 1.
  - `app/repositories/anios_lectivos_repository.py`: `leer_anio_lectivo`.
    Nuevo `app/services/anio_lectivo.py`, el servicio que este documento
    preveía, con `exigir_anio_lectivo`: si el año no existe, `ValueError`
    con el mensaje listo. Cualquier estado vale (decisión 6).
  - `app/controllers/pagos_controller.py`: registrar un pago o un adelanto
    con año (se valida el año, se calculan la deuda y los meses de ese año,
    y se guarda en él), y las opciones de meses vencidos y de adelanto con
    año. Una aplicación solo puede ser de un concepto del año del pago,
    porque las cuotas válidas se calculan con los conceptos de ese año.
  - `app/controllers/estudiante_controller.py`, `app/routes/pagos.py`,
    `app/routes/estudiantes.py` y `app/schemas/pago.py`: el parámetro
    `?anio_lectivo_id=` (entero mayor que 0, opcional) en las tres
    consultas, y el campo opcional en los dos cuerpos. Un año que no existe
    da 400 en pagos y 404 en deudas, como los demás errores de cada ruta.
- Sin año, todo queda igual: las 1516 pruebas que ya existían pasaron sin
  tocar ninguna, incluidas las de escrituras de pagos y las de conteo de
  consultas.
- Pruebas: `tests/test_anio_lectivo_cobros_por_anio.py`, 22 nuevas (con los
  casos parametrizados):
  - las consultas con y sin año, y el precio del curso de 2027 (350.000
    frente a 300.000 en 2026, con una base simulada de dos años);
  - el mensaje sin matrícula y el INSERT con el año;
  - pago a un año cerrado y a uno en preparación, año inexistente (no se
    registra y se revierte) y pago sin año (ni siquiera se consulta el año);
  - cuotas del año del pago, y opciones y registro de adelantos de 2027 en
    diciembre;
  - deudas del estudiante en otro año, rutas y esquemas.

  Se invirtió la última `test_error_actual_`, la de "adelantos de
  diciembre": la cuenta de meses por año ya existía desde el 2.1, y el 2.3
  la conecta con el año del pago. Contra el código del paso 2.2 fallan 21
  de las 22 nuevas; pasa la que comprueba que, sin año, los conceptos se
  piden igual.
- Documentación: `docs/API_ENDPOINTS.md` (el parámetro y el campo nuevos).
- Verificación: `scripts/verify.py` → **1538 pasan, 0 fallan**; ruff y
  `pip check` limpios; `git diff --check` limpio.
- Efecto al desplegar: ninguno visible, porque el frontend todavía no manda
  el año. Queda listo para el selector "Año del pago" de la fase 5 del
  frontend.
- Commit `b5f4099` (hecho por el usuario el 2026-10-01).

**Avance del 2026-10-01 — paso 2.4, deuda de años anteriores (sin
desplegar):**

- Medición previa y decisión del usuario (2026-10-01), como pedía el plan.
  Medido antes: deudas de un estudiante 11 consultas; cartera 12 con
  estudiantes y 5 sin ellos. Calculado sobre el diseño: +1 en cada pantalla
  mientras haya un solo año; con años anteriores, +8 en deudas y +5 en
  cartera, sin crecer con los estudiantes. El usuario lo aceptó. Medido
  después, ya escrito: **exactamente esos números** (12 y 13 hoy; 19 y 17
  con un año anterior). Quedan fijados en pruebas.
- Código:
  - `app/services/cobros.py`: `calcular_deudas_anios_anteriores(cursor,
    estudiante_ids, ...)` calcula para varios estudiantes a la vez. Una
    consulta busca las matrículas de años anteriores al que se mira; si no
    hay, termina ahí. Si hay, trae en una consulta los conceptos de esos
    años, los precios de esos cursos y los valores por estudiante (o los
    recibe ya cargados, como hace cartera) y, en tres, lo pagado por
    estudiante y año. Cada año se calcula con `_calcular_deudas`, la misma
    regla de siempre, y solo se devuelven años y conceptos con deuda. Se
    sacó `_concepto_desde_fila` para no repetir la lectura de un concepto.
  - `app/controllers/estudiante_controller.py`: `GET
    /estudiantes/{id}/deudas` trae `deuda_anios_anteriores`, aparte de
    `total_deuda`.
  - `app/controllers/cartera_mora_controller.py`: cada estudiante trae
    `deuda_anios_anteriores`, aparte de `total`. Un estudiante que solo debe
    de años anteriores también aparece (con `total` 0), y el resumen suma
    `total_anios_anteriores`.
- Pruebas:
  - `tests/test_anio_lectivo_cobros_por_anio.py`, 10 nuevas, con una base
    simulada de dos años (2026 cerrado y 2027 activo) y el reloj fijado en
    el 15 de enero de 2027:
    - **caso B completo**: con 2027 activo, la matrícula de 2027 en la deuda
      del año y octubre y noviembre de 2026 ($400.000) aparte;
    - **caso A completo**: con 2026 pagado entero, no hay deuda de años
      anteriores (lo de 2027 quedó probado en el paso 2.2);
    - cartera con deuda de 2026 y con un estudiante que solo debe de 2026;
    - una sola consulta sin años anteriores, y ninguna sin estudiantes;
    - y los conteos medidos.
  - Ajustadas a propósito, por el campo nuevo y el costo aceptado: el
    conteo de cartera en `test_reportes_query_counts.py` (12 → 13, con la
    consulta nueva reconocida), y la respuesta de deudas en
    `test_asignaciones_estudiantes_caracterizacion.py` y en la prueba del
    paso 2.3.
  - Contra el código del paso 2.3: fallan las 10 nuevas y la del 2.3
    ajustada; pasan las otras 37.
- Documentación: `docs/API_ENDPOINTS.md` (los campos nuevos de deudas y
  cartera).
- Verificación: `scripts/verify.py` → **1548 pasan, 0 fallan**; ruff y
  `pip check` limpios; `git diff --check` limpio.
- Efecto al desplegar: ninguno visible mientras haya un solo año. Hoy, una
  consulta más en las deudas de un estudiante y en cartera (unos 60 ms).
  El frontend tiene que mostrar `deuda_anios_anteriores` antes de activar
  2027 (fase 6).
- Commit `f03b032` (hecho por el usuario el 2026-10-01).

**Con esto, el código de la fase 2 queda completo (2026-10-01).** Se
cumplen las condiciones del punto 9:
- Las caracterizaciones de "dentro del año" siguen iguales.
- Los casos A y B dan el resultado correcto: A, debe la matrícula 2027,
  febrero y marzo; B, los $400.000 de 2026 se ven como deuda anterior.
- Hay pruebas de pago a un año cerrado, pago a uno en preparación y precio
  del curso de 2027.
- `verify.py` pasa.

Falta que el usuario lo revise en local y lo despliegue. Al 2026-10-02 los
cuatro commits siguen sin subir (`git status`: `ahead 4`).

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
   - Cartera y estado de cuenta (pasado aquí desde la fase 2, 2026-10-01):
     `GET /cartera/mora` acepta `?anio_lectivo_id=`, y su lista de
     estudiantes sale de las matrículas de ese año
     (`cartera_mora_controller.py`). El estado de cuenta por curso
     (`estado_cuenta_controller.py`, `reportes_controller.py`) usa el año
     de ese curso. Los cálculos ya aceptan el año desde el paso 2.3.
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

**Inventario confirmado el 2026-10-02** (con `grep` sobre `app/`, como pide
el punto 2; solo lectura, sin cambios de código):

- Lo que ya estaba en la lista sigue ahí: `curso_controller.py` (nombre
  repetido `:26`, listado `:113`, paginado y conteo `:137`),
  `listas_seguimiento_repository.py:211` y `:226`, `reportes_repository.py:9`
  y `:31` (antes `:6` y `:28`; se corrieron con el `import` de la fase 2) y
  `:211` (estudiantes del estado de cuenta por curso),
  `cartera_mora_controller.py:96`, `boletin_repository.py` (`:103`, `:181`,
  `:241`, `:261`, `:300`, `:343`), `tipos_pagos_controller.py` (crear `:25`,
  listar `:56`, detallado `:204`, cursos de un concepto `:379`, guardar
  precios `:427`) y el observador del admin (`observador_repository.py:82`,
  `leer_bitacora`).
- Asignaciones del profesor, ubicadas: "mis clases"
  (`leer_clases_con_horario_de_profesor`, `asignaciones_repository.py:639`),
  `GET /profesores/{id}/cursos` (`leer_cursos_de_profesor`, `:436`, abierta a
  profesores) y el inicio del profesor (`dashboard_repository.py:144`
  inasistencias y `:178` promedios). **Corrección:** `profesor_controller.py`
  sale del inventario. Su `obtener_clases_profesor_controller` (`:203`) no
  tiene ruta, igual que la homónima de `asignacion_controller.py:421`
  (código sin uso; no se borra sin permiso).
- **Nuevo, no estaba en la lista:**
  1. **Choques de horario del profesor.** `verificar_cruce_horario` y
     `verificar_cruce_horario_editar` (`asignacion_controller.py:318` y
     `:584`, con `leer_horarios_del_dia` y `leer_horarios_del_dia_excluyendo`
     de `asignaciones_repository.py:257` y `:272`) y la disponibilidad
     (`leer_horarios_ocupados`, `:350`, `GET
     /profesores/{id}/disponibilidad`) miran todas las clases del profesor,
     de cualquier año. Sin filtro, al armar la carga de 2027 (fase 5) cada
     clase chocaría con la del mismo profesor a la misma hora en 2026, y la
     pantalla lo mostraría ocupado. Se limitan al año del curso. El choque
     por curso no necesita año: el curso ya lo implica.
  2. **Listados de asignaciones del admin:** `GET /asignaciones/lista`
     (`asignaciones_repository.py:570`, `:592`, `:605`) y `GET
     /hora/horarios-admin` (`:472`). La lista anterior hablaba de horarios
     solo del lado del profesor.
  3. **Detalle del estudiante** (`GET /estudiantes/{id}/detalles`,
     `estudiantes_repository.py:219`, `:235` y `:244`): promedios, faltas y
     observaciones suman todos los años. La deuda de esa respuesta ya es
     del año activo (fase 2). Se mezclaría desde que 2027 tenga notas, o
     sea, después de activarlo.
  4. **Nombre repetido al editar un concepto** (`actualizar_tipo_pago`,
     `tipos_pagos_controller.py:67`), además del de crear.
  5. **Planes de clase del admin** (`GET /admin/plan-de-clases`): lista los
     de todos los años.
  6. Para la fase 5, no la 3: los valores especiales por estudiante
     (`/estudiantes/{id}/valores-pago-personalizados`) listan los de todos
     los años, y al guardar uno toman el precio del curso de
     `estudiantes.curso_id` (`tipos_pagos_controller.py:613`). Es lo que
     ordena la decisión 8.
- **Sin año, a propósito** (no se tocan): lo que parte de un `curso_id` o
  un `asignacion_id` (planilla, asistencia, planeador, observaciones, plan
  de clases del profesor, listas de un curso, orden del boletín); lo que el
  profesor alcanza por `estudiantes.curso_id`, que es siempre del año activo
  (`permissions.py`, `notas_repository.py`, `observador_repository.py:133`,
  cumpleaños); y `/notas/{id}`, `/boletin/{id}` y `/boletin/detallado/{id}`,
  que ninguna pantalla del frontend usa (búsqueda en
  `frontend-react/src`).
- **Rutas que escriben datos académicos** (punto 4, la guardia), 33:
  - Profesor y admin (12): `POST /notas`, `POST /planilla/nota`, `DELETE
    /planilla/tipo`, `POST /asistencia`, `POST /boletines/guardar`, `POST
    /observaciones`, `POST /observador`, `PUT /observador/{id}`, `PUT
    /planeador-anual/{asignacion_id}/{periodo}`, `POST /plan-de-clases`,
    `DELETE /plan-de-clases/{id}/imagen` y `PATCH
    /plan-de-clases/{id}/observaciones/{id}/vista`.
  - Solo admin (21): asignaciones (`POST`, `PUT`, los dos `DELETE` y `PUT
    /cursos/{id}/orden-boletin`), cursos (`PUT` y `PATCH .../estado`),
    listas de seguimiento (las 4), planes de clase (`PATCH .../revision`,
    `POST .../observaciones`, `DELETE /admin/.../imagen`), conceptos (`PUT`,
    `DELETE`, `PUT .../configuracion`, `PUT` y `DELETE .../cursos`) y
    valores por estudiante (`PUT` y `DELETE`).
  - Sin guardia, a propósito: `POST /cursos` y `POST /tipos-pagos` (hoy
    siempre crean en el año activo, que es editable; ver "Preguntas
    abiertas"), estudiantes y materias (no tienen año; materias tiene el
    aviso del punto 3) y pagos (decisión 6).

**Plan por pasos (propuesto el 2026-10-02; cada paso, con el visto bueno del
usuario):**

Principios, los mismos de la fase 2: con el año activo cada respuesta y
cada consulta quedan idénticas (caracterización antes de cambiar); el año
viaja como la subconsulta `ANIO_ACTIVO_ID_SQL` o como un parámetro, sin
consultas extra en las lecturas; un paso se puede desplegar solo.

- **3.1 — Años lectivos y la regla del año pedido.** `GET /anios-lectivos`
  (admin: todos; profesor: solo el activo) y, en `app/services/anio_lectivo.py`,
  la regla común para `?anio_lectivo_id=`: sin él, el activo; un profesor
  que pide otro, 403; uno que no existe, error. No cambia ninguna respuesta
  existente.
- **3.2 — Profesor y horarios, solo del año.** "Mis clases", cursos del
  profesor e inicio del profesor, limitados al año activo; listados de
  asignaciones y horarios del admin con el año pedido; choques de horario y
  disponibilidad por el año del curso (hallazgo 1). Es lo que más gente usa:
  todos los profesores.
- **3.3 — Cursos y conceptos por año.** Listados de cursos; nombre repetido
  de cursos y conceptos (crear y editar) dentro del año; listado y detalle
  de conceptos; cursos ofrecidos para precios, y al guardar un precio,
  concepto y curso del mismo año; listas de seguimiento "en todos los
  cursos"; reporte general.
- **3.4 — Estudiantes y cartera desde las matrículas** (dinero: zona
  sensible). Listado y conteo de estudiantes del año pedido, con los mismos
  resultados de hoy para el activo (incluidos los sin curso); `GET
  /cartera/mora` y su resumen con `?anio_lectivo_id=`; estado de cuenta por
  curso con el año de ese curso.
- **3.5 — Boletín, certificados y consultas del admin por año.** Boletín,
  reporte parcial y puesto desde la matrícula del año pedido; observador
  del admin; detalle del estudiante (hallazgo 3); planes de clase del admin
  (hallazgo 5).
- **3.6 — Aviso al renombrar una materia** (punto 3, decisión 12).
- **3.7 — Guardia de escritura** en las 33 rutas (punto 4). Antes de
  escribirla se mide cuántas consultas agrega a cada guardado, y el usuario
  decide, como en el paso 2.4: averiguar el año de una asignación cuesta
  una ida a la base (~60 ms) si no se junta con una consulta que ya exista.

Los siete pasos van antes de la fase 4: el orden de fases es obligatorio.
Dentro de la fase, van primero los que bloquearían la fase 5 (3.2 y 3.3: sin
ellos, crear el primer curso o la primera clase de 2027 se mezclaría con
2026 o chocaría con sus horarios).

**Avance del 2026-10-02 — paso 3.1, los años lectivos y la regla del año
pedido (sin desplegar):**

- Plan y paso aprobados por el usuario el 2026-10-02 ("continúa"), con las
  dos preguntas abiertas de la fase 3 todavía sin respuesta (no afectan
  este paso).
- Código, todo nuevo; ninguna respuesta existente cambia:
  - `GET /anios-lectivos` (`app/routes/anios_lectivos.py`, archivo nuevo),
    protegida en el router con `get_current_user`: admin y profesor. Responde
    `[{id, anio, estado}]`, el más reciente primero. Solo esos tres campos:
    las fechas de la tabla no las necesita ninguna pantalla todavía, y
    agregarlas después no rompe nada.
  - `app/controllers/anios_lectivos_controller.py` (nuevo): abre el cursor y
    da forma a la respuesta.
  - `app/services/anio_lectivo.py`: `listar_anios_visibles` (admin, todos,
    decisión 3; cualquier otro rol, solo el activo, decisión 4) y
    `resolver_anio_pedido`, la regla que usarán los listados de los pasos
    3.2 a 3.5. Sin año devuelve `None` **sin consultar nada** (quien llama
    usa `ANIO_ACTIVO_ID_SQL`); con año, `ValueError` si no existe y
    `AnioLectivoNoPermitidoError` si quien no es admin pide uno que no es el
    activo. Cada ruta traducirá esos errores a 404 y 403.
  - `app/repositories/anios_lectivos_repository.py`: `listar_anios_lectivos`
    y `leer_anio_activo`. No se creó un repositorio nuevo: cinco pruebas
    enumeran todos los repositorios y este ya estaba.
- Pruebas: `tests/test_anio_lectivo_lecturas.py`, 21 nuevas, sin base de
  datos: qué ve cada rol (con una consulta), que sin año pedido no se
  consulta nada, que el admin puede mirar un año en cualquier estado, que el
  profesor solo el activo, el mensaje de año inexistente, la forma de la
  respuesta, y la ruta por HTTP (protección en el router, 401 sin sesión,
  admin y profesor reciben 200). Cinco versiones dañadas del código las
  hacen fallar: orden ascendente, un rol desconocido que ve todo, consultar
  sin año pedido, profesor con cualquier año y router sin protección.
- Documentación: `docs/API_ENDPOINTS.md`, `docs/ROLES_PERMISOS_BACKEND.md` y
  `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1569 pasan, 0 fallan** (antes
  1548); ruff y `pip check` limpios; `git diff --check` limpio. Corrido con
  un `DATABASE_URL` inventado, como en CI.
- Efecto al desplegar: una ruta nueva que ninguna pantalla usa todavía. Se
  puede probar en local (solo lee; el backend local apunta a la base real):
  con la sesión del admin iniciada en el frontend local, abrir en otra
  pestaña `/anios-lectivos` en la **misma dirección** del `VITE_API_URL`
  del frontend (normalmente `http://localhost:8000`; con `127.0.0.1` la
  sesión no viaja). Debe mostrar `[{"id": 1, "anio": 2026, "estado":
  "activo"}]` (el `id` puede ser otro). Con un profesor, lo mismo.
- Commit `fea2e83` (hecho por el usuario el 2026-10-02).

**Avance del 2026-10-02 — paso 3.2, profesor y horarios solo del año (sin
desplegar):**

- Aprobado por el usuario el 2026-10-02 ("por ahora continúa"). Pidió que
  las preguntas abiertas se le hagan justo antes del paso que las necesita.
- Código:
  - `app/repositories/anios_lectivos_repository.py`: `condicion_anio(columna,
    anio_lectivo_id)`, el filtro que usarán todos los listados por año. Sin
    año devuelve la subconsulta del activo y ningún parámetro; con año,
    `%s`. Así la consulta de hoy conserva sus parámetros y su número.
  - Lo que ve el profesor, siempre el año activo y sin parámetro nuevo:
    "mis clases" (`leer_clases_con_horario_de_profesor`), sus cursos
    (`leer_cursos_de_profesor`) y las faltas de su inicio
    (`dashboard_repository.leer_inasistencias_por_curso`). Revisado y sin
    cambio: los promedios del inicio parten de un curso, y los cumpleaños, de
    `estudiantes.curso_id`.
  - Choques de horario (hallazgo 1): `leer_horarios_del_dia` y
    `leer_horarios_del_dia_excluyendo` reciben el curso de la clase que se
    guarda y solo miran clases de cursos de su mismo año, con una
    subconsulta dentro de la misma consulta. `verificar_cruce_horario` y
    `verificar_cruce_horario_editar` lo pasan, en el alta y en la edición.
  - Listados del admin con `?anio_lectivo_id=` (sin él, el activo; si no
    existe, 404): `GET /asignaciones/lista` (con y sin paginar), `GET
    /hora/horarios-admin` y `GET /profesores/{id}/disponibilidad`. Son rutas
    solo de admin, así que validan el año con `exigir_anio_lectivo`, como las
    deudas del paso 2.3; `resolver_anio_pedido` queda para las rutas que
    también usa el profesor.
- No se tocó: `obtener_clases_profesor_controller` de `asignacion_controller`
  y de `profesor_controller`, que no tienen ruta; lo que parte de un curso o
  de una asignación.
- Pruebas:
  - `tests/test_anio_lectivo_lecturas.py`, 34 nuevas. La principal usa una
    base simulada con una clase de 2026 y una de 2027 del mismo profesor, que
    como PostgreSQL solo filtra por año si la consulta trae el filtro: la de
    2026 ya no choca con una de 2027 a la misma hora, y dentro de cada año el
    choque se detecta como siempre (alta, edición y por curso). Además: el
    flujo completo de crear y editar pasa el curso a los dos cruces y sigue
    en 13 y 11 consultas; las tres lecturas del profesor; los listados del
    admin con y sin año (sin año, sin parámetros); el orden de parámetros del
    paginado (el año antes de `limit`); la disponibilidad; un año inexistente
    que no llega a consultar el listado; y las tres rutas por HTTP (pasan el
    año, 422 con 0, 404 si no existe).
  - Ajustadas a propósito: los dos dobles de ruta de
    `tests/test_asignaciones_pagination.py`, que ahora reciben el año (y
    comprueban que sin año llega `None`). Las demás 1567 pruebas, incluidas
    las que cuentan consultas al crear y editar asignaciones y en el inicio
    del profesor, pasaron sin tocarlas.
  - Catorce versiones dañadas del código las hacen fallar: cada filtro
    quitado, cada listado que ignora el año, crear y editar pasando otro id
    como curso, el paginado sin año, los horarios sin validar el año, la ruta
    que no pasa el año y la ruta sin 404.
- Documentación: `docs/API_ENDPOINTS.md` (Asignaciones y Dashboard) y
  `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1603 pasan, 0 fallan** (antes
  1569); ruff y `pip check` limpios; `git diff --check` limpio.
- Para el frontend (su fase 4): esas tres rutas del admin ya aceptan el año.
  Se anota en su documento al cerrar la fase 3, con el contrato completo.
- Efecto al desplegar: ninguno visible mientras haya un solo año. Revisión
  en local recomendada (solo lectura, el backend local lee la base real):
  con un profesor, "mis clases" y su inicio iguales que en producción; con
  el admin, la lista de asignaciones, los horarios y la disponibilidad de un
  profesor al crear una clase. **No crear ni editar clases en local**: eso
  escribe en la base real.
- Commit `43764f2` (hecho por el usuario el 2026-10-02).

**Avance del 2026-10-02 — paso 3.3, cursos y conceptos por año (sin
desplegar):**

- Aprobado por el usuario el 2026-10-02 ("continúa"). Toca conceptos de
  pago (zona de dinero): cambio mínimo y ninguna consulta nueva.
- Código:
  - Cursos (`curso_controller.py`, `routes/cursos.py`): `GET /cursos` (con
    y sin paginar) acepta `?anio_lectivo_id=`; sin él, el activo, con
    `condicion_anio` al final de los filtros (sin parámetro nuevo). El
    nombre repetido (`_validar_curso_unico`) compara dentro del año: el
    activo al crear (el curso nace ahí), el del propio curso al editar.
  - Conceptos (`tipos_pagos_controller.py`, `routes/tipos_pagos.py`): `GET
    /tipos-pagos` y `GET /tipos-pagos/detallado` con `?anio_lectivo_id=`; el
    nombre repetido al crear (año activo) y al editar (año del concepto,
    hallazgo 4). Al guardar precios por curso (`upsert_cursos_asignados`),
    la consulta que ya miraba si el concepto existe ahora también devuelve
    los cursos pedidos que son de otro año; si hay alguno, error nuevo
    `CursoDeOtroAnioError` → 400 con sus nombres, y no se guarda nada. Se
    atrapa antes del `except Exception` para que no salga como fallo
    interno (500).
  - Listas de seguimiento: `contar_cursos_activos` y
    `crear_columna_en_cursos_activos` limitadas a un año, y `POST
    /listas-seguimiento/columnas-en-todos-los-cursos` acepta
    `?anio_lectivo_id=` (por defecto el activo; si no existe, 404 sin
    escribir).
  - Reporte general (`reportes_repository.consultar_reporte_general`):
    `total_cursos` y `estudiantes_por_curso`, solo del año activo, sin
    parámetro: los estudiantes por curso salen de `estudiantes.curso_id`,
    que ya es del año activo. Lo de dinero no se tocó.
- No se tocó: `GET /tipos-pagos/{id}/cursos` y `/detalle` (parten de un
  concepto), la segunda consulta de `listar_tipos_pagos_detallado` (trae
  los precios de todos los conceptos y se queda con los del año; el
  resultado es el mismo) y los valores especiales por estudiante (fase 5).
- Pruebas:
  - `tests/test_anio_lectivo_lecturas.py`, 32 nuevas, con tres bases
    simuladas de dos años que, como PostgreSQL, solo separan por año si la
    consulta trae el filtro: "PRIMERO A" puede existir una vez en 2026 y
    otra en 2027, pero no dos en el mismo año (cursos y conceptos, al crear
    y al editar); un concepto de 2027 acepta precios de cursos de 2027 y
    rechaza uno de 2026 sin escribir nada; guardar precios sigue costando 5
    consultas. Más: listados con y sin año (sin año, los parámetros de
    siempre), listas de seguimiento, y las rutas por HTTP (pasan el año, 422
    con 0, 404 si no existe, 400 con el mensaje de precios).
  - Ajustadas a propósito, sin cambiar la respuesta que comprueban: en
    `test_anio_lectivo_listados_caracterizacion.py`, el texto de las dos
    consultas de conceptos y "todos sin `WHERE`" (ahora: sin filtro de
    estado, con el del año); el texto de las dos consultas del reporte en
    `test_reportes_simple_controllers.py`; los dos dobles de la ruta de
    cursos (`test_catalogos_pagination.py`); el doble del repositorio de
    listas (`test_listas_seguimiento_controlador.py`, recibe el año); y las
    bases simuladas de `test_pagos_escrituras_caracterizacion.py` y
    `test_threadpool_capacity.py`, que no conocían la consulta de precios.
    Las demás pruebas pasaron sin tocarlas.
  - Diecisiete versiones dañadas del código las hacen fallar. Una primera
    vuelta encontró un hueco: invertir la comparación de año en los precios
    (`<>` por `=`) no lo detectaba ninguna, porque la base simulada decidía
    sola qué cursos eran de otro año. Se corrigió para que solo separe por
    año si la consulta trae esa comparación exacta.
- Documentación: `docs/API_ENDPOINTS.md` (Cursos, Reportes, Tipos de pagos y
  Listas de seguimiento) y `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1635 pasan, 0 fallan** (antes
  1603); ruff y `pip check` limpios; `git diff --check` limpio.
- Efecto al desplegar: ninguno visible mientras haya un solo año. Revisión
  en local recomendada (solo lectura): Cursos, Tipos de pago (lista y
  detalle de un concepto con sus precios) y la pantalla de reportes con
  "estudiantes por curso", iguales que en producción. **No crear, editar ni
  guardar precios en local**: escribe en la base real.
- Commit `da4da87` (hecho por el usuario el 2026-10-02).

**Avance del 2026-10-02 — paso 3.4, estudiantes y cartera desde las
matrículas (sin desplegar):**

- Zona de dinero: antes de escribir se le explicó al usuario el cambio y el
  costo en consultas, y decidió (2026-10-02) las decisiones 18 (retirados
  con deuda, visibles al mirar ese año) y 19 (ventas solo en el año activo)
  y aceptó una consulta más en `/reportes/estado-cuenta/{curso}`.
- Código:
  - Lista de estudiantes (`estudiantes_repository.py`,
    `estudiante_controller.py`, `routes/estudiantes.py`): `GET /estudiantes`
    con `?anio_lectivo_id=`. Sin año, **o con el activo**, el SQL de siempre,
    letra por letra: todos los estudiantes con su curso actual, porque la
    usan Pagos, Ventas, Boletines y Certificados, y Pagos tiene que encontrar
    también a un estudiante nuevo de 2027 sin curso este año. Con otro año,
    un camino aparte: los matriculados de ese año (subconsulta de
    `matriculas` con la columna renombrada, para que los filtros sin prefijo
    sigan siendo de `estudiantes`), cada uno con su curso de ese año.
  - Cartera (`cartera_mora_controller.py`, `routes/cartera.py`): `GET
    /cartera/mora` y `/resumen` con `?anio_lectivo_id=`. Los estudiantes
    salen de las matrículas del año (`FROM estudiantes e JOIN matriculas
    m`), con el curso de la matrícula, el mismo que fija sus precios desde el
    paso 2.2. Conceptos, pagos y años anteriores se piden con el año (las
    funciones de `cobros.py` lo aceptan desde el 2.3; `cobros.py` no se
    tocó). Mirando el año activo: solo activos y con ventas, como hoy.
    Mirando otro año: sin filtro de estado y sin ventas (decisiones 18 y 19).
  - Estado de cuenta por curso (sin pantalla hoy): `/estado-cuenta/curso/{id}`
    toma los estudiantes de las matrículas del curso y trae el año y su
    estado en la misma consulta; `/reportes/estado-cuenta/{id}` lee primero
    el año del curso (`leer_anio_de_curso`, nueva en el repositorio del año).
    En los dos, si el curso es del año activo se sigue el camino de siempre
    (sin año explícito), como hizo `con_anio` en el paso 2.3.
- Consultas, medidas en pruebas: sin año, iguales (lista 1 y 2; cartera
  5/13/13; estado de cuenta 1/13/37). Con año, una más para validarlo:
  cartera con el id del activo 6/14/14; cartera de otro año 6/13/13 (la
  validación suma una y las ventas, que ya no se consultan, restan una).
  `/reportes/estado-cuenta`: 7/16/16 (antes 6/15/15), aceptado.
- No se tocó: `cobros.py`; el estado de cuenta por estudiante (año activo);
  la consulta de "otros pagos" que compara nombres con conceptos de todos
  los años (con un año el resultado es el mismo).
- Pruebas:
  - `tests/test_anio_lectivo_lecturas.py`, 22 nuevas, con bases simuladas de
    dos años que solo leen matrículas si la consulta las une: la lista de
    estudiantes (sin año y con el activo, la de siempre; con 2026, Luis, que
    se retiró, y Ana con su curso de 2026; filtro de estado; paginado);
    **cartera** (año activo: solo Ana, con su venta; 2026: Ana y Luis, sin
    ventas; el id del activo da lo del activo; curso; resumen; año
    inexistente sin calcular nada); estado de cuenta y reporte de un curso
    de 2026 (calculan en 2026) y del activo (camino de siempre); rutas.
  - `tests/test_reportes_query_counts.py`, 6 nuevas: los conteos de cartera
    con año.
  - Ajustadas a propósito: los dos dobles de la ruta de estudiantes; las
    bases simuladas de estado de cuenta de `test_reportes_query_counts.py`,
    `test_reportes_estado_cuenta.py` y `test_pagos_adelantados.py`, que no
    conocían la lectura del año del curso ni los estudiantes desde
    matrículas; el conteo aceptado del reporte. Cartera no necesitó ningún
    ajuste: su consulta nueva se escribió `FROM estudiantes e JOIN
    matriculas m` y las bases que ya la reconocían siguieron sirviendo.
  - Diecinueve versiones dañadas del código las hacen fallar. Antes de
    correrlas se corrigió una base simulada que habría tapado una: ponía el
    curso de la matrícula aunque la consulta pidiera el curso actual.
- Documentación: `docs/API_ENDPOINTS.md` (Estudiantes, Cuentas, Reportes y
  Cartera) y `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1663 pasan, 0 fallan** (antes
  1635); ruff y `pip check` limpios; `git diff --check` limpio.
- Efecto al desplegar: ninguno visible mientras haya un solo año. Revisión
  en local recomendada (solo lectura): Estudiantes, el buscador de
  estudiantes de Pagos, Cartera vencida (lista, filtro por curso y el
  resumen del inicio), iguales que en producción.

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
  No lo causa ni lo arregla el año lectivo. **Decidido el 2026-10-01:** se
  corrige después de la fase 2, como cambio aparte (ver "Preguntas
  abiertas").
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
- ~~Antes de la fase 2: ¿se corrige primero el hallazgo de conceptos
  desactivados que ocultan deuda?~~ **Respondida el 2026-10-01: no.** El
  usuario decidió que la regla quede como está durante la fase 2 y se
  corrija después, como cambio aparte. Motivos que se le dieron: hoy no hay
  conceptos "único" en `tenant_2005`, así que no afecta a nadie todavía;
  la fase 2 es zona de dinero con fecha límite; y con conceptos por año la
  fase 2 funciona bien con la regla actual. **Trampa a tener en cuenta
  cuando se corrija:** en `tenant_2005` la MATRICULA está inactiva y nadie
  la tiene pagada en el sistema (se cobró por fuera antes de julio). Si
  desactivar dejara de borrar la deuda, los 174 estudiantes aparecerían
  debiendo la matrícula de 2026. Idea planteada: "desactivar" deja de
  cobrar desde ese día, lo ya vencido se conserva, y una acción aparte y
  explícita de "anular deuda" sirve para casos como esa matrícula.
  Precaución operativa mientras tanto: no desactivar un concepto que
  todavía tenga deudas pendientes.
- Fase 3, paso 3.5 (encontrada el 2026-10-02): el punto 2 de la fase 3 pide
  que el boletín de un año cerrado oculte las materias de
  `anios_lectivos_materias_ocultas`, pero esa tabla se crea en la fase 6 y
  hoy no existe (búsqueda en todo el repo). Propuesto: en la fase 3 el
  boletín queda como hoy para cualquier año, y la parte de años cerrados va
  en la fase 6 junto con la tabla. Antes de la fase 6 no puede existir un
  año cerrado (cerrar es parte de activar), así que no queda ningún caso sin
  cubrir, y la fase 3 no necesita migración. La otra opción es crear la
  tabla en la fase 3, con una migración que no se usaría hasta la fase 6.
  **Sin respuesta del usuario.**
- Antes de la fase 5 (encontrada el 2026-10-02): `POST /cursos` y `POST
  /tipos-pagos` siempre crean en el año activo. La fase 4 dice que el admin
  prepara 2027 desde las pantallas existentes, pero ningún documento dice
  cómo se crea un curso o un concepto **nuevo** (que no venga de la copia)
  en el año en preparación. ¿Se agrega `anio_lectivo_id` opcional a esas dos
  rutas, y en qué fase? No bloquea los pasos 3.1 a 3.4. **Sin respuesta del
  usuario.**
- Antes de la fase 4 (frontend): en las pantallas que no dependen del año,
  ¿el selector se esconde o se muestra desactivado?
- Antes de la fase 6: ¿un estudiante del último grado que termina se marca
  "no continúa" (retirado) o hace falta un estado distinto como "egresado"?
  Dato encontrado el 2026-10-01, para cuando se decida: el estado
  `egresado` ya existe (`ESTADOS_ESTUDIANTE` en
  `app/controllers/estudiante_controller.py`, y el filtro
  `GET /estudiantes?estado=egresado`).

## Entrega para el siguiente chat

Estado al 2026-10-02. Si `git status` o el historial de git dicen otra
cosa, gana lo que se pueda verificar.

- **Hecho:** fase 0 y **fase 1 completas**. Migración A (2026-09-30) y
  migración B (2026-10-01, commit `47c61c2`) aplicadas en producción en
  `tenant_colegio_1` y `tenant_2005`; el código que escribe el año
  (`df53299`) está desplegado en Render (`67b2d4b`, Live); esquema base
  regenerado tras cada una. Detalle y verificación de cada paso en los
  "Avance" de las fases 0 y 1.
- **Fase 2, código completo:** la pregunta de los conceptos desactivados
  quedó respondida (se deja como está y se corrige después, aparte). Los
  cuatro pasos del plan están escritos y probados, en los commits
  `b2362f1`, `34712dd`, `b5f4099` y `f03b032`, todavía sin subir al
  2026-10-02. Ver los "Avance" de cada uno.
- **Fase 3, iniciada el 2026-10-02** con la autorización del usuario (y
  sabiendo que la fase 2 sigue sin subir): inventario confirmado con `grep`
  y plan en siete pasos, 3.1 a 3.7. Ver "Inventario confirmado" y "Plan por
  pasos" en la fase 3. El inventario encontró seis cosas que no estaban en
  la lista; la más importante, los choques de horario del profesor, que sin
  filtro por año bloquearían la carga académica de 2027. Paso 3.1 en el
  commit `fea2e83` (`GET /anios-lectivos` y `resolver_anio_pedido`); paso
  3.2 en `43764f2` (lo que ve el profesor, los listados del admin y los
  choques de horario, por año); paso 3.3 en `da4da87` (cursos, conceptos,
  precios por curso, listas de seguimiento y reporte general, por año).
  **Paso 3.4 escrito y probado, sin commit** (lista de estudiantes, cartera
  y estado de cuenta por curso, por año; decisiones 18 y 19; ver su
  "Avance").
- **Hecho aparte, la noche del 2026-09-30:** el arreglo de la hora
  (`2e77634` en este repo, `033c042` en el frontend). Cobros, cartera y
  alta de colegios usan la fecha de Colombia (`app/core/fechas.py`), y el
  frontend propone fechas de Colombia (`src/utils/fechaColombia.js`). Ver
  el hallazgo correspondiente y `docs/CAMBIOS_BACKEND.md`.
- **Pendiente del usuario:**
  - Pasos 2.1 a 2.4: revisarlos en local (Cartera vencida, la pantalla de
    Pagos y el detalle de un estudiante deben mostrar los mismos números
    que producción) y después el push. Las consultas
    nuevas solo se probaron con bases simuladas, y esa revisión es la que
    las corre contra la base real (solo lectura). No registrar pagos en
    local: escribe en la base real; para eso, una rama de Neon. El push
    despliega; no cambia nada visible mientras haya un solo año.
  - Borrar la rama `prueba-anio-lectivo-b` de Neon, si no se borró sola.
  - Si no se hizo todavía, **rotar la contraseña** de `neondb_owner` (ver
    el punto siguiente).
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
  No pedirle al usuario que pegue cadenas de conexión. El `.env` debe
  quedar en el endpoint `-pooler`: así `apply_migration.py` se niega a
  correr si falta `$env:DATABASE_URL`. Antes de probar la app contra una
  rama, detener el backend local que esté corriendo; si no, el frontend
  sigue hablando con el que apunta a producción.
- **Siguiente acción exacta:** que el usuario revise y haga el commit del
  paso 3.4. Después, **paso 3.5** (boletín, reporte parcial y puesto desde la
  matrícula del año pedido; observador del admin; detalle del estudiante,
  hallazgo 3; planes de clase del admin, hallazgo 5), solo con su visto
  bueno. **Antes de empezarlo, hacerle al usuario la pregunta abierta de las
  materias ocultas** (ver "Preguntas abiertas"): define si el 3.5 lleva una
  migración o no. Las preguntas abiertas se le
  hacen al usuario justo antes del paso que las necesita (lo pidió así el
  2026-10-02): la de materias ocultas, antes del 3.5; la de crear en el año
  en preparación, antes de la fase 5. La fase 3 tiene que estar en
  producción **antes de crear el primer curso de 2027** (fase 5, meta:
  principios de noviembre). Sigue siendo recomendable subir la fase 2
  antes.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_ANIO_LECTIVO.md`.
