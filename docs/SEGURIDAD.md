# Seguridad

Ultima revision documental: 2026-07-21.

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
- exige colegio con estado operativo permitido: `activo` o `en_mora`;
- calcula estado efectivo con `public.tenant_suscripciones` cuando existen
  `fecha_proximo_pago` y `dias_gracia`;
- responde `403` con mensaje especifico si el colegio esta `suspendido` o
  `cancelado`;
- cambia al schema del colegio;
- busca primero en `usuarios`;
- si no valida, busca en `profesor`;
- acepta passwords bcrypt;
- si detecta password legacy en texto plano y valida, rehashea y actualiza.

Nota operativa:

- El flujo de login abre conexiones contra `public` y luego contra el schema del
  tenant; esas conexiones deben cerrarse siempre para no agotar el pool en
  produccion.
- Despues del incidente `connection pool exhausted` en Render, el login quedo
  documentado como ruta critica a revisar cuando se toque autenticacion.

Respuestas esperadas:

- `401`: credenciales incorrectas o codigo de colegio inexistente.
- `403`: colegio existente pero bloqueado por estado SaaS (`suspendido` o
  `cancelado`).

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

La duracion por defecto de `ACCESS_TOKEN_EXPIRE_MINUTES` es `240` minutos
para mantener la sesion activa hasta 4 horas desde el inicio de sesion.

La respuesta no devuelve `access_token` ni `token_type`; la sesion real queda
en la cookie `token` y el JSON solo entrega datos minimos de sesion para la UI.

`POST /logout` elimina la cookie `token`.

Produccion y moviles:

- Con HTTPS debe usarse `SESSION_COOKIE_SECURE=true`.
- Si frontend y backend estan en sitios distintos, revisar
  `SESSION_COOKIE_SAMESITE=none`; con `lax` algunos navegadores pueden no
  enviar la cookie en requests cross-site.
- Cuando la cookie no se guarda o no se envia, el sintoma visible es que el
  usuario entra y queda fuera de sesion enseguida.

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
- `http://127.0.0.1:5173` solo si `ALLOW_DEV_CORS_ORIGINS=true`
- `http://localhost:5173` solo si `ALLOW_DEV_CORS_ORIGINS=true`

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

Actualizacion 2026-06-10:

- El admin inicial de un colegio ya no debe conservar la password temporal.
- `usuarios.debe_cambiar_password` obliga el cambio en primer ingreso.
- `POST /auth/cambiar-password` exige password actual y password nueva fuerte.
- El panel de super admin muestra estado efectivo por suscripcion y conserva
  `estado_manual` para decisiones administrativas.
- Las tablas publicas SaaS deben existir por migracion previa al deploy; las
  consultas normales no deben crear tablas en caliente.

- El login ya no devuelve `access_token` ni `token_type`; mantener ese contrato
  para no exponer JWT en el navegador.
- Existen endpoints con SQL directo en rutas.
- No todos los endpoints con IDs directos estan descritos con su prueba especifica en este documento.
- CORS solo debe permitir localhost y 127.0.0.1 en desarrollo con
  `ALLOW_DEV_CORS_ORIGINS=true`; en produccion debe quedar `false`.
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




## Uploads con storage local o Cloudflare R2

El endpoint protegido `GET /uploads/{file_path:path}` se mantiene como puerta unica de acceso a archivos.

Estado actual:

- En desarrollo puede usar disco local con `STORAGE_PROVIDER=local`.
- En produccion puede usar Cloudflare R2 con `STORAGE_PROVIDER=r2`.
- El backend valida tenant y permisos antes de servir el archivo.
- Branding permite archivos bajo `branding/{tenant}/...` solo al mismo tenant.
- Plan diario permite archivos bajo `{tenant}/plan_de_clases/...` al admin del tenant o al profesor propietario del plan.

Riesgo cubierto:

- Evita exponer directamente el bucket al frontend.
- Evita acceso cruzado por cambiar la URL del archivo.
- Evita depender del disco local del servidor para produccion.
