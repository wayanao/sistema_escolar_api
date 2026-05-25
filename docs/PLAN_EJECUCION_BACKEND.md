# Plan Ejecucion Backend

Estado documentado: 2026-05-25.

Plan basado en la documentacion actual de `docs/` del backend y en `CHECKLIST_PRODUCCION_BACKEND.md`. Este archivo ordena trabajo futuro; no representa cambios de codigo ya aplicados.

## 1. Seguridad frontend

En backend esta fase significa blindar todo lo que el navegador puede intentar manipular: token, rol, tenant, IDs directos y archivos.

- Objetivo: asegurar que el backend sea la fuente real de permisos, tenant y ownership.
- Tareas:
  - Revalidar endpoints sensibles con `get_current_user` o `get_current_active_admin`.
  - Confirmar que rutas con `estudiante_id`, `profesor_id`, `asignacion_id` o `plan_id` usan permisos de `app/core/permissions.py`.
  - Probar que profesores no puedan consultar estudiantes, planes, asistencia, notas o boletines fuera de sus asignaciones.
  - Confirmar que admin solo opera dentro de su tenant.
  - Confirmar que `/uploads/{file_path:path}` sigue exigiendo autorizacion y tenant correcto.
- Archivos probables:
  - `app/dependencies.py`
  - `app/core/permissions.py`
  - `app/routes/notas.py`
  - `app/routes/planilla.py`
  - `app/routes/asistencia.py`
  - `app/routes/boletines.py`
  - `app/routes/dashboard.py`
  - `app/routes/asignaciones.py`
  - `app/routes/plan_de_clases.py`
  - `app/main.py`
- Riesgo: ALTO. Un endpoint sin ownership puede permitir lectura o modificacion cruzada entre profesores o tenants.
- Como probar:
  - Crear dos tenants con datos distintos.
  - Entrar como profesor A y cambiar manualmente IDs de profesor B.
  - Entrar como tenant A e intentar acceder a datos conocidos del tenant B.
  - Abrir `/uploads/...` sin token, con token de otro tenant y con profesor no propietario.
- Cuando hacer commit:
  - Hacer commit por grupo de rutas cerrado y probado, por ejemplo `notas/boletines`, luego `asistencia/planilla`, luego `uploads`.

## 2. Manejo de sesion

- Objetivo: consolidar sesion segura con cookie HttpOnly y evitar depender de token legible por JavaScript.
- Tareas:
  - Revisar `POST /login` y confirmar cookie `token` con `httponly=True`.
  - Confirmar `SESSION_COOKIE_SECURE` y `SESSION_COOKIE_SAMESITE` para produccion.
  - Mantener `POST /logout` limpiando cookie.
  - Definir si la respuesta de login debe seguir devolviendo `access_token` cuando frontend ya use cookie HttpOnly.
  - Confirmar que `get_current_user` lee Bearer token y cookie, y revalida usuario/rol contra DB.
- Archivos probables:
  - `app/routes/auth.py`
  - `app/controllers/auth_controller.py`
  - `app/dependencies.py`
  - `app/security.py`
  - `app/config.py`
  - `.env.example`
- Riesgo: ALTO. Una sesion mal configurada puede exponer tokens, romper login o dejar usuarios inactivos con acceso.
- Como probar:
  - Login admin y profesor desde navegador.
  - Revisar cookie en DevTools y confirmar atributos.
  - Consumir endpoint protegido sin header Bearer, usando solo cookie.
  - Ejecutar logout y confirmar que la cookie queda eliminada.
  - Desactivar o cambiar rol de usuario en DB y confirmar bloqueo en requests sensibles.
- Cuando hacer commit:
  - Despues de probar login, request autenticado, revalidacion contra DB y logout.

## 3. Roles y guards

En backend los guards reales son las dependencias FastAPI y funciones de permisos. La UI solo oculta o muestra pantallas.

- Objetivo: asegurar que cada ruta use la dependencia correcta segun rol y contexto.
- Tareas:
  - Revisar rutas admin-only y confirmar `get_current_active_admin`.
  - Revisar rutas de profesor y confirmar `require_profesor_scope`, `require_asignacion_access`, `require_estudiante_access` o funcion equivalente.
  - Diferenciar respuestas `401` para no autenticado y `403` para sin permiso.
  - Revisar rutas con SQL directo para que no salten permisos centralizados.
- Archivos probables:
  - `app/dependencies.py`
  - `app/core/permissions.py`
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
  - `app/routes/observaciones.py`
- Riesgo: ALTO. Un profesor podria consumir rutas administrativas si falta una dependencia de rol.
- Como probar:
  - Usar token de profesor contra endpoints administrativos.
  - Usar token admin contra datos de otro tenant.
  - Probar rutas con IDs directos cambiando parametros manualmente.
- Cuando hacer commit:
  - Despues de cerrar una familia de rutas y dejar pruebas o evidencia manual clara.

## 4. Componentes grandes

En backend esta fase corresponde a separar rutas, controladores, servicios y repositorios donde hoy haya SQL o logica pesada mezclada.

- Objetivo: mejorar mantenibilidad sin cambiar contratos de API.
- Tareas:
  - Identificar controladores grandes o rutas con SQL directo.
  - Mover consultas repetidas a services/repositories cuando se trabaje cada modulo.
  - Mantener responses actuales para no romper frontend.
  - Priorizar modulos sensibles: estudiantes, reportes, cartera, boletines, asignaciones y plan de clases.
- Archivos probables:
  - `app/controllers/*.py`
  - `app/routes/observaciones.py`
  - `app/routes/asignaciones.py`
  - `app/repositories/`
  - `app/services/`
- Riesgo: MEDIO. Refactors amplios pueden romper endpoints si se mezclan con cambios funcionales.
- Como probar:
  - Comparar respuesta antes/despues de cada endpoint tocado.
  - Ejecutar pruebas existentes.
  - Probar manualmente el modulo conectado desde frontend.
- Cuando hacer commit:
  - Un commit por modulo, solo cuando el contrato de API quede igual y probado.

## 5. Performance

- Objetivo: asegurar que consultas y endpoints escalen con varios colegios y datos historicos.
- Tareas:
  - Verificar indices por tenant con script oficial.
  - Revisar reportes financieros con datos grandes.
  - Revisar endpoints que devuelven listas sin paginacion o limites.
  - Ejecutar `EXPLAIN ANALYZE` en consultas criticas.
  - Confirmar que migraciones e indices esten aplicados en todos los tenants activos.
- Archivos probables:
  - `scripts/apply_tenant_indexes.py`
  - `scripts/check_tenant_schemas.py`
  - `apply_migration.py`
  - `migrations/`
  - `app/controllers/reportes_controller.py`
  - `app/routes/reportes.py`
  - endpoints de estudiantes, pagos, ventas y cartera.
- Riesgo: MEDIO/ALTO. Con datos reales pueden aparecer timeouts, lentitud o carga alta en PostgreSQL.
- Como probar:
  - Ejecutar `scripts/check_tenant_schemas.py`.
  - Ejecutar `scripts/apply_tenant_indexes.py --dry-run` y luego aplicar si corresponde.
  - Probar reportes con historico grande.
  - Medir tiempos desde backend y navegador.
- Cuando hacer commit:
  - Despues de aplicar indices/migraciones con dry-run previo y validacion en tenants de prueba.

## 6. Manejo de errores

- Objetivo: entregar respuestas consistentes, seguras y utiles para frontend y soporte.
- Tareas:
  - Revisar manejo de `401`, `403`, `404`, `422`, `429` y `500`.
  - Evitar exponer detalles internos de SQL o stacktrace en produccion.
  - Confirmar errores claros para tenant no configurado, tenant invalido y usuario sin permiso.
  - Revisar validaciones Pydantic y advertencias de configuracion legacy.
- Archivos probables:
  - `app/main.py`
  - `app/dependencies.py`
  - `app/db/tenant.py`
  - `app/controllers/*.py`
  - `app/schemas/*.py`
- Riesgo: MEDIO. Errores inconsistentes dificultan soporte y pueden filtrar informacion tecnica.
- Como probar:
  - Token ausente.
  - Token invalido.
  - Usuario sin permiso.
  - Tenant manipulado.
  - Formulario invalido.
  - Simular error interno en entorno de prueba.
- Cuando hacer commit:
  - Despues de validar respuestas en al menos login, ruta admin, ruta profesor y upload protegido.

## 7. Build produccion

En backend esta fase significa preparacion real de despliegue: variables, CORS, cookies, migraciones, tenants y scripts operativos.

- Objetivo: dejar backend listo para operar con frontend desplegado y multiples tenants.
- Tareas:
  - Revisar `.env.example` contra `app/config.py`.
  - Confirmar `SECRET_KEY` fuerte y privado.
  - Confirmar `FRONTEND_URL` real y CORS sin origins innecesarios en produccion.
  - Confirmar `SESSION_COOKIE_SECURE=True` en HTTPS.
  - Probar `crear_cliente.py` para tenant nuevo.
  - Probar migraciones con `--dry-run` y aplicacion controlada.
  - Validar rate limit detras de proxy/load balancer.
- Archivos probables:
  - `.env.example`
  - `app/config.py`
  - `app/main.py`
  - `crear_cliente.py`
  - `apply_migration.py`
  - `scripts/*.py`
  - `migrations/`
- Riesgo: ALTO. Una mala configuracion puede romper login, CORS, cookies, tenants o migraciones.
- Como probar:
  - Levantar backend con variables tipo produccion.
  - Login desde frontend con dominio configurado.
  - Crear tenant de prueba y entrar con admin inicial.
  - Ejecutar migracion en dry-run y revisar `public.schema_migrations`.
  - Probar rate limit de login.
- Cuando hacer commit:
  - Despues de validar entorno completo tipo staging: login, rutas protegidas, uploads, tenant nuevo y migraciones.
