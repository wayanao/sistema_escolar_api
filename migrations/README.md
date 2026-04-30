# Migraciones de base de datos

Esta carpeta queda reservada para Alembic.

El proyecto usa PostgreSQL con schemas por colegio, asi que las migraciones deben distinguir entre:

- objetos globales en `public`, como `colegios`;
- tablas repetidas en cada schema `tenant_*`;
- cambios de indices, columnas y constraints que deben ejecutarse en todos los tenants.

Inicializacion recomendada:

```bash
alembic init migrations
```

Despues de inicializar Alembic, conserva este criterio:

- una migracion por cambio funcional;
- nombres claros;
- pruebas en una copia de la base antes de produccion;
- nunca editar una migracion ya aplicada en produccion, crear una nueva.
