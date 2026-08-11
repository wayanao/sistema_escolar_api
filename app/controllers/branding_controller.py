import json
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.database import get_cursor
from app.globals import tenant_schema_var
from app.services.storage import delete_file, save_bytes, storage_url_for_key

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2MB


def obtener_branding_controller():
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT id, nombre_institucion, eslogan, logo_principal_url, logo_secundario_url,
                   direccion, telefono, email, nit, codigo_dane, sitio_web,
                   color_primario, color_secundario, configuracion_extra
            FROM institucion_branding
            ORDER BY id ASC
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            cursor.execute("""
                INSERT INTO institucion_branding (nombre_institucion)
                VALUES ('')
                RETURNING id, nombre_institucion, eslogan, logo_principal_url, logo_secundario_url,
                         direccion, telefono, email, nit, codigo_dane, sitio_web,
                         color_primario, color_secundario, configuracion_extra
            """)
            row = cursor.fetchone()

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
        "codigo_dane": row[9] or "",
        "sitio_web": row[10] or "",
        "color_primario": row[11] or "#0f314f",
        "color_secundario": row[12] or "#526775",
        "configuracion_extra": row[13] or {},
    }


def actualizar_branding_controller(data):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE institucion_branding
            SET nombre_institucion = %s,
                eslogan = %s,
                direccion = %s,
                telefono = %s,
                email = %s,
                nit = %s,
                codigo_dane = %s,
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
            data.codigo_dane or "",
            data.sitio_web or "",
            data.color_primario or "#0f314f",
            data.color_secundario or "#526775",
            json.dumps(data.configuracion_extra or {}),
        ))

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

    schema = tenant_schema_var.get()
    nombre_archivo = f"logo_{slot}_{uuid.uuid4().hex}{ext}"
    key = f"branding/{schema}/{nombre_archivo}"
    save_bytes(key, contenido, archivo.content_type)

    nueva_url = storage_url_for_key(key)
    columna = "logo_principal_url" if slot == "principal" else "logo_secundario_url"

    with get_cursor(commit=True) as cursor:
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

    if url_anterior and url_anterior != nueva_url:
        delete_file(url_anterior)

    return {"url": nueva_url, "slot": slot}


def eliminar_logo_controller(slot: str):
    if slot not in {"principal", "secundario"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="slot debe ser 'principal' o 'secundario'"
        )

    columna = "logo_principal_url" if slot == "principal" else "logo_secundario_url"
    with get_cursor(commit=True) as cursor:
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

    delete_file(url_anterior)
    return {"mensaje": "Logo eliminado", "slot": slot}
