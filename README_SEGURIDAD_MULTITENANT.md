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

## Verificaciones realizadas

- Validacion de sintaxis con `ast.parse` en los archivos Python modificados.
- Build de frontend con `pnpm run build` despues de corregir el horario del profesor.
- El build de frontend termino correctamente.

## Pendientes importantes

### 1. Revalidar usuario activo y rol contra DB

Archivo principal:
- `app/dependencies.py`

Pendiente:
- `get_current_user` hoy decodifica JWT y confia en `id`, `rol` y `tenant`.
- Falta consultar la base del tenant para confirmar que el usuario/profesor sigue existiendo y esta activo.

Riesgo:
- Si un usuario cambia de rol, se elimina o se desactiva, un token viejo podria seguir funcionando hasta expirar.

### 2. Proteger `/uploads`

Archivo principal:
- `app/main.py`

Estado actual:
- Sigue activo:
  - `app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")`

Pendiente:
- Reemplazar acceso publico por endpoints autenticados.
- Validar tenant y permisos antes de servir imagenes/documentos.
- Sanitizar nombres de archivos en `plan_de_clases_controller.py`.

Riesgo:
- Archivos subidos pueden quedar accesibles por URL si alguien la conoce o la adivina.

### 3. Revisar boletines por estudiante

Archivos:
- `app/routes/boletines.py`
- `app/routes/notas.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/notas_controller.py`

Pendiente:
- Endpoints por `estudiante_id` deben validar que el profesor tenga relacion real con ese estudiante mediante curso/asignacion.
- Rutas admin de generacion de boletin deben ser admin-only.

Riesgo:
- Profesor podria consultar boletines o notas de estudiantes que no le corresponden si cambia el ID.

### 4. Revisar asistencia

Archivo:
- `app/routes/asistencia.py`

Pendiente:
- Validar que el profesor solo registre/consulte asistencia de sus asignaciones.

Riesgo:
- Profesor podria registrar asistencia en una clase ajena.

### 5. Revisar estudiantes, pagos, cuentas y cartera

Archivos:
- `app/routes/estudiantes.py`
- `app/routes/pagos.py`
- `app/routes/cuentas.py`
- `app/routes/cartera.py`

Pendiente:
- Decidir que es admin-only y que puede leer un profesor.
- Para lectura de profesor, validar curso/asignacion/estudiante.

Riesgo:
- Acceso a datos personales o financieros de estudiantes fuera del alcance del usuario.

### 6. Revisar cursos, materias y profesores

Archivos:
- `app/routes/cursos.py`
- `app/routes/materias.py`
- `app/routes/profesores.py`

Pendiente:
- Separar operaciones admin de lecturas necesarias para formularios.
- Crear rutas de lectura seguras si profesor necesita catalogos.

Riesgo:
- Profesor podria crear, modificar o borrar estructura academica si esas rutas siguen abiertas.

### 7. Revisar scripts antiguos

Archivo:
- `insert_admin.sql`

Pendiente:
- Mover a `scripts/legacy/` o eliminar.
- Agregar advertencia de no usar en produccion.

Riesgo:
- Guarda password en texto plano (`admin123`) si alguien lo ejecuta.

### 8. Provisionamiento de tenants

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

1. Revalidar usuario activo/rol contra DB en `get_current_user`.
2. Revisar `boletines` y endpoints por `estudiante_id`.
3. Revisar `asistencia`.
4. Definir modelo de acceso para `estudiantes`, `pagos`, `cuentas` y `cartera`.
5. Proteger `/uploads` con endpoints autenticados.

