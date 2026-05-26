# Checklist Produccion Backend

Estado documentado: 2026-05-25.

Este checklist documenta puntos pendientes o sensibles observados en el backend actual. No propone cambios de codigo dentro de este archivo; solo deja control para revision antes de produccion.

## 1. Critico

### 1.1 Validar acceso cruzado entre tenants

Archivo afectado:

- `app/dependencies.py`
- `app/db/tenant.py`
- `app/db/session.py`
- `app/main.py`

Riesgo:

- Un token o request mal validado podria fijar un tenant incorrecto.

Que puede pasar:

- Un usuario podria consultar datos de otro colegio si el tenant del JWT o el `search_path` no se aplica correctamente.

Como probarlo:

- Crear dos tenants con datos distintos.
- Iniciar sesion en tenant A.
- Intentar consultar IDs conocidos del tenant B.
- Confirmar que no devuelve datos cruzados.
- Repetir con profesor y admin.

### 1.2 Confirmar ownership por profesor en rutas con IDs directos

Archivo afectado:

- `app/core/permissions.py`
- `app/routes/notas.py`
- `app/routes/planilla.py`
- `app/routes/asistencia.py`
- `app/routes/boletines.py`
- `app/routes/dashboard.py`
- `app/routes/asignaciones.py`
- `app/routes/plan_de_clases.py`

Riesgo:

- Un profesor podria cambiar manualmente un `profesor_id`, `asignacion_id`, `estudiante_id` o `plan_id` en la URL.

Que puede pasar:

- Acceso a notas, asistencia, boletines, planes o dashboards de otro profesor.

Como probarlo:

- Entrar como profesor A.
- Tomar un `asignacion_id` o `estudiante_id` perteneciente a profesor B.
- Probar endpoints de notas, planilla, asistencia, dashboard, boletines y plan de clases.
- Confirmar respuesta `403`.

### 1.3 Revisar endpoints con SQL directo en rutas

Archivo afectado:

- `app/routes/observaciones.py`
- `app/routes/asignaciones.py`
- `app/main.py`

Riesgo:

- La logica de permisos o acceso a datos puede quedar dispersa fuera de controllers/services.

Que puede pasar:

- Una ruta nueva o modificada podria saltarse permisos centralizados o consultas esperadas.

Como probarlo:

- Revisar manualmente cada ruta con SQL directo.
- Confirmar que usa `get_current_user` o `get_current_active_admin`.
- Confirmar que valida ownership cuando recibe IDs directos.

### 1.4 Confirmar uploads privados

Archivo afectado:

- `app/main.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/controllers/branding_controller.py`

Riesgo:

- Archivos de un tenant o profesor podrian ser accesibles por URL directa.

Que puede pasar:

- Fuga de logos, imagenes de planeadores u otros archivos subidos.

Como probarlo:

- Abrir una URL `/uploads/...` sin token.
- Abrir archivo de tenant A con usuario de tenant B.
- Abrir imagen de plan de profesor A con profesor B.
- Confirmar `401`, `403` o `404` segun caso.

### 1.5 Verificar migraciones aplicadas en todos los tenants activos

Archivo afectado:

- `apply_migration.py`
- `migrations/`
- `scripts/check_tenant_schemas.py`
- `scripts/apply_tenant_indexes.py`

Riesgo:

- Tenants con tablas, columnas o indices diferentes.

Que puede pasar:

- Errores solo en algunos colegios, datos incompletos o reportes lentos.

Como probarlo:

- Ejecutar comparacion de schemas:

```powershell
.\venv\Scripts\python.exe scripts\check_tenant_schemas.py
```

- Ejecutar indices:

```powershell
.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py --dry-run
```

- Revisar `public.schema_migrations`.

### 1.6 Revisar SECRET_KEY y variables sensibles

Archivo afectado:

- `app/config.py`
- `.env`
- `.env.example`

Riesgo:

- Secret debil, filtrado o reutilizado.

Que puede pasar:

- Tokens JWT falsificados o sesiones comprometidas.

Como probarlo:

- Confirmar que `SECRET_KEY` real no sea el valor de ejemplo.
- Confirmar que `.env` no este versionado.
- Generar secret largo y aleatorio.

## 2. Importante

### 2.1 Revisar CORS para produccion

Archivo afectado:

- `app/main.py`
- `app/config.py`

Riesgo:

- Origins de desarrollo permitidos en produccion.

Que puede pasar:

- Superficie innecesaria para requests desde entornos no productivos.

Como probarlo:

- Revisar valor de `FRONTEND_URL`.
- Confirmar si `localhost` y `127.0.0.1` deben estar permitidos en produccion.
- Probar login desde dominio real.

### 2.2 Confirmar cookie segura en produccion

Archivo afectado:

- `app/routes/auth.py`
- `app/config.py`
- `.env.example`

Riesgo:

- Cookie enviada sin `Secure` en HTTPS productivo o configuracion incompleta.

Que puede pasar:

- Mayor exposicion de sesion si el despliegue no fuerza HTTPS correctamente.

Como probarlo:

- Revisar `SESSION_COOKIE_SECURE`.
- Revisar `SESSION_COOKIE_SAMESITE`.
- Hacer login en navegador y revisar atributos de cookie.

### 2.3 Revisar que `.env.example` refleje todas las variables usadas

Archivo afectado:

- `.env.example`
- `app/config.py`

Riesgo:

- Despliegues incompletos por variables no documentadas.

Que puede pasar:

- Produccion arranca con defaults no deseados o falla por configuracion faltante.

Como probarlo:

- Comparar atributos de `Settings` contra `.env.example`.
- Confirmar que esten documentadas variables de cookie y pool.

### 2.4 Validar rate limit real detras de proxy

Archivo afectado:

- `app/main.py`
- `app/routes/auth.py`

Riesgo:

- `slowapi` puede identificar mal IP si hay proxy/load balancer sin configuracion adecuada.

Que puede pasar:

- Rate limit inutil o bloqueos incorrectos a usuarios reales.

Como probarlo:

- Probar varios intentos de login.
- Revisar IP detectada en entorno de despliegue.
- Confirmar que `5/minute` en login se aplique.

### 2.5 Revisar reportes financieros con datos grandes

Archivo afectado:

- `app/routes/reportes.py`
- `app/controllers/reportes_controller.py`
- `scripts/apply_tenant_indexes.py`

Riesgo:

- Consultas lentas con historicos grandes.

Que puede pasar:

- Timeouts, carga alta en DB o experiencia lenta en reportes.

Como probarlo:

- Poblar datos de pagos historicos.
- Probar `/reportes/ingresos-mes/{mes}` y `/reportes/ingresos-rango`.
- Ejecutar `EXPLAIN ANALYZE` sobre consultas de pagos por fecha.

### 2.6 Probar provisionamiento de tenant nuevo

Archivo afectado:

- `crear_cliente.py`
- `app/controllers/auth_controller.py`
- `scripts/apply_tenant_indexes.py`
- `apply_migration.py`

Riesgo:

- Tenant nuevo incompleto o sin datos base requeridos.

Que puede pasar:

- El colegio nuevo inicia sesion pero falla en pantallas por tablas, indices o plantillas faltantes.

Como probarlo:

- Crear tenant de prueba.
- Iniciar sesion con admin inicial.
- Entrar a pantallas principales.
- Ejecutar indices y revisar migraciones.

### 2.7 Revisar endpoints admin-only

Archivo afectado:

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

Riesgo:

- Profesor accediendo a modulos administrativos.

Que puede pasar:

- Modificacion o lectura de datos administrativos/financieros.

Como probarlo:

- Iniciar sesion como profesor.
- Intentar consumir endpoints administrativos.
- Confirmar `403`.

## 3. Opcional

### 3.1 Completar documentacion detallada por modulo

Archivo afectado:

- `docs/API_ENDPOINTS.md`
- `docs/ARQUITECTURA_BACKEND.md`

Riesgo:

- Baja trazabilidad de responsabilidades por modulo.

Que puede pasar:

- Mayor dificultad para mantener o auditar el sistema.

Como probarlo:

- Elegir un modulo y verificar si el documento explica ruta, controller, schema y permisos.

### 3.2 Revisar advertencias de Pydantic

Archivo afectado:

- `app/schemas/*.py`

Riesgo:

- Uso de configuracion antigua en Pydantic v2.

Que puede pasar:

- Advertencias en pruebas y posible deuda tecnica para futuras versiones.

Como probarlo:

- Ejecutar pruebas.
- Revisar warnings `PydanticDeprecatedSince20`.

### 3.3 Ordenar SQL directo hacia repositories

Archivo afectado:

- `app/controllers/*.py`
- `app/routes/observaciones.py`
- `app/routes/asignaciones.py`
- `app/repositories/`

Riesgo:

- Dificultad para probar consultas aisladas.

Que puede pasar:

- Cambios de negocio mezclados con HTTP o formateo de respuesta.

Como probarlo:

- Revisar si un modulo tiene SQL en route/controller.
- Confirmar si existe repository equivalente.

### 3.4 Ampliar pruebas de integracion

Archivo afectado:

- `tests/`

Riesgo:

- Pruebas unitarias no detectan fallos completos de request + DB + permisos.

Que puede pasar:

- Regresiones que pasan unit tests pero fallan en ejecucion real.

Como probarlo:

- Crear pruebas con cliente FastAPI y base de prueba.
- Cubrir login, tenant, admin, profesor y uploads.

### 3.5 Revisar scripts historicos

Archivo afectado:

- `scripts/*.py`
- `apply_migration.py`
- `crear_cliente.py`

Riesgo:

- Multiples caminos para cambiar schema o datos.

Que puede pasar:

- Cambios aplicados por script antiguo sin historial o sin checksum.

Como probarlo:

- Listar scripts usados actualmente.
- Confirmar cuales son oficiales y cuales son legacy.
- Revisar si escriben historial o usan `--dry-run`.


## Bitacora detallada de avance

Para revisar el detalle historico de lo ya ejecutado durante la auditoria multi-tenant, usar:

- `docs/CAMBIOS_BACKEND.md`

Ese archivo sirve como evidencia de avance antes de produccion y complementa este checklist con verificaciones, comandos de prueba y resultados registrados.



## Estado de avance 2026-05-26

Puntos de seguridad revisados durante la sesion:

- Ownership por observaciones: cerrado con cambio de codigo.
- Ownership por planeador anual: cerrado con cambio de codigo.
- Plan de clases: revisado, ya protegido.
- Asistencia: revisado, ya protegido.
- Boletines: revisado, ya protegido.
- Dashboard: revisado, ya protegido.
- Rutas admin-only principales: revisadas, usan `get_current_active_admin`.

Archivos con cambios reales de codigo:

- `app/routes/observaciones.py`
- `app/routes/planeador_anual.py`

Archivos/documentos actualizados:

- `docs/CAMBIOS_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`

Pendiente recomendado:

- Continuar con configuracion de produccion: variables `.env`, cookies, CORS, `SECRET_KEY`, migraciones e indices.

## Estado de avance 2026-05-26 - Configuracion de produccion

Puntos actualizados:

- `.env.example` ahora incluye `ALLOW_DEV_CORS_ORIGINS`.
- `.env.example` ahora incluye `SESSION_COOKIE_SECURE`.
- `.env.example` ahora incluye `SESSION_COOKIE_SAMESITE`.
- `app/config.py` ahora expone `ALLOW_DEV_CORS_ORIGINS`.
- `app/main.py` permite desactivar origins locales de desarrollo en CORS.
- `POST /logout` elimina la cookie `token` con los atributos configurados de seguridad.

Valores recomendados para produccion:

- `ENVIRONMENT=production`
- `FRONTEND_URL=https://<dominio-frontend-real>`
- `ALLOW_DEV_CORS_ORIGINS=false`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=lax` si frontend y backend comparten sitio compatible; revisar `none` solo si se requiere cross-site con HTTPS.
- `SECRET_KEY` largo, aleatorio y privado.

Pendiente:

- Definir valores reales de produccion.
- Probar login/logout desde el dominio real.
- Confirmar en navegador que la cookie `token` queda HttpOnly y Secure.

## Estado de avance 2026-05-26 - Base de datos

Checklist operativo revisado contra la base:

```text
Base de datos
[x] migraciones aplicadas en todos los tenants activos
[x] indices aplicados
[x] revisar public.schema_migrations
[ ] backup antes de salir
```

Detalle:

- Tenants activos revisados:
  - `tenant_colegio_1`
  - `tenant_3333`
- Las migraciones de `migrations/` quedaron registradas en `public.schema_migrations` para ambos tenants.
- Los indices principales por tenant fueron verificados como existentes.

Pendiente antes de produccion:

- Realizar backup de la base de datos.
- Conservar evidencia/archivo del backup y probar restauracion en entorno de prueba cuando sea posible.
