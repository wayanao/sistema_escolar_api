import contextvars

# Variable de contexto que guardará el esquema de la BD en cada petición
# Se usa un objeto para que sea mutable y rastreable si lo amerita, guardará el string
tenant_schema_var = contextvars.ContextVar("tenant_schema", default="tenant_colegio_1")