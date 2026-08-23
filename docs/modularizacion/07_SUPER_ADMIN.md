# Capa 7: super_admin

Última revisión: 2026-08-23.

## Control

- Estado: **Activa** desde el 2026-08-23 por orden explícita del usuario.
- Commit base: `2ec924a3308581b746a61fa24a44f71433034dbc`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.1**, primera extracción protegida del bloque
  de consulta y cambio de estado de tenants.
- Subcapa 7.0: **Cerrada** el 2026-08-23 con producto intacto, 27 pruebas de
  caracterización nuevas, 88 pruebas específicas y compuerta global de 1088
  pruebas.
- Código de producto modificado al activar: **Ninguno**.
- Dominio de esta capa: **`super_admin`, y solo ese**.
- Autorización: el usuario escribió «sigue super admin» después de que se le
  informó que `profesores` estaba cerrado, que su verificación manual seguía
  pendiente y que `super_admin` permanecía en espera.
- Decisión sobre verificaciones pendientes: la orden nombra el siguiente
  dominio y autoriza continuar localmente aceptando que la verificación manual
  de `profesores`, la de `branding` y las heredadas sigan pendientes. Ninguna
  se marca como cumplida.
- La activación es exclusivamente documental. No autoriza implementar 7.0,
  hacer commit, push, deploy, migraciones reales ni acceder a producción.

## Objetivo

Migrar el dominio de **super_admin** con contratos y pruebas, conservando su
comportamiento observable actual y tratando como invariantes de seguridad sus
privilegios y cualquier operación transversal entre tenants.

El índice maestro exige trabajar un dominio a la vez, caracterizar antes de
extraer y no crear abstracciones compartidas sin dos usos reales. La activación
no inspecciona código ni infiere la frontera; 7.0 debe delimitarla con evidencia.

## Dependencias de capas anteriores

- La capa 7 para `profesores` está cerrada: 7.0 y 7.1 completas, 7.2 y 7.3
  **No aplica**, compuerta de cierre con **1061 pruebas**, Ruff correcto y
  dependencias íntegras.
- Staging y rollback de `profesores` están documentados; su verificación manual
  propia permanece pendiente.
- El commit base de esta capa es el `HEAD` limpio vigente,
  `2ec924a3308581b746a61fa24a44f71433034dbc`.
- Los cuatro commits posteriores al base de `profesores` están explicados en su
  bitácora: `4f459c1` activa el dominio, `3ae2884` cierra 7.0, `3eb6a44`
  contiene 7.1 y `2ec924a` contiene el cierre documental. Sus archivos
  coinciden con el alcance registrado.
- `HEAD` coincide con la referencia local `origin/main`. No se consultó el
  remoto real ni se atribuye publicación, despliegue o GitHub Actions.
- Siguen pendientes, sin marcarse como cumplidas: la calibración operativa
  final de `DB_STATEMENT_TIMEOUT_MS`; evidencia de GitHub Actions posterior a
  la capa 0; pasos manuales heredados no confirmados; las verificaciones
  manuales de `branding` y `profesores`; y la rotación de la credencial
  privilegiada registrada en la capa 4.

## Alcance autorizado

- Trabajar únicamente en el dominio `super_admin`.
- En 7.0, delimitar la frontera real por entradas, llamadores, tablas,
  consumidores y efectos laterales, no solo por nombres de archivo.
- Inventariar métodos, paths, guards, permisos, roles, operaciones globales,
  ownership, tenant, payloads, status codes, respuestas, SQL, transacciones,
  conexiones y concurrencia.
- Identificar de forma explícita cualquier capacidad de crear, modificar,
  desactivar o acceder a tenants y credenciales privilegiadas.
- Agregar o conservar pruebas de caracterización antes de una extracción.
- Medir consultas y conexiones críticas antes y después de cambios posteriores.

## Fuera de alcance

- Reabrir `profesores`, `branding` u otro dominio cerrado por inferencia.
- Completar verificaciones heredadas o rotar credenciales dentro de esta
  activación.
- Cambiar rutas, payloads, status codes, permisos, roles, ownership, tenant,
  SQL observable, transacciones o comportamiento actual sin autorización
  explícita apoyada en caracterización.
- Crear privilegios, endpoints o capacidades nuevas.
- Cambiar PostgreSQL, `psycopg2`, schemas tenant, pool, timeouts, concurrencia,
  ORM o driver.
- Migraciones reales, acceso a producción, DDL, DML, deploy, commit o push.

## Invariantes

- Métodos, paths, status codes y forma exacta de las respuestas permanecen
  idénticos.
- Permisos, roles, ownership, alcance global y aislamiento entre tenants se
  conservan exactamente.
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
| Línea base heredada | `.\venv\Scripts\python.exe -m pytest tests\test_super_admin.py tests\test_tenant_provisioning.py tests\test_esquema_base.py tests\test_auth_threadpool.py tests\test_auth_tenant.py -q` | **61 passed**, 6 warnings |
| Caracterización 7.0 | `.\venv\Scripts\python.exe -m pytest tests\test_super_admin_caracterizacion.py -q` | **27 passed**, 6 warnings |
| Pruebas específicas integradas | Línea base heredada más `tests\test_super_admin_caracterizacion.py` | **88 passed**, 6 warnings |
| Suite global | `.\venv\Scripts\python.exe scripts\verify.py` | **1088 passed**, 5 warnings; Ruff correcto; dependencias íntegras |
| Ruff específico | `.\venv\Scripts\python.exe -m ruff check tests\test_super_admin_caracterizacion.py` | Correcto |
| Dependencias | Incluidas en `scripts\verify.py` | Íntegras |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos y caracterización | **Cerrada** el 2026-08-23 |
| 7.1 | Extraer las cinco operaciones SQL de consulta y estado de tenants | **Pendiente; siguiente acción exacta** |
| 7.2 | Provisionamiento privilegiado y autenticación, por decidir con evidencia de 7.1 | Pendiente |
| 7.3 | Retiro heredado y cierre | Pendiente |

Las subcapas se adaptan al trabajo real. Las innecesarias se marcan `No aplica`
con una explicación; nunca se ejecutan dos sin orden explícita.

## Resultado de 7.0: frontera e inventario

### Entradas, archivos y consumidores

- Frontera propia: `app/routes/super_admin.py` —64 líneas—,
  `app/controllers/super_admin_controller.py` —393 líneas— y
  `app/core/super_admin.py` —112 líneas—. No existía repositorio del dominio.
- Entrada compartida: `POST /login` en `app/routes/auth.py`, cuyo dispatcher en
  `app/controllers/auth_controller.py` deriva los códigos privilegiados a
  `autenticar_super_admin`.
- Entradas propias: cuatro operaciones síncronas, sin `response_model`, todas
  protegidas por `get_current_super_admin`: `GET /super-admin/tenants`, `POST
  /super-admin/tenants`, `PATCH /super-admin/tenants/{tenant_id}/estado` y `GET
  /super-admin/tenants/{tenant_id}/estado-auditoria`.
- Los schemas de entrada `TenantCreate` y `TenantEstadoUpdate` están definidos
  inline en la ruta. Pydantic conserva el 422 previo al controlador cuando
  faltan campos requeridos.
- Consumidores directos de las tablas públicas de esta frontera:
  `super_admin_controller.py`, `core/super_admin.py` y
  `core/tenant_status.py`. No se modificó el último por ser una dependencia
  compartida y no una extracción autorizada.

### Seguridad, tenant y contratos observables

- Los códigos de login privilegiado son exactamente `super_admin`,
  `superadmin` y `plataforma`; autentican contra `public.super_admins` y solo
  aceptan una fila con estado `activo` y contraseña válida.
- El JWT y la revalidación exigen rol `super_admin`, tenant `public`, id entero
  y super admin todavía activo. La respuesta canónica de rechazo del guard es
  401. El guard asíncrono conserva la validación síncrona fuera del event loop.
- No existe ownership tenant para estas rutas: la identidad privilegiada puede
  enumerar, crear y cambiar tenants globalmente. El id del super admin se pasa
  al provisionamiento y a la auditoría de cambios de estado.
- Las cuatro rutas conservan 200 en sus caminos felices y devuelven directamente
  las listas o diccionarios del controlador. Los errores propios observados son
  404 para tenant ausente, 409 para conflicto de integridad y 422 para estado o
  datos de alta inválidos, además del 422 de Pydantic.
- Un cambio al mismo estado ejecuta rollback y devuelve el tenant sin insertar
  auditoría. Un cambio real actualiza el estado manual, inserta auditoría y hace
  commit. Los estados admitidos son `activo`, `en_mora`, `suspendido` y
  `cancelado`.

### SQL, recursos y transacciones medidos

- La frontera propia contiene 20 sitios `cursor.execute`: 18 en el controlador
  y 2 en el núcleo de autenticación/revalidación. No hay `execute` dentro de un
  bucle ni cantidad de consultas dependiente del tamaño de entrada o resultado.
- Login privilegiado: una conexión pública y una consulta. Revalidación del
  guard: una conexión pública y una consulta por petición protegida.
- Listado de tenants y auditoría: cada controlador usa una conexión pública y
  una consulta; la auditoría ordena descendente y limita a 50 filas. Incluido
  el guard, cada petición usa dos conexiones secuenciales y dos consultas.
- Cambio de estado ausente o sin cambio: una conexión y una consulta en el
  controlador, seguida de rollback; con el guard son dos conexiones y dos
  consultas. Cambio real: una conexión, tres consultas y commit en el
  controlador; con el guard son dos conexiones y cuatro consultas.
- Provisionamiento exitoso: una conexión y una transacción de 13 llamadas
  observables a `execute` en este orden: insertar colegio, crear schema, fijar
  `search_path` local, ejecutar el SQL base, comprobar historial público,
  copiar historial cuando existe, fijar `search_path` tenant/public, sembrar
  branding, copiar plantilla predefinida, crear admin tenant, volver a
  `public`, crear suscripción e insertar evento de auditoría. Con el guard son
  dos conexiones y 14 llamadas a `execute`.
- La lectura completa del SQL base cuenta como una llamada observable al
  cursor aunque contenga varias sentencias. El controlador conserva el
  `commit`; cualquier excepción revierte y cierra cursor/conexión, y el
  `ContextVar` vuelve a su valor anterior. `IntegrityError` se traduce a 409.
- `get_connection` y el helper público son los dueños actuales de contexto,
  conexión y cursor; ninguna extracción futura puede mover silenciosamente
  `commit`, `rollback`, cierre o cambios de `search_path`.

### Tablas y restricciones observadas

- Autenticación usa `public.super_admins`; gestión usa `public.colegios`,
  `public.tenant_suscripciones`, `public.tenant_estado_auditoria` y
  `public.tenant_eventos_auditoria`, además de tablas tenant sembradas durante
  el alta.
- Las migraciones versionadas fijan email único para super admins; tenant único
  y días de gracia no negativos para suscripciones; y claves foráneas de las
  auditorías. Las tablas de auditoría no declaran `ON DELETE` para sus claves
  foráneas.
- No existe migración versionada que cree `public.colegios`; su definición se
  localizó únicamente en `scripts/legacy/setup_saas.py`, con unicidad de
  subdominio y esquema. La observación queda registrada, no corregida.

### Caracterización agregada

- `tests/test_super_admin_caracterizacion.py` agrega 27 casos ejecutados y fija
  la frontera, el montaje HTTP, dependencia exacta, 200/401/422, payloads,
  schemas, dispatch de login, matrices de autenticación y revalidación, SQL y
  recursos de listar/auditar/cambiar estado, las 13 operaciones y rollback del
  provisionamiento, consumidores directos y DDL público.
- También fija que no existe repositorio todavía, que son 18 sitios SQL en el
  controlador y 2 en el núcleo, y que no hay ejecuciones dentro de bucles.
- No se cambió ninguna expectativa heredada ni archivo de producto.

## Primera subcapa pendiente: trabajo exacto para 7.1

1. Extraer únicamente los cinco sitios SQL del bloque de listado, auditoría y
   cambio de estado desde `super_admin_controller.py` a un repositorio propio
   del dominio.
2. Hacer que las operaciones del repositorio reciban el cursor; el controlador
   debe conservar validación, normalización, mapeo, contexto `public`, conexión,
   cursor, `commit`, `rollback` y cierre.
3. Conservar literalmente SQL, parámetros, orden, conteos, 200/401/404/422,
   payloads y el caso sin cambio que revierte sin auditar.
4. No tocar los 13 sitios del provisionamiento, los 2 sitios de
   `core/super_admin.py`, rutas, schemas inline, dispatcher compartido,
   `tenant_status.py`, migraciones ni dominios cerrados.
5. Mantener la caracterización y actualizar cualquier guarda estructural que
   deba reconocer el repositorio sin debilitar los conteos de frontera.
6. Ejecutar pruebas específicas, Ruff, compuerta global, `git diff --check` y
   revisión exclusiva de alcance; actualizar esta bitácora y detenerse antes
   de 7.2.

## Criterios de cierre de la subcapa 7.0

- Frontera delimitada con evidencia y sin reabrir dominios cerrados.
- Contratos privilegiados y tenant fijados por pruebas ejecutables.
- Consultas, conexiones, transacciones y efectos laterales medidos.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.0.
- Bitácora actualizada con resultados, riesgos y siguiente acción.

Todos se cumplieron el 2026-08-23. La primera ejecución de la compuerta bajo
sandbox no fue evidencia válida porque 30 casos no pudieron crear su fixture
temporal; la repetición autorizada con acceso al directorio temporal terminó
completa y verde.

## Criterios de cierre de la capa

- Todas las subcapas necesarias están cerradas.
- Compuerta global correcta.
- Contratos conservados o cambios explícitamente aprobados.
- Staging, rollback y verificación manual documentados.
- No se activa otro trabajo sin una nueva orden explícita del usuario.

## Decisiones

- **Activar `super_admin` y solo ese dominio.** El usuario lo nombró en la
  orden «sigue super admin» después del cierre de `profesores`.
- **Continuar localmente con verificaciones pendientes.** La orden sigue al
  aviso explícito de la verificación manual pendiente de `profesores`; ninguna
  verificación se considera cumplida y sus riesgos permanecen vigentes.
- **Usar el `HEAD` limpio vigente como commit base.** Es el punto posterior al
  cierre documental de `profesores` y todos sus descendientes desde el base
  anterior están explicados.
- **Activación exclusivamente documental.** No se inspecciona ni implementa
  7.0 en este turno.
- **No inferir la frontera privilegiada.** Archivos, rutas, permisos y tablas
  quedan como preguntas que 7.0 debe resolver con evidencia.
- **Caracterizar también las entradas compartidas.** El login privilegiado y
  la revalidación viven fuera de la ruta propia, pero forman parte del contrato
  de seguridad de la capa; se inspeccionaron y fijaron sin modificarlos.
- **Separar la primera extracción por riesgo transaccional.** 7.1 queda limitada
  a los cinco sitios SQL de listar, auditar y cambiar estado. Los 13 sitios del
  provisionamiento y los 2 del núcleo de autenticación permanecen intactos
  hasta nueva evidencia y una subcapa posterior.
- **No corregir hallazgos durante el inventario.** La ausencia de una migración
  versionada para `public.colegios`, los schemas inline y la ausencia de
  `response_model` se registran como comportamiento o riesgo actual, no como
  autorización de rediseño.

## Riesgos

- **Verificación manual de `profesores` pendiente.** Se aceptó continuar; un
  fallo real de admin, tenant, login o ciclo CRUD podría no estar cubierto por
  la compuerta automática.
- **Verificación manual de `branding` y verificaciones heredadas pendientes.**
  Conservan sus riesgos y esta capa no puede presentarlas como cumplidas.
- **Dominio privilegiado.** Una frontera, guard o operación transversal mal
  caracterizada podría afectar varios tenants; 7.0 debe fijar el modelo real
  antes de cualquier extracción.
- **Credencial privilegiada pendiente de rotación.** La capa 4 la registró y
  esta activación no autoriza rotarla ni asumir que el riesgo desapareció.
- **Publicación no comprobada contra el remoto real.** `HEAD` coincide con la
  referencia local `origin/main`, pero no se consultó el remoto ni se verificó
  deploy o GitHub Actions.
- **Provisionamiento de alto impacto.** El alta combina DDL, ejecución del SQL
  base, semillas, credenciales, suscripción y auditoría en una sola transacción
  de 13 llamadas observables. Cambiar orden, `search_path` o ownership podría
  dejar un tenant parcial o contaminar otro schema.
- **Origen heredado de `public.colegios`.** No hay una migración pública
  versionada que cree la tabla que sostiene la frontera; la única definición
  localizada está en un script legacy. La capa no debe fingir que esa
  precondición está gestionada por el runner actual.
- **Contrato de respuesta implícito.** Las cuatro rutas carecen de
  `response_model` y exponen directamente diccionarios/listas del controlador;
  una extracción podría alterar formas o normalizaciones sin que FastAPI las
  estabilice.
- **Doble acceso público por ruta protegida.** El guard revalida en una conexión
  y la operación abre otra. Es comportamiento medido y no se optimiza por
  inferencia.
- **Integridad de auditoría.** Las claves foráneas de auditoría no usan `ON
  DELETE`; una eliminación futura de tenants o super admins tendría efectos no
  caracterizados y queda fuera de alcance.

## Registro de ejecución

### 2026-08-23 — activación de la capa para `super_admin`

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales
  validados directamente.
- Documentos leídos en el orden exigido: índice maestro, bitácora cerrada más
  reciente `07_PROFESORES.md`, instrucciones locales —no se encontraron— y
  `PLANTILLA_CAPA.md`.
- Autorización: el usuario escribió «sigue super admin» después de ser
  informado del cierre de `profesores`, de su verificación manual pendiente y
  de que `super_admin` seguía en espera.
- Rama acordada y observada: `main`.
- Estado antes de escribir: árbol limpio; `git status --porcelain=v1 --branch`
  mostró únicamente `## main...origin/main`.
- Commit base: `2ec924a3308581b746a61fa24a44f71433034dbc`, el `HEAD`
  limpio vigente y coincidente con la referencia local `origin/main`.
- Continuidad: los cuatro descendientes del base de `profesores` son
  `4f459c1` —activación—, `3ae2884` —7.0—, `3eb6a44` —7.1— y `2ec924a`
  —cierre documental—. Todos están explicados; la inspección del último mostró
  únicamente los dos documentos registrados.
- Estado de publicación observado localmente: `HEAD` coincide con
  `origin/main`. No se consultó el remoto real ni se verificó GitHub Actions.
- Decisión heredada: permanecen pendientes las verificaciones manuales de
  `profesores` y `branding`, la calibración de timeout, la evidencia de CI, los
  pasos manuales heredados y la rotación de la credencial privilegiada. El
  usuario aceptó continuar con sus riesgos.
- Archivos creados o modificados: esta bitácora y
  `docs/modularizacion/README.md`.
- Código de producto, pruebas, consultas, migraciones, schemas, configuración
  y dependencias inspeccionados o modificados: **ninguno**.
- Pruebas, conexiones a PostgreSQL, acceso a producción, commit, push y deploy:
  **ninguno**.
- Verificación documental: `git diff --check` terminó en exit 0 para el índice;
  `git diff --no-index --check -- NUL
  docs/modularizacion/07_SUPER_ADMIN.md` no reportó errores de whitespace —su
  exit 1 indica que el archivo nuevo difiere de `NUL`—. Los avisos fueron solo
  de normalización futura LF/CRLF.
- Revisión de alcance: `git status --short --branch` mostró exactamente el
  índice modificado y esta bitácora nueva sobre `main...origin/main`. El índice
  contiene una sola fila **Activa** y corresponde a `super_admin`.
- Siguiente acción exacta: ejecutar únicamente 7.0 conforme al trabajo exacto
  de esta bitácora y detenerse antes de 7.1.

### 2026-08-23 — cierre de la subcapa 7.0

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales se
  validaron directamente.
- Autorización: después de la activación documental, el usuario escribió
  «continua». Conforme a esta bitácora, la orden autorizó solamente 7.0.
- Precondiciones antes de modificar: rama `main`; árbol limpio confirmado con
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 1]`; `HEAD`
  `a3212ecf7519feb490634bf7397b09936c1a05fd`; y base
  `2ec924a3308581b746a61fa24a44f71433034dbc` comprobada como ancestro.
- Continuidad posterior al base: existía únicamente `a3212ec`, cuyo diff
  contenía la creación de esta bitácora y la actualización del índice para la
  activación. Coincide con la ejecución registrada y no había divergencia sin
  explicar.
- Alcance inspeccionado: exclusivamente rutas, controlador, núcleo de
  autenticación, dispatcher de login, estado tenant, sesión DB, migraciones
  públicas, definición legacy de `public.colegios` y pruebas relacionadas con
  la frontera documentada arriba.
- Línea base heredada antes de agregar caracterización: **61 passed**, 6
  warnings.
- Archivo agregado: `tests/test_super_admin_caracterizacion.py`, con 27 casos.
  Documentación modificada: esta bitácora y
  `docs/modularizacion/README.md`. Archivos de producto modificados:
  **ninguno**.
- Caracterización aislada: **27 passed**, 6 warnings. Ruff específico: correcto.
- Batería específica integrada: **88 passed**, 6 warnings.
- Primera ejecución de `.\venv\Scripts\python.exe scripts\verify.py` dentro del
  sandbox: pytest informó **1058 passed y 30 errores de setup**, todos por
  `PermissionError` al acceder a
  `C:\Users\David\AppData\Local\Temp\pytest-of-David`; Ruff y `pip check`
  pasaron. Ese intento se registra como inválido, no como regresión ni como
  compuerta cumplida.
- Repetición autorizada de la misma compuerta con acceso al directorio temporal:
  **1088 passed**, 5 warnings; Ruff correcto; `pip check` sin dependencias
  rotas.
- No se ejecutó PostgreSQL real, migración, producción, deploy, commit ni push;
  tampoco se atribuye evidencia de GitHub Actions.
- Decisión de siguiente frontera: 7.1 extraerá solo los cinco sitios SQL de
  listar, auditar y cambiar estado, con cursor recibido y recursos/transacción
  aún en el controlador. Provisionamiento y autenticación quedan fuera.
- Whitespace: `git diff --check` terminó en exit 0 para los dos documentos;
  `git diff --no-index --check -- NUL
  tests\test_super_admin_caracterizacion.py` no reportó errores —su exit 1
  indica que el archivo nuevo difiere de `NUL`—. Los únicos avisos fueron de
  normalización futura LF/CRLF y del perfil local de PowerShell.
- Revisión de alcance: `git status --short --branch` mostró exactamente esta
  bitácora y el índice modificados, más la caracterización nueva, sobre
  `main...origin/main [ahead 1]`. El índice contiene una sola fila **Activa**,
  correspondiente a `super_admin`.
- Siguiente acción exacta: esperar una orden nueva para iniciar únicamente 7.1
  y detenerse antes de 7.2.

## Entrega al próximo chat

- Capa activa: **7 para `super_admin`**.
- Última capa cerrada: **7 para `profesores`**.
- Última subcapa cerrada: **7.0**, inventario, contratos y caracterización; 27
  casos nuevos, 88 pruebas específicas y compuerta global con 1088 pruebas.
- Primera subcapa pendiente: **7.1**, extracción de los cinco sitios SQL de
  listar, auditar y cambiar estado; no incluye provisionamiento ni
  autenticación.
- Verificaciones pendientes aceptadas: manuales de `profesores` y `branding`,
  además de las heredadas del índice.
- Bloqueos: ninguno.
- Siguiente acción exacta: esperar una orden nueva para ejecutar únicamente
  7.1 y detenerse antes de 7.2.
