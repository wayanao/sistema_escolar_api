# Capa 7: branding

Última revisión: 2026-08-22.

## Control

- Estado: **Activa** desde el 2026-08-22 por orden explícita del usuario.
- Commit base: `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, no iniciada.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **`branding`, y solo ese**. `profesores` y
  `super_admin` siguen en espera.
- Autorización: el usuario nombró `branding`, ordenó activarlo y, después de
  recibir la advertencia, confirmó continuar localmente aceptando que las
  verificaciones heredadas permanezcan pendientes.
- La activación es exclusivamente documental. No autoriza 7.0, commit, push,
  deploy, migraciones reales ni acceso a producción.

## Objetivo

Migrar el dominio de **branding** con contratos y pruebas, conservando su
comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar **un dominio a la vez**;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspecciona código ni infiere la frontera. La subcapa 7.0 debe
delimitarla con evidencia antes de proponer cualquier extracción.

## Dependencias de capas anteriores

- La capa 7 para `plan_de_clases` está cerrada: 7.0 y 7.1 completas, 7.2 y
  7.3 **No aplica**, compuerta final con **1011 pruebas**, Ruff correcto y
  dependencias íntegras.
- La verificación manual de `plan_de_clases` está completada de forma global
  con la reserva «aparentemente bien», sin entorno, artefacto ni desglose punto
  por punto.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b`.
- Los cinco commits posteriores al base de `plan_de_clases` están explicados en
  su bitácora: `31b3f6b` activa la capa, `80f7f21` contiene 7.0, `98c438f`
  contiene 7.1, `d6eeecf` contiene el cierre documental y `bb34cf6` registra
  la verificación manual posterior. El último modifica únicamente la bitácora
  y el índice maestro, como declara ese registro.
- La referencia local `origin/main` coincide con el commit base. No se consultó
  el remoto real ni se atribuye publicación, despliegue o GitHub Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales no confirmados heredados de `ventas`, `asistencia`,
  `boletin` y `observaciones`; y la rotación de la credencial privilegiada
  registrada en la capa 4.

## Supuestos documentales que 7.0 debe resolver

La activación no inspeccionó fuentes ni pruebas de `branding`. Estas referencias
del índice son **supuestos**, no conclusiones verificadas:

1. `branding` constituye una frontera de dominio pendiente y separable.
2. Usa `app/services/storage.py`; la capa 6 registró que solo `branding` y
   `plan_de_clases` consumían ese servicio en aquel momento.
3. La capa 2 registró una lectura async de branding que descargaba trabajo de
   almacenamiento y DB a un worker. 7.0 debe comprobar el estado vigente y la
   preservación del `ContextVar` del tenant.
4. Métodos, paths, payloads, status codes, permisos, ownership, respuestas,
   SQL, conexiones, transacciones y efectos de almacenamiento están por
   determinar.
5. La cantidad y ubicación de archivos, rutas, pruebas, consumidores y
   persistencia propias están por determinar.
6. No está verificado si el dominio escribe base de datos, archivos o ambos, ni
   si existe N+1 de consultas, conexiones u operaciones de almacenamiento.

La subcapa 7.0 debe confirmar, matizar, refutar o atribuir correctamente cada
supuesto, sin corregir los hallazgos que descubra.

## Alcance autorizado

- Trabajar únicamente en el dominio `branding`.
- En 7.0, delimitar primero su frontera por rutas, llamadores, tablas,
  consumidores y efectos de almacenamiento, no solo por nombres de archivo.
- Inventariar entradas HTTP, permisos, ownership, tenant, payloads, status
  codes, respuestas, SQL, transacciones, conexiones, archivos y demás efectos
  laterales.
- Resolver uno por uno los supuestos documentales con evidencia.
- Agregar caracterización antes de cualquier extracción importante.
- Medir consultas, conexiones y operaciones de almacenamiento críticas antes
  y después de cualquier cambio de producto posterior.

## Fuera de alcance

- `profesores` y `super_admin`, que siguen en espera.
- Reabrir por inferencia `plan_de_clases` u otro dominio cerrado.
- Corregir hallazgos abiertos de las capas 1 a 7 o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  SQL observable, transacciones, archivos o comportamiento actual sin una
  autorización explícita apoyada en la caracterización.
- Cambiar PostgreSQL, `psycopg2`, schemas tenant, pool, timeouts, concurrencia,
  ORM, driver o proveedor de almacenamiento.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos, incluidos orden, nulos y errores.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- SQL, parámetros, número y orden observable de operaciones y límites de
  transacción se conservan.
- Se conserva quién posee conexión, cursor, `commit`, `rollback`, archivos y
  efectos de almacenamiento.
- Ninguna operación DB o de almacenamiento síncrona vuelve al event loop ni se
  altera la propagación del tenant sin caracterización y autorización.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Por determinar después de delimitar la frontera en 7.0 | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Alcance por determinar en 7.0 | Pendiente |
| Dependencias | Incluidas en la compuerta global | Pendiente |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos, almacenamiento y caracterización | **Pendiente** |
| 7.1 | Primera extracción protegida, solo si la evidencia la justifica | Pendiente |
| 7.2 | Segunda extracción o integración, solo si se autoriza | Pendiente |
| 7.3 | Retiro heredado y cierre, si aplica | Pendiente |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No aplica`
con una explicación; nunca se ejecutan dos sin orden explícita.

## Subcapa activa: trabajo exacto de 7.0

1. Delimitar la frontera real de `branding` por entradas, llamadores, tablas,
   consumidores y efectos de almacenamiento antes de contar o modificar nada.
2. Inspeccionar únicamente la documentación, fuentes y pruebas relacionadas
   con esa frontera.
3. Inventariar métodos, paths, guards, permisos, payloads, status codes,
   respuestas, orden, nulos y errores de cada entrada.
4. Inventariar SQL inline y delegado, tablas, transacciones, propiedad de
   conexión/cursor y operaciones locales o remotas de almacenamiento.
5. Comprobar el límite async/síncrono, el offload y la propagación del tenant
   sin cambiar la concurrencia.
6. Medir consultas, conexiones y operaciones de almacenamiento por camino,
   buscando dependencia del tamaño de entrada o resultado.
7. Revisar solo las pruebas relacionadas y agregar caracterización sin cambiar
   expectativas heredadas.
8. Resolver los seis supuestos documentales y registrar hallazgos sin
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
- Los seis supuestos quedan resueltos uno por uno.
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

- **Activar `branding` y solo ese dominio.** El usuario lo nombró y después
  ordenó activarlo explícitamente.
- **Continuar localmente con las verificaciones heredadas pendientes.** El
  usuario confirmó la alternativa después de recibir la advertencia; ninguna
  verificación se considera cumplida y sus riesgos permanecen vigentes.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre y al registro de verificación manual de `plan_de_clases`; todos sus
  descendientes desde el base anterior están explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera por nombres o referencias heredadas.** Los datos
  previos se registran como supuestos que 7.0 debe contrastar.

## Riesgos

- **Verificaciones heredadas pendientes.** Se aceptó continuar sin cerrarlas;
  conservan su riesgo y esta capa no puede presentarlas como cumplidas.
- **Almacenamiento con efectos externos.** La documentación vincula branding
  con `storage.py`; hasta 7.0 no se conocen propiedad, compensaciones ni punto
  real de rollback.
- **Límite async/síncrono y tenant.** La capa 2 protegió un camino de branding;
  una extracción podría bloquear el event loop o perder el `ContextVar` si no
  conserva el offload vigente.
- **Frontera y consumidores desconocidos.** Inspeccionar por nombres podría
  omitir rutas o piezas compartidas, como ocurrió en dominios anteriores.
- **Publicación no comprobada contra el remoto real.** Solo se observó que la
  referencia local `origin/main` coincide con `HEAD`; no se atribuye despliegue
  ni GitHub Actions.

## Registro de ejecución

### 2026-08-22 — activación de la capa para `branding`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_PLAN_DE_CLASES.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario nombró `branding`, ordenó activarlo y confirmó
  continuar localmente aceptando las verificaciones heredadas pendientes.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `bb34cf6f31413fdbbd2c1866b43f2da71f8ea03b`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: el base `bfe80d4` de `plan_de_clases` es ancestro. Sus cinco
  descendientes son `31b3f6b` —activación—, `80f7f21` —7.0—, `98c438f`
  —7.1—, `d6eeecf` —cierre documental— y `bb34cf6` —registro de la
  verificación manual—. Todos están explicados en esa bitácora; el último toca
  únicamente esa bitácora y el índice, como declara su registro.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden. No se consultó el remoto real ni se verificó GitHub
  Actions.
- Decisión heredada: permanecen pendientes la calibración de timeout, la
  evidencia de CI, los pasos manuales no confirmados y la rotación de la
  credencial privilegiada. El usuario aceptó continuar con sus riesgos.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el índice;
  `git diff --no-index --check -- NUL docs/modularizacion/07_BRANDING.md` no
  reportó errores de whitespace —su exit 1 indica que el archivo nuevo difiere
  de `NUL`—. Los avisos fueron únicamente de normalización futura LF/CRLF.
- Revisión de alcance: `git status --short --branch` mostró exactamente el
  índice modificado y esta bitácora nueva sobre `main...origin/main`. La tabla
  del índice contiene una sola fila **Activa** y el conjunto de bitácoras una
  sola declaración de estado **Activa**, ambas para `branding`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7 para `branding`**.
- Última subcapa terminada: ninguna; la activación fue documental.
- Primera subcapa pendiente: **7.0**, inventario, contratos, almacenamiento y
  caracterización.
- Verificaciones heredadas: pendientes por decisión explícita del usuario.
- Dominios en espera: `profesores` y `super_admin`.
- Bloqueos: ninguno.
- Siguiente acción exacta: ejecutar únicamente 7.0 y detenerse antes de 7.1.
