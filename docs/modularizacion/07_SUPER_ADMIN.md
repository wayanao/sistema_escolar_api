# Capa 7: super_admin

Última revisión: 2026-08-23.

## Control

- Estado: **Activa** desde el 2026-08-23 por orden explícita del usuario.
- Commit base: `2ec924a3308581b746a61fa24a44f71433034dbc`.
- Rama acordada: `main`.
- Primera subcapa pendiente: **7.3**, extracción protegida de las 13 operaciones
  del provisionamiento y cierre de la capa.
- Subcapa 7.0: **Cerrada** el 2026-08-23 con producto intacto, 27 pruebas de
  caracterización nuevas, 88 pruebas específicas y compuerta global de 1088
  pruebas.
- Subcapa 7.1: **Cerrada** el 2026-08-23; cinco SQL idénticos byte a byte
  viven ahora en `super_admin_repository`, con 89 pruebas específicas y
  compuerta global de 1089 pruebas.
- Subcapa 7.2: **Cerrada** el 2026-08-23; las dos consultas de autenticación y
  revalidación viven ahora en `super_admin_repository`, con 2 de 2 SQL
  idénticos byte a byte, 89 pruebas específicas y compuerta global de 1089
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
| Pruebas específicas después de 7.1 | Línea base heredada más `tests\test_super_admin_caracterizacion.py` | **89 passed**, 6 warnings |
| Pruebas específicas después de 7.2 | Línea base heredada más `tests\test_super_admin_caracterizacion.py` | **89 passed**, 6 warnings |
| Guardias históricas de repositorios | Las cinco pruebas exactas de dashboard, notas, ventas, asistencia y planilla | **5 passed**, 1 warning |
| Suite global de 7.0 | `.\venv\Scripts\python.exe scripts\verify.py` | **1088 passed**, 5 warnings; Ruff correcto; dependencias íntegras |
| Suite global de 7.1 | `.\venv\Scripts\python.exe scripts\verify.py` | **1089 passed**, 5 warnings; Ruff correcto; dependencias íntegras |
| Suite global de 7.2 | `.\venv\Scripts\python.exe scripts\verify.py` | **1089 passed**, 5 warnings; Ruff correcto; dependencias íntegras |
| Ruff específico | `.\venv\Scripts\python.exe -m ruff check tests\test_super_admin_caracterizacion.py` | Correcto |
| Dependencias | Incluidas en `scripts\verify.py` | Íntegras |

## Subcapas

| Subcapa | Resultado | Estado |
|---:|---|---|
| 7.0 | Inventario, contratos y caracterización | **Cerrada** el 2026-08-23 |
| 7.1 | Extraer las cinco operaciones SQL de consulta y estado de tenants | **Cerrada** el 2026-08-23 |
| 7.2 | Extraer las dos consultas de autenticación y revalidación | **Cerrada** el 2026-08-23 |
| 7.3 | Extraer el provisionamiento de 13 operaciones y cerrar la capa | **Pendiente; siguiente acción exacta** |

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

## Subcapa 7.1 cerrada: trabajo ejecutado

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

Resultado:

- `app/repositories/super_admin_repository.py` contiene cinco funciones y 97
  líneas. Todas reciben el cursor existente y ninguna importa ni administra
  conexión, cursor, contexto, transacción o cierre.
- `super_admin_controller.py` pasó de 393 a 339 líneas y de 18 a 13 sitios
  `cursor.execute`. Los cinco sitios movidos son exactamente los de listar
  tenants, listar auditoría, obtener el estado actual, actualizarlo y registrar
  su auditoría.
- La frontera propia conserva 20 sitios SQL: 13 de provisionamiento todavía en
  el controlador, 5 en el repositorio y 2 en `core/super_admin.py`.
- Los hashes SHA-256 de los cinco literales SQL del `HEAD` de entrada y del
  repositorio nuevo coincidieron uno a uno: **5 de 5 textos idénticos byte a
  byte**. Las pruebas conservaron parámetros, orden, resultados, conteos y
  eventos de `commit`/`rollback`/cierre.
- La caracterización suma un caso positivo para la superficie del repositorio
  y sus límites de recursos. Cinco guardias históricas incorporan deliberadamente
  `super_admin_repository`; no se debilitó ninguna enumeración exacta.
- No se tocaron provisionamiento, autenticación, rutas, schemas, dispatcher,
  `tenant_status.py`, migraciones ni dominios cerrados.

## Subcapa 7.2 cerrada: trabajo ejecutado

1. Extraer únicamente los dos sitios SQL de `app/core/super_admin.py` —login y
   revalidación— al repositorio propio ya existente.
2. Hacer que ambas operaciones reciban el cursor. `core/super_admin.py` debe
   conservar contexto `public`, conexión, cursor, cierre, normalización de
   email, comprobación de estado, contraseña, errores y offload del guard.
3. Conservar literalmente SQL, parámetros, número y orden de consultas,
   resultados `None`, 401, rol `super_admin`, tenant `public` y restauración del
   `ContextVar`.
4. No tocar los 13 sitios del provisionamiento, controlador de gestión, rutas,
   schemas inline, dispatcher compartido, `tenant_status.py`, migraciones ni
   dominios cerrados.
5. Actualizar la caracterización y las guardias estructurales sin cambiar
   expectativas de contrato.
6. Ejecutar pruebas específicas, Ruff, compuerta global, `git diff --check` y
   revisión exclusiva de alcance; actualizar esta bitácora y detenerse antes
   de 7.3.

Resultado:

- `core/super_admin.py` pasó de 112 a 100 líneas y de 2 a 0 sitios
  `cursor.execute`; conserva contexto `public`, conexión, cursor, cierre,
  normalización de email, comprobaciones de estado y contraseña, errores y
  offload del guard.
- `super_admin_repository.py` pasó de 97 a 121 líneas y de 5 a 7 funciones y
  sitios `cursor.execute`. Las dos operaciones nuevas reciben el cursor
  existente, reciben parámetros ya normalizados cuando corresponde y devuelven
  `fetchone()` sin administrar recursos ni transacciones.
- Los hashes SHA-256 de los dos literales SQL del `HEAD` de entrada y del
  repositorio coincidieron uno a uno: **2 de 2 textos idénticos byte a byte**.
  La caracterización conservó además parámetros, una consulta por camino,
  resultados `None`, rol, tenant, 401, restauración del contexto y cierres.
- La frontera propia conserva 20 sitios SQL: 13 de provisionamiento todavía en
  el controlador y 7 en el repositorio; el núcleo ya no contiene SQL inline.
- No se tocaron provisionamiento, controlador de gestión, rutas, schemas,
  dispatcher, `tenant_status.py`, migraciones, guardias históricas ni dominios
  cerrados.

## Primera subcapa pendiente: trabajo exacto para 7.3

1. Extraer únicamente los 13 sitios `cursor.execute` del provisionamiento de
   tenants desde `app/controllers/super_admin_controller.py` al repositorio
   propio ya existente.
2. Hacer que las operaciones del repositorio reciban el cursor. El controlador
   debe conservar validación, contexto `public`, conexión, cursor, lectura del
   SQL base, identificadores seguros, `search_path`, `commit`, `rollback`,
   cierres y traducción de errores.
3. Conservar literalmente SQL y parámetros, así como el orden y conteo de las
   13 operaciones: colegio, schema, SQL base, historial, semillas, admin,
   suscripción y auditoría. No cambiar DDL, credenciales, payloads, status
   codes, tenant, ownership ni límites de transacción.
4. No tocar rutas, schemas inline, dispatcher compartido, `tenant_status.py`,
   migraciones ni dominios cerrados; no agregar capacidades ni corregir los
   hallazgos registrados.
5. Actualizar la caracterización y cualquier guardia estructural necesaria sin
   debilitar expectativas de contrato.
6. Por ser la última subcapa, ejecutar pruebas específicas, Ruff y compuerta
   global; documentar staging, rollback y verificación manual; ejecutar
   `git diff --check`, revisar el alcance, cerrar la capa y actualizar el índice
   dejando cualquier trabajo posterior en espera.

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

## Criterios de cierre de la subcapa 7.1

- Cinco sitios SQL y solo esos extraídos al repositorio propio.
- SQL y parámetros idénticos; conteos, resultados y orden conservados.
- Controlador todavía dueño de contexto, conexión, cursor, transacción y cierre.
- Provisionamiento y autenticación intactos.
- Pruebas específicas, guardias históricas, Ruff, compuerta y dependencias
  correctas.
- `git diff --check` correcto y diff exclusivo de 7.1.
- Bitácora e índice actualizados con siguiente acción exacta.

Todos se cumplieron el 2026-08-23.

## Criterios de cierre de la subcapa 7.2

- Dos sitios SQL y solo esos extraídos al repositorio propio.
- SQL y parámetros idénticos; conteos, resultados y orden conservados.
- Núcleo todavía dueño de contexto, conexión, cursor, cierre, seguridad y
  offload; repositorio sin recursos ni transacciones.
- Provisionamiento, gestión, rutas, schemas, dispatcher, `tenant_status.py`,
  migraciones y dominios cerrados intactos.
- Pruebas específicas, Ruff, compuerta y dependencias correctas.
- `git diff --check` correcto y diff exclusivo de 7.2.
- Bitácora e índice actualizados con siguiente acción exacta.

Todos se cumplieron el 2026-08-23.

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
- **Crear un repositorio propio singular.** El nombre
  `super_admin_repository.py` coincide con el dominio y evita la variante plural
  que la caracterización rechaza expresamente.
- **Mantener los recursos en el controlador.** Las cinco funciones nuevas solo
  reciben cursor y devuelven filas; no conocen contexto, conexiones,
  transacciones, cierres ni FastAPI.
- **Reconocer el repositorio en cinco guardias históricas.** Las enumeraciones
  exactas de dashboard, notas, ventas, asistencia y planilla se ampliaron sin
  cambiar su severidad, tal como exige el precedente del programa.
- **Separar autenticación y provisionamiento.** La evidencia de 7.1 permite que
  7.2 sea una extracción de solo dos consultas de seguridad. Las 13 operaciones
  transaccionales y DDL del alta quedan aisladas para 7.3 y la compuerta de
  cierre.
- **Mantener la seguridad y los recursos en el núcleo.** Las dos operaciones de
  7.2 reciben cursor y devuelven una fila. Normalización, estado, contraseña,
  rol, tenant, 401, contexto, conexión, cursor, cierre y threadpool permanecen
  en `core/super_admin.py`.
- **No ampliar guardias históricas en 7.2.** El repositorio ya estaba enumerado
  desde 7.1; solo se actualizaron su superficie exacta, los conteos de frontera
  y el consumidor directo de SQL público.

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
- **Persistencia deliberadamente parcial.** Tras 7.2 el controlador conserva 13
  sitios SQL de provisionamiento y el núcleo ninguno. El repositorio no
  representa aún toda la frontera y no debe presentarse como migración completa.
- **Autenticación es una frontera de seguridad.** Mover sus dos consultas en
  7.2 exigía conservar contexto, normalización, contraseña, 401 y offload. La
  caracterización y la compuerta están verdes, pero cualquier cambio futuro a
  esos contratos podría bloquear o ampliar el acceso privilegiado.

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

### 2026-08-23 — cierre de la subcapa 7.1

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales se
  validaron directamente.
- Documentos leídos en el orden exigido: índice maestro completo, esta bitácora
  activa completa e instrucciones locales —no se encontraron—.
- Autorización: el usuario escribió «sigue». Conforme al índice y a esta
  bitácora, la orden autorizó solamente 7.1.
- Precondiciones antes de modificar: rama `main`; árbol limpio confirmado con
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 2]`; `HEAD`
  `f3d1711e065c9840f53674e67d9169b49ff1d3c9`; y base
  `2ec924a3308581b746a61fa24a44f71433034dbc` ancestro del `HEAD`.
- Continuidad posterior al base: `a3212ec` contiene únicamente la activación
  documental y `f3d1711` contiene únicamente los dos documentos y la prueba de
  caracterización de 7.0. Ambos alcances coinciden con esta bitácora; no había
  commits ni cambios sin explicar.
- Línea base específica sobre el `HEAD` limpio: **88 passed**, 6 warnings.
- Producto modificado: `app/controllers/super_admin_controller.py` y el nuevo
  `app/repositories/super_admin_repository.py`. El controlador pasó de 393 a
  339 líneas y de 18 a 13 `execute`; el repositorio tiene 97 líneas, cinco
  funciones y cinco `execute`.
- Pruebas modificadas: la caracterización propia y las cinco guardias exactas
  de repositorios en dashboard, notas, ventas, asistencia y planilla. La
  caracterización agregó un caso y llegó a 28 casos.
- Equivalencia estática contra el `HEAD` de entrada: **5 de 5 hashes SHA-256 de
  literales SQL idénticos**. La batería de caracterización conserva además los
  parámetros y el orden observable en ejecución.
- Batería específica integrada: **89 passed**, 6 warnings. Guardias históricas:
  **5 passed**, 1 warning. Ruff sobre los ocho archivos de producto/prueba:
  correcto.
- Compuerta global con acceso válido al directorio temporal: **1089 passed**, 5
  warnings; Ruff correcto; `pip check` sin dependencias rotas.
- No se ejecutó PostgreSQL real, migración, producción, deploy, commit ni push;
  tampoco se atribuye evidencia de GitHub Actions.
- Whitespace previo a la documentación: `git diff --check` terminó en exit 0;
  la comprobación `--no-index --check` del repositorio nuevo no reportó errores
  —su exit 1 indica que difiere de `NUL`—. Los avisos fueron solo de
  normalización futura LF/CRLF.
- Revisión previa de alcance: exactamente el controlador, el repositorio nuevo,
  la caracterización propia y las cinco guardias históricas; ningún otro archivo
  de producto.
- Decisión de siguiente frontera: 7.2 extraerá únicamente las dos consultas de
  autenticación/revalidación. El provisionamiento de 13 operaciones queda para
  7.3.
- Revisión final: `git diff --check` volvió a terminar en exit 0 después de la
  documentación. `git status --short --branch` mostró exactamente dos archivos
  de producto —controlador y repositorio—, seis pruebas —la propia y cinco
  guardias históricas— y dos documentos; todo pertenece a 7.1. El índice
  conserva una sola fila **Activa**, `super_admin`.
- Siguiente acción exacta: esperar una orden nueva para iniciar únicamente 7.2
  y detenerse antes de 7.3.

### 2026-08-23 — cierre de la subcapa 7.2

- Modo de acceso: mismo checkout local en
  `C:\Users\David\Documents\sistema_escolar_api`; Git y commits locales se
  validaron directamente.
- Documentos leídos en el orden exigido: índice maestro completo, esta bitácora
  activa completa e instrucciones locales —no se encontraron—.
- Autorización: el usuario escribió «continua». Conforme al índice y a esta
  bitácora, la orden autorizó solamente 7.2.
- Precondiciones antes de modificar: rama `main`; árbol limpio confirmado con
  `git status --porcelain=v1 --branch`, que mostró
  `## main...origin/main [ahead 3]`; `HEAD`
  `83e418a1c2fa0f62b28ce992f9fcbe609c4f5339`; y base
  `2ec924a3308581b746a61fa24a44f71433034dbc` ancestro del `HEAD`.
- Continuidad posterior al base: `a3212ec` contiene la activación documental,
  `f3d1711` contiene 7.0 y `83e418a` contiene 7.1. El último modifica
  exactamente controlador, repositorio, caracterización, cinco guardias e
  índice/bitácora, como ya estaba registrado; no había commits ni cambios sin
  explicar.
- Línea base específica sobre el `HEAD` limpio: **89 passed**, 6 warnings.
- Producto modificado: `app/core/super_admin.py` y
  `app/repositories/super_admin_repository.py`. El núcleo pasó de 112 a 100
  líneas y de 2 a 0 `execute`; el repositorio pasó de 97 a 121 líneas y de 5 a
  7 funciones y `execute`.
- Prueba modificada: `tests/test_super_admin_caracterizacion.py`, únicamente
  para actualizar las líneas, conteos, superficie exacta del repositorio y
  consumidores directos del SQL público. Sus 28 casos se conservan.
- La primera ejecución focal después del cambio tuvo **1 fallo y 51 passed**:
  la guarda de frontera detectó que los dos conteos de líneas previstos eran
  dos líneas menores que los reales. Se corrigieron solo esas expectativas a
  100 y 121; la repetición terminó con **52 passed**, 6 warnings.
- Equivalencia estática contra el `HEAD` de entrada: **2 de 2 hashes SHA-256 de
  literales SQL idénticos**. La batería conserva parámetros, retornos, contexto,
  cierres, seguridad y ejecución fuera del event loop.
- Batería específica integrada: **89 passed**, 6 warnings. Ruff sobre núcleo,
  repositorio y caracterización: correcto.
- Compuerta global con acceso válido al directorio temporal: **1089 passed**, 5
  warnings; Ruff correcto; `pip check` sin dependencias rotas.
- No se ejecutó PostgreSQL real, migración, producción, deploy, commit ni push;
  tampoco se atribuye evidencia de GitHub Actions.
- Whitespace previo a la documentación: `git diff --check` terminó en exit 0;
  los avisos fueron solo de normalización futura LF/CRLF y del perfil local de
  PowerShell.
- Revisión previa de alcance: exactamente núcleo, repositorio y caracterización
  propia; ningún archivo de provisionamiento, gestión u otro dominio.
- Decisión de siguiente frontera: 7.3 extraerá únicamente las 13 operaciones
  de provisionamiento y, por ser la última subcapa, incluirá la compuerta y la
  documentación de cierre. No se inició en este turno.
- Revisión final: `git diff --check` terminó en exit 0 después de la
  documentación. `git status --short --branch` mostró exactamente dos archivos
  de producto —núcleo y repositorio—, la caracterización propia y los dos
  documentos; todo pertenece a 7.2. El índice conserva una sola fila
  **Activa**, `super_admin`.
- Siguiente acción exacta: esperar una orden nueva para iniciar únicamente 7.3,
  completar su compuerta de cierre y detenerse sin activar trabajo posterior.

## Entrega al próximo chat

- Capa activa: **7 para `super_admin`**.
- Última capa cerrada: **7 para `profesores`**.
- Última subcapa cerrada: **7.2**, extracción de las dos consultas de
  autenticación y revalidación; 2 de 2 literales idénticos, 89 pruebas
  específicas y compuerta global con 1089 pruebas.
- Primera subcapa pendiente: **7.3**, extracción de las 13 operaciones de
  provisionamiento y cierre de la capa.
- Verificaciones pendientes aceptadas: manuales de `profesores` y `branding`,
  además de las heredadas del índice.
- Bloqueos: ninguno.
- Siguiente acción exacta: esperar una orden nueva para ejecutar únicamente
  7.3 y cerrar la capa sin activar trabajo posterior.
