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

Pendiente:
- Mover a `scripts/legacy/` o eliminar.
- Agregar advertencia de no usar en produccion.

Riesgo:
- Guarda password en texto plano (`admin123`) si alguien lo ejecuta.

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
- Eliminarlo si ya no se usa, o moverlo a `scripts/legacy/`.
- Agregar advertencia clara: "No usar en produccion".
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

### 4. Migraciones

Estado actual:
- Existen scripts sueltos y una carpeta `migrations`, pero Alembic no esta
  inicializado como fuente formal de verdad.

Accion recomendada:
- Inicializar Alembic, o consolidar un runner propio de migraciones por tenant.
- Registrar historial de migraciones aplicadas.
- Distinguir entre:
  - cambios globales en `public`;
  - cambios repetidos en schemas `tenant_*`;
  - indices y constraints por tenant.

Riesgo si no se hace:
- Un tenant nuevo puede quedar con tablas o columnas distintas.
- Un cambio aplicado manualmente puede no llegar a todos los colegios.

### 5. Indices y revision con `EXPLAIN ANALYZE`

Accion recomendada:
- Aplicar indices por tenant para consultas frecuentes.
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

### 6. Paginacion

Problema:
- Varios endpoints devuelven listas completas. Esto funciona con pocos datos,
  pero puede afectar memoria, tiempos de respuesta y experiencia de usuario.

Empezar por:
- `GET /estudiantes`
- ventas
- pagos por estudiante
- reportes de ingresos por rango
- inventario
- asignaciones/listados administrativos

Accion recomendada:
- Agregar `limit` y `offset` con limites maximos razonables.
- Mantener compatibilidad con el frontend actual mientras se migra pantalla por pantalla.

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