# Capa 7: planeador anual

Última revisión: 2026-08-21.

## Control

- Estado: **Activa** desde el 2026-08-21.
- Commit base: `235672ea609444a46003175940376c37bfe191c4`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, no iniciada.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **`planeador_anual`, y solo ese**. Los otros cuatro
  dominios en espera necesitan su propia bitácora y su propia orden.
- Autorización: el usuario eligió la opción 2 —continuar localmente aceptando
  las verificaciones heredadas pendientes— y ordenó expresamente activar el
  dominio «planeador anual».
- La autorización cubre **solo esta activación documental**. No autoriza
  inspeccionar código del dominio, ejecutar 7.0, modificar producto, hacer
  commit, push, deploy, migraciones reales ni acceso a producción.

## Objetivo

Migrar el dominio de **planeador anual** con contratos y pruebas, conservando
su comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspeccionó código. Por eso no afirma qué archivos, rutas,
consultas, escrituras, permisos, fórmulas o pruebas pertenecen al dominio.
Determinarlo es el primer trabajo de 7.0.

## Dependencias de capas anteriores

- La capa 7 para `planilla` está cerrada: 7.0 y 7.1 completas, 7.2 **No
  aplica**, compuerta final con **957 pruebas**, Ruff correcto y dependencias
  íntegras.
- La verificación manual propia de `planilla` quedó completada y correcta con
  8 de 8 puntos reportados; el entorno no fue especificado.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `235672ea609444a46003175940376c37bfe191c4`.
- Los seis commits posteriores al base de `planilla` están explicados en su
  bitácora: activación, 7.0, 7.1, cierre y dos actualizaciones documentales de
  la verificación manual.
- La referencia local `origin/main` coincide con el commit base. No se consultó
  el remoto real ni se atribuye ninguna ejecución de GitHub Actions.
- Por decisión explícita del usuario, siguen pendientes y aceptadas: la
  calibración operativa final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub
  Actions posterior a la capa 0; pasos manuales no confirmados de `ventas`,
  `asistencia`, `boletin` y `observaciones`; y la rotación de la credencial
  privilegiada registrada en la capa 4.

## Lo que el programa cree saber y 7.0 debe comprobar

La documentación de continuidad solo confirma que `planeador_anual` era uno de
los cinco dominios en espera. Todo supuesto sobre su implementación permanece
**no verificado** hasta contrastarlo en 7.0.

| # | Supuesto documental | Estado al activar |
|---:|---|---|
| 1 | `planeador_anual` era un dominio pendiente de la capa 7 | **Confirmado documentalmente** por el índice y por la orden del usuario |
| 2 | Su frontera coincide con archivos que llevan ese nombre | **No verificado** |
| 3 | Tiene entradas HTTP propias | **No verificado** |
| 4 | Lee o escribe datos | **No verificado** |
| 5 | Abre transacciones o produce efectos laterales | **No verificado** |
| 6 | Sus permisos y reglas de ownership son uniformes | **No verificado** |
| 7 | Tiene servicio o repositorio propio | **No verificado** |
| 8 | Contiene cálculos o fórmulas observables | **No verificado** |
| 9 | Presenta N+1 de consultas o conexiones | **No verificado** |
| 10 | Sus pruebas actuales bastan para proteger una extracción | **No verificado** |

El nombre parecido a `plan_de_clases` no demuestra que compartan frontera,
datos ni comportamiento. Esa relación solo puede confirmarse o refutarse con
la inspección acotada de 7.0 y no autoriza tocar el dominio vecino.

## Alcance autorizado

- Trabajar únicamente en el dominio `planeador_anual`.
- En 7.0, delimitar primero su frontera por rutas, llamadas, tablas y
  consumidores, no solo por nombres de archivo.
- Inventariar entradas HTTP, archivos, permisos, ownership, tenant, payloads,
  status codes, respuestas, cálculos, SQL, tablas, transacciones, conexiones,
  efectos laterales, pruebas y consumidores del dominio.
- Resolver uno por uno los supuestos documentales, indicando si quedan
  confirmados, incompletos, refutados o mal atribuidos.
- Agregar caracterización antes de cualquier extracción importante.
- Medir consultas y conexiones críticas antes y después de cualquier cambio de
  producto posterior.

## Fuera de alcance

- `plan_de_clases`, `branding`, `profesores` y `super_admin`, que siguen en
  espera.
- Reabrir por inferencia `planilla` u otro dominio cerrado.
- Corregir hallazgos abiertos de las capas 1 a 7 o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  fórmulas, SQL observable, transacciones o comportamiento actual sin una
  autorización explícita apoyada en la caracterización.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, la concurrencia, el ORM, el driver o el almacenamiento.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de respuestas permanecen
  idénticos, incluidos orden, nulos y errores.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- Las fórmulas y cifras que 7.0 encuentre forman parte del contrato hasta que
  el usuario autorice expresamente un cambio.
- Se conservan texto SQL, parámetros, número y orden observable de operaciones
  y límites de transacción.
- Se conserva quién es dueño de conexión, cursor, `commit` y `rollback`.
- Ninguna operación DB síncrona vuelve al event loop ni se cambia el limitador
  compartido sin una medición de capacidad propia.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Por determinar en 7.0 después de delimitar la frontera | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente para 7.0; última compuerta heredada documentada: 957 pruebas |
| Ruff | Por determinar según el alcance de 7.0 | Pendiente |
| Dependencias | Incluido en `scripts\verify.py` | Pendiente para 7.0; íntegras en el cierre heredado |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Delimitar la frontera, inventariar contratos y caracterizar el comportamiento y la línea base | **Pendiente y no iniciada** |
| 7.1 | Primera extracción protegida, solo si la evidencia de 7.0 la justifica | En espera; alcance por definir |
| 7.2 | Cambio adicional posterior, solo si resulta necesario y autorizado | En espera; alcance por definir |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No
aplica` con una explicación. Nunca se ejecutan dos en el mismo turno.

## Subcapa 7.0: trabajo exacto pendiente

1. Delimitar la frontera real de `planeador_anual` por entradas, llamadores,
   tablas y consumidores antes de contar o modificar nada.
2. Inventariar métodos, paths, guards, permisos, payloads, status codes,
   respuestas, orden, nulos y errores de cada entrada del dominio.
3. Inventariar archivos y contar SQL inline en rutas, controladores, servicios
   y repositorios que pertenezcan realmente a la frontera.
4. Determinar si el dominio escribe, qué tablas toca, qué transacciones abre y
   quién posee conexión, cursor, `commit` y `rollback`.
5. Identificar y fijar por prueba cálculos, fórmulas, archivos y otros efectos
   observables antes de una extracción.
6. Medir consultas y conexiones por camino, buscando N+1 y dependencia del
   tamaño de la entrada o del resultado.
7. Revisar solo las pruebas relacionadas y crear o ampliar caracterización sin
   cambiar expectativas heredadas salvo autorización explícita.
8. Resolver los diez supuestos de esta bitácora y registrar los hallazgos sin
   corregirlos.
9. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el estado correspondiente del índice maestro. **Ningún archivo de
   producto se modifica.**
10. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
    global, `git diff --check` y revisión de alcance.
11. Actualizar la bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
12. **Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de la subcapa 7.0

- La frontera queda delimitada con evidencia y sin reabrir otros dominios.
- Los diez supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable de contratos, fórmulas, SQL,
  transacciones, consultas y conexiones aplicables.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, decisiones, riesgos y siguiente acción.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- La capa queda cerrada y el siguiente dominio permanece en espera hasta una
  nueva orden explícita.

## Decisiones

- **Activar `planeador_anual` y solo ese dominio.** Motivo: el usuario lo
  nombró explícitamente y el índice exige trabajar uno por uno.
- **Continuar localmente aceptando las verificaciones heredadas.** El usuario
  eligió expresamente la opción 2. Ninguna se marca como cumplida.
- **Usar el `HEAD` limpio vigente como commit base.** Motivo: es el punto
  posterior al cierre y a la actualización de la verificación manual de
  `planilla`; toda su historia posterior al base anterior está explicada.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera por el nombre.** La semejanza con
  `plan_de_clases` se registra como riesgo, no como autorización para incluirlo.

## Riesgos

- **Frontera todavía desconocida.** El nombre del dominio puede no coincidir
  con archivos, rutas o tablas. Mitigación: delimitar por comportamiento y
  consumidores en el primer paso de 7.0.
- **Perfil de escritura desconocido.** No se sabe aún si el dominio modifica
  datos, archivos o ambos. Mitigación: resolverlo antes de decidir una
  extracción.
- **Cifras o estructura anual como contrato.** Cualquier cálculo u orden que
  aparezca debe caracterizarse antes de moverlo.
- **Verificaciones heredadas pendientes y aceptadas.** Conservan sus riesgos y
  no se consideran cumplidas por activar este dominio.
- **Posible vecindad con `plan_de_clases`.** Compartir vocabulario no demuestra
  dos usos reales ni una frontera común; incluirlo ampliaría el alcance sin
  autorización.

## Registro de ejecución

### 2026-08-21 — activación de la capa para `planeador_anual`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_PLANILLA.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario eligió la opción 2, aceptó continuar localmente con
  las verificaciones heredadas pendientes y nombró «planeador anual».
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1` produjo
  salida vacía.
- Commit base: `235672ea609444a46003175940376c37bfe191c4`, el `HEAD`
  limpio vigente.
- Continuidad: `580c0ad`, base de `planilla`, es ancestro de `HEAD`. Sus seis
  descendientes corresponden a `50d6d41` —activación—, `e8e3336` —7.0—,
  `5019fd2` —7.1—, `838b71b` —cierre—, `485ed78` —registro documental de la
  verificación manual— y `235672e` —ajuste final del índice sobre esa misma
  verificación—. Todos pertenecen a la continuidad descrita en la bitácora.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden en `235672e`, con cero commits a favor o en contra.
  No se consultó el remoto real ni se verificó GitHub Actions.
- Decisión heredada: las verificaciones pendientes continúan aceptadas con su
  riesgo y ninguna se marca como cumplida.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el archivo
  rastreado; la comprobación `--no-index --check` de esta bitácora nueva no
  reportó errores de whitespace —su exit 1 indica que el archivo difiere de
  `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
  `git status --short` mostró exactamente esta bitácora nueva y el índice
  maestro modificado. La tabla del índice contiene exactamente una fila
  marcada **Activa**, la de `planeador_anual`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7 para `planeador_anual`**.
- Última capa cerrada: **7 para `planilla`**.
- Última subcapa terminada: ninguna en este dominio.
- Primera subcapa pendiente: **7.0**, no iniciada.
- Código de producto modificado al activar: ninguno.
- Verificaciones heredadas: pendientes y aceptadas por decisión explícita.
- Bloqueos: ninguno.
- Siguiente acción exacta: ejecutar únicamente 7.0, actualizar esta bitácora y
  detenerse antes de 7.1.
