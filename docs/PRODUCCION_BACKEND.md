# Produccion Backend

Estado documentado: 2026-05-25.

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

No se observo en los archivos leidos un comando unico de produccion documentado en `docs`.

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
- `crear_cliente.py`

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

SaaS/cobro:

- Mantener esta regla operativa:
  - `activo`: pago al dia;
  - `en_mora`: pago vencido, acceso permitido con aviso;
  - `suspendido`: bloqueo temporal por no pago;
  - `cancelado`: cliente retirado/contrato terminado.
- Pendiente agregar auditoria y motivo al cambio de estado.
- Pendiente agregar canales de pago configurables para el aviso de mora.

Auditoria de estado:

- Los cambios de estado de tenant quedan registrados en
  `public.tenant_estado_auditoria`.
- Se guarda tenant, estado anterior, estado nuevo, motivo, super admin y fecha.
- El endpoint `GET /super-admin/tenants/{tenant_id}/estado-auditoria` expone
  los ultimos 50 cambios para consulta desde el panel.

Passwords:

- Pendiente implementar recuperacion/cambio de password para:
  - admin de colegio;
  - profesor;
  - super admin.
