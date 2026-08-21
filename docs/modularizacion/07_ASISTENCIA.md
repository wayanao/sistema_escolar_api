# Capa 7: asistencia

Última revisión: 2026-08-20.

## Control

- Estado: **Activa** desde el 2026-08-20. **7.0 cerrada** el 2026-08-20.
- Commit base: `a894441f8676b0486e3395f88179cdf6cba61430`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.1**, **no iniciada**. Su alcance queda definido
  por la evidencia de 7.0; ver «Resultado de 7.0» y «Subcapa 7.1 — trabajo
  exacto».
- Código de producto modificado al activar: **ninguno**. Tampoco en 7.0: su diff
  es **un solo archivo de prueba nuevo** y ningún archivo rastreado modificado,
  igual que los de 5.0, 6.0 y las tres 7.0 anteriores.
- Dominio de esta capa: **asistencia, y solo ese**. La capa 7 del índice es
  «resto de dominios» y ordena expresamente **priorizar uno a la vez**, así que
  esta bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-20. **El dominio lo
  nombró el usuario**, eligiéndolo de la lista de los nueve que quedaban en
  espera y tras recibir las advertencias que las bitácoras cerradas ya
  registraban sobre esa lista. No se dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

### Relación con las bitácoras de `dashboard`, `notas` y `ventas`

`07_DASHBOARD.md`, `07_NOTAS.md` y `07_VENTAS.md` son las bitácoras **cerradas**
de los tres primeros dominios migrados bajo la capa 7. Esta es la cuarta, y es
**independiente**: su commit base, sus subcapas, su compuerta y su cierre son
propios. Cerrar `asistencia` no reabre ninguna de las tres, ni al revés.

**Las subcapas se numeran por bitácora**, así que esta capa vuelve a empezar en
**7.0**. Existen por tanto una «7.0 de dashboard», una «7.0 de notas» y una «7.0
de ventas», las tres cerradas, y una «7.0 de asistencia», que es la pendiente.
En prosa deben citarse siempre con el nombre del dominio; el número solo no
identifica una subcapa.

## Objetivo

Migrar el dominio de **asistencia** con contratos y pruebas, conservando su
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

## Por qué este dominio es distinto de los tres anteriores

Trae **dos novedades que ningún dominio de la capa 7 ha tenido**, y las dos
salen de que una capa anterior ya pasó por aquí.

**1. Es el primer dominio de la capa 7 que llega con pruebas de caracterización
ya escritas.** La subcapa 1.4g dejó `tests/test_asistencia_historial.py` con
**5 pruebas**, y el inventario de contratos de 0.0 ya apuntaba a
`tests/test_asistencia_validaciones.py`. `dashboard`, `notas` y `ventas`
empezaron los tres desde cero y su 7.0 escribió 41, 34 y 41 pruebas nuevas.
**Esto no adelanta trabajo por sí solo**: esas pruebas se escribieron para otra
cosa —proteger una migración del ciclo de vida de conexiones— y 7.0 **no puede
suponer que cubren lo que una extracción necesita**. Debe medirlas contra lo que
las otras tres 7.0 fijaron: payloads, permisos, status codes reales, conteos de
consultas **y de conexiones**, orden, nulos y transacciones.

**2. Es el primer dominio de la capa 7 que una capa anterior ya migró en
parte.** 1.4g tocó `app/controllers/asistencia_controller.py` y migró **1 sitio
de 2**: `obtener_historial_asistencia` pasó a `get_cursor()` y
`guardar_asistencia_controller` **no se tocó**, deliberadamente, porque ya
estaba protegida con `try/except/finally` y es el reemplazo parcial
transaccional que 0.0 registró como efecto a preservar. Es decir: **el dominio
tiene hoy dos idiomas de conexión conviviendo**, a diferencia de `ventas`, donde
las cinco funciones usaban `get_connection()` de forma uniforme. Qué implica eso
para la propiedad de `commit`, `rollback`, cursor y conexión es trabajo de 7.0.

Y comparte con `notas`, y **no** con `ventas`, el antecedente de la capa 3:
**`asistencia` sí fue una de las ocho tablas averiadas** de `tenant_2005` que no
admitían inserciones. Quedó reparada el 2026-08-13.

## Perfil de riesgo esperado

A diferencia de los tres dominios anteriores, aquí **el supuesto que manda no
está abierto**. En `dashboard`, `notas` y `ventas` la pregunta que fijaba el
perfil entero era «¿el dominio escribe?», y hubo que resolverla en 7.0. Aquí
llega **ya documentada, y por la capa 0, no por inferencia**: el inventario de
contratos de 0.0 registra como efecto a preservar un **«reemplazo parcial
transaccional con rollback probado»**, y 1.4g se abstuvo de tocar
`guardar_asistencia_controller` precisamente porque era esa transacción.

**El dominio escribe.** Su perfil de riesgo es el de la capa 5, `notas` y
`ventas`, no el de `dashboard`. Lo que 7.0 tiene que hacer no es descubrirlo
sino **cuantificarlo**: qué tablas, con qué transacción y quién es dueño de
`commit`, `rollback`, cursor y conexión.

Diferencias con `ventas`, y las dos importan:

- **No es el dominio financiero.** Los contratos de la capa 4 —6/15, 1/13/37 y
  5/12/12— no rodean este código. Un error aquí no da dinero mal contado; da
  **historial académico incorrecto**, que la capa 6 registró que **no se
  recalcula**.
- **Los permisos no parecen uniformes.** 0.0 los registró como «usuario
  autenticado con acceso a la asignación; estudiante debe pertenecer a ella»,
  con `403` y lote inválido `422`. Eso lo acerca a `notas` y `dashboard`, y lo
  aleja de `ventas`, que fue el primer dominio con un solo modelo. **No
  verificado**: es exactamente el supuesto que resultó falso en `ventas`.

Lo que comparte con todos los que escriben: las **26 claves foráneas repuestas
por la capa 3** siguen vigentes en `tenant_2005`, así que una inserción que
antes pasaba en silencio puede fallar hoy.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último
  resultado registrado, al cerrar la capa 7 para `ventas`, es **835 pruebas,
  exit 0**, Ruff correcto y `pip check` íntegro; **no se reprodujo durante esta
  activación documental**. 7.0 debe reproducirlo antes de tocar nada.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  **Esta es la primera capa 7 cuya capa 1 ya tocó el dominio**: ver 1.4g. El
  valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Sobre
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` sigue pesando el pendiente del
  2026-08-17: se quedó sin ejemplo real que la respalde. `dashboard` encontró
  caminos de **cuatro** conexiones, `notas` de **cuatro o cinco** y `ventas` de
  **una**. Si `asistencia` aporta un cuarto caso, se registra igual: **no se
  toca la constante**.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—. **`asistencia` fue una de las ocho tablas reparadas** y su
  volumen registrado entonces rondaba las **3.125 filas**.
- Contratos de lectura financieros fijados por la capa 4. **`asistencia` no
  entra en ellos**, que es la diferencia favorable frente a `ventas`.
- Frontera de persistencia de pagos establecida en la capa 5. Sin relación
  conocida con este dominio; 7.0 lo comprueba, no lo supone.
- Fronteras de estudiantes y asignaciones cerradas por la capa 6. **Dos cosas de
  esa capa alcanzan a este dominio**: `asistencia_controller` es uno de los
  **nueve módulos** que consumen `resolver_asignacion_academica_id_cursor`, y
  `estudiantes_repository` **lee `asistencia`** dentro del bloque rotulado como
  el expediente de un estudiante. Es un consumidor **ya migrado** cuyo contrato
  esta capa no puede romper.
- Fronteras de dashboard, notas y ventas cerradas por la capa 7, con
  `dashboard_repository` en 8 funciones, `notas_repository` en 9 y
  `ventas_repository` en 17. **`dashboard_repository` también lee `asistencia`**,
  para `GET /dashboard/inasistencias/{profesor_id}`. Sus 42, 34 y 41 pruebas de
  caracterización deben seguir pasando.

## Lo que el programa cree saber de `asistencia`, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6 y que las tres capas 7 confirmaron: **un
supuesto heredado se marca como no verificado y se comprueba en la subcapa 0**.
De los siete supuestos de `dashboard` **uno resultó falso**; de los diez de
`notas` **uno resultó incompleto**, y era el que fijaba la frontera del dominio;
de los doce de `ventas` **uno resultó falso**, y era el único marcado como
inferencia de patrón.

Ninguno de los de abajo procede de haber leído el código de `asistencia`. Todos
son restos de lo que las capas 0, 1, 3, 6 y 7 observaron desde fuera, **más una
inferencia de patrón marcada como tal**. La columna de origen dice de dónde sale
cada uno, para que 7.0 pueda contrastarlo.

**Los doce quedaron resueltos en 7.0**, uno por uno y con evidencia. **Diez se
confirmaron y dos resultaron incompletos.** **Ninguno resultó falso**, a
diferencia de `dashboard`, `notas` y `ventas`, donde siempre cayó uno.

| # | Supuesto | Origen documental | Resultado en 7.0 |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/asistencia.py` y `app/controllers/asistencia_controller.py` | Inventario de contratos de 0.0 y subcapa 1.4g | **INCOMPLETO.** Son **tres archivos, no dos**: existe además `app/schemas/asistencia.py`. Es el mismo tipo de fallo que en `notas`, pero **mucho menos grave**: allí el tercer y cuarto archivo escondían un tercio de la persistencia; aquí el tercero es el **contrato de entrada** y tiene **cero SQL**. No existe `app/services/asistencia_service.py` |
| 2 | **El dominio escribe**, con un reemplazo parcial transaccional y `rollback` | Inventario de contratos de 0.0, que lo registra como efecto a preservar | **CONFIRMADO y cuantificado.** `guardar_asistencia_controller` emite **1 `DELETE` + N `INSERT`** en **una transacción propia** con `commit` y `rollback` explícitos. **Una sola tabla escrita: `asistencia`.** Es el dominio que menos tablas escribe de los que escriben —`notas` escribía 1 también, `ventas` 4, `pagos` 6— |
| 3 | `guardar_asistencia_controller` conserva el idioma antiguo y `obtener_historial_asistencia` usa `get_cursor()` | Subcapa 1.4g, «1 sitio de 2» | **CONFIRMADO exactamente.** La escritura abre con `get_connection()` y cierra en `finally`; la lectura usa `with get_cursor() as cursor`. **Dos idiomas conviviendo**, fijado por aserción |
| 4 | **El controlador tiene exactamente dos funciones** | **Inferencia de patrón** a partir del «1 sitio de 2» de 1.4g | **CONFIRMADO, y conviene decir por qué eso no lo valida.** La bitácora lo marcó como el supuesto **con más probabilidad de resultar falso**, porque «sitio» en la capa 1 significaba apertura de conexión y no función. Acertó **por casualidad**: el controlador tiene exactamente `guardar_asistencia_controller` y `obtener_historial_asistencia`. Es la primera vez en el programa que una inferencia de patrón marcada como tal **se confirma**; en `ventas` la equivalente se refutó |
| 5 | **Los permisos no son uniformes** | Inventario de contratos de 0.0 | **CONFIRMADO.** El router exige `get_current_user` para las dos entradas; **ambas** exigen `require_asignacion_access`; **solo la escritura** exige además `require_estudiante_in_asignacion`. Son **dos modelos en dos entradas**. `ventas` sigue siendo el único dominio con permisos uniformes |
| 6 | Consume `resolver_asignacion_academica_id_cursor` | Subcapa 6.0, que enumeró los nueve consumidores | **CONFIRMADO.** Lo llaman **los dos caminos**, y cuesta **1 consulta** sobre el cursor que recibe: no abre conexión propia |
| 7 | `estudiantes_repository` **lee `asistencia`** en el bloque del expediente | Subcapa 6.2 | **CONFIRMADO.** Una sola lectura, `contar_inasistencias`, un `count(*)` con `estado ILIKE 'ausente'` |
| 8 | `dashboard_repository` **lee `asistencia`** para `GET /dashboard/inasistencias/{profesor_id}` | Subcapas 7.0 y 7.1 de `dashboard` | **CONFIRMADO.** Una sola lectura, un CTE con `ROW_NUMBER()` por curso, `a.estado ILIKE 'ausente'` y `posicion_curso <= 3` |
| 9 | **El estado se compara por texto**, con `ILIKE 'ausente'` | Guion de verificación manual de la capa 6 y contrato de `dashboard` | **CONFIRMADO y delimitado, que era el trabajo.** El criterio vive **enteramente fuera del dominio**: en los dos consumidores ajenos. **Ninguna de las tres sentencias del dominio usa `ILIKE`.** El dominio escribe un `estado` restringido por `Literal` a minúsculas y **los dos lectores no se apoyan en esa restricción** |
| 10 | Existen ya `tests/test_asistencia_historial.py` —5 pruebas— y `tests/test_asistencia_validaciones.py` | Subcapa 1.4g e inventario de 0.0 | **INCOMPLETO, en la dirección favorable.** Son **12 pruebas heredadas, no 5**: 5 en historial y **7** en validaciones. Pero **el hueco es real**: ninguna mide conteos de consultas ni de conexiones, ninguna observa un status code HTTP —todas llaman a las funciones de ruta directamente— y ninguna deja guardias estructurales. Ver «El hueco de las pruebas heredadas» |
| 11 | Contratos ya fijados por 1.4g: `fecha` nula, `periodo` 1 por defecto, agrupación | Subcapa 1.4g | **CONFIRMADO en código.** La guarda `if r[3]` conserva al estudiante con historial vacío, la firma es `periodo=1` y el diccionario agrupa por `estudiante_id` |
| 12 | `asistencia` fue una de las **ocho tablas averiadas** de `tenant_2005`, con ~3.125 filas, y tiene clave foránea **a `asignaciones`** con `ON DELETE CASCADE` y **a `estudiantes`** | Capa 3 y subcapa 6.0 | **Confirmado documentalmente**, sin cambio. Relevante para 7.1: el dominio **sí emite un `DELETE`**, aunque acotado por `asignacion_id`, `fecha`, `periodo` y la lista de estudiantes |

## Alcance autorizado

- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de asistencia** mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, orden, nulos, **fechas, periodos y
  estados**, transacciones y errores.
- **Medir qué cubren realmente las pruebas heredadas** de 1.4g y del inventario
  de 0.0, y completarlas hasta el nivel que fijaron las otras tres 7.0. No se
  reescriben ni se retiran sin evidencia.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado seis veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas **y conexiones** críticas antes y después. Las
  tres capas 7 anteriores demostraron que medir solo consultas esconde el coste
  real, y aquí importa doble porque el dominio tiene dos idiomas de conexión.
- **Leer** `estudiantes_repository.py` y `dashboard_repository.py` lo
  indispensable para clasificar sus lecturas de `asistencia` y documentar el
  punto de decisión. **Leer no es mover**: modificarlos exige una orden
  explícita posterior a la evidencia de 7.0.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: boletín, observaciones, planilla,
  planeador anual, plan de clases, branding, profesores, super admin y
  cualquier otro. Esta capa es de un solo dominio. Se permite la lectura mínima
  indispensable para caracterizar un contrato que `asistencia` consuma o que
  consuma de `asistencia`, sin modificarlo.
- **`pagos`, `estudiantes`, `asignaciones`, `dashboard`, `notas` y `ventas`, ya
  migrados.** Sus fronteras de persistencia están cerradas y sus pruebas de
  caracterización deben seguir pasando. **Mover cualquier sentencia fuera de
  `estudiantes_repository` o de `dashboard_repository` no está autorizado por
  esta activación.**
- `app/services/asignacion_academica.py`, del que dependen nueve módulos, y
  `app/services/cobros.py`, del que dependen los contratos financieros de la
  capa 4: se leen si hace falta, **no se tocan**.
- Los hallazgos abiertos de las capas 5, 6 y 7. En particular el **paso 2 de la
  clave de idempotencia** de `POST /pagos`, los status codes 500 de
  `tipos_pagos_controller`, la **ausencia de lock en el alta y la edición de
  asignaciones**, el `SELECT *` de `GET /estudiantes/{id}`, los **diez hallazgos
  de dashboard**, los **doce de notas** y los **once de ventas**, empezando por
  la colisión del `ILIKE` al anular. **No entran por inferencia**, por cerca que
  queden del código que esta capa toque.
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa».
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, **fechas, periodos, estados**, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos el **orden**, los **nulos** y la **agrupación** del
  historial que 1.4g fijó.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción, incluida la comprobación de que el estudiante pertenece a la
  asignación.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1. **El dominio escribe, así que esta invariante es la más
  delicada de la capa**, y el reemplazo parcial transaccional con `rollback` es
  un efecto que 0.0 registró expresamente como preservable.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de los dominios ya migrados que leen esta tabla siguen pasando
  su caracterización: el expediente de `estudiantes_repository` y las
  inasistencias de `dashboard_repository`.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.
- Ninguna escritura de archivos cambia de momento, de nombre ni de destino sin
  una decisión explícita y un rollback documentado.

## Línea base registrada en 7.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Compuerta heredada, **antes de tocar nada** | `.\venv\Scripts\python.exe scripts\verify.py` | **835 pruebas, exit 0.** Coincide exactamente con lo registrado al cerrar `ventas`: **no había deriva** |
| Pruebas específicas nuevas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_asistencia_caracterizacion.py` | **34 pasaron** en 0,85 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **869 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La suite pasó de **835 a 869** con la caracterización de 7.0.

## Inventario y contratos fijados en 7.0

**El dominio son tres archivos**, y es **el más pequeño que ha migrado el
programa** en superficie y en SQL:

| Archivo | Líneas | Sentencias SQL |
|---|---:|---:|
| `app/routes/asistencia.py` | 48 | **0** |
| `app/controllers/asistencia_controller.py` | 84 | **3** |
| `app/schemas/asistencia.py` | 10 | **0** |

Tres sentencias frente a las 17 de `ventas`, las 9 de `notas` y las 8 de
`dashboard`.

**Dos entradas HTTP**, sin prefijo de router:

| Método y path | Controlador | Escribe |
|---|---|---|
| `POST /asistencia` | `guardar_asistencia_controller` | **sí** |
| `GET /asistencia/historial/{asignacion_id}/{periodo}` | `obtener_historial_asistencia` | no |

**Permisos: dos modelos en dos entradas.** El router entero exige
`Depends(get_current_user)`. Las dos entradas exigen `require_asignacion_access`
—que deja pasar a `admin` sin consultar y comprueba `profesor_id` para un
profesor—. **Solo la escritura** exige además `require_estudiante_in_asignacion`.
No aparece `get_current_active_admin` por ninguna parte.

### Propiedad transaccional y los dos idiomas

La escritura abre con **`get_connection()`**, el idioma anterior a la capa 1, y
cierra con `try` / `except` / `finally`: `commit` al final, `rollback` y `raise`
ante cualquier excepción, `cursor.close()` y `conn.close()` siempre. La lectura
usa **`with get_cursor() as cursor`**, migrada por 1.4g. **El controlador es
dueño del ciclo de vida en los dos caminos**, fijado por aserción.

**Una sola transacción propia** y **una sola tabla escrita**, `asistencia`, con
`DELETE` e `INSERT`. La escritura es un **reemplazo parcial**: borra las filas
de esa asignación, fecha y periodo **solo para los estudiantes del lote**, y
reinserta.

## Línea base de consultas y conexiones

Medida con dobles. Aquí está el hallazgo principal de la subcapa, y **no se ve
midiendo solo el controlador**: hay que medir el camino HTTP completo, porque el
coste vive en el bucle de permisos de la ruta.

| Camino | Conexiones | Consultas |
|---|---:|---|
| `guardar_asistencia_controller`, N estudiantes | 1 | **N + 2** |
| `obtener_historial_asistencia` | 1 | **2** |
| `POST /asistencia` como **admin**, N estudiantes | **N + 1** | 2N + 2 |
| `POST /asistencia` como **profesor**, N estudiantes | **2N + 1** | 3N + 2 |
| `GET /asistencia/historial/...` como admin | 1 | 2 |
| `GET /asistencia/historial/...` como profesor | 2 | 3 |

**No hay N+1 en consultas por estudiante ajeno al lote**: los conteos variables
dependen del tamaño del lote, que es el curso que se está pasando. Pero **sí hay
N+1 en CONEXIONES**, y es el hallazgo 1.

Detalle medido: `resolver_asignacion_academica_id_cursor` cuesta **1 consulta**
sobre el cursor que recibe y **no abre conexión propia**, en los dos caminos.

## El hueco de las pruebas heredadas

Este dominio llegó con **12 pruebas** —5 en `test_asistencia_historial.py` y 7
en `test_asistencia_validaciones.py`—, más de las 5 que el supuesto 10
anticipaba. **El hueco es real de todos modos**, y se midió punto por punto
contra lo que fijaron las 7.0 de dashboard, notas y ventas:

| Lo que una 7.0 fija | ¿Lo cubrían las heredadas? |
|---|---|
| Guardias estructurales de línea base | **No.** Ninguna |
| Conteos de consultas | **No.** Ninguna |
| Conteos de **conexiones** | **No.** Ninguna — y es donde estaba el hallazgo |
| Status codes **HTTP reales** | **No.** Las cuatro que comprueban un 422 **llaman a la función de ruta directamente** y leen `HTTPException`, sin observar nunca una respuesta HTTP |
| Frontera del dominio y modelo de permisos | **No** |
| Contratos de la respuesta y de la agrupación | **Sí**, y bien: las 5 de historial |
| Transacción, `rollback` y reemplazo parcial | **Sí**, dos de validaciones |

Es exactamente la limitación que 7.0 de `notas` destapó para todo el programa:
**no existe ni un solo `TestClient` en `tests/`**. 7.0 de `asistencia` la cierra
para su dominio midiendo por **interfaz ASGI cruda**, como hicieron `notas` y
`ventas`. **Ninguna prueba heredada se retiró ni se reescribió.**

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas y conexiones | **Cerrada** el 2026-08-20 |
| 7.1 | Extraer las 3 sentencias a `asistencia_repository` sin cambiar SQL, conteos ni ciclo de vida | **Pendiente, no iniciada** |
| 7.2 | Punto de decisión: `response_model`, errores de dominio y el N+1 en conexiones | **Sin decidir**: es un punto de decisión, no una subcapa pendiente |

El desglose se dejó deliberadamente sin decidir hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las tres capas 7 anteriores. Con esa
evidencia, **7.1 queda definida** y el resto sigue abierto. Las subcapas
innecesarias se marcarán `No aplica` con explicación. **Nunca se ejecutan dos
subcapas en el mismo turno.**

## Hallazgos de 7.0, registrados y sin corregir

Son **ocho**. Ninguno se corrige en esta capa: 7.0 inventaría y caracteriza, no
arregla. Todos quedan fijados por aserción para que una extracción posterior no
los cambie sin que alguien lo note.

1. **N+1 en CONEXIONES, y es el peor perfil que ha medido el programa.**
   `require_estudiante_in_asignacion` **abre su propia conexión** y la ruta la
   llama **una vez por estudiante del lote**. Siendo admin, guardar la
   asistencia de un curso de 30 abre **31 conexiones en serie**; siendo
   profesor, **61**, porque `require_asignacion_access` también abre la suya.
   El pool tiene **10 conexiones** y el limitador de la capa 2 deriva **5
   workers**. `dashboard` encontró 4 conexiones y `notas` 4 o 5; **este es el
   primero cuyo número crece con el tamaño de la entrada.** Las dos funciones
   viven en `app/core/permissions.py`, **infraestructura compartida y fuera de
   alcance**, igual que `require_estudiante_access` lo estuvo para `notas`.
   Verificado por aserción con lotes de cinco.
2. **El permiso de asignación se comprueba N veces con el mismo argumento.** La
   ruta **ya validó** que los N registros comparten `asignacion_id`, y aun así
   llama a `require_asignacion_access` una vez por estudiante con el mismo
   valor. Es desperdicio puro. La prueba heredada
   `test_guardar_asistencia_valida_permisos_y_envia_lote` **ya lo fijaba por
   aserción** —espera `[(10, 3), (10, 3)]`— sin señalarlo como defecto.
3. **Las tres validaciones de lote viven en la capa de rutas.** Que el lote no
   esté vacío, que los registros compartan asignación, fecha y periodo, y que no
   haya estudiantes duplicados: las tres son **reglas de dominio** y ninguna se
   repite en el controlador. Es el simétrico del hallazgo de `/mis-clases` de la
   capa 6: allí había SQL de dominio en la ruta; aquí hay **reglas** de dominio.
4. **Y esa ubicación tiene consecuencia medible.** El `DELETE` toma `fecha` y
   `periodo` de **`data[0]`** mientras cada `INSERT` usa los **del item**. Hoy
   es inocuo porque la ruta valida antes que coincidan, pero **quien llame al
   controlador directamente** con un lote heterogéneo borraría por un contexto e
   insertaría por otro. Fijado por aserción.
5. **El controlador no valida `estado`.** Inserta `item.estado` crudo; el
   `Literal["presente", "ausente"]` del esquema **solo protege el camino HTTP**.
   Comprobado: llamando al controlador con `"EXCUSA"` se escribe `"EXCUSA"`.
6. **El `ILIKE 'ausente'` vive enteramente fuera del dominio.** El dominio
   escribe un valor restringido a minúsculas y **ninguna de sus tres sentencias
   usa `ILIKE`**; los **dos** consumidores ajenos ya migrados sí lo usan, sin
   apoyarse en esa restricción. No es un defecto activo —`ILIKE` sin comodines
   es igualdad sin distinguir mayúsculas—, pero significa que **el contrato del
   campo no está donde parece**: una fila heredada con `"Ausente"` la cuentan
   los dos lectores y el dominio ya no puede producirla.
7. **La lectura no tiene `try/except`.** Solo la escritura lo tiene, y su
   `except` hace `rollback` y **reenvía**. Un fallo de infraestructura en
   cualquiera de las dos entradas sale como **500**, no como 4xx. Es el mismo
   hallazgo que 7.0 de `notas` registró para su dominio entero.
8. **Ninguna de las dos entradas declara `response_model`.** No es un defecto;
   se fija por aserción para que añadirlo **no entre por inferencia** en 7.1.

### Lo que 7.0 buscó expresamente y **no** encontró

- **El patrón del falso éxito de `POST /notas` no está aquí.** Medido por ASGI,
  `POST /asistencia` responde **200** con `{"mensaje": "Asistencia guardada"}`
  solo cuando la transacción confirma; un lote vacío responde **422**, un lote
  heterogéneo **422** y un `estado` desconocido **422**, este último rechazado
  por Pydantic antes de llegar al controlador. **El cliente siempre se entera.**
- **No hay `SELECT *`**, ni f-strings en SQL, ni código muerto, ni una segunda
  definición de ninguna función. El dominio es pequeño y está limpio en todo lo
  que las tres capas 7 anteriores encontraron sucio.
- **No toca `storage`**: el rollback no necesita cubrir archivos.

## Subcapa 7.0 — trabajo exacto, ejecutado y cerrado

1. **Reproducir la compuerta heredada antes de tocar nada** y comprobar que da
   **835 pruebas y exit 0**.
2. **Determinar la frontera real del dominio** por búsqueda dirigida, sin
   fiarse de los nombres de archivo. Es la lección directa de `notas`: allí el
   supuesto de dos archivos escondía un tercio de la persistencia en un
   servicio. Buscar **por tabla y por símbolo**, no por nombre.
3. **Inventariar las entradas HTTP** con su método, path, permisos, roles,
   payload de entrada y forma exacta de la respuesta.
4. **Cuantificar la escritura**: qué tablas, con qué transacción, y quién es
   dueño de `commit`, `rollback`, cursor y conexión. Documentar expresamente
   **cómo conviven los dos idiomas de conexión** que 1.4g dejó, si siguen ahí.
5. **Medir qué cubren realmente las pruebas heredadas** de 1.4g y de 0.0, punto
   por punto contra lo que fijaron las 7.0 de dashboard, notas y ventas.
   Registrar el hueco antes de escribir nada nuevo. **No retirarlas.**
6. **Contar las sentencias SQL inline** del dominio, por archivo.
7. **Fijar la línea base de consultas y conexiones** de cada camino, con
   dobles, como hicieron las tres 7.0 anteriores.
8. **Clasificar las lecturas de `asistencia` que viven fuera del dominio**, en
   `estudiantes_repository` y `dashboard_repository`, para documentar el punto
   de decisión. **Sin mover ninguna.**
9. **Mapear dónde se compara el estado por texto** con `ILIKE 'ausente'` y si el
   propio dominio lo usa al escribir. **Buscarlo, no corregirlo.**
10. **Resolver los doce supuestos** de la tabla de arriba, uno a uno y con
    evidencia, dejando constancia de cuáles se confirman, cuáles se refutan y
    cuáles resultan incompletos.
11. **Medir los status codes con peticiones HTTP reales**, por la interfaz ASGI
    cruda, como hicieron `notas` y `ventas`. El dominio escribe y 0.0 registró
    un `422` por lote inválido: conviene verlo, no deducirlo.
12. **Registrar los hallazgos sin corregir ninguno.**
13. Archivos permitidos: **un archivo de prueba nuevo** y esta bitácora. Ningún
    archivo de producto, como en 5.0, 6.0 y las tres 7.0 anteriores.
14. Verificación: pruebas específicas, compuerta global, Ruff, `pip check`,
    `git diff --check` y revisión del alcance del diff.
15. **Punto exacto donde detenerse**: con 7.0 cerrada y su bitácora actualizada.
    **No iniciar 7.1**, ni siquiera si la extracción parece evidente.

## Criterios de cierre de la subcapa 7.0

- El dominio queda inventariado: archivos, entradas HTTP, permisos, tablas
  leídas y escritas, transacciones y sentencias inline.
- Los doce supuestos quedan resueltos uno a uno, con evidencia.
- La línea base de consultas **y conexiones** queda fijada por aserción.
- **El hueco entre lo que cubren las pruebas heredadas y lo que una extracción
  necesita queda medido y registrado.**
- El punto de decisión sobre las lecturas ajenas queda documentado con
  evidencia, **y sin resolver por inferencia**.
- Los hallazgos quedan registrados **sin corregir**.
- Pruebas específicas, compuerta global, Ruff y dependencias correctos.
- Diff exclusivo de la subcapa: un archivo de prueba nuevo y esta bitácora.
- `git diff --check` correcto.

Estado de los nueve criterios al 2026-08-20:

| Criterio | Estado |
|---|---|
| Dominio inventariado | **Cumplido**: 3 archivos, 2 entradas, 2 modelos de permiso, 1 tabla escrita, 1 transacción propia y 3 sentencias inline |
| Doce supuestos resueltos | **Cumplido**: **diez confirmados y dos incompletos**; ninguno falso |
| Línea base de consultas y conexiones | **Cumplido**: seis caminos fijados por aserción, incluidos los dos de la ruta completa que destaparon el N+1 en conexiones |
| Hueco de las pruebas heredadas medido | **Cumplido**: tabla punto por punto; **ninguna se retiró ni se reescribió** |
| Punto de decisión sobre las lecturas ajenas documentado sin resolver | **Cumplido**: las dos lecturas quedan clasificadas y fijadas por prueba; **no se movió ninguna** |
| Hallazgos registrados sin corregir | **Cumplido**: ocho, ninguno corregido |
| Pruebas, compuerta, Ruff y dependencias | **Cumplido**: 34 específicas y **869 globales, exit 0** |
| Diff exclusivo | **Cumplido**: un archivo de prueba nuevo; **ningún archivo rastreado modificado** |
| `git diff --check` | **Cumplido**: limpio |

**Los nueve criterios quedan resueltos. La subcapa 7.0 queda cerrada.**

## Subcapa 7.1 — trabajo exacto

Queda **definida por la evidencia de 7.0** y **no iniciada**.

1. Crear `app/repositories/asistencia_repository.py`, **el noveno repositorio**
   del proyecto, con funciones que **reciben el cursor existente** y no abren ni
   cierran nada. La propiedad de conexión, `commit` y `rollback` **se queda en
   el controlador**, en **los dos idiomas**: la escritura seguirá con
   `get_connection()` y la lectura con `get_cursor()`.
2. Mover las **3 sentencias** conservando su texto **byte a byte**. Si alguna
   necesitara cambiar de texto, **pedir autorización explícita**, como hizo 5.1
   y como no necesitaron la capa 6 ni las tres capas 7.
3. **No unificar los dos idiomas de conexión.** Sería una mejora real y
   **cambiaría los conteos fijados por aserción**: queda como trabajo
   disponible.
4. **No tocar el N+1 en conexiones.** Vive en `app/core/permissions.py`,
   infraestructura compartida y fuera de alcance. Corregirlo exige orden
   explícita y probablemente una auditoría de capacidad propia, que es el
   pendiente que la capa 2 dejó abierto.
5. **No mover las dos lecturas ajenas** de `estudiantes_repository` y
   `dashboard_repository`. Ese es el punto de decisión de 7.2, no de 7.1, y
   ampliaría el diff a módulos que las capas 6 y 7 cerraron.
6. Conservar los **conteos de consultas y de conexiones** exactamente como 7.0
   los fijó.
7. Ejecutar el **comparador AST contra el commit base** `a894441` para demostrar
   conjunto de SQL idéntico y literales byte a byte, **y además la comprobación
   de `(SQL, parámetros)` y retorno** que 7.1 de `ventas` incorporó al programa.
   Con tres sentencias y dos caminos es barata y cierra el hueco de evidencia.
8. Las **tres guardias de línea base** que 7.0 dejó puestas
   —`test_el_dominio_todavia_no_tiene_repositorio_propio`,
   `test_las_tres_sentencias_viven_hoy_en_el_controlador` y
   `test_la_ruta_no_contiene_sql`— **deben fallar las dos primeras y seguir en
   verde la tercera**. Es la señal esperada, lección 14 de la capa 6, aplicada
   por quinta vez. Se sustituyen por versiones positivas.
9. **Revisar antes las pruebas de hallazgo ancladas a un archivo concreto.** Es
   la lección que 7.1 de `ventas` aprendió: preveía dos fallos y fueron cuatro,
   porque dos pruebas de hallazgo también eran guardias sin estar rotuladas. En
   este archivo son candidatas `test_el_borrado_toma_el_contexto_del_primer_registro`,
   `test_las_tres_validaciones_de_lote_viven_en_la_ruta` y
   `test_el_dominio_no_tiene_ningun_try_except_propio_en_la_lectura`.
10. **Ejecutar la compuerta completa**, no solo las pruebas del dominio: las
    **dos** guardias que enumeran el conjunto exacto de repositorios, en
    `test_dashboard_caracterizacion.py` y `test_notas_caracterizacion.py`,
    **volverán a fallar al aparecer el noveno**, igual que con el séptimo y el
    octavo. La de este archivo también.
11. **No corregir ninguno de los ocho hallazgos.**
12. Punto exacto donde detenerse: con 7.1 cerrada y su bitácora actualizada.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- El dominio queda migrado con contratos estables y pruebas, **sin arrastrar
  otros dominios**.
- `response_model`, errores de dominio y pruebas HTTP, si se añadieron, llegaron
  **después** de caracterizar y conservando la respuesta existente, demostrado.
- No se creó ninguna abstracción compartida sin dos consumidores reales.
- Los contratos del frontend y de la base de datos permanecen intactos, y
  también los de los seis dominios ya migrados, en particular el expediente de
  `estudiantes_repository` y las inasistencias de `dashboard_repository`.
- **El punto de decisión sobre las lecturas ajenas queda resuelto de forma
  explícita**, se mueva o no se mueva nada, con su evidencia y su alternativa
  descartada.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados. **El dominio
  escribe, así que el rollback debe cubrir datos explícitamente** y no puede
  declararse «puramente de código» sin comprobarlo.
- El índice maestro queda actualizado y **ningún otro dominio se activa sin
  orden explícita del usuario**.

## Decisiones

- Se usa `a894441f8676b0486e3395f88179cdf6cba61430` como commit base porque es
  el `HEAD` limpio vigente de `main`, coincide con `origin/main` y con el
  remoto real, y el reflog lo registra como publicado por push el 2026-08-20 a
  las 16:21:16. Alternativa descartada: reutilizar el base de `ventas`,
  `58c5233`, que dejaría fuera de auditoría los cinco commits de esa capa.
- **El dominio lo eligió el usuario.** Se le presentó la lista de los nueve que
  quedaban en espera con las advertencias que las bitácoras cerradas ya
  registraban: que `boletin` y `planilla` no son fronteras limpias porque
  `notas` ya posee esas rutas; que `branding` y `super_admin` cambian el perfil
  de riesgo, el primero por `storage.py` y el segundo por ser territorio de la
  capa 3; y que `plan_de_clases` ya tiene repositorio propio. Eligió
  `asistencia`. Alternativa descartada: deducirlo, que habría sido justo la
  inferencia que el índice prohíbe.
- **Verificaciones heredadas: continuar aceptándolas pendientes.** Se preguntó
  explícitamente antes de escribir nada, ofreciendo también cerrar la evidencia
  de CI —hoy obtenible, porque hay un push reciente sobre `main`—, completar los
  tres pasos del guion de `ventas` que no constan, o calibrar el timeout de la
  capa 1. El usuario eligió continuar. **Ninguna se marca como cumplida** y
  todas conservan su riesgo.
- **No se mueve nada de `estudiantes_repository` ni de `dashboard_repository` en
  esta capa sin una orden explícita posterior a la evidencia de 7.0.** Motivo:
  el criterio que 5.2, 6.2 y las tres 7.1 aplicaron cinco veces es que la
  vecindad no manda y que una consulta vive donde está el código que la
  necesita. Alternativa descartada: dar por hecho que un `asistencia_repository`
  debe recibirlas, que ampliaría el diff a módulos que las capas 6 y 7 cerraron.
- **Las pruebas heredadas no se retiran ni se reescriben en 7.0.** Se miden y se
  completa el hueco. Motivo: se escribieron para proteger otra cosa y su
  severidad actual es un dato, no un estorbo.

## Riesgos

- **El dominio escribe y su escritura es un reemplazo parcial transaccional.**
  Es el efecto que 0.0 registró como preservable y que 1.4g se negó a tocar. Una
  extracción que cambie la propiedad de `commit` o `rollback` puede dejar
  asistencia a medias sin que falle nada visible. Mitigación: caracterizar antes
  de mover, comparador AST contra el commit base **y comprobación de
  `(SQL, parámetros)` y retorno**, como hizo 7.1 de `ventas`. Responsable de
  validarlo: el usuario, en la verificación manual.
- **Dos idiomas de conexión conviviendo.** Ningún dominio anterior de la capa 7
  llegó así. Unificarlos sería una mejora real y **cambiaría los conteos de
  conexiones**, que se fijan por aserción en 7.0. Queda como trabajo disponible,
  no como parte de la extracción.
- **Las pruebas heredadas pueden dar falsa confianza.** Existen desde la capa 1
  y protegen el ciclo de vida, no el contrato HTTP ni los conteos. Es un riesgo
  nuevo: los tres dominios anteriores no tenían nada y por eso nadie pudo
  confiarse. Mitigación: medir el hueco en 7.0 antes de escribir nada.
- **El supuesto de la frontera del dominio.** Es el que falló en `notas` y el
  que más daño hace, porque un inventario incompleto invalida todo lo que se
  construye encima. Mitigación: 7.0 busca por tabla y por símbolo, no por nombre
  de archivo. El supuesto 4 está marcado **como inferencia de patrón** justo
  para poder refutarlo sin arrastrar la conclusión.
- **Dos consumidores ajenos ya migrados.** `estudiantes_repository` y
  `dashboard_repository` leen esta tabla. Romper cualquiera de esos contratos
  **no haría fallar las pruebas de `asistencia`**: solo la compuerta global. Es
  lo que ocurrió en 7.1 de `notas` y por partida doble en 7.1 de `ventas`.
  Mitigación: **ejecutar siempre la compuerta completa**, nunca solo las pruebas
  del dominio. Y contar con que las guardias que enumeran el conjunto exacto de
  repositorios **volverán a fallar** si aparece el noveno.
- **El estado se compara por texto.** `ILIKE 'ausente'` es el criterio que
  `dashboard` usa y que el guion de la capa 6 menciona. Es el mismo tipo de
  patrón que produjo el hallazgo más grave de `ventas`. **7.0 lo mapea; no lo
  corrige.**
- **`asistencia` fue una de las ocho tablas averiadas de la capa 3** y tiene
  clave foránea a `asignaciones` con `ON DELETE CASCADE`. Un `DELETE`
  introducido por una extracción borraría en cascada o fallaría contra la clave.
  Mitigación: no ejecutar nada contra la base; caracterizar con dobles, como las
  cinco capas anteriores.
- **`response_model` filtra** en FastAPI los campos que no declara, así que
  añadirlo puede recortar un payload sin que falle nada. El índice solo lo
  autoriza tras caracterizar y conservar la respuesta existente.
- **Hueco de evidencia heredado**: el comparador AST de las capas 4 a 7 compara
  texto SQL pero **no parámetros**. Solo 7.1 de `ventas` lo cerró, y para su
  propia capa. Esta debe cerrarlo igual si extrae.
- Heredados y aceptados como pendientes: calibración de
  `DB_STATEMENT_TIMEOUT_MS` de la capa 1, ausencia de evidencia de GitHub
  Actions desde la capa 0, la credencial privilegiada de la capa 4 **sin
  rotar**, y los tres pasos del guion de `ventas` que **no constan**.

## Registro de ejecución

### 2026-08-20 — activación de la capa para `asistencia`

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local; el remoto se comprobó además contra el remoto real.
- Autorización: orden explícita del usuario en este turno, nombrando el dominio
  `asistencia` al elegirlo de la lista de los nueve en espera. **No se pegó el
  bloque preparado** de `PROMPT_CONTINUACION.md`; la autorización llegó en
  conversación, después de que el asistente se negara a activar sobre un
  «activar otro dominio de la capa» que no nombraba ninguno. La condición que
  ese bloque exige —nombrar el dominio explícitamente y no deducirlo— **se
  cumplió**.
- **Verificaciones heredadas**: se preguntó explícitamente al usuario, antes de
  escribir nada, si quería completarlas o continuar aceptándolas pendientes,
  ofreciendo cuatro salidas concretas. **Eligió continuar aceptándolas.** Quedan
  registradas con su riesgo y **ninguna se marca como cumplida**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía **dos veces**; `HEAD` real
  `a894441f8676b0486e3395f88179cdf6cba61430`, comprobado y no recordado.
- Continuidad: el base de la capa 7 para `ventas`,
  `58c5233afc4772ba040da690f4d719b518bb1b0a`, existe y es ancestro de `HEAD`,
  verificado con `git merge-base --is-ancestor`. Sus **cinco** commits
  posteriores forman una historia lineal y **todos quedan explicados**: la
  activación `040b027`, el cierre de 7.0 `2fbe83f`, la extracción de 7.1
  `76f76e7` y la documentación del guion `8948e40` están en `07_VENTAS.md`; el
  quinto, `a894441`, es su propio commit de cierre, que la bitácora no podía
  registrar sobre sí misma y que se verificó con `git show --stat`: toca
  **exactamente dos archivos de documentación y ningún código**. **No es una
  divergencia de producto.** Es el mismo matiz que la activación de `ventas`
  comprobó sobre el cierre de `notas`.
- **Estado remoto comprobado, no supuesto**: `origin/main` está en
  `a894441f8676b0486e3395f88179cdf6cba61430`, el mismo commit que `HEAD`,
  confirmado con `git rev-parse origin/main` y contra el remoto real con
  `git ls-remote origin main`. El reflog registra `update by push` de `a894441`
  el 2026-08-20 a las **16:21:16 -0500**, diez segundos después de crearse el
  commit. **No se consultó ni se atribuye ningún run de GitHub Actions**; esa
  evidencia sigue sin obtenerse desde la capa 0.
- **Desfase documental corregido en el índice, con autorización explícita del
  usuario**: `07_VENTAS.md` y el índice afirmaban que la capa 7 para `ventas`
  **no estaba publicada**, que `origin/main` seguía en `58c5233` y que su
  rollback era «una operación puramente local». **Ya no es cierto.** Producción
  corre el código de `ventas` desde el push del 2026-08-20, y revertir a
  `58c5233` exigiría otro push y otro despliegue. Se preguntó al usuario antes
  de tocar nada y autorizó corregir **el índice**; las líneas fechadas se
  conservan intactas, conforme al criterio que la capa 4 fijó, y lo que se añade
  es la línea que registra el cambio de estado. **`07_VENTAS.md` no se editó**:
  corregir una bitácora cerrada exige una orden propia. Es el mismo desfase que
  `notas` tuvo, y el segundo consecutivo.
- **Segundo residuo documental detectado y NO corregido**: el índice conserva,
  después de las líneas que cierran `ventas`, un párrafo que describe su punto
  de decisión como **abierto** y añade «Queda pendiente también la
  **verificación manual**». Las líneas de más arriba registran las dos cosas
  como resueltas el 2026-08-20. Es texto anterior al cierre, del mismo tipo que
  el que la capa 4 limpió con autorización explícita y que el residuo de
  `dashboard` que el índice ya arrastra anotado. **La autorización de este turno
  cubría el estado de publicación, no este párrafo**, así que queda anotado y
  sin tocar: exige una orden propia.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  `asistencia`** ni de ningún otro dominio, ni siquiera el listado de nombres de
  archivo. Los doce supuestos de la tabla de arriba salen **exclusivamente de la
  documentación del programa** —`00_LINEA_BASE_CALIDAD.md`,
  `01_FUNDACION_BASE_DATOS.md`, `03_MIGRACIONES_TENANTS.md`,
  `06_ASIGNACIONES_ESTUDIANTES.md`, `07_DASHBOARD.md` y el índice—, y cada uno
  lleva su origen anotado para que 7.0 pueda contrastarlo.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --abbrev-ref HEAD`,
  `git status --porcelain=v1`, `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git ls-remote origin main`, `git merge-base --is-ancestor`,
  `git log --oneline` desde el base de `ventas`, `git reflog show origin/main` y
  `git show --stat`; todos con resultado coherente con la activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  `asistencia`; **7.0 pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente **7.0** conforme al trabajo
  exacto de arriba y detenerse antes de 7.1. *(Ejecutada en el turno siguiente;
  ver el cierre de 7.0 más abajo.)*

### 2026-08-20 — cierre de 7.0

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`.
- Autorización: el usuario ordenó continuar. **Con capa activa esa orden sí
  autoriza**, porque el índice manda ejecutar la primera subcapa pendiente de la
  bitácora activa; lo que una instrucción genérica no autoriza es **activar** una
  capa cuando no hay ninguna, que era el caso de dos turnos antes.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `4e38e6caf8f3598694b89e799e77966efa93aad7`, el commit de activación que el
  usuario hizo entre turnos. El commit base `a894441` existe y es ancestro, y el
  único commit posterior es esa activación, explicada en esta bitácora.
- **Compuerta heredada reproducida antes de tocar nada**:
  `.\venv\Scripts\python.exe scripts\verify.py` → **835 pruebas, exit 0**, Ruff
  correcto, `pip check` íntegro. Coincide exactamente con lo registrado al
  cerrar la capa 7 para `ventas`, así que la línea base no tenía deriva.
- Archivos creados: `tests/test_asistencia_caracterizacion.py`, **34 pruebas**.
  Archivos modificados: esta bitácora y `docs/modularizacion/README.md`.
  **Código de producto: ninguno.** `git status` mostró un solo archivo sin
  rastrear y **ningún archivo rastreado modificado**.
- Compuerta tras la caracterización: **869 pruebas, exit 0**, Ruff correcto,
  `pip check` íntegro. La suite pasó de **835 a 869**.
- `git diff --check`: **limpio**.
- **La frontera se buscó por tabla y por símbolo, no por nombre de archivo**, y
  fue lo que destapó el tercer archivo: un `grep` de la tabla sobre `app/`
  devolvió diez archivos, de los cuales tres son el dominio y dos son los
  consumidores ya migrados.
- **El hallazgo principal no se veía midiendo el controlador.** Los conteos del
  controlador son buenos —1 conexión en los dos caminos—; el N+1 aparece solo al
  medir **el camino HTTP completo**, porque el coste vive en el bucle de
  permisos de la ruta. Es la confirmación más fuerte del criterio que las tres
  capas 7 anteriores fijaron: **medir consultas sin medir conexiones esconde el
  coste real**, y aquí además había que subir un nivel, hasta la ruta.
- **La inferencia de patrón se confirmó**, por primera vez en el programa. El
  supuesto 4 daba dos funciones al controlador y son dos. Se registra que
  **acertó por casualidad**: «sitio» en la capa 1 significaba apertura de
  conexión y no función, así que la deducción no era válida aunque el resultado
  lo fuera. Marcarla como inferencia siguió siendo lo correcto.
- **Evidencia que esta subcapa aporta al programa**: `asistencia` es el **tercer
  caso** de camino con varias conexiones en serie —tras los 4 de `dashboard` y
  los 4 o 5 de `notas`— y **el primero cuyo número crece con el tamaño de la
  entrada**. Es la evidencia real que le faltaba a
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2`, el pendiente que la capa 2
  dejó abierto el 2026-08-17. **Se registra sin actuar**: cambiar esa constante
  exige una auditoría de capacidad propia.
- Hallazgos: **ocho**, todos **registrados y sin corregir**.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno por
  parte del asistente**.
- Estado al cerrar el turno: capa 7 **activa** para `asistencia`; **7.0
  cerrada**; **7.1 pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente **7.1** conforme a su trabajo
  exacto y detenerse antes de cualquier otra subcapa. **No se inició en este
  turno.**

## Entrega al próximo chat

- Capa activa: **la capa 7 para el dominio `asistencia`**, activada el
  2026-08-20. **Es el único dominio activo**; los otros ocho siguen en espera.
- Última subcapa terminada: **7.0**, cerrada el 2026-08-20.
- Primera subcapa pendiente: **7.1**, no iniciada. Su trabajo exacto está
  arriba, en doce pasos, y el punto donde detenerse es antes de cualquier otra
  subcapa.
- Compuerta al cerrar 7.0: **869 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro. La suite pasó de **835 al activar la capa a 869**.
- Lo que 7.0 dejó medido: el dominio son **tres archivos** —el supuesto decía
  dos—; **2 entradas HTTP** con **dos modelos de permiso**; **una sola tabla
  escrita**, `asistencia`; **una transacción propia**; **3 sentencias SQL
  inline**, todas en el controlador y 0 en la ruta y el esquema; **34 pruebas de
  caracterización** nuevas sobre las **12 heredadas** de la capa 1. Es **el
  dominio más pequeño que ha migrado el programa**.
- **Los doce supuestos quedaron resueltos**: **diez confirmados y dos
  incompletos**, y **ninguno falso** —la primera vez que no cae ninguno—. Los
  dos incompletos: el dominio son tres archivos y no dos, y las pruebas
  heredadas son doce y no cinco.
- **El hallazgo que manda es el N+1 en CONEXIONES** del bucle de permisos de la
  ruta: guardar la asistencia de un curso de 30 abre **31 conexiones** siendo
  admin y **61** siendo profesor, contra un pool de 10 y 5 workers. **No se ve
  midiendo el controlador**, que abre una sola en los dos caminos. Vive en
  `app/core/permissions.py`, **fuera de alcance**, y **7.1 no lo toca**.
- Commit base: `a894441f8676b0486e3395f88179cdf6cba61430`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1), evidencia de GitHub Actions posterior a la
  capa 0, y los **tres pasos del guion de `ventas`** que no constan. La
  credencial privilegiada de la capa 4 sigue **sin rotar**.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `dashboard`, `notas` y `ventas` están cerrados en sus
     propias bitácoras y los otros ocho siguen en espera.
  2. **El dominio escribe una sola tabla en una sola transacción**, con un
     reemplazo parcial: `DELETE` acotado más N `INSERT`. El `rollback` es del
     controlador y 7.1 no puede moverlo.
  3. **Los dos idiomas de conexión se conservan.** Unificarlos bajaría el coste
     pero **cambiaría los conteos fijados por aserción**: trabajo disponible, no
     parte de la extracción.
  4. **El N+1 en conexiones no se toca.** Vive en `app/core/permissions.py`,
     infraestructura compartida. Es el hallazgo más grave y **7.1 no lo corrige**.
  5. **Dos consumidores ajenos ya migrados** leen esta tabla:
     `estudiantes_repository` y `dashboard_repository`. Romper su contrato **no
     haría fallar las pruebas de `asistencia`**, solo la compuerta global.
     Ejecutarla siempre completa: **dos guardias de repositorios volverán a
     fallar** al aparecer el noveno.
  6. **Una prueba de hallazgo anclada a un archivo es también una guardia de
     línea base.** Lección de 7.1 de `ventas`: hay tres candidatas en el archivo
     nuevo, listadas en el paso 9 del trabajo exacto de 7.1.
  7. **No corregir ninguno de los ocho hallazgos**, ni los treinta y tres que
     dashboard, notas y ventas dejaron abiertos.
  8. **El `ILIKE 'ausente'` está mapeado y vive fuera del dominio.** No se
     arregla.
- **Residuos documentales abiertos**: `07_VENTAS.md` describe su capa como no
  publicada y su rollback como puramente local, y **ya no es cierto**; el índice
  lo registra corregido, la bitácora cerrada no se editó. Y el índice conserva
  un párrafo que declara abierto el punto de decisión de `ventas` y pendiente su
  verificación manual, cuando las dos cosas se resolvieron. Corregir cualquiera
  de los dos exige una orden explícita.
- **Pendiente la publicación de esta capa.** Los commits se quedan en local
  hasta que el usuario decida; publicar dispara el despliegue.
- Siguiente acción exacta: ejecutar únicamente **7.1** y detenerse antes de
  cualquier otra subcapa.
