# Capa 7: dashboard

Última revisión: 2026-08-25.

## Control

- Estado: **Cerrada** el 2026-08-19, con sus dos subcapas **7.0 y 7.1**
  completas y la **verificación manual ejecutada por el usuario con resultado
  correcto**. Activada el 2026-08-17.
- Correcciones puntuales posteriores al cierre: el 2026-08-25 el usuario
  autorizó primero exigir `asignaciones.activo = TRUE` en las dos
  precondiciones de rendimiento, después reducir las conexiones seriales y por
  último reutilizar la resolución académica. Las dos primeras quedaron
  publicadas en `9f19089` y `1f1ffc9`; la tercera permanece local. La capa sigue
  **Cerrada**, sin subcapa activa, y quedan **siete
  hallazgos abiertos**.
- Commit base: `123637ee80895023ecece9c32df526ef4eddd1e5`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **ninguna definida**. Las subcapas **7.0 y 7.1**
  quedaron **cerradas** el 2026-08-17. Lo que sigue exige una **decisión del
  usuario**: cerrar la capa como refactorización pura, o abrir una 7.2 para
  `response_model` y errores de dominio. Ver «Punto de decisión abierto».
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
| 7.1 | Extraer la persistencia a `dashboard_repository` sin cambiar SQL, conteos ni ciclo de vida | **Cerrada** |
| 7.2 | `response_model` y errores de dominio, **si el usuario los autoriza** | **Sin decidir**: es un punto de decisión, no una subcapa pendiente |

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

## Hallazgos de 7.0 y estado posterior

7.0 registró **diez** sin corregir ninguno. Las tres correcciones puntuales
autorizadas el 2026-08-25 resolvieron los tres primeros; **siete siguen
abiertos**. El texto conserva la línea base histórica y añade el estado vigente.

**Hay además un hallazgo undécimo, que no venía de 7.0: lo introdujeron las
propias correcciones.** Está al final de la lista, marcado como tal.

**Y el 2026-08-25 uno de los siete heredados —las dos definiciones de
promedio— quedó refutado en su parte central** al ir a corregirlo, y **sustituido
por dos divergencias que sí están demostradas**. El recuento vigente de
hallazgos abiertos es por tanto **nueve**: **seis** heredados de 7.0 que siguen
intactos, las **dos** divergencias que sustituyen al refutado, y el
**undécimo**.

**Actualizado ese mismo día**: corregidas las siete entradas que absorbían
`Exception`, el recuento baja a **ocho** abiertos —cinco heredados intactos, las
dos divergencias y el undécimo—, con **cuatro** de los diez originales
resueltos.

- **CORREGIDO Y PUBLICADO EN `9f19089` EL 2026-08-25 — las dos precondiciones de permiso
  ignoraban el estado `activo`.** Era el hallazgo más importante de 7.0 porque
  **toca permisos**.
  `profesor_tiene_curso_controller` y
  `profesor_tiene_asignacion_en_curso_controller` consultaban `asignaciones` sin
  `activo = TRUE`, así que **un profesor cuya asignación fue desactivada
  conservaba el acceso** al rendimiento de ese curso. La incoherencia era interna:
  la consulta de cumpleaños **del mismo controlador** sí exige `a.activo = TRUE`,
  y la capa 6 dejó registrado que desactivar es precisamente como este sistema
  «borra». **Estado vigente:** las dos consultas testigo conservan sus
  parámetros y añaden `AND activo = TRUE`; si no existe una asignación activa,
  las rutas conservan sus respuestas 403 ya caracterizadas.
- **CORREGIDO Y PUBLICADO EN `1f1ffc9` EL 2026-08-25 — hasta cuatro conexiones por petición,
  en serie.** El camino de notas con asignación abría cuatro conexiones
  sucesivas: una por cada precondición y una para la consulta. **No había
  anidamiento**, por lo que no contradecía
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2`. **Estado vigente:** las tres
  precondiciones comparten una conexión y la lectura final conserva otra; el
  máximo baja de **4 a 2** sin cambiar las **6 consultas** del profesor ni las
  **5 del admin**.
- **CORREGIDO LOCALMENTE EL 2026-08-25 — la asignación académica se resolvía dos
  veces** en ese mismo camino, con el mismo `asignacion_id`: una en la
  precondición de pertenencia y otra dentro del controlador. **Estado vigente:**
  la validación devuelve el ID académico ya resuelto y la lectura final lo
  reutiliza. El profesor baja de **6 a 5 consultas** y el admin de **5 a 4**;
  ambos conservan dos conexiones.
- **Dos definiciones distintas de «promedio» en el mismo panel.** Notas altas y
  bajas promedian **los promedios por clase**, `TRUNC(AVG(promedio_clase), 2)`;
  los rankings promedian **las notas planas**,
  `TRUNC(AVG(CAST(n.nota AS numeric)), 2)`. Con 4,0 en una clase de dos notas y
  2,0 en otra de seis, la primera fórmula da **3,00** y la segunda **2,50**: el
  mismo estudiante aparece aprobado en un panel y en rojo en el otro. Y la capa
  6 ya registró una **tercera** en estudiantes, `ROUND(..., 1)`. Ninguna es un
  error; son contratos distintos que hoy nadie declara.

  > **REVISADO EL 2026-08-25: el párrafo anterior está equivocado en su parte
  > central y se conserva porque es lo que 7.0 registró.** Al ir a corregirlo se
  > comprobó que **las dos fórmulas nunca se aplican al mismo ámbito**, así que
  > no se contradicen:
  >
  > - los rankings filtran `n.asignacion_id = %s`, es decir **una sola
  >   asignatura a la vez**. Dentro de una sola asignatura, promedio de
  >   promedios y promedio plano son **matemáticamente idénticos**, porque el
  >   `AVG` exterior recorre un único grupo y `promedio_clase` **no se trunca**
  >   antes de entrar en él. Comprobado con tres juegos de notas: 3 y 3, 3 y 3,
  >   3,47 y 3,47;
  > - la divergencia 3,00 frente a 2,50 **exige dos asignaturas o más**, y en
  >   ese caso **la aplicación nunca calcula el 2,50**: no existe ninguna
  >   consulta que promedie notas planas cruzando asignaturas. Con el ejemplo
  >   del párrafo, los rankings mostrarían **4,00** y **2,00**, cada uno en su
  >   asignatura, nunca 2,50;
  > - que un estudiante salga aprobado en notas altas y en rojo en un ranking
  >   **sí ocurre**, pero porque los dos paneles **miden cosas distintas** —el
  >   conjunto de sus asignaturas frente a una asignatura concreta—, no por la
  >   fórmula. Eso es esperable, no un defecto.
  >
  > Además, el promedio de promedios **es el criterio correcto** para el
  > agregado multi-asignatura y **coincide con el del boletín**, que 7.0 de
  > `notas` registró como «el promedio de los promedios». Cambiarlo a plano
  > sería una **regresión**: haría que una asignatura con más notas pesara más
  > que otra con menos.
  >
  > **Lo que sí quedó demostrado son otras dos divergencias**, y son las que
  > importan; ver los dos puntos siguientes.

- **Divergencia real 1: `TRUNC(…, 2)` frente a `ROUND(…, 1)` para la misma
  cifra.** El expediente del estudiante calcula el promedio por materia con
  `ROUND(AVG(n.nota), 1)` en `estudiantes_repository.leer_promedios_por_materia`
  y el dashboard con `TRUNC(…, 2)`. **Aquí el ámbito sí es el mismo** —un
  estudiante en una materia—, así que las dos cifras son directamente
  comparables y **discrepan**. Cuatro ejemplos comprobados, todos con el corte
  en 3,0: notas 2,9/3,0/3,0 dan **3,0** en el expediente y **2,96** en el
  dashboard; 2,95/2,95 dan **3,0** y **2,95**; 3,0/2,9 dan **3,0** y **2,95**;
  2,5/3,4 dan **3,0** y **2,95**. En los cuatro casos el estudiante aparece
  **aprobado en el expediente y en rojo en el dashboard**. Es el efecto que el
  párrafo original describía, pero por el **redondeo**, no por el promedio de
  promedios. Corregirlo **cruza a `estudiantes`, un dominio ya migrado**, y
  exige decidir cuál de las dos es el contrato.

  **DECISIÓN DEL USUARIO EL 2026-08-25: dejar las dos como están**, registrando
  la divergencia sin corregirla. Se le presentaron las cuatro salidas —adoptar
  `TRUNC(…, 2)`, adoptar `ROUND(…, 1)`, consultar antes la regla académica real
  del colegio, o no tocar nada— y eligió no tocar nada. **Queda vigente que la
  misma nota se vea aprobada en el expediente y en rojo en el dashboard.** Es el
  mismo criterio que la capa 6 aplicó a su código muerto y que el hallazgo 11
  acaba de recibir: se registra, no se corrige. Cambiarlo exigiría una orden
  explícita, y además **una decisión previa sobre cuál es la regla académica**,
  que no es técnica.

- **Divergencia real 2: notas altas y bajas no filtran por `periodo` y los
  rankings sí.** `leer_estudiantes_por_promedio` **no tiene filtro de periodo**,
  así que mezcla todo el año; `leer_ranking_bajo_rendimiento` y su gemela
  filtran `n.periodo = %s`. En el mismo panel conviven una cifra anual y una
  cifra por periodo sin que nada lo indique. Es la misma familia que el hallazgo
  de `periodo` que 7.0 de `notas` registró en su dominio.

  **DECISIÓN DEL USUARIO EL 2026-08-25: dejarlo registrado, sin corregir.**
  Añadir el filtro cambiaría la cifra que el panel muestra hoy —pasaría de anual
  a por periodo— y obligaría a decidir **qué periodo por defecto** y si la ruta
  lo acepta como parámetro. Es una decisión propia, separada de la del redondeo,
  y no se toma por inferencia.
- **CORREGIDO LOCALMENTE EL 2026-08-25 — las siete entradas absorbían
  `Exception` y respondían 400 con `str(e)`.** Un fallo de infraestructura se
  presentaba como error del cliente **y el texto de la excepción viajaba en el
  `detail`**, así que un error de PostgreSQL podía llegar al navegador. Era la
  misma familia que el hallazgo de la capa 5 en `tipos_pagos_controller`, pero
  aquí **no se registraba nada en el log** y además **se devolvía el mensaje
  interno**.

  **Estado vigente:** las siete responden **500** con una constante única,
  `_ERROR_INTERNO_DASHBOARD`, y registran el fallo con `logger.exception`, que
  conserva el traceback. **El texto de la excepción ya no sale del servidor.**
  Los demás status codes no se tocan: el 422 por curso ausente, los dos 403 del
  filtro y los de permisos siguen exactamente igual, porque se lanzan **fuera**
  del `try`.

  **Decisión: no se introdujo una excepción de dominio**, a diferencia de
  `tipos_pagos`, que sí definió `TipoPagoInfraestructuraError`. Allí hacía falta
  **distinguir** un fallo de infraestructura de errores de negocio que debían
  conservar su 409 o su 400. Aquí no hay nada de lo que distinguirla: dashboard
  es de **solo lectura**, sus controladores no lanzan errores de negocio y todo
  lo que cae en esos siete `except` es infraestructura. Crear la clase habría
  sido una abstracción con **un solo uso**, que el índice prohíbe.
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

### Hallazgo 11, **introducido por las propias correcciones** el 2026-08-25

- **`profesor_tiene_curso_controller` y
  `profesor_tiene_asignacion_en_curso_controller` quedaron sin ningún consumidor
  en producción.** No venía de 7.0: en el commit base de la capa,
  `123637ee80895023ecece9c32df526ef4eddd1e5`, las **dos estaban vivas** y
  `app/routes/dashboard.py` las importaba y las llamaba. La corrección del
  hallazgo 2 —la reducción de conexiones, **publicada en `1f1ffc9`**— absorbió
  su lógica dentro de `validar_filtro_rendimiento_profesor_controller`, y desde
  entonces **ningún código de `app/` las invoca**: solo las mantienen vivas
  cuatro pruebas de `tests/test_dashboard_caracterizacion.py`.

  Lo que agrava el detalle es que **cada una sigue abriendo su propia
  conexión** con `get_connection()`, que es exactamente el recurso que aquella
  corrección buscaba ahorrar. No hay consecuencia funcional —no se ejecutan en
  ningún camino HTTP—, pero **es código muerto que ya está publicado y
  desplegado**, y hasta hoy **no constaba en ninguna parte**.

  **Detectado el 2026-08-25**, al auditar qué faltaba del hallazgo 3. **Decisión
  del usuario ese mismo día: registrarlo sin retirar nada**, para que las
  correcciones puntuales sigan siendo cambios de comportamiento y no arrastren
  borrados de producto. Es el mismo criterio que la capa 6 aplicó al código
  muerto duplicado de `obtener_clases_profesor_controller`, que también se
  conservó por decisión explícita.

  Retirarlas —y con ellas las cuatro pruebas que solo existen para sostenerlas—
  queda como **trabajo disponible que exigiría una orden explícita**. No debe
  hacerse por inferencia ni «de paso» en otra corrección.

- **Matiz relacionado, este sí deliberado y ya documentado**: el fallback de
  `_obtener_notas_profesor`, que resuelve el ID académico cuando nadie se lo
  suministra, **tampoco tiene consumidor en el camino HTTP**, porque la ruta
  siempre entrega el valor ya validado. Se conserva a propósito para los
  llamadores directos y no se cuenta como hallazgo.

## Subcapa 7.1 — trabajo exacto, ejecutado y cerrado

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

## Resultado de 7.1

Las **8 sentencias** salieron del controlador a
`app/repositories/dashboard_repository.py`, **ocho funciones** que reciben el
cursor existente más los **dos fragmentos** que componen las consultas de
cumpleaños. El controlador pasó de **336 a 146 líneas** y de **8 sentencias SQL
inline a 0**; la ruta seguía teniendo 0. Conserva conexión, cursor, `try/finally`,
la resolución de la asignación académica, la normalización de `dias`, el formateo
del payload y el color de cada fila.

El comparador AST **contra el commit base de la capa**, `123637e`, confirmó **16
literales SQL distintos antes y 16 después, conjunto idéntico**, ninguno perdido
y ninguno nuevo, con **16 de 16 conservados byte a byte**, y **8 puntos de
llamada antes y después**. **No hizo falta autorizar ningún cambio de texto
SQL**, igual que en toda la capa 6.

**Ninguna prueba cambió de expectativa salvo las dos que debían cambiar**: 75 de
las 77 pasaron sin tocarlas, incluidos los ocho conteos de consultas y conexiones
y todas las aserciones sobre el texto del SQL.

## Punto de decisión, resuelto el 2026-08-17

**La frontera de persistencia de dashboard ya está cerrada**: el controlador no
tiene SQL, la ruta tampoco y el repositorio existe. Lo que queda del objetivo que
el índice fijó para la capa 7 es la parte condicional: «agregar `response_model`,
errores de dominio y pruebas HTTP o de integración **solo después de caracterizar
y conservar la respuesta existente**».

Esa parte **no se inicia por inferencia**, por dos razones registradas:

1. `response_model` **filtra** en FastAPI los campos que no declara. Las siete
   entradas devuelven hoy listas de diccionarios construidos a mano; declarar un
   modelo que se quede corto **recortaría el payload sin que fallara nada**. Es
   el riesgo propio de esta capa, anotado desde la activación.
2. Las capas 5 y 6 cerraron siendo **refactorizaciones puras**. Añadir
   `response_model` haría de la 7 la primera que toca la superficie del contrato,
   aunque sea para conservarla. Eso es una decisión del usuario.

Las dos salidas eran legítimas:

- **cerrar la capa aquí**, como refactorización pura, con su compuerta global,
  staging, rollback y verificación manual; o
- **abrir 7.2** para añadir `response_model` y errores de dominio sobre la
  caracterización que ya existe, demostrando payload por payload que la respuesta
  no cambia.

**El usuario eligió cerrar la capa aquí**, el 2026-08-17 y de forma explícita.
Consecuencias registradas, ninguna de ellas una deuda oculta:

- La capa 7 para `dashboard` es, como la 5 y la 6, **exclusivamente una
  refactorización**. Ningún contrato observable cambió.
- **`response_model` y los errores de dominio no se añaden.** No quedan como
  trabajo pendiente de esta capa: quedan registrados como trabajo disponible que
  exigiría una orden explícita, igual que el resto de hallazgos abiertos.
- **Al cerrarse el 2026-08-17**, los diez hallazgos de 7.0 seguían vivos y sin
  corregir, incluido el primero, que las dos precondiciones de permiso ignoraban
  `activo`. El 2026-08-25 una orden posterior resolvió ese primero; nueve siguen
  abiertos.

## Staging, rollback y verificación manual de la capa 7

### Lo que esta capa hizo y no hizo

La capa 7 para `dashboard` es **exclusivamente una refactorización**, igual que
la 5 y la 6. No añadió funciones, no cambió reglas, no tocó rutas, payloads,
status codes, permisos, tenant, ownership, transacciones, timeouts, dependencias
ni configuración. Y **no abrió una sola conexión a PostgreSQL**: ni migraciones,
ni DDL, ni DML, ni lecturas de medición. Toda la caracterización se hizo con
dobles.

La evidencia de que el comportamiento observable no cambió es doble:

1. un comparador AST contra el commit base `123637e` demuestra que los **16
   literales SQL distintos son los mismos**, ninguno perdido y ninguno nuevo, con
   **16 de 16 byte a byte**, y que hay **8 puntos de llamada antes y después**.
   **No hizo falta autorizar ni un solo cambio de texto SQL**, como en la capa 6
   y a diferencia de la 5, que necesitó dos;
2. **42 pruebas de caracterización** fijan payloads, permisos por rol, conteos de
   consultas **y de conexiones**, ciclo de vida y fórmulas de cálculo. **Ninguna
   cambió de expectativa**; las dos únicas que fallaron fueron las guardias que
   7.0 dejó *deliberadamente* sobre la línea base previa a la extracción, y que
   debían fallar cuando 7.1 la moviera.

### Rollback

**Es puramente de código.** No hay nada que deshacer en datos ni en esquema.
Revertir los commits de la capa hasta
`123637ee80895023ecece9c32df526ef4eddd1e5` devuelve el controlador a su versión
anterior y elimina el repositorio nuevo. Como el SQL ejecutado es equivalente,
revertir no cambia el comportamiento observable.

Ese commit base **ya está publicado y desplegado**, así que revertir exigiría un
push y un despliegue, no una operación local. Es la misma situación que dejó la
capa 6.

No cambiar los timeouts durante el rollback.

### Staging

No se usó un entorno de staging y **no se considera necesario** para esta capa,
por la misma razón que hace trivial el rollback: no hay cambio de esquema, de
datos ni de SQL. Un despliegue prudente solo necesita comprobar que la
aplicación arranca y que los siete paneles responden, que es lo que cubre la
verificación manual.

### Verificación manual: **hecha y correcta**

Es la única evidencia que no puede delegarse en un asistente, porque exige
reconocer datos reales. En un panel de estadísticas eso es más cierto que en
ningún otro dominio: **la cifra es el contrato**, y solo quien conoce el colegio
sabe si un promedio cuadra.

**Ejecutada por el usuario el 2026-08-19, en local, con resultado correcto y
cobertura completa del guion.**

**Artefacto verificado**: se confirmó expresamente **antes** de registrarla,
conforme a la lección 10 de la capa 5. A diferencia de la capa 6, aquí **no había
ambigüedad**: el árbol estaba limpio y `HEAD` coincidía con `origin/main` en
`8591816`, así que el código ejercitado en local y el publicado son **el mismo
commit**, y ese commit contiene la capa entera.

**Limitación registrada, no disimulada**: la verificación fue **en local**. Que
el commit sea el mismo que corre en producción no la convierte en una
verificación del despliegue: no ejercita el endpoint agrupado de Neon, los
timeouts reales, el proxy ni la latencia. Nadie ha repetido el guion contra el
despliegue. Es aceptable aquí por lo que la capa es —una refactorización con SQL
equivalente demostrado y sin ningún acceso a la base de datos—; no lo sería en
una capa que cambiara comportamiento o tocara datos.

Guion ejecutado:

- **Cumpleaños, como admin**: abrir el panel y comprobar que salen los de los
  próximos 7 días, en orden de fecha; cambiar el rango de días y comprobar que la
  lista crece o se reduce. Comprobar que **aparece un estudiante sin curso**, si
  lo hay: el panel de admin los incluye a propósito.
- **Cumpleaños, como profesor**: comprobar que solo salen los estudiantes de sus
  **cursos activos**, y que un estudiante retirado **no** aparece.
- **Inasistencias**: entrar como profesor y comprobar que salen **como mucho tres
  estudiantes por curso**, los de más faltas, y que las cifras cuadran con las
  ausencias reales.
- **Notas altas y bajas**: elegir un curso propio y comprobar que salen **como
  mucho cinco**, con sus colores —verde arriba, rojo o amarillo abajo—; intentar
  **sin elegir curso** y comprobar el aviso; intentar un curso **de otro
  profesor** y comprobar que se rechaza.
- **Rankings**: abrir el ranking de una asignación propia por periodo y comprobar
  que los promedios cuadran y el orden es el correcto en los dos sentidos;
  comprobar que un profesor **no** puede abrir el de otro.
- **Lo más importante, las cifras**: contrastar un promedio del panel con las
  notas reales de ese estudiante. Y tener presente el hallazgo de 7.0: **notas
  altas/bajas y los rankings no calculan el promedio igual**, así que pueden
  discrepar entre sí **desde antes de esta capa**. Si discrepan, no es la
  refactorización: es el hallazgo, ya registrado.
- Comprobar todo en **los dos tenants**, sin mezclar datos.

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

Estado de los ocho criterios al 2026-08-17:

| Criterio | Estado |
|---|---|
| Subcapas cerradas o `No aplica` | **Cumplido**: 7.0 y 7.1 cerradas; no hubo más |
| Dominio migrado sin arrastrar otros | **Cumplido**: el diff no toca ningún otro dominio |
| `response_model` solo tras caracterizar | **No aplica**: el usuario decidió no añadirlo |
| Ninguna abstracción sin dos consumidores | **Cumplido**: el repositorio por módulo es la convención de `app/repositories/README.md`, con cuatro precedentes |
| Contratos del frontend y de la base intactos | **Cumplido**: comparador AST 16 de 16 y 42 pruebas sin cambio de expectativa |
| Compuerta, Ruff, dependencias y `git diff --check` | **Cumplido**: 756 pruebas, exit 0 |
| Staging, rollback y verificación manual documentados | **Cumplido** el documentarlos; el rollback **no** necesita cubrir archivos porque 7.0 demostró que el dominio no los escribe |
| Índice actualizado y ningún dominio activado | **Cumplido** |

**Los ocho criterios quedan resueltos.** La verificación manual, que era lo
único que faltaba, la ejecutó el usuario el 2026-08-19 con resultado correcto.

## Cierre de la capa 7 para `dashboard`

### Resultado frente a su objetivo

El índice le pedía migrar el dominio con contratos y pruebas, priorizando uno a
la vez, añadiendo `response_model` y errores de dominio **solo después** de
caracterizar y conservar la respuesta, y sin crear abstracciones compartidas sin
dos consumidores reales.

| Objetivo | Resultado |
|---|---|
| Migrar el dominio con contratos y pruebas | `dashboard_controller.py` pasó de **336 a 146 líneas** y de **8 sentencias SQL inline a 0**; la persistencia vive en `dashboard_repository`, **ocho funciones** que reciben el cursor más dos fragmentos. **42 pruebas de caracterización** nuevas fijan payloads, permisos por rol, conteos de consultas **y de conexiones**, ciclo de vida y fórmulas de cálculo |
| Un dominio a la vez | **Cumplido**: el diff no toca ningún otro dominio. Los demás siguen en espera, cada uno con su propia bitácora pendiente |
| `response_model` solo tras caracterizar | **No se añadió**, por decisión explícita del usuario. No queda como deuda de la capa: es trabajo disponible que exigiría una orden |
| Sin abstracciones sin dos consumidores | **Cumplido**: el repositorio por módulo es la convención de `app/repositories/README.md`, con cuatro precedentes |

La suite pasó de **714 a 756** pruebas. Compuerta de cierre: **exit 0 con 756
pruebas**, Ruff correcto y `pip check` íntegro.

### Lo que esta capa NO hizo

- **No tocó la base de datos**, ni siquiera para leer. Es la tercera capa
  consecutiva que no abre una sola conexión a PostgreSQL, después de la 5 y la 6.
- **No tocó archivos.** 7.0 lo demostró con prueba: solo branding y plan de
  clases usan `storage`.
- No cambió rutas, payloads, status codes, permisos, tenant, ownership,
  transacciones, timeouts, dependencias ni configuración.
- Durante 7.0 y 7.1 **no corrigió ninguno de los diez hallazgos**. La corrección
  puntual del 2026-08-25 resolvió después los tres primeros; **siete siguen
  vivos**.
- **No necesitó autorizar ni un solo cambio de texto SQL**, como la capa 6.

### Estado de publicación

**Publicada y desplegada.** El reflog de `origin/main` registra `update by push`
de `8591816`, que arrastra los **cuatro** commits de la capa —`fb303d5`,
`59efda6`, `c75a5b7` y `8591816`—. Como un push a `main` dispara el despliegue,
**producción ya corre este código**, y el rollback a `123637e` exigiría otro push
y otro despliegue.

Las líneas fechadas del registro de ejecución que dicen «sin publicar» describen
el estado de su momento y **se conservan intactas**: eran ciertas entonces.

### Riesgos que la capa deja abiertos

- ~~**Las dos precondiciones de permiso ignoran `activo`.**~~ **Corregido
  y publicado en `9f19089` el 2026-08-25**: ambas exigen ahora `activo = TRUE`,
  sin cambiar parámetros, conteos de consultas/conexiones ni mensajes 403.
- Las **siete entradas** devuelven 400 con el texto de la excepción, sin
  registrar nada.
- **Dos definiciones distintas de promedio** en el mismo panel, y una tercera en
  estudiantes.
- ~~Hasta **cuatro conexiones por petición** en el camino más caro.~~
  **Corregido y publicado en `1f1ffc9` el 2026-08-25**: el máximo es ahora
  **dos**, sin alterar parámetros ni límites de error.
- ~~La asignación académica se resolvía **dos veces**.~~ **Corregido localmente
  el 2026-08-25**: la lectura reutiliza la resolución de la validación; profesor
  y admin ahorran una consulta.
- Los **cinco hallazgos heredados** de 7.0 que siguen intactos, las **dos
  divergencias** que sustituyeron al del promedio tras refutarlo —el redondeo
  `ROUND(…, 1)` frente a `TRUNC(…, 2)` y el `periodo` ausente—, y el **undécimo
  que introdujeron las propias correcciones**, más `response_model` sin añadir.
  **Ocho abiertos en total**, y el usuario decidió el 2026-08-25 **no corregir
  las dos divergencias nuevas**.
- Heredados: calibración de `DB_STATEMENT_TIMEOUT_MS` de la capa 1, ausencia de
  evidencia de GitHub Actions desde la capa 0, la credencial privilegiada de la
  capa 4 sin rotar, los hallazgos abiertos de las capas 5 y 6 —incluida la clave
  de idempotencia y la ausencia de lock frente a horarios solapados—.

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
- **Las dos consultas de precondición viven en `dashboard_repository`, no en
  `asignaciones_repository`, decidido en 7.1 con evidencia.** Consultan la tabla
  `asignaciones`, que **sí** tiene repositorio propio desde la capa 6, así que el
  criterio de 5.2 y 6.2 —no crear un repositorio con un solo consumidor— no
  decide aquí. Deciden otras tres cosas: **no son duplicados**, porque
  `buscar_asignacion_activa` y `buscar_ultima_asignacion_activa` **filtran por
  `activo` y estas no**; llevarlas allí ampliaría el diff a un módulo que la capa
  6 cerró y haría que dashboard dependa del repositorio de otro dominio; y sobre
  todo, **poner una consulta que no filtra `activo` al lado de sus vecinas que sí
  lo hacen invita a "arreglarla"**, que es exactamente el hallazgo abierto que
  esta capa tiene prohibido corregir. El docstring de las dos funciones lo
  advierte. Alternativa descartada: moverlas a `asignaciones_repository`.
- **Los dos fragmentos SQL viajan con sus consultas.** `_cte_rango_cumpleanos` y
  `_filtro_rango_cumpleanos` no son helpers de formato: son **texto SQL**, así
  que pertenecen al repositorio. Siguen siendo privados y solo los usan las dos
  funciones de cumpleaños. Es el punto que 7.1 había marcado como delicado, y se
  resolvió copiándolos verbatim.
- **La resolución de la asignación académica se queda en el controlador.** El
  repositorio recibe el id **ya resuelto**. Mover la llamada habría cambiado el
  orden de las consultas —que los conteos de 7.0 fijan— y habría metido en el
  repositorio una dependencia de `app/services/asignacion_academica.py`, que esta
  capa tiene prohibido tocar. Es la misma frontera que 6.1 fijó con el filtro de
  estado.
- **El ciclo de vida no se tocó**, como exigía el trabajo exacto de 7.1: las
  cuatro funciones que usaban `get_connection()` con `try/finally` lo siguen
  usando. Unificarlas con `get_cursor()` es trabajo de la capa 1 y habría
  cambiado el número de conexiones, que es justo lo que 7.0 midió.
- **Las dos guardias de línea base se sustituyeron por su versión positiva.**
  `test_el_controlador_conserva_sus_ocho_sentencias` y
  `test_el_dominio_no_tiene_repositorio_propio` **fallaron al extraer**, que era
  la señal esperada: 7.0 las escribió sabiendo que una extracción debía tumbarlas.
  Es la lección 14 de la capa 6, aplicada dos veces. Ahora fijan que el SQL vive
  **solo** en el repositorio y que este es el sexto. Se añadió además una guardia
  de que sus ocho funciones públicas reciben el cursor.
- **Error propio detectado y corregido dentro de la subcapa**: los archivos
  generados quedaron con finales de línea **mezclados**, porque la detección
  inicial fue defectuosa y dio CRLF donde el repositorio usa LF. Se normalizaron
  los tres archivos a LF antes de cerrar, y se repitieron el comparador, las
  pruebas y la compuerta. No afecta al valor de las cadenas —Python normaliza los
  finales de línea del código fuente—, pero habría ensuciado el diff.

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
  *(Ejecutada en el turno siguiente; ver el cierre de 7.1 más abajo.)*

### 2026-08-17 — cierre de 7.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local. **La primera comprobación del turno
  salió del repositorio equivocado** —el shell había vuelto al directorio del
  frontend— y se detectó al ver un `HEAD` que no existe en esta historia; se
  repitió con la ruta explícita antes de tocar nada.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `59efda6f83c877d514eb095cdbd0057b550c2873`, el cierre de 7.0 que el usuario
  commiteó entre turnos y que contiene exactamente los tres archivos que 7.0
  declaró. El commit base `123637e` existe y es ancestro; `origin/main` sigue en
  el base, así que hay **dos commits locales por delante, sin publicar**, ambos
  explicados aquí.
- Alcance inspeccionado y modificado: `dashboard_controller.py` y el repositorio
  nuevo. Se leyeron además, **solo para decidir con evidencia y sin
  modificarlos**, `app/repositories/README.md`, la cabecera y dos funciones de
  `estudiantes_repository` y `asignaciones_repository`, y el estilo de import de
  dos controladores ya migrados. **No se inspeccionó ningún otro dominio.**
- Archivos de producto: `app/controllers/dashboard_controller.py` y el nuevo
  `app/repositories/dashboard_repository.py`. Pruebas modificadas:
  `tests/test_dashboard_caracterizacion.py`, para sustituir las dos guardias de
  línea base por su versión positiva y añadir una tercera.
- Implementación: **ocho funciones** que reciben el cursor existente cubren los
  ocho puntos de llamada, más los **dos fragmentos privados** que componen las
  consultas de cumpleaños. El controlador pasó de **336 a 146 líneas** y **ya no
  contiene SQL**.
- Técnica usada para no alterar el texto: las cadenas **no se transcribieron a
  mano**. Un script copió los rangos de línea exactos del controlador al
  repositorio, así que cada literal viaja con su sangría original aunque el
  código que lo rodea cambie de nivel. Es lo que hace que el comparador dé 16 de
  16.
- Equivalencia SQL verificada con el comparador AST **contra el commit base de la
  capa**, `123637e`, excluyendo docstrings: **16 literales SQL distintos antes y
  16 después, conjunto idéntico**, ninguno perdido y ninguno nuevo, **16 de 16
  byte a byte**, y **8 puntos de llamada antes y después**. Ninguna autorización
  de cambio de SQL fue necesaria.
- **Señales esperadas, producidas y atendidas**: las dos guardias que 7.0 había
  escrito sobre la línea base previa a la extracción —ocho sentencias en el
  controlador y ningún repositorio de dashboard— **fallaron**, y solo esas dos.
  Las otras **75 pruebas pasaron sin cambiar de expectativa**, incluidos los ocho
  conteos de consultas y conexiones y todas las aserciones sobre el texto del
  SQL. Se sustituyeron por versiones positivas.
- Error propio, detectado y corregido dentro de la subcapa: los archivos
  generados quedaron con finales de línea mezclados por una detección defectuosa.
  Se normalizaron a LF y se repitieron comparador, pruebas y compuerta.
- Conteos conservados: los ocho caminos que 7.0 fijó siguen costando lo mismo,
  incluido el de **6 consultas y 4 conexiones**. Los de la capa 4 no se tocan.
- Pruebas específicas: **78 pasaron** en 0,80 s sobre los tres archivos del
  dominio. Ruff del alcance: **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **756 pruebas pasaron**, 5 warnings heredadas, Ruff correcto, `pip check`
  íntegro y exit 0. La suite pasó de 755 a 756 por la guardia añadida.
- Revisión final: `git diff --check` en exit 0. El diff contiene tres archivos:
  dos de producto y la prueba. El del controlador son **21 líneas añadidas** —un
  import y las llamadas al repositorio— y 211 eliminadas. No hubo cambios en
  rutas, payloads, status codes, permisos, tenant, ownership, transacciones,
  timeouts, dependencias ni configuración.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 7.1 **cerrada**. La frontera de persistencia del dominio queda cerrada.
- Siguiente acción exacta: **pedir al usuario la decisión** entre cerrar la capa
  como refactorización pura o abrir 7.2 para `response_model` y errores de
  dominio. No se inicia ninguna de las dos sin orden explícita. *(Respondida en
  el turno siguiente: cerrar. Ver abajo.)*

### 2026-08-17 — preparación del cierre de la capa

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente.
- Decisión del usuario, explícita: **cerrar la capa aquí**, sin abrir 7.2. La
  capa queda siendo una refactorización pura, como la 5 y la 6.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `c75a5b720a751ffb9fcbda10640fd4a9d80d5f21`, el commit de 7.1 que el usuario
  hizo entre turnos. El commit base `123637e` existe y es ancestro, y los **tres**
  commits posteriores están explicados aquí: la activación `fb303d5`, el cierre
  de 7.0 `59efda6` y la extracción de 7.1 `c75a5b7`. `origin/main` sigue en el
  base, así que hay **tres commits locales por delante, sin publicar**.
- **Compuerta global de cierre**: `.\venv\Scripts\python.exe scripts\verify.py`;
  **756 pruebas pasaron**, 5 warnings heredadas, Ruff correcto, `pip check`
  íntegro y exit 0.
- Archivos modificados en este turno: esta bitácora,
  `docs/modularizacion/README.md` y `docs/modularizacion/PROMPT_CONTINUACION.md`.
  **Código de producto y pruebas: ninguno.**
- Se retiró de `PROMPT_CONTINUACION.md` la autorización puntual de la capa 7, ya
  consumida, como se había registrado al activar. Queda preparada una nueva para
  **el siguiente dominio**, con su condición de caducidad y el mismo requisito de
  rellenar el nombre antes de pegarla.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**, ni en
  este turno ni en toda la capa.
- Estado: subcapas 7.0 y 7.1 **cerradas**; **el cierre de la capa queda
  supeditado a la verificación manual**, que el usuario decide si ejecuta o
  acepta como pendiente.
- Siguiente acción exacta: obtener del usuario el resultado de la verificación
  manual o su aceptación explícita como pendiente. Solo entonces marcar la capa
  cerrada. **No activar ningún otro dominio.** *(Obtenido el 2026-08-19; ver el
  cierre más abajo.)*

### 2026-08-19 — cierre de la capa 7 para `dashboard`

Con la verificación manual ejecutada, la capa queda cerrada.

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD` `8591816`, el commit de
  preparación del cierre que el usuario hizo entre turnos. El commit base
  `123637e` existe y es ancestro, y los **cuatro** commits posteriores están
  explicados en esta bitácora.
- **Hecho nuevo detectado en este turno**: el usuario **publicó la capa**.
  `origin/main` está en `8591816` y el reflog lo registra como `update by push`.
  Producción ya corre este código. Se comprobó **antes** de registrar nada, y no
  se dio por supuesto.
- **Verificación manual**: el usuario informó primero «ya ejecuté las pruebas del
  dashboard», una frase que admite dos lecturas —`pytest` o el guion manual—. Se
  preguntó **antes** de registrarla, conforme a la lección 10 de la capa 5, y
  confirmó: **prueba manual del dashboard, en local, cobertura completa y
  resultado correcto**. No se infirió ni el tipo, ni el artefacto, ni el
  resultado.
- Artefacto: sin ambigüedad, a diferencia de la capa 6. Árbol limpio y `HEAD`
  igual a `origin/main`, así que el código ejercitado en local y el desplegado
  son **el mismo commit**. La limitación que queda es de **entorno**, no de
  artefacto: nadie ha repetido el guion contra el despliegue.
- Archivos modificados en este turno: esta bitácora,
  `docs/modularizacion/README.md` y `docs/modularizacion/PROMPT_CONTINUACION.md`.
  **Código de producto y pruebas: ninguno.**
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno por parte
  del asistente**, ni en este turno ni en toda la capa. La publicación la hizo el
  usuario.
- Estado: **capa 7 cerrada para el dominio `dashboard`**. Los demás dominios de
  la capa 7 quedan **en espera** y **ninguno fue activado**.
- Siguiente acción exacta: esperar una orden explícita del usuario. Una
  instrucción genérica de continuar no autoriza activar otro dominio.

## 2026-08-25 — corrección puntual posterior al cierre: asignaciones activas en permisos

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente. El frontend se revisó en solo lectura en su checkout
  local separado.
- Autorización: después de revisar los diez hallazgos, el usuario eligió
  `dashboard` y respondió «sí» a la pregunta explícita de corregir únicamente
  el hallazgo de las precondiciones que ignoraban `activo`. La autorización no
  reactiva la capa ni abre otra subcapa.
- Precondiciones antes de modificar: rama acordada `main`; árbol limpio
  confirmado con `git status --porcelain=v1 --branch`, que mostró solo
  `## main...origin/main`; `HEAD`
  `1ab891208b1bcd3f4f6249ff40457ed3b1e82834`, coincidente con la referencia
  local `origin/main`; y base de continuidad
  `2ec924a3308581b746a61fa24a44f71433034dbc` comprobada como ancestro.
- Continuidad: los once commits posteriores al base quedaron revisados por el
  rango `2ec924a..HEAD`. Los cinco de `super_admin`, las dos correcciones de
  caracterización, las tres correcciones puntuales del 2026-08-24 y la
  consolidación documental final corresponden a los archivos y ejecuciones
  registrados en sus bitácoras; no apareció divergencia sin explicar.
- Hallazgo confirmado: `buscar_curso_de_profesor` y
  `buscar_asignacion_de_profesor_en_curso` aceptaban filas de `asignaciones`
  desactivadas. Afectaba únicamente a
  `GET /dashboard/notas-bajas/{profesor_id}` y
  `GET /dashboard/notas-altas/{profesor_id}`.
- Caracterización antes del cambio: las dos suites propias terminaron con
  **71 passed**. La guardia se invirtió primero para exigir el filtro y produjo
  la señal esperada contra la línea base: **1 failed, 41 deselected**, por la
  ausencia exacta de `AND activo = TRUE`.
- Producto modificado: únicamente
  `app/repositories/dashboard_repository.py`. Se añadió `AND activo = TRUE` a
  las dos consultas testigo y se actualizaron sus docstrings. No cambiaron
  firmas, parámetros, orden, `LIMIT`, recursos ni llamadores.
- Prueba modificada: `tests/test_dashboard_caracterizacion.py`. La antigua
  guardia negativa exige ahora el filtro en ambas consultas y conserva la
  secuencia exacta de parámetros `(7, 4)`, `(12,)`, `(77, 7, 4)`.
- Contrato conservado: sin curso continúa el 422; un curso sin asignación activa
  conserva el 403 «No tienes permisos para consultar este curso»; y una
  asignación que no supera la pertenencia conserva el 403 «La asignación no
  pertenece al curso seleccionado». Las asignaciones activas conservan el
  camino de éxito. Tenant, ownership, payloads y respuestas no cambian.
- Coste conservado: no se añadió ninguna consulta ni conexión. Los caminos
  fijados siguen en 2 consultas/2 conexiones sin asignación, 6/4 con asignación
  como profesor y 5/3 como admin.
- Frontend: no requiere cambio. Sus selectores consumen `/mis-clases`, eliminan
  una selección persistida que ya no aparezca y, ante un 403 obsoleto, vacían
  el rendimiento y muestran el mensaje genérico existente. Un tratamiento UX
  específico para 403/404 sería otro alcance.
- Verificación: la prueba focal quedó en **1 passed**; dashboard, rutas y
  permisos terminaron con **88 passed**; Ruff específico informó
  **All checks passed**. La primera compuerta global dentro del sandbox fue
  inválida: 30 errores de setup por `PermissionError` sobre el directorio
  temporal de pytest, con 1086 pruebas ya pasadas, Ruff y `pip check`
  correctos. La repetición autorizada con acceso válido terminó en **1116
  passed**, 5 warnings heredados, Ruff correcto, `pip check` íntegro y exit 0.
- Revisión de alcance y whitespace: `git diff --check` terminó en exit 0; los
  avisos fueron únicamente de normalización futura LF/CRLF. El diff contiene
  un archivo de producto, una prueba y tres documentos de continuidad, todos
  pertenecientes a esta corrección.
- Riesgo residual, no ampliado: las precondiciones y la lectura final siguen en
  conexiones separadas, por lo que existe una ventana TOCTOU. Además, la
  consulta agregada sin `asignacion_id` no filtra por `asi.activo` y puede
  incluir historial de otra asignación inactiva si el profesor conserva una
  asignación activa en el curso. Los rankings usan otra guardia. Corregir
  cualquiera de esos comportamientos requiere una orden distinta.
- PostgreSQL real, migraciones, producción, staging, deploy, commit y push:
  **ninguno**. No se atribuye GitHub Actions ni despliegue de esta corrección.
- Staging propuesto: con un profesor del tenant de prueba, comprobar notas
  altas/bajas para un curso activo; desactivar su única asignación y verificar
  ambos 403; reactivarla y verificar de nuevo el payload exitoso. Repetir con
  filtro de asignación y confirmar aislamiento entre tenants.
- Rollback: retirar exclusivamente los dos predicados, restaurar la guardia de
  caracterización y revertir esta documentación. No hay rollback de datos.
- Estado: la capa continúa **Cerrada**. El primero de los diez hallazgos queda
  corregido localmente; **nueve siguen abiertos**. La verificación manual y
  staging de esta corrección quedan pendientes.
- Siguiente acción exacta: el usuario revisa el diff y decide cuándo ejecutar
  staging/publicar. No iniciar otro hallazgo de dashboard ni otra capa.

## 2026-08-25 — corrección puntual posterior al cierre: conexiones seriales

- Modo de acceso: mismo checkout local del backend; Git y los commits locales
  se validaron directamente. No se usó GitHub para inferir el estado local.
- Autorización: después de identificar expresamente el siguiente hallazgo y
  preguntar si debía corregirse continuando localmente con las verificaciones
  anteriores pendientes, el usuario respondió «continua». La autorización se
  limita al máximo de cuatro conexiones seriales; no incluye el siguiente
  hallazgo, la resolución académica duplicada.
- Precondiciones: rama `main`, árbol limpio confirmado por `git status`, `HEAD`
  y la referencia local `origin/main` coincidentes en
  `9f1908938514094486aa25f205e5f40c1990ee84`. Ese commit contiene exactamente
  la corrección anterior de `activo` y sus cinco archivos documentados. El
  commit base `123637ee80895023ecece9c32df526ef4eddd1e5` sigue siendo ancestro;
  la auditoría de continuidad anterior cubría hasta `1ab8912` y el único commit
  añadido después, `9f19089`, queda explicado aquí y en la entrada precedente.
  Que coincida con `origin/main` demuestra publicación, no CI ni despliegue.
- Caracterización antes de producto: las suites relacionadas partieron de
  **95 passed**. Se cambiaron primero solo las dos expectativas de conexiones:
  la señal contra el código anterior fue la esperada, **2 failed y 40
  deselected**, porque mostraba 6/4 y 5/3 en vez de 6/2 y 5/2.
- Producto modificado:
  `app/controllers/dashboard_controller.py` consolida las tres precondiciones
  DB en una conexión;
  `app/core/permissions.py` permite que `require_asignacion_access` reciba un
  cursor prestado sin abrirlo ni cerrarlo; y `app/routes/dashboard.py` conserva
  los mismos 422/403 interpretando el resultado consolidado.
- Consultas conservadas: profesor con asignación, **6 consultas y 2
  conexiones**; admin con asignación, **5 y 2**; profesor sin asignación, **2 y
  2**. Las cuatro consultas de las precondiciones conservan orden y parámetros:
  `(7, 4)`, `(12, 7)`, `(12,)`, `(77, 7, 4)`. La lectura final conserva su
  conexión separada y vuelve a resolver la asignación, como antes.
- Límites de error conservados: las precondiciones siguen fuera del
  `try/except`, por lo que sus fallos de infraestructura continúan como 500; la
  lectura final sigue dentro y conserva el 400 heredado. Permanecen idénticos
  el 422 sin curso y los mensajes 403 de scope, curso, acceso a asignación y
  pertenencia al curso.
- Pruebas modificadas:
  `tests/test_dashboard_caracterizacion.py` fija conteos, orden SQL, propiedad
  del cursor y las dos resoluciones aún existentes;
  `tests/test_dashboard_routes.py` fija delegación y límites de error; y
  `tests/test_permissions.py` demuestra que un cursor prestado no abre ni cierra
  recursos.
- Verificación específica:
  `pytest tests/test_dashboard_routes.py tests/test_dashboard_caracterizacion.py tests/test_dashboard_controlador.py tests/test_permissions.py`
  terminó con **99 passed**. Ruff sobre los seis archivos de producto/prueba
  informó **All checks passed**.
- Compuerta global: la primera ejecución restringida fue inválida por los 30
  errores de setup ya conocidos al acceder al temporal de pytest; alcanzó 1090
  pruebas pasadas y dejó Ruff y `pip check` correctos. La repetición con acceso
  válido terminó con **1120 passed**, 5 warnings heredados, Ruff correcto,
  dependencias íntegras y exit 0.
- Frontend: no se modificó ni necesita adaptación. Métodos, paths, query params,
  payloads, status codes y mensajes permanecen iguales; el cambio solo reduce
  checkouts internos del pool.
- PostgreSQL real, migraciones, staging, producción, deploy, commit y push de
  esta corrección: **ninguno**. Tampoco se atribuye evidencia de GitHub Actions.
- Staging propuesto: ejecutar notas altas y bajas como profesor y admin, con y
  sin `asignacion_id`; comprobar los mismos payloads y 422/403, y observar que
  el camino con asignación no supera dos checkouts de conexión. Repetir una
  denegación de curso y otra de asignación para comprobar el cierre de recursos.
- Rollback: revertir la consolidación del controlador y la ruta, retirar el
  cursor opcional del permiso compartido, restaurar las expectativas 6/4 y 5/3
  y revertir esta documentación. No hay rollback de datos.
- Riesgos residuales: la validación y la lectura final siguen en conexiones
  distintas, por lo que permanece la ventana TOCTOU. La asignación académica
  continúa resolviéndose dos veces y es el siguiente hallazgo; eliminar esa
  consulta exige una orden propia. El cursor prestado es propiedad del llamador
  y la prueba impide que el permiso lo cierre.
- Estado: la capa continúa **Cerrada**. Dos de los diez hallazgos originales
  están corregidos y **ocho siguen abiertos**. Staging, verificación manual,
  publicación y CI de esta corrección quedan pendientes.
- Siguiente acción exacta: el usuario revisa el diff y decide cuándo ejecutar
  staging/publicar. El siguiente hallazgo es la resolución duplicada de la
  asignación académica; **no iniciarlo sin otra orden explícita**.

## 2026-08-25 — corrección puntual posterior al cierre: resolución académica duplicada

- Modo de acceso: mismo checkout local del backend; Git, el árbol y los commits
  locales se comprobaron directamente.
- Autorización: después de entregar la reducción de conexiones e identificar
  expresamente la resolución duplicada como siguiente hallazgo no iniciado, el
  usuario respondió «continua». La orden cubre solo esa consulta duplicada.
- Precondiciones: rama `main`, árbol limpio confirmado con `git status`, `HEAD`
  y la referencia local `origin/main` coincidentes en
  `1f1ffc9d7395676abf73e1b77304178d47110534`. Ese commit contiene exactamente
  los nueve archivos de la reducción de conexiones. El base
  `123637ee80895023ecece9c32df526ef4eddd1e5` sigue siendo ancestro y el único
  commit posterior a `9f19089`, `1f1ffc9`, está explicado por la entrada
  anterior. La coincidencia con `origin/main` demuestra publicación, no CI ni
  despliegue.
- Caracterización antes de producto: las suites relacionadas partieron de
  **99 passed**. Se cambiaron primero el contrato de traspaso y los conteos; la
  señal esperada fue **10 failed y 72 passed** porque la validación aún devolvía
  dos valores, la ruta descartaba el ID resuelto y el controlador no aceptaba
  reutilizarlo.
- Producto modificado: únicamente
  `app/controllers/dashboard_controller.py` y `app/routes/dashboard.py`. La
  validación devuelve ahora el `asignacion_academica_id` que ya comprobó; la
  ruta lo entrega al controlador final y este omite la segunda llamada a
  `resolver_asignacion_academica_id_cursor`. Los llamadores directos que no
  suministren el ID resuelto conservan el fallback anterior.
- SQL y recursos: profesor con asignación pasa de **6 a 5 consultas**; admin de
  **5 a 4**. Ambos conservan **2 conexiones**. Sin asignación permanece en 2/2.
  Se elimina únicamente el segundo `SELECT` del resolvedor; las cuatro
  consultas de validación, la consulta agregada, sus parámetros y el ID
  académico usado por el filtro permanecen iguales.
- Contrato conservado: no cambian métodos, paths, query params, payloads,
  promedios, orden, colores, tenant, ownership, roles, 422, mensajes 403 ni el
  límite 500/400. La validación sigue fuera del `try/except` y la lectura final
  dentro, cada una con su conexión.
- Pruebas modificadas:
  `tests/test_dashboard_caracterizacion.py` fija 5/2 y 4/2 y exige una sola
  resolución;
  `tests/test_dashboard_controlador.py` demuestra que el controlador reutiliza
  `77` sin llamar al resolvedor; y
  `tests/test_dashboard_routes.py` fija el traspaso exacto del ID resuelto.
- Verificación específica: dashboard terminó con **82 passed**; al incluir
  permisos compartidos, **100 passed**. Ruff del alcance informó
  **All checks passed**.
- Compuerta global: `scripts/verify.py` se ejecutó con acceso válido al temporal
  de pytest y terminó con **1121 passed**, 5 warnings heredados, Ruff correcto,
  dependencias íntegras y exit 0.
- Frontend: no se modificó ni requiere adaptación; el cambio es interno y la
  superficie HTTP permanece idéntica.
- PostgreSQL real, migraciones, staging, producción, deploy, commit y push de
  esta corrección: **ninguno**. No se atribuye evidencia de GitHub Actions.
- Staging propuesto: ejecutar notas altas y bajas con una asignación derivada
  cuya `asignacion_academica_id` apunte a la base, comprobar el mismo payload y
  observar una sola consulta de resolución. Repetir como profesor y admin, y
  verificar los mismos 403 con una asignación ajena o de otro curso.
- Rollback: dejar de devolver/reenviar el ID académico resuelto, restaurar el
  resolvedor dentro de la lectura final y devolver las expectativas a 6/2 y
  5/2. No hay rollback de datos.
- Riesgos residuales: validación y lectura continúan en conexiones distintas,
  por lo que permanece la ventana TOCTOU. El fallback del controlador sigue
  resolviendo el ID para sus llamadores directos; la ruta HTTP usa siempre el
  valor ya validado.
- Estado: la capa continúa **Cerrada**. Tres de los diez hallazgos originales
  están corregidos y **siete siguen abiertos**, a los que se suma el undécimo
  que las correcciones introdujeron: **ocho en total** en esa fecha. *(El
  recuento cambió a **nueve** ese mismo día al refutarse el del promedio y
  sustituirse por dos.)* Staging, verificación manual,
  publicación y CI de esta corrección quedan pendientes.
- Siguiente acción exacta: el usuario revisa el diff y decide cuándo ejecutar
  staging/publicar. El siguiente hallazgo son las dos definiciones distintas de
  promedio; **no iniciarlo sin otra orden explícita**.

## 2026-08-25 — auditoría del hallazgo 3 y registro del hallazgo 11

- Modo de acceso: mismo checkout local del backend; Git y el árbol se
  comprobaron directamente.
- Motivo: el usuario pidió verificar **qué faltaba del hallazgo en curso** antes
  de commitear. La auditoría no modificó producto ni pruebas.
- Precondiciones: rama `main`, `HEAD` y `origin/main` coincidentes en
  `1f1ffc9d7395676abf73e1b77304178d47110534`, con la corrección del hallazgo 3
  **sin commitear** en seis archivos del árbol.
- **Lo que se confirmó del hallazgo 3, comprobándolo y no dándolo por bueno:**
  - la duplicación desaparece en las dos entradas afectadas, para profesor y
    para admin;
  - **no quedan otros caminos con el mismo patrón**. Los dos rankings parecían
    candidatos, pero `require_asignacion_access` consulta `asignaciones` por id
    y **no** resuelve la académica, así que resuelven una sola vez;
  - los conteos están **fijados por aserción** y no solo afirmados en prosa:
    `(5, 2)` para profesor, `(4, 2)` para admin y una comprobación explícita de
    que hay **una sola** resolución;
  - los tres caminos de rechazo siguen lanzando: el 422 por curso ausente y los
    dos 403. El `return` que pasó a `return None` cubre únicamente el camino sin
    asignación, donde el controlador no resolvía nada;
  - compuerta global con el árbol tal cual: **1121 pruebas, exit 0**, Ruff
    correcto y dependencias íntegras.
- **Lo que la auditoría encontró y no constaba**: las dos precondiciones
  `profesor_tiene_curso_controller` y
  `profesor_tiene_asignacion_en_curso_controller` quedaron **sin consumidor en
  producción** desde la corrección del hallazgo 2, que **ya está publicada**.
  Sigue en la lista de hallazgos como el **undécimo**, y es el primero del
  programa **introducido por una corrección** en vez de heredado.
- **Decisión del usuario**: registrarlo **sin retirar nada**. No se borra código
  de producto ni pruebas. El precedente es la capa 6 con
  `obtener_clases_profesor_controller`.
- Archivos modificados en este turno: **solo esta bitácora**. Código de
  producto y pruebas: **ninguno**.
- PostgreSQL real, migraciones, staging, producción, deploy, commit y push:
  **ninguno**. No se atribuye evidencia de GitHub Actions.
- Estado: la capa continúa **Cerrada**. Del hallazgo 3 **no falta código**: solo
  commit, publicación, staging y verificación manual. Hallazgos abiertos:
  **ocho** —los siete heredados de 7.0 más el undécimo—.
- Siguiente acción exacta: el usuario commitea y decide cuándo publicar. **No
  retirar las dos funciones huérfanas ni iniciar el hallazgo del promedio sin
  una orden explícita.**

## 2026-08-25 — el hallazgo del promedio, revisado antes de corregirlo

- Modo de acceso: mismo checkout local; Git y el árbol comprobados
  directamente.
- Autorización: el usuario ordenó continuar tras identificarse expresamente
  este hallazgo como el siguiente. La orden cubre **solo** las dos definiciones
  de promedio.
- Precondiciones: rama `main`, árbol **limpio**, `HEAD` y `origin/main`
  coincidentes en `6130ce245d4ac6def4736da58251addd68d4e9ad`, que contiene la
  corrección del hallazgo 3 y el registro del 11.
- **No se modificó producto ni pruebas.** La revisión previa demostró que el
  hallazgo, tal como 7.0 lo redactó, **está equivocado en su parte central**, y
  corregirlo según ese texto habría sido una **regresión**.
- **Evidencia de la refutación**, obtenida leyendo las cuatro consultas y
  calculando ambas fórmulas:
  - los rankings filtran **una sola asignatura**, y en ese ámbito promedio de
    promedios y promedio plano son **idénticos**, porque el `AVG` exterior
    recorre un único grupo y `promedio_clase` no se trunca antes. Verificado con
    tres juegos de notas;
  - el 2,50 del ejemplo **no lo calcula ninguna consulta de la aplicación**:
    exige cruzar asignaturas con promedio plano, y eso no existe. Con ese mismo
    ejemplo los rankings darían 4,00 y 2,00;
  - el promedio de promedios **coincide con el del boletín**, registrado por
    7.0 de `notas`, y es el criterio correcto para un agregado
    multi-asignatura.
- **Dos divergencias reales encontradas en su lugar**, ambas añadidas a la lista
  de hallazgos:
  1. **`ROUND(…, 1)` en el expediente frente a `TRUNC(…, 2)` en el dashboard**,
     para **el mismo ámbito** —un estudiante en una materia—. Cuatro ejemplos
     comprobados en los que el estudiante sale **aprobado en el expediente y en
     rojo en el dashboard**: 2,9/3,0/3,0 → 3,0 frente a 2,96; 2,95/2,95 → 3,0
     frente a 2,95; 3,0/2,9 → 3,0 frente a 2,95; 2,5/3,4 → 3,0 frente a 2,95.
     **Es el efecto que el hallazgo original describía, pero por el redondeo.**
  2. **Notas altas y bajas no filtran por `periodo`; los rankings sí.** El
     mismo panel mezcla una cifra anual con una cifra por periodo.
- **Ninguna de las dos se corrige en este turno.** La primera **cruza a
  `estudiantes`, un dominio ya migrado**, y las dos cambian **la cifra que ve el
  usuario**, así que exigen una decisión explícita sobre cuál es el contrato.
  No se decide por inferencia.
- Archivos modificados: **solo esta bitácora**. Producto y pruebas: **ninguno**.
- Compuerta global: **1121 pruebas, exit 0**, Ruff correcto y dependencias
  íntegras, sin cambios respecto al commit publicado.
- PostgreSQL real, migraciones, staging, producción, deploy, commit y push:
  **ninguno**.
- **Decisiones del usuario en este mismo turno, tras presentarle las salidas de
  cada una:**
  - sobre el **redondeo**, con cuatro salidas ofrecidas —adoptar `TRUNC(…, 2)`,
    adoptar `ROUND(…, 1)`, consultar antes la regla académica del colegio, o no
    tocar nada—: **dejar las dos como están**, registrando la divergencia. Queda
    vigente que la misma nota se vea aprobada en el expediente y en rojo en el
    dashboard;
  - sobre el **`periodo` ausente**, con dos salidas: **dejarlo registrado**, sin
    añadir el filtro.
- **Ninguna de las dos se marca como corregida ni como resuelta.** Conservan su
  riesgo íntegro. Es el mismo criterio que la capa 6 aplicó a su código muerto y
  que el hallazgo 11 recibió horas antes: **se registra, no se corrige**.
- **`estudiantes_repository` no se tocó**, que era la condición para no ampliar
  el alcance a un dominio ya migrado.
- Estado: la capa continúa **Cerrada**. El hallazgo del promedio queda
  **refutado en su parte central y sustituido por dos divergencias reales**, las
  dos **abiertas y registradas por decisión explícita**. Recuento vigente:
  **nueve** hallazgos abiertos.
- Siguiente acción exacta: **esperar una orden explícita del usuario.** No queda
  ningún hallazgo en curso. Los que siguen —las siete entradas que absorben
  `Exception` y devuelven `str(e)` al cliente, la doble validación de `dias`, la
  pareja de literales gemelos, las f-strings en SQL y el `periodo: int = 1`
  inalcanzable— **no se inician sin orden**, y ninguna de las dos divergencias
  recién registradas se corrige sin una decisión previa sobre cuál es la regla
  académica.

## 2026-08-25 — corrección puntual posterior al cierre: `Exception` absorbida y `str(e)` filtrado

- Modo de acceso: mismo checkout local; Git y el árbol comprobados
  directamente.
- Autorización: el usuario ordenó continuar tras haberse identificado este
  hallazgo como **el más serio de los que quedaban**. La orden cubre solo estas
  siete entradas.
- Precondiciones: rama `main`, árbol **limpio**, `HEAD` y `origin/main`
  coincidentes en `451fb7bf51144056f983f92a6e080ef4c000cd4f`.
- **Riesgo evaluado antes de tocar nada, y descartado con evidencia.** El cambio
  de 400 a 500 es contrato observable, así que se comprobó **en el frontend
  desplegado** si alguien depende de él: **ningún consumidor del dashboard lee
  `status` ni `detail`**. `useRendimientoProfesor`, `useRankingProfesor`,
  `useInasistenciasProfesor`, `useCumpleanosProfesor` y `useDashboardAdmin`
  capturan de forma genérica y muestran **su propia constante**. El cambio es
  por tanto **invisible para el frontend**. Es la primera vez en el programa que
  una corrección se valida contra el repositorio del cliente antes de aplicarse.
- Producto modificado: **únicamente `app/routes/dashboard.py`**. Se añadieron
  `logging`, un `logger` de módulo y la constante `_ERROR_INTERNO_DASHBOARD`, y
  los **siete** manejadores —idénticos entre sí, verificado antes de sustituir—
  pasaron de `except Exception as e: HTTPException(400, str(e))` a
  `except Exception: logger.exception(...); HTTPException(500, constante)`. Cada
  uno registra **qué panel** falló y con qué id.
- Contrato conservado salvo lo que el hallazgo exigía cambiar: no cambian
  métodos, paths, query params, payloads de éxito, promedios, orden, tenant,
  ownership ni roles. El **422** por curso ausente, los **dos 403** del filtro y
  los de permisos siguen igual, porque se lanzan **fuera** del `try`.
- Decisión registrada: **no se introdujo una excepción de dominio**, al
  contrario que en `tipos_pagos`. Allí servía para distinguir infraestructura de
  errores de negocio; aquí **no hay errores de negocio** que distinguir, así que
  la clase habría tenido **un solo uso**.
- Pruebas: `test_dashboard_routes_translate_controller_errors_to_400` era la
  guardia que fijaba el comportamiento anterior. Se sustituyó por
  `..._to_500`, que sobre las **siete** entradas comprueba el 500, que el
  `detail` es la constante, que **el texto interno no viaja al cliente** y que
  **sí queda en el log con su `exc_info`**.
- **Verificación por ASGI, con una respuesta HTTP real.** Es la técnica que 7.0
  de `notas` introdujo y la única que observa un status code de verdad; en este
  hallazgo era obligada, porque el hallazgo **es** sobre status codes. Se
  condujo la aplicación con un controlador que lanza
  `RuntimeError('FATAL: password authentication failed for user "admin"')`.
  Resultado: **status 500**, cuerpo
  `{"detail":"No se pudo cargar la informacion del panel"}` y **la credencial no
  aparece en la respuesta**, mientras el traceback completo sí queda en el log.
- Compuerta global: **1121 pruebas, exit 0**, Ruff correcto, dependencias
  íntegras. `git diff --check` limpio. El diff son **dos archivos**.
- PostgreSQL real, migraciones, staging, producción, deploy, commit y push:
  **ninguno**. No se atribuye evidencia de GitHub Actions.
- Rollback: devolver los siete manejadores a `except Exception as e` con
  `HTTPException(400, str(e))`, retirar el logger y la constante, y restaurar la
  prueba anterior. No hay rollback de datos.
- Riesgos residuales: el **otro** hallazgo sigue vivo y ahora es más visible —el
  filtro de rendimiento consulta la base **fuera** del `try`, así que un fallo
  *ahí* sale como 500 por la vía de FastAPI, no por esta—. El resultado coincide,
  pero por caminos distintos y sin pasar por el log nuevo.
- Estado: la capa continúa **Cerrada**. **Cuatro** de los diez hallazgos
  originales corregidos; abiertos: **ocho**.
- Siguiente acción exacta: el usuario revisa el diff y decide cuándo publicar.
  **No iniciar otro hallazgo sin orden explícita.**

## Entrega al próximo chat

- Capa activa: **Ninguna**. `dashboard` continúa cerrado; las correcciones
  puntuales del 2026-08-25 no lo reactivaron.
- Última subcapa terminada: **7.1**, cerrada el 2026-08-17. Con ella la
  frontera de persistencia del dominio quedó cerrada.
- **Capa cerrada** el 2026-08-19. La verificación manual original fue correcta.
  Para las correcciones puntuales del 2026-08-25 siguen pendientes staging y
  verificación manual. La primera está publicada en `9f19089`; la reducción de
  conexiones permanece local.
- Primera subcapa pendiente: **ninguna.** El usuario decidió **cerrar la capa
  aquí**, sin abrir 7.2: `response_model` y los errores de dominio **no se
  añaden** y no quedan como deuda de esta capa, sino como trabajo que exigiría
  una orden explícita.
- Commit base: `123637ee80895023ecece9c32df526ef4eddd1e5`, rama `main`,
  **publicado y desplegado**. Al cerrar la capa, `HEAD` es `8591816` y **coincide
  con `origin/main`**: los cuatro commits de la capa **están publicados**, y como
  un push a `main` dispara el despliegue, **producción ya corre este código**. El
  rollback a `123637e` exigiría otro push y otro despliegue.
- Compuerta de cierre: **756 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro. La suite pasó de 714 al activar la capa a 756.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas**: valor
  operativo final de `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub
  Actions posterior a la capa 0. La credencial privilegiada de la capa 4 sigue
  **sin rotar**.
- Lo que consiguió 7.1: `dashboard_controller.py` pasó de **336 a 146 líneas** y
  de **8 sentencias SQL inline a 0**; la persistencia vive en
  `app/repositories/dashboard_repository.py`, **ocho funciones** que reciben el
  cursor más dos fragmentos privados. Comparador AST contra el commit base:
  **conjunto de SQL idéntico, 16 de 16 literales byte a byte**, sin una sola
  autorización de cambio de texto. **Ninguna prueba cambió de expectativa salvo
  las dos que debían fallar.**
- Lo que 7.0 dejó medido: **7 entradas HTTP**, todas `GET` y todas de **solo
  lectura**; **cero tablas escritas** y **cero transacciones propias**; **42
  pruebas de caracterización** y los conteos de ocho caminos. La línea base más
  cara era **6 consultas y 4 conexiones**; la corrección puntual conserva las 6
  consultas y reduce el máximo a **2 conexiones**. **No hay N+1.**
- **Lo que la activación creía y resultó falso**: que dashboard concentraba
  «varias consultas de promedios por estudiante». Cada panel se resuelve con
  **una sola consulta agregada**. El coste identificado eran las conexiones
  seriales, reducidas ahora de cuatro a dos.
- Estado de la capa: **exclusivamente una refactorización hasta aquí**, como la 5
  y la 6. **No ha tocado la base de datos**, ni siquiera para leer: toda la
  caracterización se hizo con dobles. Su rollback es de código: revertir hasta
  `123637e`, que **ya está desplegado**, así que revertir exigiría push y
  despliegue.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** La capa 7 es «uno a la vez»; los demás necesitan su
     propia bitácora y su propia orden.
  2. Los dos primeros hallazgos quedaron corregidos con órdenes explícitas: las
     precondiciones exigen `activo = TRUE` y comparten una conexión. **Los ocho
     restantes siguen abiertos** y no se corrigen por inferencia.
  3. **No volver a cambiar el ciclo de vida por inferencia.** La validación
     consolidada posee una conexión y la lectura final otra para conservar los
     límites 500/400. Unificarlas exigiría otra decisión.
  4. **`response_model` filtra campos.** Es el riesgo propio de esta capa y el
     centro del punto de decisión abierto.
  5. **En un panel, la cifra es el contrato.** Este dominio usa **dos** fórmulas
     de promedio distintas, y el sistema una tercera en estudiantes.
  6. Las dos consultas testigo permanecen en `dashboard_repository`, filtran
     `activo` y se ejecutan con el cursor de la validación consolidada; no se
     amplió el cambio a `asignaciones_repository`.
- Siguiente acción exacta: el usuario revisa este diff y decide cuándo ejecutar
  staging/publicar. El siguiente hallazgo es la resolución académica duplicada;
  **no iniciarlo ni activar otra capa sin una orden explícita**.
