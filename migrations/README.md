# Migraciones de base de datos

Esta carpeta contiene archivos SQL de migracion y queda preparada para una
futura adopcion formal de Alembic.

El proyecto usa PostgreSQL con schemas por colegio, asi que las migraciones deben distinguir entre:

- objetos globales en `public`, como `colegios`;
- tablas repetidas en cada schema `tenant_*`;
- cambios de indices, columnas y constraints que deben ejecutarse en todos los tenants.

## Runner actual

Mientras Alembic no este inicializado, el runner oficial es:

```bash
python apply_migration.py migrations/<archivo>.sql --dry-run
python apply_migration.py migrations/<archivo>.sql
```

El runner:

- busca tenants activos en `public.colegios`;
- ejecuta el SQL dentro de cada schema tenant usando `search_path`;
- crea historial en `public.schema_migrations`;
- evita repetir una migracion ya aplicada;
- bloquea una migracion si el mismo nombre aparece con checksum diferente;
- permite simular con `--dry-run` antes de tocar datos.

Reglas:

- no editar un SQL ya aplicado en produccion;
- crear un archivo nuevo por cada cambio funcional;
- probar primero en copia de la base;
- ejecutar primero con `--dry-run`;
- revisar el resultado tenant por tenant.

Inicializacion recomendada:

```bash
alembic init migrations
```

Cuando se inicialice Alembic, conserva este criterio:

- una migracion por cambio funcional;
- nombres claros;
- pruebas en una copia de la base antes de produccion;
- nunca editar una migracion ya aplicada en produccion, crear una nueva.
