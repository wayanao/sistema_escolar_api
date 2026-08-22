# Capa 7: plan_de_clases

Última revisión: 2026-08-22.

## Control

- Estado: **Activa** desde el 2026-08-22 por orden explícita del usuario.
- Commit base: `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0, no iniciada**.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **`plan_de_clases`, y solo ese**. `branding`,
  `profesores` y `super_admin` siguen en espera.
- Autorización: el usuario informó «planeador revisado» y ordenó «sigue con
  plan de clases». La verificación manual de `planeador_anual` se registra como
  completada de forma global, sin atribuir entorno ni confirmación individual
  de los siete puntos que no fueron reportados.
- Ninguna autorización incluye implementar 7.0 en este turno, commit, push,
  deploy, migraciones reales ni acceso a producción.

## Objetivo

Migrar el dominio de **plan de clases** con contratos y pruebas, conservando su
comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspeccionó código. Por eso no afirma qué archivos, rutas,
consultas, escrituras, permisos, archivos almacenados o pruebas forman la
frontera. Determinarlo es el primer trabajo de 7.0.

## Dependencias de capas anteriores

- La capa 7 para `planeador_anual` está cerrada: 7.0 y 7.1 completas, 7.2
  **No aplica**, compuerta final con **987 pruebas**, Ruff correcto y
  dependencias íntegras.
- El usuario reportó después «planeador revisado». La verificación manual se
  considera completada de forma global y suficiente para continuar, pero no se
  conoce el entorno ni consta el resultado separado de los siete puntos.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`.
- Los cuatro commits posteriores al base de `planeador_anual` están explicados:
  `6358c5a` activa el dominio, `2a8d3c3` contiene 7.0, `51203da` contiene 7.1 y
  `bfe80d4` cierra la capa y documenta la verificación manual entonces
  pendiente. Este último toca únicamente la bitácora y el índice maestro.
- La referencia local `origin/main` coincide con el commit base. No se consultó
  el remoto real ni se atribuye publicación, despliegue o GitHub Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales no confirmados heredados de `ventas`, `asistencia`,
  `boletin` y `observaciones`; y la rotación de la credencial privilegiada
  registrada en la capa 4.

## Supuestos documentales que 7.0 debe comprobar

La activación conserva como **no verificados** los siguientes datos del índice
y de la bitácora cerrada de `planeador_anual`:

1. `plan_de_clases` tiene una frontera propia separada de `planeador_anual`.
2. `GET /notificaciones/planeadores` pertenece a este dominio y llama a su
   propio controlador y servicio.
3. Existe ya un repositorio propio, pero no se sabe si cubre toda la
   persistencia del dominio.
4. Tres handlers con «observacion» en el nombre pertenecen a este dominio y no
   al dominio cerrado `observaciones`.
5. Esos handlers escriben una tabla documentada como
   `plan_de_clases_observaciones`.
6. El dominio usa `app/services/storage.py`, lo que podría convertir archivos y
   efectos externos en parte del contrato y del rollback.
7. No están determinados sus métodos, paths, payloads, status codes, permisos,
   ownership, tenant, SQL, transacciones, conexiones, cálculos ni efectos
   laterales completos.
8. No está determinado si las pruebas existentes bastan para proteger una
   extracción.

7.0 debe confirmar, matizar, refutar o separar uno por uno estos supuestos. No
se actúa sobre ninguno durante la activación.

## Alcance autorizado

- Trabajar únicamente en el dominio `plan_de_clases`.
- En 7.0, delimitar primero su frontera por rutas, llamadores, tablas,
  consumidores y efectos de almacenamiento, no solo por nombres de archivo.
- Inventariar entradas HTTP, permisos, ownership, tenant, payloads, status
  codes, respuestas, cálculos, SQL, tablas, transacciones, conexiones, archivos
  y otros efectos laterales.
- Resolver uno por uno los supuestos documentales indicando si quedan
  confirmados, incompletos, refutados o mal atribuidos.
- Agregar caracterización antes de cualquier extracción importante.
- Medir consultas, conexiones y operaciones de almacenamiento críticas antes y
  después de cualquier cambio de producto posterior.

## Fuera de alcance

- `branding`, `profesores` y `super_admin`, que siguen en espera.
- Reabrir por inferencia `planeador_anual`, `observaciones` u otro dominio
  cerrado.
- Corregir hallazgos abiertos de las capas 1 a 7 o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  cálculos, SQL observable, transacciones, archivos o comportamiento actual sin
  una autorización explícita apoyada en la caracterización.
- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas tenant, el pool, los
  timeouts, la concurrencia, el ORM, el driver o el proveedor de almacenamiento.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos orden, nulos y errores.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- SQL, parámetros, número y orden observable de operaciones y límites de
  transacción se conservan.
- Se conserva quién posee conexión, cursor, `commit`, `rollback`, archivos y
  efectos de almacenamiento.
- Ninguna operación DB síncrona vuelve al event loop ni se cambia el limitador
  compartido sin una medición de capacidad propia.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Se determinará en 7.0 tras delimitar las pruebas realmente relacionadas | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Sobre la caracterización y cualquier archivo permitido por 7.0 | Pendiente |
| Dependencias | Incluido en `scripts\verify.py` | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Delimitar la frontera, inventariar contratos y caracterizar el comportamiento y la línea base | **Pendiente, no iniciada** |
| 7.1 | Primera extracción protegida que la evidencia de 7.0 justifique | Pendiente |
| 7.2 | Segunda extracción, integración o cambio adicional, solo si la evidencia y el usuario lo autorizan | Pendiente |
| 7.3 | Retiro heredado y cierre, solo si resulta necesario | Pendiente |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No
aplica` con una explicación; nunca se ejecutan dos en el mismo turno.

## Subcapa activa: trabajo exacto de 7.0

1. Delimitar la frontera real de `plan_de_clases` por entradas, llamadores,
   tablas, consumidores y efectos de almacenamiento antes de contar o modificar
   nada.
2. Inspeccionar únicamente la documentación, fuentes y pruebas relacionadas
   con esa frontera; separar expresamente las piezas nominales de
   `planeador_anual` y `observaciones`.
3. Inventariar métodos, paths, guards, permisos, payloads, status codes,
   respuestas, orden, nulos y errores de cada entrada.
4. Inventariar SQL inline y delegado, tablas, transacciones, propiedad de
   conexión/cursor y operaciones sobre archivos o servicios externos.
5. Identificar y fijar por prueba cálculos, orden, nombres, contenido y otros
   efectos observables antes de cualquier extracción.
6. Medir consultas, conexiones y operaciones de almacenamiento por camino,
   buscando N+1 o dependencia del tamaño de entrada o resultado.
7. Revisar solo las pruebas relacionadas y agregar caracterización sin cambiar
   expectativas heredadas salvo autorización explícita.
8. Resolver los ocho supuestos documentales y registrar hallazgos sin
   corregirlos.
9. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el índice maestro. **Ningún archivo de producto se modifica.**
10. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
    global, `git diff --check` y revisión de alcance.
11. Actualizar esta bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
12. **Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.**

## Criterios de cierre de la subcapa

- La frontera queda delimitada con evidencia y sin reabrir otros dominios.
- Los ocho supuestos quedan resueltos uno por uno.
- Existe caracterización ejecutable de contratos, SQL, transacciones,
  consultas, conexiones, archivos y efectos laterales aplicables.
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

- **Activar `plan_de_clases` y solo ese dominio.** Motivo: el usuario lo nombró
  explícitamente y el índice exige trabajar uno por uno.
- **Registrar la verificación manual de `planeador_anual` como completada de
  forma global.** Motivo: el usuario informó «planeador revisado» y ordenó
  seguir. No se inventan entorno ni resultados punto por punto.
- **Mantener pendientes las verificaciones heredadas.** La orden no aporta
  evidencia nueva sobre ellas y ninguna se marca como cumplida.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre documental de `planeador_anual`; sus cuatro commits están explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera por nombres o referencias heredadas.** Los datos
  previos se registran como supuestos que 7.0 debe contrastar.

## Riesgos

- **Frontera desconocida.** El vocabulario se cruza con `planeador_anual` y
  `observaciones`. Mitigación: delimitar por rutas, llamadas, tablas y efectos.
- **Persistencia parcialmente migrada.** La documentación dice que existe un
  repositorio, pero no demuestra cobertura completa. Mitigación: contar SQL en
  todas las capas de la frontera antes de proponer una extracción.
- **Almacenamiento externo.** Si el uso documentado de `storage.py` se confirma,
  el rollback puede incluir archivos y no ser solo de código. Mitigación:
  caracterizar creación, lectura, reemplazo y eliminación antes de mover nada.
- **Permisos y tenant todavía desconocidos.** Mitigación: fijarlos por entrada y
  probar denegaciones y aislamiento antes de una extracción.
- **Verificaciones heredadas pendientes.** Conservan sus riesgos y esta
  activación no las considera cumplidas.
- **Cobertura manual de `planeador_anual` sin desglose.** La revisión reportada
  permite continuar, pero no demuestra individualmente los siete escenarios ni
  un entorno desplegado.

## Registro de ejecución

### 2026-08-22 — activación de la capa para `plan_de_clases`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git validado directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_PLANEADOR_ANUAL.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario informó «planeador revisado» y ordenó «sigue con plan
  de clases», nombrando el dominio.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `bfe80d4152b802aeb22f4c5a2c5aab9265ba7630`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: el base `235672e` de `planeador_anual` es ancestro. Sus cuatro
  descendientes son `6358c5a` —activación—, `2a8d3c3` —7.0—, `51203da` —7.1—
  y `bfe80d4` —cierre documental—. El último modifica únicamente la bitácora y
  el índice, tal como describe el cierre.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden. No se consultó el remoto real ni se verificó GitHub
  Actions.
- Verificación manual anterior: registrada como completada de forma global a
  partir del reporte «planeador revisado»; entorno y desglose no especificados.
- Decisión heredada: las demás verificaciones pendientes siguen abiertas con
  su riesgo y ninguna se marca como cumplida.
- Archivos creados o modificados: esta bitácora,
  `07_PLANEADOR_ANUAL.md` y `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para los dos
  archivos rastreados; la comprobación `--no-index --check` de esta bitácora
  nueva no reportó errores de whitespace —su exit 1 indica que difiere de
  `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
  `git status --short` mostró exactamente esta bitácora nueva y los otros dos
  documentos modificados. La tabla del índice y el conjunto de bitácoras
  contienen exactamente una capa marcada **Activa**, `plan_de_clases`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7 para `plan_de_clases`**.
- Última capa cerrada: **7 para `planeador_anual`**.
- Última subcapa terminada de esta bitácora: ninguna.
- Primera subcapa pendiente: **7.0, no iniciada**.
- Código de producto modificado al activar: ninguno.
- Verificación manual de `planeador_anual`: completada de forma global, sin
  entorno ni desglose punto por punto reportados.
- Verificaciones heredadas: pendientes; ninguna se marca como cumplida.
- Bloqueos técnicos: ninguno.
- Siguiente acción exacta: ejecutar solo la caracterización 7.0 de
  `plan_de_clases` y detenerse antes de cualquier extracción.
