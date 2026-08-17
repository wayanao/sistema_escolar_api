# Capa 6: asignaciones y estudiantes

Última revisión: 2026-08-17.

## Control

- Estado: **Activa** desde el 2026-08-17.
- Commit base: `589cb6d1391161c692a6f24aee9d523317cbb1ce`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`, que el reflog registra como publicada por push el 2026-08-17.
  A diferencia de todas las activaciones anteriores salvo la de la capa 5, el
  commit base **ya está desplegado**: un push a `main` dispara el despliegue en
  este repositorio.
- Primera subcapa pendiente: **6.0**, inventario, contratos y caracterización.
  **No iniciada.**
- Código de producto modificado al activar: **ninguno**.
- Autorización: orden explícita del usuario el 2026-08-17, coincidente con la
  autorización puntual que `PROMPT_CONTINUACION.md` conservaba para la capa 6 y
  cuya condición de caducidad se cumplía. El usuario decidió además, de forma
  explícita, continuar aceptando las verificaciones heredadas pendientes. La
  activación **no** autoriza inspeccionar código de la capa 6 ni iniciar 6.0 en
  ese mismo turno.

## Objetivo

Separar los dominios de asignaciones y estudiantes con contratos estables,
trabajando cada dominio en subcapas y evitando una extracción conjunta masiva,
y protegiendo permisos, relaciones académicas, archivos e historial.

El objetivo procede exclusivamente del índice maestro. La activación no
inspeccionó el código y por eso **no afirma todavía** qué endpoints, archivos,
consultas, escrituras, archivos binarios o pruebas forman estos dominios. Esa
determinación es trabajo de 6.0.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0. El último
  resultado registrado, tras las tres correcciones puntuales posteriores al
  cierre de la capa 5, es **669 pruebas, exit 0**, Ruff correcto y `pip check`
  íntegro; no se reprodujo durante esta activación documental. 6.0 debe
  reproducirlo antes de tocar nada.
- Ciclo de vida de conexiones, transacciones y timeouts definido en la capa 1.
  El valor operativo final de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptado**: el candidato de 15000 ms está documentado y **no aplicado**, y
  continúa vigente 30000.
- DB síncrona fuera del event loop y limitador compartido de capacidad
  establecidos en la capa 2. Esta capa no puede reintroducir trabajo bloqueante
  en el event loop ni cambiar esa capacidad sin una nueva auditoría. Sobre esa
  constante pesa además el pendiente heredado del 2026-08-17: se quedó sin
  ejemplo real que la respalde y se conserva como margen.
- Tenants versionados y alta reproducible cerrados en la capa 3. Quedan dos
  schemas, `tenant_2005` —el único de producción— y `tenant_colegio_1`
  —plantilla y demo—, ambos con 37 claves foráneas, 30 secuencias propias y 30
  migraciones registradas.
- Contratos de lectura financieros fijados por la capa 4 y protegidos por su
  caracterización, con los conteos 6/15 del estado de cuenta de reportes,
  1/13/37 de cuentas y 5/12/12 de cartera.
- Frontera de persistencia de pagos establecida en la capa 5:
  `app/repositories/pagos_repository.py` con 16 funciones que reciben el cursor.
  Es el patrón que esta capa debe seguir si extrae persistencia, incluida la
  regla de no crear abstracciones compartidas sin dos usos reales.
- La última evidencia de GitHub Actions corresponde a la capa 0. Hubo pushes
  autorizados el 2026-08-15 y el 2026-08-17, pero **no se ha obtenido evidencia
  de ningún run**; esa verificación permanece **pendiente y aceptada**. No se
  atribuye CI remota porque `HEAD` coincida con `origin/main`.

## Perfil de riesgo propio de esta capa

Estos dominios son mayores que los financieros y su perfil de riesgo cambia en
un punto que ninguna capa anterior tuvo: **tocan archivos, no solo filas**.

- **Un rollback de datos no deshace un archivo ya escrito.** Si el dominio de
  estudiantes escribe o borra archivos a través de `app/services/storage.py`,
  el rollback de una subcapa deja de ser puramente de código o de filas, y debe
  documentarse antes de ejecutarla, no después. Registrado en
  `PROMPT_CONTINUACION.md`; **no verificado en código**, porque la activación no
  inspecciona. 6.0 debe comprobarlo.
- **Las 26 claves foráneas repuestas en la capa 3** pueden hacer fallar
  inserciones y borrados que antes pasaban en silencio. Es más probable aquí que
  en pagos: asignaciones y estudiantes son precisamente las tablas que esas
  claves relacionan.
- **`cobros.calcular_deudas_estudiante` ya se consume desde estudiantes**, y la
  capa 4 fijó contratos de lectura que dependen de él. Mover o alterar ese
  camino puede romper informes financieros sin que fallen las pruebas del
  dominio que se está tocando. Registrado en documentación; a verificar en 6.0.
- **El historial académico no se recalcula.** Notas, asistencia y boletines son
  datos acumulados; un error de escritura no produce un informe equivocado sino
  un expediente equivocado.
- Los permisos aquí no son uniformes como en pagos, donde solo alcanzaba
  `rol == 'admin'` estricto. Estos dominios los consumen también profesores, así
  que el inventario de roles y ownership de 6.0 es parte del contrato de
  seguridad, no un detalle.

## Alcance autorizado

- Inventariar entradas HTTP, reglas, escrituras, consultas, archivos, pruebas y
  consumidores de asignaciones y estudiantes mediante búsquedas dirigidas.
- Caracterizar antes de extraer: rutas, métodos, payloads, status codes,
  permisos, roles, tenant, ownership, relaciones académicas, archivos,
  historial, orden, nulos, transacciones y errores.
- Separar progresivamente HTTP, reglas, servicios y persistencia, **un dominio a
  la vez y en subcapas**, con pruebas de caracterización previas a cada
  extracción importante.
- Contar y comparar consultas y escrituras críticas antes y después.
- Medir con `EXPLAIN ANALYZE` conforme al criterio corregido en la capa 4:
  `SELECT` en producción bajo transacción `READ ONLY` cerrada con `rollback`.
  Ninguna medición puede escribir.

## Fuera de alcance

- Una extracción conjunta de asignaciones y estudiantes. El índice lo prohíbe
  expresamente: cada dominio va en sus propias subcapas.
- El resto de dominios, que pertenecen a la capa 7, salvo la lectura mínima
  indispensable para caracterizar un contrato consumido desde aquí.
- Los siete hallazgos abiertos de la capa 5, incluido el **paso 2 de la clave de
  idempotencia** y el cambio de status codes a 500. Están registrados en
  `05_PAGOS_TIPOS_PAGO.md` y **no entran por inferencia**.
- El trabajo registrado en `PROMPT_CONTINUACION.md` bajo «trabajo fuera del
  alcance de la capa activa»: colisión de mayúsculas en reportes,
  `/estado-cuenta/curso`, los 14 índices duplicados, la deduplicación de
  `_tabla_pagos_aplicaciones_existe` y la auditoría de capacidad de la capa 2.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, reglas
  académicas, orden o semántica transaccional.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, el limitador de concurrencia, el ORM, el driver o el almacenamiento
  de archivos.
- Migraciones reales, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción. Incluye los caminos de profesor, no solo los de admin.
- Relaciones académicas, historial, archivos adjuntos y su nomenclatura
  conservan su resultado actual.
- Los límites de transacción se conservan: qué se confirma junto, qué se
  revierte junto y quién es dueño de `commit`, `rollback`, cursor y conexión,
  conforme a la capa 1.
- Ninguna operación DB síncrona vuelve al event loop ni se altera el limitador
  compartido sin medir de nuevo su capacidad.
- Los contratos de lectura financieros fijados por la capa 4 siguen pasando su
  caracterización, incluidos los conteos 6/15, 1/13/37 y 5/12/12.
- El SQL de dominio se conserva hasta que una subcapa autorice, con
  caracterización previa, un cambio concreto.
- Ninguna escritura de archivos cambia de momento, de nombre ni de destino sin
  una decisión explícita y un rollback documentado.

## Línea base

Pendiente: la establece 6.0. No se reprodujo durante la activación documental.

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Por determinar en 6.0 | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente; último registrado 669, exit 0 |
| Ruff | Ejecutado por la compuerta global y sobre el alcance | Pendiente |
| Dependencias | Ejecutado por la compuerta global | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 6.0 | Inventario, contratos, caracterización y línea base de consultas, escrituras y archivos | **Pendiente, no iniciada** |
| 6.1 en adelante | **Sin decidir.** El desglose se define con la evidencia de 6.0, no antes | Sin definir |

El desglose posterior a 6.0 se deja explícitamente sin decidir, igual que en la
capa 5, para no inventar detalles de implementación antes de inspeccionar el
código. Las subcapas innecesarias se marcarán `No aplica` con explicación.

Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa activa: trabajo exacto de 6.0

1. Confirmar `main`, árbol limpio y que todo commit posterior al base
   `589cb6d1391161c692a6f24aee9d523317cbb1ce` esté explicado en esta bitácora.
2. Reproducir la compuerta heredada y determinar las pruebas específicas sin
   ampliar el alcance.
3. Localizar mediante búsquedas dirigidas únicamente la documentación, entradas
   HTTP, archivos fuente y pruebas de asignaciones y estudiantes.
4. Inventariar responsabilidades y dependencias actuales sin mover código:
   HTTP, reglas, persistencia, cálculos, escrituras, archivos y efectos
   laterales.
5. Registrar los contratos observables exactos: rutas, métodos, payloads, status
   codes, permisos por rol, tenant, ownership, relaciones académicas, historial,
   archivos, orden, nulos, transacciones y errores.
6. Comprobar con evidencia los tres puntos que esta activación registra **sin
   verificar**: si estos dominios escriben archivos vía `app/services/storage.py`
   y en qué momento respecto del `commit`; si `calcular_deudas_estudiante` se
   consume desde estudiantes y qué contratos de la capa 4 dependen de ello; y
   qué claves foráneas de la capa 3 afectan a estas tablas.
7. Caracterizar con pruebas los caminos que una extracción posterior pueda
   alterar, incluidas las escrituras y los archivos. 6.0 no autoriza una
   extracción ni un cambio de producto.
8. Medir o instrumentar herméticamente el número de consultas y escrituras de
   los caminos críticos; no optimizarlos todavía.
9. Ejecutar las pruebas específicas, Ruff del alcance, la compuerta global y
   `git diff --check`; revisar que el diff pertenezca solo a 6.0.
10. Actualizar esta bitácora, definir 6.1 con la evidencia obtenida y detenerse
    sin iniciarla.

## Criterios de cierre de la subcapa 6.0

- Los dos dominios y sus consumidores están inventariados con archivos y puntos
  de entrada concretos, sin lectura global innecesaria, y **separados entre sí**:
  el inventario debe dejar claro dónde termina uno y empieza el otro.
- Los contratos HTTP, de permisos por rol, tenant, ownership, académicos, de
  archivos y de transacción están enumerados y protegidos por caracterización
  suficiente.
- Las escrituras críticas y las escrituras de archivos están identificadas con
  una línea base reproducible, no por inferencia.
- La dependencia con los contratos de lectura de la capa 4 está registrada con
  evidencia.
- No se modificó producto ni se inició una extracción.
- Pruebas específicas, Ruff, compuerta global y `git diff --check` terminan
  correctamente, y el diff es exclusivo de 6.0.
- La subcapa 6.1 queda definida y no iniciada.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- Asignaciones y estudiantes quedaron separados **cada uno en sus subcapas**,
  con contratos estables, y no mediante una extracción conjunta.
- Permisos, relaciones académicas, archivos e historial están protegidos por
  caracterización y conservados.
- Los contratos del frontend y de la base de datos permanecen intactos.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- Staging, rollback y verificación manual están documentados; el rollback debe
  cubrir explícitamente los archivos, no solo las filas y el código.
- La capa 7 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- Se usa `589cb6d1391161c692a6f24aee9d523317cbb1ce` como commit base porque es
  el `HEAD` limpio vigente de `main` y coincide con la referencia local
  `origin/main`. No se reutilizó ningún hash de memoria: se comprobó el `HEAD`
  real antes de registrarlo.
- El usuario eligió explícitamente continuar manteniendo pendientes la
  calibración de `DB_STATEMENT_TIMEOUT_MS` y la evidencia remota de GitHub
  Actions. Ninguna se marca como cumplida y ambas conservan su riesgo.
- La activación consume la autorización puntual que `PROMPT_CONTINUACION.md`
  guardaba para la capa 6; queda retirada de ese archivo con el mismo criterio
  aplicado a las capas 3, 4 y 5.
- El mismo turno corrigió, con autorización explícita, el estado de publicación
  de la capa 5, que el índice y su bitácora seguían declarando sin push. Ese
  trabajo es exclusivamente documental y está registrado en
  `05_PAGOS_TIPOS_PAGO.md`.
- El commit base **está publicado y desplegado**, no solo local. Es por tanto un
  punto de rollback real, pero revertir a él exigiría otro push y otro
  despliegue, no una operación local.
- El desglose de subcapas posteriores a 6.0 se deja explícitamente sin decidir
  para no inventar detalles de implementación antes de inspeccionar el código.

## Riesgos

- **Los archivos son el riesgo nuevo de esta capa.** Un rollback de código o de
  datos no deshace un archivo ya escrito ni recupera uno borrado. Cualquier
  subcapa que toque `storage` debe documentar su rollback de archivos **antes**
  de ejecutarse.
- Estos dominios son los más grandes del programa. El riesgo de una extracción
  conjunta masiva es real y el índice lo prohíbe; el desglose por dominio y
  subcapa es la mitigación, y debe respetarse aunque parezca más lento.
- Las 26 claves foráneas repuestas en la capa 3 relacionan precisamente estas
  tablas. Inserciones y borrados pueden fallar donde antes pasaban en silencio.
  Se documentará el comportamiento y no se cambiarán las claves por inferencia.
- Los contratos de lectura financieros de la capa 4 dependen de código que estos
  dominios consumen. Pueden romperse desde aquí sin que fallen las pruebas de
  asignaciones o estudiantes. La mitigación es verificar sus conteos y payloads
  en cada subcapa.
- Los permisos no son uniformes: intervienen roles distintos de `admin`. Un
  inventario incompleto de roles es un riesgo de seguridad, no de calidad.
- El historial académico es acumulado: un error de escritura produce un
  expediente equivocado, no un informe recalculable.
- Heredado de la capa 1: `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrar contra
  volumen representativo y el deadline HTTP/proxy externo.
- Heredado de la capa 0: no hay evidencia de GitHub Actions posterior a esa
  capa. Las verificaciones locales no se presentarán como CI remota.
- Heredado de la capa 2: `MAX_DB_CONNECTIONS_PER_THREADPOOL_WORKER = 2` se
  quedó sin ejemplo real que la respalde y se conserva como margen. Si esta capa
  encontrara un camino que anida conexiones, es evidencia relevante y debe
  registrarse, no actuarse.
- Heredado de la capa 4: la credencial privilegiada compartida en chat sigue
  **sin rotar** y no debe reutilizarse.
- Heredado de la capa 5: siete hallazgos sin corregir, incluido `POST /pagos`
  sin clave de idempotencia. No se corrigen desde aquí.
- **Nuevo respecto a todas las capas anteriores salvo la 5**: el commit base ya
  está desplegado. Un push a `main` en este repositorio dispara el despliegue,
  así que la publicación de esta capa afectará a producción en cuanto ocurra.

## Registro de ejecución

### 2026-08-17 — activación de la capa

- Modo de acceso: mismo checkout local; Git validado directamente en
  `C:\Users\David\Documents\sistema_escolar_api`. No se usó GitHub para inferir
  el estado local.
- Autorización: orden explícita del usuario en este turno —«esta es la base
  589cb6d, solo documental, y activa la capa 6»—, coincidente con la
  autorización puntual que `PROMPT_CONTINUACION.md` conservaba para la capa 6 y
  cuya condición de caducidad se cumplía: el índice seguía sin capa activa y con
  la 6 en espera. La decisión sobre las verificaciones heredadas se pidió por
  separado y el usuario eligió **continuar aceptándolas como pendientes**.
- Rama acordada: `main`.
- Estado antes de escribir: árbol limpio, verificado con
  `git status --porcelain=v1`; `HEAD` y la referencia local `origin/main` en
  `589cb6d1391161c692a6f24aee9d523317cbb1ce`.
- Continuidad: el base de la capa 5,
  `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`, existe y es ancestro de `HEAD`.
  Sus **diez** commits posteriores forman una historia lineal. Nueve estaban
  explicados en `05_PAGOS_TIPOS_PAGO.md`: activación `42c9960`, cierre de 5.0
  `7718c37`, 5.1 `ebc1bd8`, 5.2 `72fc12e`, 5.3 y cierre de la capa `dcf7ffd`,
  candado de registro `11565eb`, retiro del hallazgo de ownership `a464b59`,
  logger de fallos absorbidos `27df23c` y una sola conexión por upsert
  `544bd5c`. El décimo, `589cb6d`, **no tenía entrada**; se comprobó que es
  documental —un solo archivo, `PROMPT_CONTINUACION.md`, +21/−5— y quedó
  registrado en la bitácora de la capa 5 antes de activar.
- Estado remoto: el reflog registra `update by push` de `544bd5c` y de
  `589cb6d`. La capa 5 y sus tres correcciones puntuales **están publicadas**, al
  contrario de lo que el índice y su bitácora seguían afirmando. **No se
  consultó ni se atribuye ningún run de GitHub Actions**; esa evidencia sigue sin
  obtenerse.
- Ambigüedad encontrada y corregida antes de activar: el índice y la bitácora de
  la capa 5 declaraban «sin push ni despliegue» y dejaban «publicar la capa» como
  pendiente operativo, contradiciendo el reflog. Se informó al usuario, que
  autorizó explícitamente la corrección documental. Las líneas fechadas que
  describían el estado del 2026-08-16 se conservaron intactas, con una nota que
  advierte que ya no son el estado vigente.
- Archivos creados o modificados: esta bitácora,
  `docs/modularizacion/README.md`, `docs/modularizacion/05_PAGOS_TIPOS_PAGO.md`
  y `docs/modularizacion/PROMPT_CONTINUACION.md`.
- Código de producto, pruebas, consultas, configuración, dependencias y workflow
  inspeccionados o modificados: **ninguno**. No se inspeccionó código de
  asignaciones ni de estudiantes.
- Pruebas, migraciones, conexiones a PostgreSQL, acceso a producción, commit,
  push y deploy: **ninguno**.
- Comandos de precondición: `git rev-parse --show-toplevel`,
  `git branch --show-current`, `git status --porcelain=v1`, `git status -sb`,
  `git log --oneline`, `git rev-parse HEAD`, `git rev-parse origin/main`,
  `git merge-base --is-ancestor`, `git log --reverse` desde el base de la capa 5,
  `git show --stat 589cb6d` y `git reflog show origin/main`; todos con resultado
  coherente con la activación.
- Estado al cerrar el turno de activación: capa 6 **activa**; 6.0 **pendiente y
  no iniciada**.
- Siguiente acción exacta: ejecutar únicamente 6.0 conforme al trabajo exacto de
  arriba y detenerse antes de 6.1.

## Entrega al próximo chat

- Capa activa: **6, asignaciones y estudiantes**.
- Última subcapa terminada: **ninguna**. La capa acaba de activarse.
- Primera subcapa pendiente: **6.0**, inventario, contratos y caracterización.
- Commit base: `589cb6d1391161c692a6f24aee9d523317cbb1ce`, rama `main`, árbol
  limpio y **ya publicado y desplegado**.
- Bloqueos: ninguno. Verificaciones heredadas pendientes y aceptadas: valor
  operativo final de `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub
  Actions posterior a la capa 0. La credencial privilegiada de la capa 4 sigue
  sin rotar.
- Lo que esta capa debe recordar antes de tocar nada: **toca archivos, no solo
  filas**. Un rollback de datos no deshace un archivo ya escrito. Además, estos
  dominios los consumen roles distintos de `admin`, las claves foráneas de la
  capa 3 los relacionan directamente, y los contratos financieros de la capa 4
  dependen de código que consumen.
- Siguiente acción exacta: ejecutar únicamente 6.0 y detenerse antes de 6.1. No
  iniciar dos subcapas en el mismo turno.
