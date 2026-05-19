from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import settings
from app.database import get_connection
from app.db.tenant import TENANT_SCHEMA_PATTERN
from app.globals import tenant_schema_var

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
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
            
        # Configuramos el contexto de esta petición para que la BD apunte al colegio correcto
        tenant_schema_var.set(tenant)
        
    except JWTError:
        raise credentials_exception
    
    return {"id": int(user_id), "rol": rol, "tenant": tenant}

async def get_current_active_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes los permisos necesarios"
        )
    return current_user
