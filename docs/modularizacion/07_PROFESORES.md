# Capa 7: profesores

Última revisión: 2026-08-23.

## Control

- Estado: **Activa** desde el 2026-08-23 por orden explícita del usuario.
- Commit base: `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.0**, inventario, contratos y
  caracterización.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **`profesores`, y solo ese**.
- Autorización: el usuario escribió «activa el dominio proefesores»; se
  interpreta la errata inequívoca como `profesores`, el dominio que estaba en
  espera y que había sido ofrecido expresamente en el turno anterior.
- Decisión sobre verificaciones pendientes: la orden respondió a la alternativa
  previamente planteada y autoriza continuar localmente aceptando que la
  verificación manual de `branding` y las verificaciones heredadas permanezcan
  pendientes. Ninguna se marca como cumplida.
- La activación es exclusivamente documental. No autoriza implementar 7.0,
  hacer commit, push, deploy, migraciones reales ni acceder a producción.

## Objetivo

Migrar el dominio de **profesores** con contratos y pruebas, conservando su
comportamiento observable actual.

El índice maestro fija tres condiciones para esta capa:

1. trabajar un dominio a la vez;
2. agregar `response_model`, errores de dominio y pruebas HTTP o de integración
   solo después de caracterizar y conservar la respuesta existente;
3. no crear abstracciones compartidas sin dos consumidores reales.

La activación no inspecciona código ni infiere la frontera. La subcapa 7.0 debe
delimitarla con evidencia antes de proponer cualquier extracción.

## Dependencias de capas anteriores

- La capa 7 para `branding` está cerrada: 7.0 y 7.1 completas, 7.2 y 7.3
  **No aplica**, compuerta final con **1032 pruebas**, Ruff correcto y
  dependencias íntegras.
- La verificación manual propia de `branding` permanece pendiente.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6`.
- Los cuatro commits posteriores al base de `branding` están explicados en su
  bitácora: `f53711b` activa el dominio, `0083237` cierra 7.0, `5ddd504`
  contiene 7.1 y `58eb5c2` contiene el cierre documental. Sus archivos
  coinciden con el alcance registrado.
- `HEAD` y la referencia local `origin/main` coinciden en el commit base. No se
  consultó el remoto real ni se atribuye publicación, despliegue o GitHub
  Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales no confirmados heredados de `ventas`, `asistencia`,
  `boletin` y `observaciones`; la verificación manual propia de `branding`; y
  la rotación de la credencial privilegiada registrada en la capa 4.

## Supuestos documentales pendientes de resolver en 7.0

La activación no inspeccionó fuentes ni pruebas de `profesores`. Por tanto, los
siguientes puntos son preguntas de inventario, no afirmaciones sobre el código:

1. La frontera real del dominio, incluidos archivos con nombres distintos y
   consumidores externos, está por determinar.
2. La cantidad de entradas HTTP, sus permisos, roles, ownership, tenant,
   payloads, respuestas y status codes está por determinar.
3. Las tablas leídas o escritas, SQL inline o delegado, transacciones y
   propiedad de conexiones y cursores están por determinar.
4. Debe comprobarse si existen consultas, conexiones o efectos cuyo número
   crezca con el tamaño de la entrada o del resultado.
5. Deben identificarse contratos compartidos con dominios ya cerrados sin
   reabrirlos ni modificar sus fronteras por inferencia.
6. Debe inventariarse la cobertura heredada y distinguir las pruebas que
   observan HTTP real de las que invocan funciones directamente.

## Alcance autorizado

- Trabajar únicamente en el dominio `profesores`.
- En 7.0, delimitar primero la frontera real por rutas, llamadores, tablas,
  consumidores y efectos laterales, no solo por nombres de archivo.
- Inventariar métodos, paths, guards, permisos, ownership, tenant, payloads,
  status codes, respuestas, SQL, transacciones, conexiones y concurrencia.
- Resolver uno por uno los supuestos documentales con evidencia.
- Agregar o conservar pruebas de caracterización antes de cualquier extracción
  importante.
- Medir consultas y conexiones críticas antes y después de cualquier cambio de
  producto posterior.

## Fuera de alcance

- `super_admin`, que continúa en espera.
- Reabrir `branding` u otro dominio cerrado por inferencia.
- Corregir hallazgos abiertos de capas anteriores o completar verificaciones
  heredadas dentro de esta activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  SQL observable, transacciones o comportamiento actual sin autorización
  explícita apoyada en caracterización.
- Cambiar PostgreSQL, `psycopg2`, schemas tenant, pool, timeouts, concurrencia,
  ORM o driver.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan.
- SQL, parámetros, número y orden observable de operaciones y límites de
  transacción se conservan.
- Se conserva quién posee conexión, cursor, `commit`, `rollback` y demás
  efectos laterales.
- La DB síncrona permanece fuera del event loop y el `ContextVar` del tenant se
  preserva donde corresponda.
- No se crea una abstracción compartida sin dos consumidores reales.

## Línea base

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Se determinará en 7.0 después de delimitar la frontera | Pendiente |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Se determinará sobre el alcance de 7.0 | Pendiente |
| Dependencias | Incluidas en `scripts\verify.py` | Pendiente |

No se ejecutan pruebas durante la activación documental.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos y caracterización | **Pendiente y no iniciada** |
| 7.1 | Primera extracción protegida | Pendiente de evidencia de 7.0 |
| 7.2 | Segunda extracción o integración | Pendiente de evidencia de 7.0 |
| 7.3 | Retiro heredado y cierre | Pendiente de evidencia de 7.0 |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No aplica`
con una explicación; nunca se ejecutan dos sin orden explícita.

## Subcapa activa: trabajo exacto de 7.0

1. Delimitar la frontera real de `profesores` por entradas, llamadores, tablas,
   consumidores y efectos laterales antes de contar o modificar nada.
2. Inspeccionar únicamente la documentación, fuentes y pruebas relacionadas
   con esa frontera.
3. Inventariar contratos HTTP, permisos, roles, ownership, tenant, SQL,
   transacciones, recursos y comportamiento observable.
4. Medir consultas y conexiones por camino y buscar dependencias del tamaño de
   entrada o resultado.
5. Identificar consumidores y dependencias compartidas sin modificar dominios
   cerrados.
6. Revisar las pruebas relacionadas y agregar caracterización sin cambiar
   expectativas heredadas.
7. Resolver los seis supuestos documentales y registrar los hallazgos sin
   corregirlos.
8. Archivos modificables en 7.0: pruebas de caracterización del dominio, esta
   bitácora y el índice maestro. No se modifica producto durante el inventario.
9. Ejecutar pruebas específicas, Ruff sobre la caracterización, la compuerta
   global, `git diff --check` y revisión de alcance.
10. Actualizar esta bitácora con archivos, comandos, resultados, decisiones,
    riesgos y la siguiente acción exacta.
11. Detenerse al cerrar 7.0. No iniciar 7.1 en el mismo turno.

## Criterios de cierre de la subcapa

- La frontera queda delimitada con evidencia y sin reabrir otros dominios.
- Los seis supuestos documentales quedan resueltos uno por uno.
- Existe caracterización ejecutable de contratos, SQL, transacciones,
  consultas, conexiones y efectos laterales aplicables.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, decisiones, riesgos y siguiente acción.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- El siguiente dominio queda en espera hasta una orden explícita del usuario.

## Decisiones

- **Activar `profesores` y solo ese dominio.** El usuario lo nombró —con la
  errata inequívoca `proefesores`— y ordenó activarlo.
- **Continuar localmente con verificaciones pendientes.** La orden responde a
  la alternativa presentada en el turno anterior; ninguna verificación se
  considera cumplida y sus riesgos permanecen vigentes.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre de `branding`; todos sus descendientes desde el base anterior están
  explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera.** Los datos del dominio se registran como preguntas
  que 7.0 debe resolver con evidencia.
- **No activar `super_admin`.** Permanece en espera y requiere una orden nueva.

## Riesgos

- **Verificación manual de `branding` pendiente.** Se aceptó continuar sin
  cerrarla; fallos de GET/PUT, permisos, tenant o ciclo de logos podrían no
  estar cubiertos por la compuerta automática.
- **Verificaciones heredadas pendientes.** Conservan los riesgos documentados
  en el índice y esta capa no puede presentarlas como cumplidas.
- **Perfil del dominio desconocido.** Antes de 7.0 no se sabe con evidencia si
  `profesores` escribe, cuántos permisos usa, qué tablas comparte o si presenta
  N+1 de consultas o conexiones.
- **Frontera transversal posible.** El rol profesor aparece en dominios ya
  migrados; la coincidencia nominal no autoriza mover ni modificar esos
  consumidores.
- **Publicación de `branding` no comprobada contra el remoto real.** Al activar,
  `HEAD` coincide con la referencia local `origin/main`, pero no se consultó el
  remoto real ni se verificaron deploy o GitHub Actions.

## Registro de ejecución

### 2026-08-23 — activación de la capa para `profesores`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Documentos leídos completamente y en orden: índice maestro,
  `07_BRANDING.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario ordenó «activa el dominio proefesores» después de
  recibir la decisión explícita entre completar la verificación manual de
  `branding` o continuar localmente aceptándola como pendiente.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `58eb5c2eb43a9d20708b75ca8bd798e9f13b33e6`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: el base `bb34cf6` de `branding` es ancestro. Sus cuatro
  descendientes son `f53711b` —activación—, `0083237` —7.0—, `5ddd504`
  —7.1— y `58eb5c2` —cierre documental—. Todos están explicados en esa
  bitácora y sus archivos coinciden con lo registrado.
- Estado de publicación observado localmente: `HEAD` y la referencia local
  `origin/main` coinciden. No se consultó el remoto real ni se verificó GitHub
  Actions.
- Decisión heredada: permanecen pendientes la verificación manual propia de
  `branding`, la calibración de timeout, la evidencia de CI, los pasos manuales
  no confirmados y la rotación de la credencial privilegiada. El usuario
  aceptó continuar con sus riesgos.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, esquemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el índice;
  `git diff --no-index --check -- NUL docs/modularizacion/07_PROFESORES.md`
  no reportó errores de whitespace —su exit 1 indica que el archivo nuevo
  difiere de `NUL`—. Los avisos fueron únicamente de normalización futura
  LF/CRLF.
- Revisión de alcance: `git status --short --branch` mostró exactamente el
  índice modificado y esta bitácora nueva sobre `main...origin/main`. El índice
  contiene una sola fila de estado **Activa** y los encabezados de control de
  las bitácoras una sola declaración **Activa**, ambas para `profesores`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

## Entrega al próximo chat

- Capa activa: **7 para `profesores`**.
- Última subcapa terminada: ninguna; activación documental solamente.
- Primera subcapa pendiente: **7.0**, inventario, contratos y caracterización.
- Verificaciones pendientes: la manual de `branding` y las heredadas
  registradas en el índice; ninguna se considera cumplida.
- Dominio en espera: `super_admin`.
- Bloqueos: ninguno.
- Siguiente acción exacta: ejecutar únicamente 7.0 y detenerse antes de 7.1.
