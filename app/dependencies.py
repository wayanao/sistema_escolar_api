from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.core.tenant_status import (
    colegio_usa_entrevista_admision,
    ensure_tenant_allowed_for_app,
)
from app.database import get_connection
from app.db.tenant import TENANT_SCHEMA_PATTERN
from app.globals import tenant_schema_var

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# Cache de las columnas de una tabla, por (schema del tenant, tabla).
#
# `_columnas_tabla` se ejecutaba en CADA peticion autenticada de toda la API.
#
# Medido contra la base real el 2026-09-03: la consulta tarda lo mismo que
# cualquier otra. No es cara por si misma; es cara porque la base esta en otro
# continente -Neon, us-east-1- y lo que se paga es el numero de idas y vueltas,
# se consulte lo que se consulte. Lo que ahorra el cache es por tanto una ida y
# vuelta por peticion, ni mas ni menos.
#
# Vuelto a medir el 2026-09-24, porque la cifra escrita aqui estaba mal: una
# ida y vuelta cuesta ~60 ms, no ~180. Los ~180 ms eran el precio de **una
# conexion entera**, que gasta tres idas antes de consultar nada (el BEGIN
# implicito, el search_path y los timeouts). El cache sigue ahorrando una sola
# ida: ~60 ms por peticion.
#
# Se deja esta historia escrita porque la primera version de este comentario
# afirmaba que `information_schema` era "de las lecturas mas caras de
# PostgreSQL". Sonaba plausible y era falso. Dos veces ya: el ahorro real es
# modesto y el cache cuesta una busqueda en un dict. Sigue mereciendo la pena,
# pero por el motivo correcto y por la cifra correcta.
#
# Lo que cachea es **metadata de esquema**, no datos: solo cambia cuando una
# migracion anade o quita una columna. Cada despliegue reinicia el proceso y
# vacia el cache, asi que una migracion desplegada de la forma habitual se
# recoge sola. Si alguna vez se migra en caliente, sin reiniciar, hay que llamar
# a `limpiar_cache_columnas()`.
#
# La clave incluye el tenant porque la consulta filtra por
# `current_schemas(false)`: dos colegios pueden tener columnas distintas si uno
# va retrasado de migraciones.
#
# Sin candado a proposito. Dos hilos que fallen el cache a la vez repiten la
# consulta y escriben el mismo valor; asignar a un dict es atomico en CPython,
# asi que la carrera es inofensiva y no justifica serializar el camino de
# lectura, que es el caliente.
_cache_columnas: dict[tuple[str, str], frozenset[str]] = {}


def limpiar_cache_columnas() -> None:
    """Vacia el cache de columnas. Para pruebas y para migraciones en caliente."""
    _cache_columnas.clear()


def _columnas_tabla(cursor, tabla: str) -> frozenset[str]:
    clave = (tenant_schema_var.get() or "", tabla)
    cacheado = _cache_columnas.get(clave)
    if cacheado is not None:
        return cacheado

    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = %s
        """,
        (tabla,),
    )
    columnas = frozenset(row[0] for row in cursor.fetchall())
    _cache_columnas[clave] = columnas
    return columnas


def _valor_activo(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"activo", "activa", "active", "true", "1", "si", "sí"}


def _validar_usuario_en_bd(user_id: int, rol: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if rol == "profesor":
            columnas = _columnas_tabla(cursor, "profesor")
            campos = ["id"]
            if "estado" in columnas:
                campos.append("estado")
            if "activo" in columnas:
                campos.append("activo")

            cursor.execute(
                f"SELECT {', '.join(campos)} FROM profesor WHERE id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Profesor no existe")

            valores_extra = row[1:]
            if not all(_valor_activo(valor) for valor in valores_extra):
                raise ValueError("Profesor inactivo")
            return

        columnas = _columnas_tabla(cursor, "usuarios")
        campos = ["id", "rol"]
        if "estado" in columnas:
            campos.append("estado")
        if "activo" in columnas:
            campos.append("activo")

        cursor.execute(
            f"SELECT {', '.join(campos)} FROM usuarios WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Usuario no existe")
        if str(row[1]) != rol:
            raise ValueError("Rol desactualizado")

        valores_extra = row[2:]
        if not all(_valor_activo(valor) for valor in valores_extra):
            raise ValueError("Usuario inactivo")
    finally:
        cursor.close()
        conn.close()


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        token = request.cookies.get("token")

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Asegurarnos de soportar variables str o int desde JWT
        user_id = str(payload.get("sub")) if payload.get("sub") else None
        rol = str(payload.get("rol")) if payload.get("rol") else None
        tenant = str(payload.get("tenant")) if payload.get("tenant") else None
        
        if not user_id or not rol or not tenant or not TENANT_SCHEMA_PATTERN.fullmatch(tenant):
            raise credentials_exception
            
        user_id_int = int(user_id)

        await run_in_threadpool(ensure_tenant_allowed_for_app, tenant)

        # Configuramos el contexto de esta petición para que la BD apunte al colegio correcto
        tenant_schema_var.set(tenant)
        await run_in_threadpool(_validar_usuario_en_bd, user_id_int, rol)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    return {"id": user_id_int, "rol": rol, "tenant": tenant}

async def get_current_active_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes los permisos necesarios"
        )
    return current_user


# Entrevista de admisión solo en los colegios que la usan (2026-10-30). Ver
# docs/funcionalidades/ENTREVISTA_ADMISION.md, "Solo en los colegios que la
# usan". Dependen del admin: un profesor recibe 403 antes de que se consulte
# nada.
MENSAJE_SIN_ENTREVISTA = "Este colegio no usa la entrevista de admisión."


async def usa_entrevista_admision(
    current_user: dict = Depends(get_current_active_admin),
) -> bool:
    return await run_in_threadpool(
        colegio_usa_entrevista_admision, current_user["tenant"]
    )


async def exigir_entrevista_admision(
    usa_entrevista: bool = Depends(usa_entrevista_admision),
):
    if not usa_entrevista:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MENSAJE_SIN_ENTREVISTA,
        )
