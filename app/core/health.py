"""Chequeo de salud de la API para monitoreo externo.

No pertenece a ningun dominio: es infraestructura transversal, igual que
`logging` o `tenant_status`, asi que vive en `app/core/`.

El chequeo es deliberadamente barato. No cuenta filas, no toca ningun schema de
colegio y no revela versiones ni rutas: es el unico endpoint sin autenticacion
ademas de `login`, y un monitor no necesita mas que un si o un no.
"""
import logging

from app.database import get_connection
from app.globals import tenant_schema_var

logger = logging.getLogger(__name__)

HEALTH_SCHEMA = "public"


def check_database() -> bool:
    """Confirma que el pool entrega una conexion y que PostgreSQL responde.

    Fija el tenant en `public` porque `get_connection()` exige un schema en el
    `ContextVar` y el monitor no envia token. `public` existe siempre y no
    pertenece a ningun colegio, asi que el chequeo no queda atado a que un
    tenant concreto siga activo.

    Cubre de una vez los dos fallos que dejan el sistema inservible aunque el
    proceso siga vivo: que la base no responda y que el pool este agotado
    —`ThreadedConnectionPool` lanza `PoolError` en vez de esperar, asi que
    `connection pool exhausted`, el incidente ya documentado en produccion,
    llega aqui como excepcion—.

    Devuelve False en vez de propagar: quien llama traduce el resultado a un
    status code, y un fallo de infraestructura no debe salir como 500.
    """
    token = tenant_schema_var.set(HEALTH_SCHEMA)
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return cursor.fetchone() is not None
    except Exception:
        # El detalle solo va al log del servidor. La respuesta HTTP no lo
        # incluye: es un endpoint publico y el mensaje de psycopg2 revela DSN,
        # host y nombres internos.
        logger.exception("Chequeo de salud: la base de datos no respondio")
        return False
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                logger.warning("Chequeo de salud: no se pudo cerrar el cursor")
        if conn is not None:
            try:
                conn.close()
            except Exception:
                logger.warning("Chequeo de salud: no se pudo devolver la conexion")
        tenant_schema_var.reset(token)
