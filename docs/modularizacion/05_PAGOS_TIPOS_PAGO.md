# Capa 5: pagos y tipos de pago

Última revisión: 2026-08-15.

## Control

- Estado: **Activa** desde el 2026-08-15.
- Commit base: `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`, que el reflog registra como publicada por push el 2026-08-15 a
  las 13:20:16.
- Primera subcapa pendiente: **5.3, no iniciada**. 5.0, 5.1 y 5.2 quedaron
  **cerradas** el 2026-08-15.
- Código de producto modificado hasta ahora: `app/controllers/pagos_controller.py`
  y `app/repositories/pagos_repository.py`, en 5.1 y 5.2. Sin cambios en rutas,
  payloads, status codes, permisos, tenant, ownership, transacciones ni SQL
  observable.
- Autorización: orden explícita del usuario el 2026-08-15 para corregir la
  continuidad documental de la capa 4 y activar la capa 5, aceptando que las
  verificaciones heredadas sigan pendientes. La activación **no** autoriza
  inspeccionar código de la capa 5 ni iniciar 5.0 en ese mismo turno.

## Objetivo

Modularizar y proteger el dominio financiero de pagos y tipos de pago, segundo
por criticidad después de reportes. El resultado debe proteger montos, saldos,
comprobantes, idempotencia y transacciones, y conservar los contratos del
frontend y de la base de datos.

El objetivo procede exclusivamente del índice maestro. La activación no
inspeccionó el código y por eso no afirma todavía qué endpoints, archivos,
consultas, escrituras o pruebas forman el dominio. Esa determinación es trabajo
de 5.0.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último cierre
  local registrado, correspondiente a la capa 4, terminó en exit 0 con 606
  pruebas, Ruff correcto y `pip check` íntegro; no se reprodujo durante esta
  activación documental.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  El valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una nueva auditoría.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—, ambos con 37 claves foráneas, 30 secuencias propias y 30
  migraciones registradas.
- Contratos de **lectura** de `pagos` fijados por la capa 4 y protegidos por su
  caracterización. Cambiar cómo se escriben esos datos puede romperlos.
- La última evidencia de GitHub Actions corresponde a la capa 0. Hubo un push
  autorizado el 2026-08-15, pero **no se ha obtenido evidencia del run**
  asociado; esa verificación permanece **pendiente y aceptada**. No se atribuye
  CI remota por el solo hecho de que `HEAD` coincida con `origin/main`.

## Perfil de riesgo propio de esta capa

Esta capa escribe donde las anteriores solo leían, y eso cambia el perfil de
riesgo respecto a la capa 4:

- La capa 3 repuso 26 claves foráneas en `tenant_2005`. Inserciones y borrados
  pueden fallar ahora donde antes pasaban en silencio.
- La capa 4 fijó los contratos de lectura de `pagos`. Cualquier cambio en la
  escritura debe demostrar que esos contratos siguen intactos.
- `pagos.concepto_id` **no existe** en el schema. El concepto vive en
  `pagos.descripcion`, el medio de pago en `pagos.tipo_pago`, y las aplicaciones
  enlazan el catálogo por `pagos_aplicaciones.tipo_pago_id`. El ID lógico de
  concepto es `tipos_de_pagos.id`.

## Alcance autorizado

- Inventariar las entradas HTTP, reglas, escrituras, consultas, pruebas y
  consumidores del dominio de pagos y tipos de pago mediante búsquedas
  dirigidas.
- Caracterizar antes de extraer rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, cálculos, montos, saldos, comprobantes,
  idempotencia, orden, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia, con pruebas de
  caracterización previas a cada extracción importante.
- Contar y comparar las consultas y escrituras críticas antes y después.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback` es
  preferible a una rama con datos de menores. Ninguna medición puede escribir.

## Fuera de alcance

- Asignaciones, estudiantes y el resto de dominios, que pertenecen a las capas 6
  y 7, salvo la lectura mínima indispensable para caracterizar un contrato
  consumido por pagos.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas
  financieras, redondeos, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM o el driver.
- Agregar funciones de producto, rediseñar respuestas o corregir defectos ajenos
  a la primera subcapa pendiente. El trabajo registrado como disponible en
  `PROMPT_CONTINUACION.md` no entra por inferencia.
- Crear abstracciones compartidas sin dos usos reales comprobados.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Importes, saldos, comprobantes, filtros, agrupaciones, orden, nulos y
  redondeos conservan su resultado actual.
- La idempotencia observable de las escrituras se conserva: una operación no
  puede pasar a duplicar ni a rechazar donde antes no lo hacía.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de lectura de `pagos` fijados por la capa 4 siguen pasando su
  caracterización, incluidos los conteos 6/15 del estado de cuenta de reportes,
  1/13/37 de cuentas y 5/12/12 de cartera.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.

## Línea base registrada en 5.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_pagos_escrituras_caracterizacion.py tests\test_pagos_adelantados.py tests\test_pagos_historial.py tests\test_pagos_meses_vencidos.py tests\test_pagos_pagination.py tests\test_anulaciones_financieras.py tests\test_reportes_query_counts.py` | **81 pasaron** en 0,59 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **646 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La compuerta heredada de la capa 4 se reprodujo antes de tocar nada: 606
pruebas, exit 0. La suite pasó de **606 a 646** con la caracterización de 5.0.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 5.0 | Inventario, contratos, caracterización y línea base de consultas y escrituras | **Cerrada** |
| 5.1 | Extraer la persistencia de las escrituras de `pagos` sin cambiar SQL, conteos ni transacción | **Cerrada** |
| 5.2 | Completar la frontera de persistencia de `pagos_controller`: lecturas y contacto con `ventas` | **Cerrada** |
| 5.3 | Guardas de migración restantes, retiro heredado y cierre de la capa | **Pendiente, no iniciada** |

5.3 quedó definida desde lo que 5.2 dejó fuera. Las subcapas innecesarias se
marcarán `No aplica` con explicación.

Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa 5.0 — alcance ejecutado

1. Confirmar `main`, árbol limpio y que todo commit posterior al base
   `f4d091329f84bcdd100b1bf0c70c02a0e32ee138` esté explicado en esta bitácora.
2. Reproducir la compuerta heredada y determinar las pruebas específicas sin
   ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas del dominio de pagos y tipos de pago.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, persistencia, cálculos, escrituras y efectos laterales.
5. Registrar los contratos observables exactos: rutas, métodos, payloads, status
   codes, permisos, tenant, ownership, montos, saldos, comprobantes,
   idempotencia, orden, nulos, redondeos, transacciones y errores.
6. Caracterizar con pruebas los caminos que una extracción posterior pueda
   alterar, incluidas las escrituras. 5.0 no autoriza una extracción ni un
   cambio de producto.
7. Medir o instrumentar herméticamente el número de consultas y escrituras de
   los caminos críticos; no optimizarlos todavía.
8. Registrar qué contratos de lectura de la capa 4 dependen de estas escrituras
   y cómo se comprobará que siguen intactos.
9. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 5.0.
10. Actualizar esta bitácora, definir 5.1 con la evidencia obtenida y detenerse
    sin iniciarla.

## Criterios de cierre de la subcapa 5.0

- El dominio y sus consumidores están inventariados con archivos y puntos de
  entrada concretos, sin lectura global innecesaria.
- Los contratos HTTP, financieros, de seguridad, tenant, idempotencia y
  transacción están enumerados y protegidos por caracterización suficiente.
- Las escrituras críticas están identificadas con una línea base reproducible,
  no por inferencia.
- La dependencia entre estas escrituras y los contratos de lectura de la capa 4
  está registrada.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 5.0.
- La subcapa 5.1 queda definida y no iniciada.

Los siete criterios se cumplieron. El diff de 5.0 contiene **un solo archivo
nuevo** y ningún archivo rastreado modificado.

## Inventario y contratos fijados en 5.0

La frontera son **19 entradas HTTP**, todas protegidas por
`get_current_active_admin` a nivel de router y ejecutadas por FastAPI en el
threadpool. Ninguna declara `response_model` ni `status_code` explícito.

| Entrada | Contrato observable que debe conservarse |
|---|---|
| `POST /pagos` | `{mensaje, pago_id}`. `pago_id` es **int** con un pago y **lista** con varios métodos |
| `GET /pagos/vencidos/opciones/{estudiante_id}` | `{estudiante_id, opciones}` con cuotas vencidas y saldo por periodo |
| `GET /pagos/adelanto/opciones/{estudiante_id}` | `{estudiante_id, opciones}` con periodos futuros, `max_meses` y `total_disponible` |
| `POST /pagos/adelanto` | `{mensaje, pago_id, monto, descripcion, periodos}` |
| `GET /pagos/{estudiante_id}` | Lista heredada sin `limit`; con `limit`, sobre `{total,limit,offset,items}` |
| `POST /pagos/{pago_id}/anular` | `{mensaje, pago_id}` |
| `POST /tipos-pagos` | `{id, nombre, valor}` |
| `GET /tipos-pagos` | Lista `{id, nombre, valor}` ordenada por nombre |
| `PUT /tipos-pagos/{id}` | `{message}`; no toca las columnas avanzadas |
| `DELETE /tipos-pagos/{id}` | **Siempre 405**, con texto fijo. No toca la base |
| `GET /tipos-pagos/detallado` | Lista con configuración avanzada y `cursos` |
| `GET /tipos-pagos/{id}/detalle` | Tipo con `cursos`; inexistente da 404 |
| `PUT /tipos-pagos/{id}/configuracion` | `{message, tipo_pago}`; solo columnas avanzadas |
| `GET /tipos-pagos/{id}/cursos` | Lista de asignaciones; `[]` si falta la tabla puente |
| `PUT /tipos-pagos/{id}/cursos` | `{message, cursos}`; **reemplaza** el estado completo |
| `DELETE /tipos-pagos/{id}/cursos/{curso_id}` | `{message}`; inexistente da 404 |
| `GET /estudiantes/{id}/valores-pago-personalizados` | Lista con `valor`, `valor_base` y `valor_curso` |
| `PUT /estudiantes/{id}/valores-pago-personalizados/{tipo_pago_id}` | `{message, valores}` |
| `DELETE /estudiantes/{id}/valores-pago-personalizados/{tipo_pago_id}` | `{message}`; **desactiva**, no borra |

- Exactamente **ocho** entradas reciben body. Éxito normal: 200; validación
  FastAPI: 422; autenticación inválida: 401; admin o tenant no
  autorizado/suspendido: 403.
- Traducción de errores: `ValueError` → **400**;
  `MigracionPagosAdelantadosPendienteError`, `MigracionPendienteError` y
  `TipoPagoDuplicadoError` → **409**; `DELETE /tipos-pagos/{id}` → **405** fijo.
- **Rareza conservada**: siete funciones de `tipos_pagos_controller` capturan
  `Exception` a secas y devuelven `None`/`False`. Un fallo de infraestructura se
  presenta al cliente como **400 o 404**, no como 500. No se unifica.
- El orden de declaración de `pagos.py` importa: `/pagos/adelanto`,
  `/pagos/adelanto/opciones/{id}` y `/pagos/vencidos/opciones/{id}` se declaran
  **antes** que `/pagos/{estudiante_id}`, que si no las capturaría.
- Tenant por `search_path` desde el JWT. **No hay un segundo filtro de ownership**
  por estudiante, curso o pago dentro del tenant: `anular_pago_controller` recibe
  un `pago_id` y lo anula sin comprobar a qué estudiante pertenece.

### Tablas escritas y propiedad transaccional

Seis tablas reciben escritura: `pagos`, `pagos_aplicaciones`, `ventas`,
`tipos_de_pagos`, `tipos_pagos_cursos` y `tipos_pagos_estudiantes`.

- Todos los escritores abren su conexión con `get_connection()`, crean el cursor,
  hacen `commit` explícito, `rollback` en `except` y cierran cursor y conexión en
  `finally`. `historial_pagos_controller` es el único que usa `get_cursor()`.
- `historial_pagos_paginado_controller` es lector y **no** hace `commit` ni
  `rollback`; la devolución al pool revierte la transacción abierta.
- **Rareza de ciclo de vida**: `upsert_cursos_asignados` y
  `upsert_valor_personalizado_estudiante` releen el estado **después** del
  `commit` llamando a funciones que abren **su propia conexión**. Una petición
  HTTP consume por tanto **dos conexiones del pool en serie**, y la relectura
  ocurre fuera de la transacción confirmada.

### Idempotencia y concurrencia

| Camino | Protección actual |
|---|---|
| `POST /pagos` | **Ninguna.** No hay clave de idempotencia: dos envíos idénticos crean dos pagos mientras no superen la deuda |
| `POST /pagos/adelanto` | `pg_advisory_xact_lock` por `(estudiante_id, tipo_pago_id)` antes de leer disponibles y escribir |
| Cuotas dentro de `POST /pagos` | Mismo advisory lock, más el índice parcial único `uq_pagos_aplicaciones_pago_periodo_activas`, exigido antes de escribir |
| `POST /pagos/{id}/anular` | `SELECT … FOR UPDATE` sobre `pagos` y sobre `ventas` |
| `PUT /tipos-pagos/{id}/cursos` | `ON CONFLICT (tipo_pago_id, curso_id) DO UPDATE`, idempotente |
| `PUT …/valores-pago-personalizados/{tipo_pago_id}` | `ON CONFLICT (tipo_pago_id, estudiante_id) DO UPDATE`, idempotente |

Una colisión en `pagos_aplicaciones` sube como `IntegrityError` y se traduce a
`ValueError` con el mensaje «Uno de los meses seleccionados ya tiene un pago
adelantado».

## Línea base de consultas y escrituras

Medida herméticamente con el doble de 5.0. Los conteos excluyen autenticación,
`search_path` y la sentencia de timeouts de cada checkout de conexión.

| Camino | Consultas | de ellas escrituras |
|---|---:|---:|
| `POST /pagos`, pago simple | **12** | 1 |
| `POST /pagos`, dos métodos | 13 | 2 |
| `POST /pagos`, cargo de inventario | **4** | 3 |
| `POST /pagos/adelanto`, un mes | 12 | 2 |
| `POST /pagos/{id}/anular`, sin venta | 4 | 2 |
| `POST /pagos/{id}/anular`, con venta | 6 | 3 |
| `GET /pagos/adelanto/opciones/{id}` | 9 | 0 |
| `PUT /tipos-pagos/{id}/cursos`, un curso | 5 | 2 |
| `PUT …/valores-pago-personalizados/{id}` | 8 | 1 |
| `POST /tipos-pagos` | 2 | 1 |
| `DELETE …/valores-pago-personalizados/{id}` | 2 | 1 |

Lectura del resultado, sin optimizar todavía:

- **Once de las doce consultas de un pago simple son lecturas**: recalcular la
  deuda académica completa del estudiante para validar que el monto no la excede.
  Cada método adicional añade exactamente una escritura, no una lectura.
- El pago de un cargo de inventario cuesta **4** porque sale antes por la rama de
  `venta_id` y no recalcula deuda. Es la misma entrada HTTP con dos costes muy
  distintos.
- Ninguno de estos conteos depende del número de estudiantes: no hay un N+1 como
  el que corrigió la capa 4. El coste está en la profundidad por petición.

## Dependencia con los contratos de lectura de la capa 4

Lo que esta capa escribe es exactamente lo que la capa 4 lee:

- `pagos.descripcion` recibe el concepto en un pago normal, y en un pago con
  cuotas o adelanto recibe una **cadena compuesta** —`«Pension · Pago adelantado:
  Enero 2026: $100,00»`— que **no** coincide con el nombre del catálogo. Por eso
  la capa 4 excluye de sus agregados por `descripcion` y `tipo_pago` cualquier
  pago con aplicaciones y los cuenta por su lectura propia. Cambiar ese texto
  cambia el informe.
- `pagos.tipo_pago` recibe el **medio de pago**, no el concepto:
  `«Efectivo»` o `«Transferencia - Nequi»` cuando hay nota. El fallback heredado
  de la capa 4 que agrupa por `tipo_pago` solo acierta cuando un medio coincide
  por casualidad con un nombre del catálogo.
- `pagos.venta_id` decide que un pago vaya a «Otros Pagos».
- `pagos.estado = 'Anulado'` con `motivo_anulacion`, `fecha_anulacion` y
  `anulado_por` es lo que excluye el pago de todos los totales.
- **Ninguna escritura menciona `pagos.concepto_id`**, la columna inexistente que
  rompía el informe antes de la capa 4. Queda congelado por prueba.

Comprobado además que los conteos de la capa 4 siguen intactos: reportes 6/15/15,
cuentas 1/13/37 y cartera 5/12/12.

## Subcapa 5.1 — alcance ejecutado

1. Revalidar Git y limitar la inspección a las escrituras de `pagos` y
   `pagos_aplicaciones` en `pagos_controller.py`, sus pruebas y el SQL implicado.
2. Conservar la caracterización de 5.0 y ampliarla solo si una extracción
   concreta lo exige, antes de mover producto.
3. Extraer únicamente las sentencias SQL de escritura de esos dos destinos a una
   frontera de persistencia específica de pagos, siguiendo el patrón de 4.1:
   funciones que **reciben el cursor existente** y no abren, cierran, confirman
   ni revierten recursos.
4. Conservar byte por byte las cadenas SQL, sus parámetros y su orden. El
   controlador sigue siendo dueño de conexión, cursor, `commit`, `rollback`,
   cierres, advisory lock, validaciones y traducción de errores.
5. No tocar `tipos_pagos_controller`, `cobros.py`, ventas, cartera, cuentas,
   reportes, timeouts ni la base de datos. No corregir la ausencia de
   idempotencia de `POST /pagos`, las once lecturas de validación, la rareza de
   las dos conexiones ni los errores absorbidos: están registrados y pertenecen a
   una decisión posterior.
6. Verificar que los conteos de 5.0 no cambian y que los de la capa 4 siguen
   intactos.
7. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; documentar y detenerse antes de 5.2.

Los siete puntos se cumplieron. El punto 4 requirió una autorización explícita
del usuario, registrada en Decisiones: dos literales idénticos salvo sangría se
unificaron en una sola constante.

## Subcapa 5.2 — alcance ejecutado

1. Revalidar Git y limitar la inspección a lo que 5.1 dejó fuera de
   `pagos_controller.py`: las tres lecturas de `pagos` —la de bloqueo con
   `FOR UPDATE`, el historial y el historial paginado— y las cuatro sentencias
   que tocan `ventas` desde este controlador.
2. Conservar la caracterización de 5.0 y ampliarla antes de mover producto para
   los caminos que hoy no cubre: historial paginado con su `COUNT(*)` y la
   lectura de saldo de venta.
3. Decidir **con evidencia, no por inferencia**, dónde vive el contacto con
   `ventas`. Es una tabla de otro dominio escrita desde pagos: puede quedarse en
   `pagos_repository`, ir a una frontera propia o permanecer en el controlador.
   Registrar la decisión y su motivo antes de mover nada.
4. Extraer las lecturas conservando el texto SQL, sus parámetros, su orden y el
   `FOR UPDATE`. Mantener en el controlador la propiedad de conexión, cursor,
   `commit`, `rollback`, cierres y traducción de errores.
5. No tocar `tipos_pagos_controller`, `cobros.py`, cartera, cuentas, reportes,
   timeouts ni la base de datos. No corregir ninguno de los cuatro hallazgos de
   5.0.
6. Verificar que los conteos de 5.0 y de la capa 4 no cambian, y volver a
   ejecutar el comparador de SQL exigiendo conjunto idéntico.
7. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
   `git diff --check`; documentar y detenerse antes de 5.3.

Los siete puntos se cumplieron, con una **corrección de conteo** respecto a lo
que este plan anticipaba: no eran «tres lecturas de `pagos` y cuatro sentencias
que tocan `ventas`», sino **cuatro lecturas** de `pagos` y **siete puntos de
llamada** contra `ventas` sobre **seis literales**. El plan se escribió al cerrar
5.1 sin volver a contar; el inventario real de 5.2 lo corrigió antes de mover
nada.

## Primera subcapa pendiente: 5.3 — trabajo exacto

1. Revalidar Git y limitar la inspección a las **cuatro sentencias** que quedan
   inline en `pagos_controller.py`: las tres guardas de migración y bloqueo
   —`information_schema.tables`, `pg_indexes` y `pg_advisory_xact_lock`— y la
   lectura de `_periodos_disponibles` sobre `pagos_aplicaciones`.
2. Decidir **con evidencia** si esas cuatro pertenecen a la frontera de
   persistencia o deben quedarse. Las tres primeras no son consultas de dominio
   sino comprobaciones de esquema y un lock; moverlas puede ser correcto o puede
   ser ruido. Registrar la decisión y su motivo antes de mover nada.
3. Caracterizar antes de mover lo que hoy no esté cubierto, en particular
   `_periodos_disponibles`.
4. Buscar código heredado que quede probado sin consumidores tras las tres
   extracciones y retirarlo solo si se demuestra huérfano. No retirar nada por
   inferencia.
5. No tocar `tipos_pagos_controller`, `cobros.py`, `venta_controller.py`,
   cartera, cuentas, reportes, timeouts ni la base de datos. No corregir ninguno
   de los cuatro hallazgos de 5.0.
6. Verificar que los conteos de 5.0 y de la capa 4 no cambian, y volver a
   ejecutar el comparador de SQL contra el commit base de la capa exigiendo
   conjunto idéntico.
7. Al ser la última subcapa, ejecutar además la compuerta global completa,
   documentar staging, rollback y verificación manual, actualizar el índice
   maestro, marcar la capa cerrada y dejar la capa 6 en espera. **No activar la
   capa 6 sin orden explícita.**

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- HTTP, reglas, servicios y persistencia del dominio están separados con
  contratos estables.
- Montos, saldos, comprobantes, idempotencia y transacciones están protegidos
  por caracterización y conservados.
- Los contratos del frontend y de la base de datos permanecen intactos.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados; la verificación
  manual fue ejecutada o quedó aceptada explícitamente como pendiente antes del
  cierre.
- La capa 6 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- Se usa `f4d091329f84bcdd100b1bf0c70c02a0e32ee138` como commit base porque es el
  `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main` al activar. No se reutilizó ningún hash de memoria: se comprobó
  el `HEAD` real antes de registrarlo.
- El usuario eligió continuar manteniendo pendientes la calibración de
  `DB_STATEMENT_TIMEOUT_MS` y la evidencia remota de GitHub Actions. Ninguna se
  marca como cumplida y ambas conservan su riesgo.
- La activación consume la autorización puntual que `PROMPT_CONTINUACION.md`
  guardaba para la capa 5; queda retirada de ese archivo con el mismo criterio
  aplicado a las capas 3 y 4.
- El mismo turno corrigió la continuidad documental residual de la capa 4, con
  autorización explícita. Ese trabajo es exclusivamente documental y está
  registrado en `04_REPORTES_FINANCIEROS.md`.
- A diferencia de las activaciones anteriores, esta parte de un `HEAD` **ya
  publicado**. El commit base es por tanto un punto de rollback real y
  alcanzable, no solo local.
- El desglose de subcapas posteriores a 5.0 se deja explícitamente sin decidir
  para no inventar detalles de implementación antes de inspeccionar el código.
- **Unificación autorizada en 5.1.** Las dos sentencias
  `INSERT INTO pagos (estudiante_id, venta_id, …)` de la rama de métodos y de la
  rama simple eran idénticas salvo cuatro espacios de sangría, heredados de estar
  una dentro del bucle y la otra fuera. Conservar el byte a byte habría exigido
  dos constantes en el repositorio cuya única diferencia sería la sangría del
  código viejo. El usuario autorizó explícitamente unificarlas en una sola
  constante; el flujo de tokens que recibe PostgreSQL es el mismo y quedó
  verificado. Es el único cambio de texto SQL de la subcapa.
- 5.1 creó `app/repositories/pagos_repository.py` con **seis funciones** que
  cubren **ocho puntos de llamada**. Dos tienen dos consumidores reales
  —`insertar_pago` e `insertar_aplicacion`—; las otras cuatro tienen uno solo,
  pero no son abstracciones compartidas: son la sentencia concreta de su tabla.
  No se creó ningún helper genérico.
- Las funciones reciben el cursor y no abren, cierran, confirman ni revierten
  nada, igual que la frontera de 4.1. El advisory lock, las guardas de
  migración, la validación de deuda, el reparto en centavos, el
  `try/except/finally` y la traducción de `IntegrityError` siguen en el
  controlador.
- `marcar_pago_anulado` conserva su `RETURNING id` aunque el controlador no lo
  consuma. Retirarlo habría cambiado el SQL sin necesidad.
- Las sentencias que tocan `ventas` **no se movieron** en 5.1 pese a vivir en
  este controlador: son de otro dominio y su ubicación se decide en 5.2 con
  evidencia.
- 5.1 **no modificó ninguna prueba**. La caracterización de 5.0 fue suficiente
  para demostrar que payloads, conteos, transacción y ciclo de vida no cambiaron.
  Es la señal de que caracterizar antes de extraer funcionó.
- **Dónde vive el contacto con `ventas`, decidido en 5.2 con evidencia.** El
  inventario mostró que `venta_controller.py` ya escribe en `ventas` por su
  cuenta —`INSERT`, `DELETE` y un `UPDATE`— con SQL inline, y que **no existe**
  un `ventas_repository`. Crear uno tendría un solo consumidor real, porque
  migrar `venta_controller` está fuera del alcance de esta capa, y la regla del
  programa prohíbe abstracciones compartidas sin dos usos reales. Por eso las
  cinco sentencias viven en `pagos_repository.py`, en un bloque propio rotulado
  como **el efecto que un pago tiene sobre un cargo**, no como persistencia
  general de ventas. Si alguna vez existe un `ventas_repository` con dos
  consumidores, ese bloque es lo que se mueve. Alternativa descartada: dejarlas
  en el controlador, que habría dejado la frontera a medias sin ganar nada.
- La unificación autorizada en 5.1 se aplicó también en 5.2 al par
  `UPDATE ventas SET pagado = COALESCE(pagado, 0) + %s`, idéntico salvo cuatro
  espacios de sangría por la misma razón —una rama dentro del bucle y otra
  fuera—. Es el mismo caso que el usuario ya resolvió, no una decisión nueva. El
  espacio final tras el parámetro se conserva con un escape explícito, como hizo
  4.3, para no alterar el valor en tiempo de ejecución y mantener
  `git diff --check` limpio.
- 5.2 **sí amplió la caracterización antes de mover**, porque el historial
  paginado solo tenía prueba de ruta y el saldo de venta no tenía ninguna. Once
  casos nuevos se escribieron y se vieron pasar contra el producto anterior; solo
  entonces se extrajo.
- Las tres guardas de esquema y el `pg_advisory_xact_lock` **no se movieron**:
  no son consultas de dominio y su sitio se decide en 5.3.

## Riesgos

- Esta capa escribe. Un error no produce un informe equivocado sino datos
  financieros equivocados, y el rollback puede exigir reparación de información,
  no solo revertir código. Cada subcapa que toque escritura debe documentar su
  rollback de datos antes de ejecutarse.
- La idempotencia es un contrato invisible en el payload. Reintentos del
  frontend, doble clic o reenvíos pueden duplicar cobros si una extracción
  cambia el momento del `commit` o el alcance de la transacción.
- Los contratos de lectura de `pagos` fijados por la capa 4 pueden romperse
  desde el lado de la escritura sin que sus pruebas fallen, si el cambio afecta
  a datos y no a código. La mitigación es caracterizar la escritura y verificar
  los conteos y payloads heredados.
- Las 26 claves foráneas repuestas en la capa 3 pueden hacer fallar inserciones
  o borrados que antes pasaban en silencio. Se documentará el comportamiento y
  no se cambiarán las claves por inferencia.
- La asociación de pagos normales depende de texto histórico en
  `descripcion`/`tipo_pago`. Cualquier cambio de escritura que altere esos
  valores desplaza pagos hacia «Otros Pagos» en el informe de la capa 4.
- Heredado de la capa 1: `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrar contra
  volumen representativo y el deadline HTTP/proxy externo.
- Heredado de la capa 0: no hay evidencia de GitHub Actions posterior a esa
  capa. Las verificaciones locales no se presentarán como CI remota.
- Heredado de la capa 4: la credencial privilegiada compartida en chat sigue
  **sin rotar** y no debe reutilizarse.
- Heredado y latente: `app/services/reportes_financieros.py` indexa por
  `str(nombre).lower()` mientras el SQL agrupa respetando mayúsculas. Hoy hay 0
  casos en producción. No se corrige dentro de esta capa por inferencia.

### Encontrados en 5.0, registrados y sin corregir

Ninguno se corrige por inferencia: son hallazgos del inventario, no defectos de
la subcapa. Corregir cualquiera exige una decisión explícita del usuario.

- **`POST /pagos` no tiene clave de idempotencia.** Un doble clic o un reintento
  del frontend crea dos pagos mientras la suma no supere la deuda. Es el riesgo
  financiero más directo del dominio y hoy solo lo contiene la validación de
  saldo, que no distingue un reintento de un segundo pago legítimo.
- **No hay filtro de ownership dentro del tenant.** `anular_pago_controller`
  anula cualquier `pago_id` que reciba sin comprobar a qué estudiante pertenece.
  El aislamiento entre colegios sí está garantizado por `search_path`.
- **Siete funciones absorben `Exception` a secas** y devuelven `None`/`False`;
  un fallo de infraestructura llega al cliente como 400 o 404. Enmascara
  incidentes reales y una extracción podría cambiar qué queda absorbido.
- **Dos conexiones por petición** en los dos upsert de tipos de pago, con la
  relectura fuera de la transacción confirmada. Consume el doble de pool y puede
  devolver un estado distinto del que se acaba de escribir.
- **Once lecturas para validar un pago simple.** No es un N+1 —no depende del
  número de estudiantes— pero es el camino de escritura más caro y recalcula la
  deuda entera para una sola comparación.
- **`actualizar_configuracion_tipo_pago` compone SQL con f-string.** Los nombres
  de columna salen de la lista fija `_ADVANCED_COLUMNS` intersecada con el schema
  real, así que hoy **no es inyectable**. Queda anotado para que ninguna
  extracción futura abra esa lista a entrada del cliente.

## Registro de ejecución

### 2026-08-15 — activación de la capa

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local.
- Autorización: orden explícita del usuario en este turno, coincidente con la
  autorización puntual que `PROMPT_CONTINUACION.md` conservaba para la capa 5 y
  cuya condición de caducidad se cumplía. La decisión mantiene pendientes y
  acepta el riesgo de `DB_STATEMENT_TIMEOUT_MS` sin calibrar y de la CI remota
  sin evidencia posterior a la capa 0.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio; `HEAD` y la referencia local
  `origin/main` en `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`.
- Continuidad: el base de la capa 4,
  `46fad2c4c12482830cc58ac28ea2512f96155fb8`, existe y es ancestro de `HEAD`.
  Sus **siete** commits posteriores forman una historia lineal y todos están
  explicados en `04_REPORTES_FINANCIEROS.md`: activación `5f62e3d`, cierre de
  4.0 `5a55b86`, cierre de 4.1 `5f9035d`, 4.2 `5cb76d6`, 4.3 `1287021`,
  corrección de `concepto_id` `5a00f44` y cierre documental `f4d0913`.
- Estado remoto: el reflog registra `update by push` de `f4d0913` el 2026-08-15
  a las 13:20:16. El trabajo de la capa 4 está publicado. **No se consultó ni se
  atribuye ningún run de GitHub Actions**: `gh` no está disponible en este
  entorno y la evidencia del run sigue sin obtenerse.
- Ambigüedad encontrada y corregida antes de activar: el índice y la bitácora de
  la capa 4 conservaban líneas obsoletas que aún declaraban esa capa activa y
  4.3 en verificación, junto a las que la declaraban cerrada. Se informó al
  usuario, que autorizó explícitamente corregir esos residuos. El detalle está
  en `04_REPORTES_FINANCIEROS.md`.
- Archivos creados o modificados: esta bitácora,
  `docs/modularizacion/README.md`,
  `docs/modularizacion/04_REPORTES_FINANCIEROS.md` y
  `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. No se inspeccionó código del
  dominio de pagos.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git status --porcelain=v1 --branch`,
  `git branch --show-current`, `git log -1`, `git rev-parse origin/main`,
  `git merge-base --is-ancestor`, `git rev-list --count`, `git log --reverse`
  desde el base de la capa 4, `git show --stat HEAD` y
  `git reflog show origin/main`; todos con resultado coherente con la
  activación.
- Estado al cerrar el turno de activación: capa 5 **activa**; 5.0 **pendiente y
  no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 5.0 conforme al trabajo exacto
  anterior y detenerse antes de 5.1. *(Ejecutada en el turno siguiente; ver el
  cierre de 5.0 más abajo.)*

### 2026-08-15 — cierre de 5.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, árbol inicialmente limpio, `HEAD`
  `42c99600fcc895be3995ebf214827cf4a5e9433f`, un commit por delante de la
  referencia local `origin/main`. El commit base
  `f4d091329f84bcdd100b1bf0c70c02a0e32ee138` existe y es ancestro; el único
  commit posterior es la activación documental de esta capa, que modifica
  exactamente los cuatro documentos que declara. No existen instrucciones
  locales del repositorio.
- Compuerta heredada reproducida antes de tocar nada: **606 pruebas, exit 0**,
  Ruff correcto y `pip check` íntegro. Coincide con el cierre de la capa 4.
- Inventario dirigido: `app/routes/pagos.py`, `app/routes/tipos_pagos.py`,
  `app/controllers/pagos_controller.py`,
  `app/controllers/tipos_pagos_controller.py`, `app/schemas/pago.py` y, solo como
  dependencia directa ya inventariada por la capa 4, las funciones de
  `app/services/cobros.py` que consumen. No se leyó historia global ni código de
  las capas 6 y 7.
- Caracterización añadida: `tests/test_pagos_escrituras_caracterizacion.py`,
  **40 casos** sobre la frontera HTTP, el contrato transaccional de cada
  escritura, idempotencia, concurrencia, ciclo de vida y las columnas que lee la
  capa 4. Código de producto y configuración modificados: **ninguno**.
- Pruebas específicas: **81 pasaron** en 0,59 s sobre los siete archivos del
  dominio y de la capa 4. La prueba nueva aislada: 40 pasaron en 0,54 s. Ruff del
  archivo nuevo: **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **646 pruebas pasaron** en 2,05 s, 5 warnings heredadas, Ruff correcto,
  `pip check` sin dependencias rotas, exit 0. La suite pasó de 606 a 646. No hizo
  falta salir del sandbox: la restricción del directorio temporal de pytest que
  registraron las subcapas 4.x no se reprodujo en este turno.
- Medición: hermética, con un doble de cursor. Se registraron los conteos de once
  caminos. Tres del inventario no se midieron con el doble actual —historial
  paginado, listado simple de tipos de pago y un pago con cuotas vencidas
  reales— porque exigen fixtures de fila que 5.0 no necesitaba; queda anotado.
- Diff final: `git diff --check` en exit 0 y el chequeo equivalente del archivo
  nuevo sin diagnósticos de whitespace. El alcance es **un solo archivo nuevo** y
  **ningún archivo rastreado modificado**: no se tocó producto, rutas, payloads,
  status codes, permisos, tenant, ownership, SQL, transacciones, configuración ni
  dependencias.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 5.0 **cerrada**; 5.1 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 5.1, extracción de la persistencia
  de las escrituras de `pagos`, y detenerse antes de 5.2. *(Ejecutada en el turno
  siguiente; ver el cierre de 5.1 más abajo.)*

### 2026-08-15 — cierre de 5.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, árbol inicialmente limpio, `HEAD`
  `7718c3758646abe396c3c0d5bbcf1ba6535a53b4`, dos commits por delante de la
  referencia local `origin/main`. El commit base `f4d0913` existe y es ancestro;
  los dos commits posteriores son la activación de la capa y el cierre de 5.0,
  ambos explicados en esta bitácora. El segundo modifica exactamente los tres
  archivos que declaró.
- Alcance inspeccionado y modificado: únicamente las escrituras de `pagos` y
  `pagos_aplicaciones` de `pagos_controller.py`. No se inspeccionó
  `tipos_pagos_controller`, cartera, cuentas ni reportes.
- Archivos de producto: `app/controllers/pagos_controller.py` y el nuevo
  `app/repositories/pagos_repository.py`. **Pruebas modificadas: ninguna.**
- Autorización previa: el usuario decidió explícitamente unificar los dos
  literales `INSERT INTO pagos` que solo diferían en sangría, tras exponerle las
  tres opciones. Sin esa autorización la subcapa se habría detenido.
- Implementación: seis funciones que reciben el cursor existente cubren los ocho
  puntos de llamada de escritura. El controlador pasó de **717 a 701 líneas** y
  ya no contiene SQL de escritura contra esas dos tablas.
- Equivalencia SQL verificada con un comparador AST contra
  `git show HEAD:app/controllers/pagos_controller.py`: **19 sentencias distintas
  antes y 19 después, conjunto idéntico**, ninguna perdida y ninguna nueva.
  **20 de 21** literales distintos se conservan **byte a byte**; el único
  reindentado es el `INSERT INTO pagos` autorizado. Dos sentencias pasaron de dos
  puntos de llamada a una constante compartida.
- Conteos conservados: pago simple 12, dos métodos 13, cargo de inventario 4,
  adelanto 12, anulación 4 y 6. De la capa 4, reportes 6/15/15, cuentas 1/13/37 y
  cartera 5/12/12. Todos los verifica la caracterización de 5.0 sin cambios.
- Pruebas específicas:
  `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
  tests\test_pagos_escrituras_caracterizacion.py tests\test_pagos_adelantados.py
  tests\test_pagos_historial.py tests\test_pagos_meses_vencidos.py
  tests\test_pagos_pagination.py tests\test_anulaciones_financieras.py
  tests\test_reportes_query_counts.py`; **81 pasaron** en 0,61 s, el mismo
  resultado que antes de extraer.
- Ruff del alcance:
  `.\venv\Scripts\python.exe -m ruff check app\controllers\pagos_controller.py
  app\repositories\pagos_repository.py`; **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **646 pruebas pasaron** en 2,10 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. El total no cambia porque 5.1 no añadió pruebas.
- Revisión final: `git diff --check` en exit 0 y el chequeo equivalente del
  archivo nuevo sin diagnósticos de whitespace. El diff contiene exactamente dos
  archivos de producto. No hubo cambios en rutas, payloads, status codes,
  permisos, tenant, ownership, transacciones, timeouts, dependencias ni
  configuración.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 5.1 **cerrada**; 5.2 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 5.2 y detenerse antes de 5.3.
  *(Ejecutada en el turno siguiente; ver el cierre de 5.2 más abajo.)*

### 2026-08-15 — cierre de 5.2

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y no
  se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, árbol inicialmente limpio, `HEAD`
  `ebc1bd8ac46794d12314bdf7cc457527e565f9ee`, tres commits por delante de la
  referencia local `origin/main`. El commit base `f4d0913` existe y es ancestro;
  los tres commits posteriores son la activación, el cierre de 5.0 y el cierre de
  5.1, todos explicados en esta bitácora. El tercero modifica exactamente los
  cuatro archivos que declaró.
- Corrección del plan: 5.1 había anticipado «tres lecturas de `pagos` y cuatro
  sentencias contra `ventas`». El inventario real dio **cuatro lecturas** y
  **siete puntos de llamada sobre seis literales**. Se corrigió antes de mover
  nada; el plan se había escrito sin volver a contar.
- Decisión con evidencia sobre `ventas`: registrada en Decisiones. `ventas` se
  queda en `pagos_repository.py`, en un bloque rotulado, porque
  `venta_controller.py` ya tiene su propio SQL inline, no existe
  `ventas_repository` y crear uno tendría un solo consumidor real.
- Caracterización añadida **antes** de mover producto:
  `tests/test_pagos_escrituras_caracterizacion.py` pasó de 40 a **51 casos**. Los
  once nuevos cubren el historial paginado con su `COUNT(*)`, sus parámetros,
  orden y ciclo de vida; la lectura de saldo de venta y sus tres rechazos; el
  abono que no cierra la venta; el orden `FOR UPDATE` antes del `UPDATE`; las
  cinco columnas de la lectura de bloqueo; y la recuperación de `venta_id` desde
  el texto `Cargo #N`. Se vieron pasar contra el producto anterior.
- Archivos de producto: `app/controllers/pagos_controller.py` y
  `app/repositories/pagos_repository.py`. Pruebas modificadas:
  `tests/test_pagos_escrituras_caracterizacion.py`.
- Implementación: **nueve funciones nuevas** en el repositorio, cuatro de lectura
  de `pagos` y cinco del efecto sobre `ventas`, todas recibiendo el cursor. El
  repositorio pasa a **15 funciones**. El controlador bajó de **701 a 644
  líneas**; desde el base de la capa, de **717 a 644**.
- Equivalencia SQL verificada con un comparador AST **contra el commit base de la
  capa**, `f4d0913`, no solo contra el turno anterior: **19 sentencias distintas
  antes y 19 después, conjunto idéntico**, ninguna perdida y ninguna nueva.
  **19 de 21** literales distintos conservados **byte a byte**; los dos
  reindentados son el `INSERT INTO pagos` de 5.1 y el
  `UPDATE ventas SET pagado` de 5.2, ambos por la misma unificación autorizada.
  Cuatro literales duplicados pasaron a una constante compartida sin cambiar el
  número de `execute()` en tiempo de ejecución.
- SQL que queda inline en el controlador: **cuatro sentencias**, las tres guardas
  de esquema y bloqueo y la lectura de `_periodos_disponibles`.
- Conteos conservados: pago simple 12, dos métodos 13, cargo de inventario 4,
  adelanto 12, anulación 4 y 6, historial paginado 2. De la capa 4, reportes
  6/15/15, cuentas 1/13/37 y cartera 5/12/12.
- Pruebas específicas: **92 pasaron** en 0,59 s sobre los siete archivos del
  dominio y de la capa 4.
- Ruff del alcance: `app\controllers\pagos_controller.py`,
  `app\repositories\pagos_repository.py` y la prueba modificada; **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **657 pruebas pasaron** en 2,14 s, 5 warnings heredadas, Ruff correcto,
  `pip check` íntegro y exit 0. La suite pasó de 646 a 657.
- Revisión final: `git diff --check` en exit 0, incluido el espacio final
  conservado con escape explícito. El diff contiene tres archivos. No hubo
  cambios en rutas, payloads, status codes, permisos, tenant, ownership,
  transacciones, timeouts, dependencias ni configuración.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
- Estado: 5.2 **cerrada**; 5.3 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 5.3 y, por ser la última subcapa,
  aplicar su compuerta de cierre sin activar la capa 6.

## Entrega al próximo chat

- Capa activa: **5, pagos y tipos de pago**.
- Última subcapa terminada: **5.2**. Primera subcapa pendiente: **5.3, guardas
  de migración restantes, retiro heredado y cierre de la capa**.
- Commit base: `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`, rama `main`, ya
  publicado. Al cerrar 5.2, `HEAD` es `ebc1bd8` más tres archivos sin commitear.
- Bloqueos: ninguno para iniciar 5.3.
- Precondición antes de continuar: el usuario debe revisar y dejar limpio el
  cambio de 5.2; después se reaudita todo commit posterior al base.
- Lo que 5.1 y 5.2 dejaron decidido y no debe rehacerse: la persistencia de
  `pagos`, `pagos_aplicaciones` y el efecto sobre `ventas` vive en
  `app/repositories/pagos_repository.py`, quince funciones que reciben el cursor.
  El controlador conserva conexión, cursor, `commit`, `rollback`, advisory lock,
  validaciones y traducción de errores. Solo quedan inline las tres guardas de
  esquema y la lectura de `_periodos_disponibles`.
- **5.3 es la última subcapa**: además de su trabajo debe ejecutar la compuerta
  global, documentar staging, rollback y verificación manual, actualizar el
  índice maestro, cerrar la capa y dejar la capa 6 en espera.
- Lo que 5.0 dejó medido: 19 entradas HTTP, seis tablas escritas, 40 pruebas de
  caracterización y los conteos de once caminos. Un pago simple cuesta **12
  consultas, once de ellas lecturas de validación**; un cargo de inventario
  cuesta **4**. No hay N+1 en este dominio.
- Hallazgos registrados y **sin corregir**: `POST /pagos` no es idempotente, no
  hay filtro de ownership por pago dentro del tenant, siete funciones absorben
  `Exception` y devuelven 400/404, y los dos upsert de tipos de pago abren dos
  conexiones por petición.
- Verificaciones heredadas pendientes y aceptadas: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub Actions posterior a
  la capa 0. Además, la credencial privilegiada compartida en la capa 4 sigue
  sin rotar.
- Lo que esta capa debe recordar antes de tocar nada: **escribe donde las
  anteriores solo leían**. Claves foráneas repuestas en la capa 3, contratos de
  lectura de `pagos` fijados en la capa 4, y `pagos.concepto_id` inexistente.
- Siguiente acción exacta: ejecutar solo 5.3, que es la última subcapa, y
  aplicar su compuerta de cierre sin activar la capa 6.
