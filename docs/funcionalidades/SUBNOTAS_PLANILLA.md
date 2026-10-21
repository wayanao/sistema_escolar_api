# Funcionalidad: Subnotas y porcentajes en la planilla — Backend

## Control

- Estado: **A0 (diseño) en `185d5b6`. A1 (backend) y A2 (rama de Neon y
  esquema base) terminados el 2026-10-21, sin commit.** La migración se probó
  en una rama de Neon; **en producción todavía no se ha aplicado.**
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
- Última actualización: 2026-10-21.

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
- **A3 — Frontend: contratos.** El servicio, las utilidades (vista previa del
  cálculo, cuándo una celda es calculada) y los ganchos, con pruebas. Detalle
  en el documento del frontend.
- **A4 — Frontend: pantalla.** El botón en la celda, el modal con
  Anterior/Siguiente, la celda calculada y la vista de celular.
- **A5 — Prueba en local** con el Colegio Demo (`tenant_colegio_1`), nunca con
  estudiantes de `tenant_2005`. El backend local escribe en la base real, así
  que la prueba necesita la migración ya aplicada (paso 2 del orden de
  publicación) o un backend local apuntando a la rama de Neon.

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
   local, ya con la migración en producción, sirve para probar.
5. Push del frontend.

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
- Producción **no se tocó**: ni migración, ni push.

## Parte B — Porcentajes por tipo de nota (esbozo; se diseña en B0)

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
- **Antes de B0** (no hace falta responderlas ahora): ¿los tableros y la ficha
  del estudiante también usan los porcentajes? ¿Preescolar también lleva
  porcentajes? ¿Qué pasa con los tipos creados sin porcentaje en un periodo ya
  empezado?

## Entrega para el siguiente chat

- Hecho: **A0 (diseño)** en `185d5b6` (frontend `1553574`). **A1 (backend) y
  A2 (rama de Neon y esquema base) terminados el 2026-10-21, sin commit.** Ver
  "Avance del paso A1" y "Avance del paso A2".
- `scripts/verify.py`: 2733 pasan, 0 fallan. Ruff y `pip check` limpios.
- La migración está probada en la rama `prueba-subnotas`. **En producción no
  se ha aplicado ni se ha hecho push.** El frontend no tiene código de esta
  funcionalidad.
- Siguiente acción exacta:
  1. El usuario hace **un solo commit** del backend con A1 y A2: migración,
     esquema base, código, pruebas y documentos. **Sin push todavía.**
  2. Orden de publicación, pasos 2 y 3, **seguidos**: aplicar la migración en
     producción (`--dry-run`, aplicar y `--dry-run`, con el `DATABASE_URL`
     directo de producción) y, en seguida, push del backend esperando a que
     Render quede **Live**. Entre uno y otro no se crean colegios.
  3. Después, **A3 (frontend)**, solo con autorización explícita.
- La rama `prueba-subnotas` ya se puede borrar en Neon.
- Prompt para retomar:
  `docs/funcionalidades/PROMPT_CONTINUACION_SUBNOTAS_PLANILLA.md`.
