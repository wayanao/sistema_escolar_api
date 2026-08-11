from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Rutas absolutas: no dependen del CWD desde donde se arranque uvicorn
_API_DIR  = Path(__file__).parent.parent          # sistema_escolar_api/
_ROOT_DIR = _API_DIR.parent                        # proyecto_escolar/

class Settings(BaseSettings):
    APP_NAME: str = "Sistema Escolar API"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # SECRET_KEY debe estar en el .env o como variable de entorno de la plataforma.
    # Genera una con: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240

    DATABASE_URL: str
    DB_POOL_MIN_CONNECTIONS: int = 1
    DB_POOL_MAX_CONNECTIONS: int = 10

    # Timeouts de base de datos. En todos, 0 significa "no fijar nada" y deja el
    # valor por defecto del servidor; no lo desactiva.
    #
    # connect_timeout va en segundos porque es de libpq y se resuelve en el
    # cliente. Los otros tres van en milisegundos porque son parametros de
    # PostgreSQL, y se aplican por transaccion con set_config(..., TRUE), nunca
    # en el paquete de arranque: un endpoint agrupado como el -pooler de Neon
    # rechaza la conexion entera si recibe parametros que no sabe rastrear.
    DB_CONNECT_TIMEOUT_SECONDS: int = 10
    DB_STATEMENT_TIMEOUT_MS: int = 30000
    DB_LOCK_TIMEOUT_MS: int = 10000
    DB_IDLE_IN_TRANSACTION_TIMEOUT_MS: int = 60000
    DEFAULT_TENANT_SCHEMA: str = "tenant_colegio_1"

    FRONTEND_URL: str = "http://localhost:5173"
    ALLOW_DEV_CORS_ORIGINS: bool = True
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAMESITE: str = "lax"
    STORAGE_PROVIDER: str = "local"
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_ENDPOINT_URL: str = ""
    R2_REGION: str = "auto"

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


