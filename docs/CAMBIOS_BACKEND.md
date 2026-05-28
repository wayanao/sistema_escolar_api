# Cambios Backend

Estado documentado: 2026-05-25.

## Proposito

Bitacora de cambios documentales y tecnicos observables del backend.

## Cambio documentado

Fecha: 2026-05-25

Cambio:

- Se actualiza carpeta `docs/` para documentar el estado real actual del backend.

Archivos documentales actualizados:

- `docs/ARQUITECTURA_BACKEND.md`
- `docs/MULTITENANT.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/BASE_DATOS.md`
- `docs/API_ENDPOINTS.md`
- `docs/SEGURIDAD.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Alcance:

- estructura de `app/`;
- rutas y controladores;
- servicios y repositorios;
- autenticacion JWT;
- roles y permisos;
- multi-tenant por schema PostgreSQL;
- uso de `search_path`;
- conexion a base de datos;
- endpoints existentes;
- migraciones y scripts existentes;
- riesgos pendientes;
- variables `.env`;
- estado de preparacion para produccion.

Restricciones aplicadas:

- No se modifico logica del backend.
- No se propusieron cambios nuevos en estos documentos.
- Se documento solo lo observado en el codigo actual.

## 2026-05-25 - Seguridad multi-tenant consolidada

Se consolida en este archivo la bitacora detallada que estaba en README_SEGURIDAD_MULTITENANT.md.

Motivo:

- Evitar documentacion duplicada en la raiz del backend.
- Dejar docs/CAMBIOS_BACKEND.md como bitacora oficial de cambios.
- Conservar pruebas, comandos, decisiones y pendientes de la auditoria multi-tenant.

Resultado:

- README_SEGURIDAD_MULTITENANT.md fue eliminado de la raiz.
- docs/HISTORIAL_SEGURIDAD_MULTITENANT.md fue eliminado porque quedaba duplicado.
- La bitacora historica queda integrada abajo en este mismo archivo.

### Bitacora historica integrada

# Seguimiento de seguridad multi-tenant

Fecha: 2026-05-19

Este documento resume los cambios realizados para endurecer la seguridad
multi-tenant del backend antes de produccion, y deja una lista clara de
pendientes para continuar mas adelante.

## Cambios realizados hoy

### 1. Nomina protegida solo para admin

Archivo:
- `app/routes/nomina.py`

Cambio:
- El router de nomina ahora usa `get_current_active_admin`.
- Antes cualquier request podia acceder a endpoints de nomina si conocia la URL.

Impacto:
- Sin token responde `401`.
- Profesor responde `403`.
- Admin puede operar normalmente.

### 2. Eliminado fallback a tenant por defecto

Archivos:
- `app/globals.py`
- `app/db/tenant.py`
- `app/dependencies.py`
- `app/main.py`

Cambio:
- El `ContextVar` de tenant ya no inicia en `tenant_colegio_1`.
- Si una request no tiene tenant valido, falla en vez de apuntar a un colegio real.
- El JWT debe traer `tenant` valido.

Impacto:
- Evita que requests mal formadas o sin tenant caigan accidentalmente sobre datos reales.

### 3. `public` ya no es tenant valido para usuarios

Archivo:
- `app/db/tenant.py`

Cambio:
- `TENANT_SCHEMA_PATTERN` ya no acepta `public`.
- Se agrego `INTERNAL_SCHEMA_PATTERN` para permitir `public` solo en operaciones internas, como login.

Impacto:
- Un JWT de usuario con `tenant = public` ya no debe ser aceptado.
- El login sigue pudiendo consultar `public.colegios`.

### 4. Usuarios administrativos solo para admin

Archivos:
- `app/routes/usuario.py`
- `app/controllers/usuario_controller.py`

Cambio:
- `/usuarios` ahora requiere `get_current_active_admin`.
- Al crear o actualizar usuarios, la password se guarda con `get_password_hash`.

Impacto:
- Profesor no puede crear, editar, listar ni eliminar usuarios internos.
- Nuevas passwords ya no se guardan en texto plano.

### 5. Inventario solo para admin

Archivo:
- `app/routes/inventario.py`

Cambio:
- Todo el modulo de inventario ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede consultar ni modificar inventario desde API.

### 6. Tipos de pagos solo para admin

Archivo:
- `app/routes/tipos_pagos.py`

Cambio:
- Todo el modulo de tipos de pagos ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede cambiar conceptos, valores, mora ni asignaciones por curso.

### 7. Reportes solo para admin

Archivo:
- `app/routes/reportes.py`

Cambio:
- Todo el modulo de reportes ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede acceder a reportes financieros o resumenes globales.

### 8. Asignaciones separadas por permisos

Archivos:
- `app/routes/asignaciones.py`
- `src/pages/DashboardProfesor.jsx` en frontend

Cambio:
- Crear, editar, eliminar y listar todas las asignaciones ahora es admin-only.
- Profesor puede consultar solo sus propias clases.
- Se agrego validacion de ownership por `profesor_id`.
- El dashboard del profesor ya no consume `/asignaciones/lista`; usa `/mis-clases/{profesor_id}`.
- `/mis-clases/{profesor_id}` ahora devuelve tambien `dia`, `hora_inicio` y `hora_fin`.

Impacto:
- Profesor ya no puede consultar la lista global de asignaciones.
- Profesor conserva su horario y sus clases.

### 9. Dashboard de profesor con ownership

Archivo:
- `app/routes/dashboard.py`

Cambio:
- Endpoints por `profesor_id` validan que el profesor solo consulte su propio ID.
- Endpoints por `asignacion_id` validan que la asignacion pertenezca al profesor.
- Admin puede consultar todo.

Impacto:
- Evita que un profesor cambie IDs para ver datos academicos de otro profesor.

### 10. Plan de clases con ownership

Archivo:
- `app/routes/plan_de_clases.py`

Cambio:
- `POST /plan-de-clases` valida que la asignacion pertenezca al profesor.
- `GET /plan-de-clases/{asignacion_id}` valida ownership.
- Admin mantiene acceso global por `/admin/plan-de-clases`.

Impacto:
- Profesor no puede crear ni consultar planeadores de una asignacion ajena.

### 11. Planilla y notas con ownership por asignacion

Archivos:
- `app/routes/planilla.py`
- `app/routes/notas.py`

Cambio:
- `POST /planilla/nota` valida ownership de `data.asignacion_id`.
- `GET /planilla-excel/{asignacion_id}/{periodo}` valida ownership.
- `DELETE /planilla/tipo` valida ownership.
- `POST /notas` valida ownership de `nota.asignacion_id`.
- `GET /planilla/{asignacion_id}` valida ownership.
- `POST /boletin/guardar` valida ownership de cada `materia.asignacion_id`.

Impacto:
- Profesor no puede registrar, borrar o consultar planillas/notas de asignaciones ajenas.

### 12. Revalidacion de usuario/rol contra DB

Archivo:
- `app/dependencies.py`

Cambio:
- `get_current_user` ya no confia solamente en el JWT.
- Despues de validar firma, tenant y rol del token, consulta la base del tenant.
- Si el rol es `profesor`, confirma que exista en la tabla `profesor`.
- Si el rol no es `profesor`, confirma que exista en `usuarios` y que el rol actual en DB coincida con el rol del token.
- Si en alguna tabla existen columnas `estado` o `activo`, tambien las respeta.

Impacto:
- Si un usuario se elimina o cambia de rol, un token viejo deja de servir.
- Si mas adelante se agregan columnas `estado` o `activo` a `usuarios`/`profesor`, la validacion queda lista para bloquear cuentas inactivas.

### 13. Boletines con permisos separados

Archivo:
- `app/routes/boletines.py`

Cambio:
- `POST /boletines/guardar` valida que la asignacion pertenezca al profesor o que el usuario sea admin.
- `POST /boletines/guardar` tambien valida que el estudiante pertenezca al curso de esa asignacion.
- `GET /boletines/referencia/{asignacion_id}/{periodo}` valida ownership por asignacion.
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede guardar ni consultar boletines de asignaciones ajenas.
- Profesor no puede guardar boletin cruzando un estudiante que no pertenece a la asignacion.
- La generacion global de boletines queda limitada a admin.

### 14. Asistencia con ownership por asignacion

Archivos:
- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`

Cambio:
- `POST /asistencia` valida que cada asignacion enviada pertenezca al profesor o que el usuario sea admin.
- `POST /asistencia` valida que cada estudiante pertenezca al curso de su asignacion.
- `GET /asistencia/historial/{asignacion_id}/{periodo}` valida ownership por asignacion.
- Se removieron `print` con datos de asistencia recibida para no exponer informacion en logs.

Impacto:
- Profesor no puede registrar ni consultar asistencia de asignaciones ajenas.
- Profesor no puede registrar asistencia cruzando estudiantes fuera del curso de la asignacion.

### 15. Estudiantes, pagos, cuentas y cartera solo para admin

Archivos:
- `app/routes/estudiantes.py`
- `app/routes/pagos.py`
- `app/routes/cuentas.py`
- `app/routes/cartera.py`

Cambio:
- Estos routers ahora usan `get_current_active_admin`.
- Se confirmo que el flujo del profesor para observaciones usa `/planilla/{asignacion_id}`, no `/estudiantes`.

Impacto:
- Profesor no puede listar ni modificar estudiantes desde endpoints administrativos.
- Profesor no puede consultar ni registrar pagos.
- Profesor no puede consultar estados de cuenta ni cartera vencida.
- Las pantallas admin existentes siguen siendo las consumidoras naturales de estos endpoints.

### 16. Cursos, materias y profesores solo para admin

Archivos:
- `app/routes/cursos.py`
- `app/routes/materias.py`
- `app/routes/profesores.py`

Cambio:
- Estos routers ahora usan `get_current_active_admin`.
- Se revisaron usos en frontend y aparecen ligados a pantallas administrativas como crear cursos, crear materias, crear profesores, asignar clases, planeadores admin y boletin admin.
- Los flujos del profesor continúan usando rutas ya acotadas como `/mis-clases/{profesor_id}`, `/planilla/{asignacion_id}` y rutas por asignacion con ownership.

Impacto:
- Profesor no puede crear, editar ni listar catalogos academicos globales desde API.
- La estructura academica queda bajo control del admin.

### 17. `/uploads` protegido por autenticacion y tenant

Archivos:
- `app/main.py`
- `app/dependencies.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/controllers/branding_controller.py`

Cambio:
- Se elimino el `app.mount("/uploads", StaticFiles(...))` publico.
- Se agrego `GET /uploads/{file_path:path}` como endpoint autenticado.
- `get_current_user` ahora tambien puede leer el token desde cookie `token`, necesario para que etiquetas `<img>` puedan cargar logos/imagenes.
- El endpoint valida que la ruta real quede dentro de la carpeta `uploads`.
- El endpoint valida tenant:
  - `uploads/branding/{tenant}/...` solo se sirve a usuarios autenticados de ese tenant.
  - `uploads/{tenant}/plan_de_clases/...` solo se sirve al admin del tenant o al profesor propietario de la asignacion asociada a esa imagen.
- Las imagenes de plan de clases ahora se guardan con UUID, no con el nombre original del archivo.
- Las imagenes de plan de clases validan extension, content-type y tamano maximo.
- Los nuevos logos ya no permiten SVG; solo PNG, JPG/JPEG y WEBP.
- El borrado de logos valida que el archivo real este dentro de `uploads`.

Impacto:
- Un usuario sin token ya no puede abrir archivos de `/uploads`.
- Un usuario de otro tenant no puede abrir archivos de otro colegio por URL.
- Un profesor no puede abrir imagenes de planeadores ajenos si adivina la URL.
- Se reduce riesgo de path traversal y de XSS por SVG en nuevos logos.

Nota:
- En produccion, si frontend y backend viven en dominios/subdominios distintos, revisar configuracion de cookie `token` para que las imagenes autenticadas se carguen correctamente desde `<img>`.

### 18. Script legacy de admin eliminado

Archivos:
- `insert_admin.sql`

Cambio:
- Se elimino `insert_admin.sql` de la raiz del backend.
- Tambien se elimino la copia legacy que habia quedado como referencia.

Impacto:
- Elimina el riesgo de ejecutar por accidente un script que crea un admin con password en texto plano.
- El flujo recomendado para crear tenants y admin inicial sigue siendo `crear_cliente.py`, porque hashea la password.

### 19. Prueba base de permiso por estudiante

Archivos:
- `app/core/permissions.py`
- `tests/test_permissions.py`
- `tests/test_notas_permissions.py`

Cambio:
- Se agregaron pruebas unitarias para `require_estudiante_access`.
- Las pruebas validan:
  - admin pasa sin consultar DB;
  - profesor duenio del estudiante pasa;
  - profesor no duenio recibe `403`;
  - rol no autorizado recibe `403`.
- Se agregaron pruebas de cableado para confirmar que las rutas antiguas de
  `notas.py` llaman el permiso antes de devolver datos:
  - `GET /notas/{estudiante_id}`;
  - `GET /boletin/{estudiante_id}`;
  - `GET /boletin/detallado/{estudiante_id}`.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py`
- Resultado: 8 pruebas pasaron.

Pendiente manual:
- Probar funcionalmente en la app con usuarios reales:
  - profesor duenio del estudiante;
  - profesor no duenio;
  - admin;
  - request sin token.

Prueba manual realizada:
- Se intento consultar un estudiante no autorizado desde URL directa y el backend respondio `{"detail":"No autorizado"}`.

### 20. Pruebas base de auth, tenant y uploads

Archivos:
- `tests/test_auth_tenant.py`
- `tests/test_uploads_permissions.py`

Cambio:
- Se agregaron pruebas unitarias para `get_current_user`:
  - sin token responde `401`;
  - token invalido responde `401`;
  - token con `tenant=public` responde `401`;
  - token valido fija el tenant y revalida usuario contra DB;
  - usuario eliminado o rol cambiado invalida el token.
- Se agregaron pruebas unitarias para la validacion de `/uploads`:
  - branding del mismo tenant se permite;
  - branding de otro tenant se bloquea;
  - path traversal se bloquea;
  - admin del tenant puede abrir imagen de plan de clases;
  - profesor duenio puede abrir imagen de su plan de clases;
  - profesor no duenio recibe `403`.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 19 pruebas pasaron.

Nota:
- Aparecieron advertencias de dependencias/Pydantic, pero no errores de pruebas.

### 21. Runner de migraciones con historial

Archivos:
- `apply_migration.py`
- `migrations/README.md`
- `tests/test_apply_migration.py`

Cambio:
- Se mejoro `apply_migration.py` para registrar historial en `public.schema_migrations`.
- Se agrega checksum SHA-256 por migracion.
- Si una migracion ya fue aplicada en un tenant con el mismo checksum, se omite.
- Si existe el mismo nombre de migracion con checksum diferente, se bloquea.
- Se agrego modo `--dry-run` para simular antes de aplicar cambios.
- Se reemplazo el `SET search_path` construido manualmente por `psycopg2.sql.Identifier`.

Uso recomendado:
- `python apply_migration.py migrations/<archivo>.sql --dry-run`
- `python apply_migration.py migrations/<archivo>.sql`

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 24 pruebas pasaron.

Pendiente:
- Probar el runner contra una copia de la base real antes de usarlo en produccion.
- Decidir mas adelante si se migra completamente a Alembic.

### 22. Script de indices por tenant actualizado

Archivos:
- `scripts/apply_tenant_indexes.py`
- `tests/test_apply_tenant_indexes.py`

Cambio:
- Se completo la lista de indices recomendados para consultas frecuentes.
- Se agrego modo `--dry-run` para simular sin crear indices.
- El script ahora valida que la tabla exista antes de crear el indice.
- El script ahora valida que las columnas existan antes de crear el indice.
- Si una tabla o columna falta en un tenant, se omite sin romper todo el proceso.

Indices incluidos:
- `estudiantes(curso_id)`
- `asignaciones(profesor_id)`
- `asignaciones(curso_id)`
- `notas_detalle(estudiante_id, asignacion_id, periodo)`
- `boletin_cabecera(estudiante_id, asignacion_id, periodo)`
- `asistencia(asignacion_id, periodo)`
- `asistencia(estudiante_id, fecha)`
- `pagos(estudiante_id)`
- `ventas(estudiante_id, estado)`
- `plan_de_clases(asignacion_id, fecha)`

Uso recomendado:
- Simular: `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py --dry-run`
- Aplicar: `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py`

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 28 pruebas pasaron.
- Se ejecuto `--dry-run` y encontro 2 tenants activos: `tenant_3333` y `tenant_colegio_1`.
- No se crearon indices durante la simulacion.
- Se ejecuto el script real y los indices quedaron verificados en `tenant_3333` y `tenant_colegio_1`.

Pendiente:
- Despues de aplicar, revisar consultas pesadas con `EXPLAIN ANALYZE`.

### 23. Paginacion compatible en estudiantes

Archivos:
- `app/routes/estudiantes.py`
- `app/controllers/estudiante_controller.py`
- `tests/test_estudiantes_pagination.py`

Cambio:
- `GET /estudiantes` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /estudiantes?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agrego `busqueda` opcional:
  - `GET /estudiantes?limit=50&offset=0&busqueda=ana`
- El limite maximo permitido por request es `200`.

Motivo:
- Evita romper las pantallas actuales que consumen `/estudiantes` como lista.
- Permite migrar el frontend a paginacion pantalla por pantalla.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_estudiantes_pagination.py tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 30 pruebas pasaron.

Pruebas manuales recomendadas:
- `GET /estudiantes`
- `GET /estudiantes?limit=20&offset=0`
- `GET /estudiantes?limit=20&offset=0&busqueda=<texto>`

### 24. Paginacion compatible en ventas

Archivos:
- `app/routes/ventas.py`
- `app/controllers/venta_controller.py`
- `tests/test_ventas_pagination.py`

Cambio:
- `GET /api/ventas/` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /api/ventas/?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `busqueda`;
  - `estudiante_id`;
  - `estado`.
- El limite maximo permitido por request es `200`.
- En modo paginado, el backend solo carga los detalles de las ventas de esa pagina, no todos los detalles historicos.

Motivo:
- Evita cargar todas las ventas y todos sus detalles cuando el historial crezca.
- Mantiene intacta la pantalla actual mientras se migra el frontend con calma.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`

Pruebas manuales recomendadas:
- `GET /api/ventas/`
- `GET /api/ventas/?limit=20&offset=0`
- `GET /api/ventas/?limit=20&offset=0&estado=Pendiente`
- `GET /api/ventas/?limit=20&offset=0&busqueda=<texto>`

### 25. Paginacion compatible en pagos por estudiante

Archivos:
- `app/routes/pagos.py`
- `app/controllers/pagos_controller.py`
- `tests/test_pagos_pagination.py`

Cambio:
- `GET /pagos/{estudiante_id}` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /pagos/{estudiante_id}?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.

Motivo:
- El historial de pagos puede crecer mucho por estudiante.
- Permite migrar la pantalla de pagos a paginacion sin romper el flujo actual de facturacion/recibos.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /pagos/<estudiante_id>`
- `GET /pagos/<estudiante_id>?limit=20&offset=0`
- `GET /pagos/<estudiante_id>?limit=20&offset=20`

### 26. Paginacion compatible en inventario

Archivos:
- `app/routes/inventario.py`
- `app/controllers/inventario_controller.py`
- `tests/test_inventario_pagination.py`

Cambio:
- `GET /inventario` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /inventario?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `busqueda`;
  - `solo_con_stock`.
- El limite maximo permitido por request es `200`.

Motivo:
- Inventario se usa en administracion y en punto de venta.
- Al crecer el catalogo, permite cargar productos por paginas sin romper las pantallas actuales.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /inventario`
- `GET /inventario?limit=20&offset=0`
- `GET /inventario?limit=20&offset=0&busqueda=<texto>`
- `GET /inventario?limit=20&offset=0&solo_con_stock=true`

### 27. Paginacion compatible en reportes de ingresos

Archivos:
- `app/routes/reportes.py`
- `app/controllers/reportes_controller.py`
- `scripts/apply_tenant_indexes.py`
- `tests/test_reportes_pagination.py`
- `tests/test_apply_tenant_indexes.py`

Cambio:
- `GET /reportes/ingresos-mes/{mes}` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /reportes/ingresos-rango?inicio=<fecha>&fin=<fecha>` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- Ambos endpoints aceptan ahora `limit` y `offset`.
- Con paginacion devuelven:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.
- Se agregaron al script de indices:
  - `pagos(fecha)`;
  - `pagos(fecha_pago)`.

Motivo:
- Los reportes financieros por mes/rango pueden crecer mucho y devolver demasiados pagos.
- La pantalla actual de reportes sigue funcionando sin cambios.
- Los indices por fecha preparan mejor la base para consultas historicas grandes.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_reportes_pagination.py tests\test_apply_tenant_indexes.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /reportes/ingresos-mes/2026-05`
- `GET /reportes/ingresos-mes/2026-05?limit=20&offset=0`
- `GET /reportes/ingresos-rango?inicio=2026-05-01&fin=2026-05-31`
- `GET /reportes/ingresos-rango?inicio=2026-05-01&fin=2026-05-31&limit=20&offset=0`

Pendiente operativo:
- Se ejecuto `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py --dry-run` y encontro los indices nuevos pendientes de verificacion en `tenant_3333` y `tenant_colegio_1`.
- Si la simulacion se ve bien, ejecutar `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py` para verificar/crear los indices nuevos.

### 28. Paginacion compatible en asignaciones administrativas

Archivos:
- `app/routes/asignaciones.py`
- `app/controllers/asignacion_controller.py`
- `tests/test_asignaciones_pagination.py`

Cambio:
- `GET /asignaciones/lista` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /asignaciones/lista?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `profesor_id`;
  - `curso_id`;
  - `materia_id`;
  - `busqueda`.
- El limite maximo permitido por request es `200`.

Motivo:
- La grilla de asignacion de clases necesita seguir cargando todas las asignaciones como hoy para validar cruces visuales y materias duplicadas.
- La paginacion queda disponible para futuras vistas administrativas o busquedas mas livianas.
- Es un listado sensible porque cruza profesor, curso, materia y horario.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_asignaciones_pagination.py tests\test_reportes_pagination.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /asignaciones/lista`
- `GET /asignaciones/lista?limit=20&offset=0`
- `GET /asignaciones/lista?limit=20&offset=0&profesor_id=<id>`
- `GET /asignaciones/lista?limit=20&offset=0&curso_id=<id>`
- `GET /asignaciones/lista?limit=20&offset=0&busqueda=<texto>`

### 29. Paginacion compatible en catalogos administrativos

Archivos:
- `app/routes/profesores.py`
- `app/controllers/profesor_controller.py`
- `app/routes/cursos.py`
- `app/controllers/curso_controller.py`
- `app/routes/materias.py`
- `app/controllers/materia_controller.py`
- `app/routes/usuario.py`
- `app/controllers/usuario_controller.py`
- `tests/test_catalogos_pagination.py`

Cambio:
- `GET /profesores`, `GET /cursos`, `GET /materias` y `GET /usuarios` conservan el comportamiento anterior si no se envian parametros: devuelven listas simples.
- Todos aceptan ahora `limit` y `offset`.
- `profesores`, `cursos`, `materias` y `usuarios` aceptan `busqueda`.
- `usuarios` acepta ademas filtro `rol`.
- Con paginacion devuelven:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.

Motivo:
- Son catalogos normalmente pequenos, pero dejarlos con paginacion opcional completa el patron del backend.
- Permite crear futuras pantallas administrativas con busqueda/paginacion sin cambiar contratos existentes.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_catalogos_pagination.py tests\test_asignaciones_pagination.py tests\test_reportes_pagination.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /profesores`
- `GET /profesores?limit=20&offset=0&busqueda=<texto>`
- `GET /cursos`
- `GET /cursos?limit=20&offset=0&busqueda=<texto>`
- `GET /materias`
- `GET /materias?limit=20&offset=0&busqueda=<texto>`
- `GET /usuarios`
- `GET /usuarios?limit=20&offset=0&busqueda=<texto>&rol=admin`

### 30. Permisos repetidos centralizados

Archivos:
- `app/core/permissions.py`
- `app/routes/notas.py`
- `app/routes/planilla.py`
- `app/routes/asistencia.py`
- `app/routes/boletines.py`
- `app/routes/dashboard.py`
- `app/routes/asignaciones.py`
- `app/routes/plan_de_clases.py`
- `tests/test_permissions.py`

Cambio:
- Se consolido `app/core/permissions.py` como modulo unico para permisos reutilizables.
- Se agregaron funciones centrales:
  - `require_profesor_scope`;
  - `require_asignacion_access`;
  - `require_estudiante_access`;
  - `require_estudiante_in_asignacion`;
  - `require_plan_de_clases_access`.
- Se reemplazaron validaciones locales repetidas en rutas criticas:
  - notas;
  - planilla;
  - asistencia;
  - boletines;
  - dashboard;
  - asignaciones;
  - plan de clases.

Motivo:
- Evita que cada ruta tenga su propia version de permisos.
- Reduce riesgo de que una ruta quede mas permisiva que otra por error.
- Hace mas facil auditar y endurecer reglas multi-tenant/profesor/admin en un solo lugar.

Decision tecnica:
- Se mantuvo el modulo en `app/core/permissions.py`.
- No se creo `app/security/permissions.py` porque ya existe `app/security.py`; crear una carpeta con el mismo nombre podria causar conflictos de importacion en Python.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_asignaciones_pagination.py`
- Resultado: 25 pruebas pasaron.

Pruebas manuales recomendadas:
- Profesor debe poder ver sus propias clases en `/mis-clases/<profesor_id>`.
- Profesor no debe poder ver clases de otro profesor cambiando el ID.
- Profesor debe poder abrir planilla/notas/asistencia de sus asignaciones.
- Profesor debe recibir `403` al intentar una asignacion ajena.
- Admin debe conservar acceso administrativo normal.

## Verificaciones realizadas

- Validacion de sintaxis con `ast.parse` en los archivos Python modificados.
- Build de frontend con `pnpm run build` despues de corregir el horario del profesor.
- El build de frontend termino correctamente.
- Validacion de sintaxis de `app/dependencies.py` despues de agregar revalidacion contra DB.
- Validacion de sintaxis de `app/routes/boletines.py` despues de agregar permisos por asignacion/admin.
- Validacion de sintaxis de `app/routes/asistencia.py` y `app/controllers/asistencia_controller.py`.
- Validacion de sintaxis de `app/routes/estudiantes.py`, `app/routes/pagos.py`, `app/routes/cuentas.py` y `app/routes/cartera.py`.
- Validacion de sintaxis de `app/routes/cursos.py`, `app/routes/materias.py` y `app/routes/profesores.py`.
- Validacion de sintaxis de `app/main.py`, `app/dependencies.py`, `app/controllers/plan_de_clases_controller.py` y `app/controllers/branding_controller.py`.

## Pendientes importantes

### 1. Revisar scripts antiguos

Archivo:
- `insert_admin.sql`

Estado:
- Hecho. El script fue eliminado por completo.

Riesgo residual:
- Ninguno desde el repositorio, mientras no se recree un script similar con password en texto plano.

### 2. Provisionamiento de tenants

Archivo:
- `crear_cliente.py`

Estado:
- Actualmente el alta de tenant se hace por terminal.
- Este flujo hashea la password del admin inicial.

Pendiente:
- Mas adelante crear panel o comando superadmin mas robusto.
- Asegurar migraciones completas para cada tenant nuevo.

## Recomendacion de siguiente sesion

Orden sugerido:

1. Revisar scripts antiguos y provisionamiento de tenants.
2. Probar en entorno real que logos e imagenes de planeadores cargan correctamente con el nuevo `/uploads` autenticado.

## Hoja de ruta de auditoria para produccion

Esta seccion resume el paso a paso recomendado despues de la auditoria general
del sistema. El objetivo es seguir endureciendo seguridad, escalabilidad y
mantenibilidad sin romper funcionalidades existentes.

### 1. Seguridad inmediata: cerrar endpoints por `estudiante_id`

Archivo principal:
- `app/routes/notas.py`

Endpoints a cerrar:
- `GET /notas/{estudiante_id}`
- `GET /boletin/{estudiante_id}`
- `GET /boletin/detallado/{estudiante_id}`

Riesgo:
- Aunque el usuario este autenticado, hoy un profesor podria cambiar el
  `estudiante_id` en la URL e intentar consultar notas o boletines de un
  estudiante que no pertenece a sus asignaciones dentro del mismo tenant.

Accion recomendada:
- Crear una validacion de acceso por estudiante.
- Admin: puede consultar estudiantes dentro de su tenant.
- Profesor: solo puede consultar estudiantes cuyo curso tenga una asignacion
  perteneciente a ese profesor.
- Si no cumple, responder `403`.

Pruebas necesarias:
- Profesor duenio del estudiante recibe `200`.
- Profesor no duenio recibe `403`.
- Admin recibe `200` dentro de su tenant.
- Sin token recibe `401`.
- Token de otro tenant no debe ver datos fuera de su schema.

### 2. Scripts peligrosos

Archivo:
- `insert_admin.sql`

Riesgo:
- Crea un usuario admin con password plano (`admin123`).

Accion recomendada:
- Hecho: fue eliminado por completo porque no era necesario para el funcionamiento del sistema.
- Mantener como flujo oficial `crear_cliente.py`, porque hashea la password.

### 3. Pruebas base de seguridad

Objetivo:
- Montar pruebas automatizadas minimas antes de produccion.

Casos obligatorios:
- Login correcto por tenant.
- Login falla con colegio inactivo o inexistente.
- Token viejo falla si el usuario se elimina o cambia de rol.
- Profesor no puede consultar asignaciones ajenas.
- Profesor no puede consultar estudiantes ajenos.
- Admin puede operar dentro de su tenant.
- `/uploads` exige autenticacion.
- `/uploads` bloquea archivos de otro tenant.
- Passwords nuevas siempre quedan hasheadas.

Estado:
- Iniciado. Ya existen pruebas para:
  - regla de acceso por estudiante;
  - rutas antiguas de notas;
  - auth/JWT/tenant;
  - validacion de uploads protegidos.
- Falta ampliar pruebas a flujos completos con DB de prueba e integracion de endpoints reales.

### 4. Migraciones

Estado actual:
- Existen scripts sueltos y una carpeta `migrations`.
- Alembic aun no esta inicializado como fuente formal de verdad.
- `apply_migration.py` ya tiene historial por tenant con checksum y `--dry-run`.

Accion recomendada:
- Usar `apply_migration.py` como runner temporal seguro.
- Ejecutar siempre primero con `--dry-run`.
- Inicializar Alembic mas adelante, o consolidar este runner propio como flujo oficial.
- Distinguir entre:
  - cambios globales en `public`;
  - cambios repetidos en schemas `tenant_*`;
  - indices y constraints por tenant.

Riesgo si no se hace:
- Un tenant nuevo puede quedar con tablas o columnas distintas.
- Un cambio aplicado manualmente puede no llegar a todos los colegios.

### 5. Indices y revision con `EXPLAIN ANALYZE`

Accion recomendada:
- Usar `scripts/apply_tenant_indexes.py` para aplicar indices por tenant.
- Ejecutar primero `--dry-run`.
- Revisar reportes con `EXPLAIN ANALYZE`.

Prioridad de indices:
- `estudiantes(curso_id)`
- `asignaciones(profesor_id)`
- `asignaciones(curso_id)`
- `notas_detalle(estudiante_id, asignacion_id, periodo)`
- `boletin_cabecera(estudiante_id, asignacion_id, periodo)`
- `asistencia(asignacion_id, periodo)`
- `asistencia(estudiante_id, fecha)`
- `pagos(estudiante_id)`
- `ventas(estudiante_id, estado)`
- `plan_de_clases(asignacion_id, fecha)`

Estado:
- Script actualizado con modo seguro `--dry-run`.
- Pruebas unitarias agregadas.
- Simulacion ejecutada correctamente.
- Indices reales aplicados/verificados en los tenants activos.
- Falta medir consultas pesadas con `EXPLAIN ANALYZE`.

### 6. Paginacion

Problema:
- Varios endpoints devuelven listas completas. Esto funciona con pocos datos,
  pero puede afectar memoria, tiempos de respuesta y experiencia de usuario.

Empezar por:
- `GET /estudiantes` (iniciado con paginacion compatible)
- ventas
- pagos por estudiante
- reportes de ingresos por rango
- inventario
- asignaciones/listados administrativos

Accion recomendada:
- Agregar `limit` y `offset` con limites maximos razonables.
- Mantener compatibilidad con el frontend actual mientras se migra pantalla por pantalla.

Estado:
- `GET /estudiantes` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /api/ventas/` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /pagos/{estudiante_id}` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /inventario` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /reportes/ingresos-mes/{mes}` y `GET /reportes/ingresos-rango` ya soportan paginacion opcional sin romper el contrato anterior.
- `GET /asignaciones/lista` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /profesores`, `GET /cursos`, `GET /materias` y `GET /usuarios` ya soportan paginacion opcional sin romper el contrato anterior.
- La fase de paginacion compatible queda cubierta en los listados administrativos principales.

### 7. Refactor de permisos

Problema:
- Las validaciones de permisos estan repetidas en varios routers.

Accion escalable recomendada:
- Crear un archivo central, por ejemplo:
  - `app/security/permissions.py`

Funciones sugeridas:
- `require_admin(current_user)`
- `require_asignacion_access(asignacion_id, current_user)`
- `require_estudiante_access(estudiante_id, current_user)`
- `require_estudiante_in_asignacion(estudiante_id, asignacion_id)`

Estrategia segura:
- No mover todo de una vez.
- Primero crear funciones centrales.
- Migrar una ruta critica.
- Probar.
- Continuar modulo por modulo.

Estado:
- Iniciado y aplicado en rutas criticas de profesor/asignacion/estudiante/plan de clases.
- Falta una segunda pasada mas adelante para revisar otros permisos especiales y simplificar imports/casos no cubiertos por estas funciones.

### 8. Refactor de modulos grandes

Archivos backend que conviene dividir:
- `app/controllers/estudiante_controller.py`
- `app/controllers/reportes_controller.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/asignacion_controller.py`
- `app/controllers/tipos_pagos_controller.py`

Archivos frontend que conviene dividir:
- `src/components/cartera/AdministrarTiposPago.jsx`
- `src/pages/EstudiantesAdmin.jsx`
- `src/components/AsignarClaseGrid.jsx`
- `src/pages/CarteraVencidaAdmin.jsx`
- `src/pages/PagosAdmin.jsx`

Objetivo:
- Separar UI, llamadas API, helpers de formato, validaciones y componentes hijos.
- Reducir riesgo de romper una pantalla completa por cambios pequenos.

### 9. Endurecer sesion

Estado actual:
- El frontend guarda token en cookie creada por JavaScript y conserva datos en
  `localStorage`.

Riesgo:
- Si algun dia aparece XSS, el token podria quedar expuesto.

Accion recomendada para produccion:
- Mover el token a cookie `HttpOnly`, `Secure`, `SameSite`.
- El backend debe emitir y limpiar la cookie.
- El frontend no deberia necesitar leer el token directamente.

### 10. Provisionamiento de tenants

Archivo actual:
- `crear_cliente.py`

Estado:
- Hoy el tenant se crea desde terminal.
- El flujo actual hashea la password del admin inicial.

Accion recomendada:
- Mantener terminal por ahora, pero documentar checklist.
- Validar que cada tenant nuevo reciba todas las tablas, datos iniciales,
  plantillas, branding vacio, indices y migraciones.
- A mediano plazo crear flujo superadmin o comando CLI mas robusto.

Checklist minimo de tenant nuevo:
- Registro en `public.colegios`.
- Schema creado con nombre valido.
- Tablas completas.
- Indices aplicados.
- Plantillas predefinidas copiadas.
- Branding inicial creado.
- Admin inicial con password hasheada.
- Login probado.
- Build/frontend apuntando al backend correcto.

## Lectura general de estado

El sistema ya avanzo bastante en seguridad multi-tenant: se elimino el fallback
a tenant real, se protegio gran parte de los modulos administrativos, se
revalida usuario contra DB, y `/uploads` ya no es publico.

Aun asi, no se considera listo para produccion masiva hasta cerrar tres frentes:

1. Ownership por `estudiante_id` en rutas antiguas de `notas.py`.
2. Pruebas automatizadas de acceso cruzado, autenticacion, tenants y uploads.
3. Migraciones confiables para que todos los tenants tengan el mismo schema.

La base ya es seria, pero falta la parte menos visible y mas importante:
pruebas, permisos centralizados, migraciones, paginacion e indices.

importante: cuando se modifique cada paso pedir probar lo que se acctualizo



## 2026-05-26 - Cierre incremental de ownership en rutas de profesor

Se continuo la fase critica de seguridad backend enfocada en rutas con IDs directos manipulables desde el navegador.

### Observaciones protegidas por asignacion y estudiante

Archivo modificado:

- `app/routes/observaciones.py`

Cambio:

- `POST /observaciones` ahora valida `asignacion_id` con `require_asignacion_access`.
- `POST /observaciones` ahora valida que `estudiante_id` pertenezca a la asignacion con `require_estudiante_in_asignacion`.
- `GET /observaciones/{estudiante_id}/{asignacion_id}/{periodo}` aplica las mismas validaciones antes de consultar.

Riesgo cerrado:

- Un profesor autenticado podia intentar cambiar manualmente `estudiante_id` o `asignacion_id` para leer o guardar observaciones de una asignacion ajena.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m py_compile app\routes\observaciones.py
.\venv\Scripts\python.exe -m pytest tests\test_permissions.py
```

Resultado:

- `tests/test_permissions.py`: 14 pruebas pasaron.

Pruebas manuales recomendadas:

- Profesor duenio debe poder guardar y consultar observaciones de su asignacion.
- Profesor no duenio debe recibir `403` al cambiar `asignacion_id` por una asignacion ajena.
- Profesor debe recibir `403` si intenta cruzar un estudiante que no pertenece a la asignacion.
- Admin debe conservar acceso normal dentro del tenant.
- Request sin token debe responder `401`.

### Planeador anual protegido por asignacion

Archivo modificado:

- `app/routes/planeador_anual.py`

Cambio:

- `GET /planeador-anual/{asignacion_id}/{periodo}` ahora valida `asignacion_id` con `require_asignacion_access`.
- `PUT /planeador-anual/{asignacion_id}/{periodo}` aplica la misma validacion antes de actualizar.

Riesgo cerrado:

- Un profesor autenticado podia intentar cambiar manualmente `asignacion_id` para consultar o actualizar el planeador anual de otro profesor.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m py_compile app\routes\planeador_anual.py
.\venv\Scripts\python.exe -m pytest tests\test_permissions.py
```

Resultado:

- `tests/test_permissions.py`: 14 pruebas pasaron.

Pruebas manuales recomendadas:

- Profesor duenio debe poder consultar y actualizar su planeador anual.
- Profesor no duenio debe recibir `403` al usar una `asignacion_id` ajena.
- Admin debe conservar acceso normal dentro del tenant.
- Request sin token debe responder `401`.

Nota de entorno:

- Durante las ejecuciones de PowerShell aparecieron mensajes locales de `fnm`/perfil de PowerShell por permisos en `AppData`; no afectaron las pruebas de backend.

## 2026-05-26 - Verificacion de rutas criticas ya protegidas

Se continuo la fase critica de seguridad backend y se verificaron modulos sensibles sin requerir cambios de codigo adicionales.

### Plan de clases

Archivos revisados:

- `app/routes/plan_de_clases.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/core/permissions.py`

Estado:

- `POST /plan-de-clases` ya valida `require_asignacion_access`.
- `GET /plan-de-clases/{asignacion_id}` ya valida `require_asignacion_access`.
- `DELETE /plan-de-clases/{plan_id}/imagen` ya valida `require_plan_de_clases_access`.
- Rutas admin de plan de clases ya usan `get_current_active_admin`.

Resultado:

- No se modifico codigo.
- Se valido sintaxis con `py_compile`.
- `tests/test_permissions.py` paso, pero `tests/test_uploads_permissions.py` no pudo completarse por permisos locales de pytest creando temporales en Windows.

### Asistencia

Archivos revisados:

- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`
- `app/schemas/asistencia.py`

Estado:

- `POST /asistencia` ya valida cada item con `require_asignacion_access` y `require_estudiante_in_asignacion`.
- `GET /asistencia/historial/{asignacion_id}/{periodo}` ya valida `require_asignacion_access`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py`: 14 pruebas pasaron.

### Boletines

Archivos revisados:

- `app/routes/boletines.py`
- `app/controllers/boletin_controller.py`
- `app/schemas/boletin.py`

Estado:

- `POST /boletines/guardar` ya valida `require_asignacion_access` y `require_estudiante_in_asignacion`.
- `GET /boletines/referencia/{asignacion_id}/{periodo}` ya valida `require_asignacion_access`.
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` ya exige `get_current_active_admin`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py tests/test_notas_permissions.py`: 18 pruebas pasaron.

### Dashboard

Archivos revisados:

- `app/routes/dashboard.py`
- `app/controllers/dashboard_controller.py`

Estado:

- Endpoints por `profesor_id` ya usan `require_profesor_scope`.
- Endpoints por `asignacion_id` ya usan `require_asignacion_access`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py`: 14 pruebas pasaron.

### Rutas admin-only

Archivos revisados:

- `app/routes/estudiantes.py`
- `app/routes/pagos.py`
- `app/routes/cursos.py`
- `app/routes/profesores.py`
- `app/routes/materias.py`
- `app/routes/usuario.py`
- `app/routes/reportes.py`
- `app/routes/inventario.py`
- `app/routes/tipos_pagos.py`
- `app/routes/cartera.py`
- `app/routes/nomina.py`

Estado:

- Todos los routers revisados usan `get_current_active_admin` a nivel de router.

Resultado:

- No se modifico codigo.
- `py_compile` correcto para todos los archivos revisados.

Conclusion:

- La fase de revision de ownership/admin-only queda avanzada.
- Los cambios reales de codigo hechos hoy fueron en `observaciones.py` y `planeador_anual.py`.
- Los demas modulos listados quedaron verificados como ya protegidos.

## 2026-05-26 - Configuracion base para produccion

Se avanzo en la preparacion de variables y comportamiento de sesion/CORS para despliegue.

Archivos modificados:

- `app/config.py`
- `app/main.py`
- `app/routes/auth.py`
- `.env.example`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- Se agrego `ALLOW_DEV_CORS_ORIGINS` a configuracion.
- CORS ahora incluye `localhost` y `127.0.0.1` solo si `ALLOW_DEV_CORS_ORIGINS=true`.
- `.env.example` ahora documenta `ALLOW_DEV_CORS_ORIGINS`.
- `.env.example` ahora documenta `SESSION_COOKIE_SECURE`.
- `.env.example` ahora documenta `SESSION_COOKIE_SAMESITE`.
- `POST /logout` borra la cookie `token` usando `httponly`, `secure` y `samesite` segun configuracion.

Valores recomendados para produccion:

- `ENVIRONMENT=production`
- `FRONTEND_URL=https://<dominio-frontend-real>`
- `ALLOW_DEV_CORS_ORIGINS=false`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=lax` o el valor requerido segun dominio/subdominio real.
- `SECRET_KEY` largo, aleatorio y privado.

Verificacion:

```powershell
.\venv\Scripts\python.exe -m py_compile app\config.py app\main.py app\routes\auth.py
.\venv\Scripts\python.exe -m pytest tests\test_auth_tenant.py
```

Resultado:

- `tests/test_auth_tenant.py`: 5 pruebas pasaron.

Pruebas manuales recomendadas:

- Iniciar sesion como admin y profesor.
- Revisar en DevTools que la cookie `token` sea HttpOnly.
- En entorno HTTPS/productivo, confirmar que `SESSION_COOKIE_SECURE=true` marca cookie Secure.
- Ejecutar logout y confirmar que la cookie `token` desaparece.
- Con `ALLOW_DEV_CORS_ORIGINS=false`, confirmar que solo el dominio `FRONTEND_URL` puede consumir la API.

## 2026-05-26 - Migraciones e indices verificados en tenants activos

Se aplicaron las migraciones SQL pendientes usando el runner oficial `apply_migration.py`.

Tenants activos verificados:

- `tenant_colegio_1` - Colegio Demo
- `tenant_3333` - milagro

Migraciones aplicadas en ambos tenants:

- `20260429_pagos_tipo_pago_largo.sql`
- `20260429_plan_de_clases_reportes.sql`
- `20260509_branding_plantillas_impresion.sql`
- `20260517_tipos_pagos_avanzado.sql`

Comandos ejecutados:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260429_pagos_tipo_pago_largo.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260429_plan_de_clases_reportes.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260509_branding_plantillas_impresion.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260517_tipos_pagos_avanzado.sql
```

Resultado:

- Las 4 migraciones respondieron `OK` en los 2 tenants activos.
- `public.schema_migrations` quedo con historial para las 4 migraciones por cada tenant activo.
- La verificacion posterior mostro `MIGRACIONES_TODAS_OK: True`.

Indices:

- Se verificaron los indices principales por tenant.
- La verificacion posterior mostro `INDICES_TODOS_OK: True`.

Estado del bloque de base de datos:

```text
Base de datos
[x] migraciones aplicadas en todos los tenants activos
[x] indices aplicados
[x] revisar public.schema_migrations
[ ] backup antes de salir
```

Pendiente:

- Hacer backup antes de cualquier salida real a produccion.
- Probar flujo principal de admin/profesor despues de migraciones.

## 2026-05-26 - Inicio centralizacion de cobros en tipos de pago

Se inicio la transicion para que la logica financiera dependa de `tipos_de_pagos`
y `tipos_pagos_cursos`, dejando los valores financieros de `cursos` como fallback
legacy temporal para matricula/mensualidad.

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/pagos_controller.py`
- `app/controllers/estudiante_controller.py`

Cambio:

- Se creo `app/services/cobros.py` como servicio central para:
  - cargar tipos de pago;
  - leer asignaciones por curso desde `tipos_pagos_cursos`;
  - aplicar fallback legacy de `cursos.matricula`, `cursos.mensualidad` y `cursos.meses`;
  - calcular deudas por estudiante usando `app/services/cartera.py`;
  - obtener saldo pendiente por concepto.
- `pagos_controller.py` ya no calcula saldos con una copia local de la logica de matricula/mensualidad.
- `pagos_controller.py` valida el monto del pago contra `obtener_saldo_concepto` del servicio central.
- `estudiante_controller.py` usa `calcular_deudas_estudiante` para poblar `deudas` y `total_deuda`.

Objetivo:

- Evitar logica financiera duplicada en pagos, estudiante, cartera y reportes.
- Preparar el sistema para que antes de produccion los cobros se administren desde Tipos de Pago.
- Mantener compatibilidad mientras se retiran gradualmente los campos financieros del formulario de curso.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\pagos_controller.py', r'app\controllers\estudiante_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Nota:

- `py_compile` no pudo usarse porque Windows nego permisos al escribir `__pycache__`.
- La validacion con `ast.parse` no escribe bytecode y paso correctamente.

Pruebas manuales recomendadas antes de continuar:

- Abrir detalle de un estudiante con deuda y confirmar que `deudas` y `total_deuda` se ven igual o correctamente.
- Registrar un pago parcial de un concepto configurado en Tipos de Pago.
- Intentar registrar un pago mayor al saldo pendiente: debe bloquear.
- Registrar pago de matricula/mensualidad legacy y confirmar que respeta descuento del estudiante.
- Confirmar que conceptos opcionales no generen deuda automatica.

Pendiente:

- Migrar `cartera_mora_controller.py` al servicio central sin perder eficiencia en listados grandes.
- Migrar reportes financieros al mismo servicio.
- Ajustar frontend de Crear Curso para dejar matricula/mensualidad/meses como legacy o retirarlos del flujo principal.

### Cartera vencida conectada al servicio central

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`

Cambio:

- Se agrego `calcular_deudas_desde_contexto` en `app/services/cobros.py`.
- Esta funcion permite calcular deudas usando datos ya precargados para evitar consultas repetidas por estudiante.
- `cartera_mora_controller.py` ahora usa esa funcion para calcular deuda academica, mora y cuotas vencidas.
- Se conserva la carga agrupada de estudiantes, pagos, ventas y asignaciones para mantener eficiencia en listados grandes.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\cartera_mora_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Abrir cartera vencida general.
- Confirmar que los estudiantes con deuda aparecen con total correcto.
- Filtrar cartera vencida por curso si la pantalla lo permite.
- Confirmar que deuda academica, deuda inventario, mora y total se ven coherentes.
- Confirmar que conceptos opcionales no aparecen como deuda automatica.
- Confirmar que un concepto asignado desde Tipos de Pago a un curso aparece en los estudiantes de ese curso.

Pendiente actualizado:

- Migrar reportes financieros al servicio central.
- Revisar `estado_cuenta_controller.py`, que todavia calcula deuda usando directamente `cursos.matricula`, `cursos.mensualidad` y `cursos.meses`.
- Ajustar frontend de Crear Curso para dejar los campos financieros como legacy/fallback.

### Reporte de estado de cuenta por curso conectado al servicio central

Archivo modificado:

- `app/controllers/reportes_controller.py`

Cambio:

- `reporte_estado_cuenta_curso_controller` ahora usa:
  - `obtener_tipos_pago`;
  - `obtener_asignaciones_cobro_por_curso`;
  - `calcular_deudas_desde_contexto`.
- Se elimino de ese reporte la logica repetida que detectaba manualmente conceptos legacy y calculaba deuda por matricula/mensualidad.
- Se conserva compatibilidad con pagos por `concepto_id`, `tipo_pago` y el formato actual de respuesta.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\reportes_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Abrir el reporte de estado de cuenta por curso.
- Confirmar que cada estudiante conserva `pagado`, `total`, `deuda` y `deudas_detalle`.
- Confirmar que conceptos asignados desde Tipos de Pago aparecen en el curso correcto.
- Confirmar que matricula/mensualidad legacy siguen funcionando como fallback.
- Registrar un pago y volver a abrir el reporte para verificar que baja la deuda.

Pendiente actualizado:

- Revisar `estado_cuenta_controller.py`, que todavia contiene consultas directas antiguas.
- Ajustar frontend de Crear Curso para que cobros queden en Tipos de Pago y los campos financieros del curso dejen de ser el flujo principal.

### Estado de cuenta conectado al servicio central

Archivo modificado:

- `app/controllers/estado_cuenta_controller.py`

Cambio:

- `estado_cuenta_curso_controller` ya no calcula deuda con la formula fija:
  `cursos.matricula + cursos.mensualidad * cursos.meses`.
- `estado_cuenta_estudiante_controller` tambien usa el servicio central.
- Ambos controladores llaman `calcular_deudas_estudiante`.
- Se conserva el formato de respuesta:
  - `id`;
  - `nombre`;
  - `apellido`;
  - `pagado`;
  - `total`;
  - `deuda`;
  - `tipos_pagos`.

Motivo:

- Hacer que estado de cuenta respete conceptos configurados desde Tipos de Pago.
- Mantener los campos financieros de curso solo como fallback legacy.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\controllers\estado_cuenta_controller.py', r'app\services\cobros.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.
- No queda la formula directa de `cursos.matricula`, `cursos.mensualidad` y `cursos.meses` en `estado_cuenta_controller.py`.

Pruebas manuales recomendadas:

- Abrir estado de cuenta por curso.
- Abrir estado de cuenta de un estudiante.
- Confirmar que los conceptos de Tipos de Pago afectan deuda/total.
- Confirmar que un pago registrado reduce la deuda.
- Confirmar que matricula/mensualidad legacy siguen funcionando como fallback mientras se ajusta Crear Curso.

### Ajuste de fallback para conceptos asignados con valor 0

Archivo modificado:

- `app/services/cobros.py`

Cambio:

- Si un tipo de pago esta asignado a un curso en `tipos_pagos_cursos` con valor `0`, ya no se toma ese `0` como deuda final automaticamente.
- Nueva regla:
  - si el valor asignado al curso es mayor que `0`, se usa ese valor;
  - si el valor asignado es `0`, se usa el valor global de `tipos_de_pagos`;
  - si tambien es `0` y el concepto es matricula/mensualidad legacy, se usa el valor del curso como fallback.

Motivo:

- Evitar que una asignacion en cero bloquee pagos de matricula o mensualidad.
- Mantener Tipos de Pago como fuente principal sin romper colegios que todavia usan valores financieros en Crear Curso.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; ast.parse(pathlib.Path(r'app\services\cobros.py').read_text(encoding='utf-8')); print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Revisar un curso con `matricula` configurada en Crear Curso.
- En Tipos de Pago, confirmar que el concepto Matricula exista y este activo.
- Si Matricula esta asignada al curso con valor `0`, intentar registrar el pago.
- Debe tomar el valor global del tipo de pago o, si es `0`, el valor de matricula del curso.

## 2026-05-26 - Curso queda solo academico y Tipos de Pago queda como fuente unica de deuda

Se cerro la transicion financiera para que los cobros academicos dependan de
`tipos_de_pagos` y `tipos_pagos_cursos`, no de columnas financieras en `cursos`.

Archivos modificados:

- `app/schemas/curso.py`
- `app/controllers/curso_controller.py`
- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/reportes_controller.py`
- `crear_cliente.py`
- `migrations/20260526_cursos_solo_academicos.sql`

Cambios:

- `CursoCreate` ya no exige:
  - `matricula`;
  - `mensualidad`;
  - `meses`.
- `crear_curso_controller` solo inserta:
  - `nombre`;
  - `jornada`.
- `actualizar_curso_controller` solo actualiza:
  - `nombre`;
  - `jornada`.
- Los listados de cursos ya no retornan campos financieros.
- `app/services/cobros.py` ya no usa fallback legacy contra `cursos.matricula`, `cursos.mensualidad` ni `cursos.meses`.
- `cartera_mora_controller.py` y `reportes_controller.py` ya no seleccionan ni pasan esos campos al servicio de cobros.
- `crear_cliente.py` se actualizo para que el SQL base de `cursos` no incluya columnas financieras.

Migracion aplicada:

- `migrations/20260526_cursos_solo_academicos.sql`

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260526_cursos_solo_academicos.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.
- Verificacion posterior:
  - `tenant_colegio_1`: cursos sin columnas financieras.
  - `tenant_3333`: cursos sin columnas financieras.

Estado nuevo:

```text
Tipos de Pago = fuente unica de deuda academica
Curso = entidad academica
```

Pruebas manuales recomendadas:

- Crear curso nuevo.
- Editar curso existente.
- Crear/asignar un tipo de pago al curso.
- Ver cartera vencida.
- Ver detalle del estudiante.
- Registrar pago de un concepto asignado.
- Confirmar que si un tipo de pago no esta asignado al curso, no genera deuda.

## 2026-05-26 - Nomina expone sueldo del profesor

Se ajusto la consulta de empleados de nomina para devolver el sueldo asignado al
profesor.

Archivo modificado:

- `app/controllers/nomina_controller.py`

Cambio:

- `obtener_estado_cuenta_profesores()` ahora selecciona `COALESCE(p.sueldo, 0) AS sueldo`.
- La respuesta de `/api/nomina/empleados` incluye:
  - `sueldo`;
  - `saldo_prestamos`.

Motivo:

- Permitir que el frontend precargue el campo `Salario Base` en el modal de pago
  de nomina con el sueldo real configurado en el profesor.

Verificacion:

- Sintaxis de `app/controllers/nomina_controller.py`: OK.

Pruebas manuales recomendadas:

- Crear o editar un profesor con sueldo.
- Consultar nomina desde Admin.
- Abrir `Realizar Pago`.
- Confirmar que el salario base coincide con el sueldo del profesor.

## 2026-05-26 - Mensaje claro para tipos de pago duplicados

Se ajusto la creacion/edicion de tipos de pago para devolver una causa clara
cuando el nombre ya existe.

Archivos modificados:

- `app/controllers/tipos_pagos_controller.py`
- `app/routes/tipos_pagos.py`

Cambio:

- Se agrego `TipoPagoDuplicadoError`.
- Antes de crear un tipo de pago se valida si ya existe otro con el mismo nombre,
  ignorando mayusculas/minusculas y espacios al inicio/final.
- Antes de editar un tipo de pago se valida que el nuevo nombre no exista en otro
  registro.
- La API responde `409 Conflict` con un mensaje legible cuando hay duplicado.

Motivo:

- Evitar que el frontend muestre un error generico de servidor cuando el problema
  real es que el concepto ya existe.

Verificacion:

- Sintaxis de `app/controllers/tipos_pagos_controller.py` y `app/routes/tipos_pagos.py`: OK.

Pruebas manuales recomendadas:

- Crear un tipo de pago con un nombre existente.
- Confirmar que responde una alerta de concepto duplicado.
- Editar un tipo de pago y ponerle el nombre de otro existente.
- Confirmar que tambien se bloquea con mensaje claro.

## 2026-05-26 - Normalizacion de nombres academicos en backend

Se agrego normalizacion en backend para guardar nombres con iniciales en
mayuscula en entidades academicas y profesores.

Archivos modificados:

- `app/controllers/profesor_controller.py`
- `app/controllers/curso_controller.py`
- `app/controllers/materia_controller.py`

Cambio:

- Al crear o editar profesor:
  - `nombre` se guarda en formato titulo;
  - `apellido` se guarda en formato titulo;
  - `email` se guarda en minusculas.
- Al crear o editar curso:
  - `nombre` se guarda en formato titulo.
- Al crear o editar materia:
  - `nombre` se guarda en formato titulo.

Motivo:

- Mantener datos consistentes aunque se envie informacion directa por API.
- Evitar listados, boletines, reportes e impresos con nombres en minusculas o
  mayusculas mezcladas.

Verificacion:

- Sintaxis de controladores de profesor, curso y materia: OK.

Pruebas manuales recomendadas:

- Crear profesor con nombre/apellido en minusculas.
- Crear curso con nombre en minusculas.
- Crear materia con nombre en minusculas.
- Confirmar que se listan con iniciales en mayuscula.

## 2026-05-27 - Anulacion auditada de pagos

Se implemento anulacion de pagos sin eliminacion fisica, empezando desde el
historial de pagos del estudiante.

Archivos modificados:

- `migrations/20260527_pagos_anulacion.sql`
- `app/schemas/pago.py`
- `app/controllers/pagos_controller.py`
- `app/routes/pagos.py`
- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/estado_cuenta_controller.py`
- `app/controllers/reportes_controller.py`
- `crear_cliente.py`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agregaron columnas a `pagos`:
  - `estado`;
  - `motivo_anulacion`;
  - `fecha_anulacion`;
  - `anulado_por`.
- Se agrego endpoint admin:
  - `POST /pagos/{pago_id}/anular`
- La anulacion exige motivo.
- Los pagos anulados quedan visibles en historial y reportes.
- Cartera, estado de cuenta y calculo de deudas ignoran pagos con `estado = 'Anulado'`.
- Reportes de ingresos mensuales/rango incluyen la huella del pago anulado, pero
  lo devuelven con `monto_valido = 0`.
- Totales generales e ingresos mensuales suman solo pagos validos.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_pagos_anulacion.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Registrar un pago academico.
- Anularlo desde historial de pagos del estudiante con motivo.
- Confirmar que aparece marcado como `Anulado`.
- Confirmar que la deuda vuelve a subir.
- Abrir Reportes > Ingresos Mensuales.
- Confirmar que el pago anulado aparece como huella, pero no suma al total valido.

### Anulacion segura de pagos de inventario

Se amplio la anulacion para cubrir pagos asociados a ventas de inventario.

Archivos modificados:

- `migrations/20260527_pagos_venta_id.sql`
- `app/controllers/pagos_controller.py`
- `crear_cliente.py`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agrego `pagos.venta_id`.
- Al registrar un pago de inventario, se guarda el `venta_id`.
- Al anular un pago con `venta_id`, se resta el monto anulado de `ventas.pagado`.
- Si despues de la anulacion la venta vuelve a tener saldo pendiente, `ventas.estado`
  queda en `Pendiente`.
- Para pagos antiguos sin `venta_id`, el backend intenta inferirlo desde la
  descripcion con formato `Cargo #ID`.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_pagos_venta_id.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Crear una venta de inventario a credito.
- Registrar un abono desde pagos del estudiante.
- Confirmar que la venta aumenta `pagado`.
- Anular ese pago desde historial.
- Confirmar que el pago queda anulado.
- Confirmar que la venta vuelve a `Pendiente` y el saldo vuelve a aparecer.

## 2026-05-27 - Anulacion de ventas de inventario

Se agrego anulacion transaccional de ventas de inventario.

Archivos modificados:

- `migrations/20260527_ventas_anulacion.sql`
- `app/controllers/venta_controller.py`
- `app/routes/ventas.py`
- `docs/API_ENDPOINTS.md`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agregaron columnas a `ventas`:
  - `motivo_anulacion`;
  - `fecha_anulacion`;
  - `anulado_por`.
- Se agrego endpoint admin:
  - `POST /api/ventas/{venta_id}/anular`
- Al anular una venta:
  - la venta queda con `estado = 'Anulada'`;
  - se devuelve el stock de cada item al inventario;
  - se anulan pagos asociados por `venta_id`;
  - se intenta cubrir pagos antiguos asociados por descripcion `Cargo #ID`;
  - `ventas.pagado` vuelve a `0`.

Motivo:

- Evitar eliminacion fisica de ventas.
- Mantener trazabilidad financiera y de inventario.
- Evitar que cartera siga cobrando cargos anulados.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_ventas_anulacion.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Crear una venta/cargo de inventario.
- Confirmar que baja el stock.
- Anular la venta desde el listado de cargos recientes.
- Confirmar que la venta queda `Anulada`.
- Confirmar que el stock vuelve.
- Si tenia pagos asociados, confirmar que quedan anulados y no suman en reportes.

## 2026-05-27 - Ingresos Hoy usa fecha local Colombia

Se ajusto el calculo de `ingresos_hoy` del reporte general para comparar contra
la fecha local de Colombia.

Archivo modificado:

- `app/controllers/reportes_controller.py`

Cambio:

- Antes usaba `CURRENT_DATE` de PostgreSQL.
- Ahora usa `(NOW() AT TIME ZONE 'America/Bogota')::date`.
- Se mantiene la regla de no sumar pagos con `estado = 'Anulado'`.

Motivo:

- Evitar que Neon/PostgreSQL calcule "hoy" con una zona horaria distinta a la
  fecha local con la que se registran los pagos.

Pruebas manuales recomendadas:

- Registrar un pago con fecha de hoy.
- Abrir Admin > Reportes y Estadisticas.
- Confirmar que `Ingresos Hoy` suma el pago.
- Anular ese pago y confirmar que `Ingresos Hoy` deja de sumarlo.

## 2026-05-27 - Bloqueo de eliminacion fisica de ventas

Se bloqueo el endpoint legacy de eliminacion fisica de ventas.

Archivo modificado:

- `app/routes/ventas.py`

Cambio:

- `DELETE /api/ventas/{venta_id}` ya no elimina la venta.
- Ahora responde `405` con mensaje indicando usar:
  - `POST /api/ventas/{venta_id}/anular`

Motivo:

- Evitar perdida de trazabilidad financiera e inventario.
- Forzar el flujo seguro de anulacion con motivo, devolucion de stock y anulacion
  de pagos asociados.

Pruebas manuales recomendadas:

- Intentar llamar `DELETE /api/ventas/{venta_id}`.
- Confirmar que responde bloqueado.
- Anular una venta desde el frontend y confirmar que usa el endpoint de anulacion.

## 2026-05-27 - Pruebas de anulaciones financieras

Se agregaron pruebas unitarias para blindar los flujos de anulacion financiera.

Archivo agregado:

- `tests/test_anulaciones_financieras.py`

Casos cubiertos:

- Anular pago academico sin tocar ventas.
- Anular pago de inventario descontando el abono de la venta asociada.
- Anular venta con devolucion de stock.
- Anular venta dejando pagos asociados en estado `Anulado`.
- Reporte general excluyendo pagos anulados de ingresos y de ingresos de hoy.
- Formato de ingresos marcando `monto_valido = 0` cuando el pago esta anulado.

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q tests\test_anulaciones_financieras.py -p no:cacheprovider
```

Resultado:

- 5 pruebas pasaron correctamente.

Motivo:

- Evitar regresiones en anulaciones de pagos academicos, pagos de inventario,
  ventas, reportes y devolucion de stock antes de produccion.

## 2026-05-28 - Soporte Cloudflare R2 para uploads

Se agrego una capa de almacenamiento para que logos e imagenes del plan diario puedan guardarse en Cloudflare R2 sin romper las URLs actuales.

Archivos modificados/agregados:

- `app/services/storage.py`
- `app/config.py`
- `app/main.py`
- `app/controllers/branding_controller.py`
- `app/controllers/plan_de_clases_controller.py`
- `.env.example`
- `requirements.txt`
- `docs/PRODUCCION_BACKEND.md`
- `docs/SEGURIDAD.md`

Cambio:

- `STORAGE_PROVIDER=local` mantiene `uploads/` local.
- `STORAGE_PROVIDER=r2` usa Cloudflare R2 compatible con S3.
- `/uploads/...` sigue siendo el endpoint de lectura protegido.
- Se agrego dependencia `boto3`.

Comandos ejecutados:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\config.py app\services\storage.py app\controllers\plan_de_clases_controller.py app\controllers\branding_controller.py app\main.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_uploads_permissions.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- Pruebas de permisos de uploads: 6 pasaron.

Pendiente para activar R2 real:

- Crear bucket en Cloudflare R2.
- Crear Access Key/Secret con permiso sobre el bucket.
- Configurar variables R2 en produccion.
- Reiniciar backend.
- Probar subida/visualizacion/eliminacion de logo y plan diario.
