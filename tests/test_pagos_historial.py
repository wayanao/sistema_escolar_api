"""Caracterizacion de historial_pagos_controller, migrada en la subcapa 1.4l.

Era el unico sitio desprotegido de pagos_controller; los otros seis ya tenian
try/finally.

Es dominio financiero, asi que ademas del SQL se fija el formato exacto que ve el
usuario: el monto como float, la fecha en formato dia/mes/anio con hora de 12
horas, el estado por defecto 'Pagado' y la bandera 'anulado' derivada del estado
sin distinguir mayusculas.
"""

from contextlib import contextmanager
from datetime import datetime

import pytest

from app.controllers import pagos_controller

FECHA = datetime(2026, 8, 3, 14, 30)
ANULACION = datetime(2026, 8, 5, 9, 15)


class CursorFalso:
    def __init__(self, filas):
        self.filas = list(filas)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchall(self):
        return self.filas


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(filas=()):
        cursor = CursorFalso(filas)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(pagos_controller, "get_cursor", fake_get_cursor)
        return cursor, commits

    return instalar


def test_historial_consulta_los_pagos_del_estudiante_mas_recientes_primero(cursor_de):
    fila = (7, 11, 150000, FECHA, "Pensión agosto", "mensualidad", "Pagado", None, None, None)
    cursor, commits = cursor_de(filas=[fila])

    resultado = pagos_controller.historial_pagos_controller(11)

    query, params = cursor.calls[0]
    assert "FROM pagos" in query
    assert "WHERE estudiante_id = %s" in query
    assert "ORDER BY id DESC" in query
    assert params == (11,)
    assert commits == [False]
    assert resultado == [{
        "pago_id": 7,
        "estudiante_id": 11,
        "monto": 150000.0,
        "fecha": "03/08/2026 02:30 PM",
        "descripcion": "Pensión agosto",
        "tipo_pago": "mensualidad",
        "estado": "Pagado",
        "anulado": False,
        "motivo_anulacion": None,
        "fecha_anulacion": None,
        "anulado_por": None,
    }]


def test_historial_marca_los_pagos_anulados(cursor_de):
    fila = (
        8, 11, 150000, FECHA, "Pensión julio", "mensualidad",
        "Anulado", "Pago duplicado", ANULACION, "admin@colegio.edu",
    )
    cursor_de(filas=[fila])

    pago = pagos_controller.historial_pagos_controller(11)[0]

    assert pago["estado"] == "Anulado"
    assert pago["anulado"] is True
    assert pago["motivo_anulacion"] == "Pago duplicado"
    assert pago["fecha_anulacion"] == "05/08/2026 09:15 AM"
    assert pago["anulado_por"] == "admin@colegio.edu"


def test_historial_detecta_anulado_sin_importar_mayusculas(cursor_de):
    fila = (9, 11, 1000, FECHA, "X", "otro", "  ANULADO  ", None, None, None)
    cursor_de(filas=[fila])

    assert pagos_controller.historial_pagos_controller(11)[0]["anulado"] is True


def test_historial_asume_pagado_si_el_estado_viene_vacio(cursor_de):
    fila = (10, 11, 1000, FECHA, "X", "otro", None, None, None, None)
    cursor_de(filas=[fila])

    pago = pagos_controller.historial_pagos_controller(11)[0]

    assert pago["estado"] == "Pagado"
    assert pago["anulado"] is False


def test_historial_devuelve_fecha_vacia_si_el_pago_no_la_tiene(cursor_de):
    fila = (11, 11, 1000, None, "X", "otro", "Pagado", None, None, None)
    cursor_de(filas=[fila])

    assert pagos_controller.historial_pagos_controller(11)[0]["fecha"] == ""


def test_historial_sin_pagos_devuelve_lista_vacia(cursor_de):
    cursor_de(filas=[])

    assert pagos_controller.historial_pagos_controller(11) == []
