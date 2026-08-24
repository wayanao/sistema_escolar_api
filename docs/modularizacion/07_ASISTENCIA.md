# Capa 7: asistencia

Última revisión: 2026-08-24.

## Control

- Estado: **Cerrada** el 2026-08-21, con sus dos subcapas **7.0 y 7.1**
  completas —ambas del 2026-08-20— y la **verificación manual ejecutada por el
  usuario con resultado correcto**. Activada el 2026-08-20.
- Corrección puntual posterior al cierre: el 2026-08-24 el usuario autorizó
  eliminar el N+1 de conexiones de los permisos de escritura. Quedó implementada
  y verificada localmente **sin reabrir la capa ni activar otra**. Staging,
  verificación manual, commit, push y evidencia de CI siguen pendientes.
- Commit base: `a894441f8676b0486e3395f88179cdf6cba61430`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **ninguna definida**. Con 7.1 la **frontera de
  persistencia del dominio quedó cerrada**. **El usuario decidió cerrar la capa
  aquí**, sin abrir 7.2. Ver «Punto de decisión, resuelto el 2026-08-21».
- Código de producto modificado al activar: **ninguno**. Tampoco en 7.0: su diff
  es **un solo archivo de prueba nuevo** y ningún archivo rastreado modificado,
  igual que los de 5.0, 6.0 y las tres 7.0 anteriores. **7.1 sí modifica
  producto**: el controlador y un repositorio nuevo.
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
| 7.1 | Extraer las 3 sentencias a `asistencia_repository` sin cambiar SQL, conteos ni ciclo de vida | **Cerrada** el 2026-08-20 |
| 7.2 | Punto de decisión: `response_model`, errores de dominio y el N+1 en conexiones | **Sin decidir**: es un punto de decisión, no una subcapa pendiente |

El desglose se dejó deliberadamente sin decidir hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las tres capas 7 anteriores. Con esa
evidencia, **7.1 queda definida** y el resto sigue abierto. Las subcapas
innecesarias se marcarán `No aplica` con explicación. **Nunca se ejecutan dos
subcapas en el mismo turno.**

## Hallazgos de 7.0 y estado posterior

7.0 registró **ocho** sin corregir ninguno. La corrección puntual autorizada el
2026-08-24 resolvió los dos primeros; **seis siguen abiertos**. El texto de cada
hallazgo conserva la línea base histórica y añade su estado vigente.

1. **N+1 en CONEXIONES —corregido localmente el 2026-08-24.** En la línea base
   `require_estudiante_in_asignacion` **abre su propia conexión** y la ruta la
   llama **una vez por estudiante del lote**. Siendo admin, guardar la
   asistencia de un curso de 30 abre **31 conexiones en serie**; siendo
   profesor, **61**, porque `require_asignacion_access` también abre la suya.
   El pool tiene **10 conexiones** y el limitador de la capa 2 deriva **5
   workers**. `dashboard` encontró 4 conexiones y `notas` 4 o 5; **este es el
   primero cuyo número crece con el tamaño de la entrada.** Las dos funciones
   viven en `app/core/permissions.py`, **infraestructura compartida y fuera de
   alcance**, igual que `require_estudiante_access` lo estuvo para `notas`.
   Verificado por aserción con lotes de cinco. **Estado vigente:** la ruta usa
   una guardia batch nueva y mantiene **2 conexiones totales como admin y 3 como
   profesor** para lotes de 1, 5 y 30. La guardia singular permanece intacta
   para `boletines` y `observaciones`.
2. **El permiso de asignación se comprobaba N veces con el mismo argumento
   —corregido localmente el 2026-08-24.** La
   ruta **ya validó** que los N registros comparten `asignacion_id`, y aun así
   llama a `require_asignacion_access` una vez por estudiante con el mismo
   valor. Es desperdicio puro. La prueba heredada
   `test_guardar_asistencia_valida_permisos_y_envia_lote` **ya lo fijaba por
   aserción** —esperaba `[(10, 3), (10, 3)]`— sin señalarlo como defecto. La
   expectativa autorizada ahora es una sola comprobación por lote.
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

## Resultado de 7.1

**Las 3 sentencias salieron del controlador a
`app/repositories/asistencia_repository.py`, 3 funciones que reciben el cursor
existente y el noveno repositorio del proyecto.**

| Métrica | Antes | Después |
|---|---:|---:|
| `asistencia_controller.py`, líneas | **84** | **69** |
| `asistencia_controller.py`, sentencias SQL inline | **3** | **0** |
| `app/routes/asistencia.py`, sentencias SQL inline | 0 | 0 |
| `app/schemas/asistencia.py`, sentencias SQL inline | 0 | 0 |
| Repositorios del proyecto | 8 | **9** |

**Comparador AST contra el commit base `a894441`: 3 literales SQL distintos
antes y después, conjunto idéntico, con 3 de 3 byte a byte**, y 3 puntos de
llamada antes y después. **No hizo falta autorizar ningún cambio de texto SQL**,
como en la capa 6 y en las tres capas 7 anteriores, y a diferencia de la 5, que
necesitó dos.

Conservar los literales byte a byte exigió reproducir la sangría interior de
cada uno en su nueva ubicación, aunque quede visualmente rara, y **dejar vacías
las dos líneas en blanco interiores del `SELECT`**. Es exactamente la trampa que
1.4g ya había registrado sobre este mismo literal: `git diff --check` rechaza
líneas nuevas con espacios finales y la compuerta lo ejecuta. La comprobación
pasó limpia.

**El controlador conserva la propiedad del ciclo de vida, y en los dos
idiomas**: la escritura sigue abriendo con `get_connection()` y cerrando en
`finally`, con su `commit` y su `rollback`; la lectura sigue usando
`with get_cursor() as cursor`. El repositorio **no abre, no cierra, no confirma
y no revierte** nada, fijado por prueba sobre el AST: sus únicas llamadas son
`execute` y `fetchall`, y **no importa nada**.

### Equivalencia en tiempo de ejecución, incluida la de parámetros

Se ejecutó el controlador del commit base y el actual con las mismas entradas,
comparando la secuencia exacta de `(SQL, parámetros)`, el valor devuelto, el
número de conexiones y los eventos del ciclo de vida. Con tres sentencias y dos
caminos la comprobación es barata, así que no había razón para omitirla.

| Camino | Consultas | `(SQL, parámetros)` | Retorno | Conexiones | Ciclo de vida |
|---|---:|---|---|---|---|
| `guardar_asistencia_controller`, tres estudiantes | 5 | idénticos | idéntico | 1 | `commit`, `close` |
| `obtener_historial_asistencia` | 2 | idénticos | idéntico | 1 | `close` |

**Los dos idénticos**, incluido el caso de una fila con `fecha` nula, que sigue
apareciendo con historial vacío. Es la evidencia que el comparador AST no da,
porque compara texto SQL y **no parámetros**.

### Las guardias que fallaron, que era la señal esperada

**Fallaron cinco pruebas al extraer**, y las cinco eran previsibles. Es la
lección 14 de la capa 6, aplicada por quinta vez.

| Prueba | Por qué falló |
|---|---|
| `test_el_dominio_todavia_no_tiene_repositorio_propio` | Guardia de línea base declarada. Apareció el noveno repositorio |
| `test_las_tres_sentencias_viven_hoy_en_el_controlador` | Guardia de línea base declarada. El controlador bajó a 0 |
| `test_dashboard_caracterizacion.py::test_el_dominio_tiene_su_repositorio` | **Fuera del dominio.** Enumera el conjunto exacto de repositorios |
| `test_notas_caracterizacion.py::test_el_repositorio_de_notas_es_el_septimo` | **Fuera del dominio.** Mismo motivo |
| `test_ventas_caracterizacion.py::test_el_repositorio_de_ventas_es_el_octavo` | **Fuera del dominio.** Mismo motivo |

**Dentro del dominio la previsión acertó**: fallaron **solo las dos guardias
declaradas**, y ninguna prueba de hallazgo. El paso 9 del trabajo exacto —revisar
antes las pruebas de hallazgo ancladas a un archivo— **funcionó**: las tres
candidatas que señalaba sobrevivieron, porque comprueban el texto de la ruta y
del controlador, no el SQL. Es la lección de 7.1 de `ventas` aplicada **antes**
de extraer en vez de descubierta después.

**Corrección de lo que esta bitácora había previsto**: anunciaba **dos**
enumeraciones ajenas y fueron **tres**. `ventas` añadió la suya en su propia 7.1
y esta bitácora no la contó. El patrón ya es visible y conviene dejarlo escrito:
**cada dominio migrado añade una guardia de enumeración, así que el número crece
en uno con cada migración**. En 7.1 de `notas` falló una, en la de `ventas` dos,
en esta tres, y la próxima tendrá cuatro.

**Las otras 44 pruebas del dominio pasaron sin cambiar de expectativa**: las 32
restantes del archivo de 7.0 —incluidos los seis conteos de consultas y
conexiones y las cinco de contrato HTTP real— y **las 12 heredadas de la capa 1,
que no se tocaron**. Esa es la evidencia de que nada observable cambió, y aquí
vale más que en los dominios anteriores porque esas doce se escribieron **antes**
de que existiera esta capa.

**Consecuencia fuera del dominio, por tercera vez en el programa**: las tres
guardias que enumeran el conjunto exacto de repositorios fallaron al aparecer el
noveno. **No era una rotura de contrato**; se actualizaron conservando su
severidad, que es deliberada y obliga a reconocer cada migración nueva. Lo
detectó **la compuerta global, no las pruebas de `asistencia`**, que es
exactamente el riesgo que 7.0 había registrado.

### Decisión de 7.1 sobre dónde viven las tres sentencias

**Las tres viven en `asistencia_repository`**, y esta vez la decisión fue fácil,
a diferencia del `UPDATE pagos` de `ventas`. Ninguna de las tres escribe una
tabla ajena.

El único matiz que la merecía: **el `SELECT` del historial arranca `FROM
estudiantes e` y hace `JOIN asistencia`**, así que su tabla conductora pertenece
a un dominio ya migrado. Aun así vive aquí, por el criterio que 6.2 fijó con el
expediente y que las tres 7.1 anteriores repitieron: **es el historial de
asistencia de una asignación, no persistencia general de estudiantes**, y lo
necesita este controlador y solo este. Llevarlo a `estudiantes_repository`
ampliaría el diff a un módulo que la capa 6 cerró y crearía una dependencia
entre dominios que 7.1 no está autorizada a introducir.

**Las dos lecturas ajenas no se movieron**, como el trabajo exacto exigía:
`contar_inasistencias` sigue en `estudiantes_repository` y las inasistencias por
profesor en `dashboard_repository`. El módulo nuevo lleva una advertencia en su
propio docstring sobre el `ILIKE 'ausente'` que ambas usan y que este dominio no
usa, para que nadie lo «unifique» por vecindad. Es el criterio que 7.1 de
dashboard fijó y que las de notas y ventas repitieron.

### Lo que 7.1 no tocó, y estaba prohibido tocar

- **Los dos idiomas de conexión se conservan.** Unificarlos bajaría
  `POST /asistencia` de dos aperturas a una en el controlador, pero cambiaría
  los conteos fijados por aserción. Trabajo disponible.
- **El N+1 en conexiones sigue intacto.** Vive en `app/core/permissions.py`,
  infraestructura compartida. Sigue siendo el hallazgo más grave de la capa.
- **Ninguno de los ocho hallazgos se corrigió.**
- **Ninguna prueba heredada se retiró ni se reescribió.**

## Subcapa 7.1 — trabajo exacto, ejecutado y cerrado

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
  turno.** *(Ejecutada en el turno siguiente; ver el cierre de 7.1 más abajo.)*

### 2026-08-20 — cierre de 7.1

- Modo de acceso: mismo checkout local; Git validado directamente.
- Autorización: el usuario ordenó continuar. Con capa activa y 7.1 como primera
  subcapa pendiente, esa orden autoriza ejecutarla.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `68ff9a4642c85ddf1af7f981ccc1af1a13df4806`, el commit de 7.0 que el usuario
  hizo entre turnos. El commit base `a894441` existe y es ancestro, y los **dos**
  commits posteriores están explicados aquí: la activación `4e38e6c` y el cierre
  de 7.0 `68ff9a4`.
- Archivos modificados: `app/controllers/asistencia_controller.py`,
  `tests/test_asistencia_caracterizacion.py`,
  `tests/test_dashboard_caracterizacion.py`,
  `tests/test_notas_caracterizacion.py` y
  `tests/test_ventas_caracterizacion.py`. Creado:
  `app/repositories/asistencia_repository.py`. Más esta bitácora y
  `docs/modularizacion/README.md`. **Siete archivos**, ninguno fuera del alcance
  de la subcapa; los tres de dashboard, notas y ventas son **una línea cada uno**
  y **no son código de producto**.
- **Comparador AST contra el commit base**: 3 literales SQL distintos antes y
  después, **conjunto idéntico**, **3 de 3 byte a byte**, y 3 puntos de llamada
  antes y después. Ningún cambio de texto SQL autorizado ni necesario.
- **Equivalencia en tiempo de ejecución**: los **dos** caminos emiten la misma
  secuencia de `(SQL, parámetros)`, devuelven lo mismo, abren el mismo número de
  conexiones y producen los mismos eventos de ciclo de vida que el commit base.
- Compuerta global: `.\venv\Scripts\python.exe scripts\verify.py` → **872
  pruebas, exit 0**, Ruff correcto, `pip check` íntegro. La suite pasó de 869 a
  872: se retiraron las dos guardias de línea base y se añadieron cinco pruebas
  positivas.
- `git diff --check`: **limpio**, incluidas las dos líneas en blanco interiores
  del `SELECT`, que se conservaron **vacías**. Era la trampa que 1.4g ya había
  registrado sobre ese mismo literal.
- **Cinco pruebas fallaron al extraer y las cinco eran previsibles**: las dos
  guardias de línea base declaradas y las **tres** enumeraciones de repositorios
  de dashboard, notas y ventas. **Ninguna otra cambió de expectativa**, y en
  particular **ninguna de las doce heredadas de la capa 1**.
- **Una aserción propia se escribió mal y se corrigió**, ninguna de producto:
  `test_el_repositorio_no_es_dueno_de_ningun_recurso` buscaba `get_connection`
  en el **texto** del módulo, y el docstring del repositorio lo menciona en
  prosa al explicar que la propiedad se queda en el controlador. Se pasó a
  comprobarlo sobre el **AST**. Es la lección 13 de la capa 6 otra vez: la prosa
  que describe algo no puede contarse como si fuera ese algo.
- Hallazgos: **ninguno nuevo**. Los ocho de 7.0 siguen vivos y **ninguno se
  corrigió**.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno por
  parte del asistente**.
- Estado al cerrar el turno: capa 7 **activa** para `asistencia`; **7.0 y 7.1
  cerradas**; **punto de decisión abierto** con tres salidas y **verificación
  manual pendiente**.
- Siguiente acción exacta: **esperar la decisión del usuario**. Ninguna de las
  tres salidas se inicia por inferencia, y la verificación manual no la puede
  hacer un asistente. *(Ambas llegaron el 2026-08-21; ver el cierre más abajo.)*

### 2026-08-21 — verificación manual y cierre de la capa

- Modo de acceso: mismo checkout local; Git validado directamente.
- **Artefacto confirmado antes de registrar la verificación**, conforme a la
  lección 10 de la capa 5 y **sin ambigüedad**: rama `main`, árbol **limpio**,
  `HEAD` `4a4d9e1edcee96f04674026df1bc13161279aefb`. Los **tres** commits
  posteriores al base están explicados en esta bitácora: la activación
  `4e38e6c`, el cierre de 7.0 `68ff9a4` y la extracción de 7.1 `4a4d9e1`.
  `origin/main` seguía en el base `a894441`, comprobado con `git rev-parse` y
  contra el remoto real con `git ls-remote`.
- **Verificación manual**: el usuario informó haberla ejecutado en local con
  resultado correcto. **Lo reportó de forma global**, y al preguntársele **punto
  por punto** por los cuatro pasos de más peso confirmó **uno**: el **paso 3**,
  el reemplazo parcial. Los pasos **4, 7 y 8 no constan** y **no se marcan como
  cumplidos**. Se registra así, sin inflarlo. Es evidencia **más fuerte que la
  de `ventas`** —donde ningún paso llegó a constar— y **más débil que la de
  `notas`**, y consta precisamente el paso que más valor tenía aquí.
- **Decisión del usuario, explícita**: cerrar la capa aquí, sin abrir 7.2. Se le
  ofrecieron **cuatro** salidas —cerrar, una 7.2 con el N+1 en conexiones, una
  con `response_model` o una con los errores de dominio— y eligió cerrar. La
  capa queda siendo una refactorización pura, como la 5, la 6 y las tres capas 7
  anteriores.
- **Compuerta global de cierre**: `.\venv\Scripts\python.exe scripts\verify.py`;
  **872 pruebas pasaron**, 5 warnings heredadas, Ruff correcto, `pip check`
  íntegro y exit 0. La suite pasó de 835 al activar la capa a 872.
- `git diff --check`: **limpio**.
- **Lo que el cierre NO marca como cumplido**: los tres pasos del guion que no
  constan, el N+1 en conexiones, los ocho hallazgos de 7.0 y las verificaciones
  heredadas de las capas 0 y 1. Ninguno cambia de estado por cerrar la capa.
- Archivos modificados en este turno: esta bitácora y
  `docs/modularizacion/README.md`. **Código de producto y pruebas: ninguno.**
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno por
  parte del asistente**, ni en este turno ni en toda la capa.
- Estado: **capa 7 cerrada para el dominio `asistencia`**. Los **ocho** dominios
  restantes de la capa 7 quedan **en espera** y **ninguno fue activado**.
- Siguiente acción exacta: esperar una orden explícita del usuario. Una
  instrucción genérica de continuar no autoriza activar otro dominio. Queda
  además **pendiente la publicación**, que decide y ejecuta el usuario.

## Staging, rollback y verificación manual

### Lo que esta capa hizo y no hizo

La capa 7 para `asistencia` es **exclusivamente una refactorización**, igual que
la 5, la 6 y las tres capas 7 anteriores. No añadió funciones, no cambió reglas,
no tocó rutas, payloads, status codes, permisos, tenant, ownership,
transacciones, timeouts, dependencias ni configuración. Y **no abrió una sola
conexión a PostgreSQL**: ni migraciones, ni DDL, ni DML, ni lecturas de
medición. Toda la caracterización se hizo con dobles.

Es la **sexta capa consecutiva** que no abre una conexión a PostgreSQL, y la
**tercera de esas seis cuyo dominio escribe**.

### Rollback

**Es puramente de código.** No hay nada que deshacer en datos ni en esquema.
Revertir los commits de la capa hasta
`a894441f8676b0486e3395f88179cdf6cba61430` devuelve el controlador a su versión
anterior y elimina el repositorio nuevo.

**Mientras la capa siga sin publicar, el rollback es una operación puramente
local.** Esa ventaja desaparece en cuanto se publique, porque un push a `main`
dispara el despliegue. Es la misma advertencia que registraron `notas` y
`ventas`, y en los dos casos dejó de aplicar al poco tiempo.

No cambiar los timeouts durante el rollback.

### Staging

No se usó un entorno de staging y **no se considera necesario** para esta capa,
por la misma razón que hace trivial el rollback: no hay cambio de esquema, de
datos ni de SQL. Un despliegue prudente solo necesita comprobar que la
aplicación arranca y lo que cubre el guion.

### Verificación manual: **hecha, con la cobertura que el usuario reportó**

**Ejecutada por el usuario el 2026-08-21, en local, con resultado correcto.**

**Artefacto confirmado antes de registrarla**, conforme a la lección 10 de la
capa 5, y **sin ambigüedad**: rama `main`, árbol **limpio**, `HEAD`
`4a4d9e1edcee96f04674026df1bc13161279aefb`, el commit de 7.1. `origin/main`
seguía en el commit base `a894441`, comprobado contra el remoto real, así que
**lo ejercitado en local y lo commiteado son el mismo contenido**.

**Alcance real de la evidencia, registrado sin inflarlo.** El usuario informó el
resultado **de forma global** —«ya verifiqué manualmente en local»— y después,
preguntado **punto por punto** sobre los cuatro pasos de más peso, confirmó
**uno**:

| Paso | ¿Consta? |
|---|---|
| **3. Reemplazo parcial**: repasar lista el mismo día y periodo cambiando solo a algunos estudiantes, comprobando que los demás conservan su valor y no se duplican filas | **SÍ** |
| 4. Lote que no incluye a todo el curso: la asistencia de los compañeros no se borra | **No consta** |
| 7. Prueba cruzada: que las ausencias cuadren en el expediente del estudiante y en el panel de inasistencias del dashboard | **No consta** |
| 8. Aislamiento entre los dos tenants | **No consta** |

Los pasos 1, 2, 5 y 6 —arranque, ida y vuelta, las tres validaciones y
permisos— quedan cubiertos **solo por el reporte global**, no por confirmación
explícita.

**Esta evidencia es más fuerte que la de `ventas` y más débil que la de
`notas`.** `ventas` se reportó de forma enteramente global y ningún paso llegó a
constar; `notas` se respondió sobre un guion explícito y por eso su bitácora
pudo afirmar que no se infirió nada. Aquí consta **el paso que más valor tenía
en este dominio**: el reemplazo parcial es exactamente lo que una extracción mal
hecha habría roto, porque es la única escritura y la única transacción, y su
fallo no daría una cifra rara sino **asistencia perdida o duplicada**.

**Qué respalda entonces la capa**, y es bastante:

- la evidencia automática: **3 de 3 literales SQL byte a byte** y **los dos
  caminos emitiendo la misma secuencia de `(SQL, parámetros)`, devolviendo lo
  mismo y abriendo las mismas conexiones** que el commit base;
- **872 pruebas en verde**, con los seis conteos de consultas y conexiones y los
  cinco contratos HTTP reales fijados por aserción, y ninguna que cambiara de
  expectativa;
- **las doce pruebas heredadas de la capa 1, que no se tocaron y siguen
  pasando**. Se escribieron antes de que esta capa existiera, así que son
  evidencia independiente de ella;
- el paso 3 del guion, confirmado por el usuario;
- el uso real que el usuario le dio a la aplicación, sin encontrar nada raro.

**Qué no respalda.** Que la aplicación «se vea bien» **no equivale** a haber
comprobado que un lote parcial no borra a los compañeros, que las ausencias
cuadran con los dos consumidores ajenos, ni que los dos colegios siguen
aislados. **El paso 7 es el que más pesa de los tres que faltan**, porque los dos
consumidores ajenos son precisamente los contratos que **las pruebas de
`asistencia` no harían fallar** si se rompieran. Lo mitiga que la compuerta
global sí los cubre y pasó en verde, pero **no consta la comprobación contra
datos reales**.

Es aceptable por lo que la capa es —una refactorización con SQL y parámetros
demostrados equivalentes y sin ningún acceso a la base de datos—; no lo sería en
una capa que cambiara comportamiento o tocara datos. **El guion completo se
conserva arriba** por si se quieren cerrar esos tres huecos.

## Punto de decisión, resuelto el 2026-08-21

**La frontera de persistencia de `asistencia` ya está cerrada**: ni el
controlador, ni la ruta, ni el esquema tienen SQL, y el repositorio existe. Lo
que queda del objetivo que el índice fijó para la capa 7 es la parte
condicional, más una decisión propia de este dominio.

Son tres cosas, y **ninguna entra por inferencia**:

1. **El N+1 en conexiones.** Es el hallazgo 1 y el más grave de la capa.
   Corregirlo significa que `require_estudiante_in_asignacion` reciba un cursor
   o compruebe el lote entero en una consulta, y **toca
   `app/core/permissions.py`, infraestructura compartida que alcanza a otros
   dominios**. Exigiría orden explícita y probablemente la auditoría de
   capacidad que la capa 2 dejó pendiente. Es, con diferencia, la salida con más
   valor operativo.
2. **`response_model`.** Las dos entradas podrían declararlo demostrando payload
   por payload que la respuesta no cambia. Riesgo propio: `response_model`
   **filtra** los campos que no declara, y la respuesta del historial es una
   lista de diccionarios anidados construida a mano.
3. **Errores de dominio.** Aquí el dilema es **menor que en `notas`** y parecido
   al de `ventas`: la ruta ya traduce sus tres validaciones a `HTTPException`
   con 422, así que el trabajo no sería cambiar status codes sino **mover las
   reglas del lote fuera de la capa HTTP**, que es el hallazgo 3. Eso **sí**
   cambiaría el comportamiento de quien llame al controlador directamente, así
   que no es una refactorización pura.

**El usuario eligió cerrar la capa aquí**, el 2026-08-21 y de forma explícita,
entre cuatro salidas planteadas —cerrar, una 7.2 con el N+1 en conexiones, una
7.2 con `response_model`, o una 7.2 con los errores de dominio—. Consecuencias
registradas, ninguna de ellas una deuda oculta:

- La capa 7 para `asistencia` es, como la 5, la 6 y las tres capas 7 anteriores,
  **exclusivamente una refactorización**. Ningún contrato observable cambió.
- **El N+1 en conexiones se queda.** Es la salida con más valor operativo y
  **no se descarta para siempre**: pasa a ser trabajo disponible que exigiría una
  orden propia, y probablemente la auditoría de capacidad que la capa 2 dejó
  pendiente. Sigue activo: pasar lista a un curso de 30 abre **31 conexiones**
  siendo admin y **61** siendo profesor, contra un pool de 10.
- **`response_model` y los errores de dominio no se añaden.** No quedan como
  trabajo pendiente de esta capa: quedan registrados como trabajo disponible.
- Los **ocho hallazgos de 7.0 siguen vivos y sin corregir**. Cerrar la capa **no
  los resuelve ni los cancela**, y **tampoco los introdujo**: los ocho son
  anteriores a este trabajo.
- **Los tres pasos del guion que no constan siguen sin constar.** No se marcan
  como cumplidos.

## Cierre de la capa 7 para `asistencia`

### Resultado frente a su objetivo

| Objetivo | Resultado |
|---|---|
| Migrar el dominio con contratos y pruebas | `asistencia_controller.py` pasó de **84 a 69 líneas** y de **3 sentencias SQL inline a 0**; la persistencia vive en `asistencia_repository`, **3 funciones** que reciben el cursor. **37 pruebas de caracterización** nuevas fijan payloads, permisos, conteos de consultas **y de conexiones**, ciclo de vida en los dos idiomas y **status codes HTTP reales**, sobre las **12 heredadas** que no se tocaron |
| Un dominio a la vez | **Cumplido**: no se tocó código de producto de ningún otro dominio. Los ocho restantes siguen en espera |
| `response_model` solo tras caracterizar | **No se añadió**, por decisión explícita del usuario. No queda como deuda |
| Sin abstracciones sin dos consumidores | **Cumplido**: el repositorio por módulo es la convención documentada, con ocho precedentes |

La suite pasó de **835 a 872** pruebas. Compuerta de cierre: **exit 0 con 872
pruebas**, Ruff correcto y `pip check` íntegro.

### Lo que esta capa NO hizo

- **No tocó la base de datos**, ni siquiera para leer. Es la **sexta capa
  consecutiva** que no abre una sola conexión a PostgreSQL.
- **No tocó archivos.** 7.0 lo comprobó: ninguno de los tres archivos del
  dominio menciona `storage`.
- No cambió rutas, payloads, status codes, permisos, tenant, ownership,
  transacciones, timeouts, dependencias ni configuración.
- **No corrigió ninguno de los ocho hallazgos.** Siguen vivos, empezando por el
  N+1 en conexiones.
- **No unificó los dos idiomas de conexión** ni retiró ninguna prueba heredada.
- **No necesitó autorizar ni un solo cambio de texto SQL**, como la capa 6 y las
  tres capas 7 anteriores.

### Lo que esta capa aporta al programa, más allá de su dominio

- **La evidencia que le faltaba a la constante de capacidad de la capa 2.**
  `asistencia` es el tercer caso de camino con varias conexiones en serie, y
  **el primero cuyo número crece con el tamaño de la entrada**. Se registra sin
  actuar.
- **Un patrón de mantenimiento que ya es regla**: cada dominio migrado añade una
  guardia que enumera el conjunto exacto de repositorios, así que el número de
  guardias ajenas que fallan en cada 7.1 **crece en uno con cada migración**.
  Una en notas, dos en ventas, tres en esta, cuatro en la próxima.
- **La confirmación de que revisar antes las pruebas de hallazgo funciona.** La
  lección que 7.1 de `ventas` aprendió a posteriori se aplicó aquí por
  adelantado, y la previsión dentro del dominio acertó exactamente.
- **El primer caso en que un dominio llega con pruebas de otra capa**, y el
  método para no confiarse: medir el hueco punto por punto antes de escribir
  nada, sin retirar ni reescribir lo heredado.

### Estado de publicación

**No publicada.** `origin/main` sigue en `a894441`, el commit base de la capa, y
hay **tres commits locales por delante** —`4e38e6c`, `68ff9a4` y `4a4d9e1`—, más
el del cierre. **Producción no corre este código**: sigue con el anterior a la
capa.

Mientras siga así, **el rollback es una operación puramente local**. En cuanto se
publique, y como un push a `main` dispara el despliegue, esa ventaja desaparece
y revertir exigirá otro push. La publicación la decide y la ejecuta el usuario.

**No se atribuye ningún run de GitHub Actions**: esa evidencia sigue sin
obtenerse desde la capa 0.

### Riesgos que la capa dejó abiertos y estado posterior

- ~~**El N+1 en conexiones.**~~ **Corregido localmente el 2026-08-24**: para un
  lote de 30 el camino abre 2 conexiones totales como admin y 3 como profesor.
  La verificación manual, commit, push y evidencia de CI de esta corrección aún
  no constan, por lo que no se atribuye a producción.
- **Las reglas del lote viven en la capa de rutas**, así que llamar al
  controlador fuera de la ruta admite un lote heterogéneo y borra por un
  contexto e inserta por otro.
- **El controlador no valida `estado`.**
- **Un fallo de infraestructura en la lectura sale como 500**, no como 4xx.
- **El `ILIKE 'ausente'` vive fuera del dominio**, en los dos consumidores ya
  migrados, y no se apoya en la restricción que el dominio sí impone.
- **Tres pasos del guion de verificación manual no constan**: lote parcial,
  prueba cruzada contra el expediente y el dashboard, y aislamiento entre
  tenants.
- El resto de los ocho hallazgos de 7.0, más `response_model` sin añadir.
- Heredados: calibración de `DB_STATEMENT_TIMEOUT_MS` de la capa 1, ausencia de
  evidencia de GitHub Actions desde la capa 0, la credencial privilegiada de la
  capa 4 sin rotar, y los hallazgos abiertos de las capas 5, 6 y 7 —incluidas la
  clave de idempotencia, la ausencia de lock frente a horarios solapados, los
  diez de dashboard, los doce de notas y los once de ventas—.

## Guion de verificación manual propuesto

Lo que la evidencia automática ya cubre, y que por tanto el guion **no** tiene
que buscar: que el SQL es el mismo —3 de 3 byte a byte—, que los parámetros y
los valores devueltos son los mismos en los dos caminos, y que los conteos de
consultas y conexiones no cambiaron. Lo que **solo** puede ver una persona es lo
que ocurre contra PostgreSQL real, con las claves foráneas de la capa 3 puestas
y con los dos tenants.

**Antes de empezar, confirmar el artefacto**: qué commit o árbol se está
ejercitando. Si el árbol tiene cambios sin commitear, lo verificado es el árbol,
no `HEAD`. Es la lección 10 de la capa 5.

Guion, en ocho pasos:

1. **Arranque.** La aplicación levanta sin error de importación. El repositorio
   nuevo es un módulo más y un error de import sería inmediato.
2. **Pasar lista, ida y vuelta.** Guardar la asistencia de un curso completo con
   una mezcla de `presente` y `ausente`. Comprobar que responde
   `{"mensaje": "Asistencia guardada"}` y que el historial de esa asignación y
   periodo muestra exactamente lo guardado, **agrupado por estudiante** y
   ordenado por apellido, nombre y fecha.
3. **El reemplazo parcial**, que es el paso más delicado. Volver a pasar lista
   **el mismo día y periodo** cambiando el estado de **algunos** estudiantes, no
   de todos. Comprobar que los cambiados se actualizan, que los demás
   **conservan** su valor, y que **no aparecen filas duplicadas**.
4. **Un lote que no incluye a todo el curso.** Enviar solo dos estudiantes.
   Comprobar que la asistencia de los compañeros **no se borra**: el `DELETE`
   acota por la lista de estudiantes del lote.
5. **Las tres validaciones.** Un lote vacío, un lote con dos asignaciones o
   fechas distintas, y un lote con un estudiante repetido. Los tres deben
   responder **422** y **no dejar ninguna fila**.
6. **Permisos.** Con un **profesor** dueño de la asignación, las dos entradas
   funcionan. Con un profesor **ajeno**, ambas responden **403**. Y comprobar
   que un estudiante que **no pertenece** a la asignación responde 403 al
   intentar pasarle lista.
7. **El consumidor ajeno, que es la mejor prueba cruzada.** Marcar a un
   estudiante como `ausente` varias veces y comprobar que el número cuadra en
   los **dos** sitios que leen esta tabla sin pasar por el dominio: las
   **inasistencias del expediente del estudiante** y el panel de
   **inasistencias por profesor** del dashboard, que muestra los tres peores de
   cada curso. La extracción no los tocó, pero leen lo mismo.
8. **Los dos tenants.** Repetir el paso 2 en el segundo colegio y comprobar que
   **no se mezclan datos**.

**Lo que NO debe interpretarse como fallo de la refactorización.** Son hallazgos
abiertos y **anteriores** a esta capa; están en la lista de los ocho:

- que pasar lista a un curso grande **tarde** o agote conexiones —hallazgo 1—;
- que un fallo de infraestructura en la lectura salga como **500** y no como
  4xx —hallazgo 7—;
- que llamar al controlador **fuera de la ruta** admita un lote heterogéneo o un
  `estado` que no sea `presente` ni `ausente` —hallazgos 3, 4 y 5—.

## Entrega al próximo chat

- Capa activa: **ninguna.** La capa 7 quedó **cerrada para `asistencia`** el
  2026-08-21, al día siguiente de activarse. Los otros ocho dominios siguen en
  espera.
- Última subcapa terminada: **7.1**, cerrada el 2026-08-20. Con ella la frontera
  de persistencia del dominio quedó cerrada.
- **Capa cerrada** el 2026-08-21. No quedan bloqueos.
- Primera subcapa pendiente: **ninguna.** El usuario decidió **cerrar la capa
  aquí**, sin abrir 7.2: el **N+1 en conexiones**, `response_model` y los errores
  de dominio **no se abordan** y pasan a ser trabajo disponible que exigiría una
  orden explícita.
- **Verificación manual: hecha** el 2026-08-21, en local y con resultado
  correcto, **reportada de forma global y confirmada punto por punto solo en el
  paso 3**, el reemplazo parcial —el que más valor tenía en este dominio—. **No
  constan** el lote parcial, la prueba cruzada contra el expediente y el
  dashboard, ni el aislamiento entre tenants. El guion íntegro se conserva por si
  se quiere cerrar ese hueco.
- Compuerta al cerrar 7.1: **872 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro. La suite pasó de **835 al activar la capa a 872**.
- Lo que consiguió 7.1: `asistencia_controller.py` pasó de **84 a 69 líneas** y
  de **3 sentencias SQL inline a 0**; la persistencia vive en
  `app/repositories/asistencia_repository.py`, **3 funciones** que reciben el
  cursor y **el noveno repositorio** del proyecto. Comparador AST contra el
  commit base: **conjunto de SQL idéntico, 3 de 3 literales byte a byte**, sin
  una sola autorización de cambio de texto. **Los dos caminos emiten la misma
  secuencia de `(SQL, parámetros)`, devuelven lo mismo y abren las mismas
  conexiones** que el commit base. **Ninguna prueba cambió de expectativa** salvo
  las cinco que debían fallar, y **las doce heredadas de la capa 1 no se
  tocaron**.
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
  hasta que el usuario decida; publicar dispara el despliegue. Mientras siga
  así, **el rollback es una operación puramente local**: revertir hasta
  `a894441` devuelve el controlador a su versión anterior y elimina el
  repositorio nuevo. **La capa no ha tocado la base de datos** ni siquiera para
  leer; es la **sexta consecutiva** que no abre una conexión a PostgreSQL, y la
  **tercera de esas seis cuyo dominio sí escribe**.
- Siguiente acción exacta: **esperar la decisión del usuario** sobre el punto de
  decisión y la verificación manual. Una instrucción genérica de continuar no la
  sustituye.

## 2026-08-24 — corrección puntual posterior al cierre: permisos O(1)

**La capa 7 para `asistencia` sigue cerrada y no se activó ninguna capa.** Esta
entrada sustituye únicamente el estado vigente de los hallazgos 1 y 2. Los
registros anteriores conservan la situación que existía al cerrar la capa y al
medir el defecto el 2026-08-21.

- Autorización: el usuario nombró el pendiente «Optimización N+1 de conexiones
  en asistencia» y ordenó hacerlo. No autorizó commit, push, deploy, migraciones
  ni acceso a producción.
- Precondiciones: rama `main`; `git status --porcelain=v1 --branch` mostró el
  checkout limpio antes de editar; `HEAD` y la referencia local `origin/main`
  coincidían en `9a90462117884d0bf88697154d6eec261d5021ba`. El commit base de
  la fuente de continuidad más reciente,
  `2ec924a3308581b746a61fa24a44f71433034dbc`, y el base histórico de esta
  bitácora, `a894441f8676b0486e3395f88179cdf6cba61430`, son ancestros de ese
  `HEAD`. Los ocho commits posteriores al base de continuidad quedaron
  explicados en `07_SUPER_ADMIN.md`, `07_PROFESORES.md`,
  `05_PAGOS_TIPOS_PAGO.md` o el índice maestro.
- Línea base focal antes de editar: `tests/test_asistencia_caracterizacion.py`,
  `tests/test_asistencia_historial.py`, `tests/test_asistencia_validaciones.py` y
  `tests/test_permissions.py`: **63 passed, 5 warnings**.
- Evidencia test-first: primero se cambiaron las expectativas para exigir un
  perfil constante y una sola validación del lote. Contra el código anterior el
  conjunto directo terminó con **12 failed, 55 passed**: faltaba la guardia
  batch y los conteos todavía crecían con el número de estudiantes.
- Producto: `app/core/permissions.py` incorpora
  `require_estudiantes_in_asignacion`, que abre una sola conexión y ejecuta una
  sola consulta con `e.id = ANY(%s)`, compara `COUNT(*)` con el tamaño del lote y
  conserva el 403 exacto `El estudiante no pertenece a esta asignación`. La
  función singular queda intacta porque tiene tres consumidores reales fuera
  del bucle: uno en `boletines` y dos en `observaciones`.
- Ruta: `app/routes/asistencia.py` conserva primero las validaciones 422 del
  lote, después llama una sola vez a `require_asignacion_access` y una sola vez
  a la guardia batch. El controlador recibe `data` intacto y en el mismo orden.
- Contrato preservado: no cambian método, path, payload, 200 de éxito, 422 de
  validación, 403 ni sus detalles, autenticación, roles, ownership, tenant,
  orden de precedencia, SQL del controlador, parámetros de escritura,
  transacción, `commit`, `rollback` ni respuesta. Los fallos SQL del permiso no
  se capturan ni se convierten en 403: se propagan como infraestructura y los
  recursos se cierran en `finally`.
- Tenant: la consulta nueva sigue entrando por `get_connection`; conserva el
  aislamiento por `tenant_schema_var` y `search_path`. No se añadió tenant al
  payload ni un predicado nuevo al SQL.
- Perfil comprobado con dobles para lotes de **1, 5 y 30**: admin pasa de `N+1`
  conexiones a **2 totales** —una de pertenencia y una del controlador—;
  profesor pasa de `2N+1` a **3** —asignación, pertenencia y controlador—. El
  modelo documentado el 2026-08-21 proyecta además bajar a aproximadamente 39 y
  43 round-trips para un lote de 30; esa latencia **no se midió contra una base
  real en este turno**.
- Frontend revisado, sin cambios: conserva un único `POST /asistencia` con el
  array ordenado, recarga el historial solo tras éxito y muestra
  `error.response.data.detail` ante un fallo. El número de conexiones y guardias
  internas no forma parte de su contrato.
- Pruebas añadidas o actualizadas: perfil O(1) para admin/profesor, una llamada
  por permiso, lote original intacto, precedencia del 403 de asignación, rechazo
  de pertenencia también para admin, SQL y parámetros batch, cierre de recursos
  en éxito/rechazo/error y propagación de fallos de base de datos.
- Resultados específicos:
  - conjunto directo tras implementar: **67 passed, 5 warnings**;
  - conjunto focal final, incluidos historial y permisos: **72 passed, 5
    warnings**;
  - Ruff focal sobre los cinco archivos de producto/prueba: **exit 0**.
- Compuerta global: la primera ejecución dentro del sandbox terminó con **1086
  passed y 30 errores de preparación**, todos por `PermissionError` al acceder a
  `AppData/Local/Temp/pytest-of-David`; Ruff y `pip check` sí pasaron. La
  repetición del mismo `python scripts/verify.py` fuera del sandbox, con acceso a
  temporales, terminó con **1116 passed**, Ruff correcto y dependencias íntegras,
  todo en **exit 0**.
- Archivos modificados: `app/core/permissions.py`,
  `app/routes/asistencia.py`, `tests/test_permissions.py`,
  `tests/test_asistencia_caracterizacion.py`,
  `tests/test_asistencia_validaciones.py`, esta bitácora, el índice maestro y
  `PROMPT_CONTINUACION.md`. Ningún archivo de `frontend-react` se modificó.
- Decisión registrada: se ejecutó el plan de dos pasos ya documentado y se
  descartó compartir el cursor del controlador. Esa alternativa cambiaría
  firmas usadas por otros dominios y abriría la transacción antes de terminar
  las validaciones.
- Riesgos residuales: autorización, pertenencia y escritura siguen en
  conexiones separadas, por lo que la ventana TOCTOU preexistente no cambia. La
  guardia batch presupone una colección no vacía y sin duplicados; su único
  consumidor la llama después de las validaciones 422 que garantizan ambas
  condiciones. Validar todo el lote en una sola consulta usa una instantánea
  única en vez de N instantáneas sucesivas, sin cambio observable esperado.
- Staging y verificación manual pendiente: en un tenant no productivo, guardar
  un lote de 30 como admin y como profesor dueño, confirmar el mismo 200 y el
  historial; repetir con profesor ajeno y con un estudiante de otro curso para
  confirmar ambos 403; repetir en el segundo tenant para comprobar aislamiento.
  Si el entorno expone métricas del pool, confirmar 2 y 3 adquisiciones. **No se
  ejecutó este guion ni se atribuye evidencia a GitHub Actions.**
- Rollback: no requiere rollback de datos ni migraciones. Antes de un commit se
  pueden descartar exclusivamente los ocho archivos listados; después de un
  eventual commit, revertir únicamente ese commit restaura el bucle anterior.
- Siguiente acción exacta: revisión del diff por el usuario y, si lo aprueba,
  verificación manual en staging y su flujo de commit/push. No hay subcapa
  pendiente, no hay capa activa y no se inicia otro hallazgo.
