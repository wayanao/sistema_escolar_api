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
- tenants activos en `public.colegios`
- migraciones/indices aplicados a schemas activos

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
