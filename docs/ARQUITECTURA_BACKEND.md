# Arquitectura Backend

Ultima revision documental: 2026-07-15.

## Stack actual

- Python.
- FastAPI.
- PostgreSQL.
- `psycopg2` con `ThreadedConnectionPool`.
- JWT con `python-jose`.
- Password hashing con `bcrypt`.
- Rate limiting con `slowapi`.

## Estructura de raiz

- `app/`: aplicacion FastAPI.
- `docs/`: documentacion de control.
- `migrations/`: archivos SQL de migracion.
- `scripts/`: scripts operativos para tenants, migraciones e indices.
- `tests/`: pruebas automatizadas.
- `uploads/`: archivos subidos, servidos por endpoint autenticado.
- `apply_migration.py`: runner de migraciones por tenant.
- `scripts/legacy/crear_cliente.py`: script antiguo para crear un tenant/colegio por terminal.
- `scripts/legacy/setup_saas.py`: script antiguo de migracion inicial SaaS.
- `.env` y `.env.example`: variables de entorno.
- `requirements.txt`: dependencias Python.

## Estructura de `app/`

- `app/main.py`: crea la app, configura CORS, rate limiter, middleware tenant, endpoint `/uploads/{file_path:path}` e incluye routers.
- `app/config.py`: carga configuracion con `pydantic-settings`.
- `app/security.py`: hash/verificacion de password y creacion de JWT.
- `app/dependencies.py`: dependencias de autenticacion y autorizacion basicas.
- `app/database.py`: reexporta conexion/cursor/pool desde `app/db/session.py`.
- `app/globals.py`: `ContextVar` del tenant actual.
- `app/db/tenant.py`: validacion de schemas y `SET search_path`.
- `app/db/session.py`: pool y obtencion de conexiones.
- `app/core/permissions.py`: permisos reutilizables por profesor, asignacion, estudiante y plan de clases.
- `app/core/logging.py`: configuracion de logging.
- `app/core/tenant_status.py`: calculo de estado efectivo del tenant por suscripcion, mora y bloqueo.
- `app/core/super_admin.py`: dependencia de autenticacion para plataforma SaaS en `public`.
- `app/routes/`: routers HTTP.
- `app/controllers/`: logica de negocio y consultas principales.
- `app/schemas/`: schemas Pydantic.
- `app/services/`: servicios de dominio.
- `app/services/storage.py`: abstraccion de almacenamiento local o Cloudflare R2.
- `app/repositories/`: carpeta iniciada; actualmente contiene repositorio de plan de clases.

## Rutas y controladores

El patron predominante actual es:

- `app/routes/<modulo>.py`: define endpoints FastAPI y dependencias.
- `app/controllers/<modulo>_controller.py`: ejecuta logica y SQL.
- `app/schemas/*.py`: define modelos de entrada/salida donde aplica.

Hay excepciones reales:

- `app/routes/observaciones.py` contiene SQL directo para lectura de observaciones.
- `app/routes/asignaciones.py` contiene SQL directo para `/mis-clases/{profesor_id}`.
- `app/main.py` contiene la validacion y servicio de `/uploads`.
- `app/repositories/plan_de_clases_repository.py` ya separa consultas de plan de clases.

## Servicios y repositorios

Servicios existentes:

- `app/services/cartera.py`
- `app/services/nota_service.py`
- `app/services/plan_de_clases_service.py`
- `app/services/planilla_service.py`

Repositorio existente:

- `app/repositories/plan_de_clases_repository.py`

La carpeta `app/repositories/README.md` indica que los repositorios deben recibir datos simples, devolver datos simples y no conocer detalles HTTP de FastAPI.

## Routers incluidos en `main.py`

`main.py` incluye routers de:

- estudiantes
- cuentas
- pagos
- cursos
- profesores
- asignaciones
- notas
- planilla
- asistencia
- auth
- materias
- observaciones
- plan_de_clases
- dashboard
- planeador_anual
- usuario
- reportes
- super_admin
- tenant
- tipos_pagos
- inventario
- egresos
- prestamos
- ventas
- nomina con prefijo `/api/nomina`
- boletines
- branding
- plantillas
- cartera

## Middleware y ciclo de vida

- `lifespan` registra inicio y cierra el pool con `close_pool()` al apagar.
- `tenant_middleware` intenta leer el JWT del header `Authorization: Bearer ...`, extraer `tenant` y fijarlo en `tenant_schema_var`.
- Al finalizar la request, el middleware resetea el contexto del tenant.

## Convencion de conexiones DB

La conexion a PostgreSQL se centraliza en `app/db/session.py`.

Reglas operativas:

- Codigo nuevo deberia preferir `get_cursor()` como context manager.
- Si un modulo usa `get_connection()` manualmente, debe cerrar cursor y
  conexion en `finally`.
- `PooledConnection.close()` no destruye la conexion normal: la devuelve al
  `ThreadedConnectionPool`.
- El pool se cierra durante el shutdown de FastAPI con `close_pool()`.

Riesgo documentado:

- En produccion, una ruta que abra conexiones y no las cierre puede terminar en
  `psycopg2.pool.PoolError: connection pool exhausted`, especialmente con
  varias requests concurrentes en Render.

## CORS y rate limit

CORS permite:

- `settings.FRONTEND_URL`
- `http://127.0.0.1:5173` solo si `ALLOW_DEV_CORS_ORIGINS=true`
- `http://localhost:5173` solo si `ALLOW_DEV_CORS_ORIGINS=true`

Rate limit global:

- `100/minute`

Login:

- `5/minute`
