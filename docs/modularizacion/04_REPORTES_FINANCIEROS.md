# Capa 4: reportes financieros

Última revisión: 2026-08-14.

## Control

- Estado: **Activa**.
- Commit base: `46fad2c4c12482830cc58ac28ea2512f96155fb8`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **4.3**.
- Progreso: **4.0, 4.1 y 4.2 cerradas**; el N+1 de estado de cuenta de reportes
  pasó de `10 + 5N` a 15 consultas fijas para `N > 0`, sin cambiar contratos ni
  reglas financieras.
- Código de producto modificado al activar: **ninguno**.
- Autorización: orden explícita del usuario el 2026-08-14 para corregir la
  continuidad documental y activar la capa 4. La activación no autoriza iniciar
  4.0 en este mismo turno.

## Objetivo

Modularizar el dominio de reportes financieros separando HTTP, reglas,
servicios y persistencia; eliminar el N+1 mediante consultas agrupadas
equivalentes; y medir las consultas críticas con `EXPLAIN ANALYZE` sobre datos
no productivos.

El resultado debe conservar rutas, métodos, payloads, status codes, permisos,
tenant, ownership, cálculos, orden, transacciones y demás comportamiento
observable. El objetivo procede exclusivamente del índice maestro; la
activación no inspeccionó el código y por eso no afirma todavía qué endpoints,
archivos, consultas o pruebas forman el dominio.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último cierre
  local registrado, correspondiente a la capa 3, terminó en exit 0 con 570
  pruebas, Ruff correcto y dependencias íntegras; no se reprodujo durante esta
  activación documental.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  La cancelación real y una primera medición no productiva de
  `DB_STATEMENT_TIMEOUT_MS` quedaron comprobadas en 4.0. El valor operativo
  definitivo sigue **pendiente y aceptado** porque la rama entregada no es
  estructuralmente equivalente al código actual, tiene poco volumen financiero
  y no se conoce el deadline HTTP externo.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una nueva auditoría.
- Tenants versionados y alta reproducible cerrados en la capa 3. Los dos schemas
  conservados tienen 37 claves foráneas, 30 secuencias propias y 30 migraciones
  registradas.
- La última evidencia de GitHub Actions corresponde a la capa 0. No existe
  evidencia de un run remoto asociado a los cambios posteriores y esa
  verificación permanece **pendiente y aceptada**.

## Alcance autorizado

- Inventariar las entradas HTTP, reglas, consultas, pruebas y consumidores del
  dominio de reportes financieros mediante búsquedas dirigidas.
- Caracterizar antes de extraer rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, cálculos, orden, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia, con pruebas de
  caracterización previas a cada extracción importante.
- Identificar y eliminar el N+1 solo mediante consultas agrupadas cuya
  equivalencia funcional quede demostrada.
- Contar y comparar las consultas críticas antes y después.
- Ejecutar `EXPLAIN ANALYZE` únicamente sobre datos no productivos y registrar
  el plan y las condiciones de medición.

## Fuera de alcance

- Pagos y tipos de pago, que pertenecen a la capa 5, salvo la lectura mínima
  indispensable para caracterizar un contrato consumido por reportes.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas
  financieras, redondeos, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM o el driver.
- Agregar funciones de producto, rediseñar respuestas o corregir defectos
  ajenos a la primera subcapa pendiente.
- Crear abstracciones compartidas sin dos usos reales comprobados.
- Ejecutar `EXPLAIN ANALYZE`, pruebas destructivas o consultas de medición sobre
  producción; hacer deploy, migraciones reales, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Importes, saldos, filtros, agrupaciones, orden, nulos y redondeos conservan su
  resultado actual.
- La propiedad de cursor, conexión, `commit`, `rollback` y devolución al pool
  definida en la capa 1 no cambia.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, sustituir un N+1 por una consulta agrupada
  equivalente. Esa autorización no permite ningún otro cambio de semántica.
- Toda medición que dependa del volumen de datos se hace fuera de producción y
  declara el conjunto de datos y las limitaciones de la evidencia.

## Línea base registrada en 4.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider -q tests\test_reportes_query_counts.py tests\test_reportes_pagination.py tests\test_anulaciones_financieras.py::test_formatear_ingreso_anulado_no_suma_como_monto_valido tests\test_anulaciones_financieras.py::test_reporte_general_excluye_pagos_anulados_de_totales tests\test_pagos_adelantados.py::test_reporte_curso_aplica_solo_adelantos_maduros_y_no_los_duplica` | **31 pasaron** en 0,48 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **585 pasaron**, 5 warnings conocidas, exit 0 |
| Ruff | Ejecutado por la compuerta global y también sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 4.0 | Inventario, contratos, caracterización y línea base de consultas | **Cerrada** |
| 4.1 | Extraer la persistencia de los reportes simples sin cambiar SQL ni respuestas | **Cerrada** |
| 4.2 | Sustituir el N+1 de `/reportes/estado-cuenta/{curso_id}` por lecturas agrupadas equivalentes | **Cerrada** |
| 4.3 | Separar reglas financieras de sus consumidores y cerrar medición/retirada heredada | **Pendiente** |

El desglose se deriva del inventario de 4.0. Cada subcapa deberá volver a
acotar sus archivos antes de modificar y no podrá incorporar trabajo de la
siguiente.

Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa 4.0 — alcance ejecutado

1. Confirmar `main`, árbol limpio y que todo commit posterior al base esté
   explicado en esta bitácora.
2. Reproducir la compuerta heredada y determinar las pruebas específicas sin
   ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas del dominio de reportes financieros.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, persistencia, cálculos y efectos laterales.
5. Registrar los contratos observables exactos: rutas, métodos, payloads,
   status codes, permisos, tenant, ownership, orden, nulos, redondeos,
   transacciones y errores.
6. Caracterizar con pruebas los caminos que una extracción posterior pueda
   alterar. 4.0 no autoriza una extracción ni un cambio de producto.
7. Medir o instrumentar herméticamente el número de consultas de los caminos
   críticos para identificar con evidencia el N+1; no optimizarlo todavía.
8. Definir el conjunto no productivo y el procedimiento seguro que se usarán
   para `EXPLAIN ANALYZE`, sin acceder a producción.
9. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 4.0.
10. Actualizar esta bitácora, definir la siguiente subcapa con la evidencia
    obtenida y detenerse sin iniciarla.

## Criterios de cierre de la subcapa 4.0

- El dominio y sus consumidores están inventariados con archivos y puntos de
  entrada concretos, sin lectura global innecesaria.
- Los contratos HTTP, financieros, de seguridad, tenant y transacción están
  enumerados y protegidos por caracterización suficiente.
- El N+1 está localizado con una línea base reproducible de consultas, no por
  inferencia.
- Existe un procedimiento de medición con `EXPLAIN ANALYZE` limitado a datos no
  productivos.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 4.0.
- La siguiente subcapa queda definida y no iniciada.

Los siete criterios se cumplieron en 4.0. La limitación de la rama de prueba
descrita abajo no invalida la caracterización hermética ni el procedimiento de
medición; sí impide presentar el valor operativo final del timeout como cerrado.

## Inventario y contratos fijados en 4.0

La frontera directa tiene nueve entradas síncronas `GET`, todas protegidas por
`get_current_active_admin` y ejecutadas por FastAPI en el threadpool:

| Entrada | Contrato observable que debe conservarse |
|---|---|
| `/reportes/general` | Objeto con estadísticas, estudiantes por curso e ingresos/egresos mensuales |
| `/reportes/estado-cuenta/{curso_id}` | Lista con `id`, nombre, apellido, pagado, total, deuda y `deudas_detalle` |
| `/reportes/ingresos-mes/{mes}` | Lista heredada sin `limit`; con `limit`, sobre `{total,limit,offset,items}` |
| `/reportes/ingresos-rango` | Igual dualidad lista/sobre; rango inicio inclusivo y fin inclusivo mediante `< fin + 1 day` |
| `/reportes/egresos-rango` | Igual dualidad; orden `fecha DESC, id DESC` |
| `/estado-cuenta/curso/{curso_id}` | Lista con deuda y `tipos_pagos`; no equivale al estado de cuenta de `/reportes` |
| `/estado-cuenta/estudiante/{estudiante_id}` | Objeto equivalente al consumidor anterior; inexistente devuelve mensaje con 200 |
| `/cartera/mora` | Lista detallada de deuda académica/inventario; `curso_id=0` conserva hoy el significado de no filtrar |
| `/cartera/mora/resumen` | Totales, `top_5` y distribución por curso |

- No hay body, `response_model` ni status explícito. Éxito normal: 200;
  validación FastAPI: 422; autenticación inválida: 401; admin o tenant no
  autorizado/suspendido: 403.
- Las rutas `/reportes` traducen una excepción que escape a 400, pero sus
  controladores actualmente absorben errores y retornan fallbacks 200. Cuentas
  y cartera dejan propagar el error. Estas diferencias no se unifican.
- El tenant procede del JWT y cada conexión recibe `search_path` al schema del
  tenant más `public`. No hay un segundo filtro de ownership por curso o
  estudiante dentro del tenant.
- Los controladores de lectura no hacen `commit`; cierran cursor y conexión, y
  la devolución al pool hace `rollback` de la transacción abierta.
- Pagos anulados no suman en saldos/totales, aunque permanecen en listados con
  `monto_valido=0`. Se conservan los fallbacks de nulos, la zona
  `America/Bogota`, los redondeos, los órdenes actuales y la forma irregular de
  «Otros Pagos».
- `estado_cuenta_controller.py` y `cartera_mora_controller.py` son consumidores
  directos de las mismas reglas; `calcular_deudas_estudiante` también se usa en
  estudiantes, y otras funciones de cobros llegan a pagos (capa 5). Una
  extracción no puede mover esos consumidores por inferencia.

La prueba `tests/test_reportes_query_counts.py` congela los nueve paths, método,
ausencia de body/modelo, dependencia admin y ejecución síncrona, además de los
conteos siguientes. Las pruebas previas conservan lista frente a paginación,
errores 400, anulación y aplicaciones de pagos adelantados.

## Línea base SQL y N+1

Los conteos excluyen autenticación, `search_path` y la sentencia combinada de
timeouts de cada checkout de conexión:

| Camino | Consultas de dominio al cerrar 4.0 |
|---|---:|
| Reporte general | 4 |
| Ingresos o egresos sin paginación | 1 |
| Ingresos o egresos paginados | 2 |
| `/reportes/estado-cuenta`, curso vacío | 6 |
| `/reportes/estado-cuenta`, `N > 0` | `10 + 5N` |
| `/estado-cuenta/curso`, curso vacío | 1 |
| `/estado-cuenta/curso`, `N > 0` | `1 + 12N` |
| `/estado-cuenta/estudiante`, encontrado | 13 |
| Cartera sin estudiantes | 5 |
| Cartera con estudiantes | 12, independiente de `N` |

En la línea base de 4.0, el N+1 objetivo de la capa estaba localizado en
`reporte_estado_cuenta_curso_controller`: por estudiante repetía dos agregados
de pagos, la comprobación y lectura de valores personalizados, y la suma de
«otros». 4.2 sustituyó ese `5N`; el conteo vigente es 6 para curso vacío y 15
para cualquier `N > 0` con las tablas opcionales presentes. El consumidor
`/estado-cuenta/curso` continúa repitiendo todo el cálculo de deuda y llega a
doce consultas por estudiante. Cartera ya precarga los datos y sirve como
evidencia de un patrón agrupado, no como autorización para crear una abstracción
común.

## Medición no productiva y calibración del timeout

El usuario entregó una rama Neon de prueba. La URI se pasó solo como variable de
entorno de un proceso efímero, no se escribió en el repositorio ni se imprimió;
la sonda temporal fue eliminada. Cada conexión estableció
`default_transaction_read_only=on`, verificó `transaction_read_only=on`, usó
`ROLLBACK` y no ejecutó DDL/DML. Solo se conservaron conteos y tiempos agregados,
no filas ni planes completos.

La credencial **no es un rol read-only**: puede crear objetos en la base y el
schema, y tiene `CREATEDB`/`CREATEROLE` aunque no es superusuario. La seguridad
de esta ejecución provino de la transacción forzada. La credencial debe rotarse
por haber sido compartida en el chat y una repetición debería usar un rol
dedicado con privilegios de solo lectura.

Condiciones y límites del conjunto:

- endpoint directo distinto del host configurado localmente; dos schemas
  tenant; se midió el mayor por filas de tablas núcleo;
- 172 estudiantes, 74 pagos, 0 egresos, 225 asignaciones, 610 detalles de nota,
  3 cabeceras y 4 detalles de boletín;
- tres repeticiones calientes por camino, `EXPLAIN (ANALYZE, BUFFERS, TIMING
  OFF, SUMMARY ON, FORMAT JSON)`, timeout local de 30 s; sin filas de negocio en
  la salida;
- `public.schema_migrations` tiene 64 filas globales; ese total no se usó como
  prueba de equivalencia. Ninguno de los dos tenants contiene
  `pagos.concepto_id`, aunque el código actual sí consulta esa columna, y
  `/reportes/estado-cuenta/{curso_id}` cayó en su fallback por
  `UndefinedColumn`. No se alteró la rama para ocultar la incompatibilidad.

| Camino medido | Consultas | Tiempo total, 3 ejecuciones | Mayor `Execution Time` de PostgreSQL |
|---|---:|---:|---:|
| Reporte general | 4 | 1,025–1,170 s | 0,298 ms |
| Ingresos por mes paginados, 42 filas | 2 | 0,868–0,900 s | 0,165 ms |
| Ingresos por rango paginados, 74 filas | 2 | 0,960–0,972 s | 0,216 ms |
| Egresos por rango, conjunto vacío | 2 | 0,998–1,172 s | 0,042 ms |
| Cartera, 172 estudiantes | 12 | 1,500–1,548 s | 0,518 ms |
| Estado de cuenta consumidor, 19 estudiantes | **229** | **14,277–16,371 s** | 13,451 ms |
| Planilla, 19 estudiantes | 2 | 0,867–0,901 s | 0,182 ms |
| Boletín, 13 materias | 4 | 0,995–1,136 s | 0,984 ms |

La conexión directa y los viajes de red dominan los tiempos totales. Ninguna
sentencia fue cancelada a 30 s y la mayor llamada de cliente individual fue
142,578 ms; el endpoint de 16,371 s es lento por 229 sentencias pequeñas. Un
`statement_timeout` solo limita cada sentencia y no puede corregir esa suma.

El servidor de la rama tiene `statement_timeout=0`, `lock_timeout=0` e
`idle_in_transaction_session_timeout=5min`; por tanto, sin la configuración de
la aplicación no existiría límite de sentencia. Una sonda con
`statement_timeout=1000` canceló `pg_sleep(3)` en 1,114 s con SQLSTATE `57014`.
La sentencia dejó de ejecutarse, la transacción se revirtió y luego se cerró la
conexión; el servidor no mantuvo la consulta en segundo plano.

Decisión de calibración: **no cambiar aún el valor de producto en 4.0**. El
candidato prudente es `15000` ms: queda por encima de `lock_timeout=10000`,
reduce a la mitad la ventana actual y conserva más de cien veces la mayor
llamada de cliente observada. No se adopta todavía porque falta una rama con el
schema actual, egresos y pagos representativos, y el deadline HTTP/proxy más
corto. `30000` permanece efectivo y el pendiente operativo no se marca como
cumplido.

## Subcapa 4.1 — alcance ejecutado

1. Revalidar Git y limitar la inspección a rutas, controlador, pruebas y SQL de
   reporte general, ingresos por mes/rango y egresos por rango.
2. Añadir o conservar caracterización del texto/orden de consultas, parámetros,
   lista heredada frente a sobre paginado, formatos, nulos y fallbacks antes de
   mover persistencia.
3. Extraer únicamente las lecturas SQL de esos cuatro caminos a una frontera de
   persistencia específica de reportes, manteniendo el controlador como dueño
   de conexión, cursor, cierre y manejo de errores.
4. Conservar exactamente las cuatro consultas del general y una/dos consultas
   de cada listado, incluidos `TO_CHAR`, casts, rangos, orden y parámetros.
5. No tocar estados de cuenta, cartera, cobros, pagos, N+1, timeouts ni la base
   de datos; esos trabajos pertenecen a subcapas posteriores o al pendiente
   operativo explícito.
6. Ejecutar pruebas específicas, Ruff, compuerta global y `git diff --check`;
   documentar y detenerse antes de 4.2.

Los seis puntos se cumplieron en 4.1. El cierre y sus verificaciones están en
el registro de ejecución; no se inició el trabajo de 4.2.

## Subcapa 4.2 — alcance ejecutado

1. Revalidar Git y limitar el alcance a
   `/reportes/estado-cuenta/{curso_id}`, su controlador, persistencia y pruebas.
2. Partir de la caracterización `10 + 5N` de 4.0 y añadir casos discriminantes
   de pagos por `concepto_id`, nombre, aplicaciones maduras, valores
   personalizados y «Otros Pagos».
3. Sustituir únicamente el término `5N` por lecturas agrupadas para todos los
   estudiantes del curso, manteniendo las mismas reglas y la misma respuesta.
4. Conservar permisos admin, tenant por `search_path`, una sola conexión,
   orden, importes, mora, nulos, fallback `[]` y manejo de errores.
5. No mezclar ni corregir el `1 + 12N` del consumidor de cuentas; no modificar
   cartera, pagos, timeouts ni otras funciones de producto.
6. Medir herméticamente el conteo antes/después y documentar el nuevo valor
   fijo. No afirmar equivalencia real con la rama Neon anterior, cuyo schema
   carecía de `pagos.concepto_id`.
7. Ejecutar pruebas específicas, Ruff, compuerta global y `git diff --check`;
   documentar y detenerse antes de 4.3.

Los siete puntos se cumplieron en 4.2. El cierre y sus verificaciones están en
el registro de ejecución; no se inspeccionó ni inició el trabajo de 4.3.

## Primera subcapa pendiente: 4.3 — trabajo exacto

1. Revalidar Git y limitar la inspección a las reglas financieras de reportes,
   su orquestación, los consumidores directos ya inventariados en 4.0 y sus
   pruebas relacionadas.
2. Añadir o conservar caracterización antes de mover reglas: payloads, cálculos,
   orden, mora, redondeos, nulos, errores, tenant, lifecycle y conteo 6/15 del
   estado de cuenta de reportes.
3. Separar reglas, HTTP y persistencia solo donde el inventario confirme una
   frontera real y, para cualquier abstracción compartida, al menos dos usos
   efectivos. No unificar contratos distintos por compartir nombres.
4. No eliminar ni optimizar el `1 + 12N` del consumidor de cuentas. Si la
   separación exige ajustar una delegación o import, caracterizar y conservar
   su conteo y semántica; no modificar cartera o pagos más allá de demostrar que
   sus contratos siguen intactos.
5. Medir las consultas críticas únicamente sobre datos no productivos y un
   schema equivalente. Si el conjunto no es equivalente, registrar la limitación
   y no presentar la medición como evidencia real de equivalencia.
6. Retirar solo código heredado que quede probado sin consumidores después de la
   separación; ejecutar pruebas específicas, Ruff, compuerta global y
   `git diff --check`.
7. Al ser la última subcapa, documentar staging, rollback y verificación manual;
   cerrar la capa y actualizar el índice solo si toda la compuerta queda
   satisfecha. Dejar la capa 5 en espera y detenerse.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- HTTP, reglas, servicios y persistencia del dominio están separados con
  contratos estables.
- El N+1 está eliminado mediante consultas agrupadas equivalentes y la mejora
  está medida.
- Las consultas críticas tienen evidencia de `EXPLAIN ANALYZE` sobre datos no
  productivos.
- Rutas, payloads, status codes, permisos, tenant, ownership, cálculos,
  transacciones y comportamiento observable permanecen conservados.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados.
- La capa 5 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- Se usa `46fad2c4c12482830cc58ac28ea2512f96155fb8` como commit base porque es el
  `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main` al activar.
- Los 13 commits posteriores al base de la capa 3 fueron auditados; sus asuntos
  y archivos están explicados materialmente en `03_MIGRACIONES_TENANTS.md`. No
  hay commits ajenos ni divergencia local.
- El usuario eligió continuar localmente y activar esta capa manteniendo
  pendientes la calibración de `DB_STATEMENT_TIMEOUT_MS` y la evidencia remota
  de GitHub Actions. Ninguna se marca como cumplida.
- La activación corrige la continuidad obsoleta de la capa 3 y consume la
  autorización puntual guardada en `PROMPT_CONTINUACION.md`.
- 4.0 se mantuvo limitada a inventario, contratos, caracterización y línea
  base: añadió pruebas, pero no cambió producto, SQL ni configuración.
- La frontera incluye los cinco endpoints de `reportes.py` y, como consumidores
  de las mismas reglas, dos entradas de cuentas y dos de cartera. Los dos
  estados de cuenta no se consideran equivalentes por compartir nombre.
- El primer objetivo de eliminación es el `10 + 5N` de
  `/reportes/estado-cuenta/{curso_id}`. El `1 + 12N` del consumidor de cuentas
  queda visible, pero no se mezcla automáticamente en la misma extracción.
- La medición autorizada fue exclusivamente no productiva y READ ONLY. La rama
  entregada permite proponer `15000` ms, no adoptarlo ni cerrar la calibración.
- 4.1 creó una frontera de persistencia específica de reportes mediante cuatro
  funciones que reciben el cursor existente. El controlador conserva la
  propiedad de conexión, cursor, cierre y fallback de errores.
- La extracción conservó byte por byte las 13 cadenas SQL anteriores: cuatro
  consultas para el reporte general y una o dos para cada listado según
  `limit is not None`. También conservó parámetros, orden, nulos, fechas,
  anulación y lista heredada frente a sobre paginado.
- Las rarezas caracterizadas —`offset` sin `limit`, `[]` ante error paginado,
  comparación SQL exacta de `Anulado` y ausencia de desempate en ingresos— se
  preservaron deliberadamente; corregirlas no pertenecía a 4.1.
- No se tocaron estados de cuenta, cartera, cobros, pagos, N+1 ni timeouts.
- 4.2 mantuvo la conexión y el cursor en el controlador y añadió a la frontera
  de persistencia solo dos operaciones: los dos agregados de pagos por todos los
  estudiantes y el agregado de «Otros Pagos». Ninguna abre, cierra, confirma o
  revierte recursos.
- Los valores personalizados reutilizan el helper agrupado ya existente, ahora
  con un segundo consumidor real. No se creó un helper genérico de paginación ni
  otra abstracción compartida.
- Los dos primeros mapas de `obtener_pagos_por_concepto_estudiantes` no se
  reutilizan porque excluyen pagos con aplicaciones y no son equivalentes a las
  lecturas heredadas; solo se conserva su tercer mapa de aplicaciones maduras.
- La prioridad sigue siendo presencia del nombre —incluso con importe cero— y
  luego `concepto_id` como fallback. El nombre se normaliza con `lower()` sin
  `strip`, «Otros Pagos» conserva su forma irregular y el filtro de anulados
  continúa siendo exacto.

## Riesgos

- Un reporte financiero puede parecer equivalente y aun cambiar importes,
  filtros, nulos, redondeos u orden. La mitigación es caracterizar respuestas y
  cálculos antes de separar o agrupar consultas.
- La frontera extraída en 4.1 depende de recibir el cursor del controlador.
  Abrir una conexión dentro de ella cambiaría snapshot, tenant, timeouts,
  conteo de consultas y lifecycle; las pruebas de caracterización protegen esa
  propiedad.
- Una consulta agrupada puede romper permisos, ownership o aislamiento entre
  tenants aunque reduzca el número de consultas. La equivalencia debe incluir
  esos límites, no solo los totales.
- El conteo fijo de 15 presupone, como la caracterización de 4.0, la existencia
  de las tablas opcionales de aplicaciones y valores personalizados. En schemas
  parciales puede bajar a 14 o 13, pero permanece independiente de `N`.
- Valores de `tipo_pago` que solo difieren en mayúsculas o minúsculas continúan
  colisionando al convertirse con `lower()` en Python. Ni el SQL heredado ni el
  agrupado definen un `ORDER BY`, por lo que cuál valor prevalece ya era
  indeterminado; 4.2 conserva esa rareza y no la corrige.
- `DB_STATEMENT_TIMEOUT_MS` tiene ya evidencia no productiva y cancelación real,
  pero el valor final sigue sin calibrar contra un schema equivalente, volumen
  financiero representativo y el deadline HTTP externo.
- El timeout por sentencia no limita un endpoint entero: el camino medido de
  229 consultas tardó hasta 16,371 s aunque ninguna sentencia llegó a 143 ms.
  La mitigación primaria es eliminar el N+1, no aumentar el timeout.
- La rama de prueba carece de `pagos.concepto_id` en ambos tenants. El endpoint
  de estado de cuenta financiero conserva hoy un fallback silencioso a lista
  vacía; no se corrige ni se toma esa rama como staging equivalente.
- La credencial compartida puede crear objetos y roles. Aunque la sonda forzó
  READ ONLY, debe rotarse y sustituirse por un rol dedicado antes de repetirla.
- No hay evidencia de GitHub Actions para los cambios posteriores a la capa 0.
  Las verificaciones locales no se presentarán como CI remota.
- La capa 3 repuso claves foráneas en `tenant_2005`. Si el inventario descubre
  que algún reporte inserta o borra, puede encontrar restricciones que antes no
  existían; se documentará el comportamiento y no se cambiarán las claves por
  inferencia.
- `EXPLAIN ANALYZE` ejecuta la consulta. Debe usarse solo en un entorno no
  productivo confirmado y con datos adecuados; nunca contra producción.

## Registro de ejecución

### 2026-08-14 — activación de la capa

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`.
- Autorización: orden explícita del usuario para corregir la continuidad
  documental y activar la capa 4. La decisión mantiene pendientes y acepta el
  riesgo de `DB_STATEMENT_TIMEOUT_MS` sin calibrar y de la CI remota sin
  evidencia posterior a la capa 0.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio; `HEAD` y la referencia local
  `origin/main` en `46fad2c4c12482830cc58ac28ea2512f96155fb8`.
- Continuidad: el base de la capa 3,
  `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, existe y es ancestro de `HEAD`.
  Sus 13 commits posteriores forman una historia lineal y todos están
  explicados en la bitácora cerrada.
- Archivos creados o modificados: esta bitácora,
  `docs/modularizacion/README.md`,
  `docs/modularizacion/03_MIGRACIONES_TENANTS.md` y
  `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Correcciones de continuidad: el control de la capa 3 deja de señalar 3.5 como
  pendiente, el recuento pasa de 11 a 13 commits, el índice registra como
  resueltos la verificación manual y los dos puntos abiertos, y se retira la
  autorización puntual ya consumida.
- Código de producto, pruebas, consultas, configuración, dependencias y
  workflow inspeccionados o modificados: **ninguno**.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git status --short --branch`,
  `git branch --show-current`, `git rev-parse HEAD`,
  `git rev-parse --verify origin/main`, `git merge-base --is-ancestor` y
  `git log --reverse` desde el base de la capa 3; todos con resultado coherente
  con la activación.
- Verificación documental: `git diff --check` en exit 0; el chequeo equivalente
  del archivo nuevo no reportó errores de whitespace; `git status --short`
  contiene exclusivamente los cuatro documentos declarados; el índice marca
  exactamente una capa activa; y el diff completo fue revisado como
  exclusivamente documental.
- Evidencia remota: no se consultó ni se atribuye ningún run de GitHub Actions.
- Estado al cerrar el turno de activación: capa 4 **activa**; 4.0 **pendiente y
  no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 4.0 conforme al trabajo exacto
  anterior y detenerse antes de la siguiente subcapa.

### 2026-08-14 — cierre de 4.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; no se usó GitHub para inferir
  estado local.
- Precondición Git: rama `main`, árbol limpio, `HEAD`
  `5f62e3df1724210db4058706929980fa9f4463d1`, un commit por delante de la
  referencia local `origin/main`. El único commit posterior al base de capa 4
  es la activación documental y está explicado por esta bitácora.
- Inventario dirigido: `app/routes/reportes.py`, `cuentas.py`, `cartera.py`;
  sus controladores; `app/services/cobros.py`, `cartera.py` y
  `asignacion_academica.py` solo como dependencias directas; pruebas y
  documentación de esos caminos. No se leyó historia global ni código de la
  capa 5 fuera del consumo mínimo ya presente.
- Caracterización añadida: `tests/test_reportes_query_counts.py`, diez casos
  para la frontera HTTP/admin/threadpool y los conteos `10 + 5N`, `1 + 12N` y
  cartera constante. Código de producto y configuración modificados: **ninguno**.
- Pruebas específicas: 31 pasaron en 0,48 s. La prueba nueva aislada: 10 pasaron
  en 0,49 s. Ruff del archivo nuevo: correcto.
- Compuerta global final: 585 pruebas pasaron en 1,91 s; 5 warnings heredadas;
  Ruff correcto; `pip check` sin dependencias rotas; exit 0. Un primer intento
  dentro del sandbox encontró 29 errores de permisos al enumerar el directorio
  temporal de pytest; la misma compuerta fuera del sandbox pasó y el artefacto
  temporal exacto fue eliminado.
- Diff final: `git diff --check` en exit 0. El alcance contiene únicamente esta
  bitácora, el índice, el prompt de continuidad y
  `tests/test_reportes_query_counts.py`; el diff completo fue revisado como
  exclusivo de 4.0.
- PostgreSQL: conexión únicamente a la rama de prueba indicada por el usuario,
  mediante transacciones forzadas READ ONLY y endpoint directo distinto del
  configurado localmente. No hubo DDL, DML, migraciones ni acceso al host de
  producción configurado. Se ejecutaron `SELECT`, `SHOW`, `set_config` local,
  una cancelación deliberada de `pg_sleep` y `EXPLAIN ANALYZE` de lecturas.
- Secretos y datos: la URI no se guardó ni se imprimió; la sonda efímera fue
  eliminada y una búsqueda dirigida no encontró la credencial ni el host en el
  repositorio. No se imprimieron filas, IDs ni planes completos.
- Resultado del timeout: el servidor parte de `statement_timeout=0`; la
  aplicación continúa aplicando 30000 ms por transacción; la cancelación a 1000
  ms produjo SQLSTATE `57014` tras 1,114 s. Candidato documentado: 15000 ms,
  **no aplicado**; la calibración operativa sigue pendiente por las limitaciones
  del conjunto.
- Resultado SQL: la línea base hermética confirma el N+1 y la rama real muestra
  229 consultas para 19 estudiantes frente a 12 consultas agrupadas de cartera.
  El estado de cuenta financiero no se pudo medir por la ausencia estructural
  de `pagos.concepto_id`; no se alteró la base ni el código para encubrirlo.
- Commit, push, deploy, cambio de variables remotas y acceso a producción:
  **ninguno**. GitHub Actions posterior a la capa 0 continúa sin evidencia.
- Estado: 4.0 **cerrada**; 4.1 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar solo 4.1, extracción de persistencia de los
  reportes simples, y detenerse antes de 4.2.

### 2026-08-14 — cierre de 4.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git fue validado directamente
  y no se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, árbol inicialmente limpio, `HEAD`
  `5a55b8637f62ffa3df327adb186f26d7542f967c`, dos commits por delante de la
  referencia local `origin/main`. El commit base
  `46fad2c4c12482830cc58ac28ea2512f96155fb8` existe y es ancestro; los dos
  commits posteriores corresponden a la activación y al cierre de 4.0, ambos
  explicados en esta bitácora.
- Alcance inspeccionado y modificado: únicamente reporte general, ingresos por
  mes/rango y egresos por rango, sus pruebas y continuidad documental. No se
  inspeccionó ni inició el estado de cuenta de 4.2.
- Archivos de producto: `app/controllers/reportes_controller.py` y el nuevo
  `app/repositories/reportes_repository.py`. Prueba nueva:
  `tests/test_reportes_simple_controllers.py`. Continuidad actualizada: esta
  bitácora, `docs/modularizacion/README.md` y
  `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Caracterización previa: antes de mover producto,
  `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
  tests\test_reportes_simple_controllers.py` terminó con 12 pruebas pasadas;
  Ruff del archivo nuevo terminó correcto.
- Implementación: cuatro funciones reciben el cursor existente y devuelven
  filas crudas. El controlador continúa abriendo y cerrando conexión/cursor,
  formateando respuestas y conservando los mismos `try/except/finally` y
  fallbacks.
- Contratos conservados: payloads, lista frente a sobre paginado, nulos,
  formatos de fecha, anulación, orden, parámetros y conteos de consultas
  4/1-2/1-2/1-2. Un comparador AST contra
  `git show HEAD:app/controllers/reportes_controller.py` confirmó 13 consultas
  antes y después, sin diferencias byte por byte.
- Pruebas específicas finales:
  `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
  tests\test_reportes_simple_controllers.py tests\test_reportes_pagination.py
  tests\test_anulaciones_financieras.py tests\test_reportes_query_counts.py`;
  **47 pasaron** en 0,51 s.
- Ruff del alcance:
  `.\venv\Scripts\python.exe -m ruff check
  app\controllers\reportes_controller.py
  app\repositories\reportes_repository.py
  tests\test_reportes_simple_controllers.py`; resultado **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **598 pruebas pasaron** en 1,81 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. Un primer intento dentro del sandbox encontró
  29 errores de permiso en el directorio temporal de pytest; se repitió fuera
  del sandbox sin red ni base de datos y pasó.
- Revisión final: `git diff --check` en exit 0; los chequeos equivalentes
  `git diff --no-index --check` de los dos archivos nuevos no emitieron errores
  de whitespace. El diff es exclusivo de los seis archivos declarados. No
  hubo cambios en rutas, estado de cuenta, cartera, cobros, pagos,
  configuración, timeouts ni dependencias.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 4.1 **cerrada**; 4.2 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 4.2 y detenerse antes de 4.3.

### 2026-08-14 — cierre de 4.2

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git fue validado directamente
  y no se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, árbol inicialmente limpio, `HEAD`
  `5f9035d565c8b6366b9d6674db439d1d4c0e5cd6`, tres commits por delante de la
  referencia local `origin/main`. El commit base
  `46fad2c4c12482830cc58ac28ea2512f96155fb8` existe y es ancestro; los tres
  commits posteriores corresponden a la activación, el cierre de 4.0 y el
  cierre de 4.1, todos explicados en esta bitácora.
- Alcance inspeccionado: únicamente
  `/reportes/estado-cuenta/{curso_id}`, su controlador, las funciones de cobros
  que consume, la persistencia y pruebas directas. No se inspeccionó ni inició
  4.3.
- Línea base específica antes del cambio:
  `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
  tests\test_reportes_query_counts.py tests\test_reportes_pagination.py
  tests\test_pagos_adelantados.py::test_reporte_curso_aplica_solo_adelantos_maduros_y_no_los_duplica`;
  **29 pasaron** en 0,47 s.
- Caracterización previa: se creó
  `tests/test_reportes_estado_cuenta.py` antes de modificar producto. Sus cuatro
  casos iniciales pasaron en 0,18 s y Ruff terminó correcto. La revisión final
  amplió el archivo a seis casos para fijar también que no se reutilizan los
  mapas no equivalentes del helper masivo, los predicados agrupados, nombres sin
  `strip` y la rama sin tabla de aplicaciones.
- Producto modificado: `app/controllers/reportes_controller.py` y
  `app/repositories/reportes_repository.py`. Pruebas modificadas:
  `tests/test_reportes_query_counts.py`, `tests/test_pagos_adelantados.py` y la
  caracterización nueva. Continuidad actualizada: esta bitácora,
  `docs/modularizacion/README.md` y
  `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Implementación: dos agregados de pagos y uno de «Otros Pagos» leen todos los
  estudiantes con parámetros `(estudiante_ids,)`; el helper plural existente
  carga los valores personalizados. El controlador arma mapas aislados por
  estudiante y conserva la aplicación madura, precedencias, cálculos, forma de
  respuesta, conexión, cursor, fallback y cierres.
- Medición hermética: para 0/1/3 estudiantes con las tablas opcionales presentes,
  el conteo pasó de **6/15/25** a **6/15/15**. El nuevo valor es fijo para
  `N > 0`; no se presenta como equivalencia real contra la rama Neon anterior,
  que carecía de `pagos.concepto_id`.
- Pruebas específicas finales:
  `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
  tests\test_reportes_estado_cuenta.py tests\test_reportes_query_counts.py
  tests\test_reportes_pagination.py tests\test_pagos_adelantados.py
  tests\test_anulaciones_financieras.py tests\test_reportes_simple_controllers.py`;
  **65 pasaron** en 0,64 s.
- Ruff del alcance:
  `.\venv\Scripts\python.exe -m ruff check
  app\controllers\reportes_controller.py
  app\repositories\reportes_repository.py
  tests\test_reportes_estado_cuenta.py tests\test_reportes_query_counts.py
  tests\test_pagos_adelantados.py`; resultado **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **604 pruebas pasaron** en 2,30 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. Un primer intento dentro del sandbox dejó 575
  pruebas pasadas y 29 errores de permiso en el directorio temporal de pytest;
  se repitió fuera del sandbox, sin red ni base de datos, y pasó.
- Incidente de continuidad: durante el trabajo apareció una modificación no
  solicitada que devolvía `PROMPT_CONTINUACION.md` a un estado obsoleto. Se
  pausó; los tres revisores confirmaron no haberlo editado y el usuario autorizó
  explícitamente restaurar solo ese archivo desde `HEAD`. Se restauró, se
  comprobó que no quedara diff y únicamente después se actualizó de forma
  intencional con el cierre de 4.2.
- Revisión final: `git diff --check` terminó en exit 0 y el chequeo equivalente
  del archivo nuevo no emitió errores de whitespace. El diff pertenece solo a
  los ocho archivos declarados. No hubo cambios en rutas, cuentas, cartera,
  pagos, configuración, timeouts ni dependencias.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 4.2 **cerrada**; 4.3 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 4.3 y, por ser la última
  subcapa, aplicar su compuerta de cierre sin activar la capa 5.

## Entrega al próximo chat

- Capa activa: **4, reportes financieros**.
- Última subcapa terminada: **4.2**, eliminación agrupada del `5N` de
  `/reportes/estado-cuenta/{curso_id}`; conteo hermético 6 para curso vacío y 15
  fijo para `N > 0`.
- Primera subcapa pendiente: **4.3**, separación final de reglas y cierre de
  medición/retirada heredada.
- Commit base: `46fad2c4c12482830cc58ac28ea2512f96155fb8`, rama `main`.
- Riesgos abiertos: candidato de timeout 15000 ms no aplicado; rama de prueba no
  equivalente por ausencia de `pagos.concepto_id`; credencial privilegiada por
  rotar; colisión heredada de nombres que solo difieren en mayúsculas; evidencia
  de GitHub Actions posterior a la capa 0 aún ausente.
- Precondición antes de 4.3: el usuario debe revisar y dejar limpio este cambio;
  después se reaudita todo commit posterior al base.
- Siguiente acción exacta: ejecutar únicamente el trabajo exacto de 4.3, cerrar
  la capa 4 solo si pasa su compuerta y dejar la capa 5 en espera.
