# Capa 7: notas

Última revisión: 2026-08-19.

## Control

- Estado: **Activa** desde el 2026-08-19.
- Commit base: `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.1**, la extracción de la persistencia. La
  subcapa **7.0 quedó cerrada** el 2026-08-19.
- Código de producto modificado al activar: **ninguno**. Tampoco en 7.0: su diff
  es **un solo archivo de prueba nuevo** y ningún archivo rastreado modificado,
  igual que los de 5.0, 6.0 y 7.0 de dashboard.
- Dominio de esta capa: **notas, y solo ese**. La capa 7 del índice es «resto de
  dominios» y ordena expresamente **priorizar uno a la vez**, así que esta
  bitácora cubre un único dominio. Los demás quedan fuera y necesitarán su
  propia bitácora y su propia orden.
- Autorización: orden explícita del usuario el 2026-08-19. **El dominio lo
  nombró el usuario**, después de que se le explicara qué es un dominio en este
  programa, qué dominios quedaban en espera y qué implica activarlo. No se
  dedujo por inferencia.
- La autorización permite **solamente la activación documental**. No autoriza
  inspeccionar código del dominio, implementar 7.0, tocar la base de datos,
  hacer deploy, commit ni push.

### Relación con la bitácora de `dashboard`

`07_DASHBOARD.md` es la bitácora **cerrada** del primer dominio migrado bajo la
capa 7. Esta es la segunda, y es **independiente**: su commit base, sus
subcapas, su compuerta y su cierre son propios. Cerrar `notas` no reabre
`dashboard` ni al revés.

**Las subcapas se numeran por bitácora**, así que esta capa vuelve a empezar en
**7.0**. Existe por tanto una «7.0 de dashboard», ya cerrada, y una «7.0 de
notas», que es la pendiente. En prosa deben citarse siempre con el nombre del
dominio; el número solo no identifica una subcapa. Alternativa descartada:
renumerar como 8.x, que habría inventado una capa que el índice maestro no
define.

## Objetivo

Migrar el dominio de **notas** con contratos y pruebas, conservando su
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

## Diferencia de perfil respecto a `dashboard`

`dashboard` resultó ser un dominio de **solo lectura**: cero tablas escritas,
cero transacciones propias, cero `commit` y cero `rollback`. Eso hizo que su
rollback fuera puramente de código y que la extracción fuera de bajo riesgo.

**Confirmado en 7.0: `notas` escribe.** `POST /notas` inserta en `notas_detalle`
dentro de `get_cursor(commit=True)`. Es **la única entrada que escribe**, **la
única tabla escrita** y **la única transacción propia** del dominio; no hay
ningún `UPDATE` ni `DELETE`.

El perfil de riesgo de esta capa es por tanto **el de la capa 5, no el de
dashboard**:

- hay una transacción propia que conservar, con su dueño de `commit`;
- las **26 claves foráneas repuestas por la capa 3** pueden hacer fallar
  inserciones que antes pasaban en silencio, y `notas_detalle` fue **una de las
  ocho tablas averiadas** que esa capa reparó;
- el rollback de esta capa **ya no puede declararse «puramente de código»** sin
  comprobarlo, a diferencia de las capas 5, 6 y 7 para dashboard.

La contrapartida es que la escritura es **una sola sentencia, un solo `INSERT`
sin `RETURNING` leído fuera de la transacción**, así que la extracción es más
simple que la de pagos. Lo delicado de este dominio no resultó ser la escritura
sino **el contrato HTTP que la envuelve**: ver los hallazgos de 7.0.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último
  resultado registrado, al cerrar la capa 7 para `dashboard`, es **756 pruebas,
  exit 0**, Ruff correcto y `pip check` íntegro; **no se reprodujo durante esta
  activación documental**. 7.0 debe reproducirlo antes de tocar nada.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  El valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una auditoría propia. Sobre
  `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` pesa el pendiente del
  2026-08-17: se quedó sin ejemplo real que la respalde y se conserva como
  margen. La capa 7 para dashboard encontró un camino de **cuatro conexiones en
  serie sin anidamiento**, que es evidencia relevante y quedó registrada sin
  actuar.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—, ambos con 37 claves foráneas, 30 secuencias propias y 30
  migraciones registradas.
- **Dato de la capa 3 que afecta directamente a este dominio**: `notas_detalle`
  fue **una de las ocho tablas averiadas** de `tenant_2005` que no podían
  insertar, porque tomaban su `id` de secuencias alojadas en el schema de
  demostración y ya agotadas. Quedó reparada, con secuencia propia posicionada
  en su `MAX(id)` real. Además la capa 3 **repuso 26 claves foráneas ausentes**
  en ese tenant. Si `notas` escribe, ambas cosas son parte de su perfil de
  riesgo: una inserción que antes pasaba en silencio puede fallar hoy.
- Contratos de lectura financieros fijados por la capa 4 y protegidos por su
  caracterización, con los conteos 6/15 del estado de cuenta de reportes,
  1/13/37 de cuentas y 5/12/12 de cartera. Dependen de `cobros.py`.
- Frontera de persistencia de pagos establecida en la capa 5:
  `app/repositories/pagos_repository.py` con 16 funciones que reciben el cursor.
- Frontera de persistencia de asignaciones y estudiantes establecida en la capa
  6: `estudiantes_repository` con 11 funciones y `asignaciones_repository` con
  33.
- Frontera de persistencia de dashboard establecida en la capa 7 para ese
  dominio: `dashboard_repository` con 8 funciones y dos fragmentos privados.
  Todos los repositorios comparten el mismo patrón —funciones que **reciben el
  cursor existente** y no abren, cierran, confirman ni revierten recursos—. Es
  el patrón que esta capa debe seguir si extrae persistencia.
- La última evidencia de GitHub Actions corresponde a la capa 0. Ha habido
  pushes autorizados posteriores, el más reciente `eee8aec`, pero **no se ha
  obtenido evidencia de ningún run**; esa verificación permanece **pendiente y
  aceptada**. No se atribuye CI remota porque `HEAD` coincida con `origin/main`.

## Lo que el programa cree saber de `notas`, y que 7.0 debe verificar

Aplica la lección 12 que dejó la capa 6 y que la 7 para dashboard confirmó: **un
supuesto heredado se marca como no verificado y se comprueba en la subcapa 0**.
La capa 6 se activó anticipando que sus dominios escribían archivos, y era
falso. De los siete supuestos de dashboard, **uno resultó falso** y solo se
detectó porque estaba marcado así.

Ninguno procedía de haber leído el código de `notas`: eran restos de lo que
otras capas observaron desde fuera.

**Los diez quedaron resueltos en 7.0**, uno por uno y con evidencia. **Nueve se
confirmaron y uno resultó incompleto**, el primero, que era el que fijaba la
frontera del dominio.

| # | Supuesto | Resultado en 7.0 |
|---:|---|---|
| 1 | El dominio vive en `app/routes/notas.py` y `app/controllers/notas_controller.py` | **Incompleto.** Son **cuatro** archivos, no dos: falta `app/services/nota_service.py`, que contiene **3 de las 9 sentencias SQL** del dominio, y `app/schemas/nota.py`. Un inventario que se hubiera quedado en los dos archivos previstos habría dejado fuera un tercio de la persistencia |
| 2 | **No tiene repositorio propio** | **Confirmado.** Hay seis repositorios —asignaciones, dashboard, estudiantes, pagos, plan de clases y reportes— y ninguno es de notas. Fijado por prueba |
| 3 | **El dominio escribe** | **Confirmado.** `POST /notas` inserta en `notas_detalle` con `get_cursor(commit=True)`. Es la **única** entrada que escribe, la **única** tabla escrita y la **única** transacción propia. Cero `UPDATE` y cero `DELETE` |
| 4 | Lee o escribe la tabla `notas_detalle` | **Confirmado.** Las cinco entradas la tocan: una la escribe y cuatro la leen |
| 5 | **Otros dominios ya migrados leen sus tablas** | **Confirmado y cuantificado.** `notas_detalle` la leen **siete módulos**: tres ya migrados —`asignacion_controller`, `dashboard_repository` y `estudiantes_repository`— y tres en espera —`boletin_controller`, `planilla_controller` y `planilla_excel_controller`—, además del propio. **Es la tabla más compartida del programa hasta hoy** |
| 6 | **Boletín consume notas** | **Confirmado, y es más fuerte de lo previsto.** No es solo que boletín lea la tabla: **`notas` posee las rutas `/boletin/{id}`, `/boletin/detallado/{id}` y `/planilla/{id}`**, con nombre de otros dominios. No hay colisión de paths con `boletines.py` ni `planilla.py`, comprobado, pero la frontera **no coincide con los nombres de archivo** |
| 7 | Las fórmulas de promedio del sistema | **Resuelto: `notas` añade una cuarta.** Calcula con `round(..., 2)` **en Python**, no con `TRUNC` ni `ROUND` en SQL. Y el promedio general del boletín promedia los valores **sin redondear**, aunque muestre los redondeados. Fijado por prueba con 3,0/4,0/4,0 → **3,67**, donde `TRUNC` daría 3,66 |
| 8 | **Consume `resolver_asignacion_academica_id_cursor`** | **Confirmado.** Lo usan **dos** funciones: `crear_nota_controller` y `planilla_asignacion_controller` |
| 9 | **Los permisos no son uniformes** | **Confirmado y cuantificado.** Dos modelos en cinco entradas: `require_asignacion_access` en 2 y `require_estudiante_access` en 3. Ninguna es admin estricto. Son **menos** modelos que los cuatro de dashboard |
| 10 | **No escribe archivos** | **Confirmado.** Ninguno de los cuatro archivos del dominio menciona `storage`. El rollback no necesita cubrir archivos |

## Alcance autorizado

- Inventariar entradas HTTP, reglas, cálculos, consultas, escrituras, archivos,
  pruebas y consumidores **de notas** mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, orden, nulos, **redondeos y decimales**,
  transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia siguiendo el
  patrón ya probado cuatro veces, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas **y conexiones** críticas antes y después. La
  capa 7 para dashboard demostró que medir solo consultas esconde el coste real.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  **solo después** de caracterizar y demostrando que la respuesta existente se
  conserva.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- **Todos los demás dominios de la capa 7**: boletín, asistencia,
  observaciones, planilla, planeador anual, plan de clases, ventas, branding,
  profesores, super admin y cualquier otro. Esta capa es de un solo dominio.
  Se permite la lectura mínima indispensable para caracterizar un contrato que
  `notas` consuma o que consuma de `notas`, sin modificarlo.
- **`dashboard`, ya migrado.** Su frontera de persistencia quedó cerrada y sus
  42 pruebas de caracterización deben seguir pasando. Si `notas` comparte
  lecturas con él, se decide **con evidencia** y sin duplicar a ciegas.
- `app/services/asignacion_academica.py`, del que dependen nueve módulos, y
  `cobros.py`, del que dependen los contratos financieros de la capa 4: se leen
  si hace falta, **no se tocan**.
- Los hallazgos abiertos de las capas 5, 6 y 7. En particular el **paso 2 de la
  clave de idempotencia** de `POST /pagos`, los status codes 500 de
  `tipos_pagos_controller`, la **ausencia de lock en el alta y la edición de
  asignaciones**, el `SELECT *` de `GET /estudiantes/{id}`, y **los diez
  hallazgos de dashboard**, empezando por el `activo` ausente de sus dos
  precondiciones de permiso. **No entran por inferencia.**
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de cualquier capa activa».
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas de
  cálculo, redondeos, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos los **redondeos y el número de decimales** de cualquier
  nota, promedio o total que el dominio presente.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1. **Si el dominio escribe, esta invariante es la más
  delicada de la capa.**
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de lectura financieros fijados por la capa 4 siguen pasando su
  caracterización, incluidos los conteos 6/15, 1/13/37 y 5/12/12.
- Las fronteras de persistencia de las capas 5, 6 y 7 no se alteran: si `notas`
  necesita una lectura que ya existe allí, se decide **con evidencia** y sin
  duplicarla a ciegas.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.
- Ninguna escritura de archivos cambia de momento, de nombre ni de destino sin
  una decisión explícita y un rollback documentado.

## Línea base registrada en 7.0

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_notas_caracterizacion.py tests\test_notas_controlador.py tests\test_notas_permissions.py` | **52 pasaron** en 0,91 s |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **790 pasaron**, 5 warnings heredadas, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre la prueba nueva | **Correcto** |
| Dependencias | Ejecutado por la compuerta global | **Íntegras** |

La compuerta heredada se reprodujo **antes de tocar nada**: **756 pruebas,
exit 0**, coincidiendo exactamente con lo registrado al cerrar la capa 7 para
dashboard. La suite pasó de **756 a 790** con la caracterización de 7.0.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas y conexiones | **Cerrada** |
| 7.1 | Extraer la persistencia a `notas_repository` sin cambiar SQL, conteos ni ciclo de vida | **Pendiente**, definida y no iniciada |
| 7.2 y siguientes | **Sin decidir** | Se deciden con el resultado de 7.1 |

El desglose se dejó deliberadamente sin decidir hasta tener la evidencia del
inventario, igual que hicieron la capa 6 y la 7 para dashboard. Con esa
evidencia, **7.1 queda definida** y el resto sigue abierto.

Las subcapas innecesarias se marcarán `No aplica` con explicación. Nunca se
ejecutan dos subcapas en el mismo turno.

## Inventario y contratos fijados en 7.0

La frontera son **5 entradas HTTP** en cuatro archivos:
`app/routes/notas.py`, `app/controllers/notas_controller.py`,
`app/services/nota_service.py` y `app/schemas/nota.py`.

**Ninguna declara `response_model` ni `status_code` explícito.** El router lleva
`Depends(get_current_user)`, así que toda entrada exige usuario autenticado;
sobre eso cada una añade lo suyo.

| Entrada | Permiso | Contrato observable que debe conservarse |
|---|---|---|
| `POST /notas` | `require_asignacion_access` | **La única que escribe.** Inserta en `notas_detalle` cuatro columnas. Responde **200** con `{mensaje: "Nota registrada", id: {...}}`, donde **`id` es un diccionario, no un entero**. `nota` va validada por Pydantic al rango **0..5**; fuera de él, **422** |
| `GET /notas/{estudiante_id}` | `require_estudiante_access` | `{notas: [{nota, descripcion}], promedio}`; el promedio se calcula **en Python** con `round(..., 2)` y vale **0** si no hay notas |
| `GET /boletin/{estudiante_id}` | `require_estudiante_access` | `{nombre, apellido, curso, materias: [{materia, promedio, estado}], promedio_general, estado_final}`; corte Aprobado en **≥ 3,0**; si no hay filas responde `{mensaje: "Estudiante no encontrado"}` con **200** |
| `GET /planilla/{asignacion_id}` | `require_asignacion_access` | Lista de `{estudiante_id, nombre, apellido, materia, curso, promedio}`, solo estudiantes con `COALESCE(LOWER(estado),'activo') = 'activo'`, orden por nombre |
| `GET /boletin/detallado/{estudiante_id}` | `require_estudiante_access` | Lista por materia con `actividades`; si una materia no tiene notas **fabrica tres actividades sintéticas** con `nota: 0.0`; `promedio` va **fijo en 0**. `periodo` es query con defecto **1**, y es la **única** entrada que lo filtra |

- Tenant por `search_path` desde el JWT, igual que en las capas anteriores.
- `require_estudiante_access` y `require_asignacion_access` **no consultan la
  base cuando el rol es `admin`**; sí lo hacen, con una conexión propia, cuando
  es `profesor`. Cualquier otro rol recibe **403**.
- **La ruta no contiene SQL**, y una prueba lo fija: la invariante que dejó 6.5
  se conserva.

### Propiedad transaccional

**Una sola tabla escrita, `notas_detalle`, y solo con `INSERT`.** Cero `UPDATE`
y cero `DELETE`. Hay **una única transacción propia** en todo el dominio, la de
`crear_nota_controller`, abierta con `get_cursor(commit=True)`.

El ciclo de vida es **uniforme**, a diferencia de dashboard: las cinco funciones
del controlador y las tres del servicio usan `with get_cursor()`. **Ninguna usa
`get_connection()` con `try/finally`**, así que esta capa no hereda el problema
que la 7 de dashboard tuvo que dejar intacto.

**No hay un solo `try/except` en el dominio.** Un fallo de infraestructura sale
como **500**, no como 400. Es lo contrario de dashboard y de
`tipos_pagos_controller`, y **no es un defecto**: es un contrato distinto, que
se registra para que ninguna extracción lo cambie por parecerse a los vecinos.

## Línea base de consultas y conexiones

Medida herméticamente con dobles de cursor y conexión, **a través de la ruta**
para capturar las conexiones que abre la capa de permisos, y **fijada por
aserciones**, no anotada en prosa. Los conteos excluyen autenticación,
`search_path` y la sentencia de timeouts de cada checkout.

| Camino | Consultas | Conexiones |
|---|---:|---:|
| `POST /notas`, como **admin** | 4 | **4** |
| `POST /notas`, como **profesor** | 5 | **5** |
| `GET /notas/{id}`, admin | 1 | 1 |
| `GET /notas/{id}`, profesor | 2 | 2 |
| `GET /boletin/{id}`, admin | 1 | 1 |
| `GET /boletin/{id}`, profesor | 2 | 2 |
| `GET /planilla/{id}`, admin | 1 | 1 |
| `GET /planilla/{id}`, profesor | 2 | 2 |
| `GET /boletin/detallado/{id}`, admin | **1 + N** | 1 |
| `GET /boletin/detallado/{id}`, profesor | **2 + N** | 2 |

Lectura del resultado, sin optimizar todavía:

- **Hay N+1, y es el primero que encuentra el programa desde la capa 4.**
  `boletin_detallado_controller` emite una consulta **por cada materia** del
  estudiante, dentro de un bucle. Una prueba lo fija comparando 1 materia
  —2 consultas— contra 3 —4 consultas—. Dashboard no tenía ninguno.
- **Escribir una nota cuesta cuatro conexiones, cinco si es profesor.** Tres son
  las validaciones de `nota_service`, cada una con su propia conexión, y ninguna
  comparte cursor con la que inserta. Es **más caro que el camino peor de
  dashboard**, que costaba cuatro.
- El N+1 y las conexiones son problemas **distintos**: el boletín detallado abre
  **una sola** conexión aunque emita N+1 consultas; el alta abre cuatro para
  emitir cuatro.
- Ser admin **abarata** todas las entradas, porque ambas comprobaciones de
  permiso salen sin consultar.

## Subcapa 7.0 — trabajo exacto, ejecutado y cerrado

1. Confirmar `main`, árbol limpio y que todo commit posterior al base
   `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1` esté explicado en esta bitácora.
   Comprobar `git rev-parse --show-toplevel`, no solo `git status`.
2. Reproducir la compuerta heredada —756 pruebas esperadas— y determinar las
   pruebas específicas sin ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas **de notas**. No leer historia global ni
   código de los demás dominios de la capa 7.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, cálculos, persistencia, **escrituras**, archivos y efectos
   laterales.
5. **Determinar con evidencia si el dominio escribe**, qué tablas toca, quién es
   dueño de cada `commit` y `rollback`, y si alguna escritura carece de
   protección concurrente. Es el supuesto 3 y condiciona todo lo demás. Si
   escribe, **actualizar el perfil de riesgo de esta bitácora antes de seguir**.
6. Registrar los contratos observables exactos: rutas, métodos, payloads,
   status codes, permisos por rol, tenant, ownership, orden, nulos, **redondeos
   y decimales**, transacciones y errores.
7. Comprobar con evidencia **los diez supuestos que esta activación registra
   sin verificar**, uno por uno, y corregir la tabla con lo que se encuentre.
8. **Determinar qué fórmula de promedio usa este dominio** y si coincide con
   alguna de las tres ya registradas o añade una cuarta. En un dominio de
   calificaciones **la cifra es el contrato**.
9. Identificar qué dominios ya migrados leen estas tablas y qué contratos suyos
   podrían romperse desde aquí sin que fallen las pruebas de `notas`.
10. Caracterizar con pruebas los caminos que una extracción posterior pueda
    alterar. 7.0 **no autoriza** una extracción ni un cambio de producto.
11. Medir o instrumentar herméticamente el número de consultas **y de
    conexiones** de los caminos críticos, a través de la ruta y no solo del
    controlador, y determinar si hay N+1.
12. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
    `git diff --check`; revisar que el diff pertenezca solo a 7.0.
13. Actualizar esta bitácora, definir 7.1 con la evidencia obtenida y detenerse
    sin iniciarla.

## Criterios de cierre de la subcapa 7.0

- El dominio y sus consumidores están inventariados con archivos y puntos de
  entrada concretos, sin lectura global innecesaria, y con su frontera clara
  frente a los dominios que **no** entran en esta capa.
- **La pregunta de si el dominio escribe está respondida con evidencia**, con
  sus tablas, sus transacciones y sus dueños de `commit` y `rollback`. Si
  escribe, el perfil de riesgo de esta bitácora está actualizado.
- Los contratos HTTP, de permisos por rol, tenant, ownership, de cálculo y de
  transacción están enumerados y protegidos por caracterización suficiente,
  incluidos los redondeos y la fórmula de promedio.
- Los diez supuestos heredados están **resueltos con evidencia**, confirmados o
  refutados, y la tabla queda corregida.
- Las consultas y conexiones críticas tienen una línea base reproducible,
  fijada por aserciones y no anotada en prosa, y la pregunta del N+1 queda
  respondida con medición.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 7.0.
- La subcapa 7.1 queda definida y no iniciada.

**Los ocho criterios se cumplieron.** El diff de 7.0 contiene **un solo archivo
nuevo** y **ningún archivo rastreado modificado**, igual que los de 5.0, 6.0 y
7.0 de dashboard.

## Hallazgos de 7.0, registrados y sin corregir

Ninguno se corrige por inferencia: son hallazgos del inventario, no defectos de
la subcapa. Corregir cualquiera exige una decisión explícita del usuario.

Son **doce**, y los dos primeros son de una gravedad que no tuvo ningún hallazgo
de dashboard, porque **afectan a lo que el cliente recibe al escribir**.

- **`POST /notas` responde «Nota registrada» aunque no registre nada.** Es el
  hallazgo más grave de 7.0. Si falla cualquiera de las tres validaciones, el
  controlador devuelve `{"error": ...}`, la ruta lo envuelve y el cliente recibe
  **HTTP 200** con `{"mensaje": "Nota registrada", "id": {"error": "..."}}`. **No
  se abre ninguna conexión y no se escribe nada**, pero la respuesta afirma lo
  contrario. Un frontend que compruebe el status code o el campo `mensaje` dará
  la nota por guardada.
  **Verificado con una petición HTTP real** contra la aplicación, no deduciendo
  desde una llamada a la función de ruta: ver la corrección del 2026-08-19 en el
  registro de ejecución. El status code **200 está fijado por aserción**, junto
  al cuerpo exacto, en tres pruebas parametrizadas.
- **El campo `id` de `POST /notas` no es un entero, es un diccionario.** La ruta
  asigna a `nota_id` el **valor de retorno completo** del controlador y lo mete
  en su propio campo `id`, así que el camino feliz devuelve, con **HTTP 200**,
  `{"mensaje": "Nota registrada", "id": {"mensaje": "Nota creada", "id": 501}}`.
  El id real está anidado dos niveles. Es contrato observable y **el frontend
  desplegado depende de lo que hoy recibe**, así que cambiarlo no es una
  corrección interna. Fijado también por petición HTTP real.
- **Contraste que delimita los dos anteriores**: la validación de rango de
  Pydantic **sí** produce un status code correcto. Una `nota` fuera de 0..5
  responde **422** con el `detail` estándar. El problema no es que el dominio no
  sepa fallar: es que **sus tres validaciones propias no usan el mecanismo de
  error de FastAPI**, mientras la del esquema sí.
- **N+1 en `GET /boletin/detallado/{id}`**, el primero que el programa encuentra
  desde la capa 4. Una consulta por materia dentro de un bucle. Eliminarlo es
  trabajo del tipo que hizo la capa 4, **no está en el objetivo de la capa 7** y
  no entra sin orden explícita.
- **La escritura no fija `periodo` y una lectura filtra por él.** El `INSERT`
  pone cuatro columnas y `periodo` no está entre ellas, así que la nota hereda
  el valor por defecto de la columna en la base. `GET /boletin/detallado` filtra
  `periodo = %s` con defecto 1. **Si el defecto de la columna no coincide, una
  nota creada por esta ruta existe pero no aparece en el boletín detallado.** No
  se comprobó el defecto real de la columna: exigiría tocar la base, que esta
  subcapa no hace. Queda como la primera pregunta a resolver si alguien toca
  `periodo`.
- **Las otras tres lecturas ignoran `periodo` por completo** y promedian todos
  los periodos juntos. Fijado por prueba parametrizada.
- **Cuatro conexiones para escribir una nota, cinco si es profesor.** Las tres
  validaciones de `nota_service` abren cada una la suya y ninguna comparte
  cursor con el `INSERT`. Es más caro que el peor camino de dashboard. Pertenece
  a la auditoría de capacidad de la capa 2; **se registra, no se actúa**.
- **`validar_asignacion` no filtra por `activo`.** Es la **tercera instancia**
  del mismo patrón: dashboard registró dos en sus precondiciones de permiso.
  Aquí el efecto es peor, porque permite **escribir** una nota contra una
  asignación desactivada. Fijado por prueba, sin corregir: cambiarlo altera
  quién puede escribir.
- **`require_estudiante_access` tampoco filtra por `activo`**, y gobierna 3 de
  las 5 entradas. Vive en `app/core/permissions.py`, **infraestructura
  compartida**, así que está fuera del alcance de esta capa; se registra porque
  completa el patrón y porque ninguna capa lo ha anotado antes.
- **El dominio no tiene un solo `try/except`.** Un fallo de infraestructura sale
  como **500**. No es un defecto —es un contrato distinto del de dashboard y
  `tipos_pagos_controller`, que responden 400—, pero conviene registrarlo para
  que ninguna extracción lo «uniformice» por vecindad.
- **El boletín detallado fabrica ids sintéticos por concatenación de cadenas.**
  Cuando una materia no tiene notas inventa tres actividades con
  `int(str(materia_id) + "01")`, así que la materia 5 produce **501, 502 y
  503**, que **pueden colisionar con ids reales de `notas_detalle`**. Ya estaba
  fijado por la caracterización de 1.4h; se registra su riesgo.
- **`promedio: 0` fijo en el boletín detallado**, con el comentario «El frontend
  recalcula luego»: parte del cálculo de calificaciones vive en el cliente.
- **La frontera del dominio no coincide con los nombres de archivo.** `notas`
  posee `/boletin/{id}`, `/boletin/detallado/{id}` y `/planilla/{id}`, mientras
  existen por separado `boletines.py` y `planilla.py`, que son otros dominios en
  espera. **No hay colisión de paths**, comprobado; pero quien migre boletín o
  planilla debe saber que **tres de sus rutas ya viven aquí**.

## Subcapa 7.1 — trabajo exacto, pendiente y no iniciada

Extraer la persistencia de `notas`, y solo eso, siguiendo el patrón que las
capas 5, 6 y 7 dejaron probado cuatro veces.

1. Revalidar Git, incluido `git rev-parse --show-toplevel`, y limitar la
   inspección a los cuatro archivos del dominio y sus pruebas. **No inspeccionar
   otros dominios.**
2. Conservar la caracterización de 7.0 y ampliarla solo si una extracción
   concreta lo exige, **antes** de mover producto.
3. Extraer las **9 sentencias** —6 del controlador y 3 del servicio— a
   `app/repositories/notas_repository.py`, con funciones que **reciben el cursor
   existente** y no abren, cierran, confirman ni revierten recursos, igual que
   los seis repositorios ya existentes.
4. **Decidir con evidencia si las tres consultas de `nota_service` van al
   repositorio.** Es el punto delicado propio de esta subcapa y **no tiene
   precedente exacto**: en las capas anteriores el SQL a extraer vivía en el
   controlador, no en un servicio. El precedente más cercano es 6.4, que llevó
   al repositorio las precondiciones sobre catálogos. Registrar la decisión
   **antes** de mover. Si van, hay que decidir además si `nota_service`
   desaparece o conserva las funciones como fachada, y **cada una abre hoy su
   propia conexión**: moverlas sin más cambiaría los conteos que 7.0 fijó.
5. **No cambiar el ciclo de vida ni el número de conexiones.** Las cuatro
   conexiones de `POST /notas` se conservan, aunque sean el hallazgo más caro
   del dominio. Reducirlas es trabajo de otra capa.
6. **No tocar el N+1** del boletín detallado. Es del tipo que resolvió la capa 4
   y no está en el objetivo de esta.
7. Conservar byte por byte las cadenas SQL, sus parámetros y su orden, copiando
   **por rango de líneas y no transcribiendo**, que es la lección 17. Si
   aparecen dos literales idénticos salvo la sangría, **no unificarlos sin
   autorización explícita**.
8. **No corregir ninguno de los doce hallazgos de 7.0**, en particular ni el
   falso éxito de `POST /notas`, ni el `id` anidado, ni el `activo` ausente de
   `validar_asignacion`, ni el tratamiento de `periodo`.
9. Verificar que los conteos de consultas y conexiones de 7.0 **no cambian**, y
   ejecutar un comparador AST contra el commit base de la capa,
   `eee8aec`, exigiendo conjunto de SQL idéntico. Excluir los docstrings antes
   de comparar, que es la lección 13 de la capa 6.
10. Comprobar que **la compuerta global completa** sigue en verde, no solo las
    pruebas del dominio: `notas_detalle` la leen siete módulos y tres ya están
    migrados, así que una rotura de contrato ajeno **no aparecería** en las
    pruebas de `notas`.
11. Ejecutar pruebas específicas, Ruff del alcance, compuerta global y
    `git diff --check`; documentar y detenerse antes de decidir 7.2.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- El dominio quedó migrado con contratos estables y pruebas, **sin arrastrar
  otros dominios**.
- `response_model`, errores de dominio y pruebas HTTP, si se añadieron, llegaron
  **después** de caracterizar y conservando la respuesta existente, demostrado.
- No se creó ninguna abstracción compartida sin dos consumidores reales.
- Los contratos del frontend y de la base de datos permanecen intactos, y
  también los de los dominios ya migrados que leen estas tablas.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados. **Si 7.0 descubre
  que el dominio escribe, el rollback debe cubrir datos explícitamente** y no
  puede declararse «puramente de código» como en las capas 5, 6 y 7 para
  dashboard.
- El índice maestro queda actualizado y **ningún otro dominio se activa sin
  orden explícita del usuario**.

## Decisiones

- Se usa `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1` como commit base porque es
  el `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main`. **No se reutilizó ningún hash de memoria**: se comprobó el
  `HEAD` real antes de registrarlo, y también el repositorio con
  `git rev-parse --show-toplevel`, que es la lección 18 del programa.
- **El dominio es `notas` y lo eligió el usuario.** No llegó pegada la
  autorización preparada de `PROMPT_CONTINUACION.md`: el usuario preguntó qué
  eran los dominios pendientes, se le explicó el término, se le mostró la
  correspondencia entre los once nombres en espera y sus archivos, y eligió.
  **No se dedujo por inferencia**, que es lo que esa autorización prohíbe.
- El usuario eligió explícitamente **continuar manteniendo pendientes** las
  verificaciones heredadas, respondiendo a una pregunta directa que ofrecía
  también completarlas antes. Ninguna se marca como cumplida y todas conservan
  su riesgo: el valor operativo final de `DB_STATEMENT_TIMEOUT_MS` de la capa 1,
  la evidencia de GitHub Actions posterior a la capa 0 y la credencial
  privilegiada de la capa 4 **sin rotar**.
- **Las subcapas se numeran por bitácora y esta vuelve a empezar en 7.0.** Ver
  «Relación con la bitácora de dashboard». Alternativa descartada: renumerar
  como 8.x, que habría inventado una capa inexistente en el índice.
- **El desglose de subcapas posteriores a 7.0 se deja sin decidir** hasta tener
  la evidencia del inventario, en particular la de si el dominio escribe.
  Alternativa descartada: copiar el plan de dashboard —una sola extracción y
  cierre—, que presupondría un dominio de solo lectura sin haberlo comprobado.
- **Los supuestos heredados se registran como no verificados**, no como hechos,
  y son **diez**. Es la lección 12 de la capa 6, que ya sirvió dos veces: en la
  6 el supuesto de los archivos resultó falso, y en la 7 para dashboard el de
  los cálculos más caros.
- `PROMPT_CONTINUACION.md` **no se modifica en este turno**. Conserva una
  autorización preparada para «el siguiente dominio» que esta activación
  consume; retirarla es correcto, pero el alcance autorizado de un turno de
  activación es exclusivamente el índice maestro y la bitácora nueva. Se hará en
  el turno de 7.0, que ya toca documentación. Es el mismo criterio que aplicó la
  capa 7 para dashboard.
- **No se corrigió el residuo documental detectado en el índice.** Ver Riesgos.
  Corregirlo es limpieza ajena a la activación y exige orden explícita, como la
  que se pidió para el residuo equivalente de la capa 4.
- **El contrato HTTP de la escritura se verifica por ASGI crudo, no por
  `TestClient`.** Decidido en la corrección de 7.0. `httpx` no está instalado y
  una subcapa de inventario **no cambia dependencias**; conducir la aplicación
  por su interfaz ASGI usa solo la biblioteca estándar y recorre el mismo camino
  real —middleware, enrutado, dependencias, serialización—. Alternativas
  descartadas: instalar `httpx`, que tocaría `requirements.txt` y `pip check`
  fuera de alcance; y **dejar el status code sin fijar**, que era el estado
  anterior y es justo la laguna que el usuario detectó.
- **Solo se llevó a ASGI la entrada que escribe.** Las otras cuatro siguen
  caracterizadas por llamada directa, como el resto de la suite. Extender el
  patrón a todo el dominio sería ampliar el alcance sin que ningún hallazgo lo
  exija; `POST /notas` lo exigía porque **su status code es el hallazgo**.

## Riesgos

- **El dominio no está inspeccionado.** Todo lo que esta bitácora dice de
  `notas` son supuestos heredados marcados como tales. Un riesgo copiado de un
  documento anterior no es evidencia; 7.0 los comprueba o los refuta.
- **Si `notas` escribe —y es lo probable—, el perfil de riesgo de esta capa no
  es el de dashboard sino el de la capa 5.** Entran en juego transacciones
  propias, protección concurrente e idempotencia, y las **26 claves foráneas
  repuestas por la capa 3** pueden hacer fallar inserciones que antes pasaban en
  silencio. Además `notas_detalle` fue una de las ocho tablas averiadas que esa
  capa reparó. Esta bitácora debe actualizarse **antes** de cualquier extracción
  si 7.0 lo confirma.
- **La cifra es el contrato, y aquí más que en ningún otro dominio.** El sistema
  ya usa **tres fórmulas de promedio distintas** —`ROUND(..., 1)` en
  estudiantes y dos `TRUNC(..., 2)` diferentes en dashboard— y ninguna se ha
  observado desde `notas`. Un redondeo, un `TRUNC` frente a un `ROUND`, un
  `COALESCE` o un `AVG` de promedios cambian la calificación que ve un padre sin
  romper ninguna estructura. La caracterización debe fijar cifras, no formas.
- **Dominios ya migrados leen estas tablas.** Estudiantes lee `notas_detalle`
  para el expediente y dashboard para sus paneles, con contratos ya fijados por
  las capas 6 y 7 y **protegidos por pruebas que viven en otros archivos**. Un
  cambio hecho desde aquí puede romperlos sin que falle una sola prueba de
  `notas`. La mitigación es ejecutar siempre la compuerta global, no solo las
  pruebas del dominio.
- **`response_model` puede cambiar el payload en silencio.** En FastAPI filtra
  los campos que no declara: un modelo corto recortaría la respuesta sin que
  fallara nada. El índice lo autoriza solo tras caracterizar y conservar la
  respuesta; si la equivalencia no se puede demostrar, **no se añade**.
- **Si `notas` resulta escribir archivos**, el rollback deja de ser solo de
  código y esta bitácora debe cubrirlos explícitamente. Hoy nadie lo ha
  comprobado.
- Los permisos no son uniformes en el sistema: intervienen roles distintos de
  `admin`. Un inventario incompleto de roles es un riesgo de seguridad, no de
  calidad.
- **Residuo documental en el índice maestro, detectado y no corregido.** La
  sección «Estado actual» de `README.md` conserva un párrafo que declara el
  punto de decisión de dashboard «ya resuelto» y en la misma frase «no está
  tomada». El resto del índice y `07_DASHBOARD.md` confirman sin ambigüedad que
  **sí se tomó**: cerrar sin abrir 7.2. Es texto residual, del mismo tipo que el
  que la capa 4 tuvo que limpiar con autorización explícita. **No se corrige
  aquí** porque es ajeno a la activación; queda registrado para que un chat
  futuro no lo lea como una decisión abierta.
- Heredado de la capa 1: `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrar contra
  volumen representativo y el deadline HTTP/proxy externo.
- Heredado de la capa 0: no hay evidencia de GitHub Actions posterior a esa
  capa. Las verificaciones locales no se presentarán como CI remota.
- Heredado de la capa 2: `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` se
  conserva como margen sin ejemplo real que la respalde, más allá del camino de
  cuatro conexiones **en serie** que encontró dashboard. Si esta capa encontrara
  un camino que **anida** conexiones, es evidencia relevante y debe registrarse,
  no actuarse.
- Heredado de la capa 4: la credencial privilegiada compartida en chat sigue
  **sin rotar** y no debe reutilizarse.
- Heredado de las capas 5, 6 y 7: sus hallazgos abiertos siguen vivos, incluida
  la ausencia de lock en el alta y la edición de asignaciones —el riesgo más
  directo del backend hoy— y el `activo` ausente en las precondiciones de
  permiso de dashboard. **No se corrigen desde aquí.**
- **El commit base ya está publicado y desplegado.** Un push a `main` en este
  repositorio dispara el despliegue, así que la publicación de esta capa
  afectará a producción en cuanto ocurra. Revertir a `eee8aec` exigiría otro
  push y otro despliegue, no una operación local.

## Registro de ejecución

### 2026-08-19 — activación de la capa para `notas`

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`, comprobado con
  `git rev-parse --show-toplevel`. No se usó GitHub para inferir el estado
  local.
- Autorización: orden explícita del usuario en este turno, nombrando el dominio
  `notas`. **No se pegó el bloque preparado** de `PROMPT_CONTINUACION.md`; la
  autorización llegó en conversación, después de que el usuario preguntara qué
  significan «dominio» y «capa 7» y se le explicara el alcance. La condición que
  ese bloque exige —nombrar el dominio explícitamente y no deducirlo— **se
  cumplió**.
- **Verificaciones heredadas**: se preguntó explícitamente al usuario, antes de
  escribir nada, si quería completarlas o continuar aceptándolas pendientes,
  ofreciendo también intentar cerrar la de CI. **Eligió continuar
  aceptándolas.** Quedan registradas con su riesgo y **ninguna se marca como
  cumplida**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1` con salida vacía; `HEAD` real
  `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`, comprobado y no recordado.
- Continuidad: el base de la capa 7 para dashboard,
  `123637ee80895023ecece9c32df526ef4eddd1e5`, existe y es ancestro de `HEAD`,
  verificado con `git merge-base --is-ancestor`. Sus **cinco** commits
  posteriores forman una historia lineal y **todos están explicados** en
  `07_DASHBOARD.md`: la activación `fb303d5`, el cierre de 7.0 `59efda6`, la
  extracción de 7.1 `c75a5b7`, la preparación del cierre `8591816` y el cierre
  `eee8aec`.
- Estado remoto **comprobado, no supuesto**: `origin/main` está en
  `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`, el mismo commit que `HEAD`. El
  reflog registra `update by push` de `eee8aec` y, antes, de `8591816` y
  `123637e`. La capa 7 para dashboard **está publicada y desplegada**, y también
  lo está su commit de cierre. **No se consultó ni se atribuye ningún run de
  GitHub Actions**; esa evidencia sigue sin obtenerse desde la capa 0.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. **No se inspeccionó código de
  `notas`** ni de ningún otro dominio. Lo único observado fue el **listado de
  nombres de archivo** de `app/routes/` y `app/controllers/`, para responder al
  usuario qué dominios quedaban en espera; no se abrió ninguno.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --show-toplevel`,
  `git branch --show-current`, `git status`, `git status --porcelain=v1`,
  `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git merge-base --is-ancestor`, `git log --reverse --oneline` desde el base de
  dashboard y `git reflog show origin/main`; todos con resultado coherente con
  la activación.
- Estado al cerrar el turno de activación: capa 7 **activa** para el dominio
  `notas`; 7.0 **pendiente y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto de
  arriba y detenerse antes de 7.1. *(Ejecutada en el turno siguiente; ver el
  cierre de 7.0 más abajo.)*

### 2026-08-19 — cierre de 7.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente y
  comprobado con `git rev-parse --show-toplevel` antes de nada, que es la
  lección 18. No se usó GitHub para inferir el estado local.
- Precondición Git: rama `main`, **árbol limpio**, `HEAD`
  `a56d55f97aee0db14af8a5b66d70e6970cedfa33`. Entre la activación y este turno
  el usuario **commiteó** el trabajo documental: ese commit es exactamente la
  activación, dos archivos de `docs/modularizacion/`, y está explicado en esta
  bitácora. El commit base `eee8aec` existe y es ancestro; `origin/main` sigue
  en el base, así que hay **un commit local por delante, sin publicar**.
- Compuerta heredada reproducida **antes de tocar nada**: **756 pruebas,
  exit 0**, Ruff correcto y `pip check` íntegro. Coincide exactamente con lo
  registrado al cerrar la capa 7 para dashboard.
- Inventario dirigido: `app/routes/notas.py`,
  `app/controllers/notas_controller.py`, `app/services/nota_service.py`,
  `app/schemas/nota.py`, `tests/test_notas_controlador.py` y
  `tests/test_notas_permissions.py`. Se leyeron además, **solo para resolver los
  supuestos y medir, sin modificarlos**, `require_estudiante_access` de
  `app/core/permissions.py`, el registro de routers en `app/main.py` y el
  listado de `app/repositories/`. No se leyó historia global.
- Frontera comprobada, **no supuesta**: se listaron las rutas declaradas por
  `app/routes/boletines.py` y `app/routes/planilla.py` para descartar colisión
  de paths con las tres rutas que `notas` posee. **No hay colisión**: los
  métodos y las formas de path difieren. No se leyó el código de esos dominios.
- **Los diez supuestos que la activación registró sin verificar quedaron
  resueltos**: nueve confirmados y **uno incompleto**, el primero, que daba el
  dominio por dos archivos cuando son cuatro. `app/services/nota_service.py`
  contiene **3 de las 9 sentencias SQL**: un inventario que se hubiera fiado del
  supuesto habría dejado fuera un tercio de la persistencia. La tabla de
  supuestos quedó corregida con el resultado de cada uno.
- **Hallazgo empírico verificado, no deducido**: antes de escribir ninguna
  prueba se ejecutó una sonda desechable **fuera del repositorio**, en el
  directorio temporal de la sesión, para confirmar la forma real de la respuesta
  de `POST /notas` y su número de conexiones. Confirmó el `id` anidado, el falso
  éxito con 200 y las cuatro conexiones. La sonda **no se versionó** ni tocó la
  base de datos.
- Caracterización añadida: `tests/test_notas_caracterizacion.py`, **34 casos**
  en siete bloques —guardias estructurales, contrato de la escritura, conteos de
  consultas y conexiones, `nota_service`, contrato de cálculo, tratamiento de
  `periodo` y **contrato HTTP real por ASGI**—. Código de producto y
  configuración modificados: **ninguno**. El séptimo bloque se añadió en la
  corrección del final del turno; ver más abajo.
- **Error propio, detectado y corregido dentro de la subcapa**: una prueba
  buscaba el `INSERT` en la primera consulta del cursor, pero el cursor es
  compartido y las tres validaciones van antes. Falló al ejecutarse; se corrigió
  apuntando a la cuarta llamada y **aprovechando para fijar que el camino de
  escritura emite exactamente cuatro consultas**, que es información que la
  versión anterior no capturaba.
- Se comprobó aparte que **las guardias no pasan en vacío**: el extractor de
  literales ve **39 cadenas en el controlador, 6 de ellas con SQL**, **3 de 3 en
  el servicio** y **9 en la ruta, ninguna con SQL**, que es justo lo que la
  guardia de 6.5 exige.
- Pruebas específicas: **52 pasaron** en 0,91 s sobre los tres archivos del
  dominio. La prueba nueva aislada: 34 pasaron en 0,83 s. Ruff del archivo
  nuevo: **correcto**.
- Compuerta global final: `.\venv\Scripts\python.exe scripts\verify.py`;
  **790 pruebas pasaron** en 2,35 s, **las mismas 5 warnings heredadas y
  ninguna nueva**, Ruff correcto, `pip check` sin dependencias rotas, exit 0. La
  suite pasó de 756 a 790.
- Medición: hermética, con dobles de cursor y conexión, y **a través de la
  ruta** para capturar las conexiones que abre la capa de permisos. Los conteos
  de diez caminos quedan **fijados por aserciones**, no anotados en prosa,
  incluido el N+1 comparando 1 materia contra 3.
- Diff final: `git diff --check` en exit 0. El alcance es **un solo archivo
  nuevo** y **ningún archivo rastreado modificado**: no se tocó producto, rutas,
  payloads, status codes, permisos, tenant, ownership, SQL, transacciones,
  configuración ni dependencias. Finales de línea **LF**, verificados leyendo
  bytes y no con `grep`, que es la lección 19.
- PostgreSQL, migraciones, producción, commit, push y deploy: **ninguno**. La
  evidencia de GitHub Actions posterior a la capa 0 continúa pendiente y no se
  atribuye CI remota.
#### Corrección del mismo 2026-08-19, a petición del usuario

- **El usuario pidió verificar bien el hallazgo del falso éxito**, y tenía
  razón en pedirlo: la primera comprobación **llamaba a la función de ruta
  directamente en Python**, así que observaba el diccionario devuelto pero
  **nunca un status code**. El «200» estaba registrado por inferencia sobre cómo
  se comporta FastAPI, no por observación. El trabajo exacto de 7.0 exige
  registrar *status codes*, así que era una laguna real de esta subcapa.
- **Toda la suite del repositorio tiene la misma limitación**: no existe **ni un
  solo `TestClient`** en `tests/`, y ninguna prueba había observado nunca un
  status code real. Se comprobó con una búsqueda dirigida.
- **Verificación hecha con una petición HTTP real**, conduciendo la aplicación
  por su **interfaz ASGI cruda**: middleware, enrutado, resolución de
  dependencias, ejecución del endpoint y serialización de la respuesta. No se
  usó `TestClient` porque **`httpx` no está instalado y esta subcapa no cambia
  dependencias**. No se tocó PostgreSQL: la capa de datos fue con dobles.
- **Resultado: el hallazgo queda confirmado, no corregido a la baja.**
  Camino feliz → **200** con
  `{"mensaje":"Nota registrada","id":{"mensaje":"Nota creada","id":501}}`.
  Validación fallida → **200** con
  `{"mensaje":"Nota registrada","id":{"error":"La asignación no existe"}}` y
  **cero conexiones**. Nota fuera de rango → **422**, que es el contraste que
  demuestra que el problema no es FastAPI sino que las tres validaciones propias
  del dominio no usan su mecanismo de error.
- Se añadió el **bloque 7** a la caracterización, con **5 casos**: el status code
  y el cuerpo del camino feliz, los tres de validación fallida parametrizados y
  el 422 de contraste. Ahora el 200 está **fijado por aserción**, no por prosa.
- Efecto sobre las cifras: la prueba nueva pasa de 29 a **34 casos**, las del
  dominio de 47 a **52** y la compuerta global de 785 a **790**, exit 0, con las
  mismas 5 warnings heredadas y **ninguna nueva**. El diff sigue sin tocar
  producto.
- **Lección para el resto del programa**: llamar a la función de una ruta no
  verifica su contrato HTTP. Las capas 4 a 7 fijaron status codes en sus
  bitácoras a partir de pruebas que solo invocaban funciones; **ninguna los
  observó**. No se revisan aquí —es trabajo ajeno a esta capa—, pero queda
  anotado que esa evidencia es más débil de lo que las bitácoras sugieren.
- Estado: 7.0 **cerrada**; 7.1 **pendiente, definida y no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 7.1, la extracción de la
  persistencia a `notas_repository`, y detenerse antes de decidir 7.2. **El
  punto que exige decisión con evidencia dentro de 7.1 es si las tres consultas
  de `nota_service` van al repositorio.**

## Entrega al próximo chat

- Capa activa: **7, `notas`**, y solo ese dominio. Activada el 2026-08-19.
- Última subcapa terminada: **7.0**, cerrada el 2026-08-19.
- Primera subcapa pendiente: **7.1**, la extracción de la persistencia a
  `notas_repository`. **Definida y no iniciada.**
- Commit base: `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`, rama `main`,
  **publicado y desplegado**. Al cerrar 7.0, `HEAD` es `a56d55f` y hay **un
  commit local por delante de `origin/main`**, la activación, más el trabajo de
  7.0 sin commitear.
- Compuerta al cerrar 7.0: **790 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro. La suite pasó de 756 a 790.
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub Actions posterior a la
  capa 0. La credencial privilegiada de la capa 4 sigue **sin rotar**.
- Lo que 7.0 dejó medido: **5 entradas HTTP** en **cuatro** archivos; **una sola
  tabla escrita** y **una sola transacción propia**; **9 sentencias SQL inline**
  —6 en el controlador y 3 en el servicio, 0 en la ruta—; **34 pruebas de
  caracterización** nuevas y los conteos de diez caminos. Escribir una nota
  cuesta **4 conexiones**, 5 como profesor. **Hay N+1** en el boletín detallado.
- **El contrato HTTP de `POST /notas` está fijado con status codes reales**,
  medidos por ASGI. Es la única entrada del programa entero con esa evidencia:
  el resto de la suite, en todas las capas, solo llama funciones. Si 7.1 toca la
  escritura, **esas cinco pruebas son las que deben seguir en verde**.
- **Lo que la activación creía y resultó incompleto**: que el dominio eran dos
  archivos. Son cuatro, y el que faltaba —`app/services/nota_service.py`—
  contiene **un tercio de la persistencia**.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** La capa 7 es «uno a la vez»; `dashboard` ya está
     cerrado en su propia bitácora y los demás siguen en espera.
  2. **El dominio escribe**, confirmado. El perfil de riesgo es el de la capa 5,
     no el de dashboard, aunque la escritura sea una sola sentencia.
  3. **No corregir ninguno de los doce hallazgos de 7.0**, y menos los dos
     primeros: `POST /notas` responde «Nota registrada» aunque no registre nada,
     y su campo `id` es un diccionario. **Los dos son contrato observable del
     que depende el frontend desplegado.**
  4. **El punto que 7.1 debe decidir con evidencia** es si las tres consultas de
     `nota_service` van al repositorio. No tiene precedente exacto: hasta ahora
     el SQL a extraer vivía en controladores, no en servicios.
  5. **No tocar el N+1** del boletín detallado ni las cuatro conexiones del
     alta. Son trabajo de las capas 4 y 2 respectivamente.
  6. **`notas_detalle` la leen siete módulos**, tres ya migrados. Romper un
     contrato ajeno **no haría fallar las pruebas de `notas`**: solo la
     compuerta global. Ejecutarla siempre completa.
  7. **La cifra es el contrato**, y este dominio añade la **cuarta** fórmula de
     promedio del sistema: `round(..., 2)` en Python.
- Siguiente acción exacta: ejecutar **7.1 de `notas`**, y detenerse antes de
  decidir 7.2. No iniciar dos subcapas en el mismo turno.
