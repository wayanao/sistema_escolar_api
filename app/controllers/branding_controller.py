import json
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.database import get_connection
from app.globals import tenant_schema_var

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2MB

# Carpeta base de uploads, servida por endpoint autenticado en main.py.
UPLOADS_ROOT = Path("uploads") / "branding"
UPLOADS_BASE = Path("uploads").resolve()


def _branding_dir_for_tenant() -> Path:
    schema = tenant_schema_var.get()
    folder = UPLOADS_ROOT / schema
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _public_url(file_path: Path) -> str:
    # Convierte ruta local a URL servida por el endpoint autenticado "/uploads/...".
    rel = file_path.as_posix().split("uploads/", 1)[-1]
    return f"/uploads/{rel}"


def _delete_local_file_from_url(url: Optional[str]) -> None:
    if not url:
        return
    try:
        rel = url.split("/uploads/", 1)[-1]
        local = (Path("uploads") / rel).resolve()
        local.relative_to(UPLOADS_BASE)
        if local.exists() and local.is_file():
            local.unlink()
    except (Exception, ValueError):
        pass  # No bloquear flujo si el archivo ya no existe


def obtener_branding_controller():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre_institucion, eslogan, logo_principal_url, logo_secundario_url,
               direccion, telefono, email, nit, sitio_web,
               color_primario, color_secundario, configuracion_extra
        FROM institucion_branding
        ORDER BY id ASC
        LIMIT 1
    """)
    row = cursor.fetchone()

    # Si por algun motivo no existe la fila, la creamos vacia.
    if not row:
        cursor.execute("""
            INSERT INTO institucion_branding (nombre_institucion)
            VALUES ('')
            RETURNING id, nombre_institucion, eslogan, logo_principal_url, logo_secundario_url,
                     direccion, telefono, email, nit, sitio_web,
                     color_primario, color_secundario, configuracion_extra
        """)
        row = cursor.fetchone()
        conn.commit()

    cursor.close()
    conn.close()

    return {
        "id": row[0],
        "nombre_institucion": row[1] or "",
        "eslogan": row[2] or "",
        "logo_principal_url": row[3],
        "logo_secundario_url": row[4],
        "direccion": row[5] or "",
        "telefono": row[6] or "",
        "email": row[7] or "",
        "nit": row[8] or "",
        "sitio_web": row[9] or "",
        "color_primario": row[10] or "#0f314f",
        "color_secundario": row[11] or "#526775",
        "configuracion_extra": row[12] or {},
    }


def actualizar_branding_controller(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE institucion_branding
        SET nombre_institucion = %s,
            eslogan = %s,
            direccion = %s,
            telefono = %s,
            email = %s,
            nit = %s,
            sitio_web = %s,
            color_primario = %s,
            color_secundario = %s,
            configuracion_extra = %s,
            actualizado_en = CURRENT_TIMESTAMP
        WHERE id = (SELECT id FROM institucion_branding ORDER BY id ASC LIMIT 1)
    """, (
        data.nombre_institucion or "",
        data.eslogan or "",
        data.direccion or "",
        data.telefono or "",
        data.email or "",
        data.nit or "",
        data.sitio_web or "",
        data.color_primario or "#0f314f",
        data.color_secundario or "#526775",
        json.dumps(data.configuracion_extra or {}),
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return obtener_branding_controller()


async def subir_logo_controller(archivo: UploadFile, slot: str):
    if slot not in {"principal", "secundario"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="slot debe ser 'principal' o 'secundario'"
        )

    if archivo.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Use: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    ext = Path(archivo.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension no permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    contenido = await archivo.read()
    if len(contenido) > MAX_LOGO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo demasiado grande (max {MAX_LOGO_BYTES // 1024}KB)"
        )

    folder = _branding_dir_for_tenant()
    nombre_archivo = f"logo_{slot}_{uuid.uuid4().hex}{ext}"
    destino = folder / nombre_archivo
    destino.write_bytes(contenido)

    nueva_url = _public_url(destino)
    columna = "logo_principal_url" if slot == "principal" else "logo_secundario_url"

    conn = get_connection()
    cursor = conn.cursor()
    # Recuperar URL anterior para borrarla del disco.
    cursor.execute(f"""
        SELECT {columna} FROM institucion_branding
        ORDER BY id ASC LIMIT 1
    """)
    row = cursor.fetchone()
    url_anterior = row[0] if row else None

    cursor.execute(f"""
        UPDATE institucion_branding
        SET {columna} = %s,
            actualizado_en = CURRENT_TIMESTAMP
        WHERE id = (SELECT id FROM institucion_branding ORDER BY id ASC LIMIT 1)
    """, (nueva_url,))
    conn.commit()
    cursor.close()
    conn.close()

    if url_anterior and url_anterior != nueva_url:
        _delete_local_file_from_url(url_anterior)

    return {"url": nueva_url, "slot": slot}


def eliminar_logo_controller(slot: str):
    if slot not in {"principal", "secundario"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="slot debe ser 'principal' o 'secundario'"
        )

    columna = "logo_principal_url" if slot == "principal" else "logo_secundario_url"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT {columna} FROM institucion_branding
        ORDER BY id ASC LIMIT 1
    """)
    row = cursor.fetchone()
    url_anterior = row[0] if row else None

    cursor.execute(f"""
        UPDATE institucion_branding
        SET {columna} = NULL,
            actualizado_en = CURRENT_TIMESTAMP
        WHERE id = (SELECT id FROM institucion_branding ORDER BY id ASC LIMIT 1)
    """)
    conn.commit()
    cursor.close()
    conn.close()

    _delete_local_file_from_url(url_anterior)
    return {"mensaje": "Logo eliminado", "slot": slot}
