import re

from psycopg2 import sql

from app.globals import tenant_schema_var

TENANT_SCHEMA_PATTERN = re.compile(r"^(tenant_[a-zA-Z0-9_]+|tenant_colegio_[0-9]+)$")
INTERNAL_SCHEMA_PATTERN = re.compile(r"^(public|tenant_[a-zA-Z0-9_]+|tenant_colegio_[0-9]+)$")


def get_current_tenant_schema() -> str:
    tenant_schema = tenant_schema_var.get()
    if not tenant_schema:
        raise RuntimeError("Tenant no configurado para esta petición")
    if not INTERNAL_SCHEMA_PATTERN.fullmatch(tenant_schema):
        raise RuntimeError("Tenant inválido para esta petición")
    return tenant_schema


def set_tenant_search_path(cursor) -> str:
    tenant_schema = get_current_tenant_schema()
    cursor.execute(
        sql.SQL("SET search_path TO {}, public").format(sql.Identifier(tenant_schema))
    )
    return tenant_schema
