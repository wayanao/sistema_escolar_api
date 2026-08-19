# Capa 7: notas

Última revisión: 2026-08-19.

## Control

- Estado: **Activa** desde el 2026-08-19.
- Commit base: `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, inventario, contratos y caracterización.
- Código de producto modificado al activar: **ninguno**.
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

**No hay ninguna razón para esperar lo mismo de `notas`.** Es el dominio donde
se capturan calificaciones, así que lo probable es que **escriba**, y una capa
que escribe tiene el perfil de riesgo de la **capa 5**, no el de la 7 para
dashboard: transacciones propias, claves foráneas que pueden hacer fallar
inserciones antes silenciosas, e idempotencia. Nada de esto está verificado; ver
la tabla de supuestos.

Esa diferencia debe resolverse **en 7.0 y antes de cualquier extracción**. Si el
dominio escribe, esta bitácora debe actualizarse con el perfil de riesgo
correspondiente antes de mover una sola línea.

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

**Nada de lo que sigue se da por bueno.** Ninguno procede de haber leído el
código de `notas`: son restos de lo que otras capas observaron desde fuera.

| # | Supuesto | Origen | Estado |
|---:|---|---|---|
| 1 | El dominio vive en `app/routes/notas.py` y `app/controllers/notas_controller.py` | Listado de directorios durante la activación; **no se abrió ninguno de los dos** | **NO VERIFICADO** |
| 2 | **No tiene repositorio propio** | La capa 7 registró que `dashboard_repository` es el **sexto**, tras asignaciones, estudiantes, pagos, plan de clases y reportes | **NO VERIFICADO** |
| 3 | **El dominio escribe**, a diferencia de dashboard | Es donde se capturan calificaciones. **Es una expectativa, no una observación** | **NO VERIFICADO. Es el supuesto más importante de los diez** |
| 4 | Lee o escribe la tabla `notas_detalle` | La capa 6 registró que `estudiante_controller` la lee para el expediente | **NO VERIFICADO desde este lado** |
| 5 | **Otros dominios ya migrados leen sus tablas**: estudiantes para el expediente y dashboard para sus paneles | Capas 6 y 7, verificado desde el lado de esos dominios | **NO VERIFICADO desde este lado.** Si es así, hay contratos de lectura ajenos que esta capa puede romper sin que fallen sus propias pruebas |
| 6 | **Boletín consume notas** | Expectativa por el nombre y por que `boletin_cabecera` y `boletin_detalles` aparecieron junto a `notas_detalle` en la avería de la capa 3 | **NO VERIFICADO** |
| 7 | **Existen al menos tres fórmulas de promedio distintas en el sistema** y ninguna se ha observado desde este dominio: `ROUND(..., 1)` por materia en estudiantes, `TRUNC(AVG(promedio_clase), 2)` en notas altas/bajas de dashboard y `TRUNC(AVG(CAST(n.nota AS numeric)), 2)` en sus rankings | Capas 6 y 7 | **NO VERIFICADO cuál usa `notas`, ni si añade una cuarta** |
| 8 | **Consume `resolver_asignacion_academica_id_cursor`** | La capa 6 contó nueve consumidores de esa función; dashboard resultó ser uno | **NO VERIFICADO** |
| 9 | **Los permisos no son uniformes**: un profesor capturaría solo lo de sus asignaciones y un admin lo vería todo | Patrón observado en asignaciones y dashboard, no en este dominio | **NO VERIFICADO** |
| 10 | **No escribe archivos** vía `app/services/storage.py` | Solo se ha demostrado que branding y plan de clases **sí** lo usan | **NO VERIFICADO.** Si los escribe, el rollback deja de ser solo de código |

7.0 debe resolver los diez **uno a uno y con evidencia**, y corregir esta tabla
con lo que encuentre. Que un supuesto venga de la capa 6 o de dashboard no lo
convierte en evidencia sobre este dominio.

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

## Línea base

Pendiente de 7.0. La compuerta heredada debe reproducirse **antes de tocar
nada** y su resultado esperado, registrado al cerrar la capa 7 para dashboard,
es **756 pruebas, exit 0**.

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Por determinar en 7.0, sin ampliar el alcance | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Ejecutado por la compuerta global y sobre el alcance modificado | Pendiente |
| Dependencias | Ejecutado por la compuerta global | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, caracterización y línea base de consultas y conexiones | **Pendiente**, no iniciada |
| 7.1 y siguientes | **Sin decidir** | Se definen con la evidencia de 7.0 |

El desglose posterior a 7.0 se deja deliberadamente **sin decidir**, igual que
hicieron la capa 6 y la 7 para dashboard. Proponer ya un 7.1 y un 7.2 por
analogía fijaría un plan sobre un dominio no inspeccionado, y en este caso sería
peor que en los anteriores: **no se sabe siquiera si el dominio escribe**, y de
eso depende cuántas subcapas hacen falta y en qué orden.

Las subcapas innecesarias se marcarán `No aplica` con explicación. Nunca se
ejecutan dos subcapas en el mismo turno.

## Subcapa activa: trabajo exacto de 7.0

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
  arriba y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7, `notas`**, y solo ese dominio. Activada el 2026-08-19.
- Última subcapa terminada: **ninguna**. La capa acaba de activarse.
- Primera subcapa pendiente: **7.0**, inventario, contratos y caracterización.
  **No iniciada.**
- Commit base: `eee8aec8725fc0bdd4a98fd2fd29cb88502c56e1`, rama `main`,
  **publicado y desplegado**. `HEAD` coincidía con `origin/main` al activar.
- Compuerta esperada al empezar: **756 pruebas, exit 0**, el resultado registrado
  al cerrar la capa 7 para dashboard. **Debe reproducirse antes de tocar nada.**
- Bloqueos: ninguno. Verificaciones heredadas **pendientes y aceptadas** por
  decisión explícita del usuario: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub Actions posterior a la
  capa 0. La credencial privilegiada de la capa 4 sigue **sin rotar**.
- Lo que hay que recordar antes de tocar nada:
  1. **Un solo dominio.** La capa 7 es «uno a la vez»; `dashboard` ya está
     cerrado en su propia bitácora y los demás siguen en espera.
  2. **Nada de este dominio está verificado.** Los diez supuestos de la tabla
     son herencia de otras capas, no observación. 7.0 los resuelve uno a uno.
  3. **La pregunta que manda es si el dominio escribe.** De ella depende el
     perfil de riesgo entero de la capa. Si escribe, esto se parece a la capa 5,
     no a dashboard.
  4. **La cifra es el contrato.** El sistema ya usa tres fórmulas de promedio
     distintas y no se sabe cuál usa este dominio.
  5. **Otros dominios ya migrados leen estas tablas.** Romper sus contratos no
     hará fallar las pruebas de `notas`; solo la compuerta global.
  6. **No corregir hallazgos abiertos**, ni los de este dominio cuando aparezcan
     en 7.0, ni los heredados de las capas 5, 6 y 7.
- Siguiente acción exacta: ejecutar **7.0 de `notas`**, y detenerse antes de
  7.1. No iniciar dos subcapas en el mismo turno.
