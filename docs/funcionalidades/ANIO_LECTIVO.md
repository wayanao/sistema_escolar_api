# Funcionalidad: Año lectivo — Backend

## Control

- Estado: **Fase 5 completa y confirmada; fase 6 iniciada con autorización
  explícita del usuario y paso 6.1 terminado el 2026-10-08: migración probada
  en una rama de Neon, esquema base regenerado desde allí, commit `6c6aabb` y
  migración aplicada en los dos tenants de producción. Paso 6.2 autorizado y
  dividido en 6.2a (vista previa, commit `5726cf4`) y 6.2b (marcar la salida,
  commit `2aaee65`). Paso 6.3 autorizado y dividido en 6.3a (activar, commit
  `89b83cd`) y 6.3b (boletín de un año cerrado con su foto de materias, commit
  `5cc4f61`). Ensayo completo de activación en una rama de Neon el mismo día:
  todo correcto (ver "Ensayo de activación en una rama de Neon" en la fase
  6). Paso 6.4 autorizado el 2026-10-09 y dividido en 6.4a (reabrir y volver
  a cerrar, commit `0d6d202`) y 6.4b (listas de seguimiento por matrícula,
  commit `f0e0ca6`); el 6.4c queda para después por decisión del usuario.
  Fase 6 del frontend autorizada el mismo día, pasos 6.5 a 6.10; el 6.5
  (backend: la marca de salida en los candidatos) quedó en `a3f7086`, el
  6.6 (frontend: marcar en la promoción) en `5892602`, el 6.7 (frontend:
  sección "Activar") en `f6a035e`, el 6.8 (frontend: reabrir y volver a
  cerrar) en `5f69b77`, el 6.9 (frontend: aviso de año cerrado en Tipos de
  pago) en `cf00e3d` y el 6.10 (frontend: Certificados con todos los
  estados) en `b7184f8`. Con él, la fase 6 queda completa en los dos repos,
  salvo el 6.4c, aplazado. Al 2026-10-10 los dos repos estaban subidos a
  GitHub (`origin/main` en `0517c41` y `b7184f8`). Fase 7 iniciada el
  2026-10-10 con autorización explícita del usuario: paso 7.1 (backend: traer
  el planeador del año pasado) en `16c9052` y paso 7.2 (backend: los planes de
  clase del año pasado) en `c5dd384`. Con él, el backend de la fase 7 quedó
  completo. Paso 7.3 (frontend: el botón del planeador) en `df2afe3` y paso
  7.4 (frontend: usar un plan del año pasado) en `4e71c2b`. Con él, la fase 7
  queda completa en código en los dos repos; falta su revisión con un profesor
  de prueba en el ensayo. El 2026-10-12, ajustes pedidos por el usuario (ver
  "Ajustes pedidos por el usuario el 2026-10-12" al final de la fase 5): dos
  en el frontend y la ruta de solo lectura `GET
  /estudiantes/{id}/valores-pago` aquí, todos sin commit.** El paso 5.10 quedó en
  `82675ba`; el ajuste posterior de navegación del frontend, en `365d083`. El
  paso 5.9 quedó en `0689b7d` y su registro en este repo en
  `53da8f0`. El
  paso 5.6 quedó en `102ec77`, el 5.5 en `144feb1`, el 5.4 en `cffdfd7` y el
  5.3 en `653703c`; el 5.8 del frontend quedó en `817c47e` y su registro en
  este repo en `d3cdfd3`. El commit `a6f3cc0`
  quedó `Live` en Render; el usuario probó primero la migración en una rama de
  Neon, regeneró el esquema base y después la aplicó y verificó en los dos
  tenants de producción. El paso 5.3 no creó 2027 ni accedió a ninguna base
  real. Los pasos 5.4, 5.5 y 5.6 tampoco accedieron a una base real ni crearon
  2027. La fase 6 se inició el 2026-10-08, sin ejecutar migraciones ni acceder
  a bases reales. La
  matrícula del año activo ya es la fuente del curso vigente y solo
  `sincronizar_curso_vigente` escribe `estudiantes.curso_id`. La
  fase 4 (frontend) quedó completa y fue confirmada en los commits
  `8eac0ce` del frontend y `ce8d7a7` de documentación en este repo. Se inició
  el 2026-10-03;
  inventario y
  plan por pasos (commit `dbb0e48` del frontend), paso 4.1 (la base del
  selector, `4b14347`), paso 4.2 (Administración y horarios por año,
  `78c48f7`), paso 4.3 (Tipos de pago y Cartera vencida por año, `0798f21`),
  paso 4.4 (Estudiantes por año, `c7f0622`), paso 4.5 (Boletines y
  certificados por año, `2140fae`), paso 4.6 (Listas de seguimiento y
  bandeja de planes por año, `72be3da`) y paso 4.7 (diálogo al renombrar
  materias, `8eac0ce`); ver
  `frontend-react/docs/funcionalidades/ANIO_LECTIVO.md`. En este repo no
  tiene trabajo. **Fase 3 terminada el 2026-10-02 y subida a
  producción por el usuario el 2026-10-03** (`origin/main` en `9edbe5d`):
  pasos 3.1 a 3.5b en los commits `fea2e83`, `43764f2`, `da4da87`,
  `c9554af`, `eb835e3` y `8716fc5` (todas las lecturas quedan por año); 3.6
  (aviso al renombrar una materia) en `0110359`; 3.7 (guardia de
  escritura): medición `50d9f53`, 3.7a (rutas del profesor) `fcb18ef` y
  3.7b (rutas de solo admin) `9edbe5d`.
  **Fase 2 con el código completo el
  2026-10-01, subida a GitHub.**
  Pasos 2.1 (las cuotas se cuentan en el año del concepto), 2.2 (cada año
  cuenta solo sus pagos), 2.3 (pagar en otro año) y 2.4 (deuda de años
  anteriores) en los commits `b2362f1`, `34712dd`, `b5f4099` y `f03b032`.
  Al 2026-10-02 la copia local de GitHub (`origin/main`) ya llega a
  `f03b032`; que Render lo haya desplegado no se ve desde el repo. Fase 1
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
- Última actualización: 2026-10-12.

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
cuatro commits siguen sin subir (`git status`: `ahead 4`). *Actualizado más
tarde el 2026-10-02:* ya están en GitHub (`origin/main` en `f03b032`, visto
en la copia local); el despliegue en Render lo confirma el usuario.

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
  6. Para la fase 5, no la 3 (resuelto en el paso 5.6): los valores especiales por estudiante
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
  (hallazgo 5). *Partido en dos al hacerlo (2026-10-02), para revisarlo
  mejor:* **3.5a** boletín, reporte parcial y puesto; **3.5b** observador,
  detalle del estudiante y planes de clase del admin.
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
- Commit `c9554af` (hecho por el usuario el 2026-10-02).

**Avance del 2026-10-02 — paso 3.5a, boletín, reporte parcial y puesto por
año (sin desplegar):**

- Antes de empezar se le hizo al usuario la pregunta de las materias
  ocultas: la regla de años cerrados va en la fase 6 (ver "Preguntas
  abiertas"). Al revisar el código, el 3.5 resultó grande y se partió en dos
  (3.5a y 3.5b).
- Hallazgo al revisar: el **puesto en el curso** promediaba todas las
  definitivas del estudiante en el periodo, de cualquier año. Con 2027
  activo, el periodo 1 de 2027 se habría mezclado con el periodo 1 de 2026.
  Se corrige también para el año activo.
- Código:
  - `app/services/anio_lectivo.py`: `anio_distinto_del_activo(cursor,
    anio_lectivo_id)` (sin año o con el activo, `None`: el camino de
    siempre; con otro, su id; valida que exista) y
    `AnioLectivoInexistenteError`, subclase de `ValueError` (quien ya
    atrapaba `ValueError` sigue igual). La lista de estudiantes del 3.4 usa
    ahora esta misma regla en vez de su copia.
  - `leer_anio_lectivo` devuelve siempre una tupla, también con un cursor de
    diccionarios (el del boletín).
  - `app/repositories/boletin_repository.py`: materias, datos del estudiante
    (boletín y reporte parcial) y planilla vigente reciben el año, con
    `_curso_del_estudiante`: sin año, `e.curso_id`, y el texto que recibe
    PostgreSQL es **idéntico al del commit anterior** (comparado letra por
    letra, con sus parámetros); con año, el curso de su matrícula de ese
    año. El puesto suma `c.anio_lectivo_id = <año que se mira>` (el activo
    sin año) y, con año, los compañeros son los matriculados en el mismo
    curso ese año; sin año, los parámetros son los mismos de antes.
  - `boletin_controller.py` y `routes/boletines.py`: `?anio_lectivo_id=` en
    `/boletines/admin/generar/...` y `/admin/reporte-parcial/...`. La ruta
    atrapa `AnioLectivoInexistenteError` por su nombre → 404; cualquier otro
    `ValueError` sigue saliendo como 500 sin su texto. El parámetro va
    después del usuario en la firma, para que quien llama a la ruta por
    posición no cambie.
- Consultas: sin año, las mismas (boletín 4 con materias, reporte parcial
  2); con año, una más para validarlo.
- Pruebas:
  - `tests/test_anio_lectivo_lecturas.py`, 24 nuevas: las cuatro lecturas
    sin año (curso actual, sin matrículas, parámetros de siempre) y con año
    (curso de la matrícula, el año primero); **el puesto con dos años**, con
    una base que solo separa años si la consulta trae el filtro: con 2027
    activo Ana es primera (4,5 frente a 4,0; mezclando sería segunda), y en
    2026 es segunda; el controlador sin año, con el id del activo, con 2026 y
    con un año inexistente; y las rutas (pasan el año, 422, 404, y un
    `ValueError` cualquiera sigue en 500).
  - Ajustadas a propósito: en `test_boletin_caracterizacion.py`, el contador
    de consultas reconoce ahora las cinco que llevan un hueco para el curso
    (siguen siendo 11 y 12; las de materias inactivas siguen siendo 2), y dos
    dobles de ruta reciben el año; en `test_boletines_reporte_parcial.py`,
    dos dobles más.
  - Once versiones dañadas del código las hacen fallar, entre ellas quitar el
    filtro de año del puesto.
- Documentación: `docs/API_ENDPOINTS.md` (Boletines) y
  `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1687 pasan, 0 fallan** (antes
  1663); ruff y `pip check` limpios; `git diff --check` limpio.
- Efecto al desplegar: ninguno visible mientras haya un solo año. Revisión
  en local recomendada (solo lectura): generar el boletín de un estudiante
  (comprobar el puesto) y un certificado, iguales que en producción.
- Commit `eb835e3` (hecho por el usuario el 2026-10-02).

**Avance del 2026-10-02 — paso 3.5b, observador, expediente y planes del
admin por año (sin desplegar). Con él, todas las lecturas de la fase 3
(punto 2) quedan por año:**

- Código:
  - `anio_distinto_del_activo(cursor, anio_lectivo_id, usuario=None)`: con
    el usuario aplica además la regla del profesor (`resolver_anio_pedido`,
    403 si pide otro año). Primer uso: el observador.
  - Observador (`observador_repository.leer_bitacora`, `routes/observador.py`):
    las anotaciones son las del año activo, con el filtro en el `ON` como el
    del periodo (no esconde al estudiante sin anotaciones); con otro año, las
    de ese año y el `nivel` del curso de su matrícula. Sin año, los
    parámetros son los de siempre. Admin: cualquier año; profesor: solo el
    activo (403 con el mensaje del servicio); año inexistente: 404. El año va
    al final de la firma de la ruta, porque las pruebas la llaman por
    posición.
  - Expediente (`estudiantes_repository`, `estudiante_controller`, `GET
    /estudiantes/{id}/detalles`): notas, faltas y observaciones filtradas por
    el año del curso de cada clase, y la deuda con `con_anio`. El año se
    valida antes de las secciones: un año inexistente es 404, no una sección
    "que no se pudo cargar". Los productos de inventario no cambian.
  - **Faltas sin clase:** `asistencia.asignacion_id` admite nulos (esquema
    base) y hoy esas filas se cuentan en el expediente. En el año activo se
    siguen contando (`asignacion_id IS NULL OR ...`), así que nada cambia hoy
    tenga los datos que tenga; en otro año no, porque no se sabe de qué año
    son. Pendiente medir si existen (consulta abajo); si hay, después de
    activar 2027 se sumarían a las faltas de 2027.
  - Planes del admin (`plan_de_clases_repository.listar_planes_admin`, su
    ruta): por año, con `condicion_anio`. No valida que el año exista, porque
    el repositorio abre su propia conexión y validarlo costaría otra: un año
    inexistente da la lista vacía.
- Consultas: sin año, las mismas (observador 2 con el permiso; expediente 4;
  planes 2). Con año, una más para validarlo, salvo en planes.
- Pruebas:
  - `tests/test_anio_lectivo_lecturas.py`, 18 nuevas: la bitácora con dos
    años (sin año, la anotación de 2027; con 2026, la de 2026 y el curso de
    su matrícula); el profesor ve solo el activo y recibe 403 al pedir otro
    sin leer nada; las faltas con una de 2026, una de 2027 y una sin clase
    (año activo: 2; 2026: 1); notas y observaciones con y sin año; el
    expediente pide todo en el año (menos el inventario) y rechaza un año
    inexistente antes de leer; los planes con y sin año; las rutas.
  - Ajustadas a propósito: el contador de consultas de
    `test_observaciones_caracterizacion.py` (como el del boletín); la prueba
    de `test_observador_lectura.py` que partía la consulta en su primer
    `WHERE` (la subconsulta del año activo trae uno propio; ahora parte en el
    del estudiante); el total de líneas del dominio de planes (1382 → 1395)
    en `test_plan_de_clases_caracterizacion.py`; el doble de la ruta de
    planes en `test_plan_de_clases_routes.py`.
  - Catorce versiones dañadas del código las hacen fallar.
- Documentación: `docs/API_ENDPOINTS.md` (Estudiantes, Observador nueva,
  Plan de clases), `docs/ROLES_PERMISOS_BACKEND.md`,
  `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md` (invariante 5, precisado)
  y `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1705 pasan, 0 fallan** (antes
  1687); ruff y `pip check` limpios; `git diff --check` limpio.
- Comprobación pendiente del usuario (solo lectura, en el SQL Editor de Neon
  con `production`): cuántas faltas no tienen clase.

  ```sql
  SELECT 'faltas sin clase' AS dato, COUNT(*) FROM tenant_2005.asistencia WHERE asignacion_id IS NULL
  UNION ALL SELECT 'faltas en total', COUNT(*) FROM tenant_2005.asistencia;
  ```

  Si da 0, el caso no existe y no hay nada más que hacer. Si no, decidir
  antes de activar 2027 (fase 6) a qué año pertenecen.
- Efecto al desplegar: ninguno visible mientras haya un solo año. Revisión
  en local recomendada (solo lectura): la bitácora de un estudiante con un
  profesor y con el admin, el detalle de un estudiante y la bandeja de
  planes del admin, iguales que en producción.
- Commit `8716fc5` (hecho por el usuario el 2026-10-02).

**Avance del 2026-10-02 — paso 3.6, aviso al renombrar una materia (sin
desplegar):**

- Aprobado por el usuario el 2026-10-02 ("si"), después de explicarle el
  cambio, que con un solo año nunca avisa y el costo de una consulta más.
  Ninguna pregunta abierta afectaba este paso.
- Caracterización primero: editar una materia no tenía ninguna prueba.
  `tests/test_materias_caracterizacion.py` (12) fija el nombre que se
  guarda, los errores con su código HTTP (409 repetido, 422 vacío, 404 no
  encontrada), que un profesor recibe 403 y las dos consultas de hoy con su
  texto y parámetros. Pasó entera contra el código anterior.
- Código:
  - `app/repositories/anios_lectivos_repository.py`:
    `leer_nombre_y_anios_de_materia`, una consulta con el nombre guardado y
    los años en que se dicta la materia (por sus clases → curso → año).
    Cuenta también las clases inactivas: sus notas siguen ahí, y ante la
    duda es mejor avisar de más.
  - `app/services/anio_lectivo.py`: `anios_a_avisar_al_renombrar` (la regla
    del punto 3: más de un año, o uno `cerrado` o `reabierto`; se nombran
    los años que no son el activo) y `mensaje_materia_usada_en_otro_anio`
    (el texto del punto 3; con varios años, "2025 y 2026").
  - `app/controllers/materia_controller.py`: `MateriaUsadaEnOtroAnioError`
    (no es `ValueError`, para no salir como 422). Al editar, después de la
    revisión de nombre repetido (confirmar no arregla un repetido), si la
    petición no trae `confirmar_cambio_nombre: true` se mira si cambia el
    texto guardado tal cual (es lo que imprime el boletín) y en qué años se
    usa. Con la confirmación no se hace esa consulta: guarda como hoy.
  - `app/routes/materias.py`: el aviso sale como 409 con `detail =
    {"codigo": "materia_usada_en_otro_anio", "mensaje": ...}`. El 409 de
    nombre repetido sigue con `detail` de texto, así que el frontend los
    distingue.
- Decisiones de detalle tomadas al escribirlo, dentro de la decisión 12:
  solo el booleano `true` confirma (no `"true"` ni `1`); cambiar solo
  mayúsculas o espacios de un nombre guardado también avisa, porque cambia
  lo impreso; un solo año en preparación, sin el activo, no avisa (no es
  "más de un año" ni un año pasado).
- Consultas: editar una materia, 3 en vez de 2 (aceptado por el usuario);
  con la confirmación, las 2 de siempre. Crear una materia no cambió.
- Pruebas:
  - `tests/test_anio_lectivo_renombrar_materia.py`, 30 nuevas: la regla con
    ocho combinaciones de años, el mensaje con uno, dos y tres años, la
    consulta, el controlador con 2026 cerrado y 2027 activo (avisa sin
    guardar y con `rollback`; con la confirmación guarda sin la consulta;
    solo `true` confirma; sin cambio de nombre no avisa; el repetido va
    primero; con un solo año guarda) y la ruta por HTTP (409 con el código,
    la confirmación llega al controlador, y el flujo completo: aviso,
    confirmación, guardado).
  - Ajustada a propósito, solo la caracterización escrita en este mismo
    paso: su doble conoce la consulta nueva (responde un solo año, como
    hoy) y el conteo pasa de 2 a 3. Antes del ajuste fallaban exactamente
    las 5 pruebas que pasan por esa consulta, y solo por ella. Ninguna otra
    prueba del repo cambió.
  - Trece versiones dañadas del código hacen fallar alguna prueba: quitar
    la confirmación, aceptar `1`, ignorar los años cerrados, ignorar "más
    de un año", nombrar también el activo, avisar sin cambio de nombre,
    comparar el nombre normalizado, responder el aviso como texto, no
    atraparlo en la ruta, no hacer `rollback`, filtrar clases inactivas, no
    quitar el año nulo de una materia sin clases y avisar antes del
    repetido.
- Documentación: `docs/API_ENDPOINTS.md` (Materias) y
  `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1747 pasan, 0 fallan** (antes
  1705); ruff y `pip check` limpios; `git diff --check` limpio. Corrido con
  un `DATABASE_URL` inventado, como en CI.
- Para el frontend (su fase 4, punto 5): el código, el mensaje y el campo de
  confirmación de arriba. Se anota en su documento al cerrar la fase 3, con
  el resto del contrato, como se dijo en el 3.2. Hasta que la pantalla de
  Materias tenga su diálogo, mostraría este aviso como `[object Object]`
  (`obtenerMensajeErrorMateria` espera texto). No puede pasar antes de la
  fase 5, porque hace falta un segundo año, y la fase 4 va antes.
- Efecto al desplegar: ninguno visible mientras haya un solo año. Revisión
  en local: no hace falta. Editar una materia en local escribe en la base
  real, y lo que cambia solo se ve con dos años.
- Commit `0110359` (hecho por el usuario el 2026-10-02).

**Medición previa del paso 3.7, la guardia de escritura (2026-10-02; sin
cambios de código):**

- Aprobado empezar el paso por el usuario ("continúa"). Como pide el plan,
  primero se mide y el usuario decide el costo.
- Cómo se midió: un banco de medición fuera del repo pasó cada ruta por la
  aplicación real (ASGI) con una base simulada que cuenta conexiones,
  consultas e idas a la base. El usuario de la sesión se dobló, así que las
  cifras **no** incluyen la autenticación (~346 ms, igual con o sin
  guardia). Idas = consultas + BEGIN, preparación y cierre de cada conexión.
  Camino feliz de cada ruta.
- Resultado, hoy (conexiones / consultas / idas):

  | Ruta | Profesor | Admin |
  |---|---|---|
  | `POST /planilla/nota` | 2 / 6 / 12 | 1 / 5 / 8 |
  | `DELETE /planilla/tipo` | 2 / 3 / 9 | 1 / 2 / 5 |
  | `POST /asistencia` (1 estudiante) | 3 / 6 / 15 | 2 / 5 / 11 |
  | `POST /boletines/guardar` | 3 / 7 / 16 | 2 / 6 / 12 |
  | `POST /observaciones` | 3 / 5 / 14 | 2 / 4 / 10 |
  | `PUT /planeador-anual/...` | 2 / 3 / 9 | 1 / 2 / 5 |
  | `POST /plan-de-clases` | 2 / 3 / 9 | 1 / 2 / 5 |
  | `DELETE /plan-de-clases/{id}/imagen` | 2 / 3 / 9 | 1 / 2 / 5 |
  | `PATCH .../observaciones/{id}/vista` | 2 / 2 / 8 | — |
  | `PUT /observador/{id}` | 1 / 1 / 4 | — |
  | `POST /notas` | 5 / 6 / 21 | 4 / 5 / 17 |

  Solo admin: asignaciones `POST` 1/12/15 y `PUT` 1/11/14 (las pruebas del
  repo fijan 13 y 11 consultas: el banco tomó un camino un poco más corto al
  crear), los dos `DELETE` 1/2/5, orden del boletín 1/6/11; cursos `PUT`
  1/2/5 y estado 1/1/4; listas: crear columna 1/3/6, en todos los cursos
  1/2/5, borrar columna 1/1/4, marcas 1/3/6; planes del admin: revisión
  1/3/6, observación 1/4/7, borrar imagen 1/2/5; conceptos: editar 1/2/5,
  configuración 2/4/10, precios 1/4/7, quitar precio 1/1/4; valores por
  estudiante: guardar 1/8/11, borrar 1/2/5.
- Tres rutas de la lista no necesitan consulta: `POST /observador` (la
  anotación nueva siempre nace en el año activo, con `ANIO_ACTIVO_ID_SQL`, y
  el activo es editable para todos), `DELETE /tipos-pagos/{id}` (nunca
  escribe: responde 405 siempre) y `POST /listas-seguimiento/columnas-en-todos-los-cursos`
  (sin año usa el activo; con año ya lee su estado al validarlo).
- Diseño propuesto: la guardia corre **dentro de una conexión que el
  guardado ya abre**, nunca en una nueva (cada conexión nueva son ~3 idas
  más, ~180 ms, y presiona el pool de 10). Costo: **+1 consulta (~60 ms) en
  cada guardado de las otras 30 rutas**; ninguna conexión nueva. Ejemplo,
  lo que más usan los profesores: guardar una nota en la planilla pasa de 12
  a 13 idas (~0,72 s a ~0,78 s, sin contar la autenticación).
- Descartado por ahora: unir la guardia a la consulta de permisos del
  profesor (`permissions.py`), que la dejaría en 0 para él. Es la capa de
  permisos, zona sensible, y ahorra ~60 ms; se puede hacer después, aparte.
- Hallazgo, fuera de alcance: `POST /notas` abre 5 conexiones (21 idas,
  ~1,3 s), pero ninguna pantalla del frontend la usa (búsqueda en
  `frontend-react/src`). Deuda anotada, sin prisa.
- **Aceptado por el usuario el 2026-10-02** ("sigue", en respuesta a la
  pregunta del costo). Con un solo año la guardia nunca bloquea; solo suma
  ese tiempo. Commit `50d9f53` (esta medición, solo documento).

**Avance del 2026-10-02 — paso 3.7a, la guardia en las rutas que usa el
profesor (sin desplegar):**

- Caracterización primero: `tests/test_anio_lectivo_guardia_conteos.py`
  convierte el banco de medición en prueba del repo. Fija, para cada ruta y
  rol, las conexiones y consultas de la tabla de arriba; se escribió y pasó
  (21 de 21) contra el código anterior.
- Código:
  - `app/services/anio_lectivo.py`: `exigir_anio_editable` (la tabla de "La
    guardia de escritura"; un estado desconocido cuenta como cerrado; sin
    fila no hace nada y el guardado responde como siempre),
    `exigir_asignacion_editable`, `exigir_plan_editable`,
    `exigir_anotacion_editable` y `AnioLectivoNoEditableError`. Es una
    `HTTPException`, así llega a la respuesta sin que cada ruta la traduzca.
  - `app/repositories/anios_lectivos_repository.py`:
    `leer_anio_de_asignacion` (clase → curso → año), `leer_anio_de_plan` y
    `leer_anio_de_anotacion` (la anotación guarda su año). Una consulta cada
    una, por id.
  - La guardia es **lo primero dentro de la transacción** que ya abre cada
    guardado: notas, planilla (nota y borrar columna), asistencia, boletín,
    observaciones, planeador, crear plan, borrar evidencia, marcar vista y
    editar anotación (en la ruta del observador, que tiene su propio
    cursor). Si rechaza, no se escribe nada y la transacción se revierte.
  - Quién guarda viaja como argumento obligatorio por nombre (`usuario=`),
    de la ruta a la transacción; en el plan de clases, por controlador,
    servicio y repositorio. Obligatorio a propósito: nadie puede olvidarlo.
  - Boletín y planeador reenvían `HTTPException` antes de su `except
    Exception`; sin eso, el 409 saldría como 500.
  - `DELETE /admin/plan-de-clases/{id}/imagen` comparte el guardado con la
    del profesor, así que entró aquí. La protección de admin pasó del
    decorador a un parámetro, como en sus rutas hermanas del admin: la misma
    dependencia, una sola vez.
- Consultas, medidas: cada guardado de estas 12 rutas, **+1 consulta y 0
  conexiones**, para profesor y admin. Ejemplo, la nota de la planilla: de
  12 a 13 idas.
- Pruebas:
  - `tests/test_anio_lectivo_guardia.py`, 126 nuevas: la regla (diez
    combinaciones de estado y rol), las tres lecturas (con cursor de tuplas
    y de diccionarios), y por HTTP en cada ruta y rol: año cerrado → 409,
    nada escrito y ningún `commit`; preparación y reabierto → 403 al
    profesor y el admin guarda; activo → como siempre; el id que mira la
    guardia (clase 9, plan 20, anotación 15); y que una evidencia subida
    antes de un rechazo se borra del almacenamiento.
  - Ajustadas a propósito, **111 pruebas en 15 archivos** que fijan cómo
    se llaman estos guardados y qué consultas hacen. Un solo criterio: si el
    archivo dobla los ayudantes del guardado (resolutores), dobla también la
    guardia y anota a quién se le pidió; si cuenta las consultas reales, la
    guardia corre de verdad, se cuenta (+1) y se corren una posición los
    índices. Ninguna dejó de comprobar lo que comprobaba. Además: el total
    de líneas del dominio de planes (1395 → 1413) y las veces que la ruta
    del boletín reenvía `HTTPException` (2 → 3).
  - Veintitrés versiones dañadas del código hacen fallar alguna prueba:
    quitar la guardia de cada una de las 11 escrituras, mirar el id
    equivocado (dos), dejar escribir al profesor en preparación o al admin
    en un año cerrado, aceptar un estado desconocido, responder 403 por
    cerrado, bloquear cuando no hay fila, el 409 convertido en 500 (boletín
    y planeador), la consulta sin unir el curso, sin cursor de diccionarios
    y la ruta del admin pasando otro usuario.
- Documentación: `docs/API_ENDPOINTS.md` ("Guardia de escritura"),
  `docs/ROLES_PERMISOS_BACKEND.md` y `docs/CAMBIOS_BACKEND.md`.
- Verificación: `scripts/verify.py` → **1894 pasan, 0 fallan** (antes
  1747); ruff y `pip check` limpios; `git diff --check` limpio.
- **Hallazgo para la fase 6** (no se toca ahora): asistencia, boletín y
  observaciones comprueban en la ruta, antes de la guardia, que el
  estudiante sea del curso de la clase, comparando con
  `estudiantes.curso_id` (el curso del año activo). Dos efectos: un
  profesor que guarda en un año que ya no es el activo recibe primero ese
  403 ("El estudiante no pertenece a esta asignación") y no el 409 con el
  año (no se escribe nada, igual); y **el admin no podrá corregir el
  boletín, la asistencia ni las observaciones de un año reabierto**, porque
  esa comprobación lo rechaza antes. La fase 6 (reabrir) tiene que hacer que
  esa comprobación mire la matrícula del año de la clase.
- Efecto al desplegar: ninguno visible mientras haya un solo año; un poco
  más de tiempo en cada guardado (~60 ms). Revisión en local: no hace falta
  y no conviene (guardar en local escribe en la base real).
- Siguiente: **paso 3.7b**, la guardia en las 19 rutas de solo admin
  (asignaciones 5, cursos 2, listas de seguimiento 4 —la de "todos los
  cursos" sin consulta extra—, revisión y observaciones de planes 2,
  conceptos 4 y valores por estudiante 2), con el mismo método.
- Commit `fcb18ef` (hecho por el usuario el 2026-10-02).

**Avance del 2026-10-02 — paso 3.7b, la guardia en las rutas de solo admin
(sin desplegar). Con él, la fase 3 queda completa:**

- Aprobado por el usuario el 2026-10-02 ("continúa"). Toca conceptos de
  pago y valores por estudiante (zona de dinero): solo se agrega la guardia;
  ningún cálculo ni consulta de cobro cambia.
- Caracterización primero: las 19 rutas entraron en
  `tests/test_anio_lectivo_guardia_conteos.py` con sus conexiones y
  consultas de la medición previa; pasaron (40 de 40) contra el código
  anterior.
- Código:
  - Regla: como estas rutas ya exigen admin en su router, la guardia aplica
    la regla del admin (`exigir_anio_editable_para_admin`: solo un año
    cerrado frena, con 409) y no hace falta pasar el usuario por las capas.
    Variantes por lo que se guarda: `exigir_cursos_editables_para_admin`,
    `exigir_asignacion_editable_para_admin`,
    `exigir_plan_editable_para_admin` y
    `exigir_concepto_editable_para_admin`. Si alguna de estas rutas se
    abriera algún día a profesores, tendría que pasar a la versión con
    usuario (anotado en el servicio).
  - Lecturas nuevas en el repositorio del año: `leer_anios_de_cursos` (uno o
    varios cursos en una consulta) y `leer_anio_de_concepto` (el concepto
    guarda su año, decisión 17).
  - Dónde va: lo primero de la transacción en crear clase, desactivar
    (por id y por profesor y curso), orden del boletín, estado del curso,
    listas (crear y borrar columna, marcas), revisión y observaciones de
    planes, y las seis escrituras de conceptos y valores. Editar curso: tras
    validar que el nombre no está vacío (no consulta), antes de la primera
    consulta. Editar clase: justo después de leerla, porque mira **el curso
    de antes y el nuevo** a la vez (no se puede sacar una clase de un año
    cerrado ni meterla en uno).
  - "Columna en todos los cursos" con `?anio_lectivo_id=`: la validación
    del año que ya hacía devuelve su estado, así que la guardia no cuesta
    consulta. Sin año, son los cursos del activo, siempre editable.
  - Conceptos y valores: sus funciones convierten cualquier error en "error
    interno" (500). Se agregó `AnioLectivoNoEditableError` a la lista de
    errores que se dejan pasar, para que el 409 llegue tal cual.
- Consultas, medidas: +1 y 0 conexiones en 18 rutas; +0 en "todos los
  cursos".
- Pruebas:
  - `tests/test_anio_lectivo_guardia.py`, 103 nuevas: la regla del admin
    (cuatro estados), las dos lecturas, y por HTTP en cada una de las 19
    rutas: año cerrado → 409, nada escrito y ningún `commit`; preparación y
    reabierto → el admin guarda; activo → como siempre; lo que mira cada
    guardia (curso 2, clase 9, plan 20, concepto 4; editar clase, los dos
    cursos en una consulta); y "todos los cursos" sin año no consulta la
    guardia.
  - Ajustadas a propósito, **64 pruebas en 10 archivos**, con el criterio
    del 3.7a (si el archivo dobla los ayudantes, se dobla la guardia; si
    cuenta consultas reales, la guardia corre y se cuenta). Además, el total
    de líneas del dominio de planes (1413 → 1421).
  - Treinta versiones dañadas del código hacen fallar alguna prueba: quitar
    la guardia de cada uno de los 19 sitios, el 409 convertido en "error
    interno" en cada una de las seis escrituras de dinero, editar clase
    mirando solo el curso nuevo, la regla del admin tratándolo como
    profesor, la consulta del concepto sin unir su año, la de cursos con un
    solo id y sin cursor de diccionarios.
- Documentación: `docs/API_ENDPOINTS.md` ("Guardia de escritura"),
  `docs/ROLES_PERMISOS_BACKEND.md` y `docs/CAMBIOS_BACKEND.md`; en el
  frontend, `docs/funcionalidades/ANIO_LECTIVO.md` con el contrato completo
  de la fase 3.
- Verificación: `scripts/verify.py` → **2016 pasan, 0 fallan** (antes
  1913); ruff y `pip check` limpios; `git diff --check` limpio.
- Hallazgo, se suma al del 3.7a para la fase 6: las marcas de las listas de
  seguimiento también validan a los estudiantes con `estudiantes.curso_id`
  (los del año activo). En un año reabierto, el admin no podría marcar a
  los estudiantes de ese año. Mismo arreglo: que mire la matrícula del año
  del curso.
- Efecto al desplegar: ninguno visible mientras haya un solo año; unos 60 ms
  más en cada guardado de estas pantallas del admin.
- Commit `9edbe5d` (hecho por el usuario el 2026-10-02).

**Con esto la fase 3 queda terminada (2026-10-02).** Se cumple su punto 5:
- Con el año activo, las respuestas son las de antes: lo fijan las
  caracterizaciones de cada paso, que siguieron pasando (las que se
  ajustaron lo fueron solo por consultas nuevas o por el año como
  parámetro, nunca por la respuesta).
- Con otro año, cada listado devuelve solo lo de ese año (pasos 3.1 a 3.5,
  con bases simuladas de dos años), y nadie escribe donde no debe (3.7).
- `verify.py` pasa.
- Falta, del usuario: revisarla en local y subirla. Tiene que estar en
  producción **antes de crear el primer curso de 2027** (fase 5).
  *Hecho el 2026-10-03:* el usuario la subió a producción (`origin/main` en
  `9edbe5d`, visto con `git fetch`); que Render la haya desplegado no se ve
  desde el repo.

### Fase 4 — Selector de año en el frontend

Ver `frontend-react/docs/funcionalidades/ANIO_LECTIVO.md`. En el backend no
hay trabajo nuevo: usa lo de la fase 3. Va antes de la fase 5 porque,
mientras se prepara 2027, el admin necesita las pantallas existentes
(Cursos, Tipos de pago, Estudiantes, Horarios) mirando 2027.

Iniciada el 2026-10-03, con la autorización del usuario: inventario y plan
por pasos (4.1 a 4.7) en ese documento. Su inventario dejó un hallazgo para
la fase 5 de este repo (ver "Ojo" en la fase 5).

Avance al 2026-10-03: pasos 4.1 y 4.2 con commit (`4b14347` y `78c48f7` del
frontend); paso 4.3 (Tipos de pago y Cartera vencida por año) escrito y
probado (commit `0798f21`, el mismo día). Usa sin cambios lo que este repo ya
sirve por año (`GET /tipos-pagos`, `/tipos-pagos/detallado`, `/cursos` y
`/cartera/mora` con su `/resumen`, todos con `?anio_lectivo_id=`). Mirando
otro año, la Cartera del frontend no ofrece "Cobrar": Pagos cobra siempre en
el año activo hasta que la fase 5 traiga el selector "Año del pago", que
usará el `anio_lectivo_id` que este repo ya acepta desde el paso 2.3.

Avance al 2026-10-05: paso 4.4 (Estudiantes por año: lista, ficha y
observador de la ficha) escrito y probado (commit `c7f0622`, el mismo día).
Usa sin cambios
`GET /estudiantes`, `/estudiantes/{id}/detalles`, `/estudiantes/{id}/deudas`
y `/observador/{id}`, con `?anio_lectivo_id=`. Mirando otro año, Estudiantes
queda en solo consulta en el frontend: así nadie le pone a un estudiante un
curso de otro año desde esa pantalla, que es el hallazgo de la fase 5 (ver
"Ojo" allí), todavía abierto en este repo.

Avance al 2026-10-05: paso 4.5 (Boletines y certificados por año) escrito y
probado (commit `2140fae`, el mismo día). Usa sin cambios `GET /cursos`, `GET /estudiantes`,
`/boletines/admin/generar/...` y `/boletines/admin/reporte-parcial/...` con
`?anio_lectivo_id=` (pasos 3.3 a 3.5a). Hallazgo, de antes de esta función:
esas dos pantallas piden `GET /estudiantes` sin `estado`, y este repo
responde entonces solo activos (su valor por defecto desde `6d4e75c`,
2026-06-03), así que no listan retirados ni egresados. Para imprimir 2026
después de activar 2027 (fase 6) hace falta que los listen; el arreglo
propuesto es del frontend (que Certificados pida `?estado=todos`), sin
cambios aquí. Ver la pregunta abierta en el documento del frontend.

Avance al 2026-10-05: paso 4.6 (Listas de seguimiento y bandeja de planes
por año) escrito y probado, commit `72be3da`. Usa sin cambios `GET /cursos`,
`GET /admin/plan-de-clases` y la escritura
`POST /listas-seguimiento/columnas-en-todos-los-cursos`, con
`?anio_lectivo_id=` (pasos 3.3 y 3.5b). Hallazgo de este repo, para la fase
6: `leer_estudiantes_del_curso` (`listas_seguimiento_repository.py`) toma
los estudiantes de un curso con `estudiantes.curso_id`, así que la lista de
un curso que no es del año activo sale sin estudiantes: los de 2027 en
preparación hasta activarlo, y los de 2026 después. Amplía el hallazgo del
paso 3.7b (las marcas validan con el mismo campo): la lectura también tiene
que ir por matrícula si se quiere consultar las listas de 2026.

Avance al 2026-10-05: paso 4.7 (diálogo al renombrar materias) escrito y
probado, sin commit. El frontend reconoce únicamente el `409` con código
`materia_usada_en_otro_anio` que este repo sirve desde el paso 3.6: muestra
el mensaje del backend y ofrece "Cambiar igual" (repite el `PUT` con
`confirmar_cambio_nombre: true`) o "Crear una materia nueva" (cambia el
formulario a creación sin guardar automáticamente). La petición normal de
editar conserva el mismo cuerpo. Verificación del frontend:
`pnpm run check:deploy`, 2210 pruebas en 341 archivos, lint y build limpios;
`git diff --check` limpio. Con él, la fase 4 tiene el código completo. En
este repo no cambió ningún endpoint ni lógica. Por la actualización de este
documento principal, `scripts/verify.py` pasó con 2016 pruebas, ruff y
`pip check` limpios, usando un `DATABASE_URL` ficticio.

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

**Inicio autorizado e inventario confirmado el 2026-10-05:**

- El usuario autorizó expresamente la fase 5 y aprobó las tres decisiones que
  la bloqueaban: `POST /cursos` y `POST /tipos-pagos` aceptarán
  `anio_lectivo_id` opcional; el impreso y el nombre del CSV de Cartera
  identificarán el año consultado; y el certificado de matrícula propondrá el
  año que se está mirando. Si el año se omite, las peticiones y respuestas del
  año activo conservan el contrato anterior.
- Ambos repos estaban en `main` y limpios al iniciar. El backend estaba en
  `ce8d7a7` y el frontend en `8eac0ce`, ambos `ahead 8` respecto de su remoto
  conocido. No se hizo `fetch`, push, despliegue ni acceso a producción.
- `POST /estudiantes` y `PUT /estudiantes/{id}` escriben hoy
  `estudiantes.curso_id` directamente y después copian ese valor a la
  matrícula activa. Antes de que pueda existir un curso de 2027 hay que
  invertirlo: la matrícula será la fuente y solo
  `sincronizar_curso_vigente` escribirá la copia del año activo. El camino
  actual sin año conservará su cuerpo y su respuesta.
- `POST /cursos` y `POST /tipos-pagos` fijan hoy el año activo dentro del SQL.
  Sus validaciones de nombre ya están limitadas por año. El cambio opcional
  puede conservar literalmente el camino actual cuando no se envía año y
  usar `exigir_anio_editable` cuando sí se envía.
- La copia necesita dos columnas aditivas todavía ausentes:
  `cursos.curso_origen_id` y `tipos_de_pagos.tipo_pago_origen_id`. La guía de
  migraciones exige escribir una migración incremental, probarla en una rama
  de Neon y regenerar después el esquema base; el asistente no aplicará la
  migración a ningún tenant ni se conectará a producción.
- La carga académica vive en filas de `asignaciones`: varias franjas del mismo
  profesor, curso y materia comparten `asignacion_academica_id`. La copia debe
  conservar profesor, materia, día, horas, estado y orden de boletín, y rehacer
  esa referencia entre las filas nuevas, nunca apuntar a la asignación de
  2026.
- Los pagos ya aceptan `anio_lectivo_id` desde la fase 2. Lo pendiente en el
  backend es probar el recorrido completo con año en preparación y hacer que
  los valores especiales consulten el curso de la matrícula de ese año, no
  siempre `estudiantes.curso_id`.

**Plan por pasos de la fase 5 (uno por vez):**

1. **5.1 — Blindar la matrícula y el curso vigente.** Caracterización primero;
   añadir `sincronizar_curso_vigente`, hacerla la única escritura de
   `estudiantes.curso_id`, mantener idéntico el alta/edición del año activo y
   rechazar en ese camino un curso que no sea del activo. La consulta de
   control debe seguir dando 0.
2. **5.2 — Migración de orígenes.** Pruebas de texto primero; agregar las dos
   columnas autorreferentes, sus claves foráneas e índices. El asistente deja
   el SQL listo, pero el usuario controla la prueba en una rama de Neon y la
   regeneración del esquema base, como exige `docs/MIGRACIONES.md`.
3. **5.3 — Crear el año y altas manuales en preparación.** `POST
   /anios-lectivos` crea exactamente `N+1` en `preparacion`; `POST /cursos` y
   `POST /tipos-pagos` aceptan el año opcional aprobado. Sin año ejecutan el
   camino anterior; con año, el servidor valida existencia y edición.
4. **5.4 — Copiar la configuración.** Endpoint transaccional para cursos y
   conceptos; los conceptos siempre se copian y las opciones controlan
   precios, carga académica y directores. Copia toda la configuración
   documentada, rehace referencias y devuelve conteos claros; un choque
   revierte todo e identifica el registro.
5. **5.5 — Matricular.** Consultar candidatos por curso, promover solo los
   estudiantes marcados, permitir alta de un estudiante directamente en el
   año en preparación y devolver los valores especiales copiados como
   “revisar”. El curso vigente no cambia mientras 2026 siga activo.
6. **5.6 — Resumen y recorrido financiero del backend.** Resumen de lo
   preparado, valores especiales por matrícula/año y prueba integral de una
   matrícula 2027 pagada en 2026. No se cambia el cálculo ya cerrado en la
   fase 2 salvo lo indispensable para ese recorrido.
7. **5.7 — Pantalla base del frontend.** Servicio, ruta protegida, menú y
   página `/admin/anios-lectivos` para crear y copiar; habilitar las altas
   manuales de cursos y conceptos en preparación enviando el año solo allí.
8. **5.8 — Matrículas y resumen en el frontend.** Promoción por curso,
   selección de estudiantes, aviso de valores especiales por revisar, alta
   de estudiante en 2027 y resumen sin botón de activar.
9. **5.9 — Pagos y deudas anteriores.** Selector propio “Año del pago”,
   activo por defecto; consultas y cuerpos llevan año solo al elegir otro.
   Mostrar `deuda_anios_anteriores` en Pagos, Cartera y la ficha del
   estudiante, sin mezclar ventas con otro año.
10. **5.10 — Año en documentos.** Incluir el año consultado en el estado de
    cartera y en el nombre del CSV, y proponerlo en el certificado de
    matrícula, tal como aprobó el usuario.

Cada paso termina con sus pruebas específicas, la verificación global del
repo tocado y `git diff --check`; se documenta y se detiene antes del
siguiente. Antes de cada cambio de dinero o migración se vuelve a explicar el
alcance en palabras simples.

**Avance del 2026-10-05 — paso 5.1 terminado, sin commit:**

- Se caracterizó primero el camino existente: 27 pruebas pasaron antes del
  cambio. Después se escribieron las pruebas del nuevo contrato y se comprobó
  que fallaban contra el código anterior por las funciones y protecciones que
  todavía no existían.
- `POST /estudiantes` y `PUT /estudiantes/{id}` conservan su cuerpo y su
  respuesta para el año activo. El alta o la edición guarda primero el curso
  en `matriculas`; luego `sincronizar_curso_vigente` copia desde la matrícula
  activa a `estudiantes.curso_id`, dentro de la misma transacción.
- El `INSERT` y el `UPDATE` de los datos globales del estudiante ya no escriben
  `curso_id`. Una búsqueda de todas las escrituras en `app/` confirma que
  `sincronizar_curso_vigente` es la única que actualiza esa columna.
- Si el curso no existe o no pertenece al año activo, el upsert no guarda
  nada, la API responde `409` y la transacción revierte también el alta o la
  edición global. Así la consulta de control no puede quedar descuadrada por
  este camino.
- No se cambió el esquema ni se creó una migración. Tampoco se consultó la
  base real: la consulta de control de producción no se ejecutó, respetando la
  prohibición de acceso. La dirección del SQL y sus pruebas garantizan que,
  partiendo de control 0, crear o editar conserva ese 0.
- Pruebas específicas: **36 pasaron** en
  `test_estudiantes_controlador.py`, `test_anio_lectivo_escrituras.py`,
  `test_anio_lectivo_matriculas.py` y
  `test_migracion_anios_lectivos_obligatorio.py`. Verificación global con
  `DATABASE_URL` ficticio: `scripts/verify.py` → **2025 pruebas pasan**, Ruff
  y `pip check` limpios. La primera ejecución aislada tuvo 30 errores de
  permisos al abrir la carpeta temporal de pytest; repetida fuera de esa
  restricción pasó completa. `git diff --check` quedó limpio.

**Resuelto en 5.1 — hallazgo del 2026-10-03:** crear o editar un estudiante ya
no puede dejar `estudiantes.curso_id` apuntando a un curso de otro año. El
frontend mantiene Estudiantes en solo consulta al mirar otro año, pero la
protección decisiva está ahora en el backend. El flujo distinto para crear un
estudiante directamente en un año en preparación corresponde al paso 5.5 y no
se adelantó aquí.

**Avance del 2026-10-06 — paso 5.2 terminado y en producción:**

- Antes del cambio pasaron **34 pruebas** de las migraciones de año lectivo y
  de la compuerta del esquema base.
- Se escribieron primero 7 pruebas en
  `tests/test_migracion_anios_lectivos_origenes.py`; las siete fallaron porque
  todavía no existía el archivo SQL.
- `migrations/20261006_anios_lectivos_origenes.sql` agrega únicamente
  `cursos.curso_origen_id` y
  `tipos_de_pagos.tipo_pago_origen_id`. Ambas admiten `NULL`, apuntan a la
  misma tabla mediante claves foráneas y tienen un índice de consulta.
- No hay relleno: todos los cursos y conceptos existentes conservan `NULL`
  porque son registros iniciales de 2026, no copias. Tampoco hay `INSERT`,
  `UPDATE`, `DELETE`, `DROP` ni borrado en cascada. El SQL es reejecutable si
  una ejecución manual quedara incompleta.
- Las 7 pruebas nuevas pasan; antes de regenerar, junto con las migraciones A y
  B eran **36 pruebas relacionadas** aprobadas. La compuerta del esquema base
  falló entonces por la única razón esperada: faltaba incorporar la migración.
- El usuario creó y eligió una rama de Neon con endpoint directo, distinto del
  host local documentado como producción. El primer `--dry-run` mostró
  `PENDIENTE` en `tenant_colegio_1` y `tenant_2005`; la aplicación terminó `OK`
  en ambos y el segundo `--dry-run` los mostró `OMITIDA (ya aplicada)`.
- El usuario regeneró
  `migrations/base/20260813_esquema_base_tenant.sql` desde
  `tenant_colegio_1`: 34 tablas, 1 función y 1 disparador. La revisión del diff
  confirmó solo lo esperado: cabecera de 41 migraciones, dos columnas, dos
  índices y dos claves foráneas.
- Verificación final: **41 pruebas específicas pasan** (migraciones A, B,
  orígenes y esquema base); `scripts/verify.py` → **2032 pruebas pasan**, Ruff
  y `pip check` limpios; `git diff --check` limpio.
- La migración y el esquema base regenerado quedaron juntos en `a6f3cc0`. El
  usuario hizo push y confirmó ese commit como `Live` en Render antes de tocar
  la base real.
- En producción, el `--dry-run` mostró `PENDIENTE` en `tenant_colegio_1` y
  `tenant_2005`; la aplicación terminó `OK` en ambos y el `--dry-run` final los
  mostró `OMITIDA (ya aplicada)`. No se borró ni se rellenó ningún dato.

**Avance del 2026-10-06 — paso 5.3 terminado localmente, sin commit:**

- Antes de cambiar el código pasaron **258 pruebas de caracterización** de
  cursos, conceptos de pago, años lectivos y escrituras de pagos. Fijan que,
  sin enviar año, el SQL, sus parámetros y las respuestas siguen como antes.
- Se escribieron primero 14 pruebas del contrato nuevo y fallaron por las
  funciones, el endpoint y los campos todavía ausentes. Al terminar se
  agregaron 3 comprobaciones de regresión de las rutas: son **17 pruebas
  nuevas** en `tests/test_anio_lectivo_preparacion.py`.
- `POST /anios-lectivos` es solo para admin, no recibe un número y crea
  exactamente `N+1` en `preparacion` desde el año activo. La operación bloquea
  la fila activa y la base conserva sus índices únicos como última defensa;
  falta de activo, preparación existente o choque de `N+1` responden `409`.
- `POST /cursos` y `POST /tipos-pagos` aceptan `anio_lectivo_id` opcional. Con
  él, el servidor valida que el año exista y sea editable para el admin, limita
  el nombre repetido a ese año y escribe allí. Sin él, ejecutan el camino
  anterior del activo. Los modelos de `PUT` no reciben el campo, para impedir
  mover registros de año al editarlos.
- No se copian cursos ni conceptos (eso es 5.4), no se creó 2027 y no se tocó
  una base real. Tampoco hubo migración ni cambio en el frontend.
- Verificación: **275 pruebas específicas pasan**; `scripts/verify.py` →
  **2049 pruebas pasan**, Ruff y `pip check` limpios; `git diff --check`
  también limpio.

*Confirmado después:* el usuario guardó este paso en `653703c`.

**Avance del 2026-10-06 — paso 5.4 terminado localmente, sin commit:**

- Antes del cambio pasaron **329 pruebas de caracterización** de años,
  cursos, asignaciones, conceptos y pagos. Después se escribieron 16 pruebas
  nuevas que fallaron por las capas todavía ausentes; la cobertura final del
  paso quedó en **20 pruebas nuevas**.
- Nuevo `POST /anios-lectivos/{anio_lectivo_id}/copiar-configuracion`, solo
  para admin. El backend comprueba que el destino sea exactamente `N+1` y esté
  en `preparacion`; el frontend no decide qué año es editable.
- Copia siempre los cursos **activos** del año vigente con nombre, jornada y
  nivel; nacen activos y guardan `curso_origen_id`. Copia siempre todos los
  conceptos, incluso los inactivos, con valor, descripción, tipo, fecha/día
  límite, gracia, mora, meses, frecuencia, generación automática y estado;
  cada uno guarda `tipo_pago_origen_id`.
- Las opciones `copiar_precios`, `copiar_carga_academica` y
  `copiar_directores` empiezan en `false`. Al activarlas, los precios apuntan
  al curso y concepto nuevos; los directores, al curso nuevo; y cada franja de
  carga conserva profesor, materia, día, horas, estado y orden de boletín.
  `asignacion_academica_id` se reconstruye en una segunda pasada usando solo
  ids nuevos.
- La copia completa usa una sola transacción. Antes de insertar detecta
  nombres repetidos con las mismas reglas de cursos y conceptos; una carrera
  concurrente también identifica el registro. Cualquier choque o referencia
  inconsistente revierte todo.
- No se creó 2027, no se conectó a una base real y no se tocaron pagos,
  deudas, cálculos ni migraciones. El frontend tampoco cambió.
- Verificación: **349 pruebas específicas pasan**; `scripts/verify.py` →
  **2069 pruebas pasan**, Ruff y `pip check` limpios; `git diff --check`
  también limpio.

*Confirmado después:* el usuario guardó este paso en `cffdfd7`.

**Avance del 2026-10-06 — paso 5.5 terminado y confirmado:**

- Antes de escribir código pasaron **135 pruebas de caracterización** de
  estudiantes, matrículas, preparación, copia de configuración y escrituras
  de pagos. Se escribieron las pruebas nuevas y fallaron por las rutas,
  esquemas y consultas todavía ausentes; la red final tiene **16 pruebas**.
- Nuevas rutas solo para admin:
  - `GET /anios-lectivos/{anio_lectivo_id}/matriculas/candidatos`, con
    `curso_origen_id`, lista desde la matrícula del curso activo y marca quién
    ya tiene matrícula en el destino.
  - `POST /anios-lectivos/{anio_lectivo_id}/matriculas/promocion` recibe curso
    origen, curso destino y los ids seleccionados; no matricula a los
    desmarcados.
  - `POST /anios-lectivos/{anio_lectivo_id}/estudiantes` usa los mismos datos
    globales del alta actual, pero crea solo la matrícula en preparación.
- El servidor comprueba que el destino sea exactamente `N+1` en
  `preparacion`, que el origen sea un curso activo, que el destino pertenezca
  al año indicado y que cada estudiante venga del curso origen y todavía no
  tenga matrícula en el destino. La lista conserva también retirados y
  egresados para que el admin decida explícitamente a quién promover.
- Al crear la matrícula de un estudiante existente, copia todas sus filas de
  `tipos_pagos_estudiantes` cuyos conceptos pertenecen al activo hacia el
  concepto de destino enlazado por `tipo_pago_origen_id`. Conserva valor,
  motivo y estado, y cada fila devuelta lleva `estado: "revisar"`. Si falta
  una equivalencia, revierte toda la selección.
- La promoción no ejecuta ninguna escritura sobre `estudiantes.curso_id`. El
  alta directa inserta los 34 datos globales sin curso, crea solo la matrícula
  del año en preparación y llama a `sincronizar_curso_vigente`, que conserva
  `NULL` al no existir matrícula activa. Así 2026 sigue siendo el curso
  vigente.
- Promoción y alta directa son transaccionales. Un choque concurrente se
  informa como `409` y revierte matrículas y valores ya copiados en esa
  solicitud. No se cambió el cálculo de cobros, deudas ni cartera; no hubo
  migración, frontend, acceso a una base real ni creación de 2027.
- Verificación: **151 pruebas específicas pasan**; `scripts/verify.py` →
  **2085 pruebas pasan**, Ruff y `pip check` limpios con `DATABASE_URL`
  ficticio. `git diff --check` limpio.

*Confirmado después:* el usuario guardó este paso en `144feb1`.

**Avance del 2026-10-06 — paso 5.6 terminado (`102ec77`):**

- Antes del cambio pasaron **425 pruebas de caracterización** de matrículas,
  cobros por año, escrituras financieras y guardias. Se escribieron primero
  11 pruebas nuevas; las 10 iniciales fallaron porque todavía no existían el resumen,
  el año opcional en valores especiales ni la lectura del curso desde la
  matrícula del año correspondiente.
- Nuevo `GET /anios-lectivos/{anio_lectivo_id}/resumen`, solo para admin. El
  backend exige que sea exactamente `N+1` en `preparacion` y devuelve el año
  junto con los conteos de cursos, conceptos, matrículas, valores especiales
  y pagos no anulados, además del total pagado para ese año.
- `GET /estudiantes/{estudiante_id}/valores-pago-personalizados` acepta
  `anio_lectivo_id` opcional. Sin enviarlo conserva el año activo y la misma
  forma de respuesta; al enviarlo valida el año y limita conceptos, matrícula
  y precio por curso al mismo año.
- Al guardar un valor especial, el curso ya no sale de
  `estudiantes.curso_id`: sale de la matrícula del año al que pertenece el
  concepto. Si el estudiante no tiene matrícula en ese año, no se escribe y
  se devuelve el error de negocio. La relectura posterior también queda
  limitada a ese año.
- La prueba integral copia un valor especial de matrícula a 2027, calcula la
  deuda usando ese valor, registra en noviembre de 2026 un pago dirigido a
  2027 y comprueba que la deuda 2027 queda en cero sin alterar 2026. No se
  cambió ninguna fórmula de cobro, mora, deuda o cartera.
- No hubo migración, frontend, acceso a una base real ni creación de 2027. La
  primera verificación global detectó un doble antiguo de base de datos; se
  actualizó para devolver año y curso, sin cambiar código de negocio.
- Verificación final: **436 pruebas específicas pasan**; `scripts/verify.py`
  → **2096 pruebas pasan**, Ruff y `pip check` limpios con `DATABASE_URL`
  ficticio. `git diff --check` limpio.

**Avance del frontend — pasos 5.7 a 5.10:**

- El paso 5.7 quedó confirmado en `5bfcad1`, con el ajuste responsive
  `409ab07`: ruta protegida y menú, creación/copia de 2027, recarga del
  proveedor y altas manuales de cursos y conceptos en preparación. Mirando el
  activo, los cuerpos anteriores no cambian.
- El paso 5.8 quedó confirmado en el frontend en `817c47e` y su registro en
  este documento principal en `d3cdfd3`. La página permite elegir curso origen y destino, desmarcar
  candidatos, matricular la selección y mostrar los valores especiales como
  `Revisar`; los ya matriculados quedan bloqueados.
- Estudiantes permite únicamente el alta directa al mirar un año en
  `preparacion`, usando `POST /anios-lectivos/{id}/estudiantes`. Editar datos
  globales y cambiar estados siguen reservados al activo. El resumen muestra
  los conteos y el total del backend sin botón de activar ni cálculos propios.
- Se caracterizó primero con 31 pruebas. El bloque específico final pasa 37
  pruebas en 8 archivos y `pnpm run check:deploy` pasa 2227 pruebas en 343
  archivos, lint y build. No se tocó código del backend, cobros, cartera,
  migraciones, bases reales ni producción; tampoco se creó 2027.
- Al sincronizar este documento principal, `scripts/verify.py` del backend
  pasó **2096 pruebas**, Ruff y `pip check`, con una `DATABASE_URL` ficticia.
  La primera corrida restringida tuvo 30 errores de permisos sobre la carpeta
  temporal de pytest; repetida fuera de esa restricción quedó completamente
  verde. `git diff --check` también quedó limpio.
- El paso 5.9 quedó confirmado en el frontend en `0689b7d` y su registro en
  este documento principal en `53da8f0`. Pagos tiene un selector propio,
  activo por defecto; solo al elegir otro año añade `anio_lectivo_id` a conceptos,
  deudas, cuotas, adelantos, valores personalizados y al cuerpo del pago.
  Historial y ventas conservan sus contratos, y las ventas no se ofrecen fuera
  del activo.
- `deuda_anios_anteriores` se muestra separada en Pagos, Cartera y la ficha del
  estudiante; Cartera no la suma al total consultado y su acción `Cobrar`
  conserva el año al abrir Pagos. Las respuestas financieras tardías del año
  anterior se descartan al cambiar el selector.
- Se caracterizó primero con 114 pruebas en 22 archivos. Las pruebas nuevas se
  escribieron primero y 16 fallaron por las piezas ausentes. El bloque
  específico final pasa 76 pruebas en 12 archivos y `pnpm run check:deploy`
  pasa 2245 pruebas en 344 archivos, lint y build. No se tocó código funcional
  del backend, fórmulas financieras, migraciones, bases reales ni producción.
- Al actualizar este documento principal, `scripts/verify.py` del backend pasó
  **2096 pruebas**, Ruff y `pip check` con una `DATABASE_URL` ficticia.
- El paso 5.10 terminó localmente en el frontend el 2026-10-08, pendiente de
  revisión y commit del usuario. El estado de cuenta de Cartera muestra el año
  consultado por estudiante o curso; el nombre del CSV también lo incluye; y
  el certificado de matrícula propone ese año sin dejar de ser editable.
- No cambió ninguna petición HTTP, cálculo financiero ni regla de cobro. No se
  tocó código funcional del backend, migraciones, bases reales ni producción.
  Primero pasaron 24 pruebas de caracterización en 6 archivos; las 3 pruebas
  nuevas fallaron antes de implementar y el bloque específico final pasa 27
  pruebas en 6 archivos. `pnpm run check:deploy` pasa 2248 pruebas en 344
  archivos, lint y build. Con este paso, la fase 5 queda completa en código.
- Al registrar el cierre en este documento principal, `scripts/verify.py`
  pasa **2096 pruebas**, Ruff y `pip check` con una `DATABASE_URL` ficticia.
  `git diff --check` queda limpio en ambos repos.

**Ajustes pedidos por el usuario el 2026-10-12, después de la fase 7** (no
estaban en los documentos; el usuario los pidió y autorizó uno por uno):

- **Frontend, sin cambios aquí:** la copia de configuración explica cada
  casilla, y en la sección de matricular se pueden editar los datos de un
  estudiante con el formulario y el `PUT /estudiantes/{id}` de siempre.
  Detalle en los "Ajuste del 2026-10-12" del documento del frontend.
- **Valores de pago al matricular.** El usuario quiere, al pasar a un
  estudiante de curso, ver el precio de cada concepto de su curso nuevo y
  personalizar lo que pagará. Decidió verlo **en la misma sección de
  matricular** (se descartó un botón que llevara a Pagos) y con **todos los
  conceptos que se cobran**, no solo la mensualidad. Hace falta backend: la
  ruta de deudas solo trae conceptos con deuda, y en noviembre de 2026 la
  mensualidad de 2027 no debe nada (comprobado con `calcular_deuda_concepto`:
  mensual 2027 el 15-nov-2026 → deuda 0; anual → deuda completa). Se le
  explicó y eligió hacer primero el backend. Se descartó que el frontend
  calculara el precio con la lista de conceptos: la regla es del backend
  (decisión 11).
- **Paso de backend, terminado localmente sin commit:** `GET
  /estudiantes/{id}/valores-pago?anio_lectivo_id=`, solo admin y solo de
  lectura. `cobros.obtener_valores_pago_estudiante` recorre los mismos
  conceptos que `_calcular_deudas` (activos, no opcionales, con precio en el
  curso de la matrícula de ese año) y llama dos veces a
  `_valor_unitario_concepto`: sin el valor del estudiante da `precio_curso`;
  con él, `valor_a_pagar` (y `valor_personalizado` si viene de él). El motivo
  sale de `obtener_motivos_personalizados_estudiante`, que solo corre si hay
  algún valor personalizado. Controlador
  `tipos_pagos_controller.listar_valores_pago_estudiante` (valida el año si
  llega y siempre cierra la conexión); ruta en `app/routes/tipos_pagos.py`,
  `404` con el mensaje para un año inexistente o sin matrícula. Guardar y
  quitar siguen por `PUT` y `DELETE` de `valores-pago-personalizados`, sin
  cambios.
- Pruebas: 14 nuevas en `tests/test_anio_lectivo_valores_pago.py`, escritas
  antes del código (fallaron las 14). Entre ellas, una que compara con
  `_calcular_deudas`: mismos conceptos y mismo valor, para que lo que se vea
  sea lo que se cobra. Ajustada a propósito: la prueba que fija las rutas del
  dominio de pagos (`test_pagos_escrituras_caracterizacion.py`, 19 → 20; sigue
  exigiendo admin y rutas síncronas). `scripts/verify.py` → **2279 pruebas
  pasan, 0 fallan**, Ruff y `pip check` limpios con una `DATABASE_URL`
  ficticia; `git diff --check` limpio. Documentado en
  `docs/API_ENDPOINTS.md` y `docs/CAMBIOS_BACKEND.md`. Sin migración, sin
  bases reales.
- **Siguiente paso, sin empezar:** el recuadro "Valores de pago" en el
  frontend. Antes de usarlo en producción, el usuario sube este backend y
  espera a que Render quede **Live**.

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
   solo admin, para correcciones puntuales. Ojo (hallazgo del paso 3.7a):
   asistencia, boletín y observaciones comprueban en la ruta que el
   estudiante sea del curso de la clase con `estudiantes.curso_id`; en un
   año reabierto eso rechaza al admin antes de llegar a guardar. Hay que
   hacer que esa comprobación mire la matrícula del año de la clase. Lo
   mismo las marcas de las listas de seguimiento (hallazgo del 3.7b) y la
   lectura de la lista de un curso, que hoy sale sin estudiantes fuera del
   año activo (hallazgo del paso 4.6 del frontend).
5. Terminado cuando: el ensayo completo de activación en una rama de Neon
   con copia de producción deja la consulta de control en 0 filas, los
   profesores ven solo 2027 y el admin puede consultar e imprimir 2026.

Decisiones confirmadas por el usuario el 2026-10-08 antes de iniciar la fase:

- Quien termina el último grado queda como `egresado`, no como `retirado`.
  Para no adivinar el grado por el nombre del curso, la decisión explícita se
  guarda en la matrícula del año que termina como `estado_salida`: `retirado`
  o `egresado`. `NULL` significa que todavía no se ha decidido; una matrícula
  en el año siguiente significa que continúa.
- Certificados podrá pedir estudiantes de todos los estados, conservando
  "Activos" como filtro visual inicial. Boletines seguirá listando solo
  activos. Es trabajo posterior del frontend dentro de esta fase.

Decisiones del usuario el 2026-10-08, al autorizar el paso 6.2 (el plan no
decía cómo se guarda la marca de salida):

- El paso 6.2 incluye la forma de marcar a quien no sigue. Se divide en
  **6.2a**, la vista previa (solo lectura), y **6.2b**, guardar o quitar la
  marca `retirado` o `egresado` en la matrícula del año activo. Sin la marca,
  nadie podría quedar decidido y la activación del 6.3 nunca se podría hacer.
- **Una marca y una matrícula en el año siguiente se excluyen, y el backend
  rechaza el choque con un mensaje.** No se puede matricular en el año
  siguiente a quien tenga marca de salida (el admin la quita primero, a
  propósito), ni marcar a quien ya tenga esa matrícula. Nada cambia sin que
  el admin lo vea.

Decisiones del usuario el 2026-10-08, al autorizar el paso 6.3:

- **Quien tiene matrícula en el año nuevo conserva su estado al activar**,
  aunque sea `retirado` o `inactivo` (por ejemplo, quien se fue a mitad de
  2026 y vuelve en 2027). El admin lo cambia después desde la ficha. Ojo:
  mientras no esté `activo`, no sale en la planilla de los profesores.
- **El backend también exige escribir el año para activar**
  (`confirmar_anio`), además de la confirmación del frontend.
- El paso se divide en **6.3a** (la activación) y **6.3b** (el boletín de un
  año cerrado o reabierto oculta las materias de su foto, decisión 13, en vez
  de mirar su estado actual). Después, un ensayo en una rama de Neon con el
  backend local, que es la primera vez que las consultas de los pasos 6.2 y
  6.3 corren contra una base real.

Decisiones del usuario el 2026-10-09, al autorizar el paso 6.4:

- El paso se divide en **6.4a** (reabrir y volver a cerrar), **6.4b** (la
  lista de seguimiento de un curso y la validación de sus marcas leen a los
  estudiantes por su matrícula en ese curso, no por `estudiantes.curso_id`) y
  **6.4c** (asistencia, boletín, observaciones, notas y planilla comprueban
  al estudiante por la matrícula del año de la clase).
- **El 6.4c queda para después**, hasta que exista una pantalla del admin que
  lo necesite. Motivos: el admin no tiene pantallas para escribir notas,
  asistencia, observaciones ni boletines (son del profesor; su `/boletin`
  solo consulta e imprime); las comprobaciones viven en
  `app/core/permissions.py`, zona sensible; y en la lectura de observaciones
  (`GET /observaciones/...`) el cambio dejaría a un profesor ver datos de un
  año pasado de sus antiguos estudiantes, contra la decisión 4. Los lugares
  son: `require_estudiante_in_asignacion` y `require_estudiantes_in_asignacion`
  (`permissions.py`), `buscar_estudiante_en_curso_de_asignacion`
  (`notas_repository.py`) y `buscar_estudiante_en_asignacion`
  (`planilla_repository.py`).
- Reglas por defecto del 6.4a, que el usuario no objetó: solo un año
  reabierto a la vez; el backend exige escribir el año, como al activar;
  volver a cerrar no cambia la foto de materias ni `cerrado_en`.

Avance del paso 6.1 al 2026-10-08:

- Ambos repos estaban en `main`, limpios y sincronizados con `origin/main` al
  iniciar: backend `cc0f45e` y frontend `365d083`.
- Antes del cambio pasaron 41 pruebas de migraciones de año lectivo y esquema
  base. Se escribieron primero 9 pruebas nuevas y las 9 fallaron porque todavía
  no existía el SQL.
- Se preparó `migrations/20261008_anios_lectivos_activacion.sql`. Agrega la
  columna opcional `matriculas.estado_salida`, limitada a `retirado` o
  `egresado`, y crea `anios_lectivos_materias_ocultas` con una sola fila por
  pareja año/materia. No inserta, actualiza ni borra datos existentes.
- Las 9 pruebas nuevas pasan. El bloque completo de migraciones da 49 pruebas
  correctas y una sola falla intencional en `test_esquema_base.py`: la base aún
  no declara la migración. La verificación global confirma 2104 pruebas
  correctas y esa misma única falla; Ruff y `pip check` pasan.
- No se ejecutó la migración, no se accedió a Neon ni a producción y no se
  regeneró ni editó a mano el esquema base. Según `docs/MIGRACIONES.md`, el
  siguiente paso es probar el SQL en una rama de Neon copiada de producción y
  regenerar desde allí el esquema base. `git diff --check` queda limpio en
  ambos repos. El paso 6.1 todavía no está terminado.

Prueba en la rama de Neon, 2026-10-08 (la hizo el usuario; el asistente no se
conectó a Neon ni a producción):

- El usuario creó una rama copiada de `production` y apuntó la terminal a su
  endpoint directo. Confirmó que el servidor no era `ep-late-smoke-aip41j6x`.
  El `.env` local sigue en el endpoint `-pooler` de producción, que
  `apply_migration.py` rechaza.
- `--dry-run`: `PENDIENTE` en `tenant_colegio_1` y `tenant_2005`. Después el
  usuario informó que aplicó la migración en la rama.
- El usuario regeneró `migrations/base/20260813_esquema_base_tenant.sql` desde
  `tenant_colegio_1` en la rama: 35 tablas, 1 función y 1 disparador. La
  revisión del diff confirmó solo lo esperado: cabecera con 42 migraciones,
  la columna `matriculas.estado_salida` con `chk_matriculas_estado_salida`, la
  tabla `anios_lectivos_materias_ocultas` con su llave primaria, su índice por
  materia y sus dos claves foráneas. La cabecera confirma que la migración
  quedó registrada en `tenant_colegio_1` de la rama.
- Verificación final, con una `DATABASE_URL` ficticia: **50 pruebas
  específicas pasan** (migraciones de año lectivo y esquema base);
  `scripts/verify.py` → **2105 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios; `git diff --check` limpio.
- El usuario confirmó la migración, el esquema base, las pruebas y este
  documento en el commit `6c6aabb`.
- En producción, el 2026-10-08 (lo hizo el usuario): la aplicación terminó `OK`
  en `tenant_colegio_1` y `tenant_2005`, y el `--dry-run` final los mostró
  `OMITIDA (ya aplicada)`. Que la aplicación dijera `OK` y no `OMITIDA`
  descarta que la terminal apuntara a la rama de prueba, donde ya estaba
  aplicada; el `.env` apuntaba a `ep-late-smoke-aip41j6x`. No se borró ni se
  rellenó ningún dato.
- La migración se aplicó antes del push de `6c6aabb`. En este paso no importa,
  porque ningún código usa todavía la columna ni la tabla.
- **Paso 6.1 terminado.**

Avance del paso 6.2a (vista previa de activación) al 2026-10-08:

- Ambos repos en `main` y limpios al iniciar, con los commits del 6.1 todavía
  sin push (backend `69245bc`, frontend `37a9a69`). Antes del cambio pasaban
  598 pruebas de año lectivo.
- Se escribieron primero 14 pruebas en
  `tests/test_anio_lectivo_vista_previa_activacion.py`; las 14 fallaron porque
  la ruta no existía.
- Nuevo `GET /anios-lectivos/{id}/activacion/vista-previa`, solo admin. El id
  debe ser exactamente `N+1` en preparación (`404` si no existe, `409` si no
  es ese año o falta el activo). Lee el año activo y el destino **sin
  bloquear filas** (`_contexto_activacion`), a diferencia de matricular, que
  sí bloquea.
- Cuenta, en una sola consulta (`contar_decisiones_activacion`): `continuan`
  (matriculados en los dos años), `nuevos` (solo en el siguiente), y
  `retirados` y `egresados` (marca en la matrícula del año activo y sin
  matrícula siguiente). La matrícula siguiente gana sobre una marca, aunque
  el 6.2b impedirá que coexistan.
- Lista `sin_decidir` (`listar_sin_decidir_activacion`): matrícula en el año
  activo, estudiante `activo`, sin marca y sin matrícula siguiente, ordenados
  por curso y apellido, con su curso para saber dónde resolverlo. Quien ya no
  está activo (retirado durante el año, por ejemplo) no necesita decisión
  (decisión 9: "todo estudiante activo").
- `puede_activar` es `true` solo si `sin_decidir` está vacía. Lo calcula el
  backend (decisión 11).
- Verificación: las 14 pruebas nuevas pasan; 612 de año lectivo;
  `scripts/verify.py` → **2119 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios con una `DATABASE_URL` ficticia; `git diff --check` limpio. Las
  consultas solo se probaron como texto: la prueba real queda para el ensayo
  completo del 6.3 en una rama de Neon.
- Documentado en `docs/API_ENDPOINTS.md`, `docs/ROLES_PERMISOS_BACKEND.md` y
  `docs/CAMBIOS_BACKEND.md`. Se agregó además a `docs/MIGRACIONES.md` la
  migración del 6.1, que había quedado sin registrar ahí.
- Sin migración, sin cambio de frontend, sin acceso a bases reales.
  **Paso 6.2a terminado; el usuario lo confirmó en el commit `5726cf4`.**

Avance del paso 6.2b (marcar quién no sigue) al 2026-10-08:

- Ambos repos en `main` y limpios al iniciar (backend `5726cf4`, frontend
  `0fa1c09`, los dos sin push). Antes del cambio pasaban 612 pruebas de año
  lectivo.
- Se escribieron primero 25 pruebas en
  `tests/test_anio_lectivo_decision_salida.py` y 3 en
  `tests/test_anio_lectivo_matriculacion_preparacion.py`. Fallaron las 27 que
  describen el cambio; la que confirma que la respuesta de candidatos no
  cambia pasaba antes y después.
- Nuevo `PUT /anios-lectivos/{id}/matriculas/salida`, solo admin. Cuerpo
  `DecisionSalidaEstudiantes`: `estudiante_ids` (mismas reglas que la
  promoción) y `estado_salida` obligatorio, `retirado`, `egresado` o `null`
  para quitarla. Se exige escribirlo también para quitarla, para que un cuerpo
  incompleto no borre una decisión por accidente.
- Usa `_contexto_matricula_en_preparacion`, el mismo de la promoción: bloquea
  el año activo y el destino, así marcar y matricular no se cruzan. Lee las
  matrículas (`listar_matriculas_para_salida`) y guarda todo o nada
  (`guardar_estado_salida`, que solo cambia `estado_salida`).
- Rechaza con `409` a quien no tenga matrícula en el año activo y, al marcar,
  a quien ya tenga matrícula en el siguiente. Quitar la marca siempre se
  permite: deshace un choque, nunca lo crea. No revisa el estado global del
  estudiante: si el admin marca a alguien ya retirado, es una decisión
  explícita suya, y la vista previa la cuenta.
- La promoción ahora lee la marca en `listar_candidatos_matricula` y rechaza
  con `409` a quien la tenga: "Los estudiantes N están marcados como que no
  siguen. Quita la marca antes de matricularlos." La respuesta de candidatos
  no cambia; exponer la marca allí queda para cuando se decida la pantalla del
  frontend.
- Hoy ninguna matrícula tiene marca, así que nada de lo existente cambia de
  comportamiento. No cambia `estudiantes.curso_id` ni el estado de nadie: eso
  es del 6.3.
- Verificación: 44 pruebas de los dos archivos; 640 de año lectivo;
  `scripts/verify.py` → **2147 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios con una `DATABASE_URL` ficticia; `git diff --check` limpio. Las
  consultas se probaron como texto; la prueba real queda para el ensayo del
  6.3 en una rama de Neon.
- Documentado en `docs/API_ENDPOINTS.md`, `docs/ROLES_PERMISOS_BACKEND.md` y
  `docs/CAMBIOS_BACKEND.md`. Sin migración, sin frontend, sin bases reales.
  **Paso 6.2b terminado; el usuario lo confirmó en el commit `2aaee65`. Con
  él queda completo el paso 6.2 en el backend.**

Avance del paso 6.3a (activar el año) al 2026-10-08:

- Ambos repos en `main` y limpios al iniciar (backend `2aaee65`, frontend
  `fac0bbd`, sin push). Antes del cambio pasaban 645 pruebas de año lectivo y
  de estudiantes.
- Se escribieron primero 27 pruebas en `tests/test_anio_lectivo_activacion.py`;
  fallaron al cargar porque la activación no existía.
- Nuevo `POST /anios-lectivos/{id}/activar`, solo admin, con
  `ActivarAnioLectivo` (`confirmar_anio`, entre 2000 y 2100). En una sola
  transacción (`activar_anio_controller`):
  1. `_contexto_activacion(..., bloquear=True)`: bloquea el año activo y el
     destino, en el mismo orden que la promoción y la marca de salida, y exige
     que el destino sea `N+1` en preparación.
  2. Compara `confirmar_anio` con el año del destino: si no coincide, `409`
     "Para activar, escribe el año 2027."
  3. Vuelve a listar los pendientes con los años bloqueados. Si hay alguno,
     `409` con `{codigo: "activacion_con_pendientes", mensaje, sin_decidir}`,
     el mismo formato del aviso de materias.
  4. Cuenta las decisiones (`contar_decisiones_activacion`, la del 6.2a).
  5. `guardar_materias_ocultas`: inserta en `anios_lectivos_materias_ocultas`
     las materias con estado distinto de `activo` (el complemento exacto del
     filtro del boletín), con `ON CONFLICT DO NOTHING`.
  6. `aplicar_marcas_de_salida`: pasa `estudiantes.estado` a la marca de quien
     no tiene matrícula siguiente. Quien la tiene conserva su estado.
  7. `activar_anio_siguiente`: cierra el activo (`cerrado_en`) y después
     activa el siguiente (`activado_en`). El orden importa: el índice único de
     un solo año activo se revisa en cada sentencia. Si alguno no cambió,
     `409` "... Nada cambió." y se deshace todo.
  8. `sincronizar_curso_vigente_de_todos`: la misma consulta de
     `sincronizar_curso_vigente`, ahora compartida como plantilla, sin el
     filtro por estudiante. Sigue siendo el único lugar que escribe
     `estudiantes.curso_id`.
  9. `contar_desajustes_curso_vigente`: la consulta de control del documento.
     Si no da 0, `409` "... Nada cambió." y se deshace todo.
- Las fechas usan `CURRENT_TIMESTAMP` de la base, igual que `creado_en`; en
  Neon es hora UTC (ver el hallazgo de la hora).
- Verificación: 27 pruebas nuevas; 672 de año lectivo y estudiantes (las de
  `sincronizar_curso_vigente` siguen pasando sin cambios);
  `scripts/verify.py` → **2174 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios con una `DATABASE_URL` ficticia; `git diff --check` limpio. Las
  consultas se probaron como texto: el ensayo en una rama de Neon, después
  del 6.3b, las probará de verdad.
- Documentado en `docs/API_ENDPOINTS.md`, `docs/ROLES_PERMISOS_BACKEND.md` y
  `docs/CAMBIOS_BACKEND.md`. Sin migración, sin frontend, sin bases reales.
  **Paso 6.3a terminado; el usuario lo confirmó en el commit `89b83cd`.**

Avance del paso 6.3b (boletín de un año cerrado) al 2026-10-08:

- Ambos repos en `main` y limpios al iniciar (backend `89b83cd`, frontend
  `f22f2b3`, sin push).
- Antes había dos consultas del boletín que ocultan materias por su estado
  actual: `leer_materias_del_estudiante` (boletín) y `leer_planilla_vigente`
  (reporte parcial). Las demás que filtran por `m.estado` son listados de
  clases (`asignaciones_repository`), fuera de la decisión 13. Los
  certificados no arman su propia lista de materias en el backend.
- Se escribieron primero 6 pruebas en
  `tests/test_anio_lectivo_boletin_materias_ocultas.py`: fallaron las 4 que
  describen el cambio; las 2 que protegen el texto de hoy pasaban antes y
  después. Se ajustaron, con explicación, 2 pruebas existentes que fijaban
  texto y parámetros (`test_boletin_caracterizacion.py`,
  `test_anio_lectivo_lecturas.py`); las dos fallaron antes del cambio.
- Nuevo `_materia_visible(anio_lectivo_id)` en `boletin_repository`, al lado de
  `_curso_del_estudiante`. Sin año devuelve exactamente el filtro de hoy, sin
  parámetros. Con año, un `CASE`: si el año está `cerrado` o `reabierto`,
  oculta las materias de su foto; si no, las inactivas, como siempre. El
  controlador ya convierte el año activo en "sin año"
  (`anio_distinto_del_activo`).
- Comparado contra el commit anterior con un script: sin año, las dos consultas
  reciben el mismo texto y los mismos parámetros, carácter por carácter.
- Verificación: 194 pruebas de boletín y lecturas por año;
  `scripts/verify.py` → **2180 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios con una `DATABASE_URL` ficticia; `git diff --check` limpio.
- Documentado en `docs/API_ENDPOINTS.md` y `docs/CAMBIOS_BACKEND.md`. Sin
  migración, sin frontend, sin bases reales. **Paso 6.3b terminado; el
  usuario lo confirmó en el commit `5cc4f61`. Con él queda completo el paso
  6.3 en el backend.**

Prueba del usuario en el Colegio Demo de producción, 2026-10-08:

- El usuario probó con el backend local y su `.env`, que apunta a producción,
  en `tenant_colegio_1` (Colegio Demo). Llegó a preparar 2027; **no activó**.
- Consultas de solo lectura que corrió en el SQL Editor de Neon (`production`):
  - `tenant_colegio_1.anios_lectivos`: 2026 (`id` 1) `activo`; 2027 (`id` 2)
    `preparacion`, sin `activado_en` ni `cerrado_en`.
  - Consulta de control: 0 filas.
  - Matrículas: 10 en 2026 y 6 en 2027, ninguna con `estado_salida`.
  - `anios_lectivos_materias_ocultas`: vacía, como corresponde sin activación.
  - `tenant_2005.anios_lectivos`: 2026 `activo`. El colegio real no se tocó.
- **Estado que queda en producción:** el Colegio Demo tiene 2027 en
  preparación con 6 matrículas. La marca de salida, la activación y el boletín
  de un año cerrado todavía no han corrido contra una base real.
- Se le recomendó no activar en el Colegio Demo de producción (cerraría 2026
  ahí, sin forma de reabrirlo hasta el 6.4) y hacer el ensayo de activación en
  una rama de Neon, que la copia tal cual.

Ensayo de activación en una rama de Neon, 2026-10-08 (lo hizo el usuario,
guiado paso a paso; el asistente no se conectó a ninguna base):

- Rama nueva copiada de `production` (servidor `ep-cool-fire-aii6h9qe`,
  confirmado con `([uri]$env:DATABASE_URL).Host`), backend local con
  `$env:DATABASE_URL` de la rama, frontend local y sesión de admin del Colegio
  Demo. Las rutas sin pantalla se llamaron desde `localhost:8000/docs`, que
  usa la cookie de sesión del navegador.
- Primero hubo un `404` "El año lectivo seleccionado no existe.": la sesión
  era de otro colegio. Con el admin del Colegio Demo, `GET /anios-lectivos`
  mostró 2026 (`id` 1) activo y 2027 (`id` 2) en preparación.
- Resultados, todos los esperados:
  - Vista previa: `continuan` 6, `nuevos` 0, `sin_decidir` 4 (ids 6, 7 y 8 de
    1B; 9 de Párvulo), `puede_activar: false`.
  - Activar con `confirmar_anio: 2026`: `409` "Para activar, escribe el año
    2027."
  - Activar con 2027 y pendientes: `409` con `codigo`
    `activacion_con_pendientes`, el mensaje y la lista de los 4.
  - Candidatos de 1B (consulta cambiada en el 6.2b): correcta.
  - Marcar al estudiante 1, ya matriculado en 2027: `409` "Los estudiantes 1
    ya tienen matrícula en 2027; no se pueden marcar como que no siguen."
    (Antes, un intento con el cuerpo de ejemplo de `/docs`, `[0]`, dio `422`
    por la validación de ids positivos.)
  - Marcar 8, 7 y 6 como `retirado` y 9 como `egresado`: `200`, cantidades 3
    y 1.
  - Vista previa: `sin_decidir` 0, `retirados` 3, `egresados` 1,
    `puede_activar: true`.
  - **Activar 2027: `200`.** 2026 `cerrado`, 2027 `activo`; resumen 6, 0, 3,
    1, `materias_ocultas` 0 y `cursos_vigentes_actualizados` 10.
  - En la base (SQL Editor con la rama elegida): consulta de control 0 filas;
    6, 7 y 8 `retirado`, 9 `egresado`, los cuatro con `curso_id` nulo; el
    Colegio Demo no tenía materias inactivas, así que la foto vacía era lo
    correcto.
  - En la app: el admin ve 2027 activo y 2026 cerrado; en Estudiantes, 2027
    muestra los 6 y 2026, con el filtro "Todos", los 10 (los 4 con su estado
    nuevo; con "Activos" salen 6, como corresponde). Abre e imprime un
    boletín de 2026. El profesor ve solo 2027 y no ve a los 4 que salieron.
  - Paso 6.3b: con Matemática desactivada después de cerrar, el boletín de
    2026 la sigue mostrando y el de 2027 no. Luego se volvió a activar.
- Cierre: backend de la rama detenido y su terminal cerrada; rama borrada.
- **Con esto se cumple, para la activación, el "terminado cuando" de la
  fase 6:** control en 0, profesores solo en 2027 y el admin consulta e
  imprime 2026. Quedan el paso 6.4 (reabrir y volver a cerrar) y las
  pantallas del frontend.
- Incidente: al arrancar el backend, la cadena completa de la rama, con la
  contraseña heredada de producción, quedó pegada en el chat. Ver
  "Contraseña" en la entrega.

Avance del paso 6.4a (reabrir y volver a cerrar) al 2026-10-09:

- Ambos repos en `main` y limpios al iniciar (backend `c107262`, frontend
  `1f9cccc`, sin push).
- Se escribieron primero 30 pruebas en `tests/test_anio_lectivo_reabrir.py`;
  fallaron al cargar porque las rutas no existían.
- Nuevos `POST /anios-lectivos/{id}/reabrir` y `/cerrar`, solo admin, con
  `ConfirmacionAnioLectivo` (`confirmar_anio`). `ActivarAnioLectivo` ahora la
  hereda sin cambios, y el error del año mal escrito se renombró a
  `ConfirmacionAnioInvalidaError` (las pruebas del 6.3a solo cambiaron ese
  nombre).
- Los dos usan `_cambiar_estado_anio_pasado`: bloquea el año activo (el turno
  de todo cambio de estado de los años), bloquea el año pedido, exige su
  estado (`cerrado` para reabrir, `reabierto` para cerrar), compara el año
  escrito y, al reabrir, rechaza si ya hay otro reabierto
  (`leer_anio_reabierto`). Luego `cambiar_estado_anio`, que solo cambia
  `estado` con `WHERE estado = <el esperado>`; si no cambió una fila, `409`
  "... Nada cambió." y se deshace.
- No toca estudiantes, cursos, la foto de materias ni `activado_en` o
  `cerrado_en`.
- Verificación: 30 pruebas nuevas; 703 de año lectivo; `scripts/verify.py` →
  **2210 pruebas pasan, 0 fallan**, Ruff y `pip check` limpios con una
  `DATABASE_URL` ficticia; `git diff --check` limpio.
- Documentado en `docs/API_ENDPOINTS.md`, `docs/ROLES_PERMISOS_BACKEND.md` y
  `docs/CAMBIOS_BACKEND.md`. Sin migración, sin frontend, sin bases reales.
  **Paso 6.4a terminado; el usuario lo confirmó en el commit `0d6d202`.**

Avance del paso 6.4b (listas de seguimiento por matrícula) al 2026-10-09:

- Ambos repos en `main` y limpios al iniciar (backend `0d6d202`, frontend
  `2d0684b`, sin push).
- La lista de un curso (`GET /listas-seguimiento/{curso_id}`) y la validación
  de sus marcas usan la misma función, `leer_estudiantes_del_curso`. Solo
  cambió esa consulta: `FROM matriculas m JOIN estudiantes e ... WHERE
  m.curso_id = %s`, por apellido y nombre, sin filtrar por estado (como
  antes). Cada estudiante tiene una sola matrícula por año y cada curso es de
  un año, así que no hay repetidos.
- Equivalencia en el año activo: la consulta de control (0 filas) garantiza
  que `estudiantes.curso_id` coincide con la matrícula del año activo, así
  que un curso de ese año trae exactamente los mismos alumnos.
- Pruebas: se reemplazó la que fijaba `FROM estudiantes ... WHERE curso_id`
  por una que exige la matrícula; las 2 fallaron antes del cambio. La base
  falsa con guion de `test_anio_lectivo_guardia.py` y
  `test_anio_lectivo_guardia_conteos.py` reconocía la consulta por su
  comienzo: dio `422` hasta actualizar ese guion. La cuenta de consultas no
  cambió.
- Verificación: 70 pruebas de listas de seguimiento; `scripts/verify.py` →
  **2211 pruebas pasan, 0 fallan**, Ruff y `pip check` limpios con una
  `DATABASE_URL` ficticia; `git diff --check` limpio.
- Resuelve el hallazgo del paso 4.6 del frontend (la lista de un curso de
  2026 saldría vacía después de activar 2027) y el del 3.7b (en un año
  reabierto, el admin no podría marcar a sus estudiantes).
- **Paso 6.4b terminado; el usuario lo confirmó en el commit `f0e0ca6`. Con
  él queda completo el backend de la fase 6, salvo el 6.4c, aplazado por
  decisión del usuario.**

Fase 6 del frontend, autorizada el 2026-10-09. Plan por pasos, uno a la vez
con el visto bueno del usuario (numeración compartida con el backend):

- **Decisión del usuario:** la marca de salida se pone **en la pantalla de
  promoción por curso**: a cada estudiante que no pasa, Retirado, Egresado o
  quitar la marca. Todo se decide en un solo lugar. Se descartó ponerla en la
  lista de pendientes de la vista previa, porque para quitar una marca haría
  falta otra lista.
- **6.5 (backend):** la lista de candidatos trae `estado_salida`.
- **6.6 (frontend):** marcar y quitar la marca en la promoción; quien está
  marcado no se puede seleccionar para matricular.
- **6.7 (frontend):** sección "Activar": vista previa con la lista de
  pendientes por curso, activar con el año escrito, la lista que devuelve un
  `409` con pendientes y el resumen al terminar.
- **6.8 (frontend):** reabrir y volver a cerrar un año pasado, con el año
  escrito.
- **6.9 (frontend):** el título del aviso de año cerrado en Tipos de pago
  (hallazgo del 4.3).
- **6.10 (frontend):** Certificados pide todos los estados, con "Activos"
  como filtro inicial (decisión del 2026-10-08).

Avance del paso 6.5 (la marca de salida en los candidatos) al 2026-10-09:

- Ambos repos en `main` y limpios al iniciar (backend `f0e0ca6`, frontend
  `e2e470d`, sin push).
- `_formatear_candidato` agrega `estado_salida`, que el repositorio ya leía
  desde el 6.2b para que la promoción rechace a los marcados. Los demás campos
  no cambian.
- La prueba del 6.2b que exigía la respuesta sin cambios se reemplazó por
  `test_los_candidatos_dicen_su_marca_de_salida`, que falló antes del cambio.
- Verificación: 19 pruebas del archivo de matrícula en preparación;
  `scripts/verify.py` → **2211 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios con una `DATABASE_URL` ficticia; `git diff --check` limpio.
- Documentado en `docs/API_ENDPOINTS.md` y `docs/CAMBIOS_BACKEND.md`.
  **Paso 6.5 terminado; el usuario lo confirmó en el commit `a3f7086`.**
- **6.6 (frontend), 2026-10-09:** marcar Retirado, Egresado o quitar la marca
  en la promoción, commit `5892602` del frontend. Detalle en el avance del
  6.6 del documento del frontend.
- **6.7 (frontend), 2026-10-09:** sección "Activar" en la página de años
  lectivos (vista previa, pendientes por curso, activar escribiendo el año,
  lista del `409` y resumen), commit `f6a035e` del frontend. Detalle en el
  avance del 6.7 del documento del frontend.
- **6.8 (frontend), 2026-10-09:** sección "Años pasados" para reabrir y
  volver a cerrar escribiendo el año, commit `5f69b77` del frontend. Detalle
  en el avance del 6.8 del documento del frontend.
- **6.9 (frontend), 2026-10-09:** en Tipos de pago, el `409` de año cerrado
  sale con el título "Año cerrado". El frontend reconoce el texto fijo de
  `MENSAJE_ANIO_CERRADO` (`app/services/anio_lectivo.py`): **si ese texto
  cambia, hay que cambiar también `esAvisoAnioCerrado` en
  `frontend-react/src/utils/anioLectivo.js`.** Commit `cf00e3d` del
  frontend; el comentario junto a la constante, en `5634245` de este repo.
- **6.10 (frontend), 2026-10-09:** Certificados pide `GET /estudiantes` con
  `estado=todos` (y el año si se mira otro) con una función propia; la
  pantalla sigue empezando en "Activos" y Boletines no cambia. Es un cambio
  deliberado de una petición del año activo, por la decisión del usuario del
  2026-10-08. Commit `b7184f8` del frontend; `pnpm run check:deploy` pasa
  2294 pruebas. **Con él queda completa la fase 6**, salvo el 6.4c.

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

**Inicio autorizado el 2026-10-10.** Al empezar, los dos repos estaban en
`main`, limpios y subidos a GitHub (`origin/main` en `0517c41` y `b7184f8`).
La fase 7 no necesita migración: `cursos.curso_origen_id` existe desde el paso
5.2. No se leyó `docs/MIGRACIONES.md` por eso.

Decisión del usuario el 2026-10-10, antes del paso 7.1 (los documentos no lo
decían): **si en 2026 una materia cambió de profesor a mitad de año, para cada
periodo se trae lo del último profesor que escribió algo en ese periodo.** El
caso existe porque editar una clase con historial obliga a desactivarla y
crear otra (`editar_asignacion_controller`: "Desactívala y crea una nueva…"),
así que el curso de 2026 queda con dos planeadores de la misma materia. "El
último" es la clase de id mayor: el planeador no guarda cuándo se escribió, y
la clase del profesor que llegó se crea después. Se descartaron traer solo el
del último profesor (si no escribió nada, no se trae nada) y no traer nada si
hay dos.

Reglas por defecto del asistente, que el usuario no objetó:

- Un profesor solo puede usar lo del año pasado desde una clase del año
  activo (decisión 4).
- La lista de planes del 7.2 trae todos los de esa materia en el curso de
  origen, de cualquier profesor (decisión 15).
- Al usar un plan viejo se llena solo el texto; el periodo queda el que el
  profesor tiene elegido; la fecha y las evidencias, vacías (decisión 16).

Plan por pasos, uno a la vez con el visto bueno del usuario:

- **7.1 (backend):** el origen y el planeador (consultar si se puede traer y
  traerlo).
- **7.2 (backend):** los planes del año pasado (la lista y el texto de uno).
- **7.3 (frontend):** el botón "Traer el planeador del año pasado".
- **7.4 (frontend):** "Usar un plan del año pasado" en el formulario.

Avance del paso 7.1 (traer el planeador del año pasado) al 2026-10-10:

- Antes del cambio pasaban 307 pruebas del planeador y de la guardia. Se
  escribieron primero 31 pruebas en
  `tests/test_anio_lectivo_planeador_anterior.py`, que fallaron al cargar
  porque nada de lo que prueban existía; al revisarlas se sumó una (32).
- El origen, en un solo lugar: `CLASES_DE_ORIGEN_SQL`
  (`anios_lectivos_repository.py`), las clases de la misma materia en el curso
  `curso_origen_id` del curso de la clase, sin mirar el profesor ni si la clase
  sigue activa. El 7.2 la reutiliza.
- `planeador_anual_repository.py`: `leer_planeador_anio_anterior` (una
  consulta: año y estado de la clase, si su planeador ya tiene filas y si hay
  algo escrito que traer) y `copiar_planeador_anio_anterior` (un solo `INSERT
  ... SELECT`: periodo, slot y los cuatro textos; `fecha` `NULL`). Las filas
  que se traen: por periodo, las de la clase de origen de id mayor con algún
  texto en ese periodo; una fila sin texto no cuenta.
- `planeador_anual_controller.py`: `consultar_planeador_anio_anterior_controller`
  (`hay_origen`, `planeador_vacio`, `puede_traer`) y
  `traer_planeador_anio_anterior_controller`. El permiso del profesor
  (`require_asignacion_access`) se revisa con la misma conexión, como en el
  inicio del profesor. Al traer, la guardia del año usa el estado ya leído,
  antes de escribir; luego `409` si ya hay filas y `404` si no hay nada que
  traer. Si llegan dos clics a la vez, el segundo choca con la regla única
  (clase, periodo, slot) y recibe el mismo `409`; no queda nada a medias.
- `app/services/anio_lectivo.py`: `puede_guardar_en_anio`, la regla de la
  guardia sin lanzar, para `puede_traer`. Así el botón no aparece cuando el
  guardado lo rechazaría.
- `app/routes/planeador_anual.py`: `GET` y `POST
  /planeador-anual/{asignacion_id}/anio-anterior`, declaradas antes de las de
  un periodo (si no, `anio-anterior` se leería como periodo y daría `422`).
  Las rutas de siempre no cambian.
- Consultas, medidas en pruebas: el `GET`, 3 para el profesor y 2 para el
  admin; el `POST`, 4 y 3. Una conexión en cada caso.
- Pruebas: por primera vez en esta funcionalidad, las consultas **corren de
  verdad**, en SQLite (viene con Python; el equipo no tiene PostgreSQL), con
  un curso de 2026 donde la materia cambió de profesor, otra materia, otro
  curso, un curso de 2027 creado desde cero y una materia nueva. Comprueban:
  cada periodo del último que lo escribió y sin mezclar periodos, sin fechas,
  2026 intacto, sin origen (`404`), profesor distinto al de 2026, otra franja
  de la misma clase, planeador no vacío (`409`), profesor ajeno (`403`), año en
  preparación (profesor `403`, admin trae), año cerrado (`409`), clase
  inexistente (`404`), dos clics a la vez, la ruta de un periodo intacta y el
  conteo de consultas. Veintiuna versiones dañadas del código hacen fallar
  alguna prueba; la primera vuelta dejó pasar dos y por eso se sumaron una
  fila sin texto en un periodo elegido y la prueba desde otra franja.
- Ajustadas a propósito: las cuatro pruebas de
  `test_planeador_anual_caracterizacion.py` que fijan el inventario exacto del
  módulo (rutas, controladores importados, sentencias SQL y funciones del
  repositorio), ampliadas con lo nuevo. Fallaron solo esas cuatro; las demás
  303 pasaron sin tocarlas.
- Límite: SQLite no es PostgreSQL. Lo propio de PostgreSQL (tipos, el
  parámetro dentro del `SELECT` del `INSERT`) lo confirma el ensayo en una
  rama de Neon con el backend local.
- Verificación: 339 pruebas del planeador, la guardia y el paso;
  `scripts/verify.py` → **2243 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios con una `DATABASE_URL` ficticia; `git diff --check` limpio.
- Documentado en `docs/API_ENDPOINTS.md`, `docs/ROLES_PERMISOS_BACKEND.md` y
  `docs/CAMBIOS_BACKEND.md`. Sin migración, sin frontend, sin bases reales.
  **Paso 7.1 terminado; el usuario lo confirmó en el commit `16c9052`.**

Avance del paso 7.2 (los planes de clase del año pasado) al 2026-10-10:

- Autorizado por el usuario el 2026-10-10 ("continua"), con la fase 7 ya
  iniciada y el 7.2 nombrado como siguiente paso. Ambos repos en `main` y
  limpios al iniciar (backend `16c9052`, frontend `b7184f8`). Antes del cambio
  pasaban 414 pruebas de planes, de la guardia y del 7.1.
- Se escribieron primero 22 pruebas en
  `tests/test_anio_lectivo_planes_anterior.py`, que fallaron al cargar porque
  nada de lo que prueban existía.
- `plan_de_clases_repository.py`: `listar_planes_de_origen` (id, fecha,
  periodo, unidad y tema de los planes del origen, por fecha, la más antigua
  primero) y `obtener_plan_de_origen` (los ocho textos de un plan, cada vacío
  como `""`, solo si el plan es del origen de la clase). Las dos usan
  `CLASES_DE_ORIGEN_SQL`, la regla del 7.1, y corren primero la guardia del año
  sobre la clase en su misma conexión, como el guardado de un plan: sirven
  para crear un plan en esa clase. Siguen el estilo del módulo (cada función
  abre su conexión).
- `plan_de_clases_controller.py`: `listar_planes_anio_anterior_controller` y
  `obtener_plan_anio_anterior_controller`, que responde `403` "Ese plan no es
  del año pasado de esta clase." si el plan no es del origen o no existe (el
  mismo `403`, para no decir si existe en otra clase). El servicio solo pasa
  la llamada, como el resto del módulo.
- `app/routes/plan_de_clases.py`: `GET /plan-de-clases/{asignacion_id}/anio-anterior`
  y `/anio-anterior/{plan_id}`, con el permiso en la ruta
  (`require_asignacion_access`), como las demás rutas de planes. No chocan con
  ninguna ruta existente.
- Qué no se copia, por diseño: la fecha, las evidencias, el periodo (queda el
  que el profesor tiene elegido, regla por defecto del 2026-10-10) ni el estado
  de revisión. No se crea nada: el plan nuevo se guarda por `POST
  /plan-de-clases`, que no cambió.
- Consultas, medidas en pruebas: como `GET /plan-de-clases/{asignacion_id}`,
  dos conexiones y tres consultas para el profesor (su permiso en la ruta; la
  guardia y la lectura) y una conexión y dos consultas para el admin.
- Pruebas, con las consultas corriendo en SQLite como en el 7.1: la lista trae
  los planes de los dos profesores de 2026 (también del que se fue), por
  fecha, sin otra materia, otro curso ni el plan de 2027 de la propia clase;
  desde otra franja, la misma lista; sin origen, lista vacía; el texto viene
  sin fecha, evidencias ni periodo, y con `""` donde no hay texto; un plan de
  otra materia, de otro curso, de 2027 o inexistente da `403`; profesor ajeno
  (`403`); año en preparación (profesor `403`, admin lee); año cerrado
  (`409`); nada se escribe; la ruta de los planes de la clase sigue igual; y
  el conteo de conexiones y consultas. Catorce versiones dañadas del código
  hacen fallar alguna prueba.
- Ajustadas a propósito: las cuatro pruebas de
  `test_plan_de_clases_caracterizacion.py` que fijan el inventario del módulo
  (total de líneas 1421 → 1542, rutas 11 → 13, consultas 27 → 29 y qué
  funciones abren conexión). Fallaron solo esas cuatro; las demás 410 pasaron
  sin tocarlas.
- Verificación: 436 pruebas de planes, la guardia, el 7.1 y el 7.2;
  `scripts/verify.py` → **2265 pruebas pasan, 0 fallan**, Ruff y `pip check`
  limpios con una `DATABASE_URL` ficticia; `git diff --check` limpio.
- Documentado en `docs/API_ENDPOINTS.md`, `docs/ROLES_PERMISOS_BACKEND.md` y
  `docs/CAMBIOS_BACKEND.md`. Sin migración, sin frontend, sin bases reales.
  **Paso 7.2 terminado; el usuario lo confirmó en el commit `c5dd384`. Con él
  queda completo el backend de la fase 7.**
- **7.3 (frontend), 2026-10-10:** el botón "Traer el planeador del año pasado"
  en el planeador del profesor, commit `df2afe3` del frontend (registro aquí
  en `e34faa6`). Pregunta `GET /planeador-anual/{id}/anio-anterior` solo cuando el
  periodo que se abre llega vacío, y una vez por visita; el botón depende de
  `puede_traer`, y se esconde si hay cambios sin guardar. `pnpm run
  check:deploy` pasa 2320 pruebas. Detalle, contrato de las cuatro rutas de la
  fase 7 y verificación en el avance del 7.3 del documento del frontend. En
  este repo no cambió código.
- **7.4 (frontend), 2026-10-10:** "Usar un plan del año pasado" en el
  formulario del plan de clases, terminado localmente en el frontend, sin
  commit. **Decisión del usuario:** la lista (`GET
  /plan-de-clases/{id}/anio-anterior`) se pide al crear un plan, una vez por
  clase, y si llega vacía el navegador lo anota y no vuelve a preguntar por
  esa clase; así todo 2026, cuando ninguna clase tiene origen, casi no cuesta
  peticiones. Al elegir un plan se llenan solo los textos (con cambios sin
  guardar, se confirma antes) y se guarda por `POST /plan-de-clases`, como
  uno nuevo. `pnpm run check:deploy` pasa 2352 pruebas (en la segunda
  corrida; la primera tuvo un tiempo agotado en una prueba ajena). Detalle y
  verificación en el avance del 7.4 del documento del frontend. En este repo
  no cambió código. **Con él, la fase 7 queda completa
  en código en los dos repos.**

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
- ~~Fase 3, paso 3.5: ¿la regla de materias ocultas de un año cerrado
  (`anios_lectivos_materias_ocultas`, que se crea en la fase 6) va en el
  3.5?~~ **Respondida el 2026-10-02: no, va en la fase 6.** En el 3.5 el
  boletín oculta las materias inactivas como hoy, para cualquier año; la
  regla de "como estaba al cerrar" (decisión 13) y su tabla se hacen en la
  fase 6, cuando se cierra el primer año. Motivo: antes de la fase 6 no
  puede existir un año cerrado, así que no queda ningún caso sin cubrir, y
  el 3.5 no necesita migración.
- ~~Antes de la fase 5 (encontrada el 2026-10-02): `POST /cursos` y `POST
  /tipos-pagos` siempre crean en el año activo. La fase 4 dice que el admin
  prepara 2027 desde las pantallas existentes, pero ningún documento dice
  cómo se crea un curso o un concepto **nuevo** (que no venga de la copia)
  en el año en preparación. ¿Se agrega `anio_lectivo_id` opcional a esas dos
  rutas, y en qué fase?~~ **Respondida el 2026-10-05: sí, en la fase 5.** Si
  se omite, se conserva el año activo y el contrato actual; si se envía, el
  backend valida que ese año exista y sea editable para el admin.
- ~~Fase 4 (frontend), antes de su paso 4.1: en las pantallas que no
  dependen del año, ¿el selector se esconde o se muestra desactivado?~~
  **Respondida el 2026-10-03: se esconde.** ~~Antes de su paso 4.2: ¿qué
  puede hacer el admin mirando un año en preparación?~~ **Respondida el
  2026-10-03: editar lo que ya existe en ese año**, menos crear cursos o
  conceptos y lo de Estudiantes, que siguen solo en el año activo hasta la
  fase 5. Detalle en el documento del frontend.
- ~~Antes de la fase 6: ¿un estudiante del último grado que termina se marca
  "no continúa" (retirado) o hace falta un estado distinto como
  "egresado"?~~ **Respondida el 2026-10-08: quien termina el último grado
  queda como `egresado`.** La matrícula guardará la decisión explícita para no
  deducirla del nombre del curso. El estado y el filtro `egresado` ya existen.

## Entrega para el siguiente chat

Estado al 2026-10-10. Si `git status` o el historial de git dicen otra
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
  `b2362f1`, `34712dd`, `b5f4099` y `f03b032`, ya en GitHub al 2026-10-02
  (`origin/main` en `f03b032`). Ver los "Avance" de cada uno.
- **Fase 3, iniciada el 2026-10-02** con la autorización del usuario (y
  sabiendo que la fase 2 sigue sin subir): inventario confirmado con `grep`
  y plan en siete pasos, 3.1 a 3.7. Ver "Inventario confirmado" y "Plan por
  pasos" en la fase 3. El inventario encontró seis cosas que no estaban en
  la lista; la más importante, los choques de horario del profesor, que sin
  filtro por año bloquearían la carga académica de 2027. Paso 3.1 en el
  commit `fea2e83` (`GET /anios-lectivos` y `resolver_anio_pedido`); paso
  3.2 en `43764f2` (lo que ve el profesor, los listados del admin y los
  choques de horario, por año); paso 3.3 en `da4da87` (cursos, conceptos,
  precios por curso, listas de seguimiento y reporte general, por año); paso
  3.4 en `c9554af` (lista de estudiantes, cartera y estado de cuenta por
  curso, por año; decisiones 18 y 19); paso 3.5a en `eb835e3` (boletín,
  reporte parcial y puesto por año; el puesto ya no mezcla años); paso 3.5b
  en `8716fc5` (observador, expediente y planes del admin por año; su
  "Avance" deja una consulta de solo lectura pendiente sobre faltas sin
  clase); paso 3.6 en `0110359` (aviso al renombrar una materia que se usa
  en otro año). Paso 3.7: medición y costo aceptado en `50d9f53`; 3.7a en
  `fcb18ef` (la guardia en las rutas que usa el profesor); paso 3.7b en
  `9edbe5d` (las rutas de solo admin). **Con él, la fase 3 queda
  terminada.** Sus avances dejan un hallazgo para la fase 6 (comprobaciones
  de estudiantes con `estudiantes.curso_id`). Los once commits de la fase 3
  (`57b3710` a `9edbe5d`) están en GitHub desde el 2026-10-03: los subió el
  usuario, que dijo haberlos subido a producción.
- **Fase 4 (frontend), con código completo** y autorizada paso a paso desde
  el 2026-10-03:
  usuario: inventario y plan por pasos (4.1 a 4.7, commit `dbb0e48` del
  frontend), **paso 4.1** (la base: lista de años, selector y aviso; commit
  `4b14347`), **paso 4.2** (Cursos, Asignaciones, Orden boletín y Horarios
  con el año elegido; el admin edita lo que ya existe en un año en
  preparación; commit `78c48f7`), **paso 4.3** (Tipos de pago y Cartera
  vencida con el año elegido; mirando otro año, sin "Cobrar"; commit
  `0798f21`), **paso 4.4** (Estudiantes con el año elegido; mirando otro
  año, solo consulta; commit `c7f0622`), **paso 4.5** (Boletines y
  certificados con el año elegido; commit `2140fae`), **paso 4.6** (Listas
  de seguimiento y bandeja de planes con el año elegido; commit `72be3da`)
  y **paso 4.7** (diálogo al renombrar materias, commit frontend `8eac0ce`;
  documentación en este repo `ce8d7a7`), el 2026-10-05. Con un año no cambia
  nada visible. El 4.5 dejó un
  hallazgo de antes de esta función
  (Boletines y Certificados solo listan estudiantes activos) y el 4.6 uno de
  este repo para la fase 6 (la lista de un curso sale sin estudiantes fuera
  del año activo); ver sus "Avance" en la fase 4 de este documento. En este repo no
  tiene trabajo. Su inventario dejó un hallazgo para la fase 5 de este repo:
  crear o editar un estudiante no valida el año del curso (ver "Ojo" en la
  fase 5).
- **Fase 5 iniciada el 2026-10-05 con autorización explícita del usuario:**
  inventario y plan de diez pasos (5.1 a 5.10) escritos.
  El usuario aprobó que las altas manuales de cursos y conceptos acepten el
  año opcional, que el impreso/CSV de Cartera identifique el año y que el
  certificado de matrícula proponga el año consultado. Al iniciar, ambos
  repos estaban en `main`, limpios y `ahead 8`: backend `ce8d7a7`, frontend
  `8eac0ce`. Se leyó completa `docs/MIGRACIONES.md`; ninguna migración se
  ejecutó ni se accedió a producción. Verificación del paso documental:
  `scripts/verify.py`, 2016 pruebas, Ruff y `pip check` limpios; en el
  frontend, `pnpm run check:deploy`, 2210 pruebas en 341 archivos, lint y
  build limpios; `git diff --check` limpio en ambos repos.
- **Paso 5.1 terminado y confirmado en `d113e15`:** la
  matrícula activa pasó a ser la fuente del curso vigente;
  `sincronizar_curso_vigente` quedó como única escritura de
  `estudiantes.curso_id`; y un curso inexistente o ajeno al año activo produce
  `409` y revierte la transacción. El cuerpo y la respuesta existentes no
  cambian. No hubo migración ni acceso a bases reales. Caracterización previa:
  27 pruebas. Pruebas específicas finales: 36. Verificación global:
  `scripts/verify.py`, 2025 pruebas, Ruff y `pip check` limpios, más
  `git diff --check` limpio. Detalle en el "Avance" de la fase 5.
- **Paso 5.2 completo en producción el 2026-10-06 (`a6f3cc0`):** pruebas
  primero y migración incremental para las dos columnas de origen, sus claves
  foráneas autorreferentes y sus índices. En la rama de Neon pasó por
  `PENDIENTE` → `OK` → `OMITIDA` en los dos tenants; el usuario regeneró desde
  allí el esquema base (34 tablas, 1 función, 1 disparador). El diff generado
  solo contiene las seis piezas esperadas y la cabecera. Verificación: 41
  pruebas específicas y 2032 globales pasan, Ruff, `pip check` y
  `git diff --check` limpios. Después del push, el usuario confirmó `a6f3cc0`
  `Live` en Render y repitió en producción la secuencia `PENDIENTE` → `OK` →
  `OMITIDA` en `tenant_colegio_1` y `tenant_2005`.
- **Paso 5.3 confirmado en `653703c`:** el nuevo `POST
  /anios-lectivos` calcula y crea `N+1` en preparación, solo para admin; las
  altas de cursos y conceptos aceptan el año opcional y validado, sin cambiar
  el camino anterior cuando se omite. No se creó 2027, no hubo migración ni
  acceso a una base real. Pasaron 275 pruebas específicas y 2049 globales,
  además de Ruff y `pip check`.
- **Paso 5.4 confirmado en `cffdfd7`:** copia en una sola
  transacción cursos activos y todos los conceptos; las opciones controlan
  precios, carga académica y directores. Rehace todas las referencias con ids
  nuevos, identifica choques y devuelve conteos. No se creó 2027, no hubo
  migración ni acceso a una base real. Pasaron 349 pruebas
  específicas y 2069 globales, además de Ruff y `pip check`.
- **Paso 5.5 confirmado en `144feb1`:** tres rutas solo para admin consultan
  candidatos por matrícula, promueven solo la selección y dan
  de alta un estudiante directamente en preparación. Los valores especiales
  se copian por `tipo_pago_origen_id` y se devuelven como `revisar`; cualquier
  inconsistencia revierte todo. El curso vigente 2026 no cambia. No se creó
  2027, no hubo migración, frontend ni acceso a una base real. Pasan 151
  pruebas específicas y 2085 globales, además de Ruff y `pip check`.
- **Paso 5.6 confirmado en `102ec77`:** el resumen del año
  en preparación cuenta cursos, conceptos, matrículas, valores especiales y
  pagos no anulados, con su total. La consulta de valores especiales acepta el
  año opcional y tanto su lectura como su escritura usan el curso de la
  matrícula de ese mismo año, nunca la copia del curso vigente. Una prueba
  integral cubre una matrícula 2027 pagada en noviembre de 2026 y comprueba
  que 2026 no cambia. No hubo migración, frontend, acceso a una base real ni
  creación de 2027. Pasan 436 pruebas específicas y 2096 globales, además de
  Ruff y `pip check`.
- **Paso 5.7 confirmado en el frontend:** pantalla base en `5bfcad1` y ajuste
  responsive en `409ab07`. Permite crear/copiar el siguiente año y las altas
  manuales autorizadas, manteniendo intactas las peticiones del año activo.
- **Paso 5.8 confirmado en el frontend (`817c47e`, documento principal
  `d3cdfd3`):**
  promoción por curso con selección explícita, valores especiales marcados
  `Revisar`, alta directa de estudiante en preparación y resumen sin activar.
  Pasan 37 pruebas específicas y 2227 globales, además de lint y build. El
  backend quedó sin cambios funcionales y no hubo acceso a bases ni
  producción.
- **Paso 5.9 confirmado en el frontend (`0689b7d`, documento principal
  `53da8f0`):**
  selector propio del año del pago, año opcional en lecturas y cuerpos, ventas
  limitadas al activo y deuda anterior separada en Pagos, Cartera y ficha de
  Estudiantes. Pasan 76 pruebas específicas y 2245 globales, además de lint y
  build. En este repo solo se actualizó el documento principal; su verificación
  pasó 2096 pruebas, Ruff y `pip check` con una `DATABASE_URL` ficticia.
- **Paso 5.10 confirmado en el frontend (`82675ba`):** el
  año consultado aparece en el estado de cuenta y nombre del CSV de Cartera, y
  se propone en el certificado de matrícula sin bloquear su edición. Pasan 27
  pruebas específicas y 2248 globales, además de lint y build. No cambió
  ningún contrato HTTP ni código funcional del backend. Al actualizar este
  documento, el backend pasa 2096 pruebas, Ruff y `pip check`.
- **Hecho aparte, la noche del 2026-09-30:** el arreglo de la hora
  (`2e77634` en este repo, `033c042` en el frontend). Cobros, cartera y
  alta de colegios usan la fecha de Colombia (`app/core/fechas.py`), y el
  frontend propone fechas de Colombia (`src/utils/fechaColombia.js`). Ver
  el hallazgo correspondiente y `docs/CAMBIOS_BACKEND.md`.
- **Pendiente del usuario:**
  - Fases 2 y 3: en producción según el usuario (2026-10-03). Confirmar en
    Render que el despliegue de `9edbe5d` quedó **Live** y que Cartera
    vencida, Pagos y el detalle de un estudiante muestran los mismos
    números que antes.
  - Consulta de faltas sin clase (solo lectura; en el "Avance" del 3.5b).
  - Borrar la rama `prueba-anio-lectivo-b` de Neon, si no se borró sola.
  - Si no se hizo todavía, **rotar la contraseña** de `neondb_owner` (ver
    el punto siguiente).
- Contraseña: la cadena de conexión de una rama, con su contraseña
  heredada de producción, quedó pegada en el chat de origen. La rama ya se
  borró, pero la contraseña de producción sigue siendo la misma: rotarla en
  Neon (Roles → Reset password) y enseguida actualizar `DATABASE_URL` en
  Render y en el `.env` local, a una hora tranquila. **Volvió a pasar el
  2026-10-08**, al iniciar el ensayo de activación en la rama
  `ep-cool-fire-aii6h9qe`: la cadena completa de la rama, con la contraseña
  heredada, quedó pegada en el chat. **Rotar en cuanto termine el ensayo.** En
  adelante, pegar solo la línea del servidor (`([uri]$env:DATABASE_URL).Host`).
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
- **Fase 6 iniciada el 2026-10-08 con autorización explícita del usuario.**
  También confirmó que quien termina el último grado queda `egresado`, y que
  Certificados consultará todos los estados manteniendo Activos como filtro
  inicial; Boletines no cambia. **El paso 6.1 quedó terminado el 2026-10-08:**
  la migración se probó en una rama de Neon, el esquema base se regeneró desde
  allí (`scripts/verify.py`: 2105 pruebas sin fallas), quedó en el commit
  `6c6aabb` y se aplicó en los dos tenants de producción. Ver "Prueba en la
  rama de Neon" en la fase 6.
- **Pendiente del usuario tras el paso 6.1:** push de `6c6aabb` y de este
  registro, y confirmar en Render que el despliegue quede **Live**. Borrar la
  rama de prueba de Neon. El `DATABASE_URL` del `.env`, que el 2026-10-08
  quedó un rato en el directo de producción, ya volvió al endpoint `-pooler`
  (verificado ese mismo día, solo el servidor).
- **Paso 6.2 autorizado el 2026-10-08 y dividido en 6.2a y 6.2b** (ver
  "Decisiones del usuario... al autorizar el paso 6.2" en la fase 6). El
  **6.2a, la vista previa de activación**, quedó en `5726cf4` y el **6.2b,
  marcar quién no sigue**, en `2aaee65`. El paso 6.2 del backend está
  completo.
- **Paso 6.3 autorizado el 2026-10-08 y dividido en 6.3a y 6.3b** (ver
  "Decisiones del usuario... al autorizar el paso 6.3" en la fase 6). El
  **6.3a, la activación**, quedó en `89b83cd`. El **6.3b, el boletín de un
  año cerrado**, quedó en `5cc4f61`. El paso 6.3 del backend está completo.
  El usuario probó la preparación de 2027 en el Colegio Demo de producción
  (ver "Prueba del usuario en el Colegio Demo" en la fase 6): sin activar,
  control en 0 y el colegio real intacto.
- **Ensayo de activación hecho el 2026-10-08 en una rama de Neon, todo
  correcto** (ver "Ensayo de activación en una rama de Neon" en la fase 6).
  La rama ya se borró.
- **Pendiente urgente del usuario:** rotar la contraseña de `neondb_owner`
  (ver "Contraseña" arriba) y, después, el push de los commits de la fase 6
  (del 6.1 al 6.10), que siguen solo en local en los dos repos.
- **Paso 6.4 autorizado el 2026-10-09** y dividido en 6.4a, 6.4b y 6.4c (ver
  "Decisiones del usuario el 2026-10-09" en la fase 6). El **6.4a, reabrir y
  volver a cerrar**, quedó en `0d6d202`. El **6.4b, listas de seguimiento por
  matrícula**, quedó en `f0e0ca6`. El 6.4c queda para después. **El backend
  de la fase 6 está completo.**
- **Fase 6 del frontend autorizada el 2026-10-09**, pasos 6.5 a 6.10 (ver
  "Fase 6 del frontend" en la fase 6). La marca de salida va en la pantalla
  de promoción (decisión del usuario). El **6.5**, la marca en los
  candidatos (backend), quedó en `a3f7086` y el **6.6**, marcar en la
  promoción (frontend), en `5892602` y el **6.7**, la sección "Activar"
  (frontend), en `f6a035e` y el **6.8**, reabrir y volver a cerrar
  (frontend), en `5f69b77` y el **6.9**, el aviso de año cerrado en Tipos de
  pago (frontend), en `cf00e3d`. El **6.10**, Certificados con todos los
  estados (frontend), quedó en `b7184f8`: `pnpm run check:deploy` pasa 2294
  pruebas. **La fase 6 está completa en los dos repos**, salvo el 6.4c,
  aplazado por decisión del usuario. Al 2026-10-10 los dos repos estaban
  subidos a GitHub (visto con `git fetch`): `origin/main` en `0517c41` y
  `b7184f8`. Que Render haya desplegado, y si ya se rotó la contraseña, no se
  ve desde el repo.
- **Fase 7 iniciada el 2026-10-10 con autorización explícita del usuario**,
  paso 7.1. El usuario decidió que, si una materia tuvo dos profesores en
  2026, cada periodo se trae del último que escribió algo en él (ver la fase
  7). Plan: 7.1 y 7.2 en el backend, 7.3 y 7.4 en el frontend. **El 7.1, traer
  el planeador del año pasado**, quedó en `16c9052`: `GET` y `POST
  /planeador-anual/{asignacion_id}/anio-anterior`. **El 7.2, los planes de
  clase del año pasado**, quedó en `c5dd384`: `GET
  /plan-de-clases/{asignacion_id}/anio-anterior` y `/{plan_id}`;
  `scripts/verify.py` pasa 2265 pruebas. **Con él quedó completo el backend de
  la fase 7.** Sin migración, sin frontend, sin bases reales. **El 7.3, el
  botón del planeador (frontend)**, quedó en `df2afe3`; el contrato de las
  cuatro rutas está anotado en el documento del frontend. **El 7.4, "Usar un
  plan del año pasado" (frontend)**, quedó en `4e71c2b`.
  **Con él, la fase 7 queda completa en código en los dos repos.** Falta su
  revisión con un profesor de prueba, que es parte del ensayo de abajo.
- **Ajustes del 2026-10-12, pedidos por el usuario** (ver el final de la fase
  5): en el frontend, la explicación de las casillas de la copia y "Editar
  datos" en la sección de matricular; aquí, la ruta de solo lectura `GET
  /estudiantes/{id}/valores-pago` para "Valores de pago" al matricular. Todo
  terminado localmente, sin commit. Sin subir a GitHub al empezar: 4 commits
  aquí (`16c9052` a `144f93b`) y 2 en el frontend (`df2afe3`, `4e71c2b`).
- **Siguiente acción exacta:** el usuario revisa y hace el commit de la ruta
  `valores-pago` aquí, y el de los dos ajustes en el frontend. El siguiente
  paso, sin empezar y con su visto bueno, es el recuadro "Valores de pago" en
  el frontend. Después, cada cosa con su autorización:
  1. Subir la fase 7 y la ruta `valores-pago`: primero el backend, esperando
     a que Render quede **Live**, y después el frontend, que usa las rutas
     nuevas. Sin un año 2027 activo, la fase 7 no se ve en producción.
  2. Antes del ensayo, en el SQL Editor de Neon (solo lectura), la consulta
     de faltas sin clase del paso 3.5b, que sigue pendiente.
  3. Rotar la contraseña de `neondb_owner`, si no se hizo.
  4. Un **ensayo completo con las pantallas** en una rama de Neon copiada de
     producción, con el backend y el frontend locales: marcar en la
     promoción, ver la vista previa, activar desde el botón, reabrir y volver
     a cerrar, sacar un certificado de un retirado y, con la fase 7, traer el
     planeador y usar un plan del año pasado con un profesor de 2027. Es
     también la primera vez que las consultas del 7.1 y el 7.2 corren en
     PostgreSQL.
  5. El 6.4c, cuando exista una pantalla del admin que lo necesite.
  La activación real de `tenant_2005` la hace el usuario desde la pantalla,
  nunca el asistente.
- Prompt para retomar: `docs/funcionalidades/PROMPT_CONTINUACION_ANIO_LECTIVO.md`.
