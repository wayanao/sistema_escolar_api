# Capa 5: pagos y tipos de pago

Última revisión: 2026-08-15.

## Control

- Estado: **Activa** desde el 2026-08-15.
- Commit base: `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`, que el reflog registra como publicada por push el 2026-08-15 a
  las 13:20:16.
- Primera subcapa pendiente: **5.0, no iniciada**.
- Código de producto modificado al activar: **ninguno**.
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

## Línea base

Pendiente: se establece en 5.0. La activación es documental y no ejecutó
pruebas, lint ni compuerta.

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Se determinan en 5.0 | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Ejecutado por la compuerta global y sobre el alcance | Pendiente |
| Dependencias | Ejecutado por la compuerta global | Pendiente |

Referencia heredada: la compuerta al cerrar la capa 4 terminó en exit 0 con 606
pruebas.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 5.0 | Inventario, contratos, caracterización y línea base de consultas y escrituras | **Pendiente, no iniciada** |
| 5.1 | Primera extracción protegida | Pendiente, se define desde 5.0 |
| 5.2 | Segunda extracción o integración | Pendiente, se define desde 5.0 |
| 5.3 | Retiro heredado y cierre | Pendiente, se define desde 5.0 |

El desglose de 5.1 en adelante **no está decidido**: se deriva del inventario de
5.0 y no se inventa antes de inspeccionar. Las subcapas innecesarias se marcarán
`No aplica` con explicación.

Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa activa: 5.0 — trabajo exacto

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
  anterior y detenerse antes de 5.1.

## Entrega al próximo chat

- Capa activa: **5, pagos y tipos de pago**.
- Última subcapa terminada: ninguna. Primera subcapa pendiente: **5.0,
  inventario, contratos y caracterización**.
- Commit base: `f4d091329f84bcdd100b1bf0c70c02a0e32ee138`, rama `main`, ya
  publicado.
- Bloqueos: ninguno para iniciar 5.0.
- Verificaciones heredadas pendientes y aceptadas: valor operativo final de
  `DB_STATEMENT_TIMEOUT_MS` (capa 1) y evidencia de GitHub Actions posterior a
  la capa 0. Además, la credencial privilegiada compartida en la capa 4 sigue
  sin rotar.
- Lo que esta capa debe recordar antes de tocar nada: **escribe donde las
  anteriores solo leían**. Claves foráneas repuestas en la capa 3, contratos de
  lectura de `pagos` fijados en la capa 4, y `pagos.concepto_id` inexistente.
- Siguiente acción exacta: ejecutar solo 5.0 y detenerse antes de 5.1.
