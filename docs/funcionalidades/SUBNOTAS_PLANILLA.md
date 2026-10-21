# Funcionalidad: Subnotas y porcentajes en la planilla — Backend

## Control

- Estado: **Diseño (paso A0), 2026-10-21. No hay código de esta
  funcionalidad.**
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

## Propuestas de este diseño (el usuario las revisa con este documento)

Se escribieron en el paso A0 para cerrar los casos que las decisiones no
cubren. Si el usuario cambia alguna, se corrige aquí antes de empezar A1.

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
| `tipo_nota` | `varchar(100) NOT NULL` | el mismo texto de `notas_detalle.descripcion` |
| `nombre` | `varchar(60) NOT NULL` | |
| `creada_en` | `timestamptz NOT NULL DEFAULT now()` | da el orden (P12) |

- Índice único: `(asignacion_id, periodo, LOWER(TRIM(tipo_nota)),
  LOWER(TRIM(nombre)))`. Es la garantía real contra nombres repetidos aunque
  lleguen dos peticiones a la vez.
- Índice de lectura: `(asignacion_id, periodo)`.

**`planilla_subnotas_valores`**: una fila por calificación de un estudiante
en una subnota.

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `serial` | clave primaria |
| `subnota_id` | `integer NOT NULL` | FK a `planilla_subnotas(id)` `ON DELETE CASCADE` |
| `estudiante_id` | `integer NOT NULL` | FK a `estudiantes(id)`, sin cascada, igual que `notas_detalle` |
| `nota` | `numeric(3,2)` | `CHECK` entre 1 y 5 |
| `valoracion` | `varchar(30)` | código de carita; la API valida que exista en la escala |
| `actualizada_en` | `timestamptz NOT NULL DEFAULT now()` | |

- `UNIQUE (subnota_id, estudiante_id)`: una calificación por estudiante y
  subnota.
- `CHECK`: exactamente uno de `nota` o `valoracion` tiene valor. Una subnota
  vacía no se guarda: se borra su fila (P2).
- Índice: `(estudiante_id)`.

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

Es la propuesta del diseño; A1 la fija con pruebas. Todas las rutas nuevas
usan las mismas guardias que la planilla (ver "Diagnóstico") y responden
errores con su código HTTP (`403`, `404`, `409`, `422`) y un mensaje en español.

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
  crea la subnota para todo el curso. Responde `409` si el nombre ya existe en
  ese tipo o si el tipo no existe, y `422` si pasa el límite de P11.
- `PUT /planilla/subnotas/{id}` con `{ nombre }`: la renombra (P5).
- `DELETE /planilla/subnotas/{id}`: la borra, recalcula las celdas afectadas
  y devuelve `{ "celdas": { "<estudiante_id>": valor o null } }` para que la
  pantalla se actualice sin recargar.
- `POST /planilla/subnotas/valores` con `{ asignacion_id, periodo, tipo_nota,
  estudiante_id, valores: { "<subnota_id>": valor o null } }`: reemplaza las
  calificaciones de ese estudiante en ese tipo, recalcula su celda, la guarda y
  la devuelve (P9, P10). **Toda subnota enviada tiene que ser de esa
  asignación, periodo y tipo** (si no, `422`). Así nadie puede escribir en la
  clase de otro profesor mandando un id ajeno.

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
- **A1 — Backend.** Primero, pruebas de caracterización de las tres rutas que
  ya existen (`GET` de la planilla sin el parámetro, `POST /planilla/nota` y
  `DELETE /planilla/tipo`), con conteo de consultas, para demostrar que sin
  subnotas nada cambia. Después: la migración (escrita, sin aplicar), la
  escala de caritas, el cálculo, el repositorio, las rutas nuevas, el `409`
  de `POST /planilla/nota` y el borrado en `DELETE /planilla/tipo`.
  Documentar en `docs/API_ENDPOINTS.md`, `docs/BASE_DATOS.md`,
  `docs/MIGRACIONES.md` y `docs/CAMBIOS_BACKEND.md`.
  `tests/test_esquema_base.py` fallará a propósito hasta A2: es la compuerta
  que obliga a aplicar la migración y regenerar el esquema base.
- **A2 — Base de datos (lo hace el usuario).** Probar la migración en una rama
  de Neon, regenerar el esquema base desde esa rama y hacer un commit con la
  migración, el esquema base y el código juntos. **Todavía sin push** (ver
  "Orden de publicación").
- **A3 — Frontend: contratos.** El servicio, las utilidades (vista previa del
  cálculo, cuándo una celda es calculada) y los ganchos, con pruebas. Detalle
  en el documento del frontend.
- **A4 — Frontend: pantalla.** El botón en la celda, el modal con
  Anterior/Siguiente, la celda calculada y la vista de celular.
- **A5 — Prueba en local** con el Colegio Demo (`tenant_colegio_1`), nunca con
  estudiantes de `tenant_2005`. El backend local escribe en la base real, así
  que la prueba necesita la migración ya aplicada (paso 1 del orden de
  publicación) o un backend local apuntando a la rama de Neon.

### Orden de publicación (parte A)

1. Aplicar la migración en producción (`tenant_colegio_1` y `tenant_2005`)
   con `apply_migration.py`: primero `--dry-run`, con el `DATABASE_URL`
   directo (sin `-pooler`).
2. Probar en local (A5).
3. Push del backend y esperar a que Render quede **Live**.
4. Push del frontend.

**Aquí la migración va antes del push**, al revés que en SISBÉN y igual que en
Listas de seguimiento. El backend nuevo usa las tablas nuevas en rutas que ya
existen (guardar una nota y borrar un tipo). Si saliera primero, guardar una
nota fallaría a todos los profesores hasta aplicar la migración. Al revés no
hay riesgo: el backend viejo no sabe que esas tablas existen.

**Entre el paso 1 y el 3 no se crean colegios nuevos.** Un colegio nuevo nace
del esquema base del backend publicado, que todavía no trae las tablas, pero
copia el historial de migraciones de la plantilla, que ya marca esta como
aplicada. Quedaría sin las tablas y marcado como si las tuviera. Las altas
solo las hace el super admin.

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

## Preguntas abiertas

- **Antes de A1:** que el usuario revise las propuestas P1 a P12.
- **Antes de B0** (no hace falta responderlas ahora): ¿los tableros y la ficha
  del estudiante también usan los porcentajes? ¿Preescolar también lleva
  porcentajes? ¿Qué pasa con los tipos creados sin porcentaje en un periodo ya
  empezado?

## Entrega para el siguiente chat

- Hecho: **A0 (diseño), 2026-10-21, sin commit.** No hay código de esta
  funcionalidad en ningún repo.
- Al iniciar A0, los dos repos estaban en `main` y limpios: backend `ff800f7`,
  frontend `c67e1fd`.
- Verificación de A0 (solo documentos): `scripts/verify.py` pasa 2604 pruebas,
  con Ruff y `pip check` limpios. En el frontend, `pnpm run check:deploy` pasó
  2804 de 2805 pruebas. La que falló (`IngresoBoletinProfesor.test.jsx`) pasa
  sola (2 de 2), así que fue el fallo al azar por carga de la máquina. Lint y
  build pasan por separado. `git diff --check` limpio en los dos repos.
- Siguiente acción exacta: que el usuario revise las propuestas P1 a P12 de
  este documento y el diseño de la pantalla en el documento del frontend.
  Después, **A1 (backend)**, solo con su autorización explícita.
- Prompt para retomar:
  `docs/funcionalidades/PROMPT_CONTINUACION_SUBNOTAS_PLANILLA.md`.
