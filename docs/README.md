# Documentacion Backend

Ultima revision documental: 2026-06-13.

Indice operativo para mantener control del backend SaaS escolar.

## Lectura rapida

- `PRODUCCION_BACKEND.md`: variables, Render, cookies, CORS, pool, R2 y checklist post-deploy.
- `CHECKLIST_PRODUCCION_BACKEND.md`: riesgos criticos e importantes antes/despues de produccion.
- `CAMBIOS_BACKEND.md`: bitacora historica de cambios tecnicos y documentales.
- `API_ENDPOINTS.md`: mapa de endpoints incluidos en `app/main.py`.
- `ARQUITECTURA_BACKEND.md`: estructura de carpetas, routers, servicios, repositorios y ciclo de vida.
- `BASE_DATOS.md`: PostgreSQL, schemas tenant, pool, tablas, indices y migraciones.
- `MULTITENANT.md`: identificacion de tenant, `search_path`, estados SaaS y creacion de colegios.
- `SEGURIDAD.md`: login, JWT, cookie HttpOnly, CORS, permisos, uploads y hardening.
- `ROLES_PERMISOS_BACKEND.md`: roles `admin`, `profesor`, `super_admin` y dependencias de autorizacion.
- `MIGRACIONES.md`: runner `apply_migration.py`, migraciones publicas/tenant e historial.
- `ESCALABILIDAD.md`: lineamientos para crecer sin romper contratos actuales.
- `PLAN_EJECUCION_BACKEND.md`: orden sugerido para trabajo futuro.

## Estado actual resumido

- API FastAPI con PostgreSQL y `psycopg2`.
- Multi-tenant por schemas: `public` para datos globales y `tenant_*` para colegios.
- Sesion principal por cookie `token` HttpOnly; el JSON de login no expone JWT.
- Super admin vive en `public.super_admins` y entra con codigo de colegio `super_admin`.
- Archivos subidos se sirven por `/uploads/{file_path:path}` con autenticacion, tenant y ownership.
- Produccion puede usar almacenamiento local o Cloudflare R2 con `STORAGE_PROVIDER`.
- Conexion DB centralizada en `app/db/session.py` con `ThreadedConnectionPool`.

## Regla documental

Cuando se modifique backend, actualizar el documento del area tocada y registrar
el cambio en `CAMBIOS_BACKEND.md` si afecta produccion, seguridad, API,
base de datos, permisos, migraciones o comportamiento observable.
