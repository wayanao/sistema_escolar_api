# Capa 3: migraciones y tenants

Última revisión: 2026-08-13.

## Control

- Estado: **Activa**.
- Commit base: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`.
- Rama acordada: `main`.
- Estado al activar: árbol limpio; `HEAD` coincidente con la referencia local
  `origin/main`.
- Primera subcapa pendiente: **3.0**.
- Código de producto modificado al activar: **ninguno**.
- Autorización: orden explícita del usuario el 2026-08-13, limitada a la
  activación documental de esta capa y con la instrucción de detenerse antes de
  3.0.

## Objetivo

Dejar todos los tenants reactivables versionados y verificables, un runner de
migraciones protegido contra ejecuciones simultáneas y un alta de tenant
reproducible a partir de migraciones versionadas en lugar de la copia de un
tenant plantilla, con un ensayo previo en un entorno no productivo y un
rollback preparado.

El objetivo procede exclusivamente del alcance registrado para la capa 3 en
`docs/modularizacion/README.md`. La activación no inspeccionó código, esquemas,
migraciones ni scripts, por lo que esta bitácora no afirma todavía qué
mecanismos existen hoy ni cómo están implementados. Esa descripción es trabajo
de 3.0.

## Dependencias de capas anteriores

- Compuerta única `scripts/verify.py`, heredada de la capa 0, con CI declarada
  en `.github/workflows/backend-quality.yml`.
- Capa 1 cerrada: propiedad definida de conexión, cursor, `commit`, `rollback` y
  devolución al pool; timeouts aplicados por transacción con
  `set_config(..., TRUE)` porque el endpoint agrupado rechaza parámetros de
  arranque que no sabe rastrear.
- Capa 2 cerrada: la DB síncrona del camino HTTP está fuera del event loop y el
  limitador compartido de AnyIO deriva `T=floor((DB_POOL_MAX_CONNECTIONS-R)/H)`
  con `H=2` y `R=0`, hoy cinco workers para un pool de diez conexiones.
- Compuerta local vigente registrada al cerrar la capa 2: **477 pruebas**, Ruff
  correcto y `pip check` correcto.
- La calibración operativa de `DB_STATEMENT_TIMEOUT_MS` sigue **pendiente y
  aceptada** desde la capa 1. No se considera cumplida, no se incorpora por
  inferencia al alcance de esta capa y su riesgo se conserva.

## Alcance autorizado

- Inventariar cómo se descubren los tenants, cómo se registra la versión de cada
  schema, qué ejecuta hoy las migraciones y cómo se da de alta un tenant nuevo.
- Definir con evidencia qué significa «tenant reactivable» y qué tenants entran
  en el alcance de la capa.
- Verificar y aplicar las migraciones pendientes a los tenants que el inventario
  demuestre incluidos, primero fuera de producción.
- Agregar un bloqueo que impida ejecuciones simultáneas del runner de
  migraciones.
- Sustituir de forma progresiva el alta por copia de un tenant plantilla por un
  alta basada en migraciones versionadas.
- Agregar o conservar pruebas de caracterización antes de cualquier extracción o
  sustitución.
- Ensayar en una base de prueba o staging y preparar un rollback aplicable a
  esquema y datos, no solo a la aplicación.

## Fuera de alcance

- Cambiar PostgreSQL, `psycopg2`, el modelo de schemas por tenant o introducir
  un ORM o un driver asíncrono.
- Modificar rutas, payloads, status codes, permisos, roles, ownership o reglas
  de negocio.
- Cambiar SQL observable de los dominios, orden transaccional, `commit`,
  `rollback`, timeouts o tamaño del pool sin una autorización explícita ante un
  bloqueo demostrado.
- Rediseñar la concurrencia cerrada en la capa 2 o alterar el limitador
  compartido sin reauditar `H` y `R`.
- Modularizar dominios, eliminar N+1, optimizar consultas o crear índices por
  rendimiento; corresponde a las capas 4 en adelante.
- Ejecutar migraciones reales contra producción, desplegar o cambiar
  configuración real.
- Crear una abstracción compartida sin dos usos reales demostrados.

## Invariantes

- Métodos, paths, status codes y formas de respuesta permanecen idénticos.
- Permisos, roles, ownership y aislamiento entre tenants se conservan sin
  excepción; una migración no puede filtrar datos entre schemas.
- Un tenant existente no pierde datos, columnas ni restricciones por efecto de
  esta capa.
- La propiedad de cursor, conexión, `commit`, `rollback` y devolución al pool
  definida en la capa 1 no cambia.
- Ninguna operación de esta capa reintroduce trabajo DB síncrono en el event
  loop ni consume el limitador compartido sin recalcular la capacidad.
- Un alta de tenant nueva produce un schema equivalente al que produce hoy el
  camino vigente, salvo diferencias que la bitácora autorice de forma explícita.
- Toda ejecución de migración es idempotente frente a una repetición y no queda
  a medias sin dejar constancia de su versión.

## Línea base

La activación no ejecuta verificaciones: la subcapa 3.0 debe reproducirlas desde
el commit base antes de inventariar, medir o cambiar nada.

| Comprobación | Comando | Resultado |
|---|---|---|
| Pruebas específicas | Por determinar en 3.0 según el inventario | Pendiente |
| Compuerta global | `.\venv\Scripts\python.exe scripts\verify.py` | Pendiente |
| Ruff | Ejecutado por la compuerta | Pendiente |
| Dependencias | Ejecutado por la compuerta | Pendiente |
| Estado de versionado por tenant | Por determinar en 3.0 | Pendiente |

La referencia heredada es la compuerta de cierre de la capa 2: 477 pruebas,
Ruff correcto y `pip check` correcto, ejecutada fuera del sandbox. 3.0 debe
reproducirla sobre el commit base y registrar el resultado observado, no
copiarlo.

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 3.0 | Inventario, contratos, criterio de tenant reactivable, estrategia de verificación y línea base | **Pendiente** |
| 3.1 | Bloqueo del runner contra ejecuciones simultáneas | Pendiente |
| 3.2 | Versionado verificable de todos los tenants incluidos | Pendiente |
| 3.3 | Alta reproducible desde migraciones versionadas | Pendiente |
| 3.4 | Ensayo no productivo, rollback, verificación manual y cierre | Pendiente |

El desglose de 3.1 a 3.4 es **provisional** y deriva únicamente del alcance
registrado en el índice maestro. El inventario de 3.0 debe confirmarlo,
reordenarlo, dividirlo o marcar subcapas como `No aplica` con su explicación,
igual que el inventario de 2.0 reemplazó el desglose provisional de su capa.
Nunca se ejecutan dos subcapas en el mismo turno.

## Subcapa activa: trabajo exacto

Subcapa **3.0**, inventario y caracterización. No modifica producto.

1. Confirmar rama `main`, árbol limpio y que todo commit posterior al base
   `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70` esté explicado en esta bitácora.
2. Reproducir desde el base la compuerta global y registrar el resultado real,
   incluida cualquier limitación ambiental observada.
3. Inventariar con búsquedas dirigidas, sin modificar nada: descubrimiento de
   tenants, registro de versión por schema, ejecutor de migraciones, orden de
   aplicación, manejo de errores parciales y camino actual de alta de un tenant.
4. Registrar los contratos observables que la capa debe conservar y el criterio
   con evidencia de qué tenants son reactivables y cuáles no.
5. Determinar qué pruebas existentes cubren migraciones y alta de tenants, y
   cuál es el hueco exacto de caracterización.
6. Definir el procedimiento de ensayo no productivo y la forma del rollback de
   esquema, antes de proponer cualquier cambio.
7. Ejecutar `git diff --check`, comprobar el alcance del diff y actualizar
   únicamente esta bitácora.
8. Detenerse sin iniciar 3.1 y sin ejecutar ninguna migración.

Archivos previstos para 3.0: **únicamente esta bitácora**. Si el inventario
exigiera un script de apoyo, debe justificarse y autorizarse antes, no añadirse
por conveniencia.

## Criterios de cierre de la subcapa 3.0

- El mecanismo actual de migraciones y de alta de tenants está descrito con
  evidencia citada, no supuesto.
- El criterio de tenant reactivable está definido y aplicado a un inventario
  concreto.
- Los contratos que la capa debe conservar están enumerados.
- Existe una estrategia de prueba capaz de detectar una migración no aplicada,
  una aplicación doble y una divergencia entre schemas.
- Existe un procedimiento de ensayo no productivo y una forma de rollback de
  esquema.
- La compuerta heredada y `git diff --check` terminan correctamente.
- El diff contiene exclusivamente esta bitácora y no se inició 3.1.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas o marcadas `No aplica` con
  justificación.
- Todos los tenants incluidos en el alcance están versionados y verificables.
- El runner no puede ejecutarse dos veces en paralelo y esa protección está
  probada.
- El alta de un tenant se reproduce desde migraciones versionadas y su resultado
  es equivalente al camino anterior.
- Los contratos HTTP, permisos, tenant, ownership, SQL de dominio y
  transacciones permanecen conservados.
- Existe evidencia de un ensayo en base de prueba o staging, sin usar
  producción.
- Staging, rollback de esquema y verificación manual están documentados.
- La compuerta global, Ruff, dependencias y `git diff --check` terminan
  correctamente.
- La capa 4 queda en espera y no se activa sin orden explícita del usuario.

## Decisiones

- La capa se activa con `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70` como base
  porque es el `HEAD` limpio vigente y coincide con la referencia local
  `origin/main`. No se reutiliza el base de la capa 2 ni se asume el commit de
  cierre `8c3939a`, que quedó por detrás tras la publicación documental del
  relevo.
- La activación crea solo esta bitácora y actualiza el índice. No inspecciona ni
  modifica código, migraciones, esquemas o pruebas, conforme a la autorización
  explícita de detenerse antes de 3.0.
- 3.0 es una subcapa de inventario y caracterización. Elegir un mecanismo de
  bloqueo, un formato de versionado o una estrategia de alta antes de conocer el
  estado real fijaría una solución sin evidencia, como ya ocurrió y se evitó en
  la capa 2.
- El desglose posterior a 3.0 se registra como provisional en lugar de omitirlo,
  para que el índice tenga una forma esperada de la capa sin que ese esquema se
  confunda con un inventario verificado.
- La calibración de `DB_STATEMENT_TIMEOUT_MS` se mantiene registrada como
  verificación operativa pendiente de la capa 1 por decisión explícita del
  usuario al activar esta capa. No se da por cumplida ni se traslada al alcance
  de la capa 3.
- No se registra ningún resultado de GitHub Actions. El `HEAD` coincide con la
  referencia local `origin/main`, pero eso no es evidencia de un run; no hay
  cliente de GitHub disponible en este checkout para obtenerla.

## Riesgos

- Es la primera capa del programa que puede tocar esquema y datos. Las capas 0 a
  2 tenían un rollback exclusivamente de aplicación; aquí un error puede dejar
  un schema a medias, por lo que el rollback debe diseñarse antes de cambiar
  nada y ensayarse fuera de producción.
- Una migración aplicada a un subconjunto de tenants produce divergencia
  silenciosa entre schemas. El inventario debe poder detectarla, no suponer que
  todos están al día.
- Sin bloqueo, dos ejecuciones simultáneas del runner pueden competir por el
  mismo schema. El propio índice señala esa protección como resultado de la
  capa, de modo que debe tratarse como carencia probable hasta que 3.0 lo
  confirme con evidencia.
- Un alta basada en migraciones puede no reproducir exactamente lo que produce
  hoy la copia de un tenant plantilla, incluidos objetos, permisos o datos
  semilla. La equivalencia debe demostrarse por comparación, no por confianza.
- Si esta capa introduce un consumidor de conexiones fuera del camino HTTP
  —runner, script o job en background—, la invariante `H=2`, `R=0` y el
  limitador de cinco workers derivados en la capa 2 dejan de estar justificados
  y deben reauditarse antes de desplegar.
- `DB_STATEMENT_TIMEOUT_MS` sigue sin calibrarse contra consultas pesadas. Una
  migración larga puede toparse con ese timeout; es un riesgo operativo
  heredado, aceptado explícitamente y no resuelto por esta capa.
- La CI remota no está verificada para los commits de la capa 2. Un fallo de
  entorno en GitHub Actions podría aparecer atribuido a esta capa; conviene
  obtener evidencia del run antes de acumular más cambios.
- Las versiones del stack están limitadas solo por mínimos. Una resolución
  distinta puede alterar el comportamiento observado y exige repetir la
  compuerta.

## Registro de ejecución

### 2026-08-13 — activación de la capa

- Modo de acceso del asistente: mismo checkout local; Git validado directamente
  en `c:\Users\David\Documents\sistema_escolar_api`.
- Autorización: orden explícita del usuario para activar únicamente la capa 3,
  con aceptación registrada de mantener pendiente la calibración de
  `DB_STATEMENT_TIMEOUT_MS`.
- Rama acordada: `main`.
- Estado verificado antes de escribir: árbol limpio, sin archivos sin rastrear;
  `HEAD` y la referencia local `origin/main` en
  `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, sin divergencia.
- Commit base registrado: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`.
- Continuidad auditada: diez commits posteriores al base de la capa 2, todos
  explicados en `02_CONCURRENCIA.md`. Ocho materializaron la activación y las
  subcapas 2.0 a 2.5, `8c3939a` cerró la capa con 2.6 y `81882f3` publicó el
  cierre y preparó el relevo. Se verificó que `b24cb8d` y `8c3939a` son
  ancestros de `HEAD` y que el alcance de `81882f3` contiene exactamente
  `02_CONCURRENCIA.md`, `README.md` y `PROMPT_CONTINUACION.md`, tal como declara
  su entrada de bitácora.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, migraciones, esquemas, pruebas, configuración,
  dependencias y workflow modificados: **ninguno**.
- Código o migraciones inspeccionados: **ninguno**. La activación se definió solo
  desde el índice maestro, la bitácora de continuidad y la plantilla.
- Compuerta global: no ejecutada durante la activación; 3.0 debe reproducirla
  desde el base.
- Evidencia remota: no hay cliente de GitHub disponible en este checkout, por lo
  que **no** se obtuvo evidencia de ningún run. GitHub Actions continúa **no
  verificada** para la capa 2 y para este relevo. La coincidencia entre `HEAD` y
  la referencia local `origin/main` no se presenta como prueba de CI.
- Verificación operativa heredada: la calibración de `DB_STATEMENT_TIMEOUT_MS`
  permanece **pendiente y aceptada**, con su riesgo conservado.
- Siguiente acción exacta: ejecutar **3.0**, reproduciendo la línea base e
  inventariando migraciones, versionado por tenant, runner y alta de tenants,
  junto con sus contratos y la estrategia de verificación. Actualizar únicamente
  esta bitácora y detenerse sin iniciar 3.1 y sin ejecutar migraciones.

## Entrega al próximo chat

- Capa activa: **3, migraciones y tenants**.
- Última subcapa terminada: **ninguna**; la capa acaba de activarse.
- Primera subcapa pendiente: **3.0**, inventario, contratos y caracterización.
- Commit base: `81882f3b1ee9e3b50076b0fc1fd93dcd9fd5ac70`, rama `main`.
- Bloqueos: ninguno para iniciar 3.0. Permanece pendiente y aceptada la
  calibración de `DB_STATEMENT_TIMEOUT_MS` de la capa 1, y GitHub Actions sigue
  sin evidencia de run.
- Siguiente acción exacta: ejecutar únicamente 3.0 según «Subcapa activa:
  trabajo exacto», sin inspeccionar más de lo que esa lista autoriza, sin tocar
  producto y sin ejecutar ninguna migración.
