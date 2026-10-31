# Roles y Permisos Backend

Ultima revision documental: 2026-10-02.

## Roles actuales

Roles usados en el backend:

- `admin`
- `profesor`
- `super_admin`

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

`super_admin` usa una dependencia separada:

- archivo: `app/core/super_admin.py`;
- funcion: `get_current_super_admin`;
- exige JWT con `rol = "super_admin"` y `tenant = "public"`;
- revalida el usuario contra `public.super_admins`;
- no pasa por `get_current_user`, para no permitir `public` como tenant de usuarios normales.

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
- listas_seguimiento
- varias rutas admin de plan de clases, plantillas, branding, ventas, prestamos y egresos
- `PUT /admin/plan-de-clases/cuadros` (nombres de los cuadros del plan). Su
  lectura, `GET /plan-de-clases/cuadros`, la puede hacer cualquier sesión del
  colegio, profesor o admin: los nombres no son un dato sensible y el
  profesor los necesita para ver su formulario

## Routers protegidos por super admin

Usan `get_current_super_admin`:

- `GET /super-admin/tenants`
- `POST /super-admin/tenants`
- `PATCH /super-admin/tenants/{tenant_id}/estado`
- `GET /super-admin/tenants/{tenant_id}/estado-auditoria`
- `POST /super-admin/tenants/{tenant_id}/pagos`

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

Con usuario autenticado y alcance por rol, sin ownership:

- años lectivos: en `GET /anios-lectivos`, el admin ve todos los años y el
  profesor solo el activo. `POST /anios-lectivos` es solo para admin, calcula
  el año siguiente en el servidor y lo crea en preparación. `POST
  /anios-lectivos/{id}/copiar-configuracion` también es solo para admin y el
  backend exige que el destino sea exactamente ese siguiente año en
  preparación. Las rutas de candidatos, promoción y alta directa bajo
  `/anios-lectivos/{id}` también son solo para admin: el backend valida el
  curso de origen, el curso destino y los estudiantes seleccionados; el
  cliente no decide qué año se puede matricular. El resumen de preparación
  bajo `/anios-lectivos/{id}/resumen` también es solo para admin y solo acepta
  el siguiente año en preparación, igual que la vista previa de activación
  bajo `/anios-lectivos/{id}/activacion/vista-previa`, que además decide en el
  backend si se puede activar, y la marca de salida bajo
  `/anios-lectivos/{id}/matriculas/salida`, donde el backend valida las
  matrículas y rechaza el choque con una matrícula siguiente. Activar el año
  (`POST /anios-lectivos/{id}/activar`) también es solo para admin: el backend
  exige el año escrito, vuelve a revisar los pendientes y decide todo lo que
  cambia; el cliente no elige estados ni cursos. Reabrir y volver a cerrar
  un año pasado (`POST /anios-lectivos/{id}/reabrir` y `/cerrar`) también son
  solo para admin, con el año escrito y un solo año reabierto a la vez. La regla de
  lectura vive en `app/services/anio_lectivo.py`
  (`listar_anios_visibles`), junto con `resolver_anio_pedido`, que los
  listados por año usaran para negar con 403 a un profesor que pida otro
  año. Ver `docs/funcionalidades/ANIO_LECTIVO.md`, decisiones 3 y 4.
- observador (`GET /observador/{estudiante_id}?anio_lectivo_id=`, desde el
  paso 3.5b): ademas del ownership de siempre, un profesor solo puede pedir
  el año activo (`anio_distinto_del_activo` con el usuario); otro año da 403.
  El admin puede pedir cualquiera.
- firma del acudiente en el observador (2026-10-27,
  `docs/funcionalidades/FIRMA_OBSERVADOR.md`): ademas de
  `require_estudiante_access` y de la guardia del año, la toma el autor de la
  anotacion, el director de grupo del curso actual del alumno o el admin
  (`puede_tomar_firma` en `app/core/firma_observador.py`). **El admin firma
  pero no escribe ni edita**: es una excepcion deliberada a
  `_profesor_que_escribe`, porque firmar no cambia el texto. Su id va a
  `tomada_por_usuario_id` y el del profesor a `tomada_por_profesor_id`, nunca
  cruzados. Una anotacion firmada no la edita nadie (409). Los documentos de
  los padres (`firmantes-sugeridos`) solo para el admin, el director de grupo
  o un profesor con alguna anotacion del alumno este año. La firma de un
  periodo (`POST /observador/{estudiante_id}/firmas`) aplica la misma regla a
  cada anotacion, despues de `require_estudiante_access` sobre el alumno de la
  ruta, y es todo o nada: un profesor que no es director solo puede firmar un
  periodo hecho de anotaciones suyas.
- guardia de escritura del año lectivo (paso 3.7, `exigir_anio_editable` en
  `app/services/anio_lectivo.py`): se suma al ownership, no lo reemplaza.
  Nadie escribe en un año `cerrado` (409); el profesor solo en el `activo`
  (403 en `preparacion` o `reabierto`); el admin en el activo, el de
  preparacion y uno reabierto. Corre dentro de la transaccion del guardado,
  antes de escribir. Paso 3.7a: las rutas de escritura que usa el profesor.
  Paso 3.7b: las de solo admin, con la regla del admin (`*_para_admin`: solo
  un año cerrado las frena), porque su router ya exige admin; si alguna se
  abriera a profesores, tendria que pasar a la version con usuario. Lista
  completa en `docs/API_ENDPOINTS.md`, "Guardia de escritura".
- traer el planeador del año pasado (año lectivo, paso 7.1,
  `/planeador-anual/{asignacion_id}/anio-anterior`): el mismo ownership del
  planeador (`require_asignacion_access`, revisado en el controlador con su
  misma conexion) y la guardia del año sobre la clase de destino. El origen
  lo encuentra siempre el servidor desde la clase de este año; el cliente
  nunca manda ids del año pasado. El `GET` no niega al profesor fuera del año
  activo: responde `puede_traer: false`, con la misma regla de la guardia
  (`puede_guardar_en_anio`).
- planes del año pasado (año lectivo, paso 7.2,
  `/plan-de-clases/{asignacion_id}/anio-anterior` y `/{plan_id}`): el mismo
  ownership de las demás rutas de planes (`require_asignacion_access` en la
  ruta) y la guardia del año sobre la clase, que aquí sí niega (`403` o
  `409`), porque solo sirven para crear un plan en esa clase. El backend
  comprueba que el plan pedido sea del origen de la clase; si no, `403`.

## Riesgos pendientes documentados

- No todos los endpoints con IDs directos fueron revisados en este documento linea por linea.
- Algunos routers aun contienen SQL directo fuera de controllers.
- La autorizacion fina depende de que todos los endpoints sensibles usen las funciones centralizadas.
