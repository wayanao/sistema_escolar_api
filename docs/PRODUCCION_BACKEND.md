# Produccion Backend

Ultima revision documental: 2026-06-13.

## Variables de entorno actuales

Definidas en `app/config.py` y `.env.example`:

- `APP_NAME`
- `ENVIRONMENT`
- `LOG_LEVEL`
- `DATABASE_URL`
- `DB_POOL_MIN_CONNECTIONS`
- `DB_POOL_MAX_CONNECTIONS`
- `DEFAULT_TENANT_SCHEMA`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `FRONTEND_URL`
- `ALLOW_DEV_CORS_ORIGINS`
- `SESSION_COOKIE_SECURE`
- `SESSION_COOKIE_SAMESITE`
- `STORAGE_PROVIDER`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT_URL`
- `R2_REGION`

`.env.example` contiene:

- `APP_NAME`
- `ENVIRONMENT`
- `LOG_LEVEL`
- `DATABASE_URL`
- `DB_POOL_MIN_CONNECTIONS`
- `DB_POOL_MAX_CONNECTIONS`
- `DEFAULT_TENANT_SCHEMA`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `FRONTEND_URL`
- `ALLOW_DEV_CORS_ORIGINS`
- `SESSION_COOKIE_SECURE`
- `SESSION_COOKIE_SAMESITE`
- `STORAGE_PROVIDER`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT_URL`
- `R2_REGION`

## Configuracion de app

Archivo:

- `app/config.py`

Carga `.env` desde:

- raiz del backend `sistema_escolar_api/.env`;
- raiz padre del proyecto.

Ignora variables extra:

- `extra="ignore"`

## Servidor

Dependencias:

- `fastapi`
- `uvicorn[standard]`

Comando sugerido en Render:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Si se usan varios workers o replicas, ajustar `DB_POOL_MAX_CONNECTIONS` con el
limite real de PostgreSQL/Neon. El maximo total aproximado es:

```text
workers * replicas * DB_POOL_MAX_CONNECTIONS
```

## Base de datos

Produccion requiere configurar:

- `DATABASE_URL`
- pool minimo/maximo
- estados de tenants en `public.colegios.estado`
- migraciones/indices aplicados a schemas activos

Estados SaaS iniciales:

- `activo`: login y uso normal.
- `en_mora`: login y uso permitidos; se expone aviso por `GET /tenant/status`.
- `suspendido`: login y peticiones autenticadas bloqueadas.
- `cancelado`: login y peticiones autenticadas bloqueadas.

Los scripts operativos de migraciones, verificacion de schemas e indices deben
considerar como tenants operativos a `activo` y `en_mora`.

## Pool de conexiones en Render/Neon

Archivo central:

- `app/db/session.py`

Variables:

- `DB_POOL_MIN_CONNECTIONS`
- `DB_POOL_MAX_CONNECTIONS`

Reglas:

- Cada request que use `get_connection()` debe cerrar cursor y conexion en
  `finally`.
- Para codigo nuevo, preferir `get_cursor()` porque cierra automaticamente.
- `PooledConnection.close()` devuelve la conexion al pool.
- `close_pool()` se ejecuta al apagar la app desde el `lifespan` de FastAPI.

Incidente documentado en produccion:

- Render reporto `psycopg2.pool.PoolError: connection pool exhausted`.
- El efecto visible fue bloqueo de login porque no habia conexiones libres.
- Se reviso `app/controllers/auth_controller.py` para cerrar conexiones del
  flujo de login, incluyendo el rehash de password legacy.

Respuesta operativa si vuelve a ocurrir:

1. Reiniciar/redeployar el servicio para liberar el pool actual.
2. Revisar logs y ultima ruta usada antes del error.
3. Auditar los `get_connection()` tocados recientemente y exigir `finally`.
4. Confirmar que `DB_POOL_MAX_CONNECTIONS` no exceda el limite del plan de DB
   al multiplicarlo por workers/replicas.
5. Revisar endpoints de alto uso: login, dashboard, asistencia, planilla,
   reportes y cartera.

## Super admin de plataforma

El rol `super_admin` vive en `public.super_admins` y entra por el mismo
`POST /login` usando codigo de colegio `super_admin`.

Preparacion inicial:

```powershell
.\venv\Scripts\python.exe scripts\create_super_admin.py --nombre "David" --email "tu-correo@dominio.com" --password "password-seguro"
```

El script crea/verifica `public.super_admins`, guarda la password hasheada y
deja el usuario en estado `activo`.

## CORS

`app/main.py` permite:

- `settings.FRONTEND_URL`
- localhost y 127.0.0.1 en puerto 5173 solo si `ALLOW_DEV_CORS_ORIGINS=true`

Para produccion se recomienda:

- `FRONTEND_URL=https://<dominio-frontend-real>`
- `ALLOW_DEV_CORS_ORIGINS=false`

## Cookies

`SESSION_COOKIE_SECURE` existe en configuracion.

Login usa cookie:

- `httponly=True`
- `secure=settings.SESSION_COOKIE_SECURE`
- `samesite=settings.SESSION_COOKIE_SAMESITE`
- `max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60`

La respuesta de login no devuelve `access_token` ni `token_type`; el JSON queda
limitado a datos minimos de sesion para la UI.

La duracion por defecto de la sesion es `ACCESS_TOKEN_EXPIRE_MINUTES=120`
minutos. Si la plataforma define esta variable en el entorno, ese valor externo
tiene prioridad sobre el default del codigo.

Configuracion productiva recomendada:

- Con HTTPS: `SESSION_COOKIE_SECURE=true`.
- Si frontend y backend estan bajo el mismo sitio registrable, mantener
  `SESSION_COOKIE_SAMESITE=lax` suele ser suficiente.
- Si frontend y backend estan en sitios distintos, por ejemplo un dominio de
  frontend y otro de Render, probar `SESSION_COOKIE_SAMESITE=none` junto con
  `SESSION_COOKIE_SECURE=true`.

Sintoma relacionado:

- Si el navegador no acepta o no envia la cookie `token`, el usuario entra y la
  sesion parece cerrarse enseguida, especialmente en navegadores moviles mas
  estrictos.

## Logs

`app/main.py` llama:

- `configure_logging()`

Archivo:

- `app/core/logging.py`

## Checks existentes

Pruebas disponibles en `tests/`:

- auth/tenant
- permisos
- uploads
- paginacion
- migraciones
- indices por tenant

Scripts operativos:

- `apply_migration.py`
- `scripts/apply_tenant_indexes.py`
- `scripts/check_tenant_schemas.py`
- `/super-admin` para crear colegios
- `scripts/legacy/crear_cliente.py` y `scripts/legacy/setup_saas.py` solo como referencia historica

## Checklist post-deploy

- Abrir backend y confirmar que no hay errores de arranque.
- Probar `POST /login` desde el dominio real del frontend.
- Revisar en navegador que la cookie `token` queda `HttpOnly`, con `Secure`
  segun entorno y `SameSite` esperado.
- Probar una request autenticada sin header Bearer, usando solo cookie.
- Probar `/tenant/status` con tenant `activo` y `en_mora`.
- Probar `/uploads/...` autenticado si se usan logos o imagenes de plan diario.
- Revisar logs de Render durante login, dashboard profesor, asistencia,
  planilla y reportes.
- Confirmar que no aparece `connection pool exhausted`.

## Estado 2026-05-26

- `.env.example` ya documenta `ALLOW_DEV_CORS_ORIGINS`.
- `.env.example` ya documenta `SESSION_COOKIE_SECURE`.
- `.env.example` ya documenta `SESSION_COOKIE_SAMESITE`.
- `logout` elimina la cookie `token` usando los mismos atributos de seguridad configurados.
- CORS permite desactivar origins locales en produccion con `ALLOW_DEV_CORS_ORIGINS=false`.

## Riesgos pendientes documentados

- Falta configurar valores reales de produccion en el entorno de despliegue.
- CORS conserva origins localhost si `ALLOW_DEV_CORS_ORIGINS=true`.
- No se observo configuracion Alembic activa.
- La preparacion de produccion depende de ejecutar migraciones, indices y verificacion de tenants.
- El pool puede agotarse si alguna ruta abre conexion y no la cierra.
- Cookies cross-site mal configuradas pueden cerrar sesion en movil aunque en
  PC parezca funcionar.

## Cloudflare R2 para uploads

El backend soporta almacenamiento local y Cloudflare R2/S3 compatible para archivos subidos.

Archivos relacionados:

- `app/services/storage.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/controllers/branding_controller.py`
- `app/main.py`

Variables de entorno:

```env
STORAGE_PROVIDER=r2
R2_ACCOUNT_ID=<account-id-cloudflare>
R2_ACCESS_KEY_ID=<access-key-r2>
R2_SECRET_ACCESS_KEY=<secret-key-r2>
R2_BUCKET=<bucket-r2>
R2_ENDPOINT_URL=
R2_REGION=auto
```

Notas:

- `STORAGE_PROVIDER=local` mantiene el comportamiento anterior con carpeta `uploads/`.
- `STORAGE_PROVIDER=r2` guarda logos e imagenes de plan diario en Cloudflare R2.
- Las URLs publicas de la app no cambian: siguen entrando por `/uploads/...`.
- El backend sigue validando autenticacion, tenant y ownership antes de entregar archivos.
- La base de datos guarda rutas tipo `uploads/<tenant>/plan_de_clases/<archivo>` o `/uploads/branding/<tenant>/<archivo>`.
- R2 guarda el objeto con key sin el prefijo inicial `/uploads/`, por ejemplo `tenant_3333/plan_de_clases/archivo.png`.
- Las pruebas unitarias de permisos de uploads no deben depender del bucket real
  ni del `.env` productivo. En `tests/test_uploads_permissions.py` se simula
  storage local con `monkeypatch` para validar permisos usando archivos
  temporales.

Prueba recomendada en produccion:

1. Configurar las variables R2.
2. Reiniciar backend.
3. Subir logo desde Admin.
4. Confirmar que aparece en R2 dentro de `branding/<tenant>/`.
5. Subir imagen en plan diario.
6. Confirmar que aparece en R2 dentro de `<tenant>/plan_de_clases/`.
7. Entrar con otro tenant y confirmar que no puede abrir esa URL.
8. Eliminar una imagen/logo y confirmar que se borra del registro y del bucket.

## Pendientes antes de seguir

Super admin:

- Resetear la password real del super admin antes de usarlo en serio.
- Reiniciar el backend para cargar los cambios nuevos.
- Probar login manual usando codigo `super_admin`.
- Validar manualmente `/super-admin` con un tenant de prueba.
- Crear un colegio desde `/super-admin` con admin inicial y suscripcion.
- Confirmar que el admin inicial puede entrar usando el codigo del colegio.

SaaS/cobro:

- Mantener esta regla operativa:
  - `activo`: pago al dia;
  - `en_mora`: pago vencido, acceso permitido con aviso;
  - `suspendido`: bloqueo temporal por no pago;
  - `cancelado`: cliente retirado/contrato terminado.
- Auditoria y motivo al cambio de estado: completado; se registra en
  `public.tenant_estado_auditoria`.
- Pendiente agregar canales de pago configurables para el aviso de mora.

Creacion de colegios:

- `POST /super-admin/tenants` crea el registro en `public.colegios`.
- Crea el schema `tenant_<codigo>`.
- Copia tablas desde `DEFAULT_TENANT_SCHEMA`.
- Crea identidad institucional y plantillas iniciales.
- Crea el admin inicial dentro del schema del colegio.
- Crea `public.tenant_suscripciones` con fecha de inicio, proximo pago y dias
  de gracia.

Calculo efectivo por suscripcion:

- El backend considera `public.tenant_suscripciones` al resolver estado de
  tenant para login y sesiones.
- Si `fecha_proximo_pago` ya paso y todavia esta dentro de `dias_gracia`, el
  estado efectivo es `en_mora`.
- Si `fecha_proximo_pago + dias_gracia` ya paso, el estado efectivo es
  `suspendido`.
- Estados manuales `suspendido` y `cancelado` siguen bloqueando sin importar la
  fecha.

Auditoria de estado:

- Los cambios de estado de tenant quedan registrados en
  `public.tenant_estado_auditoria`.
- Se guarda tenant, estado anterior, estado nuevo, motivo, super admin y fecha.
- El endpoint `GET /super-admin/tenants/{tenant_id}/estado-auditoria` expone
  los ultimos 50 cambios para consulta desde el panel.

Passwords:

- El admin inicial creado desde super admin queda con
  `debe_cambiar_password = TRUE`.
- El primer ingreso usa la password temporal y despues llama
  `POST /auth/cambiar-password`.
- La nueva password debe tener minimo 10 caracteres, una mayuscula, una
  minuscula y un numero.
- Sigue pendiente recuperacion de password por correo para admin, profesor y
  super admin.

Migraciones antes de deploy:

- Ejecutar migraciones publicas antes de arrancar backend:
  - `migrations/public/20260530_super_admins.sql`
  - `migrations/public/20260601_tenant_estado_auditoria.sql`
  - `migrations/public/20260601_tenant_suscripciones.sql`
  - `migrations/public/20260601_tenant_eventos_auditoria.sql`
- Ejecutar migraciones tenant/template antes de crear colegios:
  - `migrations/20260601_usuarios_password_obligatorio.sql`
  - `migrations/20260602_asignaciones_activo.sql`
  - `migrations/20260604_profesor_estado.sql`
  - `migrations/20260604_cursos_estado.sql`
  - `migrations/20260604_materias_estado.sql`
  - `migrations/20260604_inventario_estado.sql`
  - `migrations/20260604_egresos_origen.sql`
- Las consultas normales ya no crean `public.tenant_suscripciones`; si falta la
  migracion, el deploy debe corregirse antes de usar el sistema.

Asignaciones de clases:

- El asignador administrativo usa una sola vista tipo formulario.
- El admin selecciona primero el curso y luego profesor, materia, dia, hora de
  inicio y hora de fin.
- La disponibilidad del profesor es una guia calculada desde asignaciones
  activas en los rangos `06:30-12:30` y `12:30-18:30`.
- El backend valida conflictos de profesor, conflictos de curso, horas
  invalidas y jornada del curso antes de guardar.
- Desactivar una asignacion no borra planes de clase, notas, asistencia,
  boletines ni observaciones historicas.

Estados operativos de estudiantes, profesores, cursos, materias e inventario:

- Estudiantes usan `estado`: `activo`, `retirado`, `egresado`, `inactivo`.
- Profesores usan `estado`: `activo`, `inactivo`.
- Cursos usan `estado`: `activo`, `inactivo`.
- Materias usan `estado`: `activo`, `inactivo`.
- Productos de inventario usan `estado`: `activo`, `inactivo`.
- `GET /estudiantes`, `GET /profesores`, `GET /cursos`, `GET /materias` y
  `GET /inventario` devuelven activos por defecto.
- Para revision administrativa/historica se usa `estado=todos`.
- No se hace borrado fisico desde estos flujos; el cambio de estado conserva
  historial academico, pagos, notas, asistencia, boletines y observaciones.
- Profesores `inactivo` no pueden iniciar sesion ni ser usados en nuevas
  asignaciones o ediciones de asignacion.
- Cursos `inactivo` no pueden ser usados en nuevas asignaciones o ediciones de
  asignacion, y quedan fuera de vistas operativas de clases/horarios.
- Materias `inactivo` no pueden ser usadas en nuevas asignaciones o ediciones
  de asignacion, y quedan fuera de vistas operativas de clases/horarios.
- Productos de inventario `inactivo` no aparecen para nuevas ventas y el
  backend rechaza intentos de venderlos por API.
- `DELETE /inventario/{item_id}` desactiva el producto; no borra ventas ni
  detalles historicos.
- Estudiantes que no estan `activo` quedan fuera de planilla diaria, asistencia
  y boletines del flujo del profesor.
- La migracion `migrations/20260604_profesor_estado.sql` agrega
  `profesor.estado`, normaliza registros existentes a `activo` y crea indice
  por estado.
- La migracion `migrations/20260604_cursos_estado.sql` agrega `cursos.estado`,
  normaliza registros existentes a `activo` y crea indice por estado.
- La migracion `migrations/20260604_materias_estado.sql` agrega
  `materias.estado`, normaliza registros existentes a `activo` y crea indice
  por estado.
- La migracion `migrations/20260604_inventario_estado.sql` agrega
  `inventario.estado`, normaliza registros existentes a `activo` y crea indice
  por estado.
- La migracion `migrations/20260604_egresos_origen.sql` agrega
  `egresos.origen`, marca egresos de nomina como `nomina`, completa el resto
  como `manual` y crea indice por origen.

Egresos:

- `GET /api/egresos/` muestra por defecto los egresos del dia actual.
- `PUT /api/egresos/{egreso_id}` solo permite editar egresos manuales.
- Los egresos automaticos de nomina no se editan desde el modulo de Egresos.
- `DELETE /api/egresos/{egreso_id}` esta bloqueado para conservar trazabilidad
  contable.

Prestamos:

- `POST /api/prestamos/` exige profesor valido, monto mayor que 0 y estado
  inicial `Pendiente`.
- `GET /api/prestamos/?profesor_id={profesor_id}` permite revisar historial por
  profesor.
- `PUT /api/prestamos/{prestamo_id}/estado` solo permite saldar el prestamo con
  estado `Pagado`.
- `DELETE /api/prestamos/{prestamo_id}` esta bloqueado para conservar
  trazabilidad financiera.
