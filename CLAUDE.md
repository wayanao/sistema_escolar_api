# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FastAPI + PostgreSQL backend for a multi-tenant school management system (SaaS).
Consumed by the sibling React frontend `frontend-react`. Deploys automatically to
Render on push to `main` — there is no separate deploy step to run locally, and the
deploy itself is invisible in this repo.

## Working rules

- Before modifying a module, inspect its current implementation, tests, and relevant documentation.
- Prefer the existing layering (routes → controllers → schemas, services/repositories) over a new pattern; prefer the smallest safe change that satisfies the requirement.
- Don't perform unrelated refactors, or delete files/routes/tests/functionality, without explaining why first — and don't do it at all unless it was requested or you flagged it and got a go-ahead.
- Never put secrets, tokens, credentials, `DATABASE_URL`, `SECRET_KEY`, or other env var values in source code, commits, or logs.
- Never weaken authentication, authorization, tenant isolation (schema validation, `search_path`), or input validation to make a feature work.
- **Don't push to `main` or trigger a deploy.** A push to `main` deploys automatically to Render production for real schools — leave committing and pushing to the user unless explicitly told otherwise.

### Sensitive changes

Treat these as high risk. Before touching one: inspect the current implementation,
identify affected files/contracts, explain the change, preserve backward
compatibility when possible, and run the relevant tests afterward.

- authentication/session handling, JWT, cookies
- roles, permissions, tenant resolution/isolation
- migrations (see "two sources of truth" below) and tenant provisioning
- payments, financial reports, and other money-handling controllers
- production environment configuration (`.env`, CORS, cookie flags)

### Validation

Run `python scripts/verify.py` (or the relevant `pytest` subset) after any
meaningful change, and before considering backend work done. Never report a
test/lint as passing unless it actually ran and passed.

## Commands

```bash
python -m pytest -q                       # full test suite
python -m pytest tests/test_pagos_historial.py -q   # single test file
python -m pytest -k "nombre_del_test" -q  # single test by name
python -m ruff check app tests scripts apply_migration.py
python scripts/verify.py                  # the actual CI gate: pytest -q, ruff check, pip check (matches .github/workflows/backend-quality.yml)
uvicorn app.main:app --reload             # run the API locally
```

Run `python scripts/verify.py` before considering backend work done — it's what CI runs.

Requires `.env` (see `.env.example`): `DATABASE_URL`, `SECRET_KEY`,
`DEFAULT_TENANT_SCHEMA`, `FRONTEND_URL`, cookie/CORS/pool settings, optional R2
storage vars.

## Architecture

### Layering

- `app/routes/<modulo>.py` — FastAPI endpoints + dependencies (auth/authorization).
- `app/controllers/<modulo>_controller.py` — business logic and SQL.
- `app/schemas/*.py` — Pydantic request/response models.
- `app/services/` — domain services that don't fit a single controller
  (`cartera.py`, `nota_service.py`, `plan_de_clases_service.py`, `planilla_service.py`,
  `storage.py` for local/R2 uploads).
- `app/repositories/` — newer pattern for pure data access: receive/return plain data,
  no FastAPI/HTTP knowledge (see `app/repositories/README.md`). Only partially adopted
  (`plan_de_clases_repository.py`); new modules being refactored should move SQL here.

Known exceptions to the routes→controllers pattern (documented, not bugs to
"fix" opportunistically): `app/routes/observaciones.py` and
`app/routes/asignaciones.py` (`/mis-clases/{profesor_id}`) contain SQL directly;
`app/main.py` handles `/uploads` itself.

`app/main.py` wires: CORS, rate limiter (slowapi), the tenant middleware, the
`/uploads/{file_path:path}` endpoint, and includes all routers (health first, as
infra). `lifespan` closes the DB pool on shutdown.

### Multi-tenancy — read this before touching any query

PostgreSQL schema-per-tenant: `public` holds global data (`colegios`,
`schema_migrations`, super admin tables); `tenant_*` holds each school's business
tables.

- Current tenant lives in a `ContextVar` (`app/globals.py: tenant_schema_var`),
  set per-request.
- `app/db/session.py: get_connection()` pulls from a `ThreadedConnectionPool`,
  disables autocommit, and runs `SET search_path TO <tenant>, public`
  (`app/db/tenant.py: set_tenant_search_path`) before handing back the connection.
  **Prefer `get_cursor()` as a context manager**; if you use `get_connection()`
  directly, you must close cursor and connection in `finally` — a leaked connection
  can exhaust the pool in production under concurrent Render requests.
- Tenant schema names are validated against `TENANT_SCHEMA_PATTERN` (or
  `INTERNAL_SCHEMA_PATTERN` to also allow `public`) before being interpolated with
  `psycopg2.sql.Identifier` — never format a schema name into SQL yourself.
- Login flow (`app/controllers/auth_controller.py`): sets tenant to `public`,
  looks up `colegios` by `subdominio`, then switches `tenant_schema_var` to the
  resolved `esquema_db` before querying `usuarios`/`profesor`. Only tenants
  `activo`/`en_mora` can log in; `suspendido`/`cancelado` are blocked. Every
  authenticated request re-validates tenant/user state in `get_current_user`, so a
  tenant that becomes suspended mid-session gets locked out immediately.
- The request-level `tenant_middleware` only opportunistically reads the JWT from
  an `Authorization: Bearer` header. Normal browser traffic authenticates via the
  `token` cookie instead — **route protection must depend on
  `get_current_user`/`get_current_active_admin`/`get_current_super_admin`, never
  rely on the middleware alone.**
- Full detail, including tenant provisioning and SaaS status calculation
  (`activo`/`en_mora`/`suspendido`/`cancelado` from `fecha_proximo_pago` +
  `dias_gracia`): `docs/MULTITENANT.md`.

### Auth & permissions

- JWT (`python-jose`) carries `sub`, `rol`, `tenant`, `exp`. Roles: `admin`,
  `profesor`, `super_admin`.
- `app/dependencies.py: get_current_user` decodes the JWT (Bearer or `token`
  cookie), validates the tenant pattern, sets `tenant_schema_var`, then
  re-validates the user/role against the tenant's DB (not just the token claim).
  `get_current_active_admin` layers `rol == "admin"` on top.
- `super_admin` uses a fully separate dependency (`app/core/super_admin.py:
  get_current_super_admin`) validated against `public.super_admins` with
  `tenant == "public"` — it does not go through `get_current_user`, so `public`
  is never a valid tenant for normal users.
- Cross-cutting ownership checks live in `app/core/permissions.py`:
  `require_estudiante_access`, `require_profesor_scope`,
  `require_asignacion_access`, `require_estudiante_in_asignacion`,
  `require_plan_de_clases_access`. Use these instead of re-deriving ownership
  logic in a controller. Details and which routers use which guard:
  `docs/ROLES_PERMISOS_BACKEND.md`.

### Migrations — two sources of truth, keep them in sync

- `migrations/*.sql` — incremental, applied to **existing** tenants via
  `apply_migration.py` (checksummed, tracked in `public.schema_migrations`,
  supports `--dry-run`). Unqualified table names — the runner sets `search_path`
  per target. `migrations/public/*.sql` apply against `public` only.
- `migrations/base/20260813_esquema_base_tenant.sql` — the full schema applied to
  **new** tenants at provisioning (`POST /super-admin/tenants`). Regenerated with
  `scripts/generar_esquema_base.py --schema <schema>` **after** applying new
  migrations to that schema, never before.
- `tests/test_esquema_base.py` fails if a migration exists that the base file
  doesn't declare as incorporated — this is the guardrail; don't bypass it.
- When adding a migration: write it, test against a Neon branch (never against
  prod), apply with `apply_migration.py` using the **direct** (non-pooler)
  `DATABASE_URL`, regenerate the base file, then commit migration + base
  together. Full walkthrough: `docs/MIGRACIONES.md`.

## Testing conventions

`tests/` is flat (no subfolders), one file per concern, often named
`test_<modulo>_caracterizacion.py` for behavior-locking tests written before a
refactor. No pytest config file — defaults apply. CI (`.github/workflows/backend-quality.yml`)
just runs `python scripts/verify.py` against a bare `DATABASE_URL` env var (no real
Postgres in CI for most tests — check how a given test obtains its DB before assuming
it needs a live database).

## Docs

`docs/README.md` is the index. Read the doc for the area you're touching before
changing production, security, API, DB, permissions, or migration behavior, and
update it + `docs/CAMBIOS_BACKEND.md` when you do — this is a project convention,
not optional cleanup. Key docs: `docs/ARQUITECTURA_BACKEND.md`, `docs/MULTITENANT.md`,
`docs/ROLES_PERMISOS_BACKEND.md`, `docs/MIGRACIONES.md`, `docs/SEGURIDAD.md`,
`docs/BASE_DATOS.md`, `docs/API_ENDPOINTS.md`, `docs/modularizacion/README.md`
(active layer-by-layer refactor plan).
