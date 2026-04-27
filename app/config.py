from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Rutas absolutas: no dependen del CWD desde donde se arranque uvicorn
_API_DIR  = Path(__file__).parent.parent          # sistema_escolar_api/
_ROOT_DIR = _API_DIR.parent                        # proyecto_escolar/

class Settings(BaseSettings):
    # SECRET_KEY debe estar en el .env o como variable de entorno de la plataforma.
    # Genera una con: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        # Prueba primero sistema_escolar_api/.env, luego la raíz del proyecto.
        # Ambas son rutas absolutas: funcionan sin importar el CWD.
        env_file=[
            str(_API_DIR / ".env"),
            str(_ROOT_DIR / ".env"),
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
