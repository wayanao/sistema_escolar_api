"""Carga datos demo de rendimiento en un tenant.

Uso:
    python scripts/seed_tenant_performance.py --tenant tenant_colegio_1 --reset
    python scripts/seed_tenant_performance.py --tenant tenant_colegio_1 --clean
"""
from __future__ import annotations

import argparse
import os
import random
from datetime import date, datetime, timedelta

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import execute_values

PREFIX = "PERF_DEMO"


def get_conn():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no esta configurado")
    return psycopg2.connect(database_url)


def set_tenant(cursor, tenant: str) -> None:
    cursor.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(tenant)))


def fetch_ids(cursor, table: str, where: str, params=()) -> list[int]:
    cursor.execute(f"SELECT id FROM {table} WHERE {where}", params)
    return [row[0] for row in cursor.fetchall()]


def insert_returning_ids(cursor, table: str, columns: list[str], rows: list[tuple], page_size: int = 1000) -> list[int]:
    query = sql.SQL("INSERT INTO {} ({}) VALUES %s RETURNING id").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
    )
    execute_values(cursor, query.as_string(cursor), rows, page_size=page_size)
    return [row[0] for row in cursor.fetchall()]


def clean(cursor) -> None:
    curso_ids = fetch_ids(cursor, "cursos", "nombre LIKE %s", (f"{PREFIX}%",))
    profesor_ids = fetch_ids(cursor, "profesor", "documento_identidad LIKE %s", (f"{PREFIX}%",))
    materia_ids = fetch_ids(cursor, "materias", "nombre LIKE %s", (f"{PREFIX}%",))
    estudiante_ids = fetch_ids(cursor, "estudiantes", "documento_identidad LIKE %s", (f"{PREFIX}%",))
    inventario_ids = fetch_ids(cursor, "inventario", "nombre LIKE %s", (f"{PREFIX}%",))
    tipo_pago_ids = fetch_ids(cursor, "tipos_de_pagos", "nombre LIKE %s", (f"{PREFIX}%",))

    cursor.execute("DELETE FROM pagos WHERE descripcion LIKE %s OR tipo_pago LIKE %s", (f"{PREFIX}%", f"{PREFIX}%"))
    cursor.execute("DELETE FROM ventas_detalle WHERE venta_id IN (SELECT id FROM ventas WHERE notas LIKE %s)", (f"{PREFIX}%",))
    cursor.execute("DELETE FROM ventas WHERE notas LIKE %s", (f"{PREFIX}%",))

    if estudiante_ids:
        cursor.execute("DELETE FROM asistencia WHERE estudiante_id = ANY(%s)", (estudiante_ids,))
        cursor.execute("DELETE FROM notas_detalle WHERE estudiante_id = ANY(%s)", (estudiante_ids,))
        cursor.execute("DELETE FROM estudiantes WHERE id = ANY(%s)", (estudiante_ids,))

    if curso_ids:
        cursor.execute("DELETE FROM tipos_pagos_cursos WHERE curso_id = ANY(%s)", (curso_ids,))
        cursor.execute("DELETE FROM asignaciones WHERE curso_id = ANY(%s)", (curso_ids,))
        cursor.execute("DELETE FROM cursos WHERE id = ANY(%s)", (curso_ids,))

    if profesor_ids:
        cursor.execute("DELETE FROM asignaciones WHERE profesor_id = ANY(%s)", (profesor_ids,))
        cursor.execute("DELETE FROM profesor WHERE id = ANY(%s)", (profesor_ids,))

    if materia_ids:
        cursor.execute("DELETE FROM asignaciones WHERE materia_id = ANY(%s)", (materia_ids,))
        cursor.execute("DELETE FROM materias WHERE id = ANY(%s)", (materia_ids,))

    if inventario_ids:
        cursor.execute("DELETE FROM ventas_detalle WHERE inventario_id = ANY(%s)", (inventario_ids,))
        cursor.execute("DELETE FROM inventario WHERE id = ANY(%s)", (inventario_ids,))

    if tipo_pago_ids:
        cursor.execute("DELETE FROM tipos_pagos_cursos WHERE tipo_pago_id = ANY(%s)", (tipo_pago_ids,))
        cursor.execute("DELETE FROM tipos_de_pagos WHERE id = ANY(%s)", (tipo_pago_ids,))


def seed(cursor, args) -> None:
    random.seed(args.seed)
    today = date.today()
    base_datetime = datetime.combine(today, datetime.min.time())

    curso_ids = insert_returning_ids(cursor, "cursos", ["nombre", "descripcion", "jornada"], [
        (f"{PREFIX} Curso {i:02d}", "Carga demo rendimiento", "Manana" if i % 2 else "Tarde")
        for i in range(1, args.courses + 1)
    ])

    profesor_ids = insert_returning_ids(cursor, "profesor", ["nombre", "apellido", "documento_identidad", "email", "telefono", "password", "sueldo"], [
        (f"{PREFIX} Profesor {i:02d}", f"Apellido {i:02d}", f"{PREFIX}-PROF-{i:04d}", f"prof{i:04d}@perf-demo.local", "3000000000", "perf-demo-no-login", 1500000 + (i % 5) * 100000)
        for i in range(1, args.professors + 1)
    ])

    materia_ids = insert_returning_ids(cursor, "materias", ["nombre", "descripcion"], [
        (f"{PREFIX} Materia {i:02d}", "Carga demo rendimiento")
        for i in range(1, args.subjects + 1)
    ])

    dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
    asignaciones = []
    for idx, curso_id in enumerate(curso_ids):
        for j in range(args.assignments_per_course):
            asignaciones.append((curso_id, materia_ids[(idx + j) % len(materia_ids)], profesor_ids[(idx + j) % len(profesor_ids)], dias[j % len(dias)], 1, f"{7 + j:02d}:00", f"{8 + j:02d}:00"))
    asignacion_ids = insert_returning_ids(cursor, "asignaciones", ["curso_id", "materia_id", "profesor_id", "dia", "horas", "hora_inicio", "hora_fin"], asignaciones)

    estudiantes = []
    for i in range(1, args.students + 1):
        estudiantes.append((f"{PREFIX} Estudiante {i:04d}", f"Apellido {i:04d}", f"{PREFIX}-EST-{i:06d}", curso_ids[(i - 1) % len(curso_ids)], "Activo", today.year, today - timedelta(days=365 * (8 + i % 8)), "TI", "Manana" if i % 2 else "Tarde", f"est{i:04d}@perf-demo.local"))
    estudiante_ids = insert_returning_ids(cursor, "estudiantes", ["nombre", "apellido", "documento_identidad", "curso_id", "estado", "anio_escolar", "fecha_nacimiento", "tipo_documento", "jornada", "email"], estudiantes, page_size=1000)

    tipos = [(f"{PREFIX} Matricula", 250000, "Demo rendimiento", "unico", True), (f"{PREFIX} Mensualidad", 180000, "Demo rendimiento", "mensual", True), (f"{PREFIX} Transporte", 90000, "Demo rendimiento", "mensual", True)]
    tipo_pago_ids = insert_returning_ids(cursor, "tipos_de_pagos", ["nombre", "valor", "descripcion", "tipo_cobro", "activo"], tipos)
    insert_returning_ids(cursor, "tipos_pagos_cursos", ["tipo_pago_id", "curso_id", "valor", "activo"], [(tipo_id, curso_id, valor, True) for curso_id in curso_ids for tipo_id, valor in zip(tipo_pago_ids, [250000, 180000, 90000])])

    inventario_ids = insert_returning_ids(cursor, "inventario", ["nombre", "costo", "precio_venta", "stock_actual"], [(f"{PREFIX} Producto {i:03d}", 12000, 25000, 1000) for i in range(1, args.inventory + 1)])

    payment_names = [row[0] for row in tipos]
    pagos = []
    for i in range(args.payments):
        tipo_idx = i % len(payment_names)
        fecha = base_datetime - timedelta(days=random.randint(0, 365))
        pagos.append((estudiante_ids[i % len(estudiante_ids)], payment_names[tipo_idx], [250000, 180000, 90000][tipo_idx], fecha.date(), "Anulado" if i % 37 == 0 else "Pagado", fecha.strftime("%B"), fecha, f"{PREFIX} Pago {i:06d}"))
    execute_values(cursor, "INSERT INTO pagos (estudiante_id, tipo_pago, monto, fecha_pago, estado, mes, fecha, descripcion) VALUES %s", pagos, page_size=1000)

    notas = []
    for i in range(args.notes):
        notas.append((estudiante_ids[i % len(estudiante_ids)], asignacion_ids[i % len(asignacion_ids)], f"{PREFIX} Nota {i:06d}", round(random.uniform(2.0, 5.0), 1), today - timedelta(days=random.randint(0, 180)), (i % 4) + 1, "numerica"))
    execute_values(cursor, "INSERT INTO notas_detalle (estudiante_id, asignacion_id, descripcion, nota, fecha, periodo, tipo_evaluacion) VALUES %s", notas, page_size=1000)

    asistencias = []
    for i in range(args.attendance):
        asistencias.append((estudiante_ids[i % len(estudiante_ids)], asignacion_ids[i % len(asignacion_ids)], today - timedelta(days=random.randint(0, 120)), "ausente" if i % 7 == 0 else "presente", (i % 4) + 1))
    execute_values(cursor, "INSERT INTO asistencia (estudiante_id, asignacion_id, fecha, estado, periodo) VALUES %s", asistencias, page_size=1000)

    ventas = []
    for i in range(args.sales):
        total = 25000 * (1 + (i % 3))
        pagado = total if i % 4 else total / 2
        ventas.append((estudiante_ids[i % len(estudiante_ids)], base_datetime - timedelta(days=random.randint(0, 180)), "Credito" if pagado < total else "Contado", total, "Pagado" if pagado >= total else "Pendiente", f"{PREFIX} Venta {i:06d}", pagado))
    venta_ids = insert_returning_ids(cursor, "ventas", ["estudiante_id", "fecha", "tipo_venta", "total", "estado", "notas", "pagado"], ventas, page_size=1000)
    execute_values(cursor, "INSERT INTO ventas_detalle (venta_id, inventario_id, cantidad, precio_unitario, subtotal) VALUES %s", [(venta_id, inventario_ids[i % len(inventario_ids)], 1 + (i % 3), 25000, (1 + (i % 3)) * 25000) for i, venta_id in enumerate(venta_ids)], page_size=1000)


def main():
    parser = argparse.ArgumentParser(description="Carga datos demo de rendimiento en un tenant.")
    parser.add_argument("--tenant", default="tenant_colegio_1")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--students", type=int, default=500)
    parser.add_argument("--courses", type=int, default=20)
    parser.add_argument("--professors", type=int, default=30)
    parser.add_argument("--subjects", type=int, default=12)
    parser.add_argument("--assignments-per-course", type=int, default=4)
    parser.add_argument("--payments", type=int, default=10000)
    parser.add_argument("--notes", type=int, default=20000)
    parser.add_argument("--attendance", type=int, default=3000)
    parser.add_argument("--inventory", type=int, default=50)
    parser.add_argument("--sales", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260528)
    args = parser.parse_args()

    conn = get_conn()
    try:
        conn.autocommit = False
        cur = conn.cursor()
        set_tenant(cur, args.tenant)
        if args.clean or args.reset:
            print(f">> Limpiando datos {PREFIX} en {args.tenant}...")
            clean(cur)
        if not args.clean:
            print(f">> Insertando datos {PREFIX} en {args.tenant}...")
            seed(cur, args)
        conn.commit()
        print(">> Listo.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
