# Capa 7: boletin

Última revisión: 2026-08-21.

## Control

- Estado: **Activa** desde el 2026-08-21, con su subcapa **7.0 cerrada** el
  mismo día.
- Commit base: `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.1**, **sin definir todavía**. La define la
  evidencia de 7.0, que está abajo. No se inicia sin orden.
- Código de producto modificado al activar: **Ninguno**. Tampoco en 7.0: su diff
  es **un solo archivo de prueba nuevo** y ningún archivo rastreado modificado,
  igual que los de 5.0, 6.0 y las cuatro 7.0 anteriores.
- Dominio de esta capa: **boletin, y solo ese**. La capa 7 del índice es «resto
  de dominios» y ordena expresamente **priorizar uno a la vez**, así que esta
  bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-21. **El dominio lo
  nombró el usuario**, eligiéndolo de la lista de los ocho que quedaban en
  espera y **después de recibir en ese mismo turno la advertencia de que
  `boletin` no es una frontera limpia**. No se dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

### Relación con las bitácoras de `dashboard`, `notas`, `ventas` y `asistencia`

`07_DASHBOARD.md`, `07_NOTAS.md`, `07_VENTAS.md` y `07_ASISTENCIA.md` son las
bitácoras **cerradas** de los cuatro primeros dominios migrados bajo la capa 7.
Esta es la quinta, y es **independiente**: su commit base, sus subcapas, su
compuerta y su cierre son propios. Cerrar `boletin` no reabre ninguna de las
cuatro, ni al revés.

**Las subcapas se numeran por bitácora**, así que esta capa vuelve a empezar en
**7.0**. Existen por tanto una «7.0 de dashboard», una «7.0 de notas», una «7.0
de ventas» y una «7.0 de asistencia», las cuatro cerradas, y una «7.0 de
boletin», que es la pendiente. En prosa deben citarse siempre con el nombre del
dominio; el número solo no identifica una subcapa.

**`07_NOTAS.md` tiene aquí un peso que ninguna bitácora cerrada tuvo antes.** No
es solo un antecedente: **contiene parte de este dominio**. Su 7.0 fijó que
`notas` posee rutas de boletín, y su 7.1 cerró la frontera de persistencia de
esas rutas. Leerla no es opcional para 7.0, y **modificar lo que quedó dentro de
`notas` no está autorizado por esta activación**.

## Objetivo

Migrar el dominio de **boletin** con contratos y pruebas, conservando su
comportamiento observable actual.

El objetivo procede exclusivamente del índice maestro, que para esta capa fija
tres cosas y ninguna más:

1. priorizar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   **solo después** de caracterizar y **conservar** la respuesta existente;
3. **no crear abstracciones compartidas sin dos consumidores reales**.

La activación **no inspeccionó el código** y por eso **no afirma todavía** qué
endpoints, archivos, consultas, escrituras, cálculos, permisos o pruebas forman
este dominio. Esa determinación es trabajo de 7.0.

## Por qué este dominio es distinto de los cuatro anteriores

**Su frontera está partida, y se sabe antes de empezar.** Es la diferencia que
manda. `dashboard`, `notas`, `ventas` y `asistencia` se activaron sin saber
dónde terminaba el dominio; aquí el programa ya tiene registrado que **no
coincide con los nombres de archivo**:

- existe `app/routes/boletines.py`, inventariado por la capa 0;
- pero **`notas` posee `/boletin/{id}` y `/boletin/detallado/{id}`**, y sus
  controladores `boletin_estudiante_controller` y `boletin_detallado_controller`
  viven dentro de `notas_controller.py`, migrado y cerrado por la 7.1 de
  `notas`;
- **no hay colisión de paths**, comprobado por la 7.0 de `notas`, que listó las
  rutas de `boletines.py` justamente para descartarla.

La 7.0 de `notas` dejó escrito el aviso literal: «quien migre boletín o planilla
debe saber que **tres de sus rutas ya viven aquí**».

**Consecuencia práctica para 7.0**: el primer trabajo de esta subcapa no es
inventariar, es **decidir dónde está el borde** y registrarlo con evidencia. Las
rutas que ya viven en `notas` **están cerradas y no se mueven** sin una orden
explícita posterior a esa evidencia.

Otras dos diferencias, menores pero registradas:

- **Es el primer dominio de la capa 7 cuyo commit base ya está publicado y
  desplegado al activar.** `notas`, `ventas` y `asistencia` se activaron sobre
  bases que en algún momento estuvieron sin publicar. Aquí producción **ya
  corre** el código del commit base, así que un rollback de esta capa, si
  llegara a publicarse, **no sería local**.
- **Es el dominio con menos datos reales que ha tocado el programa.** La capa 3
  midió `tenant_2005`: `boletin_cabecera` tiene **3 filas** y `boletin_detalles`
  **4**. Eso hace la verificación manual más barata y, a la vez, **más pobre**:
  un error de agrupación o de promedio puede no manifestarse con cuatro filas.

## Perfil de riesgo esperado, **no verificado**

La capa 0 registró que las entradas bajo `/boletines` **guardan definitivas**.
Si 7.0 lo confirma, **el dominio escribe** y su perfil de riesgo es el de la
capa 5, como `notas`, `ventas` y `asistencia`. La activación **no lo da por
cierto**: es el supuesto 2 de la tabla de abajo.

Lo que sí está fijado y **no** es un supuesto de este dominio: el historial
académico **no se recalcula**. La capa 6 lo registró al tratar la desactivación
de asignaciones —«notas, asistencia y boletines son fotos del pasado»—, y esa
propiedad es un invariante que esta capa no puede alterar.

## Dependencias de capas anteriores

- **Capa 0**: el inventario de contratos incluye la fila «Boletines», con su
  router y su prueba. Es el punto de partida documental de 7.0.
- **Capa 1**: migró a `get_cursor()` los cinco sitios de `notas_controller.py`,
  dos de ellos de boletín, y **fijó por prueba** el N+1 de
  `boletin_detallado_controller`. Sus doce comprobaciones de caracterización
  siguen vivas.
- **Capa 3**: reparó `boletin_cabecera` y `boletin_detalles` en `tenant_2005`;
  las dos estaban entre las ocho tablas que no admitían inserciones.
- **Capa 4**: midió un camino de boletín de 13 materias en **4 consultas**.
- **Capa 6**: `boletin_controller` es uno de los nueve consumidores de
  `resolver_asignacion_academica_id_cursor`; las rutas `orden-boletin`
  pertenecen a `asignaciones`, ya migrado.
- **Capa 7 en `notas`**: cerró la persistencia de las rutas de boletín que
  `notas` posee y dejó el aviso de frontera partida.
- Evidencia de que la capa anterior está cerrada: `07_ASISTENCIA.md` marca
  Estado **Cerrada** el 2026-08-21, con compuerta **exit 0 y 872 pruebas** y
  verificación manual ejecutada; el índice lo confirma y no marca ninguna otra
  capa activa.

## Lo que el programa cree saber de `boletin`, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6 y que las cuatro capas 7 confirmaron:
**un supuesto heredado se marca como no verificado y se comprueba en la subcapa
0**. De los siete supuestos de `dashboard` **uno resultó falso**; de los diez de
`notas` **uno resultó incompleto**, y era el que fijaba la frontera del dominio;
de los doce de `ventas` **uno resultó falso**; de los doce de `asistencia`
**dos resultaron incompletos y ninguno falso**.

Ninguno de los de abajo procede de haber leído el código de `boletin`. Todos son
restos de lo que las capas 0, 1, 3, 4, 6 y 7 observaron desde fuera. La columna
de origen dice de dónde sale cada uno, para que 7.0 pueda contrastarlo.

**Los trece quedaron resueltos en 7.0**, uno por uno y con evidencia. **Doce se
confirmaron y uno resultó incompleto.** **Ninguno resultó falso**, como en
`asistencia`.

**El resultado que importa no es ese recuento, sino a quién describían.** Cinco
de los trece —el 5, el 6, el 8, el 9 y el 10— **hablaban de código que no
pertenece a este dominio**: viven en `notas`, migrado y cerrado. Es decir,
**más de un tercio de lo que el programa creía saber de `boletin` describía en
realidad el boletín de otro dominio**. Ningún dominio anterior tuvo un desvío
así, y confirma que la decisión de poner la frontera como paso 1 era la
correcta.

| # | Supuesto | Origen documental | Resultado en 7.0 |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/boletines.py` y en un `boletin_controller` | Inventario de contratos de 0.0 y subcapa 6.0, que nombra `boletin_controller` entre los nueve consumidores del resolver | **CONFIRMADO y precisado.** Son **tres archivos**: `app/routes/boletines.py` (86 líneas), `app/controllers/boletin_controller.py` (457) y `app/schemas/boletin.py` (16). **No existe repositorio ni servicio propio.** Es el segundo dominio de la capa 7 que llega sin repositorio |
| 2 | **El dominio escribe**: guarda notas definitivas | Inventario de contratos de 0.0: «guarda definitivas o consulta respaldo/planilla vigente» | **CONFIRMADO y cuantificado.** `guardar_boletin_controller` emite **1 UPSERT + 1 `DELETE` + N `INSERT`** en **una transacción propia** con `commit` y `rollback` explícitos. **Dos tablas escritas**, `boletin_cabecera` y `boletin_detalles`: es el único dominio de la capa 7 que escribe más de una. Perfil de riesgo de la capa 5, confirmado |
| 3 | **La frontera está partida**: `notas` posee `/boletin/{id}` y `/boletin/detallado/{id}` | Subcapa 7.0 de `notas`, supuesto 6 | **CONFIRMADO sobre el código de hoy.** `notas.router` sigue declarando `/boletin/{estudiante_id}` y `/boletin/detallado/{estudiante_id}`. Fijado por prueba |
| 4 | **No hay colisión de paths** entre `boletines.py` y las rutas de boletín de `notas` | Subcapa 7.0 de `notas` | **CONFIRMADO y ahora fijado por prueba.** El router del dominio lleva `prefix="/boletines"` y **las cuatro** entradas empiezan por `/boletines/`; los conjuntos de paths son **disjuntos** |
| 5 | `boletin_estudiante_controller` y `boletin_detallado_controller` viven en `notas_controller.py` y usan `get_cursor()` | Subcapa 1.4, tabla de los cinco sitios | **CONFIRMADO con matiz, y AJENO al dominio.** Siguen en `notas_controller.py` y siguen usando `get_cursor()`, pero su SQL vive desde la 7.1 de `notas` en `notas_repository`. **No es código de esta capa** |
| 6 | **Hay N+1**: `boletin_detallado_controller` ejecuta una consulta por asignación | Subcapa 1.4, fijado por prueba | **CONFIRMADO, y AJENO al dominio.** Sigue vivo, y `notas_repository` lo documenta en el docstring de `leer_notas_de_asignacion_en_periodo` como hallazgo abierto de **su** 7.0. **`boletin_controller` no tiene ningún N+1**: sus dos lecturas por lote usan `= ANY(%s)` |
| 7 | Un camino de boletín de **13 materias cuesta 4 consultas** | Medición de 4.0 sobre producción | **CONFIRMADO y reconciliado; no había contradicción.** Las 4 consultas son las de `obtener_boletin_admin_controller`, de **este** dominio, medidas y fijadas por prueba. El N+1 del supuesto 6 está en **otro** camino y en otro dominio. Los dos hechos eran ciertos a la vez |
| 8 | **Los ids de las actividades en blanco son sintéticos** y pueden colisionar con ids reales de `notas_detalle` | Subcapa 1.4 | **CONFIRMADO como AJENO.** Viven en `notas_repository`, dominio de `notas`. **No se corrigen desde esta capa** |
| 9 | **El corte Aprobado/Reprobado está en 3,0 inclusive**; el promedio general no tiene guarda de división por cero | Subcapa 1.4 | **CONFIRMADO como AJENO.** Está en `boletin_estudiante_controller`, dentro de `notas_controller.py`. La guarda de división por cero sigue siendo inalcanzable por el `return` previo |
| 10 | **El promedio general del boletín promedia valores sin redondear**; el detallado devuelve **`promedio: 0` fijo** | Subcapa 7.0 de `notas` | **INCOMPLETO, y es el único que lo queda.** Lo que describe es cierto, pero es de `notas`, y **omitía que este dominio tiene sus propias dos fórmulas**, distintas de esa: `AVG()` en SQL y `sum()/len()` en Python sin redondear. Ver el hallazgo 3 |
| 11 | `boletin_controller` **lee `notas_detalle`** | Subcapa 7.0 de `notas`, supuesto 5 | **CONFIRMADO y ampliado.** La leen **cuatro de las cinco funciones** del controlador. `notas_detalle` sigue siendo la tabla más compartida del programa y su dueño está migrado y cerrado |
| 12 | Las tablas son `boletin_cabecera` y `boletin_detalles`, con **3 y 4 filas** en `tenant_2005`, con cascada, y estuvieron entre las **ocho averiadas** de la capa 3 | Capas 3 y 6 | **Confirmado documentalmente**, sin cambio. Con el supuesto 2 ya confirmado, la cascada importa: **borrar una cabecera se lleva sus detalles** |
| 13 | `require_estudiante_in_asignacion` tiene **un punto de llamada en `boletines`**, y **no está en un bucle** | Medición del N+1 en conexiones de `asistencia` | **CONFIRMADO y cuantificado.** Se llama **una sola vez**, en la línea 30 del router y **fuera de todo bucle**. El coste **no crece** con el número de estudiantes: es la diferencia favorable frente a `asistencia` |

## Alcance autorizado

- **Determinar y registrar con evidencia dónde está la frontera del dominio**,
  antes que ningún otro trabajo. Es el primer paso de 7.0 y condiciona el resto.
- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de boletin** mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, orden, nulos, **promedios, redondeos,
  cortes de aprobación e ids sintéticos**, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado siete veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas **y conexiones** críticas antes y después. Las
  cuatro capas 7 anteriores demostraron que medir solo consultas esconde el
  coste real.
- **Leer** `notas_controller.py`, `notas_repository.py` y `app/routes/notas.py`
  lo indispensable para delimitar la frontera y documentar el punto de decisión.
  **Leer no es mover**: modificarlos exige una orden explícita posterior a la
  evidencia de 7.0.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: observaciones, planilla, planeador
  anual, plan de clases, branding, profesores, super admin y cualquier otro.
  Esta capa es de un solo dominio. Se permite la lectura mínima indispensable
  para caracterizar un contrato que `boletin` consuma o que consuma de
  `boletin`, sin modificarlo. **`planilla` queda fuera aunque comparta el mismo
  tipo de frontera partida.**
- **`pagos`, `estudiantes`, `asignaciones`, `dashboard`, `notas`, `ventas` y
  `asistencia`, ya migrados.** Sus fronteras de persistencia están cerradas y
  sus pruebas de caracterización deben seguir pasando. **Mover cualquier
  sentencia fuera de `notas_repository` no está autorizado por esta
  activación**, por mucho que la sentencia sea de boletín.
- `app/services/asignacion_academica.py`, del que dependen nueve módulos: se lee
  si hace falta, **no se toca**.
- `app/core/permissions.py`. Es infraestructura compartida que las seis capas
  anteriores declararon expresamente fuera de alcance. **Incluye el N+1 en
  conexiones que dejó `asistencia`**, con plan de corrección ya diseñado y
  aplazado: exige bitácora propia y orden explícita.
- Los hallazgos abiertos de las capas 5, 6 y 7. En particular el **paso 2 de la
  clave de idempotencia** de `POST /pagos`, la **ausencia de lock en el alta y
  la edición de asignaciones**, los **diez hallazgos de dashboard**, los **doce
  de notas**, los **once de ventas** y los **ocho de asistencia**. **No entran
  por inferencia**, por cerca que queden del código que esta capa toque.
- **Los ids sintéticos del boletín detallado y su N+1** son deuda registrada por
  la capa 1 y **no se corrigen aquí** salvo decisión explícita con evidencia.
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa».
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, **promedios, redondeos o cortes de aprobación**, orden o semántica
  transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos el **orden**, los **nulos** y la **agrupación**.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- **Las cifras son el contrato.** Promedios, redondeos, el corte
  Aprobado/Reprobado y los ids sintéticos se conservan exactamente, incluida la
  diferencia entre promediar valores redondeados y sin redondear. Un boletín es
  un documento que el colegio entrega: una cifra distinta no es un detalle.
- El historial académico **no se recalcula**: los boletines son fotos del
  pasado, conforme fijó la capa 6.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de los dominios ya migrados que tocan estas tablas o estas rutas
  siguen pasando su caracterización, **empezando por `notas`**.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.

## Línea base registrada en 7.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Compuerta heredada, **antes de tocar nada** | `.\venv\Scripts\python.exe scripts\verify.py` | **872 pruebas, exit 0.** Coincide exactamente con lo registrado al cerrar `asistencia`: **no había deriva** |
| Pruebas específicas nuevas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_boletin_caracterizacion.py` | **24 pasaron** en 0,60 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **896 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La suite pasó de **872 a 896** con la caracterización de 7.0.

## Inventario y contratos fijados en 7.0

**El dominio son tres archivos**, y es **el que más SQL inline conserva** de
todos los que ha migrado el programa en la capa 7:

| Archivo | Líneas | SQL inline |
|---|---:|---:|
| `app/routes/boletines.py` | 86 | 0 |
| `app/controllers/boletin_controller.py` | 457 | **12** |
| `app/schemas/boletin.py` | 16 | 0 |

**Cuatro entradas HTTP con tres modelos de permiso**:

| Método | Path | Permisos | Controlador |
|---|---|---|---|
| POST | `/boletines/guardar` | `get_current_user` + `require_asignacion_access` + `require_estudiante_in_asignacion` | `guardar_boletin_controller` |
| GET | `/boletines/referencia/{asignacion_id}/{periodo}` | `get_current_user` + `require_asignacion_access` | `obtener_boletin_para_profesor_controller` |
| GET | `/boletines/admin/generar/{estudiante_id}/{periodo}` | `get_current_active_admin` | `obtener_boletin_admin_controller` |
| GET | `/boletines/admin/reporte-parcial/{estudiante_id}/{periodo}` | `get_current_active_admin` | `obtener_reporte_parcial_admin_controller` |

Los cuatro guards corren **fuera del `try`**, así que un 403 **nunca se
convierte en 500**. Las dos entradas de admin reenvían `HTTPException` antes del
`except Exception`, así que su **404** tampoco. Fijado por prueba.

**El controlador tiene cinco funciones**, y **una no pertenece al dominio**:
`obtener_notas_planilla_controller` es de `planilla` y **no la importa nadie**.

### Frontera, decidida con evidencia

| Vive en | Rutas |
|---|---|
| **`boletin`**, este dominio | `/boletines/guardar`, `/boletines/referencia/…`, `/boletines/admin/generar/…`, `/boletines/admin/reporte-parcial/…` |
| **`notas`**, migrado y cerrado | `/boletin/{estudiante_id}`, `/boletin/detallado/{estudiante_id}` |

Los conjuntos de paths son **disjuntos** y el router del dominio lleva
`prefix="/boletines"`. **La frontera queda donde está**: 7.0 no mueve nada, y
mover las rutas de `notas` exigiría una orden explícita.

### Propiedad transaccional

`guardar_boletin_controller` es la **única escritura**. Abre con
`get_connection()`, es dueño de `commit` y `rollback`, cierra cursor y conexión
en `finally` y **propaga la excepción** tras revertir. El patrón es un
**reemplazo parcial**: `UPSERT` de la cabecera con
`ON CONFLICT (estudiante_id, asignacion_id, periodo) DO UPDATE`, `DELETE` de
todos los detalles de ese boletín y N `INSERT`. Fijado por prueba, incluido el
camino de error.

## Línea base de consultas y conexiones

Medida herméticamente con dobles y **fijada por aserción**. Las consultas
excluyen los dos round-trips que `get_connection()` emite siempre.

| Camino | Consultas | Conexiones (admin) | Conexiones (profesor) |
|---|---:|---:|---:|
| `POST /boletines/guardar` | **3 + N** | **2** | **3** |
| `GET /boletines/referencia/…` | **3** | **1** | **2** |
| `GET /boletines/admin/generar/…` | **4** | **1** | — |
| `GET /boletines/admin/reporte-parcial/…` | **2** | **1** | — |

**Ningún camino tiene N+1**, ni en consultas ni en conexiones. Las dos lecturas
por lote usan `= ANY(%s)`. `require_asignacion_access` **no abre conexión**
siendo admin —retorna antes— y `require_estudiante_in_asignacion` abre siempre
una, pero **una sola vez y fuera de todo bucle**.

Es la diferencia favorable frente a `asistencia`, donde pasar lista a un curso
de 30 costaba **31 conexiones siendo admin y 61 siendo profesor**. Aquí el coste
**no depende del número de estudiantes**.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Frontera, inventario, contratos, caracterización y línea base de consultas y conexiones | **Cerrada** el 2026-08-21 |
| 7.1 | Primera extracción protegida | **Sin definir**: la evidencia de 7.0 la perfila, pero no está decidida |
| 7.2 | Segunda extracción o punto de decisión | Sin definir |

El desglose se deja deliberadamente **sin decidir** hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las cuatro capas 7 anteriores. Las
subcapas innecesarias se marcarán `No aplica` con explicación. **Nunca se
ejecutan dos subcapas en el mismo turno.**

## Hallazgos de 7.0, registrados y sin corregir

Son **diez**. Ninguno se corrige desde esta capa; corregir cualquiera exige una
orden explícita. Van ordenados por gravedad.

1. **Las observaciones guardadas se emparejan por POSICIÓN, no por identidad.**
   En `obtener_boletin_para_profesor_controller`, el bucle
   `for i, nota in enumerate(est_data['notas'])` toma
   `saved['observaciones'][i]`. Las notas vienen ordenadas por `nd.id` y las
   observaciones por `bd.id`, dos secuencias independientes. **Si un profesor
   añade, borra o reordena una nota de la planilla, la observación guardada se
   pega a la nota equivocada.** Es el hallazgo más grave del dominio y es
   silencioso: no falla, muestra el texto de otra evaluación.
2. **La capa 1 no migró este archivo.** `boletin_controller.py` sigue entero en
   `get_connection()` y **no usa `get_cursor()` ni una vez**. Es el archivo con
   más SQL inline que queda sin repositorio, y el único dominio de la capa 7
   que llega con **un solo idioma**, el antiguo. Fijado por guardia.
3. **Dos formas de promediar dentro del propio dominio.**
   `obtener_boletin_admin_controller` promedia con `AVG(nd.nota)` **en SQL**;
   `obtener_reporte_parcial_admin_controller` lo hace con `sum()/len()` **en
   Python y sin redondear**. Aplican los mismos filtros, pero una redondea según
   `NUMERIC` de PostgreSQL y la otra devuelve el `float` crudo: con 3,0/4,0/4,0
   el reporte parcial da **3,6666666666666665**, ni 3,67 ni 3,66. Fijado por
   prueba.
4. **Una definitiva guardada como 0 se trata como ausente.**
   `COALESCE(NULLIF(bc.definitiva, 0), nd_prom.promedio_numerico)` sustituye el
   0 por el promedio calculado. Un estudiante con definitiva 0 legítima **no ve
   su 0**.
5. **`obtener_notas_planilla_controller` es código muerto de otro dominio.**
   Vive en el controlador de `boletin`, pertenece a `planilla`, gasta 1 de las
   12 sentencias inline y **no tiene ni un consumidor** en `app/` ni en
   `tests/`. Fijado por prueba, que recorre el árbol y lo comprueba.
6. **El reemplazo parcial borra siempre.** Un `POST /boletines/guardar` con
   `detalles: []` conserva la cabecera y **deja el boletín sin ningún detalle**.
   No hay guarda ni aviso. Fijado por prueba.
7. **`obtener_boletin_admin_controller` no cierra su cursor.** Su `finally`
   solo hace `conn.close()`. Las otras cuatro funciones cierran cursor y
   conexión. No es una fuga —cerrar la conexión cierra sus cursores—, pero es
   la única de las cinco que rompe el patrón.
8. **El `UPSERT` de la cabecera no filtra `activo`.** La asignación resuelta se
   escribe sin comprobar que siga activa. Es el mismo hallazgo que `dashboard`
   y `notas` dejaron abiertos en sus precondiciones de permiso.
9. **Catorce líneas con espacios finales** en el controlador, entre ellas
   `ON CONFLICT (estudiante_id, asignacion_id, periodo) `, dentro de un literal
   SQL. **Importa para 7.1**: `git diff --check` obliga a limpiarlos, y eso
   **rompería la comparación byte a byte** que las cuatro 7.1 anteriores
   exigieron. Hay que decidirlo antes de mover, no durante.
10. **`BoletinCreate` no valida rangos.** `periodo` es `int` sin cota y
    `definitiva` y `nota` son `float` opcionales sin límite: nada impide un
    periodo 99 ni una nota de 500.

### Lo que 7.0 buscó expresamente y **no** encontró

- **Ningún N+1**, ni en consultas ni en conexiones. Es el primer dominio de la
  capa 7 que se inventaría y sale limpio en esto.
- **Ninguna fuga de conexión**: las cinco funciones cierran en `finally`.
- **Ningún `except Exception` que devuelva el texto de la excepción al
  cliente.** Las cuatro entradas responden un mensaje fijo y registran con
  `logger.exception`. Es lo contrario de lo que hacían `dashboard` y
  `asistencia`, y **es un acierto del dominio que conviene no perder** en una
  extracción posterior. Fijado por prueba.
- **Ninguna colisión de paths** con las rutas de boletín de `notas`.
- **Ningún f-string en SQL** ni interpolación de parámetros.

## Subcapa 7.0 — trabajo exacto, ejecutado y cerrado

1. **Determinar la frontera antes que nada.** Listar las rutas declaradas por
   `app/routes/boletines.py` y las rutas de boletín declaradas por
   `app/routes/notas.py`, y registrar cuáles pertenecen a cada dominio.
   Comprobar de nuevo que **no hay colisión de paths**. Registrar el borde
   elegido **con evidencia**, no por nombre de archivo.
2. Inventariar entradas HTTP del dominio: método, path, permisos, payload de
   entrada, forma exacta de la respuesta y status codes, incluidos los de error.
3. Inventariar archivos: router, controlador, esquema, servicio y repositorio si
   existen. Contar sentencias SQL inline por archivo.
4. Determinar **si el dominio escribe**, qué tablas y con qué semántica
   transaccional; quién es dueño de `commit`, `rollback`, cursor y conexión.
5. Fijar por prueba las **cifras**: promedios, redondeos, corte
   Aprobado/Reprobado, ids sintéticos y el `promedio: 0` del detallado si
   persiste.
6. Medir **línea base de consultas y de conexiones** por camino, con dobles
   herméticos, y fijarla por aserción. Determinar si el N+1 del supuesto 6 sigue
   vivo y reconciliarlo con la medición de 4 consultas del supuesto 7.
7. Resolver **los trece supuestos** uno por uno, con evidencia, y registrar cuál
   se confirma, cuál es incompleto y cuál es falso.
8. Escribir la caracterización en `tests/test_boletin_caracterizacion.py`, un
   archivo nuevo. **No se reescriben ni se retiran** las pruebas heredadas.
9. Registrar hallazgos **sin corregir ninguno**.
10. Archivos permitidos: **un solo archivo de prueba nuevo** y esta bitácora. El
    diff de 7.0 **no debe modificar ningún archivo rastreado de producto**,
    igual que los de 5.0, 6.0 y las cuatro 7.0 anteriores.
11. Comandos de verificación: la compuerta global antes y después, las pruebas
    específicas, Ruff sobre el archivo nuevo y `git diff --check`.
12. **Punto exacto donde debe detenerse**: al cerrar 7.0 con su registro
    escrito. **No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de la subcapa 7.0

- La frontera del dominio queda registrada con evidencia y no por inferencia.
- Los trece supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable que fija contratos, cifras y línea base de
  consultas y conexiones.
- Compuerta global correcta y Ruff correcto.
- Diff exclusivo de la subcapa y sin duplicación heredada.
- Bitácora actualizada con archivos, comandos, resultados, decisiones y riesgos.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados. **Atención**: si esta
  capa llega a publicarse, el rollback **no será local**, a diferencia de las
  cuatro anteriores en el momento de su cierre.
- Siguiente capa autorizada por el usuario.

## Decisiones

- **Decisión de la activación: el dominio es `boletin` y solo ese.** Motivo: el
  índice ordena «uno a la vez». Alternativa descartada: activar `boletin` y
  `planilla` juntos por compartir el mismo tipo de frontera partida; se descarta
  porque duplicaría el alcance y ninguna capa del programa lo ha hecho.
- **Decisión de la activación: continuar aceptando las verificaciones heredadas
  como pendientes.** Motivo: el usuario eligió activar en vez de cerrarlas, tras
  recibir las cuatro salidas por escrito. **Ninguna se marca como cumplida** y
  su riesgo queda registrado abajo.
- **Decisión de la activación: no corregir `07_ASISTENCIA.md`.** Motivo:
  corregir una bitácora cerrada exige una orden propia. La autorización de este
  turno cubría **el índice**, y allí quedó registrado el cambio de estado de
  publicación.
- **Decisión aplazada a 7.0: dónde está el borde del dominio.** No se toma por
  inferencia en la activación. Las rutas de boletín que viven en `notas` están
  cerradas; moverlas exigiría una orden explícita posterior a la evidencia.

## Riesgos

- **Frontera partida.** Evidencia: 7.0 de `notas`, supuesto 6, confirmado.
  Mitigación: determinar el borde con evidencia como primer paso de 7.0 y no
  mover nada de `notas` sin orden. Responsable de validarlo: 7.0.
- **Las cifras son el contrato y aquí son varias.** Evidencia: capa 1 fijó el
  corte en 3,0 y los ids sintéticos; 7.0 de `notas` fijó el promedio sin
  redondear y el `promedio: 0` del detallado. Mitigación: fijarlas por prueba
  antes de tocar nada. Responsable: 7.0.
- **Parte del cálculo puede vivir en el frontend.** Evidencia: el comentario «El
  frontend recalcula luego» que registró la 7.0 de `notas`. Mitigación: una
  prueba de servidor no puede cubrir eso; debe quedar explícito en la
  verificación manual. Responsable: el usuario.
- **Pocos datos reales.** Evidencia: 3 y 4 filas en `tenant_2005`. Mitigación:
  la verificación manual debe usar un curso con notas reales, no el mínimo.
  Responsable: el usuario.
- **Consumidores ajenos ya migrados.** Evidencia: `notas_detalle` la leen siete
  módulos. Mitigación: ejecutar siempre la compuerta **completa**; romper un
  contrato ajeno no haría fallar las pruebas de `boletin`. Responsable: 7.0 y
  cada subcapa posterior.
- **El commit base ya está en producción.** Evidencia: `git ls-remote` del
  2026-08-21. Mitigación: documentar el rollback como no local desde el primer
  día. Responsable: el cierre de la capa.
- **Verificaciones heredadas pendientes**, aceptadas por decisión explícita:
  valor operativo final de `DB_STATEMENT_TIMEOUT_MS` de la capa 1; ausencia de
  evidencia de GitHub Actions desde la capa 0; los tres pasos del guion de
  `ventas` y los tres del de `asistencia` que no constan; y la **credencial
  privilegiada de la capa 4 sin rotar**. Ninguna se marca como cumplida.

## Registro de ejecución

### 2026-08-21 — activación de la capa para `boletin`

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local; el remoto se comprobó además contra el remoto real.
- Autorización: orden explícita del usuario en este turno, nombrando el dominio
  `boletin` al elegirlo de la lista de los ocho en espera. **No se pegó el
  bloque preparado** de `PROMPT_CONTINUACION.md`; la autorización llegó en
  conversación, en la misma orden que autorizó la corrección documental. La
  condición que ese bloque exige —nombrar el dominio explícitamente y no
  deducirlo— **se cumplió**. **La advertencia de frontera partida se entregó
  antes de la elección**, en el informe de estado del turno anterior.
- **Verificaciones heredadas**: se ofrecieron por escrito cuatro salidas
  concretas antes de escribir nada, incluida la de cerrarlas. **El usuario
  eligió activar.** Quedan registradas con su riesgo y **ninguna se marca como
  cumplida**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía **dos veces**; `HEAD` real
  `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, comprobado y no recordado.
- Continuidad: el base de la capa 7 para `asistencia`,
  `a894441f8676b0486e3395f88179cdf6cba61430`, existe y es ancestro de `HEAD`,
  verificado con `git merge-base --is-ancestor`. Sus **cinco** commits
  posteriores forman una historia lineal y **todos quedan explicados**: la
  activación `4e38e6c`, el cierre de 7.0 `68ff9a4`, la extracción de 7.1
  `4a4d9e1` y el cierre `e5b74d2` están en `07_ASISTENCIA.md`; el quinto,
  `8e61170`, es la medición del N+1 en conexiones y **está explicado en el
  índice**, no en la bitácora, que ya estaba cerrada cuando se escribió. Se
  verificó con `git show --stat`: toca **exactamente un archivo de documentación
  y ningún código**. **No es una divergencia de producto.**
- **Estado remoto comprobado, no supuesto**: `origin/main` está en
  `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, el mismo commit que `HEAD`,
  confirmado con `git rev-parse origin/main` y contra el remoto real con
  `git ls-remote origin main`. El reflog registra `update by push` de `e5b74d2`
  el 2026-08-21 a las **13:00:34 -0500** y de `8e61170` a las **13:03:27
  -0500**. **No se consultó ni se atribuye ningún run de GitHub Actions**; esa
  evidencia sigue sin obtenerse desde la capa 0.
- **Desfase documental corregido en el índice, con autorización explícita del
  usuario**: `07_ASISTENCIA.md` y el índice afirmaban que la capa 7 para
  `asistencia` **no estaba publicada** y que su rollback era «puramente local».
  **Ya no es cierto.** Producción corre ese código desde el push del 2026-08-21.
  Se preguntó al usuario antes de tocar nada y autorizó corregir **el índice**;
  la línea fechada se conserva intacta, conforme al criterio que la capa 4 fijó,
  y lo que se añade es la línea que registra el cambio de estado, colocada
  inmediatamente antes y marcada como sustituta. **`07_ASISTENCIA.md` no se
  editó.** Es el **tercer desfase consecutivo** del mismo tipo, tras `notas` y
  `ventas`, y el primero que el propio índice había anticipado por escrito.
- **Residuo documental corregido como parte de la activación**: el índice
  conservaba un encabezado que declaraba `asistencia` «en migración y activo».
  Dejarlo habría hecho que el índice marcara **dos** capas activas, lo que el
  protocolo obliga a tratar como ambigüedad y detenerse. Se corrigió a «migrado
  y cerrado» porque **marcar únicamente esta capa como activa es requisito de la
  propia activación**.
- **Residuo documental detectado y NO corregido**: el índice conserva, después
  de las líneas que cierran `ventas`, un párrafo que describe su punto de
  decisión como **abierto** y su verificación manual como **pendiente**, cuando
  las dos cosas se resolvieron. Ya estaba anotado al activar `asistencia` y
  sigue sin tocarse: **la autorización de este turno no lo cubría**.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  `boletin`** ni de ningún otro dominio, ni siquiera el listado de nombres de
  archivo. Los trece supuestos de la tabla de arriba salen **exclusivamente de
  la documentación del programa** —`00_LINEA_BASE_CALIDAD.md`,
  `01_FUNDACION_BASE_DATOS.md`, `03_MIGRACIONES_TENANTS.md`,
  `04_REPORTES_FINANCIEROS.md`, `06_ASIGNACIONES_ESTUDIANTES.md`,
  `07_NOTAS.md`, `07_ASISTENCIA.md` y el índice—, y cada uno lleva su origen
  anotado para que 7.0 pueda contrastarlo.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --abbrev-ref HEAD`,
  `git status --porcelain=v1`, `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git ls-remote origin main`, `git merge-base --is-ancestor`,
  `git log --oneline` desde el base de `asistencia`, `git reflog show
  origin/main` y `git show --stat`; todos con resultado coherente con la
  activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  `boletin`; **7.0 pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente **7.0** conforme al trabajo
  exacto de arriba y detenerse antes de 7.1. *(Ejecutada en el turno siguiente;
  ver el cierre de 7.0 más abajo.)*

### 2026-08-21 — cierre de 7.0

- Commit observado: `0f351c867b8a07e9c1f599b2cb31d82fdfc9fdc0`, el commit de
  activación, que el usuario creó entre los dos turnos. Árbol limpio antes de
  empezar, verificado con `git status --porcelain=v1` con salida vacía. El
  commit base `8e61170` sigue siendo el registrado y `0f351c8` es su único
  descendiente, explicado en esta bitácora.
- Estado remoto: `origin/main` sigue en `8e61170`, comprobado contra el remoto
  real. **La activación y 7.0 están sin publicar.**
- Archivos modificados: **`tests/test_boletin_caracterizacion.py`, nuevo**, y
  esta bitácora. **Ningún archivo rastreado de producto fue modificado**,
  verificado con `git status --porcelain=v1`, cuya única entrada de código es
  `?? tests/test_boletin_caracterizacion.py`.
- Archivos inspeccionados sin modificar: `app/routes/boletines.py`,
  `app/controllers/boletin_controller.py`, `app/schemas/boletin.py`,
  `tests/test_boletines_reporte_parcial.py`, y **solo para delimitar la
  frontera**, `app/routes/notas.py`, `app/controllers/notas_controller.py`,
  `app/repositories/notas_repository.py`, `app/core/permissions.py`,
  `app/services/asignacion_academica.py` y el registro de routers de
  `app/main.py`. **Leer no fue mover**: ninguno se tocó.
- Pruebas antes: **3 heredadas**, todas en `tests/test_boletines_reporte_parcial.py`,
  y **ninguna** medía conteos de consultas o conexiones, ni fijaba la frontera,
  ni cubría la escritura. El hueco era real y mayor que en `asistencia`.
- Cambio realizado: **solo caracterización**. 24 pruebas nuevas que fijan la
  frontera, las cuatro entradas con sus tres modelos de permiso, los status
  codes 403/404/500, la semántica transaccional completa incluida la reversión,
  las dos fórmulas de promedio, la línea base de consultas y de conexiones, y
  **cinco guardias estructurales**: número de archivos, ausencia de repositorio
  y servicio, conteo de 12 sentencias inline, idioma `get_connection` y el
  código muerto de `planilla`.
- Comandos y resultados:
  - `.\venv\Scripts\python.exe scripts\verify.py` **antes**: **872 pruebas,
    exit 0**, Ruff correcto, `pip check` íntegro. **Sin deriva** respecto al
    cierre de `asistencia`.
  - `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_boletin_caracterizacion.py`:
    **24 pasaron** en 0,60 s.
  - `.\venv\Scripts\python.exe -m ruff check tests\test_boletin_caracterizacion.py`:
    **correcto**.
  - `.\venv\Scripts\python.exe scripts\verify.py` **después**: **896 pruebas,
    exit 0**, Ruff correcto, `pip check` íntegro.
  - `git diff --check`: **sin problemas**.
- **Tres pruebas fallaron en su primera ejecución** y se corrigieron **en el
  doble, no en el producto**: el cursor falso servía el mismo resultado a todas
  las consultas de un camino, y los tres controladores que emiten dos o más
  lecturas distintas necesitaban una secuencia. Queda anotado porque **el fallo
  era del andamiaje**: ninguna aserción sobre comportamiento se relajó para que
  pasara.
- Decisiones:
  1. **La frontera se queda donde está.** Las dos rutas de boletín que posee
     `notas` no se mueven. Motivo: su 7.1 cerró esa persistencia y moverlas
     exigiría una orden explícita. Alternativa descartada: reunificar el boletín
     en un solo dominio, que habría reabierto una capa cerrada.
  2. **Los supuestos ajenos se marcan como ajenos, no como refutados.** Cinco
     de los trece describían código de `notas` y eran ciertos; lo que fallaba
     era la atribución. Registrarlos como falsos habría borrado información
     correcta.
  3. **No se corrige el emparejamiento por posición**, pese a ser el hallazgo
     más grave. Motivo: 7.0 caracteriza, no corrige. Queda fijado por prueba el
     comportamiento **actual**, para que una corrección futura tenga contra qué
     compararse.
- Riesgos: el hallazgo 9, los espacios finales dentro de un literal SQL, **es un
  riesgo para 7.1 y no para hoy**. Obliga a decidir por adelantado si la
  comparación byte a byte de las cuatro 7.1 anteriores se puede sostener aquí o
  si hay que autorizar explícitamente la limpieza.
- Siguiente acción exacta: **esperar la definición y la orden de 7.1.** No se
  inició ni se decidió su alcance.

## Entrega al próximo chat

- Capa activa: **7, para el dominio `boletin` y solo ese.** Los otros siete
  dominios siguen en espera.
- Última subcapa terminada: **7.0**, cerrada el 2026-08-21, el mismo día en que
  se activó la capa.
- Primera subcapa pendiente: **7.1**, **sin definir y no iniciada**. La
  evidencia de 7.0 la perfila —12 sentencias inline en un solo controlador, sin
  repositorio— pero **su alcance no está decidido** y hay que resolver antes el
  hallazgo 9. No se inicia sin orden.
- Commit base: `8e61170f32a6d6a23ca23f9ead89d17bc209e7b6`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real. La activación
  quedó en `0f351c8` y **7.0 está sin commitear** al cerrar este turno.
- Compuerta al cerrar 7.0: **896 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro. La suite pasó de **872 al activar la capa a 896**.
- Lo que 7.0 dejó medido: el dominio son **tres archivos**; **4 entradas HTTP**
  con **tres modelos de permiso**; **dos tablas escritas** —la primera vez en la
  capa 7 que un dominio escribe más de una—; **una transacción propia**; **12
  sentencias SQL inline**, todas en el controlador; **3 pruebas heredadas** más
  **24 nuevas**. **Ningún N+1**, ni de consultas ni de conexiones.
- **Los trece supuestos quedaron resueltos**: **doce confirmados y uno
  incompleto**, ninguno falso. Pero el resultado que manda es otro: **cinco de
  los trece describían código de `notas`, no de este dominio**. La frontera era
  el problema, y por eso fue el paso 1.
- **El hallazgo que manda es el emparejamiento por POSICIÓN** de las
  observaciones guardadas en `obtener_boletin_para_profesor_controller`. Es
  silencioso: no falla, muestra el texto de otra evaluación.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1), evidencia de GitHub Actions posterior a la
  capa 0, los **tres pasos del guion de `ventas`** y los **tres del de
  `asistencia`** que no constan. La credencial privilegiada de la capa 4 sigue
  **sin rotar**.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `dashboard`, `notas`, `ventas` y `asistencia` están
     cerrados en sus propias bitácoras y los otros siete siguen en espera.
  2. **La frontera quedó decidida y NO se mueve.** `notas` conserva
     `/boletin/{estudiante_id}` y `/boletin/detallado/{estudiante_id}`; este
     dominio son las cuatro rutas bajo `/boletines`. Los paths son disjuntos y
     hay una prueba que lo fija.
  3. **Nada de `notas` se mueve.** Su 7.1 cerró esa frontera de persistencia.
     Cinco de los trece supuestos hablaban de código suyo: el N+1 del detallado,
     los ids sintéticos, el corte en 3,0 y el promedio sin redondear **son de
     `notas`**, no de aquí.
  4. **Las cifras de ESTE dominio son otras**: `AVG()` en SQL para el boletín de
     admin y `sum()/len()` en Python **sin redondear** para el reporte parcial.
     Ambas fijadas por prueba.
  5. **Antes de mover una sola sentencia en 7.1, resolver el hallazgo 9**: hay
     14 líneas con espacios finales, una dentro de un literal SQL.
     `git diff --check` obliga a limpiarlos y eso **rompe la comparación byte a
     byte** que las cuatro 7.1 anteriores exigieron. Es una decisión previa, no
     un detalle de ejecución.
  6. **`app/core/permissions.py` está fuera de alcance**, incluido el N+1 en
     conexiones que dejó `asistencia`. Aquí ese N+1 **no existe**.
  7. **El commit base ya está en producción.** El rollback de esta capa, si se
     publica, **no será local**.
  8. **No corregir ninguno de los diez hallazgos**, empezando por el
     emparejamiento por posición, ni los cuarenta y uno que dashboard, notas,
     ventas y asistencia dejaron abiertos.
  9. **Ejecutar siempre la compuerta completa**: los consumidores de
     `notas_detalle` no fallan con las pruebas de este dominio.
  10. **Conservar el manejo de errores.** Las cuatro entradas devuelven un
      mensaje fijo y no filtran el texto de la excepción. Es un acierto del
      dominio y una extracción descuidada lo perdería.
- Siguiente acción exacta: **esperar la definición y la orden de 7.1.** 7.0 está
  cerrada; su alcance no está decidido y el hallazgo 9 hay que resolverlo antes.
  Una instrucción genérica de continuar **no** basta para fijar ese alcance.
