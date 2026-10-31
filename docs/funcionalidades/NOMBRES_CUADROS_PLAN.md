# Funcionalidad: Nombres de los cuadros del plan de clase — Backend

## Control

- Estado: **el paso 1 (backend) se publicó el 2026-10-31** (`f4c7fcb`).
  Primero se aplicó la migración en producción y después se hizo el push.
  Render quedó Live. Lo que ven los colegios no cambia hasta el paso 2 (la
  pantalla, en `frontend-react`). El paso 0 (este documento) está en
  `864e8d6`. Ver "Avance del paso 1".
- Tipo: función nueva de producto, encima del plan de clases. No es un módulo
  de `docs/modularizacion/`.
- **Este es el documento principal.** La ventana del admin y los cambios en
  las pantallas están en
  `frontend-react/docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`.
- Repos afectados: este (una tabla y dos rutas) y `frontend-react` (la ventana
  del admin y los nombres en las pantallas del plan). **El backend va
  primero.**
- Riesgo: bajo. Es una tabla nueva que solo leen estas dos rutas. No toca
  `plan_de_clases` ni la forma de guardar un plan.
- Última actualización: 2026-10-31.

## Objetivo

Que el admin de cada colegio cambie, sin tocar código, el nombre de los
cuadros del plan de clase y el texto gris de ayuda que aparece dentro de cada
cuadro vacío. Al renombrar, la pantalla le dice qué recibe cada cuadro.

## Motivación

- Hoy los nombres están escritos en el código del frontend, en cuatro
  componentes, así que renombrar un cuadro exige una publicación. Ya se ha
  hecho así: "Logro" se guarda en la columna `proposito` y "Desarrollo
  cognitivo" en `dba`.
- Hoy un mismo cuadro tiene nombres distintos según la pantalla:

  | Cuadro | Formulario del profesor | Detalle del admin |
  |---|---|---|
  | `estandar` | Estándar / Lineamientos curriculares | Estándar |
  | `imagen1` | Actividad a desarrollar | Evidencia de desarrollo cognitivo |

## Fuera de alcance

- **Agregar, quitar u ordenar cuadros.** Se habló el 2026-10-31 y el usuario
  eligió "renombrar solamente". Si se retoma, los textos extra irían en un
  bloque JSON, como las respuestas de la entrevista de admisión
  (`app/core/cuestionario_admision.py`).
- Cambiar qué recibe un cuadro (tipos de archivo, tamaños).
- Nombres distintos por año, materia o profesor. Valen para todo el colegio.
- Los títulos de los bloques del formulario, como "Contexto pedagógico".
- El cuadro viejo "Actividad en clase" (`competencias`). Ya no está en el
  formulario del profesor y solo aparece en planes viejos que lo tienen lleno.
- El planeador anual, que es otra tabla (`planeador_anual`).

## Decisiones ya tomadas (con el usuario, 2026-10-31)

| # | Decisión |
|---|---|
| 1 | Solo se renombra. No se agregan cuadros |
| 2 | La pantalla de renombrar muestra **qué recibe cada cuadro** y avisa que cambiar el nombre no cambia lo que recibe ni borra lo escrito |
| 3 | También se renombran **los dos archivos** |
| 4 | También se cambia **el texto gris de ayuda** de los cuadros de texto |
| 5 | Los nombres valen **para todo el colegio**, y hay un botón para **volver a los originales** |
| 6 | Cada cuadro tiene **un solo nombre** en todas las pantallas |

## Qué se puede renombrar

| Clave | Nombre original | Ayuda original | Recibe |
|---|---|---|---|
| `unidad` | Unidad | Nombre de la unidad o eje de trabajo | texto |
| `estandar` | Estándar / Lineamientos curriculares | Estándar, lineamientos curriculares o referente curricular | texto |
| `tema` | Tema | Tema central de la clase | texto |
| `proposito` | Logro | Qué se espera que logren los estudiantes | texto |
| `clase` | Actividad inicial | Cómo inicia la clase y qué hacen los estudiantes | texto |
| `dba` | Desarrollo cognitivo | Proceso, habilidad o DBA relacionado | texto |
| `actividad_casa` | Actividad en casa | Refuerzo, consulta o producción para casa | texto |
| `imagen1` | Actividad a desarrollar | (no tiene) | archivo |
| `imagen2` | Evidencia de actividad en casa | (no tiene) | archivo |

- **texto:** texto libre. Al mostrarlo, los enlaces `http`/`https` se vuelven
  clic; uno de YouTube se reproduce dentro de la clase y los demás se abren en
  otra pestaña.
- **archivo:** una imagen PNG, JPG o WEBP de hasta 5 MB, o un PDF de hasta
  15 MB (`ALLOWED_EXTENSIONS`, `MAX_IMAGE_BYTES` y `MAX_PDF_BYTES` en
  `app/controllers/plan_de_clases_controller.py`).

Los nombres originales de `estandar` e `imagen1` son los del formulario del
profesor (ver P1).

## Dónde viven los nombres originales

**En el frontend, no aquí.** El backend solo guarda lo que el colegio cambió y
revisa que cada clave exista. Motivos:

- Son textos de pantalla. Si la consulta de nombres falla, el profesor sigue
  planeando con los nombres originales en vez de quedarse sin formulario.
- Así los nombres no quedan escritos en los dos repos. Las claves sí, pero ya
  lo están hoy: son los campos del plan.

## Diseño de datos

### Tabla nueva: `plan_de_clases_cuadros`

Una fila por cuadro **renombrado**. Un cuadro sin fila usa su nombre original.
"Volver a los originales" borra todas las filas.

| Columna | Tipo | Nota |
|---|---|---|
| `clave` | varchar(30) | PK |
| `nombre` | varchar(60) NOT NULL | CHECK de 1 a 60 caracteres, ya recortado |
| `ayuda` | varchar(150) NOT NULL DEFAULT `''` | Vacía significa sin ayuda. Siempre vacía en los archivos |
| `actualizado_en` | timestamptz NOT NULL DEFAULT `CURRENT_TIMESTAMP` | La pone el servidor |
| `actualizado_por` | integer NULL | FK a `usuarios(id)` con `ON DELETE SET NULL` |

- **La lista de claves válidas no va en la base.** Vive en
  `app/core/cuadros_plan_de_clases.py`, igual que las preguntas de la
  entrevista. Si algún día se agrega un cuadro, la regla cambia sin migración.
- **No se usa `institucion_branding.configuracion_extra`**, aunque ya existe y
  ahorraría la migración: guardar la marca reemplaza ese bloque entero
  (`app/repositories/branding_repository.py`), así que cambiar el logo borraría
  los nombres.

### Migración

`migrations/20261031_plan_de_clases_cuadros.sql` (o la fecha del día en que se
escriba), junto con la base regenerada, como indica `CLAUDE.md` ("two sources
of truth"). Reejecutable, con `CREATE TABLE IF NOT EXISTS`. Se prueba en una
rama de Neon y se aplica con `apply_migration.py` (`docs/MIGRACIONES.md`).

Es una tabla nueva que el código viejo no lee, así que aplicarla en producción
antes del push no cambia nada para los colegios.

## Permisos

- **Leer:** cualquier usuario con sesión del colegio (`get_current_user`), es
  decir, profesor o admin. Los nombres no son un dato sensible.
- **Guardar:** solo el admin (`get_current_active_admin`). El profesor recibe
  `403`.
- **Aislamiento por colegio:** la tabla vive en el esquema de cada colegio y
  el `search_path` de la conexión hace el resto. La ruta y el cuerpo no llevan
  colegio.

## API

- `GET /plan-de-clases/cuadros`, nuevo.
  - `200` con `{"cuadros": [{"clave", "nombre", "ayuda"}]}`. Solo trae los
    cuadros renombrados; una lista vacía significa "todos con su nombre
    original".
- `PUT /admin/plan-de-clases/cuadros`, nuevo.
  - Cuerpo: `{"cuadros": [{"clave", "nombre", "ayuda"}]}` con **la lista
    completa** de cuadros renombrados. Reemplaza todo en una sola transacción
    (borrar e insertar). Una lista vacía vuelve a los originales.
  - Respuestas:
    - `200`, con la lista guardada, igual que el `GET`;
    - `403`, si no es admin;
    - `422`, si una clave no existe o se repite, si un nombre queda vacío o
      pasa de 60 caracteres, si una ayuda pasa de 150, o si un archivo trae
      ayuda.
  - Se guarda la lista completa, y no un cuadro a la vez, porque la ventana
    tiene un solo botón "Guardar": una petición y todo o nada.
- **Orden de las rutas.** `GET /plan-de-clases/cuadros` debe declararse antes
  de `GET /plan-de-clases/{asignacion_id}`. Si no, FastAPI intenta leer
  "cuadros" como número y responde `422`. Una prueba lo fija.
- Si dos admins guardan al mismo tiempo, **gana el último**. No hay control de
  versión porque solo lo cambian admins y es un cambio raro.
- Los nombres repetidos entre cuadros los revisa la ventana del frontend, que
  conoce los nueve nombres. El backend solo ve los renombrados, y esta regla
  es de comodidad, no de seguridad.

## Peticiones

- Formulario del profesor: **una petición más al abrir la página**, en paralelo
  con las que ya hace. No se repite al cambiar de fecha ni de clase.
- Revisión del admin: una petición más al abrir la página.
- Guardar: un `PUT`.
- Cada lectura es un `SELECT` sobre una tabla de máximo nueve filas.

El conteo se fija con una prueba en el paso 2, antes y después.

## Invariantes

1. Renombrar **no toca `plan_de_clases`**. Ningún plan cambia.
2. Lo que recibe cada cuadro no cambia.
3. Si la consulta de nombres falla, el formulario funciona con los nombres
   originales.
4. Solo el admin guarda nombres, y lo exige el backend.
5. La ventana del admin no guarda si no pudo leer los nombres actuales. Si
   guardara, borraría los del colegio.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| La migración falla en producción | Es una tabla nueva, con `IF NOT EXISTS`, probada antes en una rama de Neon y con `--dry-run` |
| El código llega antes que la tabla | El `GET` daría `500` y el frontend usaría los nombres originales. Aun así, la migración va **antes** del push |
| Un admin le cambia el sentido a un cuadro y los planes viejos quedan bajo un título que no les corresponde | Aviso fijo en la ventana (decisión 2) |
| `{asignacion_id}` tapa la ruta nueva | Orden de declaración y una prueba |
| Guardar la marca borra los nombres | Tabla propia en vez de `configuracion_extra` |

## Plan de pasos y orden de publicación

| Paso | Repo | Qué | ¿Lo ven los colegios? |
|---|---|---|---|
| 0 | ambos | Este documento y el del frontend | No |
| 1 | backend | Migración, `app/core/cuadros_plan_de_clases.py`, repositorio, las dos rutas y pruebas. La migración va a producción **antes** del push | No |
| 2 | frontend | Nombres originales en un solo archivo, las pantallas leen de ahí y la ventana del admin | Sí |
| 3 | ambos | Publicación y prueba real en el Colegio Demo | Sí |

## Preguntas abiertas

- **P1 (paso 2):** cuando hoy un cuadro tiene dos nombres, ¿cuál queda como
  original? Propuesta: el del formulario del profesor, porque es lo que ve
  quien escribe el plan. Así, el admin pasaría a ver "Estándar / Lineamientos
  curriculares" en vez de "Estándar", y "Actividad a desarrollar" en vez de
  "Evidencia de desarrollo cognitivo".

## Avance del paso 1 (2026-10-31)

Qué se construyó:

- `migrations/20261031_plan_de_clases_cuadros.sql`.
- `app/core/cuadros_plan_de_clases.py`, puro: las claves, los largos, los
  mensajes, `motivo_para_rechazar` y `en_orden_del_formulario`.
- `app/schemas/cuadros_plan_de_clases.py`: `CuadroPlan` y
  `CuadrosPlanUpdate` (recortan los textos; de 0 a 9 cuadros).
- `app/repositories/cuadros_plan_de_clases_repository.py`: `leer_cuadros`,
  `bloquear_cuadros`, `borrar_cuadros` e `insertar_cuadros` (un solo
  `INSERT`).
- `app/controllers/cuadros_plan_de_clases_controller.py` y
  `app/routes/cuadros_plan_de_clases.py`, en un router propio. `app/main.py`
  lo incluye antes que el del plan.

El detalle está en `docs/CAMBIOS_BACKEND.md` y el contrato en
`docs/API_ENDPOINTS.md` ("Nombres de los cuadros").

Cambios frente al diseño:

- **Router propio**, y no dentro de `app/routes/plan_de_clases.py`, para que
  las 13 rutas del plan y sus pruebas de caracterización no cambien. Por eso
  el orden se resuelve al incluirlo en `app/main.py`, y una prueba lo fija.
- **Dos guardados a la vez:** guardar es borrar e insertar, y sin más cuidado
  dos admins podían mezclar sus listas o chocar con la llave primaria. Antes
  de borrar se bloquea la tabla (`LOCK TABLE ... IN SHARE ROW EXCLUSIVE
  MODE`), que pone en fila a quienes guardan sin frenar a quienes leen. Sigue
  ganando el último.

Consultas, sin contar la sesión: leer, 1; guardar, 3 en una transacción (2
al volver a los originales). Una lista inválida se rechaza sin abrir la base.

Verificación:

- En una rama de Neon creada desde producción, el usuario aplicó la migración
  en los dos colegios (`PENDIENTE` → `OK` → `OMITIDA`).
- En esa rama, un script dentro de una transacción que se deshace dio **24 de
  24 comprobaciones** con las funciones reales del repositorio. El esquema base
  se regeneró desde la rama, y su diff fue solo la tabla nueva. Detalle en
  `docs/MIGRACIONES.md`.
- `scripts/verify.py`: **3053 pasan, 0 fallan**; Ruff y `pip check` limpios.

Publicación (2026-10-31):

- Commit `f4c7fcb`, con la migración y la base juntas.
- El usuario aplicó la migración en producción, y al volver a simular salió
  `OMITIDA (ya aplicada)` en los dos colegios.
- Después hizo el push y Render quedó Live. `/health` dio `200` y
  `PUT /admin/plan-de-clases/cuadros` dio `401` sin sesión; con el código
  anterior habría dado `405`, así que la ruta nueva está publicada.

## Entrega para el siguiente paso

El paso 1 ya está publicado. Lo siguiente es el **paso 2**, en
`frontend-react` (ver su `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`).
Antes de empezarlo hay que resolver la P1.

Producción ya tiene la tabla, así que se puede probar en local con el Colegio
Demo. Renombrar desde local cambia los nombres de verdad en el Colegio Demo de
producción; se deshace con "Volver a los originales". La rama de Neon de
prueba ya no se necesita.
