# Multi-Tenant

Estado documentado: 2026-05-25.

## Modelo actual

El backend usa PostgreSQL con separacion por schemas.

- `public`: contiene datos globales como `colegios` y `schema_migrations`.
- `tenant_*`: contiene las tablas de negocio de cada colegio.

El tenant activo se guarda durante la request en:

- `app/globals.py`
- variable: `tenant_schema_var`

## Identificacion del tenant

El login recibe `codigo_colegio` y consulta:

- tabla global: `public.colegios`
- columna usada para buscar: `subdominio`
- columnas leidas: `esquema_db`, `estado`

Si el colegio existe y esta activo, el login cambia el contexto al schema del colegio y busca el usuario en:

- `usuarios`
- `profesor`

El JWT emitido incluye:

- `sub`
- `rol`
- `tenant`
- `exp`

## Validacion de schemas

Archivo:

- `app/db/tenant.py`

Patrones actuales:

- `TENANT_SCHEMA_PATTERN = ^(tenant_[a-zA-Z0-9_]+|tenant_colegio_[0-9]+)$`
- `INTERNAL_SCHEMA_PATTERN = ^(public|tenant_[a-zA-Z0-9_]+|tenant_colegio_[0-9]+)$`

Uso:

- `TENANT_SCHEMA_PATTERN` se usa para usuarios normales.
- `INTERNAL_SCHEMA_PATTERN` permite `public` para operaciones internas.

## Uso de `search_path`

Archivo:

- `app/db/tenant.py`

Funcion:

- `set_tenant_search_path(cursor)`

Operacion:

```sql
SET search_path TO <tenant_schema>, public
```

El schema se inyecta con `psycopg2.sql.Identifier`.

## Conexion multi-tenant

Archivo:

- `app/db/session.py`

Cada llamada a `get_connection()`:

1. Obtiene una conexion del pool.
2. Desactiva autocommit.
3. Crea un cursor.
4. Ejecuta `set_tenant_search_path(cursor)`.
5. Devuelve una `PooledConnection`.

Si no hay tenant configurado, `get_current_tenant_schema()` lanza:

```text
Tenant no configurado para esta peticion
```

## Middleware tenant

Archivo:

- `app/main.py`

El middleware:

- inicializa `tenant_schema_var` en `None`;
- intenta leer JWT desde header `Authorization`;
- si el token es valido y trae tenant con patron permitido, fija `tenant_schema_var`;
- ignora token invalido y deja que las dependencias de FastAPI respondan despues;
- resetea el contexto al final de la request.

## Login contra `public`

Archivo:

- `app/controllers/auth_controller.py`

El login hace:

1. `tenant_schema_var.set("public")`.
2. Consulta `colegios`.
3. Si el colegio esta activo, cambia a `tenant_schema_var.set(esquema_db)`.
4. Busca usuario en el schema del tenant.

## Creacion actual de tenants

Archivo:

- `crear_cliente.py`

Flujo actual:

- pide datos por terminal;
- valida codigo con `^[a-z0-9_]{3,50}$`;
- crea schema `tenant_<codigo>`;
- registra colegio en `public.colegios`;
- copia tablas desde `DEFAULT_TENANT_SCHEMA`;
- inserta branding inicial vacio;
- copia plantillas predefinidas;
- crea usuario admin con password hasheada.

## Riesgos pendientes documentados

- El tenant se apoya en `search_path`; cualquier conexion usada sin contexto de tenant falla o puede requerir contexto interno.
- Existen scripts historicos que tambien manipulan schemas y `search_path`.
- La consistencia entre tenants depende de migraciones/scripts aplicados correctamente.
- `crear_cliente.py` contiene un bloque SQL base antiguo comentado/definido en `ESQUEMA_BASE_SQL`, aunque el flujo actual copia tablas desde el template.
