# Roles y Permisos Backend

Estado documentado: 2026-05-25.

## Roles actuales

Roles usados en el backend:

- `admin`
- `profesor`

El rol se incluye en el JWT como claim `rol`.

## Dependencias de autenticacion/autorizacion

Archivo:

- `app/dependencies.py`

Funciones:

- `get_current_user`
- `get_current_active_admin`

`get_current_user`:

- acepta token por OAuth2 Bearer;
- si no hay Bearer, intenta leer cookie `token`;
- decodifica JWT con `settings.SECRET_KEY` y `settings.ALGORITHM`;
- exige `sub`, `rol` y `tenant`;
- valida el tenant con `TENANT_SCHEMA_PATTERN`;
- fija `tenant_schema_var`;
- revalida usuario/rol contra la base del tenant.

`get_current_active_admin`:

- depende de `get_current_user`;
- exige `rol == "admin"`;
- si no cumple responde `403`.

## Revalidacion contra base de datos

Funcion:

- `_validar_usuario_en_bd`

Para `profesor`:

- consulta tabla `profesor`;
- si existen columnas `estado` o `activo`, valida que esten activas.

Para otros roles:

- consulta tabla `usuarios`;
- valida que el rol actual en DB coincida con el rol del token;
- si existen columnas `estado` o `activo`, valida que esten activas.

## Modulo central de permisos

Archivo:

- `app/core/permissions.py`

Funciones actuales:

- `require_estudiante_access(estudiante_id, current_user)`
- `require_profesor_scope(profesor_id, current_user, detail="No autorizado")`
- `require_asignacion_access(asignacion_id, current_user, detail="No autorizado")`
- `require_estudiante_in_asignacion(estudiante_id, asignacion_id)`
- `require_plan_de_clases_access(plan_id, current_user, detail="No autorizado")`

## Reglas por funcion

`require_estudiante_access`:

- admin pasa;
- profesor pasa si el estudiante pertenece a un curso donde tiene asignacion;
- otros roles reciben `403`.

`require_profesor_scope`:

- admin pasa;
- profesor pasa solo si `current_user.id == profesor_id`;
- si no cumple recibe `403`.

`require_asignacion_access`:

- admin pasa;
- profesor pasa si la asignacion pertenece a su `profesor_id`;
- otros casos reciben `403`.

`require_estudiante_in_asignacion`:

- valida que el estudiante pertenezca al curso asociado a la asignacion.

`require_plan_de_clases_access`:

- admin pasa;
- profesor pasa si el plan esta asociado a una asignacion propia.

## Routers protegidos por admin

Segun los routers actuales, usan `get_current_active_admin`:

- estudiantes
- cuentas
- pagos
- cursos
- profesores
- materias
- usuario
- reportes
- tipos_pagos
- inventario
- cartera
- nomina
- varias rutas admin de plan de clases, plantillas, branding, ventas, prestamos y egresos

## Routers con usuario autenticado y permisos de ownership

Usan `get_current_user` y permisos por ownership:

- notas
- planilla
- asistencia
- boletines
- dashboard
- asignaciones para `/mis-clases` y `/profesores/{profesor_id}/cursos`
- plan de clases de profesor
- planeador anual
- observaciones
- plantillas de lectura
- branding de lectura

## Riesgos pendientes documentados

- No todos los endpoints con IDs directos fueron revisados en este documento linea por linea.
- Algunos routers aun contienen SQL directo fuera de controllers.
- La autorizacion fina depende de que todos los endpoints sensibles usen las funciones centralizadas.
