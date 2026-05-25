# Seguridad

Estado documentado: 2026-05-25.

## Autenticacion

Endpoint:

- `POST /login`

Archivo:

- `app/routes/auth.py`
- `app/controllers/auth_controller.py`

El login requiere:

- `email`
- `password`
- `codigo_colegio`

El controlador:

- consulta `public.colegios` por `subdominio`;
- exige colegio con `estado = 'activo'`;
- cambia al schema del colegio;
- busca primero en `usuarios`;
- si no valida, busca en `profesor`;
- acepta passwords bcrypt;
- si detecta password legacy en texto plano y valida, rehashea y actualiza.

## JWT

Archivo:

- `app/security.py`

El token se firma con:

- `settings.SECRET_KEY`
- `settings.ALGORITHM`

Claims usados:

- `sub`
- `rol`
- `tenant`
- `exp`

`create_access_token` fuerza a string los valores que no son `exp`, `nbf` o `iat`.

## Cookie de sesion

`POST /login` tambien escribe cookie:

- nombre: `token`
- `httponly=True`
- `secure=settings.SESSION_COOKIE_SECURE`
- `samesite=settings.SESSION_COOKIE_SAMESITE`
- `max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60`
- `path=/`

La respuesta tambien devuelve `access_token`.

`POST /logout` elimina la cookie `token`.

## Lectura de token

Archivo:

- `app/dependencies.py`

`get_current_user`:

- usa Bearer token si existe;
- si no existe, intenta cookie `token`;
- valida JWT;
- valida `sub`, `rol`, `tenant`;
- valida tenant con `TENANT_SCHEMA_PATTERN`;
- revalida usuario/rol contra DB.

## Hash de passwords

Archivo:

- `app/security.py`

Funciones:

- `get_password_hash`
- `verify_password`

Implementacion:

- usa `bcrypt.hashpw`;
- recorta password a 72 bytes/caracteres antes de hashear/verificar.

## Rate limiting

Archivo:

- `app/main.py`
- `app/routes/auth.py`

Configuracion:

- limite global default: `100/minute`.
- login: `5/minute`.

## CORS

Configurado en `app/main.py`.

Origins:

- `settings.FRONTEND_URL`
- `http://127.0.0.1:5173`
- `http://localhost:5173`

Permite credenciales:

- `allow_credentials=True`

## Uploads protegidos

Endpoint:

- `GET /uploads/{file_path:path}`

Archivo:

- `app/main.py`

Validaciones actuales:

- resuelve ruta contra `UPLOADS_ROOT`;
- rechaza path traversal;
- exige archivo existente;
- permite `uploads/branding/{tenant}/...` solo al tenant del usuario;
- permite `uploads/{tenant}/plan_de_clases/...` a admin del tenant;
- permite imagenes de plan de clases a profesor propietario de la asignacion asociada.

## Permisos centralizados

Archivo:

- `app/core/permissions.py`

Funciones:

- `require_estudiante_access`
- `require_profesor_scope`
- `require_asignacion_access`
- `require_estudiante_in_asignacion`
- `require_plan_de_clases_access`

## Riesgos pendientes documentados

- La respuesta de login todavia devuelve `access_token`, ademas de cookie HttpOnly.
- Existen endpoints con SQL directo en rutas.
- No todos los endpoints con IDs directos estan descritos con su prueba especifica en este documento.
- CORS permite localhost y 127.0.0.1 ademas de `FRONTEND_URL`.
- Hay advertencias de Pydantic v2 en pruebas para schemas con `Config` tipo clase.

## Referencia historica de endurecimiento

El detalle cronologico de endurecimiento multi-tenant esta consolidado en:

- `docs/CAMBIOS_BACKEND.md`

La bitacora oficial registra cambios ya realizados sobre:

- rutas admin-only;
- eliminacion del fallback a tenant por defecto;
- rechazo de `public` como tenant de usuario;
- revalidacion de usuario/rol contra DB;
- permisos por profesor, asignacion, estudiante y plan de clases;
- proteccion de `/uploads`;
- pruebas base de auth, tenant, permisos y uploads.



