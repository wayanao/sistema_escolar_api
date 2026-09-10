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

## Mes final de conceptos mensuales

`20260910_tipos_pagos_mes_final.sql` agrega
`tipos_de_pagos.mes_final SMALLINT NOT NULL DEFAULT 12`, valida el rango
`1..12` y, solo para conceptos `mensual`, exige `mes_final >= mes_inicial`
cuando hay mes inicial. El relleno a diciembre conserva los calendarios
actuales; la migracion habilita el campo, pero no configura noviembre para
ningun colegio.

Desde la raiz del backend, primero se simula y luego, solo tras revisar todos
los tenants operativos, se aplica:

```powershell
python apply_migration.py migrations/20260910_tipos_pagos_mes_final.sql --dry-run
python apply_migration.py migrations/20260910_tipos_pagos_mes_final.sql
```

`DATABASE_URL` debe apuntar al endpoint directo, nunca al `-pooler`. Estos
comandos no se ejecutaron al crear la migracion. El esquema base fue actualizado
en el mismo cambio para que los tenants nuevos ya incluyan la columna.

Después de aplicar y desplegar backend/frontend, `tenant_2005` se configura
desde Tipos de Pago: se establece noviembre (`11`) como mes final y se conservan
el mes inicial y la frecuencia institucionales que realmente correspondan. Esa
modificacion es un dato operativo separado y no forma parte del SQL de
migracion.

Inicializacion recomendada:

```bash
alembic init migrations
```

Cuando se inicialice Alembic, conserva este criterio:

- una migracion por cambio funcional;
- nombres claros;
- pruebas en una copia de la base antes de produccion;
- nunca editar una migracion ya aplicada en produccion, crear una nueva.
