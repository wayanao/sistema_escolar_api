import os
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from app.config import settings

def get_password_hash(password: str) -> str:
    """Retorna el hash bcrypt de una contraseña en texto plano. Evita fallos de passlib."""
    hashed = bcrypt.hashpw(password[:72].encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en base a su hash bcrypt. Sin usar passlib."""
    try:
        return bcrypt.checkpw(plain_password[:72].encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un token JWT con la información dada."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # FORZAR A STRING LOS VALORES POR SEGURIDAD DE JWT
    for key, value in to_encode.items():
        if key not in ["exp", "nbf", "iat"]:
            to_encode[key] = str(value)
            
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
