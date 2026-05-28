from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status

from app.config import settings

UPLOADS_ROOT = Path("uploads").resolve()
REMOTE_PROVIDERS = {"r2", "s3"}


def using_remote_storage() -> bool:
    return str(settings.STORAGE_PROVIDER or "local").strip().lower() in REMOTE_PROVIDERS


def normalize_storage_key(value: str) -> str:
    key = str(value or "").replace("\\", "/").strip().lstrip("/")
    if key.startswith("uploads/"):
        key = key[len("uploads/"):]
    return key


def storage_url_for_key(key: str) -> str:
    return f"/uploads/{normalize_storage_key(key)}"


def db_path_for_key(key: str) -> str:
    return f"uploads/{normalize_storage_key(key)}"


def _local_path_for_key(key: str) -> Path:
    return (UPLOADS_ROOT / normalize_storage_key(key)).resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _require_boto3():
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError as exc:
        raise RuntimeError("Falta instalar boto3 para usar Cloudflare R2/S3") from exc
    return boto3, ClientError


def _r2_endpoint_url() -> str:
    if settings.R2_ENDPOINT_URL:
        return settings.R2_ENDPOINT_URL
    if settings.R2_ACCOUNT_ID:
        return f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    raise RuntimeError("Falta R2_ENDPOINT_URL o R2_ACCOUNT_ID")


def _remote_client():
    boto3, _ClientError = _require_boto3()
    if not settings.R2_BUCKET:
        raise RuntimeError("Falta R2_BUCKET")
    if not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY:
        raise RuntimeError("Faltan credenciales R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY")
    return boto3.client(
        "s3",
        endpoint_url=_r2_endpoint_url(),
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name=settings.R2_REGION or "auto",
    )


def save_bytes(key: str, content: bytes, content_type: Optional[str] = None) -> str:
    normalized_key = normalize_storage_key(key)
    if using_remote_storage():
        extra_args = {"ContentType": content_type} if content_type else {}
        _remote_client().put_object(
            Bucket=settings.R2_BUCKET,
            Key=normalized_key,
            Body=content,
            **extra_args,
        )
        return db_path_for_key(normalized_key)

    local_path = _local_path_for_key(normalized_key)
    if not _is_relative_to(local_path, UPLOADS_ROOT):
        raise ValueError("Ruta de archivo invalida")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)
    return db_path_for_key(normalized_key)


def delete_file(value: Optional[str]) -> None:
    if not value:
        return
    key = normalize_storage_key(value.split("/uploads/", 1)[-1])
    if not key:
        return

    if using_remote_storage():
        try:
            _remote_client().delete_object(Bucket=settings.R2_BUCKET, Key=key)
        except Exception:
            pass
        return

    local_path = _local_path_for_key(key)
    try:
        if _is_relative_to(local_path, UPLOADS_ROOT) and local_path.exists() and local_path.is_file():
            local_path.unlink()
    except Exception:
        pass


def local_existing_path(key: str) -> Path:
    local_path = _local_path_for_key(key)
    if not _is_relative_to(local_path, UPLOADS_ROOT) or not local_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    return local_path


def remote_file_exists(key: str) -> bool:
    if not using_remote_storage():
        return local_existing_path(key).is_file()

    _boto3, ClientError = _require_boto3()
    try:
        _remote_client().head_object(Bucket=settings.R2_BUCKET, Key=normalize_storage_key(key))
        return True
    except ClientError as exc:
        status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status_code in {403, 404}:
            return False
        raise


def read_file_bytes(key: str) -> tuple[BytesIO, Optional[str]]:
    normalized_key = normalize_storage_key(key)
    if using_remote_storage():
        try:
            response = _remote_client().get_object(Bucket=settings.R2_BUCKET, Key=normalized_key)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado") from exc
        return BytesIO(response["Body"].read()), response.get("ContentType")

    local_path = local_existing_path(normalized_key)
    return BytesIO(local_path.read_bytes()), None
