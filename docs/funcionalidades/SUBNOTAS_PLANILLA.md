# Funcionalidad: Subnotas y porcentajes en la planilla — Backend

## Control

- Estado: **Parte A publicada el 2026-10-21.** A0 en `185d5b6`, A1 y A2 en
  `e36f976`, con la migración aplicada en producción y Render **Live**. En el
  frontend, A3 en `12c2067`, A4 (la pantalla) en `d58fb0e` y `5f9f1b1`, A5
  (la prueba en local) bien, y push con `3fb9831` publicado en Vercel. Ver
  "Publicación del frontend". **Parte B: diseño (B0) en `822dd4e`, con las
  propuestas PB1 a PB10 aprobadas por el usuario el 2026-10-21,
  caracterización (B1) en `a9cdc57` y, desde el 2026-10-22, B2 en cuatro
  partes: B2a (el cálculo) en `a630183`, B2b (tabla y ruta de los
  porcentajes, migración escrita sin aplicar) en `dcf8443`, B2c (la
  definitiva del boletín) en `05a8bbe` y B2d (las demás lecturas) en
  `0498f80`: B2 completo. B3 (rama de Neon) bien y backend de la parte B en
  producción el 2026-10-22 (`dfe0336`, migración aplicada, Render Live).**
  Nadie ve nada nuevo todavía: falta la pantalla (B4 y B5).
- Tipo: Función nueva de producto. No es una capa del programa de
  modularización de `docs/modularizacion/` y no debe confundirse con una.
- Repos afectados: este repo (`sistema_escolar_api`) y `frontend-react`. Ver
  también `frontend-react/docs/funcionalidades/SUBNOTAS_PLANILLA.md`, que
  cubre la pantalla.
- Dos partes, en este orden (decisión 6):
  - **Parte A — Subnotas.** No cambia cómo se calcula la nota del periodo.
  - **Parte B — Porcentajes por tipo de nota.** Sí la cambia. Aquí solo
    queda esbozada; se diseña en detalle (paso B0) cuando A esté publicada.
- Riesgo:
  - A: **medio.** Migración con dos tablas nuevas, y toca dos rutas que los
    profesores usan a diario (guardar una nota y borrar un tipo de nota).
  - B: **alto.** Cambia la nota oficial del periodo: boletín, reporte
    parcial y puesto.
- Origen: pedido de los profesores de preescolar y primaria, contado por el
  usuario el 2026-10-21.
- Última actualización: 2026-10-22.

## Objetivo

Hoy el profesor hace varios trabajos en el periodo para un mismo tipo de nota,
los promedia a mano al final y escribe ese resultado en la planilla. Se busca:

1. Que pueda registrar en la planilla las **subnotas** de cada tipo de nota
   sin enredarse, y que la celda muestre su **promedio**.
2. Que pueda seguir escribiendo la **nota final directa** en la celda, como
   hoy.
3. (Parte B) Que cada tipo de nota tenga un **porcentaje**, porque un tipo no
   tiene por qué valer lo mismo que otro.

## Diagnóstico (verificado en el código el 2026-10-21)

- **Cada celda de la planilla es una fila de `notas_detalle`**: estudiante,
  asignación, periodo y `descripcion` (el nombre del tipo de nota).
  `POST /planilla/nota` la reemplaza: la borra y la vuelve a insertar
  (`planilla_repository.borrar_nota_existente` e `insertar_nota`). Una celda
  vaciada queda como fila con `nota NULL`.
- **Los tipos de nota no tienen tabla propia.** Existen porque hay filas en
  `notas_detalle` con esa `descripcion`. Para crear un tipo, el frontend hace
  un `POST /planilla/nota` con el primer estudiante y `nota: null`
  (`agregarTipoEvaluacion`). `DELETE /planilla/tipo` borra todas las filas de
  esa descripción en la asignación y el periodo. El nombre se compara con
  `LOWER(TRIM(...))`.
- `GET /planilla-excel/{asignacion_id}/{periodo}` (`planilla_excel_controller`)
  arma columnas y filas y calcula el **promedio simple** de las columnas
  numéricas. Asistencia usa la misma ruta solo para la lista de estudiantes
  (`obtenerPlanillaAsistencia` en el frontend).
- **Muchas lecturas promedian todas las filas de `notas_detalle`** de un
  estudiante en una asignación y periodo: el boletín del admin cuando no hay
  definitiva guardada (`boletin_repository.leer_materias_del_estudiante`), el
  reporte parcial (`obtener_reporte_parcial_admin_controller`), los tableros
  (`dashboard_repository`), la ficha del estudiante
  (`estudiantes_repository.leer_promedios_por_materia`) y `notas_repository`.
  **Por eso las subnotas no pueden guardarse en `notas_detalle`**: cambiarían
  todas esas cifras sin que nadie lo note.
- La definitiva que propone el boletín del profesor también es el promedio
  simple de las celdas, calculado en el frontend
  (`utils/boletines/ingresoBoletin.js: crearDatosBoletinInicial`).
- El servidor decide el tipo de evaluación según el nivel del curso
  (`app/core/nivel_academico.resolver_tipo_evaluacion`): preescolar guarda
  caritas (`valoracion`, con `nota NULL`) y primaria guarda números.
- **El backend no conoce la equivalencia entre caritas y números.** Solo existe
  en el frontend: `src/constants/valoracionesDesarrollo.js` (⭐ `destacado` 5,
  😀 `logrado` 4, 🙂 `proceso` 3, 🧩 `apoyo` 2) y
  `src/utils/valoracionesDesarrollo.js` (promedio, y carita más cercana con
  empate hacia la más alta).
- Guardias que ya usa la planilla y que las rutas nuevas deben repetir:
  `get_current_user`, `require_asignacion_access`, que el estudiante sea del
  curso de la asignación, `exigir_asignacion_editable` (año lectivo, paso
  3.7) y `resolver_asignacion_academica_id_cursor` (las notas se guardan en la
  asignación académica, no en el id que llega).
- `notas_detalle.nota` es `numeric(3,2)`: guarda dos decimales.

## Decisiones ya tomadas (con el usuario, 2026-10-21)

1. Un profesor tiene sus tipos de nota (por ejemplo tres) y **cada tipo puede
   tener subnotas**. El **promedio de las subnotas** es lo que se ve en la
   celda de la planilla principal, como hoy.
2. **El porcentaje se pone en el tipo de nota al crearlo** (parte B), no en
   cada subnota. Las subnotas de un tipo valen todas igual.
3. **Las subnotas se escriben en un modal** (una ventana encima de la
   planilla) que se abre desde la celda. La planilla principal no gana
   columnas.
4. **Se puede seguir poniendo la nota final directa** en la celda, como hoy.
5. **Las subnotas de un tipo son las mismas para todo el curso.** Si se agrega
   "Taller 1" en Cognitivo, aparece vacía para todos los estudiantes. Así cada
   modal tiene los mismos espacios y se ve a quién le falta qué.
6. **Primero la parte A, después la B.**
7. Aplica a preescolar (caritas) y a primaria (números): la subnota sigue el
   tipo de evaluación del curso, igual que la celda.

## Propuestas de este diseño (aprobadas por el usuario el 2026-10-21)

Se escribieron en el paso A0 para cerrar los casos que las decisiones no
cubren. **El usuario las aprobó todas el 2026-10-21**, al autorizar A1,
incluida la de renombrar (P5).

- **P1. Celda calculada o celda a mano, por estudiante.** Si un estudiante
  tiene al menos una subnota calificada en un tipo, su celda es **calculada**:
  muestra el promedio y no se escribe a mano (el servidor responde `409` si
  se intenta). Si no tiene ninguna, la celda **se escribe a mano**, como hoy.
  Así la nota escrita y las subnotas nunca se contradicen, y un estudiante que
  no hizo los trabajos puede tener su nota final escrita a mano (decisión 4).
- **P2. Una subnota vacía no cuenta** en el promedio, igual que hoy una celda
  vacía no cuenta en el promedio de la planilla. Si el profesor quiere que
  cuente como 1.0, escribe el 1.0.
- **P3. De nota a mano a subnotas.** Si la celda ya tenía una nota escrita a
  mano, el modal avisa que al guardar se reemplaza por el promedio. Nada se
  convierte solo.
- **P4. Vaciar todas las subnotas de un estudiante** deja su celda vacía
  (`nota NULL`, como cuando hoy se borra una nota, para que la columna no
  desaparezca), y la celda vuelve a escribirse a mano.
- **P5. Borrar una subnota** (por ejemplo "Taller 2") borra sus calificaciones
  en todo el curso y recalcula la celda de cada estudiante afectado. El aviso
  dice cuántas calificaciones se van a borrar. **Renombrarla** no cambia
  ninguna nota. Sirve para corregir un nombre mal escrito sin perder lo
  calificado.
- **P6. Borrar el tipo de nota** borra también sus subnotas y calificaciones,
  en la misma operación. Si no, reaparecerían al crear otro tipo con el mismo
  nombre.
- **P7. Redondeo a dos decimales, mitad hacia arriba:** 4.125 queda en 4.13.
  Se calcula en centésimas enteras (`Decimal` en Python, enteros en el
  frontend). `round()` de Python daría 4.12, porque redondea al par, y la
  pantalla mostraría otra cosa.
- **P8. Caritas:** las caritas se pasan a número con la escala de arriba, se
  promedian y el resultado vuelve a la carita más cercana (empate, la más
  alta), con la misma regla que ya usa la planilla. La celda guarda la carita
  en `valoracion`, con `nota NULL`, igual que hoy.
- **P9. El servidor calcula y guarda la celda** en la misma operación en que
  guarda las subnotas: se guarda todo o nada. La pantalla solo muestra una
  vista previa con la misma fórmula.
- **P10. "Guardar" en el modal envía en una sola petición todas las subnotas
  del estudiante en ese tipo**, y "Siguiente" guarda y pasa al estudiante de
  abajo.
- **P11. Límites:** hasta 20 subnotas por tipo. El nombre tiene de 1 a 60
  caracteres y no se repite dentro del tipo (sin distinguir mayúsculas ni
  espacios en los extremos). Las columnas internas ocultas (`mas_alto`) no
  admiten subnotas.
- **P12. Orden de las subnotas:** el de creación. No se reordenan
  arrastrando, porque no se pidió.

## Parte A — Subnotas

### Diseño de datos

Migración nueva `migrations/<fecha>_planilla_subnotas.sql` con dos tablas
nuevas. Ninguna tabla existente se modifica.

**`planilla_subnotas`**: una fila por subnota de un tipo de nota (lo que el
profesor ve como "Taller 1").

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `serial` | clave primaria |
| `asignacion_id` | `integer NOT NULL` | FK a `asignaciones(id)` `ON DELETE CASCADE`, como `notas_detalle`. Siempre la asignación académica ya resuelta |
| `periodo` | `integer NOT NULL` | |
| `tipo_nota` | `varchar(100) NOT NULL` | el mismo texto de `notas_detalle.descripcion`; `CHECK` de no vacío |
| `nombre` | `varchar(60) NOT NULL` | `CHECK` de no vacío |
| `creada_en` | `timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP` | da el orden (P12); el mismo tipo que usa Listas de seguimiento |

- Índice único: `(asignacion_id, periodo, LOWER(TRIM(tipo_nota)),
  LOWER(TRIM(nombre)))`. Es la garantía real contra nombres repetidos aunque
  lleguen dos peticiones a la vez. **Sirve también para leer** las subnotas de
  una planilla, porque empieza por `(asignacion_id, periodo)`: el índice de
  lectura aparte que preveía el diseño sobraba y no se creó (A1).

**`planilla_subnotas_valores`**: una fila por calificación de un estudiante
en una subnota.

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `serial` | clave primaria |
| `subnota_id` | `integer NOT NULL` | FK a `planilla_subnotas(id)` `ON DELETE CASCADE` |
| `estudiante_id` | `integer NOT NULL` | FK a `estudiantes(id)`, sin cascada, igual que `notas_detalle` |
| `nota` | `numeric(3,2)` | `CHECK` entre 1 y 5 |
| `valoracion` | `varchar(30)` | código de carita; la API valida que exista en la escala |
| `actualizada_en` | `timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP` | |

- `UNIQUE (subnota_id, estudiante_id)`: una calificación por estudiante y
  subnota. Su índice sirve para guardar (`ON CONFLICT`), para leer las de un
  estudiante y para el borrado en cascada.
- `CHECK`: exactamente uno de `nota` o `valoracion` tiene valor. Una subnota
  vacía no se guarda: se borra su fila (P2).
- **Sin índice por `estudiante_id`** (el diseño lo preveía): ninguna consulta
  filtra solo por estudiante, y los estudiantes no se borran (cambian de
  estado), así que tampoco hace falta para la clave foránea (A1).

Con las cascadas, borrar una subnota borra sus calificaciones (P5), y borrar
la asignación borra todo, igual que pasa hoy con `notas_detalle`.

### Cálculo

Funciones puras, sin base de datos y con pruebas propias:

- `app/core/valoraciones_desarrollo.py` (nuevo): la escala de caritas, copia
  exacta de la del frontend. Una prueba fija los cuatro códigos y sus valores.
  El frontend tiene la prueba gemela. **Si la escala cambia, cambia en los dos
  repos.**
- `app/core/subnotas_planilla.py` (nuevo): el promedio de la celda a partir de
  las calificaciones, con las reglas P2, P7 y P8. Sin calificaciones devuelve
  "vacía".

Casos que deben quedar probados: subnotas vacías que no cuentan, todas vacías,
4.125 → 4.13, 1.005 → 1.01 (en flotante saldría 1.00), caritas con empate
(4.5 → `destacado`) y caritas sin empate (4.33 → `logrado`).

### Contrato de la API

**Fijado con pruebas en A1** (`tests/test_subnotas_planilla.py`). Lo que
cambió respecto del borrador de A0 está marcado "(A1)", con su motivo. Todas
las rutas nuevas usan las mismas guardias que la planilla (ver "Diagnóstico")
y responden errores con su código HTTP (`403`, `404`, `409`, `422`) y un
mensaje en español.

**Lectura**

- `GET /planilla-excel/{asignacion_id}/{periodo}`: **sin parámetro nuevo, la
  respuesta es idéntica a la de hoy.** Asistencia y cualquier pestaña vieja no
  cambian ni pagan una consulta de más. Con `?con_subnotas=true` agrega dos
  claves:
  - `subnotas`: `{ "<tipo_nota>": [ { "id": 7, "nombre": "Taller 1" } ] }`,
    en orden de creación;
  - en cada estudiante, `subnotas`: `{ "<subnota_id>": 4.0 }` (o el código de
    la carita).

  Así el modal se abre sin peticiones nuevas, y Anterior/Siguiente no esperan
  al servidor.

**Escrituras nuevas**

- `POST /planilla/subnotas` con `{ asignacion_id, periodo, tipo_nota, nombre }`:
  crea la subnota para todo el curso y responde `201` con `{ id, tipo_nota,
  nombre }`, ya recortados. `409` si el nombre ya existe en ese tipo. `404` si
  el tipo no está en la planilla (A1: el borrador decía `409`, pero lo que
  falta es el tipo, no hay conflicto). `422` si pasa el límite de P11 o es una
  columna interna.
- `PUT /planilla/subnotas/{id}` con `{ asignacion_id, nombre }`: la renombra
  (P5) y responde `{ id, nombre }`. `404` si no es de esa clase, `409` si el
  nombre ya existe. (A1: lleva `asignacion_id` para comprobar el permiso y el
  año lectivo igual que las demás rutas de la planilla, y para que solo se
  renombre una subnota de esa clase.)
- `DELETE /planilla/subnotas/{id}?asignacion_id=`: la borra, recalcula las
  celdas afectadas y devuelve `{ mensaje, calificaciones_borradas, celdas: {
  "<estudiante_id>": { nota, valoracion } } }` para que la pantalla se
  actualice sin recargar. (A1: `asignacion_id` por lo mismo que en el `PUT`.)
- `POST /planilla/subnotas/valores` con `{ asignacion_id, periodo, tipo_nota,
  estudiante_id, tipo_evaluacion, valores: { "<subnota_id>": valor o null } }`:
  guarda las calificaciones de ese estudiante en ese tipo, recalcula su celda,
  la guarda y la devuelve (P9, P10) como `{ estudiante_id, tipo_nota,
  tipo_evaluacion, nota, valoracion, subnotas }`. **Toda subnota enviada tiene
  que ser de esa asignación, periodo y tipo** (si no, `422`). Así nadie puede
  escribir en la clase de otro profesor mandando un id ajeno. (A1: **solo toca
  las subnotas que llegan**; una que no viene conserva lo que tenía. Así un
  modal abierto antes de que alguien agregara otra subnota no la vacía al
  guardar. `tipo_evaluacion` es el que pide la pantalla, y el nivel del curso
  manda sobre él igual que en `POST /planilla/nota`.)

Al guardar calificaciones y recalcular, se bloquean las subnotas del tipo
(`SELECT … FOR UPDATE`). Así dos guardados a la vez sobre el mismo tipo no
calculan con datos viejos.

**Cambios en rutas que ya existen**

- `POST /planilla/nota`: si el estudiante tiene subnotas calificadas en ese
  tipo, responde **`409`** con "Esta nota se calcula con sus subnotas.
  Cámbiala desde las subnotas." (P1). Sin subnotas, idéntica a hoy. Cuesta una
  consulta más en la misma conexión; A1 la mide antes y después.
- `DELETE /planilla/tipo`: borra además las subnotas de ese tipo (P6), en la
  misma operación. La respuesta no cambia.

### Plan por pasos (cada uno con autorización explícita)

- **A0 — Diseño** (este documento y su gemelo del frontend). Sin código.
  **Hecho**, en `185d5b6`.
- **A1 — Backend.** **Hecho el 2026-10-21, sin commit** (ver "Avance del paso
  A1"). Primero, pruebas de caracterización de las tres rutas que
  ya existen (`GET` de la planilla sin el parámetro, `POST /planilla/nota` y
  `DELETE /planilla/tipo`), con conteo de consultas, para demostrar que sin
  subnotas nada cambia. Después: la migración (escrita, sin aplicar), la
  escala de caritas, el cálculo, el repositorio, las rutas nuevas, el `409`
  de `POST /planilla/nota` y el borrado en `DELETE /planilla/tipo`.
  Documentar en `docs/API_ENDPOINTS.md`, `docs/BASE_DATOS.md`,
  `docs/MIGRACIONES.md` y `docs/CAMBIOS_BACKEND.md`.
  `tests/test_esquema_base.py` fallará a propósito hasta A2: es la compuerta
  que obliga a aplicar la migración y regenerar el esquema base.
- **A2 — Base de datos (lo hace el usuario).** **Hecho el 2026-10-21, sin
  commit** (ver "Avance del paso A2"). Probar la migración en una rama
  de Neon, probar allí la planilla de siempre con el backend nuevo, regenerar
  el esquema base desde esa rama y hacer un commit con la migración, el
  esquema base y el código juntos. Lista completa en "Paso A2". **Todavía sin
  push** (ver "Orden de publicación").
- **A3 — Frontend: contratos.** **Hecho el 2026-10-21**, en `12c2067` (ver
  el documento del frontend). El servicio, las utilidades (vista previa del
  cálculo, cuándo una celda es calculada) y los ganchos, con pruebas. Detalle
  en el documento del frontend.
- **A4 — Frontend: pantalla.** **Hecho el 2026-10-21**, en `d58fb0e` y
  `5f9f1b1` (ver el documento del frontend). El botón en la celda, el modal
  con Anterior/Siguiente, la celda calculada y la vista de celular.
- **A5 — Prueba en local** con el Colegio Demo (`tenant_colegio_1`), nunca con
  estudiantes de `tenant_2005`. El backend local escribe en la base real, así
  que la prueba necesita la migración ya aplicada (paso 2 del orden de
  publicación) o un backend local apuntando a la rama de Neon. **Hecho el
  2026-10-21 por el usuario, todo bien**, en primaria y en preescolar (ver
  "Avance del paso A5" del documento del frontend).

### Orden de publicación (parte A)

Ajustado en A1 para que el rato sin poder crear colegios dure minutos y no
días:

1. **A2 en la rama de Neon**, que incluye probar el backend nuevo en local
   contra la rama con la pantalla de siempre (ver "Paso A2").
2. Aplicar la migración en producción (`tenant_colegio_1` y `tenant_2005`)
   con `apply_migration.py`: `--dry-run`, aplicar y `--dry-run` otra vez, con
   el `DATABASE_URL` **directo** de producción (sin `-pooler`).
3. **En seguida**, push del backend y esperar a que Render quede **Live**.
4. A3 y A4 (frontend), y A5: prueba en local con el Colegio Demo. El backend
   local, ya con la migración en producción, sirve para probar. **Hecho el
   2026-10-21.**
5. Push del frontend. **Hecho el 2026-10-21** (ver "Publicación del
   frontend").

**Aquí la migración va antes del push**, al revés que en SISBÉN y igual que en
Listas de seguimiento. El backend nuevo usa las tablas nuevas en rutas que ya
existen (guardar una nota y borrar un tipo). Si saliera primero, guardar una
nota fallaría a todos los profesores hasta aplicar la migración. Al revés no
hay riesgo: el backend viejo no sabe que esas tablas existen.

**El backend puede salir antes que la pantalla nueva**, y por eso va en el
paso 3 y no al final. Con la pantalla de siempre nadie llama a las rutas
nuevas, la planilla sin `?con_subnotas=true` responde igual, y las dos
consultas nuevas de las rutas viejas no encuentran nada. Lo prueban
`test_subnotas_planilla_caracterizacion.py` y, contra PostgreSQL real, el
paso A2.

**Entre el paso 2 y el 3 no se crean colegios nuevos.** Un colegio nuevo nace
del esquema base del backend publicado, que todavía no trae las tablas, pero
copia el historial de migraciones de la plantilla, que ya marca esta como
aplicada. Quedaría sin las tablas y marcado como si las tuviera. Las altas
solo las hace el super admin.

## Avance del paso A1 (backend), 2026-10-21

Autorizado por el usuario el 2026-10-21, con las propuestas P1 a P12
aprobadas. Al empezar, los dos repos estaban en `main` y limpios: backend
`185d5b6`, frontend `1553574`. No se aplicó ninguna migración ni se accedió a
Neon ni a producción.

**Caracterización primero.** `tests/test_subnotas_planilla_caracterizacion.py`
se escribió y se corrió **antes** de tocar el código, contra la planilla de
siempre, y pasó (3 pruebas). Fija el JSON completo de la planilla sin el
parámetro (con notas, una carita, "Desde React" y un estudiante sin notas), y
lo que escriben en `notas_detalle` guardar una nota a mano y borrar un tipo.
Después del cambio sigue pasando igual.

**Qué se hizo:**

- Migración `migrations/20261021_planilla_subnotas.sql` (escrita, sin
  aplicar), con 6 pruebas de texto en `tests/test_migracion_planilla_subnotas.py`.
- `app/core/valoraciones_desarrollo.py`: la escala de caritas, con la prueba
  gemela de la del frontend.
- `app/core/subnotas_planilla.py`: el cálculo de la celda y el armado de las
  subnotas en la planilla. 41 pruebas en `tests/test_subnotas_planilla_calculo.py`.
- `app/repositories/subnotas_planilla_repository.py`,
  `app/schemas/subnotas_planilla.py`,
  `app/controllers/subnotas_planilla_controller.py` y
  `app/routes/subnotas_planilla.py` (registrado en `app/main.py`). Las cuatro
  rutas, sus reglas y sus conteos tienen 39 pruebas en
  `tests/test_subnotas_planilla.py`, que pasan por la aplicación real.
- En lo existente: `planilla_excel_controller` (el parámetro
  `con_subnotas`), `planilla_controller` (el `409` y el borrado de subnotas
  al borrar un tipo) y `routes/planilla.py` (traduce el `409` y recibe el
  parámetro). `planilla_repository.py` **no cambió**: sus cinco sentencias
  siguen letra por letra, y la celda de un estudiante se escribe con ellas.
- Las cuatro rutas nuevas se sumaron a `tests/test_anio_lectivo_guardia.py`:
  en un año cerrado nadie guarda, el profesor solo guarda en el año activo y
  la guardia mira la clase correcta.

**Decisiones tomadas al escribir el código** (cada una cambia algo del
borrador de A0, ya corregido arriba):

- Las rutas nuevas van en un router propio para que las tres de la planilla
  sigan exactamente como estaban.
- El permiso del profesor se comprueba con el cursor ya abierto: las rutas
  nuevas usan una conexión, no dos como las viejas.
- `PUT` y `DELETE` de una subnota llevan `asignacion_id` (permiso y año, igual
  que las demás), y el tipo que no existe da `404` y no `409`.
- Guardar calificaciones solo toca las subnotas que llegan.
- Dos índices menos que en el borrador: ninguna consulta los usaba.

**Lo que cuesta, antes y después** (admin / profesor; conexiones iguales,
1 y 2):

| Ruta | Antes | Después |
|---|---|---|
| `GET /planilla-excel` sin parámetro | 2 / 3 consultas | igual |
| `GET /planilla-excel?con_subnotas=true` | — | 3 / 4 |
| `POST /planilla/nota` | 6 / 7 | 7 / 8 |
| `DELETE /planilla/tipo` | 3 / 4 | 4 / 5 |

Rutas nuevas, en una sola conexión (admin / profesor): crear 5 / 6, renombrar
3 / 4, borrar 6 / 7 sin calificaciones y 9 / 10 con calificaciones, guardar
8 / 9 o 9 / 10 (según vacíe, escriba o haga las dos). **Ninguna crece con
los estudiantes del curso.**

**Pruebas que cambiaron a propósito**, cada una con su motivo escrito en el
archivo:

- `test_planilla_caracterizacion.py`: la frontera de la planilla pasa de seis
  a once archivos, y los conteos de `POST /planilla/nota` y `DELETE
  /planilla/tipo` suben en una consulta.
- `test_anio_lectivo_guardia_conteos.py`: las mismas dos consultas, en
  `SUBNOTAS`, aparte de las cifras de la guardia.
- `test_planilla_controlador.py`: la comprobación del `409` se dobla como la
  guardia del año.
- Las cinco listas de repositorios (asistencia, dashboard, notas, planilla y
  ventas) suman `subnotas_planilla_repository`, y la de asistencia también su
  total (de 20 a 21).

**Verificación:** `python scripts/verify.py`: **2732 pasan y 1 falla a
propósito**, `test_esquema_base.py`, que reclama solo
`20261021_planilla_subnotas.sql` hasta el A2. Ruff y `pip check` limpios.
`git diff --check` limpio.

## Paso A2: lista de comprobación en una rama de Neon

La hace el usuario; el asistente no se conecta a Neon.

1. En console.neon.tech → Branches → **Create branch** desde `production`,
   con los datos actuales. Nombre sugerido: `prueba-subnotas`.
2. En la rama nueva → **Connect**: copiar la cadena de conexión **directa**
   (con "Connection pooling" apagado; el host no debe tener `-pooler`). No
   pegarla en el chat.
3. En una terminal de PowerShell, en la carpeta del backend. La variable solo
   vive en esa ventana y gana sobre el `.env`:

   ```powershell
   $env:DATABASE_URL = "<cadena directa de la rama>"
   ([uri]$env:DATABASE_URL).Host
   .\venv\Scripts\python.exe apply_migration.py migrations/20261021_planilla_subnotas.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/20261021_planilla_subnotas.sql
   .\venv\Scripts\python.exe apply_migration.py migrations/20261021_planilla_subnotas.sql --dry-run
   ```

   El host que se imprime debe ser el de la rama, **no** el de producción.
   Esperado: `PENDIENTE` → `OK` → `OMITIDA (ya aplicada)` en
   `tenant_colegio_1` y `tenant_2005`.
4. En la misma terminal, regenerar el esquema base desde la rama:

   ```powershell
   .\venv\Scripts\python.exe scripts\generar_esquema_base.py --schema tenant_colegio_1
   ```

   Esperado en el diff: la migración en la cabecera, las dos tablas con sus
   reglas, claves foráneas e índice único, y nada más.
5. **Probar la planilla de siempre contra la rama**, con el backend nuevo. En
   esa misma terminal:

   ```powershell
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

   Con el frontend de siempre (`pnpm run dev`), entrar como profesor del
   **Colegio Demo**, abrir la planilla, crear un tipo de nota "Prueba A2",
   escribir una nota, borrarla y borrar el tipo. Todo debe funcionar como
   siempre: así se comprueba, contra PostgreSQL real, que las dos consultas
   nuevas de las rutas viejas no fallan. Después, detener el servidor y cerrar
   esa terminal.
6. En el SQL Editor de Neon, **con la rama de prueba elegida**, pegar todo
   esto junto y correrlo una vez. Prueba 16 casos en `tenant_colegio_1`,
   incluidas las sentencias que usa la API; cada uno se deshace al instante,
   así que no queda nada guardado. La columna `bien` debe salir `true` en las
   16 filas:

   ```sql
   SET search_path TO tenant_colegio_1, public;

   CREATE TEMP TABLE prueba_subnotas (orden INT, caso TEXT, debe TEXT, obtuvo TEXT);

   DO $$
   DECLARE
       asignacion INTEGER := (SELECT MIN(id) FROM asignaciones);
       estudiante INTEGER := (SELECT MIN(id) FROM estudiantes);
       subnota INTEGER;
       fila RECORD;
   BEGIN
       IF asignacion IS NULL OR estudiante IS NULL THEN
           INSERT INTO prueba_subnotas
           VALUES (0, 'Datos para probar', 'aceptar', 'no se pudo probar: faltan asignaciones o estudiantes');
           RETURN;
       END IF;

       FOR fila IN
           SELECT * FROM (VALUES
               (1, 'Subnota válida', 'aceptar',
                $q$INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Taller 1')$q$),
               (2, 'Nombre repetido con otras mayúsculas', 'idx_planilla_subnotas_nombre_unico',
                $q$INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Taller 1'), ({asig}, 1, ' prueba a2 ', ' taller 1 ')$q$),
               (3, 'Nombre de puros espacios', 'chk_planilla_subnotas_nombre_no_vacio',
                $q$INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', '   ')$q$),
               (4, 'Nombre de 61 caracteres', 'character varying(60)',
                $q$INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', repeat('x', 61))$q$),
               (5, 'Calificación con nota', 'aceptar',
                $q$WITH s AS (INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Quiz') RETURNING id)
                   INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, nota)
                   SELECT id, {est}, 4.5 FROM s$q$),
               (6, 'Calificación con carita', 'aceptar',
                $q$WITH s AS (INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Quiz') RETURNING id)
                   INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, valoracion)
                   SELECT id, {est}, 'logrado' FROM s$q$),
               (7, 'Nota 5.5', 'chk_planilla_subnotas_valores_nota_rango',
                $q$WITH s AS (INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Quiz') RETURNING id)
                   INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, nota)
                   SELECT id, {est}, 5.5 FROM s$q$),
               (8, 'Nota y carita a la vez', 'chk_planilla_subnotas_valores_un_solo_valor',
                $q$WITH s AS (INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Quiz') RETURNING id)
                   INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, nota, valoracion)
                   SELECT id, {est}, 4, 'logrado' FROM s$q$),
               (9, 'Ni nota ni carita', 'chk_planilla_subnotas_valores_un_solo_valor',
                $q$WITH s AS (INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Quiz') RETURNING id)
                   INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id)
                   SELECT id, {est} FROM s$q$),
               (10, 'El mismo estudiante dos veces', 'planilla_subnotas_valores_subnota_id_estudiante_id_key',
                $q$WITH s AS (INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Quiz') RETURNING id)
                   INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, nota)
                   SELECT id, {est}, 4 FROM s UNION ALL SELECT id, {est}, 3 FROM s$q$),
               (11, 'Guardar en lote como la API', 'aceptar',
                $q$WITH s AS (INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
                   VALUES ({asig}, 1, 'Prueba A2', 'Lote') RETURNING id)
                   INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, nota, valoracion)
                   SELECT t.subnota_id, {est}, t.nota, t.valoracion
                   FROM s, UNNEST(ARRAY[s.id]::integer[], ARRAY[4.5]::numeric[], ARRAY[NULL]::varchar[])
                       AS t(subnota_id, nota, valoracion)
                   ON CONFLICT (subnota_id, estudiante_id) DO UPDATE
                   SET nota = EXCLUDED.nota, valoracion = EXCLUDED.valoracion,
                       actualizada_en = CURRENT_TIMESTAMP$q$),
               (12, 'Bloquear como la API', 'aceptar',
                $q$SELECT s.id, v.nota, v.valoracion
                   FROM planilla_subnotas s
                   LEFT JOIN planilla_subnotas_valores v ON v.subnota_id = s.id AND v.estudiante_id = {est}
                   WHERE s.asignacion_id = {asig} AND s.periodo = 1
                     AND LOWER(TRIM(s.tipo_nota)) = LOWER(TRIM('Prueba A2'))
                   ORDER BY s.creada_en, s.id
                   FOR UPDATE OF s$q$),
               (13, 'Comprobar el 409 como la API', 'aceptar',
                $q$SELECT 1 FROM planilla_subnotas s
                   JOIN planilla_subnotas_valores v ON v.subnota_id = s.id
                   WHERE s.asignacion_id = {asig} AND s.periodo = 1
                     AND LOWER(TRIM(s.tipo_nota)) = LOWER(TRIM('Prueba A2'))
                     AND v.estudiante_id = {est}
                   LIMIT 1$q$),
               (14, 'Borrar las subnotas de un tipo como la API', 'aceptar',
                $q$DELETE FROM planilla_subnotas
                   WHERE asignacion_id = {asig} AND periodo = 1
                     AND LOWER(TRIM(tipo_nota)) = LOWER(TRIM('Prueba A2'))$q$),
               (15, 'Rehacer celdas como la API', 'aceptar',
                $q$INSERT INTO notas_detalle (estudiante_id, asignacion_id, periodo, nota,
                       descripcion, tipo_evaluacion, valoracion)
                   SELECT t.estudiante_id, {asig}, 1, t.nota, TRIM('Prueba A2'), t.tipo_evaluacion, t.valoracion
                   FROM UNNEST(ARRAY[{est}]::integer[], ARRAY[NULL]::numeric[],
                               ARRAY['numerica']::varchar[], ARRAY[NULL]::varchar[])
                       AS t(estudiante_id, nota, tipo_evaluacion, valoracion)$q$)
           ) AS c (orden, caso, debe, sentencia)
           ORDER BY orden
       LOOP
           BEGIN
               EXECUTE replace(replace(fila.sentencia, '{asig}', asignacion::text), '{est}', estudiante::text);
               RAISE EXCEPTION 'aceptada';
           EXCEPTION
               WHEN raise_exception THEN
                   INSERT INTO prueba_subnotas VALUES (fila.orden, fila.caso, fila.debe, 'aceptada');
               WHEN OTHERS THEN
                   INSERT INTO prueba_subnotas VALUES (fila.orden, fila.caso, fila.debe, SQLERRM);
           END;
       END LOOP;

       BEGIN
           INSERT INTO planilla_subnotas (asignacion_id, periodo, tipo_nota, nombre)
           VALUES (asignacion, 1, 'Prueba A2', 'Cascada') RETURNING id INTO subnota;
           INSERT INTO planilla_subnotas_valores (subnota_id, estudiante_id, nota)
           VALUES (subnota, estudiante, 4);
           DELETE FROM planilla_subnotas WHERE id = subnota;
           RAISE EXCEPTION 'quedan:%',
               (SELECT count(*) FROM planilla_subnotas_valores WHERE subnota_id = subnota);
       EXCEPTION
           WHEN OTHERS THEN
               INSERT INTO prueba_subnotas
               VALUES (16, 'Borrar una subnota borra sus calificaciones', 'quedan:0', SQLERRM);
       END;
   END
   $$;

   SELECT orden, caso, debe, obtuvo,
          CASE WHEN debe = 'aceptar' THEN obtuvo = 'aceptada'
               ELSE position(debe IN obtuvo) > 0 END AS bien
   FROM prueba_subnotas
   ORDER BY orden;
   ```

   Cómo funciona: cada caso corre en un bloque que, si la base lo acepta, se
   deshace a propósito con `RAISE EXCEPTION 'aceptada'`; si la base lo
   rechaza, también se deshace. Solo queda el resultado en una tabla temporal,
   que desaparece al cerrar la sesión.
7. En el mismo SQL Editor, comprobar que no quedó nada de las pruebas (debe
   dar 0 y 0 en los dos colegios):

   ```sql
   SELECT 'tenant_colegio_1' AS colegio,
          (SELECT count(*) FROM tenant_colegio_1.planilla_subnotas) AS subnotas,
          (SELECT count(*) FROM tenant_colegio_1.notas_detalle
            WHERE LOWER(TRIM(descripcion)) = 'prueba a2') AS celdas_de_prueba
   UNION ALL
   SELECT 'tenant_2005',
          (SELECT count(*) FROM tenant_2005.planilla_subnotas),
          (SELECT count(*) FROM tenant_2005.notas_detalle
            WHERE LOWER(TRIM(descripcion)) = 'prueba a2');
   ```

8. Correr `.\venv\Scripts\python.exe scripts\verify.py`: ahora
   `test_esquema_base.py` debe pasar.
9. Contarle al asistente lo que salió en los puntos 3 a 8, sin cadenas de
   conexión. Con eso se cierra el A2 en este documento y el usuario hace un
   solo commit con migración, esquema base, código y pruebas. Después se puede
   borrar la rama. Lo siguiente es el paso 2 del orden de publicación.

## Avance del paso A2, 2026-10-21

Lo hizo el usuario en la rama `prueba-subnotas` de Neon, creada desde
`production`. El asistente no se conectó a Neon ni a producción.

- **Punto 3, migración en la rama.** La salida del runner no se pegó en el
  chat. En su lugar, el script de comprobación (ver abajo) confirmó en la rama
  que `20261021_planilla_subnotas.sql` quedó registrada en
  `public.schema_migrations` para `tenant_colegio_1` y `tenant_2005`, y que las
  dos tablas existen en los dos colegios.
- **Punto 4, esquema base** regenerado desde `tenant_colegio_1` de la rama: 38
  tablas (eran 36), 1 función y 1 disparador. El diff, revisado línea por
  línea, trae solo la fecha, la cabecera (de 45 a 46 migraciones), las dos
  tablas con sus `CHECK`, `PRIMARY KEY` y `UNIQUE`, el índice
  `idx_planilla_subnotas_nombre_unico` y las tres claves foráneas
  (`asignacion_id` y `subnota_id` con `ON DELETE CASCADE`, `estudiante_id`
  sin cascada). Nada más.
- **Punto 5, la planilla de siempre contra la rama.** Con el backend nuevo en
  local apuntando a la rama y el frontend de siempre, el usuario entró como
  profesor del Colegio Demo: crear un tipo, escribir y borrar una nota
  funcionó igual que siempre. Así quedó probado, contra PostgreSQL real, que
  la consulta nueva de `POST /planilla/nota` no falla.
- **Puntos 6 y 7.** El usuario pidió que el asistente los hiciera. Como el
  asistente no tiene la conexión de la rama (ni debe pedirla), escribió un
  script para que el usuario lo corriera en su terminal. El script queda fuera
  del repo, en la carpeta temporal del asistente. Se niega a correr sin
  `DATABASE_URL` o con el endpoint de producción, usa los dos bloques SQL de
  "Paso A2" tal cual y lo deshace todo al final.
  - Primera corrida: los 16 casos `OK`. Quedaba **una celda** "Prueba A2" en
    `tenant_colegio_1`: el tipo creado en el punto 5, que todavía no se había
    borrado.
  - El usuario borró ese tipo desde la planilla, con el backend nuevo contra
    la rama. Segunda corrida: **TODO BIEN**, con 0 subnotas y 0 celdas de
    prueba en los dos colegios. Eso prueba también que borrar un tipo con el
    código nuevo (`DELETE /planilla/tipo`, más su consulta nueva) no deja nada
    atrás.
- **Punto 8.** `scripts/verify.py`: **2733 pasan, 0 fallan**, con
  `test_esquema_base.py` ya en verde. Ruff y `pip check` limpios.
- Producción **no se tocó** durante el A2: ni migración, ni push.

## Publicación del backend, 2026-10-21

Pasos 2 y 3 del orden de publicación. Los hizo el usuario; el asistente no se
conectó a la base de producción.

- **Migración en producción.** En la terminal del usuario, el host que usa el
  runner (el de la terminal o, si no hay, el del `.env`) empieza por
  `ep-late-smoke-aip41j6x`, que es producción. La simulación posterior dio
  `OMITIDA (ya aplicada)` en `tenant_colegio_1` y `tenant_2005`. La salida del
  comando que aplicó no se pegó en el chat. Aun así, el runner, en cada
  colegio, ejecuta la migración y guarda su registro en la misma transacción
  (`apply_migration.py`), así que el registro con el mismo checksum prueba que
  las tablas se crearon.
- **Push del backend** por el usuario: `origin/main` en `e36f976` (subió
  también `185d5b6`).
- **Render Live**, comprobado por el asistente desde fuera y sin sesión: antes
  del push, `POST /planilla/subnotas` respondía `405` (ese camino solo
  coincidía con `GET /planilla/{asignacion_id}`). Después respondió `401`: la
  ruta nueva existe y pide sesión. `/health` siguió en `200`.
- Con eso se cerró el rato sin poder crear colegios.

## Publicación del frontend, 2026-10-21

Paso 5 del orden de publicación. El push lo hizo el usuario; el asistente no
entró a Vercel ni a la página publicada.

- **Push del frontend**: `origin/main` en `3fb9831`. Subió A3 (`12c2067`), A4
  (`d58fb0e` y `5f9f1b1`) y el cierre de A5 (`3fb9831`).
- **Vercel**, comprobado por el asistente en GitHub (`gh api .../deployments`):
  el despliegue de `Production` del commit `3fb9831` quedó en `success`. Es el
  mismo código que pasó `check:deploy` al cerrar A5 (2902 pruebas, lint y
  build).
- **Con esto la parte A queda publicada**: los profesores ya ven el botón de
  subnotas en la planilla.

## Parte B — Porcentajes por tipo de nota (esbozo; se diseña en B0)

El diseño detallado está en "Avance del paso B0" (inventario, preguntas QB1 a
QB4 y propuestas PB1 a PB10). Este esbozo se conserva como punto de partida.

Lo que ya se sabe:

- El porcentaje se pone al crear el tipo (decisión 2) y debe poder editarse
  después, también en los tipos que ya existen.
- Los tipos de nota no tienen tabla propia, así que B necesita una migración
  aparte. Una migración ya aplicada no se puede editar: el runner guarda su
  checksum.
- Regla base propuesta: **sin porcentajes, todo da idéntico a hoy.** Con
  porcentajes, la suma no pasa de 100 %, y un tipo sin nota para ese
  estudiante no cuenta: su peso se reparte entre los que sí tiene, igual que
  hoy no cuenta una celda vacía.
- **Para que la nota sea la misma en todos lados, el cálculo con porcentajes
  vive en un solo lugar del servidor** y lo usan todos los que hoy calculan la
  nota del periodo como promedio simple. Inventario inicial (B0 lo confirma
  con `grep`):

  | Dónde se ve | Dónde se calcula hoy |
  |---|---|
  | Promedio de la planilla | `planilla_excel_controller.py` y, en el frontend, `utils/planilla/notas.js` |
  | Definitiva que propone el boletín del profesor | frontend, `utils/boletines/ingresoBoletin.js` |
  | Boletín del admin sin definitiva guardada | `boletin_repository.leer_materias_del_estudiante` (`AVG` en SQL) |
  | Reporte parcial | `boletin_controller.obtener_reporte_parcial_admin_controller` |
  | Tableros | `dashboard_repository` (tres consultas) |
  | Ficha del estudiante | `estudiantes_repository.leer_promedios_por_materia` |
  | Otras lecturas | `notas_repository.leer_boletin_de_estudiante` y `leer_planilla_de_asignacion` |

- Esos lugares ya hoy no calculan igual entre sí: unos descartan `nota > 0`,
  la ficha redondea a un decimal y los tableros truncan. B0 decide con el
  usuario si se igualan o si se conserva cada diferencia.
- El puesto del curso sale de la definitiva guardada en `boletin_cabecera`.
  Cambia solo cuando el profesor vuelve a guardar el boletín, igual que hoy al
  corregir una nota después de guardarlo.

Pasos previstos: **B0** diseño detallado e inventario, **B1** caracterización
de cada lugar de la tabla, **B2** backend y migración, **B3** base de datos (lo
hace el usuario), **B4** frontend y **B5** prueba en local. La publicación
sigue el mismo orden que la parte A.

## Avance del paso B0, 2026-10-21 (hecho; propuestas aprobadas)

Autorizado por el usuario el 2026-10-21 ("autorizas empezar B0" → "si"), con
la parte A ya publicada. Al empezar, los dos repos estaban en `main` y
limpios: backend `4dd0274`, frontend `05d6e10`. B0 es solo diseño: sin
código, sin base de datos y sin publicar.

### Inventario confirmado (`grep` en los dos repos)

Dónde se calcula hoy la nota de una materia en un periodo a partir de las
celdas de la planilla:

1. **Promedio de la planilla.** El servidor lo calcula en
   `planilla_excel_controller.py` (promedio simple de las celdas numéricas,
   `round(…, 2)`, incluye la columna interna `mas_alto`), pero **la pantalla
   no lo usa**: lo recalcula en `utils/planilla/notas.js`
   (`calcularPromedioEstudiante`, sin `mas_alto`, con caritas si las hay).
2. **Definitiva del boletín del profesor: la nota oficial.** La calcula **el
   frontend** (`utils/boletines/ingresoBoletin.js: crearDatosBoletinInicial`,
   promedio simple sin `mas_alto`; en preescolar, el de las caritas) y la
   envía en `construirPayloadBoletin`. El profesor no puede cambiarla: la
   pantalla solo la muestra (`VistaIngresoBoletinProfesor.jsx`). **El
   servidor la guarda tal como llega** (`guardar_boletin_controller` →
   `boletin_cabecera.definitiva`), sin recalcularla. De ella salen el
   boletín impreso, los certificados y el puesto.
3. **Puesto del curso**: promedio de las definitivas guardadas de todas las
   materias (`boletin_repository.leer_puesto_en_el_curso`). No promedia
   celdas: cambia solo si cambia la definitiva guardada.
4. **Boletín del admin sin definitiva guardada**:
   `boletin_repository.leer_materias_del_estudiante`, `AVG` en SQL del
   periodo, sin caritas y solo `nota > 0`.
5. **Reporte parcial**: `boletin_controller.obtener_reporte_parcial_admin_controller`,
   en Python, sin caritas, solo `nota > 0`, sin redondear.
6. **Certificados (respaldo en pantalla)**: `utils/certificadosImpresion/certificados.js:
   getDefinitiva` promedia los detalles (`nota > 0`) solo si la materia llega
   sin definitiva.
7. **Tableros del profesor**:
   - `dashboard_repository.leer_estudiantes_por_promedio` (tarjetas de mejor
     y bajo rendimiento): promedio de los promedios por clase, **de todos los
     periodos**, truncado a dos decimales;
   - `leer_ranking_bajo_rendimiento` y `leer_ranking_mejor_rendimiento`
     (páginas de ranking): promedio plano de las celdas **de una clase y un
     periodo**, truncado a dos decimales.
8. **Ficha del estudiante (admin)**: `estudiantes_repository.leer_promedios_por_materia`,
   promedio de todas las celdas **del año** por materia, redondeado a un
   decimal; el promedio general lo saca el controlador promediando esos
   promedios.
9. **Rutas viejas de `notas_repository`**: `GET /boletin/{id}`
   (`leer_boletin_de_estudiante`) no la usa ninguna pantalla. `GET
   /planilla/{id}` (`leer_planilla_de_asignacion`) la usa el Observador solo
   para la lista de estudiantes (`usePlanillaObservador`): no muestra el
   promedio.

Los promedios entre materias del boletín impreso
(`utils/boletines/generacionBoletin.js`) y de los certificados
(`promedioMaterias`) parten de las definitivas: los porcentajes les llegan
solos, sin tocarlos.

**Hallazgo principal para el diseño:** hoy la nota oficial (punto 2) la
decide el frontend y el servidor no la revisa. La regla de esta
funcionalidad es que el frontend no decide la nota. Con porcentajes, B0
debe proponer que el servidor la calcule.

### Preguntas al usuario (una por una)

Se anotan aquí con su respuesta a medida que se contestan.

- **QB1. ¿Preescolar también lleva porcentajes?** **Sí, igual que primaria**
  (usuario, 2026-10-21). Las caritas se pasan a número con la escala de
  siempre, se ponderan y el resultado vuelve a la carita más cercana (empate,
  la más alta), como en P8.
- **QB2. ¿Qué pasa si algunos tipos tienen porcentaje y otros no?** **Todo
  o nada** (usuario, 2026-10-21). Los porcentajes solo cuentan cuando todos
  los tipos de esa clase y periodo tienen el suyo y suman 100 %. Mientras
  falte alguno, se usa el promedio simple de hoy y la planilla avisa "Faltan
  porcentajes: se usa el promedio simple". Así un periodo ya empezado sigue
  igual hasta que el profesor complete los porcentajes.
- **QB3. ¿Qué pantallas usan los porcentajes?** **Solo las que muestran la
  nota de un periodo** (usuario, 2026-10-21): planilla, boletín (definitiva y
  respaldo del admin), reporte parcial, certificados y las páginas de ranking
  del profesor (mejor y bajo rendimiento de una clase en un periodo). Las
  tarjetas del tablero (`leer_estudiantes_por_promedio`) y la ficha del
  estudiante, que mezclan todo el año, siguen como hoy.
- **QB4. ¿Se igualan los promedios que hoy difieren entre pantallas?** **No,
  se dejan como están** (usuario, 2026-10-21). Sin porcentajes activos, cada
  lugar del inventario da exactamente lo de hoy, con sus diferencias
  (redondeo, `nota > 0`, `mas_alto`). Con porcentajes activos, todos los
  lugares de QB3 usan el mismo cálculo del servidor (PB4). Así ninguna nota
  ya entregada cambia sola.

### Propuestas de B0 (aprobadas por el usuario el 2026-10-21)

Cierran lo que las respuestas no cubren. **El usuario las aprobó todas el
2026-10-21**, incluida la consecuencia de PB10. Aprobarlas no autoriza B1:
cada paso necesita su propia autorización.

**Definición.** En una clase y un periodo, los porcentajes están **activos**
cuando cada tipo de nota de la planilla tiene el suyo y suman exactamente
100 % (QB2). Las columnas internas (`mas_alto`, `Desde React`) no llevan
porcentaje ni cuentan, igual que no admiten subnotas (P11).

- **PB1. Dónde se guardan.** Tabla nueva `planilla_tipos_porcentaje`: `id`,
  `asignacion_id` (FK a `asignaciones` `ON DELETE CASCADE`, siempre la
  asignación académica ya resuelta), `periodo`, `tipo_nota` (`varchar(100)`,
  el mismo texto de `notas_detalle.descripcion`), `porcentaje` y
  `actualizado_en`. Índice único `(asignacion_id, periodo,
  LOWER(TRIM(tipo_nota)))`. Es por clase y periodo porque los tipos de nota
  son de un periodo. Ninguna tabla existente cambia. Un tipo sin porcentaje no
  tiene fila.
- **PB2. Porcentajes enteros de 1 a 100** (`smallint` con `CHECK`). Sin
  decimales: tres tipos iguales son 33 + 33 + 34. Así el profesor no tiene
  que escribir 33,33.
- **PB3. La suma nunca pasa de 100.** El servidor rechaza con `422` el
  porcentaje que la haría pasar. Mientras sume menos o falte algún tipo, se
  usa el promedio simple de hoy (QB2).
- **PB4. Un solo cálculo, en el servidor**: `app/core/nota_periodo.py`
  (nuevo, puro, con pruebas propias). Promedio ponderado de las celdas con
  valor: suma de (nota × porcentaje) dividida por la suma de los porcentajes
  de los tipos que sí tienen nota. Un tipo sin nota para ese estudiante no
  cuenta y su peso se reparte entre los demás (esbozo). Sin ninguna celda,
  vacía. Redondeo a dos decimales mitad hacia arriba, como P7. Caritas como
  QB1. Ejemplos que deben quedar probados: Cognitivo 50 % con 4.0,
  Procedimental 30 % con 3.0 y Actitudinal 20 % con 5.0 dan **3.90**; sin la
  nota de Actitudinal, (2.0 + 0.9) / 0.8 = 3.625 → **3.63**. El frontend
  tiene la gemela para la vista previa, con los mismos casos.
- **PB5. Con porcentajes activos, la definitiva la calcula el servidor.** Al
  guardar el boletín, si los porcentajes de esa clase y periodo están
  activos, el servidor calcula la definitiva con PB4 y guarda esa, **no la
  que envía la pantalla**. Si no están activos, guarda la que llega, como hoy
  (QB4). La lectura del boletín del profesor agrega la definitiva calculada
  solo cuando están activos, para que la pantalla muestre exactamente la que
  se va a guardar. Es la regla de esta funcionalidad: el frontend no decide
  la nota.
- **PB6. El puesto no cambia su fórmula.** Sale de las definitivas
  guardadas, así que cambia cuando el profesor vuelve a guardar el boletín.
  Cambiar los porcentajes después de guardar el boletín no cambia la
  definitiva guardada hasta volver a guardarlo, igual que hoy al corregir una
  nota. No se recalculan boletines ya guardados.
- **PB7. Las lecturas de QB3 cambian solo con porcentajes activos**: el
  boletín del admin sin definitiva (`leer_materias_del_estudiante`), el
  reporte parcial, los dos rankings por clase y periodo y el promedio de la
  planilla. Con porcentajes activos usan PB4; sin ellos, su fórmula de hoy
  sin cambiar ni una letra. Los certificados reciben la definitiva del
  boletín del admin, así que no se tocan. Cada una lee los porcentajes con
  una consulta más por petición, nunca una por estudiante; B1 lo mide antes
  y después.
- **PB8. Rutas.**
  - `PUT /planilla/tipos/porcentaje` con `{ asignacion_id, periodo,
    tipo_nota, porcentaje }` (`null` lo quita). Responde `{ tipo_nota,
    porcentaje, suma, activos }`. `404` si el tipo no está en la planilla;
    `422` si no es un entero de 1 a 100, si la suma pasaría de 100 o si es
    una columna interna. Mismas guardias que la planilla (permiso, año
    lectivo, asignación académica).
  - `GET /planilla-excel/...?con_porcentajes=true` agrega `porcentajes: {
    "<tipo_nota>": 40 }` y `porcentajes_activos`. Sin el parámetro, la
    respuesta es idéntica a la de hoy (Asistencia no cambia). Es un parámetro
    aparte de `con_subnotas` porque son cosas distintas; la planilla del
    profesor manda los dos.
  - **Crear un tipo no cambia**: sigue siendo `POST /planilla/nota` con `nota:
    null`. Si el profesor escribió un porcentaje, la pantalla llama después
    a la ruta nueva. Si esa segunda llamada falla, el tipo queda sin
    porcentaje y el aviso de PB9 lo muestra; no se pierde nada.
- **PB9. Pantalla de la planilla.** Al crear un tipo, un campo opcional
  "Porcentaje (%)". En el encabezado de cada columna, su porcentaje
  ("Cognitivo · 40 %") y la forma de cambiarlo. Encima de la tabla, la suma
  ("Porcentajes: 70 % de 100 %") y, mientras no estén activos, el aviso
  "Faltan porcentajes: se usa el promedio simple". Con porcentajes activos,
  la columna Promedio muestra el ponderado. En una clase sin ningún
  porcentaje, la planilla se ve como hoy, sin aviso. El boletín del profesor
  no cambia de aspecto: solo muestra la definitiva que manda el servidor
  (PB5).
- **PB10. Borrar un tipo borra su porcentaje** en la misma operación
  (`DELETE /planilla/tipo`), como P6. **Consecuencia que el usuario debe
  conocer:** con porcentajes activos, agregar un tipo nuevo o borrar uno deja
  la suma incompleta, y la clase vuelve al promedio simple, con el aviso,
  hasta que el profesor ajuste los porcentajes. Es lo que pide "todo o nada"
  (QB2).

- **PB11. Aviso al guardar el boletín con porcentajes incompletos**
  (propuesto por el asistente y **aprobado por el usuario el 2026-10-22**,
  durante B5). El usuario preguntó si bloquear el ingreso de notas mientras
  falte un porcentaje. Se descartó: frenaría el trabajo diario del profesor,
  bloquearía también crear tipos (crear un tipo guarda una nota vacía) y,
  para ser real, exigiría cambiar `POST /planilla/nota` en producción. El
  riesgo de verdad es guardar la nota oficial sin darse cuenta de que es el
  promedio simple. Por eso, al guardar el boletín de una clase con
  porcentajes incompletos, la pantalla pregunta "Los porcentajes de esta
  clase están incompletos: la definitiva es el promedio simple. ¿Guardar
  igual?". Las notas se siguen ingresando libres. **Solo frontend** (paso
  B4c); no cambia el servidor.

**Riesgo: alto.** PB5 y PB7 tocan la nota oficial. Por eso B1 (caracterización
de cada lugar de PB7, de guardar el boletín y de la lectura del boletín del
profesor, sin porcentajes) va antes de cambiar nada, igual que en A1.

**Orden de publicación**: el mismo de la parte A. Primero la migración en
producción y en seguida el push del backend, porque el backend nuevo lee la
tabla nueva en rutas que ya existen (borrar un tipo, guardar y leer el
boletín, rankings). Entre esos dos pasos no se crean colegios nuevos. Después
B4 y B5, y por último el push del frontend.

**Fuera de alcance de B:** porcentajes en las tarjetas del tablero y en la
ficha (QB3), igualar las diferencias de hoy (QB4), recalcular boletines ya
guardados (PB6), copiar porcentajes de un periodo a otro y porcentajes dentro
de las subnotas de un tipo (decisión 2).

## Avance del paso B1 (caracterización), 2026-10-21

Autorizado por el usuario el 2026-10-21: a "¿Autorizas empezar B1?" respondió
"sigue". Al empezar, los dos repos estaban en `main` y limpios: backend
`e2bc4d0`, frontend `6044d3a`. **No se tocó el código de la aplicación** ni
la base de datos: solo se agregaron pruebas. Todas se corrieron contra el
programa de hoy y pasaron, que es lo que se busca: dejan fijado lo que existe
antes de cambiarlo.

**Backend: `tests/test_porcentajes_planilla_caracterizacion.py`, 15
pruebas.**

- **El SQL de siete consultas, letra por letra** (PB7: "sin cambiar ni una
  letra"): el respaldo del boletín del admin (`AVG`, sin caritas, `nota >
  0`), las celdas del reporte parcial, las celdas que lee el boletín del
  profesor, el puesto (PB6), la cabecera que guarda la definitiva y los dos
  rankings (`TRUNC`). Se sacaron del código ejecutándolo, no copiándolo a
  mano.
- **Guardar el boletín guarda la definitiva tal como llega**: 4.5,
  3.6666…, 4.3333… (caritas) y `None`, con las mismas cuatro escrituras.
- **La lectura del boletín del profesor devuelve el JSON de hoy**, sin
  `definitiva` (PB5 solo la agrega con porcentajes activos). Incluye la
  columna interna `mas_alto`, que la pantalla oculta.
- **El boletín del admin** entrega la definitiva que sale del SQL sin
  redondear, y `None` si no hay ninguna.
- **El reporte parcial** cuenta `mas_alto` en la definitiva y deja `None` la
  materia sin notas.
- **El promedio que el servidor calcula para la planilla** redondea como
  `round` de Python (al par: 3.625 → 3.62, 4.125 → 4.12) y cuenta `mas_alto`.
- El cursor de prueba responde según el texto del SQL y, a cualquier consulta
  que no conoce, "nada". Así la consulta nueva de B2 que lea los porcentajes,
  sin encontrar ninguno, no rompe estas pruebas: es justo el caso "sin
  porcentajes".

**Frontend: 4 pruebas** en `utils/planilla/notas.test.js` y
`utils/boletines/ingresoBoletin.test.js`: la pantalla sube los empates
exactos (3.625 se ve 3.63 y 4.125 se ve 4.13), no cuenta `mas_alto`, la
definitiva numérica sale "3.63" y viaja como 3.63, y la de caritas viaja sin
redondear (13/3).

**Lo que ya estaba fijado y no se repitió**: los conteos de consultas y
conexiones (`test_boletin_caracterizacion.py`,
`test_dashboard_caracterizacion.py`), que el reporte parcial no redondea y
deja fuera caritas y ceros, la respuesta de los rankings
(`test_dashboard_controlador.py`) y la planilla sin parámetro
(`test_subnotas_planilla_caracterizacion.py`).

**Línea base de consultas (el "antes" de B2)**, según esos archivos:

| Lectura o escritura | Hoy |
|---|---|
| Boletín del admin | 4 consultas, 1 conexión |
| Reporte parcial | 2 consultas, 1 conexión |
| Lectura del boletín del profesor | 2 consultas propias más la que resuelve la asignación |
| Guardar el boletín | 4 + 1 por detalle, más la guardia del año |
| Ranking (admin / profesor) | 2 / 3 consultas; 1 / 2 conexiones |
| Planilla sin parámetro (admin / profesor) | 2 / 3 consultas |

**Hallazgos** (se conservan, QB4):

- El promedio que el servidor calcula para la planilla (3.62) no es el que ve
  el profesor (3.63): la pantalla no usa el del servidor y lo recalcula con
  `toFixed`, que sube los empates exactos. **La regla de PB4 (mitad hacia
  arriba) coincide con lo que el profesor ya ve.**
- La definitiva de caritas viaja sin redondear, pero la columna
  `boletin_cabecera.definitiva` es `numeric(5,2)`: PostgreSQL la guarda con
  dos decimales (4.3333… queda 4.33).
- `mas_alto` cuenta en el reporte parcial, en los rankings y en el promedio
  del servidor, pero no en la planilla ni en el boletín del profesor que ve la
  pantalla.

**Verificación:** ver "Entrega para el siguiente chat".

## Avance del paso B2 (backend), desde el 2026-10-22

Autorizado por el usuario el 2026-10-22 ("continúa la siguiente fase"), sin
el botón para apagar los porcentajes de una vez: el diseño queda como se
aprobó, y para dejar de usarlos se quitan uno por uno. Al empezar, los dos
repos estaban en `main` y limpios: backend `a9cdc57`, frontend `f6b22f6`.

**B2 se hace en cuatro partes, con el visto bueno del usuario antes de cada
una.** Es lo que el usuario pide en los pasos grandes: saber antes qué
archivos cambian y a qué afectan. Además B2 llega a la nota oficial.

- **B2a — El cálculo, solo.** `app/core/nota_periodo.py` y sus pruebas.
  Nadie lo llama todavía. **Hecho el 2026-10-22, sin commit.**
- **B2b — Guardar y ver los porcentajes.** La migración (escrita, sin
  aplicar), el repositorio, `PUT /planilla/tipos/porcentaje`, `GET
  /planilla-excel?con_porcentajes=true` y el borrado del porcentaje al borrar
  un tipo (PB10). Cambia `DELETE /planilla/tipo` (una consulta más).
  `test_esquema_base.py` fallará a propósito desde aquí hasta B3. **Hecho el
  2026-10-22, sin commit.**
- **B2c — El boletín del profesor (zona sensible).** Guardar el boletín
  calcula la definitiva en el servidor con porcentajes activos (PB5), y la
  lectura del boletín del profesor la agrega. **Hecho el 2026-10-22, sin
  commit.**
- **B2d — Las demás lecturas.** El boletín del admin sin definitiva, el
  reporte parcial y los dos rankings (PB7). **Hecho el 2026-10-22, sin
  commit. Con esto B2 está completo.**

### B2a, 2026-10-22

- `app/core/nota_periodo.py` (nuevo, puro): los límites (PB2), cuándo están
  activos (QB2, todo o nada; los tipos se comparan sin mayúsculas ni
  espacios; las columnas internas no cuentan; el porcentaje de un tipo que ya
  no existe tampoco), la suma y la nota ponderada en primaria y en preescolar
  (PB4, QB1). Reutiliza de la parte A el redondeo y la validación de la nota
  (`normalizar_nota`), las columnas internas (`admite_subnotas`) y la escala
  de caritas, para que las dos partes redondeen igual.
- `tests/test_nota_periodo.py`, **46 pruebas**, escritas antes que el módulo
  (fallaron porque no existía y después pasaron). Fijan los ejemplos de B0
  (3.90 y 3.63), el redondeo mitad hacia arriba (4.125 → 4.13, 1.005 →
  1.01), 33 + 33 + 34, caritas con y sin empate, y que una nota fuera de 1 a
  5 no cuenta.
- **Hallazgo:** con porcentajes enteros que suman hasta 100, el promedio
  ponderado nunca cae entre x.495 y x.5 (la fracción más cercana por debajo
  de un medio es 49/99 = 0.4949…). Por eso redondear antes o después no
  cambia nunca la carita. El módulo usa igual el promedio exacto, y la
  prueba del casi empate (445/99 = 4.49, logrado) lo deja fijado.
- Ningún archivo existente cambió. Nada lo llama todavía: lo que ven los
  profesores no cambia.
- **Verificación:** `scripts/verify.py`, **2794 pasan** (eran 2748), 0
  fallan; Ruff y `pip check` limpios. Frontend sin cambios de código:
  `check:deploy` con 2906 pruebas, lint y build correctos. Corridas una tras
  otra. `git diff --check` limpio en los dos.
- En el commit `a630183`.

### B2b, 2026-10-22

Visto bueno del usuario el 2026-10-22 ("continua", respuesta a "¿Le das el
visto bueno a B2b?"). Al empezar, backend en `a630183` y limpio. Las pruebas
se escribieron antes que el código y fallaron porque faltaba; después
pasaron.

**Qué se hizo:**

- Migración `migrations/20261022_planilla_tipos_porcentaje.sql` (**escrita,
  sin aplicar**), con 5 pruebas de texto en
  `tests/test_migracion_planilla_tipos_porcentaje.py`. Es PB1 tal cual, y el
  `ON CONFLICT` del repositorio nombra las mismas columnas que el índice único.
- `app/repositories/porcentajes_planilla_repository.py`: leer los
  porcentajes, leer los tipos de la planilla, bloquear la clase, guardar
  (`INSERT … ON CONFLICT`) y quitar. Una sentencia cada una.
- `app/schemas/porcentajes_planilla.py`, `app/controllers/porcentajes_planilla_controller.py`
  y `app/routes/porcentajes_planilla.py` (registrado en `app/main.py`):
  `PUT /planilla/tipos/porcentaje`, con los errores en español y las mismas
  guardias de las subnotas, en una sola conexión.
- `app/core/nota_periodo.py` suma `armar_porcentajes_de_planilla` (3 pruebas
  más en `test_nota_periodo.py`).
- En lo existente: `planilla_excel_controller` y `routes/planilla.py`
  (parámetro `con_porcentajes`; sin él, la misma llamada de siempre) y
  `planilla_controller.eliminar_tipo_controller` (quita el porcentaje, PB10).
- `tests/test_porcentajes_planilla.py`, **24 pruebas por la aplicación
  real**: guardar, cambiar, quitar con `null`, la suma que pasa de 100, el
  porcentaje de un tipo que ya no existe, 404, 422 sin abrir la base (columna
  interna, 0, 101, 33.5, texto, booleano, sin el campo), 403 de un profesor
  ajeno, la planilla con y sin el parámetro, y borrar el tipo.
- La ruta nueva se sumó a `tests/test_anio_lectivo_guardia.py`: en un año
  cerrado nadie guarda porcentajes.

**Decisiones al escribir el código** (no cambian ninguna regla aprobada):

- **La suma se cuida con la clase bloqueada.** Antes de leer los porcentajes,
  la ruta bloquea la fila de la asignación (`FOR NO KEY UPDATE`). Si dos
  pestañas guardan a la vez, la segunda espera y ve la suma que dejó la
  primera. Ese tipo de bloqueo no detiene el guardado de notas de esa clase.
- **`porcentaje` es obligatorio aunque sea `null`**, para que quitar uno sea
  siempre a propósito. Un `true` o un "40" no son porcentaje; 33.5, 0 y 101
  reciben el mensaje en español "El porcentaje debe ser un número entero de 1
  a 100."
- **El tipo se guarda con el nombre de su columna** en la planilla, aunque
  llegue con otras mayúsculas o espacios, igual que en la respuesta.

**Lo que cuesta** (admin / profesor; ninguna conexión de más):

| Ruta | Antes | Después |
|---|---|---|
| `GET /planilla-excel` sin parámetro | 2 / 3 | igual |
| `GET /planilla-excel?con_porcentajes=true` | — | 3 / 4 |
| `DELETE /planilla/tipo` | 4 / 5 | 5 / 6 |
| `PUT /planilla/tipos/porcentaje` | — | 6 / 7 |

**Pruebas que cambiaron a propósito**, cada una con su motivo:

- `test_planilla_caracterizacion.py`: la frontera de la planilla pasa de once
  a quince archivos, y el coste de `DELETE /planilla/tipo` sube una consulta.
- `test_anio_lectivo_guardia_conteos.py`: la misma consulta, en
  `PORCENTAJES`, aparte de las cifras de la guardia.
- Las cinco listas exactas de repositorios (asistencia, dashboard, notas,
  planilla y ventas) suman `porcentajes_planilla_repository`; la de asistencia
  también su total (de 21 a 22).

**Documentos:** `docs/API_ENDPOINTS.md`, `docs/BASE_DATOS.md`,
`docs/MIGRACIONES.md` y `docs/CAMBIOS_BACKEND.md`.

**Verificación:** ver "Entrega para el siguiente chat".

### B2c, 2026-10-22

Visto bueno del usuario el 2026-10-22 ("si continua", respuesta a "¿Le das
el visto bueno a B2c?"). Al empezar, backend en `dcf8443` y limpio. Las
pruebas se escribieron antes que el código y fallaron porque faltaba.

**Qué se hizo** (solo `app/controllers/boletin_controller.py` en lo que ya
existía):

- **Guardar el boletín** (`POST /boletines/guardar`): antes de escribir la
  cabecera pregunta si la clase tiene porcentajes. Con porcentajes activos,
  lee las celdas del estudiante, calcula la definitiva con
  `app/core/nota_periodo.py` y guarda esa. Sin porcentajes activos guarda la
  que llega, como hoy.
- **Lectura del boletín del profesor** (`GET /boletines/referencia/...`): al
  final pregunta lo mismo. Con porcentajes activos agrega `definitiva` a cada
  estudiante con notas, calculada con las celdas que ya leyó (solo consulta,
  además, el nivel del curso). Es exactamente la que se guardará.
- `porcentajes_planilla_repository`: `leer_celdas_del_estudiante`, y las tres
  lecturas devuelven tuplas también con un cursor de diccionarios (la lectura
  del profesor usa `RealDictCursor`).
- `nota_periodo.tipo_de_evaluacion_de_celdas` (4 pruebas más).
- `tests/test_porcentajes_boletin.py`, **15 pruebas**: sin porcentajes,
  incompletos y activos al guardar y al leer; celda vacía y columna interna;
  caritas con nivel y sin nivel; el nivel de primaria que manda sobre una
  carita vieja; estudiante sin notas; y el repositorio con cursor de
  diccionarios. **Las 15 pruebas de B1 siguen pasando sin tocarlas**: sin
  porcentajes, el boletín guarda y devuelve lo mismo de antes.

**Decisiones al escribir el código** (cambio mínimo; ninguna cambia una regla
aprobada):

- **De qué tipo es la materia.** La pantalla no manda el tipo de evaluación de
  la materia (el servidor asumía "numerica"). Manda el nivel del curso; sin
  nivel, las celdas, con la misma regla de la pantalla
  (`esEvaluacionDesarrollo`: es de caritas si alguna celda lo es).
- **Estudiante sin notas con porcentajes activos:** se guarda lo que manda la
  pantalla, como hoy (0 en numérica, vacío en caritas). El cálculo ponderado
  no tiene nada que decir, y así el puesto de ese estudiante no cambia. La
  lectura no le agrega `definitiva`, y la pantalla usa la suya.
- **No se bloquea nada al guardar el boletín.** Si alguien cambia los
  porcentajes justo mientras otro guarda, ese boletín queda con los de un
  instante antes; el siguiente guardado usa los nuevos. Es lo mismo que pasa
  hoy al corregir una nota después de guardar (PB6).

**Lo que cuesta** (sin conexiones de más):

| Ruta | Sin porcentajes | Incompletos | Activos |
|---|---|---|---|
| `POST /boletines/guardar` | +1 consulta | +2 | +3 (porcentajes, tipos y celdas) |
| `GET /boletines/referencia/...` | +1 | +2 | +3 (porcentajes, tipos y nivel) |

**Pruebas que cambiaron a propósito:**

- `test_boletin_caracterizacion.py`: la pregunta por los porcentajes se dobla
  con "no hay", igual que ya se doblaba la guardia del año, para que no sume
  en sus conteos. Sus conteos y posiciones no cambiaron.
- `test_anio_lectivo_guardia_conteos.py`: `POST /boletines/guardar` suma esa
  consulta en `PORCENTAJES`.

### B2d, 2026-10-22

Visto bueno del usuario el 2026-10-22 ("si esta bien continua", respuesta a
"¿Le das el visto bueno a B2d?"). Al empezar, backend en `05a8bbe` y limpio.
Las pruebas se escribieron antes que el código y fallaron porque faltaba.

**Qué se hizo:**

- `app/services/porcentajes_activos.py` (nuevo): qué clases tienen sus
  porcentajes activos, para una clase o para varias en una sola consulta. La
  función de B2c que respondía eso para una clase **se movió aquí** desde
  `boletin_controller.py`: así los cinco lugares que cambian con porcentajes
  usan la misma regla y no hay dos copias.
- `porcentajes_planilla_repository`: cuatro lecturas más (porcentajes y tipos
  de varias clases, celdas de un estudiante en varias clases y celdas de toda
  una clase).
- **Boletín del admin** (`obtener_boletin_admin_controller`): la materia
  **sin boletín guardado** cuya clase tiene porcentajes activos usa la nota
  ponderada en vez del promedio simple de respaldo. La que tiene boletín
  guardado conserva su definitiva (PB6).
- **Reporte parcial**: cada materia cuya clase tiene porcentajes activos usa
  la nota ponderada, con las celdas que la lectura ya trae.
- **Rankings** (`dashboard_controller`): con porcentajes activos, la nota
  ponderada de cada estudiante, el mismo corte en 3.0 y el mismo orden; sin
  ellos, la consulta de siempre, que ni se ejecuta cuando hay porcentajes.
- `tests/test_porcentajes_lecturas.py`, **16 pruebas**. **Las de B1 siguen
  pasando sin tocarlas.**

**Decisiones al escribir el código** (cambio mínimo; ninguna cambia una regla
aprobada):

- **Solo notas numéricas en estos tres lugares.** Hoy ninguno cuenta las
  caritas: el boletín del admin y el reporte parcial dejan vacía la nota de
  preescolar, y los rankings promedian `nota`. Con porcentajes tampoco:
  agregar caritas ahí sería una función nueva. El boletín del profesor (B2c),
  que sí guarda hoy la definitiva de las caritas, sí las pondera (QB1).
- **El boletín del admin solo pondera la materia sin boletín guardado**
  (`boletin_id` vacío). Si el boletín se guardó con definitiva 0 o vacía, el
  respaldo sigue siendo el promedio simple de hoy: la consulta de B1 no deja
  distinguir ese caso sin cambiar su texto, y es un caso raro (un estudiante
  sin notas al guardar que las tuvo después).
- **Los rankings redondean mitad hacia arriba** con porcentajes, como el
  boletín; la consulta de hoy trunca. Un 2.995 ponderado es 3.00 y ya no sale
  en bajo rendimiento. A igual promedio, ordena por nombre.
- **Si la nota ponderada no tiene nada que ponderar**, el reporte parcial y
  el boletín del admin dejan la cifra de hoy, igual que B2c.

**Lo que cuesta** (sin conexiones de más):

| Lectura | Sin porcentajes | Con porcentajes activos |
|---|---|---|
| Boletín del admin, todo guardado | igual (ninguna más) | igual |
| Boletín del admin, alguna materia sin guardar | +1 | +3 (porcentajes, tipos y celdas) |
| Reporte parcial | +1 | +2 (porcentajes y tipos) |
| Ranking bajo o mejor | +1 | +2, y la del ranking pasa a ser la de las celdas |

**Pruebas que cambiaron a propósito:** `test_boletin_caracterizacion.py`,
`test_boletines_reporte_parcial.py`, `test_dashboard_caracterizacion.py` y
`test_dashboard_controlador.py` doblan la pregunta por los porcentajes con "no
hay", igual que en B2c: sus cursores de prueba devuelven las mismas filas a
cualquier consulta, y la pregunta nueva las recibía. Sus conteos y cifras no
cambiaron.

## Paso B3: lista de comprobación en una rama de Neon

La hace el usuario; el asistente no se conecta a Neon. Es el mismo camino del
paso A2. **Producción no se toca en este paso.**

1. En console.neon.tech → Branches → **Create branch** desde `production`,
   con los datos actuales. Nombre sugerido: `prueba-porcentajes`.
2. En la rama nueva → **Connect**: copiar la cadena de conexión **directa**
   (con "Connection pooling" apagado; el host no debe tener `-pooler`). No
   pegarla en el chat.
3. En una terminal de PowerShell, en la carpeta del backend. La variable solo
   vive en esa ventana y gana sobre el `.env`:

   ```powershell
   $env:DATABASE_URL = "<cadena directa de la rama>"
   ([uri]$env:DATABASE_URL).Host
   .\venv\Scripts\python.exe apply_migration.py migrations/20261022_planilla_tipos_porcentaje.sql --dry-run
   .\venv\Scripts\python.exe apply_migration.py migrations/20261022_planilla_tipos_porcentaje.sql
   .\venv\Scripts\python.exe apply_migration.py migrations/20261022_planilla_tipos_porcentaje.sql --dry-run
   ```

   El host que se imprime debe ser el de la rama, **no** el de producción.
   Esperado: `PENDIENTE` → `OK` → `OMITIDA (ya aplicada)` en
   `tenant_colegio_1` y `tenant_2005`.
4. En la misma terminal, regenerar el esquema base desde la rama:

   ```powershell
   .\venv\Scripts\python.exe scripts\generar_esquema_base.py --schema tenant_colegio_1
   ```

   Esperado en el diff: la fecha, la migración en la cabecera (de 46 a 47),
   la tabla `planilla_tipos_porcentaje` con sus dos `CHECK` y su clave
   primaria, el índice `idx_planilla_tipos_porcentaje_tipo_unico` y la clave
   foránea de `asignacion_id` con `ON DELETE CASCADE`. Nada más.
5. **Probar lo de siempre contra la rama**, con el backend nuevo y el
   frontend de siempre. En esa misma terminal:

   ```powershell
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

   Con `pnpm run dev` en el frontend, y **solo con el Colegio Demo**:
   - como profesor: en la planilla, crear un tipo "Prueba B3", escribirle una
     nota a un estudiante y guardar el boletín de ese estudiante;
   - abrir los rankings de esa clase (mejor y bajo rendimiento);
   - como admin: abrir el boletín y el reporte parcial de ese estudiante;
   - como profesor: borrar el tipo "Prueba B3".

   Todo debe funcionar como siempre: así se comprueba, contra PostgreSQL real,
   que las consultas nuevas de esas rutas no fallan. Después, detener el
   servidor y cerrar esa terminal.
6. En el SQL Editor de Neon, **con la rama de prueba elegida**, pegar todo
   esto junto y correrlo una vez. Prueba 16 casos en `tenant_colegio_1`,
   incluidas las sentencias que usa la API; cada uno se deshace al instante.
   La columna `bien` debe salir `true` en las 16 filas:

   ```sql
   SET search_path TO tenant_colegio_1, public;

   CREATE TEMP TABLE prueba_porcentajes (orden INT, caso TEXT, debe TEXT, obtuvo TEXT);

   DO $$
   DECLARE
       asignacion INTEGER := (SELECT MIN(id) FROM asignaciones);
       estudiante INTEGER := (SELECT MIN(id) FROM estudiantes);
       fila RECORD;
   BEGIN
       IF asignacion IS NULL OR estudiante IS NULL THEN
           INSERT INTO prueba_porcentajes
           VALUES (0, 'Datos para probar', 'aceptar', 'no se pudo probar: faltan asignaciones o estudiantes');
           RETURN;
       END IF;

       FOR fila IN
           SELECT * FROM (VALUES
               (1, 'Porcentaje válido', 'aceptar',
                $q$INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
                   VALUES ({asig}, 1, 'Prueba B3', 40)$q$),
               (2, 'El mismo tipo con otras mayúsculas', 'idx_planilla_tipos_porcentaje_tipo_unico',
                $q$INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
                   VALUES ({asig}, 1, 'Prueba B3', 40), ({asig}, 1, ' prueba b3 ', 30)$q$),
               (3, 'Porcentaje 0', 'chk_planilla_tipos_porcentaje_rango',
                $q$INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
                   VALUES ({asig}, 1, 'Prueba B3', 0)$q$),
               (4, 'Porcentaje 101', 'chk_planilla_tipos_porcentaje_rango',
                $q$INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
                   VALUES ({asig}, 1, 'Prueba B3', 101)$q$),
               (5, 'Tipo de puros espacios', 'chk_planilla_tipos_porcentaje_tipo_nota_no_vacio',
                $q$INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
                   VALUES ({asig}, 1, '   ', 40)$q$),
               (6, 'Tipo de 101 caracteres', 'character varying(100)',
                $q$INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
                   VALUES ({asig}, 1, repeat('x', 101), 40)$q$),
               (7, 'Bloquear la clase como la API', 'aceptar',
                $q$SELECT id FROM asignaciones WHERE id = {asig} FOR NO KEY UPDATE$q$),
               (8, 'Leer porcentajes de una clase', 'aceptar',
                $q$SELECT tipo_nota, porcentaje FROM planilla_tipos_porcentaje
                   WHERE asignacion_id = {asig} AND periodo = 1 ORDER BY id$q$),
               (9, 'Leer tipos de una clase', 'aceptar',
                $q$SELECT DISTINCT descripcion FROM notas_detalle
                   WHERE asignacion_id = {asig} AND periodo = 1
                     AND descripcion IS NOT NULL ORDER BY descripcion$q$),
               (10, 'Leer celdas de un estudiante', 'aceptar',
                $q$SELECT descripcion, nota, valoracion,
                          COALESCE(tipo_evaluacion, 'numerica') AS tipo_evaluacion
                   FROM notas_detalle WHERE asignacion_id = {asig} AND periodo = 1
                     AND estudiante_id = {est} AND descripcion IS NOT NULL ORDER BY id$q$),
               (11, 'Leer porcentajes de varias clases', 'aceptar',
                $q$SELECT asignacion_id, tipo_nota, porcentaje FROM planilla_tipos_porcentaje
                   WHERE asignacion_id = ANY(ARRAY[{asig}]) AND periodo = 1 ORDER BY id$q$),
               (12, 'Leer tipos de varias clases', 'aceptar',
                $q$SELECT DISTINCT asignacion_id, descripcion FROM notas_detalle
                   WHERE asignacion_id = ANY(ARRAY[{asig}]) AND periodo = 1
                     AND descripcion IS NOT NULL ORDER BY asignacion_id, descripcion$q$),
               (13, 'Leer celdas de un estudiante en varias clases', 'aceptar',
                $q$SELECT asignacion_id, descripcion, nota, valoracion FROM notas_detalle
                   WHERE asignacion_id = ANY(ARRAY[{asig}]) AND periodo = 1
                     AND estudiante_id = {est} AND descripcion IS NOT NULL ORDER BY id$q$),
               (14, 'Leer celdas de la clase como los rankings', 'aceptar',
                $q$SELECT e.id, e.nombre || ' ' || e.apellido AS nombre_estudiante, n.descripcion,
                          n.nota, n.valoracion
                   FROM notas_detalle n JOIN estudiantes e ON n.estudiante_id = e.id
                   WHERE n.asignacion_id = {asig} AND n.periodo = 1
                     AND n.descripcion IS NOT NULL ORDER BY e.id, n.id$q$),
               (15, 'Quitar un porcentaje como la API', 'aceptar',
                $q$DELETE FROM planilla_tipos_porcentaje
                   WHERE asignacion_id = {asig} AND periodo = 1
                     AND LOWER(TRIM(tipo_nota)) = LOWER(TRIM('Prueba B3'))$q$)
           ) AS c (orden, caso, debe, sentencia)
           ORDER BY orden
       LOOP
           BEGIN
               EXECUTE replace(replace(fila.sentencia, '{asig}', asignacion::text), '{est}', estudiante::text);
               RAISE EXCEPTION 'aceptada';
           EXCEPTION
               WHEN raise_exception THEN
                   INSERT INTO prueba_porcentajes VALUES (fila.orden, fila.caso, fila.debe, 'aceptada');
               WHEN OTHERS THEN
                   INSERT INTO prueba_porcentajes VALUES (fila.orden, fila.caso, fila.debe, SQLERRM);
           END;
       END LOOP;

       BEGIN
           INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
           VALUES (asignacion, 1, 'Prueba B3', 40);
           INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
           VALUES (asignacion, 1, ' prueba b3 ', 25)
           ON CONFLICT (asignacion_id, periodo, (LOWER(TRIM(tipo_nota))))
           DO UPDATE SET porcentaje = EXCLUDED.porcentaje,
                         tipo_nota = EXCLUDED.tipo_nota,
                         actualizado_en = CURRENT_TIMESTAMP;
           RAISE EXCEPTION 'quedo:% filas:%',
               (SELECT porcentaje FROM planilla_tipos_porcentaje
                 WHERE asignacion_id = asignacion AND periodo = 1
                   AND LOWER(TRIM(tipo_nota)) = 'prueba b3'),
               (SELECT count(*) FROM planilla_tipos_porcentaje
                 WHERE asignacion_id = asignacion AND periodo = 1
                   AND LOWER(TRIM(tipo_nota)) = 'prueba b3');
       EXCEPTION
           WHEN OTHERS THEN
               INSERT INTO prueba_porcentajes
               VALUES (16, 'Guardar dos veces como la API cambia el mismo', 'quedo:25 filas:1', SQLERRM);
       END;
   END
   $$;

   SELECT orden, caso, debe, obtuvo,
          CASE WHEN debe = 'aceptar' THEN obtuvo = 'aceptada'
               ELSE position(debe IN obtuvo) > 0 END AS bien
   FROM prueba_porcentajes
   ORDER BY orden;
   ```

   Cómo funciona: igual que en A2, cada caso corre en un bloque que se
   deshace solo, acepte o rechace la base. Solo queda el resultado en una
   tabla temporal, que desaparece al cerrar la sesión.
7. En el mismo SQL Editor, comprobar que no quedó nada (debe dar 0 y 0):

   ```sql
   SELECT 'tenant_colegio_1' AS colegio,
          (SELECT count(*) FROM tenant_colegio_1.planilla_tipos_porcentaje) AS porcentajes,
          (SELECT count(*) FROM tenant_colegio_1.notas_detalle
            WHERE LOWER(TRIM(descripcion)) = 'prueba b3') AS celdas_de_prueba
   UNION ALL
   SELECT 'tenant_2005',
          (SELECT count(*) FROM tenant_2005.planilla_tipos_porcentaje),
          (SELECT count(*) FROM tenant_2005.notas_detalle
            WHERE LOWER(TRIM(descripcion)) = 'prueba b3');
   ```

8. Correr `.\venv\Scripts\python.exe scripts\verify.py`: ahora
   `test_esquema_base.py` debe pasar, y con él todo.
9. Contarle al asistente lo que salió en los puntos 3 a 8, sin cadenas de
   conexión. Con eso se cierra B3 y el usuario hace un commit con el esquema
   base. Después se puede borrar la rama. Lo siguiente es aplicar la
   migración en producción y en seguida subir el backend (el orden de
   publicación es el mismo de la parte A).

## Avance del paso B3, 2026-10-22

Lo hizo el usuario en la rama `prueba-porcentajes` de Neon, creada desde
`production`, guiado paso a paso por el asistente. El asistente no se conectó
a Neon ni a producción.

- **Punto 3, migración en la rama.** Simulación: `PENDIENTE` en
  `tenant_colegio_1` y `tenant_2005`. Después de aplicarla, la simulación dio
  `OMITIDA (ya aplicada)` en los dos. La salida del comando que la aplicó no
  se pegó, pero el runner guarda el registro en la misma transacción que crea
  la tabla, así que ese `OMITIDA` prueba que la tabla existe.
- **Dónde se aplicó.** El usuario no confirmó el host con palabras, pero el
  script del punto 6 corrió **en la misma ventana** y se negó a seguir si era
  producción: imprimió la rama `ep-cool-sunset-aiox0ly8`, no
  `ep-late-smoke-aip41j6x`. La migración fue a la rama. Al aplicarla en
  producción, su simulación debe dar `PENDIENTE`: será la segunda
  comprobación.
- **Punto 4, esquema base** regenerado desde `tenant_colegio_1` de la rama: 39
  tablas (eran 38), 1 función y 1 disparador. El asistente revisó el diff
  línea por línea: solo la fecha, la cabecera (de 46 a 47 migraciones), la
  tabla `planilla_tipos_porcentaje` con sus dos `CHECK` y su `PRIMARY KEY`, el
  índice `idx_planilla_tipos_porcentaje_tipo_unico` y la clave foránea de
  `asignacion_id` con `ON DELETE CASCADE`. Nada más.
- **Punto 5, lo de siempre contra la rama**, con el backend nuevo y el
  frontend de siempre, como profesor y admin del Colegio Demo: crear el tipo
  "Prueba B3" con una nota, guardar el boletín de ese estudiante, abrir los
  dos rankings, el boletín y el reporte parcial del admin, y borrar el tipo.
  Todo funcionó igual que siempre.
- **Puntos 6 y 7.** En vez de pegar el SQL en el editor de Neon, el asistente
  lo puso en un script fuera del repo (carpeta temporal del asistente) que el
  usuario corrió en la ventana de la rama. Se niega a correr sin
  `DATABASE_URL`, contra producción o contra el pooler; nunca imprime la
  cadena; usa los dos bloques SQL de "Paso B3" tal cual y deshace todo al
  final. Resultado: **TODO BIEN, 16 de 16 casos**, y 0 porcentajes y 0
  celdas de prueba en los dos colegios.
- **Punto 8.** `scripts/verify.py`: **2870 pasan, 0 fallan**, con
  `test_esquema_base.py` ya en verde. Ruff y `pip check` limpios.
- Producción **no se tocó** durante B3: ni migración ni push.

## Publicación del backend de la parte B, 2026-10-22

La hizo el usuario, guiado paso a paso; el asistente no se conectó a la base
de producción.

- **Commit del esquema base** (`dfe0336`), con B0 a B3 ya en commits
  anteriores.
- **Migración en producción** en una ventana nueva, con la cadena directa de
  producción. La simulación previa dio `PENDIENTE` en `tenant_colegio_1` y
  `tenant_2005`: **segunda prueba de que B3 no tocó producción**. Después el
  usuario aplicó la migración y la simulación siguiente dio `OMITIDA (ya
  aplicada)` en los dos ("todo ok"; la salida no se pegó).
- **Push del backend** en seguida: `origin/main` en `dfe0336`.
- **Render Live**, comprobado por el asistente desde fuera y sin sesión, con
  una lectura que no cambia nada: `GET /planilla/tipos/porcentaje` respondía
  `404` (la ruta no existía) y pasó a `405` (existe y solo acepta `PUT`).
  `/health` siguió en `200`. Con eso se cerró el rato sin poder crear
  colegios.
- **Qué ven los profesores:** nada nuevo todavía. La pantalla para poner
  porcentajes llega en B4; hasta entonces ninguna clase puede tenerlos y
  ninguna nota cambia.

## Fuera de alcance

- Mostrar las subnotas en el boletín, el reporte parcial o cualquier impreso.
- Que el admin vea o edite subnotas: la planilla es del profesor.
- Porcentajes dentro de las subnotas de un tipo (decisión 2).
- Copiar subnotas o porcentajes de un periodo a otro.
- Reordenar subnotas arrastrando (P12).

## Hallazgos fuera de alcance (no se corrigen aquí)

- `POST /planilla/nota` responde `200` con `{"error": ...}` cuando el
  estudiante no pertenece a la asignación, y la pantalla lo toma como
  guardado. Se conserva para no cambiar esa ruta; las rutas nuevas no copian
  esa forma.
- Los distintos promedios de la tabla de la parte B ya hoy difieren entre sí.
  Queda para B0.
- `POST /planilla/subnotas/valores` comprueba que el estudiante sea del curso
  con `estudiantes.curso_id`, la misma consulta de `require_estudiante_in_asignacion`
  y de la planilla. Hereda así el hallazgo que el año lectivo dejó para su
  fase 6 (comprobaciones de estudiantes con `estudiantes.curso_id`): en un año
  reabierto, el admin no podría calificar a un estudiante que ya pasó al curso
  de otro año. Si la fase 6 lo corrige allí, queda corregido aquí también.

## Preguntas abiertas

- ~~Antes de A1: que el usuario revise las propuestas P1 a P12.~~
  **Aprobadas todas el 2026-10-21.**
- ~~Antes de B0: ¿los tableros y la ficha del estudiante también usan los
  porcentajes? ¿Preescolar también lleva porcentajes? ¿Qué pasa con los tipos
  creados sin porcentaje en un periodo ya empezado?~~ **Respondidas el
  2026-10-21** (QB1 a QB4 en "Avance del paso B0").
- ~~Antes de B1: que el usuario revise y apruebe las propuestas PB1 a PB10.~~
  **Aprobadas todas el 2026-10-21.**

## Entrega para el siguiente chat

- **Parte A publicada el 2026-10-21.** Backend: A0 en `185d5b6`, A1 y A2 en
  `e36f976`, migración en los dos colegios y Render **Live** (ver
  "Publicación del backend"). Frontend: A3, A4 y A5 subidos hasta `3fb9831`
  y publicados en Vercel (ver "Publicación del frontend").
- Última verificación del backend (al cerrar A5): `scripts/verify.py`, 2733
  pasan, 0 fallan; Ruff y `pip check` limpios.
- En este repo quedan commits **solo de documentos** sin push. Subirlos hace
  que Render publique otra vez el mismo código: no cambia nada, pero es una
  publicación.
- Pendiente del usuario: borrar la rama `prueba-subnotas` en Neon, si no lo
  hizo, y devolver el `DATABASE_URL` del `.env` al endpoint `-pooler`, si lo
  cambió.
- **B0 (diseño de los porcentajes) hecho el 2026-10-21, en `822dd4e`.
  Propuestas PB1 a PB10 aprobadas por el usuario el mismo día.**
  Inventario confirmado, preguntas QB1 a QB4 respondidas por el usuario y
  propuestas PB1 a PB10 escritas. Ver "Avance del paso B0". No hay código de
  la parte B. Verificación al cerrar B0 (solo documentos):
  `scripts/verify.py`, 2733 pasan, 0 fallan, Ruff y `pip check` limpios; en
  el frontend, `check:deploy` con 2902 pruebas, lint y build correctos. `git
  diff --check` limpio en los dos.
- **B1 (caracterización) hecho el 2026-10-21, sin commit**: 15 pruebas en
  `tests/test_porcentajes_planilla_caracterizacion.py` y 4 en el frontend.
  No cambió el código de la aplicación. Ver "Avance del paso B1".
- Verificación al cerrar B1: `scripts/verify.py`, **2748 pasan** (eran
  2733), 0 fallan; Ruff y `pip check` limpios. Frontend: `check:deploy` con
  **2906 pruebas** (eran 2902), lint y build correctos. Corridas una tras
  otra, sin otra carga. `git diff --check` limpio en los dos.
- B1 en `a9cdc57` (backend) y `f6b22f6` (frontend).
- **B2 completo** (ver "Avance del paso B2"): **B2a (el cálculo) en
  `a630183`, B2b (tabla, ruta para guardar porcentajes, lectura en la
  planilla y borrado con el tipo) en `dcf8443`, B2c (la definitiva del
  boletín, PB5) en `05a8bbe` y B2d (boletín del admin, reporte parcial y
  rankings, PB7) hecho el 2026-10-22, sin commit.** En la práctica ninguna
  nota cambia todavía: solo cambia en clases con porcentajes completos, y
  ninguna puede tenerlos hasta B3 y B4.
- Verificación al cerrar B2b: `scripts/verify.py`, **2835 pasan y 1 falla a
  propósito** (`test_esquema_base.py`); Ruff y `pip check` limpios. Frontend
  sin cambios de código: `check:deploy` con 2906 pruebas, lint y build
  correctos. Corridas una tras otra. `git diff --check` limpio en los dos.
- Verificación al cerrar B2c: `scripts/verify.py`, **2853 pasan y 1 falla a
  propósito** (`test_esquema_base.py`); Ruff y `pip check` limpios. Frontend
  sin cambios de código: `check:deploy` con 2906 pruebas, lint y build
  correctos. Corridas una tras otra. `git diff --check` limpio en los dos.
- Verificación al cerrar B2d (B2 completo): `scripts/verify.py`, **2869
  pasan y 1 falla a propósito** (`test_esquema_base.py`); Ruff y `pip check`
  limpios. Frontend sin cambios de código: `check:deploy` con 2906 pruebas,
  lint y build correctos. Corridas una tras otra. `git diff --check` limpio
  en los dos.
- **Desde B2b, `test_esquema_base.py` falla a propósito** (reclama solo
  `20261022_planilla_tipos_porcentaje.sql`) hasta B3, y **el backend no se
  sube** hasta que la migración esté en producción: si saliera antes,
  `DELETE /planilla/tipo` fallaría para todos los profesores. Los commits se
  pueden hacer; el push no.
- B2d en `0498f80`.
- **B3 hecho el 2026-10-22** (ver "Avance del paso B3"): migración probada en
  la rama `prueba-porcentajes`, esquema base regenerado (sin commit), 16 de
  16 casos y `scripts/verify.py` con **2870 pasan, 0 fallan**.
  `test_esquema_base.py` ya pasa.
- Pendiente del usuario: borrar la rama `prueba-porcentajes` en Neon (y la
  vieja `prueba-subnotas`, si sigue).
- **Backend de la parte B en producción el 2026-10-22**: esquema base en
  `dfe0336`, migración aplicada en los dos colegios, push y Render **Live**.
  Ver "Publicación del backend de la parte B". Nadie ve nada nuevo todavía.
- Pendiente del usuario: devolver el `DATABASE_URL` del `.env` al endpoint
  `-pooler`, si lo cambió para aplicar la migración.
- **B4 va en dos partes en el frontend.** **B4a (contratos: servicio,
  cálculo gemelo, ganchos y la definitiva del servidor en el boletín) hecho
  el 2026-10-22, sin commit.** Detalle en "Avance del paso B4a" del documento
  del frontend. Lo que ve el profesor no cambia todavía.
- B4a en `7ddd42c` (frontend). **B4b (la pantalla) hecho el 2026-10-22, sin
  commit**: franja de porcentajes encima de la tabla, porcentaje en cada
  encabezado y campo al crear un tipo. Detalle en "Avance del paso B4b" del
  documento del frontend.
- B4b en `63f8528` (frontend).
- **B5 en curso** (el usuario, guiado paso a paso). En el paso 2 propuso
  bloquear las notas con porcentajes incompletos; se decidió **PB11** (aviso
  al guardar el boletín) y se hizo como **B4c**, solo en el frontend, el
  2026-10-22, sin commit. Detalle en "Avance del paso B4c" del documento del
  frontend.
- Siguiente acción exacta: **seguir B5 desde el paso 5** (lista en "Paso B5"
  del documento del frontend, que ya incluye el aviso; los pasos 1 a 4
  salieron bien). Si sale bien, push del frontend y la parte B queda
  publicada.
- Prompt para retomar:
  `docs/funcionalidades/PROMPT_CONTINUACION_SUBNOTAS_PLANILLA.md`.
