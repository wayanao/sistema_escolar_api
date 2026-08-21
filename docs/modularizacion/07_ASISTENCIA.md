# Capa 7: asistencia

Última revisión: 2026-08-20.

## Control

- Estado: **Activa** desde el 2026-08-20.
- Commit base: `a894441f8676b0486e3395f88179cdf6cba61430`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, **no iniciada**.
- Código de producto modificado al activar: **ninguno**.
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

| # | Supuesto | Origen documental | Estado |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/asistencia.py` y `app/controllers/asistencia_controller.py` | Inventario de contratos de 0.0 y subcapa 1.4g | **No verificado.** `notas` demostró que el recuento de archivos puede fallar: daba dos y eran cuatro, con un tercio de la persistencia en un servicio |
| 2 | **El dominio escribe**, con un reemplazo parcial transaccional y `rollback` | Inventario de contratos de 0.0, que lo registra como efecto a preservar | **Documentado, no medido.** Es el supuesto que en los tres dominios anteriores fijaba el perfil de riesgo; aquí llega resuelto y 7.0 debe **cuantificarlo**: qué tablas, qué transacción y quién es dueño del ciclo de vida |
| 3 | `guardar_asistencia_controller` conserva el idioma antiguo y `obtener_historial_asistencia` usa `get_cursor()` | Subcapa 1.4g, «1 sitio de 2» | **No verificado hoy.** Si sigue así, el dominio tiene **dos idiomas de conexión conviviendo**, cosa que no tenía ninguno de los tres anteriores |
| 4 | **El controlador tiene exactamente dos funciones** | **Inferencia de patrón** a partir del «1 sitio de 2» de 1.4g | **No verificado, y marcado como inferencia.** «Sitio» en la capa 1 significaba apertura de conexión, **no** función. Un controlador puede tener funciones que no abran ninguna. Es el supuesto con más probabilidad de resultar falso, y se marca así a propósito: es lo que permitió refutar limpiamente el de los permisos en `ventas` |
| 5 | **Los permisos no son uniformes**: usuario autenticado con acceso a la asignación, y el estudiante debe pertenecer a ella; `403` y lote inválido `422` | Inventario de contratos de 0.0 | **No verificado.** En `ventas` el supuesto equivalente resultó **falso** |
| 6 | Consume `resolver_asignacion_academica_id_cursor` de `app/services/asignacion_academica.py` | Subcapa 6.0, que enumeró los nueve consumidores | **No verificado.** Ese servicio está **fuera de alcance**: se lee, no se toca |
| 7 | `estudiantes_repository` **lee `asistencia`** en el bloque del expediente | Subcapa 6.2 | **No verificado desde este lado.** Consumidor **ya migrado**; romper su contrato no haría fallar las pruebas de `asistencia` |
| 8 | `dashboard_repository` **lee `asistencia`** para `GET /dashboard/inasistencias/{profesor_id}`, contando solo `estado ILIKE 'ausente'` y devolviendo los tres peores de cada curso | Subcapas 7.0 y 7.1 de `dashboard` | **No verificado desde este lado.** Segundo consumidor **ya migrado** |
| 9 | **El estado se compara por texto**, con `ILIKE 'ausente'` | Guion de verificación manual de la capa 6 y contrato de `dashboard` | **No verificado dentro del dominio.** 7.0 debe **mapear dónde** aparece ese criterio y si el propio dominio lo usa al escribir. Es el eco del hallazgo del `ILIKE` de `ventas`: **buscarlo, no corregirlo** |
| 10 | Existen ya `tests/test_asistencia_historial.py` —5 pruebas— y `tests/test_asistencia_validaciones.py` | Subcapa 1.4g e inventario de 0.0 | **No verificado hoy.** 7.0 debe medir **qué cubren realmente** y no suponer que bastan |
| 11 | Contratos ya fijados por 1.4g: una fila con `fecha` nula **aparece igualmente** con el historial vacío; `periodo` toma **1** por defecto; la agrupación reúne varias fechas del mismo estudiante en una sola entrada | Subcapa 1.4g, «comportamiento conservado que no era evidente» | **No verificado hoy.** Si siguen vigentes, son contratos que una extracción **no puede cambiar** |
| 12 | `asistencia` fue una de las **ocho tablas averiadas** de `tenant_2005`, con ~3.125 filas, y tiene clave foránea **a `asignaciones`** con `ON DELETE CASCADE` y **a `estudiantes`** | Capa 3 y subcapa 6.0 | **Confirmado documentalmente**, sin cambio. Un `DELETE` introducido por una extracción borraría en cascada o fallaría contra la clave |

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

## Línea base

Pendiente: la fija 7.0 antes de tocar nada.

| Comprobación | Comando | Resultado |
|---|---|---|
| Compuerta heredada, antes de tocar nada | `.\venv\Scripts\python.exe scripts\verify.py` | **Pendiente.** Debe dar **835 pruebas, exit 0**; si difiere, hay deriva y se investiga antes de seguir |
| Pruebas específicas heredadas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_asistencia_historial.py tests\test_asistencia_validaciones.py` | Pendiente |
| Pruebas específicas nuevas | Pendiente de nombrar en 7.0 | Pendiente |
| Ruff | Ejecutado por la compuerta global y sobre los archivos nuevos | Pendiente |
| Dependencias | Ejecutado por la compuerta global | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas y conexiones | **Pendiente, no iniciada** |
| 7.1 | Primera extracción protegida | **Sin definir**: depende de la evidencia de 7.0 |
| 7.2+ | Sin definir | **Sin definir** |

El desglose se deja deliberadamente sin decidir hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y las tres capas 7 anteriores. Las
subcapas innecesarias se marcarán `No aplica` con explicación. **Nunca se
ejecutan dos subcapas en el mismo turno.**

## Subcapa 7.0 — trabajo exacto

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
  exacto de arriba y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **la capa 7 para el dominio `asistencia`**, activada el
  2026-08-20. **Es el único dominio activo**; los otros ocho siguen en espera.
- Última subcapa terminada: **ninguna**.
- Primera subcapa pendiente: **7.0**, no iniciada. Su trabajo exacto está
  arriba, en quince pasos, y el punto donde detenerse es antes de 7.1.
- Commit base: `a894441f8676b0486e3395f88179cdf6cba61430`, rama `main`,
  **publicado y desplegado**, comprobado contra el remoto real.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1), evidencia de GitHub Actions posterior a la
  capa 0, y los **tres pasos del guion de `ventas`** que no constan. La
  credencial privilegiada de la capa 4 sigue **sin rotar**.
- Compuerta que 7.0 debe reproducir antes de tocar nada: **835 pruebas, exit 0**,
  Ruff correcto y `pip check` íntegro. Si difiere, hay deriva.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** `dashboard`, `notas` y `ventas` están cerrados en sus
     propias bitácoras y los otros ocho siguen en espera.
  2. **El dominio escribe, y eso ya está documentado por la capa 0**, no es un
     supuesto abierto. Lo que falta es cuantificarlo.
  3. **Llega con pruebas ya escritas**, cosa que no le pasó a ninguno de los
     tres anteriores. **No suponer que bastan**: se escribieron para proteger el
     ciclo de vida de conexiones, no el contrato HTTP.
  4. **Llega parcialmente migrado por la capa 1**, con dos idiomas de conexión
     conviviendo. Unificarlos cambiaría los conteos y **no es parte de la
     extracción**.
  5. **Dos consumidores ajenos ya migrados** leen esta tabla:
     `estudiantes_repository` y `dashboard_repository`. Romper su contrato **no
     haría fallar las pruebas de `asistencia`**, solo la compuerta global.
     Ejecutarla siempre completa.
  6. **No fiarse de los nombres.** El supuesto 4 —que el controlador tiene dos
     funciones— está marcado **como inferencia de patrón** a propósito: «sitio»
     en la capa 1 significaba apertura de conexión, no función.
  7. **No corregir ningún hallazgo**, ni los de esta capa ni los treinta y tres
     que dashboard, notas y ventas dejaron abiertos.
  8. **El `ILIKE 'ausente'` se mapea, no se arregla.**
- **Residuos documentales abiertos**: `07_VENTAS.md` describe su capa como no
  publicada y su rollback como puramente local, y **ya no es cierto**; el índice
  lo registra corregido, la bitácora cerrada no se editó. Y el índice conserva
  un párrafo que declara abierto el punto de decisión de `ventas` y pendiente su
  verificación manual, cuando las dos cosas se resolvieron. Corregir cualquiera
  de los dos exige una orden explícita.
- Siguiente acción exacta: ejecutar únicamente **7.0** y detenerse antes de 7.1.
