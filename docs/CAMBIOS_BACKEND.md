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


