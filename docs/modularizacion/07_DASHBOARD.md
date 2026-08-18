# Capa 7: dashboard

Última revisión: 2026-08-17.

## Control

- Estado: **Activa** desde el 2026-08-17.
- Commit base: `123637ee80895023ecece9c32df526ef4eddd1e5`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.1**, definida y **no iniciada**. La **7.0**
  quedó **cerrada** el 2026-08-17.
- Código de producto modificado al activar: **ninguno**. Tampoco en 7.0: su diff
  es un solo archivo de prueba nuevo.
- Dominio de esta capa: **dashboard, y solo ese**. La capa 7 del índice es
  «resto de dominios» y ordena expresamente **priorizar uno a la vez**, así que
  esta bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-17, con el texto que
  `PROMPT_CONTINUACION.md` conservaba preparado para la capa 7 y cuya condición
  de caducidad se cumplía —el índice seguía sin capa activa y con la 7 en
  espera—. El marcador `DOMINIO` llegó **sin rellenar**; se preguntó y el
  usuario eligió `dashboard`. No se dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

## Objetivo

Migrar el dominio de **dashboard** con contratos y pruebas, conservando su
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

## Diferencia de objetivo respecto a las capas 4, 5 y 6

Es la primera capa del programa cuyo objetivo **contempla añadir algo** y no
solo mover código. Las capas 5 y 6 fueron refactorizaciones puras que no
cambiaron ni un contrato; aquí el índice autoriza `response_model`, errores de
dominio y pruebas HTTP, pero **subordinados a caracterizar y conservar primero**.

Esto no relaja la regla, la ordena: sin caracterización previa que demuestre la
respuesta actual, no se añade nada. Ver el riesgo registrado sobre
`response_model`, que en FastAPI **filtra** los campos no declarados y puede
cambiar el payload en silencio.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último
  resultado registrado, al cerrar la capa 6, es **714 pruebas, exit 0**, Ruff
  correcto y `pip check` íntegro; **no se reprodujo durante esta activación
  documental**. 7.0 debe reproducirlo antes de tocar nada.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  El valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una auditoría propia. Sobre
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` pesa el pendiente del
  2026-08-17: se quedó sin ejemplo real que la respalde y se conserva como
  margen.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—, ambos con 37 claves foráneas, 30 secuencias propias y 30
  migraciones registradas.
- Contratos de lectura financieros fijados por la capa 4 y protegidos por su
  caracterización, con los conteos 6/15 del estado de cuenta de reportes,
  1/13/37 de cuentas y 5/12/12 de cartera. Dependen de `cobros.py`.
- Frontera de persistencia de pagos establecida en la capa 5:
  `app/repositories/pagos_repository.py` con 16 funciones que reciben el cursor.
- Frontera de persistencia de asignaciones y estudiantes establecida en la capa
  6: `estudiantes_repository` con 11 funciones y `asignaciones_repository` con
  33, ambas con el mismo patrón —funciones que **reciben el cursor existente** y
  no abren, cierran, confirman ni revierten recursos—. Es el patrón que esta
  capa debe seguir si extrae persistencia.
- La última evidencia de GitHub Actions corresponde a la capa 0. Hubo pushes
  autorizados el 2026-08-15 y el 2026-08-17, pero **no se ha obtenido evidencia
  de ningún run**; esa verificación permanece **pendiente y aceptada**. No se
  atribuye CI remota porque `HEAD` coincida con `origin/main`.

## Lo que el programa cree saber de dashboard, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6: **un supuesto heredado se marca como no
verificado y se comprueba en la subcapa 0**. La capa 6 se activó anticipando que
sus dominios escribían archivos, y era falso. Nada de lo que sigue se da por
bueno.

**Los siete quedaron resueltos en 7.0**, uno por uno y con evidencia. Seis se
confirmaron y **uno resultó falso**.

| Supuesto | Origen | Resultado en 7.0 |
|---|---|---|
| Dashboard **no tiene repositorio propio** | La capa 6 enumeró los existentes | **Confirmado.** Hay cinco repositorios —asignaciones, estudiantes, pagos, plan de clases y reportes— y ninguno es de dashboard. Toda su persistencia vive en el controlador. Fijado por prueba |
| Dashboard **consume `resolver_asignacion_academica_id_cursor`** | 6.0 lo listó entre los nueve consumidores, verificado desde el lado de asignaciones | **Confirmado desde este lado.** Lo usan **cuatro** funciones: la precondición de pertenencia, `_obtener_notas_profesor` y los dos rankings |
| Dashboard **lee tablas académicas con SQL inline** y promedia con `TRUNC(..., 2)` | 6.2 leyó esos literales para decidir dónde vivían las lecturas del expediente | **Confirmado y precisado.** Son **8 sentencias inline**. Pero no hay una fórmula de promedio, hay **dos distintas**, y no dan la misma cifra. Ver hallazgos |
| Dashboard **concentra los cálculos más caros**, con varias consultas de promedios por estudiante | Visto **de pasada** en las capas 4 y 6 | **Refutado como N+1.** Cada entrada resuelve su panel con **una sola consulta agregada** y ningún conteo depende del número de estudiantes. Lo caro no son las consultas: son las **conexiones**, hasta cuatro por petición |
| Dashboard **no escribe archivos** vía `app/services/storage.py` | Solo se demostró que branding y plan de clases **sí** lo usan | **Confirmado.** Ni el controlador ni la ruta mencionan `storage`. El rollback de esta capa es de código, no de archivos. Fijado por prueba |
| Dashboard **es de solo lectura** | Nadie lo había comprobado | **Confirmado.** Cero `INSERT`, `UPDATE` y `DELETE`, cero `commit` y cero `rollback`: **ninguna función es dueña de una transacción**. Fijado por prueba |
| Los permisos **no son uniformes** | Capa 6 | **Confirmado y cuantificado.** Siete entradas con **cuatro modelos distintos**: router para todos, admin estricto, `require_profesor_scope` y `require_asignacion_access`, más un filtro propio de la ruta |

## Alcance autorizado

- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de dashboard** mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, orden, nulos, redondeos, transacciones y
  errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado tres veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas críticas antes y después.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: notas, boletín, asistencia,
  observaciones, planilla, planeador anual, plan de clases, ventas, branding,
  profesores, super admin y cualquier otro. Esta capa es de un solo dominio.
  Se permite la lectura mínima indispensable para caracterizar un contrato que
  dashboard consuma, sin modificarlo.
- `app/services/asignacion_academica.py`, del que dependen nueve módulos, y
  `cobros.py`, del que dependen los contratos financieros de la capa 4: se leen
  si hace falta, **no se tocan**.
- Los hallazgos abiertos de las capas 5 y 6, incluidos el **paso 2 de la clave
  de idempotencia** de `POST /pagos`, los status codes 500 de
  `tipos_pagos_controller`, la **ausencia de lock en el alta y la edición de
  asignaciones**, el `SELECT *` de `GET /estudiantes/{id}`, las dos rarezas de
  status code, las tres parejas de literales gemelos y el código muerto
  duplicado que el usuario decidió conservar. **No entran por inferencia.**
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa»: la colisión de mayúsculas en reportes,
  `/estado-cuenta/curso`, los 14 índices duplicados, la deduplicación de
  `_tabla_pagos_aplicaciones_existe`, `_obtener_saldo_concepto` y la auditoría
  de capacidad de la capa 2.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, redondeos, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos los **redondeos y el número de decimales** de cualquier
  promedio o total que el dashboard presente.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de lectura financieros fijados por la capa 4 siguen pasando su
  caracterización, incluidos los conteos 6/15, 1/13/37 y 5/12/12.
- Las fronteras de persistencia de las capas 5 y 6 no se alteran: si dashboard
  necesita una lectura que ya existe allí, se decide **con evidencia** y sin
  duplicarla a ciegas.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.
- Ninguna escritura de archivos cambia de momento, de nombre ni de destino sin
  una decisión explícita y un rollback documentado.

## Línea base registrada en 7.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_dashboard_caracterizacion.py tests\test_dashboard_controlador.py tests\test_dashboard_routes.py` | **77 pasaron** en 0,64 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **755 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La compuerta heredada se reprodujo antes de tocar nada: **714 pruebas, exit 0**,
coincidiendo con lo registrado al cerrar la capa 6. La suite pasó de **714 a
755** con la caracterización de 7.0.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas y conexiones | **Cerrada** |
| 7.1 | Extraer la persistencia a `dashboard_repository` sin cambiar SQL, conteos ni ciclo de vida | **Pendiente**, definida y no iniciada |
| 7.2 en adelante | **Sin decidir** | — |

El desglose posterior a 7.0 se dejó deliberadamente sin decidir, igual que hizo
la capa 6. Con la evidencia del inventario, **7.1 queda definida** y el resto
sigue abierto: si 7.1 basta para cerrar la frontera de persistencia, la capa
puede pasar directamente a su cierre.

Las subcapas innecesarias se marcarán `No aplica` con explicación. Nunca se
ejecutan dos subcapas en el mismo turno.

## Inventario y contratos fijados en 7.0

La frontera son **7 entradas HTTP**, todas `GET`, todas de **solo lectura**.
Ninguna declara `response_model` ni `status_code` explícito. El router lleva
`Depends(get_current_user)`, así que toda entrada exige un usuario autenticado;
sobre eso, **cada una añade lo suyo**.

| Entrada | Permiso | Contrato observable que debe conservarse |
|---|---|---|
| `GET /dashboard/cumpleanos/admin` | **admin estricto** | Lista de `{estudiante_id, nombre, apellido, curso, fecha_nacimiento}`; la fecha va como texto o `None`. `dias` es query 0..31, por defecto 7, y fuera de rango da **422**. `LEFT JOIN cursos`: **incluye estudiantes sin curso** |
| `GET /dashboard/cumpleanos/profesor/{profesor_id}` | **profesor propio o admin** | Mismo payload, pero `JOIN cursos` y `EXISTS` sobre una asignación **activa** del profesor, con el curso activo: **excluye** a quien no tenga curso |
| `GET /dashboard/inasistencias/{profesor_id}` | **profesor propio o admin** | `{curso_id, curso, estudiante_id, nombre, total_fallas, posicion}`; **los tres peores de cada curso**, contando solo `estado ILIKE 'ausente'` |
| `GET /dashboard/notas-bajas/{profesor_id}` | **profesor propio o admin**, más filtro propio | `{nombre, curso, materia, promedio, color}`; `curso_id` es **obligatorio** y sin él responde **422**; promedio **< 3,0**, orden ascendente, **máximo 5 filas**; color `red` o `yellow` |
| `GET /dashboard/notas-altas/{profesor_id}` | idem | Igual, con promedio **≥ 3,0**, orden descendente y color `green` |
| `GET /dashboard/ranking/{asignacion_id}/{periodo}` | **`require_asignacion_access`** | `{id, nombre, promedio}` de la asignación y el periodo, promedio **< 3,0**, ascendente |
| `GET /dashboard/ranking-mejor/{asignacion_id}/{periodo}` | idem | Igual, con **≥ 3,0** y descendente |

- Tenant por `search_path` desde el JWT, igual que en las capas anteriores.
- El filtro de rendimiento de las dos entradas de notas se ejecuta **en la capa
  de rutas**, `validar_filtro_rendimiento_profesor`, y da **422** sin curso,
  **403** si el curso no es del profesor y **403** si la asignación no pertenece
  a ese curso. Se ejecuta **fuera** del `try/except` del endpoint.
- `require_profesor_scope` **no consulta la base**: resuelve con el JWT.
  `require_asignacion_access` **sí**, y solo cuando el rol es `profesor`.

### Propiedad transaccional

**Ninguna tabla recibe escritura y ninguna función abre una transacción propia.**
No hay un solo `commit` ni `rollback` en el dominio; una prueba estructural lo
fija.

Conviven **dos** estilos de ciclo de vida, y esta capa **no los unifica**:

- `get_connection()` con `try/finally` manual en cuatro funciones: los dos
  cumpleaños y las dos precondiciones de permiso;
- `with get_cursor()` en las otras cuatro, migradas en la subcapa 1.4d de la
  capa 1.

## Línea base de consultas y conexiones

Medida herméticamente con dobles de cursor y conexión, y **fijada por pruebas**,
no escrita a mano. Los conteos excluyen autenticación, `search_path` y la
sentencia de timeouts de cada checkout.

| Camino | Consultas | Conexiones |
|---|---:|---:|
| `GET /dashboard/cumpleanos/admin` | 1 | 1 |
| `GET /dashboard/cumpleanos/profesor/{id}` | 1 | 1 |
| `GET /dashboard/inasistencias/{id}` | 1 | 1 |
| `GET /dashboard/ranking/...`, como **admin** | 2 | 1 |
| `GET /dashboard/ranking/...`, como **profesor** | 3 | 2 |
| `GET /dashboard/notas-*` sin asignación, profesor | 2 | 2 |
| `GET /dashboard/notas-*` con asignación, **admin** | 5 | 3 |
| `GET /dashboard/notas-*` con asignación, **profesor** | **6** | **4** |

Lectura del resultado, sin optimizar todavía:

- **No hay N+1**, y el supuesto heredado de «varias consultas de promedios por
  estudiante» queda **refutado**: cada panel se resuelve con una sola consulta
  agregada. Una prueba lo fija comparando 1 fila contra 50.
- El coste real está **en las conexiones, no en las consultas**. El camino más
  caro abre **cuatro**, y cada una paga además su `search_path` y su sentencia
  de timeouts, que estos conteos no incluyen.
- Ser admin **abarata** las dos rutas protegidas por `require_asignacion_access`,
  porque esa comprobación sale sin consultar.

## Subcapa activa: trabajo exacto de 7.0

1. Confirmar `main`, árbol limpio y que todo commit posterior al base
   `123637ee80895023ecece9c32df526ef4eddd1e5` esté explicado en esta bitácora.
2. Reproducir la compuerta heredada y determinar las pruebas específicas sin
   ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas **de dashboard**. No leer historia global ni
   código de los demás dominios de la capa 7.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, cálculos, persistencia, escrituras, archivos y efectos
   laterales.
5. Registrar los contratos observables exactos: rutas, métodos, payloads,
   status codes, permisos por rol, tenant, ownership, orden, nulos, **redondeos
   y decimales**, transacciones y errores.
6. Comprobar con evidencia **los siete supuestos que esta activación registra
   sin verificar**, uno por uno, y corregir la tabla con lo que se encuentre.
   Que un supuesto venga de la capa 6 no lo convierte en evidencia sobre este
   dominio.
7. Caracterizar con pruebas los caminos que una extracción posterior pueda
   alterar. 7.0 **no autoriza** una extracción ni un cambio de producto.
8. Medir o instrumentar herméticamente el número de consultas de los caminos
   críticos, en particular los promedios por estudiante, y **determinar si hay
   N+1 o no**; no optimizarlos todavía.
9. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 7.0.
10. Actualizar esta bitácora, definir 7.1 con la evidencia obtenida y detenerse
    sin iniciarla.

## Criterios de cierre de la subcapa 7.0

- El dominio y sus consumidores están inventariados con archivos y puntos de
  entrada concretos, sin lectura global innecesaria, y con su frontera clara
  frente a los dominios que **no** entran en esta capa.
- Los contratos HTTP, de permisos por rol, tenant, ownership, de cálculo y de
  transacción están enumerados y protegidos por caracterización suficiente,
  incluidos los redondeos.
- Los siete supuestos heredados están **resueltos con evidencia**, confirmados o
  refutados, y la tabla queda corregida.
- Las consultas críticas tienen una línea base reproducible, fijada por
  aserciones y no anotada en prosa, y la pregunta del N+1 queda respondida con
  medición.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 7.0.
- La subcapa 7.1 queda definida y no iniciada.

Los siete criterios se cumplieron. El diff de 7.0 contiene **un solo archivo
nuevo** y **ningún archivo rastreado modificado**, igual que los de 5.0 y 6.0.

## Hallazgos de 7.0, registrados y sin corregir

Ninguno se corrige por inferencia: son hallazgos del inventario, no defectos de
la subcapa. Corregir cualquiera exige una decisión explícita del usuario.

- **Las dos precondiciones de permiso ignoran el estado `activo`.** Es el
  hallazgo más importante de 7.0 porque **toca permisos**.
  `profesor_tiene_curso_controller` y
  `profesor_tiene_asignacion_en_curso_controller` consultan `asignaciones` sin
  `activo = TRUE`, así que **un profesor cuya asignación fue desactivada
  conserva el acceso** al rendimiento de ese curso. La incoherencia es interna:
  la consulta de cumpleaños **del mismo controlador** sí exige `a.activo = TRUE`,
  y la capa 6 dejó registrado que desactivar es precisamente como este sistema
  «borra». Corregirlo cambia quién puede ver qué, así que no se toca sin orden.
  Una guardia de prueba falla si alguien lo hace sin registrarlo.
- **Hasta cuatro conexiones por petición, en serie.** El camino de notas con
  asignación abre cuatro conexiones sucesivas: una por cada precondición y una
  para la consulta. **No hay anidamiento** —cada una se cierra antes de que se
  abra la siguiente—, así que **no contradice**
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2`; pero es **la evidencia real
  que a esa constante le faltaba** desde el 2026-08-17, y pertenece a la
  auditoría de capacidad de la capa 2. Se registra, no se actúa.
- **La asignación académica se resuelve dos veces** en ese mismo camino, con el
  mismo `asignacion_id`: una en la precondición de pertenencia y otra dentro del
  controlador, cada una en su propia conexión.
- **Dos definiciones distintas de «promedio» en el mismo panel.** Notas altas y
  bajas promedian **los promedios por clase**, `TRUNC(AVG(promedio_clase), 2)`;
  los rankings promedian **las notas planas**,
  `TRUNC(AVG(CAST(n.nota AS numeric)), 2)`. Con 4,0 en una clase de dos notas y
  2,0 en otra de seis, la primera fórmula da **3,00** y la segunda **2,50**: el
  mismo estudiante aparece aprobado en un panel y en rojo en el otro. Y la capa
  6 ya registró una **tercera** en estudiantes, `ROUND(..., 1)`. Ninguna es un
  error; son contratos distintos que hoy nadie declara.
- **Las siete entradas absorben `Exception` y responden 400 con `str(e)`.** Un
  fallo de infraestructura se presenta como error del cliente **y el texto de la
  excepción viaja en el `detail`**, así que un error de PostgreSQL puede llegar
  al navegador. Es la misma familia que el hallazgo de la capa 5 en
  `tipos_pagos_controller`, pero aquí **no se registra nada en el log** y además
  **se devuelve el mensaje interno**. Cambiar el status code es contrato
  observable; registrar el traceback no lo es.
- **El filtro de rendimiento consulta la base desde la capa de rutas.** No es
  SQL inline —la invariante que dejó 6.5 se conserva: las rutas de este dominio
  no contienen SQL, y una prueba lo fija—, pero `validar_filtro_rendimiento_profesor`
  llama a dos funciones que abren conexión, y lo hace **fuera** del
  `try/except`. Consecuencia observable: un fallo de infraestructura **ahí** sale
  como **500**, mientras que el mismo fallo dentro del endpoint sale como 400.
- **Doble validación divergente de `dias`.** La ruta rechaza con **422** fuera
  de 0..31; el controlador **recorta en silencio** y cae a 7 ante un valor no
  numérico. Por HTTP el recorte es inalcanzable, porque `Query(ge=0, le=31)`
  responde antes. Queda fijado por prueba tal como está.
- **Cuarta pareja de literales SQL gemelos del programa.** Los dos rankings solo
  difieren en `< 3.0` frente a `>= 3.0` y en `ASC` frente a `DESC`: una prueba
  fija que uno se obtiene del otro con esas dos sustituciones. Unificarlos es
  legítimo, pero es decisión del usuario y **no se pidió**, igual que las tres
  parejas de la capa 6.
- **f-strings en SQL, hoy no inyectables.** `_obtener_notas_profesor` interpola
  el comparador, el orden y el filtro de asignación desde literales del propio
  código, y `_filtro_rango_cumpleanos` interpola el alias de tabla. Los valores
  siempre van parametrizados. Queda anotado como guarda: **ninguna extracción
  futura debe abrir esa construcción a entrada del cliente**.
- **`periodo: int = 1` es un parámetro de ruta con valor por defecto** en los
  dos rankings. Al estar en el path nunca puede faltar, así que el defecto es
  inalcanzable.

## Subcapa 7.1 — trabajo exacto, definido y NO iniciado

Extraer la persistencia de dashboard, y solo eso, siguiendo el patrón que las
capas 5 y 6 dejaron probado tres veces.

1. Revalidar Git y limitar la inspección a `dashboard_controller.py`, su ruta y
   sus pruebas. **No inspeccionar otros dominios de la capa 7.**
2. Conservar la caracterización de 7.0 y ampliarla solo si una extracción
   concreta lo exige, **antes** de mover producto.
3. Extraer las **8 sentencias** a `app/repositories/dashboard_repository.py`,
   con funciones que **reciben el cursor existente** y no abren, cierran,
   confirman ni revierten recursos, igual que los cuatro repositorios ya
   existentes.
4. **Punto delicado propio de este dominio**: dos de las ocho consultas no son
   un literal único, sino una **composición** de `_cte_rango_cumpleanos()`, el
   cuerpo, `_filtro_rango_cumpleanos()` y el `ORDER BY`. Los dos fragmentos
   deben viajar con las consultas que los usan. Conservar byte por byte cada
   trozo y el resultado concatenado.
5. **No cambiar el ciclo de vida.** Las cuatro funciones que usan
   `get_connection()` con `try/finally` siguen usándolo; convertirlas a
   `get_cursor()` es trabajo de la capa 1 y **no está autorizado aquí**.
6. Decidir **con evidencia** si las dos consultas de precondición de permiso van
   al repositorio. El precedente es 6.4, que llevó allí las precondiciones sobre
   catálogos por no existir un repositorio de esos dominios; registrar la
   decisión **antes** de mover.
7. Conservar byte por byte las cadenas SQL, sus parámetros y su orden. Si
   aparecen dos literales idénticos salvo la sangría, **no unificarlos sin
   autorización explícita**; y **no unificar las dos consultas gemelas de
   ranking**, que es un hallazgo abierto.
8. **No corregir ninguno de los diez hallazgos de 7.0**, en particular ni el
   `activo` ausente de las precondiciones, ni los status codes, ni las dos
   fórmulas de promedio.
9. Verificar que los conteos de consultas y conexiones de 7.0 **no cambian**, y
   ejecutar un comparador AST contra el commit base de la capa,
   `123637e`, exigiendo conjunto de SQL idéntico. Excluir los docstrings antes
   de comparar, que es la lección 13 de la capa 6.
10. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
    `git diff --check`; documentar y detenerse antes de decidir 7.2.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- El dominio quedó migrado con contratos estables y pruebas, **sin arrastrar
  otros dominios**.
- `response_model`, errores de dominio y pruebas HTTP, si se añadieron, llegaron
  **después** de caracterizar y conservando la respuesta existente, demostrado.
- No se creó ninguna abstracción compartida sin dos consumidores reales.
- Los contratos del frontend y de la base de datos permanecen intactos.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados; si 7.0 descubre
  que el dominio escribe archivos, el rollback debe cubrirlos explícitamente.
- El índice maestro queda actualizado y **ningún otro dominio se activa sin
  orden explícita del usuario**.

## Decisiones

- Se usa `123637ee80895023ecece9c32df526ef4eddd1e5` como commit base porque es
  el `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main`. **No se reutilizó ningún hash de memoria**: se comprobó el
  `HEAD` real antes de registrarlo. Es el commit siguiente a `bf075a0`, que
  cerró la capa 6, y es documental.
- **El dominio es `dashboard` y lo eligió el usuario.** La autorización llegó
  con el marcador `DOMINIO` sin rellenar; se le preguntó explicando qué es un
  dominio y por qué la capa exige nombrar uno, y eligió. **No se dedujo por
  inferencia**, que es exactamente lo que el propio texto de la autorización
  prohíbe al decir que activar sin nombrarlo dejaría el alcance abierto.
- El usuario eligió explícitamente **continuar manteniendo pendientes** la
  calibración de `DB_STATEMENT_TIMEOUT_MS` y la evidencia remota de GitHub
  Actions. Ninguna se marca como cumplida y ambas conservan su riesgo.
- La activación consume la autorización puntual que `PROMPT_CONTINUACION.md`
  guardaba para la capa 7; queda retirada de ese archivo con el mismo criterio
  aplicado a las capas 3, 4, 5 y 6. **Esa retirada no se hace en este turno**:
  el alcance autorizado del turno de activación es exclusivamente el índice y
  esta bitácora nueva. Se hará en el turno de 7.0, que ya toca documentación.
- El commit base **está publicado y desplegado**, como el de la capa 6. Es por
  tanto un punto de rollback real, pero revertir a él exigiría otro push y otro
  despliegue, no una operación local.
- **El desglose de subcapas posteriores a 7.0 se deja sin decidir** hasta tener
  la evidencia del inventario. Alternativa descartada: proponer ya un 7.1 y un
  7.2 por analogía con las capas 5 y 6, que habría fijado un plan sobre un
  dominio no inspeccionado. La capa 6 hizo lo mismo y le funcionó.
- **Los supuestos heredados se registran como no verificados**, no como hechos.
  Es la lección 12 de la capa 6, donde el supuesto de los archivos resultó
  falso y solo se detectó porque estaba marcado así. **Sirvió**: de los siete,
  uno resultó falso.
- **7.0 no retiró ni corrigió nada**, aunque encontró diez cosas anotables. Su
  diff es un solo archivo nuevo, igual que los de 5.0 y 6.0. El hallazgo del
  `activo` ausente **toca permisos**, que es exactamente lo que las invariantes
  de la capa prohíben cambiar sin orden explícita.
- **La caracterización se escribió con dobles, sin tocar PostgreSQL.** 7.0 no
  abrió una sola conexión a la base, igual que 5.0 y 6.0.
- **No se ampliaron las pruebas existentes, se añadió un archivo nuevo.**
  `test_dashboard_routes.py` ya cubría la capa HTTP con solidez —delegación,
  traducción a 400, los 403 de scope y acceso, el 422 del filtro, el mapa de
  dependencias y el contrato OpenAPI— y `test_dashboard_controlador.py` cubría
  las cuatro funciones que migraron a `get_cursor` en la subcapa 1.4d. Lo que
  faltaba era **lo que ninguno de los dos tocaba**: las cuatro funciones que
  siguen usando `get_connection`, los conteos y las guardias estructurales.
  Alternativa descartada: ampliar los archivos existentes, que habría mezclado
  la caracterización de la capa 7 con documentos escritos para otras capas.
- **Los conteos se miden a través de la ruta, no solo del controlador.** Es la
  única forma de ver las conexiones que abren las precondiciones de permiso, que
  viven en la capa HTTP y en `app/core/permissions.py`. Medir solo el
  controlador habría dado 1 o 2 conexiones y habría escondido el camino de
  cuatro.
- **`app/core/permissions.py` se leyó pero no se tocó ni se caracterizó
  aparte.** Es infraestructura compartida por varios dominios; aquí solo se fija
  su efecto sobre los conteos de dashboard. Migrarlo no es de esta capa.

## Riesgos

- **`response_model` puede cambiar el payload en silencio.** En FastAPI, un
  `response_model` **filtra** los campos que no declara: si el modelo se queda
  corto respecto a lo que hoy devuelve el endpoint, el cliente deja de recibir
  datos sin que falle nada. El índice lo autoriza solo tras caracterizar y
  conservar la respuesta; si la equivalencia no se puede demostrar, **no se
  añade**. Es el riesgo propio y nuevo de esta capa.
- **El dominio no está inspeccionado.** Todo lo que esta bitácora dice de
  dashboard son supuestos heredados marcados como tales. Un riesgo copiado de un
  documento anterior no es evidencia; 7.0 los comprueba o los refuta.
- **Si dashboard resulta escribir archivos o filas**, el perfil de riesgo cambia
  por completo y esta bitácora debe actualizarse antes de cualquier extracción.
  Hoy nadie lo ha comprobado.
- **Los cálculos son el contrato.** En un panel de estadísticas, el resultado
  observable no es solo la forma del payload sino la cifra: un redondeo, un
  `TRUNC` frente a un `ROUND`, un `COALESCE` o un `AVG` de promedios cambian el
  número que ve el usuario sin romper ninguna estructura. La capa 6 ya encontró
  que el promedio general de estudiantes es el promedio de los promedios
  redondeado en Python —4,5 y 3,0 dan 3,8—, y que dashboard usa **otra fórmula
  distinta** para lo suyo. La caracterización debe fijar cifras, no formas.
- **Dashboard probablemente lee tablas de dominios que esta capa no puede
  tocar.** Si es así, se aplica el criterio ya usado en 5.2 y 6.2: decidir con
  evidencia dónde vive cada lectura y **no crear un repositorio nuevo que
  tendría un solo consumidor real**.
- Los contratos de lectura financieros de la capa 4 dependen de `cobros.py`.
  Pueden romperse desde aquí sin que fallen las pruebas del dominio que se está
  tocando. La mitigación es verificar sus conteos y payloads en cada subcapa.
- Los permisos no son uniformes en el sistema: intervienen roles distintos de
  `admin`. Un inventario incompleto de roles es un riesgo de seguridad, no de
  calidad.
- Heredado de la capa 1: `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrar contra
  volumen representativo y el deadline HTTP/proxy externo.
- Heredado de la capa 0: no hay evidencia de GitHub Actions posterior a esa
  capa. Las verificaciones locales no se presentarán como CI remota.
- Heredado de la capa 2: `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` se quedó
  sin ejemplo real que la respalde y se conserva como margen. Si esta capa
  encontrara un camino que anida conexiones, es evidencia relevante y debe
  registrarse, no actuarse.
- Heredado de la capa 4: la credencial privilegiada compartida en chat sigue
  **sin rotar** y no debe reutilizarse.
- Heredado de las capas 5 y 6: sus hallazgos abiertos siguen vivos, incluida la
  ausencia de lock en el alta y la edición de asignaciones, que es el riesgo más
  directo del backend hoy. **No se corrigen desde aquí.**
- **El commit base ya está desplegado**, como en las capas 5 y 6. Un push a
  `main` en este repositorio dispara el despliegue, así que la publicación de
  esta capa afectará a producción en cuanto ocurra.

## Registro de ejecución

### 2026-08-17 — activación de la capa

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local.
- Autorización: orden explícita del usuario en este turno, con el texto
  preparado en `PROMPT_CONTINUACION.md` para la capa 7. Su condición de
  caducidad se comprobó y **se cumplía**: el índice seguía marcando que no
  existe capa activa y que la capa 7 está en espera.
- **Marcador sin rellenar, detectado y no resuelto por inferencia**: la
  autorización llegó con `DOMINIO` literal. Se detuvo el trabajo, se explicó al
  usuario qué es un dominio y por qué esta capa obliga a nombrar uno, y el
  usuario eligió **dashboard**. Solo entonces se activó.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía; `HEAD` real
  `123637ee80895023ecece9c32df526ef4eddd1e5`, comprobado y no recordado.
- Continuidad: el base de la capa 6,
  `589cb6d1391161c692a6f24aee9d523317cbb1ce`, existe y es ancestro de `HEAD`,
  verificado con `git merge-base --is-ancestor`. Sus **ocho** commits
  posteriores forman una historia lineal y **todos están explicados**: siete son
  la capa 6 —`2881b03`, `9e9b4dc`, `69c0033`, `c477516`, `be725c8`, `d04a455` y
  el cierre `bf075a0`—, registrados uno a uno en
  `06_ASIGNACIONES_ESTUDIANTES.md`; el octavo, `123637e`, es documental —tres
  archivos de `docs/modularizacion/`, +191/−31— y su contenido está registrado
  en la corrección del estado de publicación que conserva esa misma bitácora y
  en el índice.
- Estado remoto **comprobado, no supuesto**: `origin/main` está en
  `123637ee80895023ecece9c32df526ef4eddd1e5`, el mismo commit que `HEAD`. El
  reflog registra `update by push` de `123637e` y, antes, de `bf075a0`. La capa
  6 **está publicada y desplegada**, y también lo está el commit documental
  posterior. **No se consultó ni se atribuye ningún run de GitHub Actions**; esa
  evidencia sigue sin obtenerse desde la capa 0.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  dashboard** ni de ningún otro dominio.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --show-toplevel`,
  `git branch --show-current`, `git status`, `git status --porcelain=v1`,
  `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git merge-base --is-ancestor`, `git log --reverse --oneline` desde el base de
  la capa 6, `git show --stat 123637e` y `git reflog show origin/main`; todos
  con resultado coherente con la activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  dashboard; 7.0 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto de
  arriba y detenerse antes de 7.1. *(Ejecutada en el turno siguiente; ver el
  cierre de 7.0 más abajo.)*

### 2026-08-17 — cierre de 7.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `fb303d58ae459e5da862211a9cef08d93dfb5058`. Entre la activación y este turno
  el usuario **commiteó** el trabajo documental: ese commit es exactamente la
  activación, dos archivos de `docs/modularizacion/`, y está explicado en esta
  bitácora. El commit base `123637e` existe y es ancestro; `origin/main` sigue
  en el base, así que hay **un commit local por delante, sin publicar**.
- Compuerta heredada reproducida antes de tocar nada: **714 pruebas, exit 0**,
  Ruff correcto y `pip check` íntegro. Coincide con lo registrado al cerrar la
  capa 6.
- Inventario dirigido: `app/routes/dashboard.py`,
  `app/controllers/dashboard_controller.py`, `tests/test_dashboard_routes.py` y
  `tests/test_dashboard_controlador.py`. Se leyeron además, **solo para resolver
  los supuestos y medir, sin modificarlos**, `app/core/permissions.py`,
  `app/services/asignacion_academica.py`, `app/db/session.py`, el registro del
  router en `app/main.py` y el listado de `app/repositories/`. No se leyó
  historia global ni código de otros dominios de la capa 7.
- Frontera comprobada: `app/routes/cartera.py` y
  `app/controllers/cartera_mora_controller.py` mencionan «dashboard» **solo en
  sus docstrings**. Son de cartera y mora, dominio financiero cuyos conteos fijó
  la capa 4; **no entran** en esta capa.
- **Los siete supuestos que la activación registró sin verificar quedaron
  resueltos**: seis confirmados y **uno refutado**, el de los cálculos más
  caros, que no es un N+1. La tabla de supuestos quedó corregida con el
  resultado de cada uno.
- Caracterización añadida: `tests/test_dashboard_caracterizacion.py`, **41
  casos** en cinco bloques —guardias estructurales, cumpleaños, precondiciones
  de permiso, conteos y contrato de cálculo—. Código de producto y configuración
  modificados: **ninguno**.
- Las 41 pruebas se escribieron contra el código actual y **pasaron todas en su
  primera ejecución**. Se comprobó aparte que las guardias no pasan en vacío: el
  extractor de literales ve **50 cadenas en el controlador, 10 de ellas con
  `SELECT`**, y **18 en la ruta, ninguna con SQL**, que es justo lo que la
  guardia de 6.5 exige.
- Pruebas específicas: **77 pasaron** en 0,64 s sobre los tres archivos del
  dominio. La prueba nueva aislada: 41 pasaron en 0,58 s. Ruff del archivo
  nuevo: **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **755 pruebas pasaron** en 2,48 s, 5 warnings heredadas, Ruff correcto,
  `pip check` sin dependencias rotas, exit 0. La suite pasó de 714 a 755.
- Medición: hermética, con dobles de cursor y conexión, y **a través de la
  ruta** para capturar las conexiones que abren las precondiciones de permiso.
  Los conteos de ocho caminos quedan **fijados por aserciones**, no anotados en
  prosa.
- Diff final: `git diff --check` en exit 0. El alcance es **un solo archivo
  nuevo** y **ningún archivo rastreado modificado**: no se tocó producto, rutas,
  payloads, status codes, permisos, tenant, ownership, SQL, transacciones,
  configuración ni dependencias.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 7.0 **cerrada**; 7.1 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 7.1, la extracción de la
  persistencia a `dashboard_repository`, y detenerse antes de decidir 7.2.

## Entrega al próximo chat

- Capa activa: **7, dashboard**, y solo ese dominio. Activada el 2026-08-17.
- Última subcapa terminada: **7.0**, cerrada el 2026-08-17.
- Primera subcapa pendiente: **7.1**, extracción de la persistencia a
  `app/repositories/dashboard_repository.py`. **Definida y no iniciada.**
- Commit base: `123637ee80895023ecece9c32df526ef4eddd1e5`, rama `main`,
  **publicado y desplegado**. Al cerrar 7.0, `HEAD` es `fb303d5` —un commit
  local por delante de `origin/main`, la activación, **sin publicar**— más el
  archivo de prueba de 7.0 sin commitear.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas**: valor
  operativo final de `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub
  Actions posterior a la capa 0. La credencial privilegiada de la capa 4 sigue
  **sin rotar**.
- Lo que 7.0 dejó medido: **7 entradas HTTP**, todas `GET` y todas de **solo
  lectura**; **cero tablas escritas** y **cero transacciones propias**; **8
  sentencias SQL inline** en el controlador y **ninguna** en la ruta; **41
  pruebas de caracterización** nuevas y los conteos de ocho caminos. El más caro
  cuesta **6 consultas y 4 conexiones**. **No hay N+1.**
- **Lo que la activación creía y resultó falso**: que dashboard concentraba
  «varias consultas de promedios por estudiante». Cada panel se resuelve con
  **una sola consulta agregada**. Lo caro son las **conexiones**, no las
  consultas.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** La capa 7 es «uno a la vez»; los demás necesitan su
     propia bitácora y su propia orden.
  2. **No corregir los diez hallazgos de 7.0**, y menos el primero: las dos
     precondiciones de permiso ignoran `activo`, así que un profesor con la
     asignación desactivada conserva el acceso. **Cambiarlo es cambiar
     permisos.**
  3. **No cambiar el ciclo de vida de las conexiones.** Cuatro funciones siguen
     con `get_connection()` y `try/finally`; convertirlas es trabajo de la capa
     1 y no está autorizado aquí.
  4. **Dos de las ocho consultas se componen de fragmentos**, no son un literal
     único. Es el punto delicado de 7.1.
  5. **`response_model` filtra campos.** Solo después de caracterizar y
     demostrando que la respuesta se conserva.
  6. **En un panel, la cifra es el contrato.** Este dominio usa **dos** fórmulas
     de promedio distintas, y el sistema una tercera en estudiantes.
- Siguiente acción exacta: ejecutar únicamente **7.1** conforme a su trabajo
  exacto y detenerse antes de decidir 7.2. No inspeccionar los demás dominios de
  la capa 7.
