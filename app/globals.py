import contextvars

# Variable de contexto que guardará el esquema de la BD en cada petición
# No debe apuntar a un colegio real por defecto: cada request debe fijar su tenant.
tenant_schema_var = contextvars.ContextVar("tenant_schema", default=None)
