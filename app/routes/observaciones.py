from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.controllers.observacion_controller import guardar_observacion_controller

router = APIRouter(tags=["Observaciones"], dependencies=[Depends(get_current_user)])

@router.post("/observaciones")
def guardar_observacion(data: dict):
    return guardar_observacion_controller(data)

@router.get("/observaciones/{estudiante_id}/{asignacion_id}/{periodo}")
def obtener_observacion(estudiante_id: int, asignacion_id: int, periodo: int):
    from app.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT conductual, cognitivo, lenguaje 
        FROM observaciones 
        WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s
    """, (estudiante_id, asignacion_id, periodo))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return {"conductual": row[0], "cognitivo": row[1], "lenguaje": row[2]}
    
    return None