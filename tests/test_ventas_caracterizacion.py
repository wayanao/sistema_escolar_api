"""Caracterizacion de la subcapa 7.0 del dominio `ventas`.

Complementa lo que ya existe y no lo repite. `test_ventas_pagination.py` fija
las dos formas de respuesta de `GET /api/ventas/`; `test_anulaciones_financieras.py`
fija cuatro comportamientos del cruce entre pagos y ventas.

Lo que ninguno de los dos toca, y este archivo fija:

- las guardias estructurales de la linea base previa a cualquier extraccion;
- la frontera real del dominio, que resulto ser de dos archivos y no de cuatro;
- el modelo de permisos, que en este dominio si es uniforme;
- los conteos de consultas y de conexiones de los cinco caminos;
- las cuatro tablas que el dominio escribe, incluida `pagos`, que pertenece a
  un dominio ya migrado;
- el contrato HTTP real de la escritura y del borrado, medidos por ASGI;
- los hallazgos que 7.0 registra sin corregir.

Nada de lo que aqui se fija se corrige: 7.0 inventaria y caracteriza, no arregla.
Varias de estas pruebas documentan comportamiento que parece defectuoso; se
fijan tal como estan hoy para que una extraccion posterior no los cambie sin que
alguien lo note.
"""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.controllers import venta_controller

RAIZ = Path(__file__).resolve().parents[1]

CONTROLADOR = "app/controllers/venta_controller.py"
RUTA = "app/routes/ventas.py"
REPOSITORIO = "app/repositories/ventas_repository.py"

ADMIN = {"id": 7, "rol": "admin", "tenant": "tenant_demo"}

PALABRAS_SQL = ("SELECT", "INSERT", "UPDATE", "DELETE", "WITH ")


def _literales_sql(ruta_relativa):
    """Literales de cadena con SQL, excluyendo docstrings.

    Excluir docstrings es la leccion 13 de la capa 6: sin ella, la prosa que
    describe una consulta se cuenta como si fuera la consulta.
    """
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))

    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            texto = ast.get_docstring(nodo, clean=False)
            if texto:
                docstrings.add(texto)

    literales = {
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
    }
    return {
        literal
        for literal in literales - docstrings
        if any(palabra in literal.upper() for palabra in PALABRAS_SQL)
    }


def _puntos_de_ejecucion(ruta_relativa):
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))
    return [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "execute"
    ]


class CursorInstrumentado:
    """Cursor doble que registra cada consulta y sirve resultados en orden.

    `fetchone` y `fetchall` comparten la misma cola, que es el idioma que ya usa
    `test_anulaciones_financieras.py` para este mismo controlador.
    """

    def __init__(self, fetches=()):
        self.fetches = list(fetches)
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fetches.pop(0) if self.fetches else None

    def fetchall(self):
        return self.fetches.pop(0) if self.fetches else []

    def close(self):
        self.closed = True

    @property
    def sql(self):
        return [query for query, _params in self.calls]


class ConexionInstrumentada:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


@pytest.fixture
def instrumentado(monkeypatch):
    """Instrumenta el controlador contando conexiones y consultas.

    Este dominio abre la conexion con `get_connection()` y no con el
    `get_cursor()` que usan los dominios migrados despues de la capa 1, asi que
    lo que se dobla es la fabrica de conexiones.
    """

    def instalar(fetches=()):
        registro = SimpleNamespace(conexiones=0, conexiones_abiertas=[])
        cursor = CursorInstrumentado(fetches=fetches)

        def fake_get_connection():
            registro.conexiones += 1
            conn = ConexionInstrumentada(cursor)
            registro.conexiones_abiertas.append(conn)
            return conn

        monkeypatch.setattr(venta_controller, "get_connection", fake_get_connection)

        registro.cursor = cursor
        registro.conexion = lambda: registro.conexiones_abiertas[-1]
        return registro

    return instalar


def _detalle(inventario_id=3, cantidad=2, precio=1500.0, subtotal=3000.0):
    return SimpleNamespace(
        inventario_id=inventario_id,
        cantidad=cantidad,
        precio_unitario=precio,
        subtotal=subtotal,
    )


def _venta(detalles=None, tipo_venta="Credito", estudiante_id=11, total=3000.0):
    return SimpleNamespace(
        estudiante_id=estudiante_id,
        tipo_venta=tipo_venta,
        total=total,
        notas="",
        detalles=detalles if detalles is not None else [_detalle()],
    )


# ---------------------------------------------------------------------------
# Bloque 1 — estructura de la frontera de persistencia
#
# Las cuatro guardias que 7.0 dejo describiendo el estado ANTERIOR a la
# extraccion fallaron en 7.1, que era la señal esperada —leccion 14 de la capa
# 6, aplicada por cuarta vez—. Aqui quedan sus versiones positivas.
# ---------------------------------------------------------------------------


def test_el_repositorio_de_ventas_es_el_octavo():
    repositorios = {
        ruta.stem
        for ruta in (RAIZ / "app" / "repositories").glob("*.py")
        if ruta.stem != "__init__"
    }

    assert repositorios == {
        "admisiones_repository",
        "anios_lectivos_repository",
        "asignaciones_repository",
        "asistencia_repository",
        "boletin_repository",
        "branding_repository",
        "cuadros_plan_de_clases_repository",
        "dashboard_repository",
        # «Mi curso» del director de grupo (2026-11-07): solo lee.
        "director_grupo_repository",
        "estudiantes_repository",
        # Firmas guardadas para el boletin (2026-11-12, FIRMAS_BOLETIN.md).
        "firmas_repository",
        "listas_seguimiento_repository",
        "notas_repository",
        "observaciones_repository",
        "observador_repository",
        "pagos_repository",
        "plan_de_clases_repository",
        "planeador_anual_repository",
        "planilla_repository",
        "porcentajes_planilla_repository",
        "profesores_repository",
        # Puntualidad de pagos del panel del admin (2026-11-11): solo lee.
        "puntualidad_repository",
        "reportes_repository",
        "subnotas_planilla_repository",
        "super_admin_repository",
        "ventas_repository",
    }


def test_el_sql_del_dominio_vive_solo_en_el_repositorio():
    """Las 17 sentencias salieron del controlador, intactas."""
    assert _literales_sql(CONTROLADOR) == set()
    assert _puntos_de_ejecucion(CONTROLADOR) == []
    assert len(_puntos_de_ejecucion(REPOSITORIO)) == 17


def test_las_diecisiete_funciones_publicas_reciben_el_cursor():
    arbol = ast.parse((RAIZ / REPOSITORIO).read_text(encoding="utf-8"))
    funciones = [
        nodo
        for nodo in arbol.body
        if isinstance(nodo, ast.FunctionDef) and not nodo.name.startswith("_")
    ]

    assert len(funciones) == 17
    for funcion in funciones:
        assert funcion.args.args[0].arg == "cursor", funcion.name


def test_el_repositorio_no_es_dueno_de_ningun_recurso():
    """No abre, no cierra, no confirma y no revierte: eso sigue en el controlador."""
    fuente = (RAIZ / REPOSITORIO).read_text(encoding="utf-8")

    for prohibido in ("get_connection", "get_cursor", "commit()", "rollback()", ".close()"):
        assert prohibido not in fuente, prohibido


def test_el_controlador_conserva_la_propiedad_del_ciclo_de_vida():
    """Seis aperturas, seis cierres, tres `commit` y dos `rollback`.

    Son seis y no cinco porque `eliminar_venta`, el codigo muerto del hallazgo
    4, tambien abre su conexion y commitea. 7.1 no lo retira.
    """
    fuente = (RAIZ / CONTROLADOR).read_text(encoding="utf-8")

    assert fuente.count("get_connection()") == 6
    assert fuente.count("conn.commit()") == 3
    assert fuente.count("conn.rollback()") == 2
    assert fuente.count("conn.close()") == 6
    assert fuente.count("cursor.close()") == 6


def test_la_ruta_no_contiene_sql():
    assert _literales_sql(RUTA) == set()
    assert _puntos_de_ejecucion(RUTA) == []


def test_el_bloque_de_ventas_de_pagos_repository_conserva_sus_cinco_funciones():
    """La frontera que la capa 5 construyo y que 7.0 no puede mover.

    Si alguna vez se mueven, esta prueba debe fallar y obligar a registrarlo.
    """
    fuente = (RAIZ / "app/repositories/pagos_repository.py").read_text(encoding="utf-8")
    arbol = ast.parse(fuente)

    def toca_la_tabla(nodo):
        segmento = ast.get_source_segment(fuente, nodo) or ""
        return any(
            marca in segmento
            for marca in ("FROM ventas", "UPDATE ventas", "INTO ventas")
        )

    funciones = {
        nodo.name
        for nodo in arbol.body
        if isinstance(nodo, ast.FunctionDef) and toca_la_tabla(nodo)
    }

    assert funciones == {
        "leer_saldo_de_venta",
        "leer_venta_para_anular",
        "abonar_a_venta",
        "marcar_venta_pagada",
        "ajustar_venta_tras_anulacion",
    }


def test_una_sexta_funcion_lleva_venta_en_el_nombre_pero_escribe_pagos():
    """`asignar_venta_a_pago` no pertenece al bloque: escribe `pagos`.

    Clasificar por nombre daria seis; clasificar por tabla da las cinco que la
    capa 5 registro. La distincion importa porque es esa sexta funcion la que
    delata el vinculo por texto entre un pago y su cargo.
    """
    from app.repositories import pagos_repository

    assert hasattr(pagos_repository, "asignar_venta_a_pago")
    assert "solo lo tenia en el texto" in pagos_repository.asignar_venta_a_pago.__doc__


# ---------------------------------------------------------------------------
# Bloque 2 — la frontera real del dominio
#
# La leccion de `notas` es que contar archivos por su nombre falla. Aqui el
# recuento sale al reves que alli: son DOS archivos, no cuatro, y el dominio no
# tiene ni servicio ni esquema propio.
# ---------------------------------------------------------------------------


def test_el_dominio_no_tiene_servicio_ni_esquema_propios():
    assert not (RAIZ / "app/services/venta_service.py").exists()
    assert not (RAIZ / "app/schemas/venta.py").exists()


def test_los_esquemas_pydantic_viven_dentro_de_la_ruta():
    """Unico dominio migrado cuyos modelos no estan en `app/schemas/`."""
    arbol = ast.parse((RAIZ / RUTA).read_text(encoding="utf-8"))
    clases = {nodo.name for nodo in arbol.body if isinstance(nodo, ast.ClassDef)}

    assert clases == {"VentaDetalleCreate", "VentaCreate", "VentaAnular"}


def test_el_controlador_expone_ocho_funciones():
    arbol = ast.parse((RAIZ / CONTROLADOR).read_text(encoding="utf-8"))
    funciones = [nodo.name for nodo in arbol.body if isinstance(nodo, ast.FunctionDef)]

    assert funciones == [
        "_formatear_venta",
        "obtener_ventas",
        "obtener_ventas_paginado",
        "obtener_ventas_pendientes",
        "validar_producto_vendible",
        "crear_venta",
        "eliminar_venta",
        "anular_venta",
    ]


# ---------------------------------------------------------------------------
# Bloque 3 — permisos
#
# Este dominio ROMPE el patron de los tres anteriores: dashboard uso cuatro
# modelos en siete entradas y notas dos en cinco. Aqui hay UNO solo.
# ---------------------------------------------------------------------------


def test_las_cinco_entradas_usan_el_mismo_modelo_de_permiso():
    fuente = (RAIZ / RUTA).read_text(encoding="utf-8")

    assert fuente.count("Depends(get_current_active_admin)") == 5
    assert "require_estudiante_access" not in fuente
    assert "require_asignacion_access" not in fuente
    assert "require_profesor_scope" not in fuente


def test_el_permiso_del_dominio_es_admin_estricto():
    from app import dependencies

    fuente = (RAIZ / "app/dependencies.py").read_text(encoding="utf-8")
    cuerpo = fuente.split("async def get_current_active_admin")[1]

    assert 'current_user.get("rol") != "admin"' in cuerpo
    assert "403" in cuerpo or "HTTP_403_FORBIDDEN" in cuerpo
    assert hasattr(dependencies, "get_current_active_admin")


# ---------------------------------------------------------------------------
# Bloque 4 — linea base de consultas y conexiones
#
# Se mide por camino. La capa 7 de dashboard demostro que contar solo consultas
# esconde el coste real, asi que se cuentan tambien las conexiones.
# ---------------------------------------------------------------------------


def test_obtener_ventas_abre_una_conexion_y_hace_dos_consultas(instrumentado):
    registro = instrumentado(fetches=[[], []])

    venta_controller.obtener_ventas()

    assert registro.conexiones == 1
    assert len(registro.cursor.calls) == 2
    assert registro.conexion().closed is True
    assert registro.cursor.closed is True


def test_obtener_ventas_paginado_hace_tres_consultas_con_resultados(instrumentado):
    registro = instrumentado(fetches=[(4,), [(1, "Ana", "Paz", "2026-01-01", "Contado", 10.0, "Pagado", "", 11, None, None)], []])

    resultado = venta_controller.obtener_ventas_paginado(limit=10, offset=0)

    assert registro.conexiones == 1
    assert len(registro.cursor.calls) == 3
    assert resultado["total"] == 4
    assert resultado["limit"] == 10
    assert resultado["offset"] == 0


def test_obtener_ventas_paginado_se_ahorra_la_tercera_consulta_si_no_hay_filas(instrumentado):
    registro = instrumentado(fetches=[(0,), []])

    resultado = venta_controller.obtener_ventas_paginado(limit=10, offset=0)

    assert len(registro.cursor.calls) == 2
    assert resultado == {"total": 0, "limit": 10, "offset": 0, "items": []}


def test_obtener_ventas_pendientes_hace_dos_consultas(instrumentado):
    registro = instrumentado(fetches=[[(1, "2026-01-01", 10.0, "Pendiente", "", 0)], []])

    venta_controller.obtener_ventas_pendientes(11)

    assert registro.conexiones == 1
    assert len(registro.cursor.calls) == 2


def test_obtener_ventas_pendientes_sale_antes_si_no_hay_ventas(instrumentado):
    registro = instrumentado(fetches=[[]])

    assert venta_controller.obtener_ventas_pendientes(11) == []
    assert len(registro.cursor.calls) == 1


def test_crear_venta_cuesta_una_validacion_por_producto_y_dos_por_detalle(instrumentado):
    """1 validacion + 1 INSERT ventas + 2 por cada detalle."""
    registro = instrumentado(fetches=[("Sudadera", 10, "activo"), (501,)])

    resultado = venta_controller.crear_venta(_venta())

    assert registro.conexiones == 1
    assert len(registro.cursor.calls) == 4
    assert resultado == {"id": 501, "mensaje": "Venta exitosa registrada!"}


def test_crear_venta_con_dos_detalles_del_mismo_producto_valida_una_sola_vez(instrumentado):
    """Las cantidades se agregan por producto antes de validar el stock."""
    registro = instrumentado(fetches=[("Sudadera", 10, "activo"), (501,)])

    venta_controller.crear_venta(
        _venta(detalles=[_detalle(inventario_id=3), _detalle(inventario_id=3)])
    )

    validaciones = [sql for sql in registro.cursor.sql if "FOR UPDATE" in sql]
    assert len(validaciones) == 1
    assert len(registro.cursor.calls) == 6


def test_anular_venta_cuesta_cuatro_consultas_mas_una_por_detalle(instrumentado):
    registro = instrumentado(fetches=[(9, "Pendiente"), [(3, 2)]])

    venta_controller.anular_venta(9, "Devolucion del cliente", admin_id=7)

    assert registro.conexiones == 1
    assert len(registro.cursor.calls) == 5


# ---------------------------------------------------------------------------
# Bloque 5 — que escribe este dominio
#
# El supuesto que mandaba en la activacion. Queda confirmado y ampliado: no
# escribe una tabla sino CUATRO, y una de ellas es de un dominio ya migrado.
# ---------------------------------------------------------------------------


def test_crear_venta_escribe_ventas_ventas_detalle_e_inventario(instrumentado):
    registro = instrumentado(fetches=[("Sudadera", 10, "activo"), (501,)])

    venta_controller.crear_venta(_venta())

    sql = " ".join(registro.cursor.sql)
    assert "INSERT INTO ventas (" in sql
    assert "INSERT INTO ventas_detalle" in sql
    assert "UPDATE inventario" in sql
    assert registro.conexion().committed is True


def test_anular_venta_escribe_inventario_pagos_y_ventas(instrumentado):
    registro = instrumentado(fetches=[(9, "Pendiente"), [(3, 2)]])

    venta_controller.anular_venta(9, "Devolucion del cliente", admin_id=7)

    sql = " ".join(registro.cursor.sql)
    assert "UPDATE inventario" in sql
    assert "UPDATE pagos" in sql
    assert "UPDATE ventas" in sql
    assert registro.conexion().committed is True


def test_la_escritura_de_pagos_vive_en_el_repositorio_de_ventas():
    """`pagos` tiene repositorio desde la capa 5 y aun asi se escribe desde aqui.

    7.1 movio esta sentencia del controlador a `ventas_repository` y **no** a
    `pagos_repository`, por simetria con el bloque que la capa 5 dejo alli con
    cinco sentencias sobre la tabla `ventas`. La decision y su alternativa
    descartada estan en la bitacora.

    Lo que la prueba fija no es donde vive, sino que el dominio de ventas sigue
    siendo quien escribe `pagos`: la frontera que la capa 5 dio por cerrada
    tiene un escritor fuera de si misma, y eso no lo cambio la extraccion.
    """
    escrituras_de_pagos = [
        sql for sql in _literales_sql(REPOSITORIO) if "UPDATE pagos" in sql
    ]

    assert len(escrituras_de_pagos) == 1
    assert "UPDATE pagos" not in str(_literales_sql(CONTROLADOR))

    # Ninguno de los dos modulos del dominio importa el repositorio de pagos:
    # la mencion que hay en el nuevo repositorio es prosa que explica la
    # decision, no una dependencia.
    for archivo in (CONTROLADOR, REPOSITORIO):
        fuente = (RAIZ / archivo).read_text(encoding="utf-8")
        assert "import pagos_repository" not in fuente
        assert "pagos_repository." not in fuente.split('"""')[-1]


def test_el_dominio_no_toca_almacenamiento_de_archivos():
    for archivo in (CONTROLADOR, RUTA):
        assert "storage" not in (RAIZ / archivo).read_text(encoding="utf-8")


def test_las_escrituras_revierten_y_cierran_ante_un_fallo(instrumentado):
    registro = instrumentado(fetches=[("Sudadera", 10, "inactivo")])

    with pytest.raises(ValueError):
        venta_controller.crear_venta(_venta())

    assert registro.conexion().rolled_back is True
    assert registro.conexion().closed is True
    assert registro.cursor.closed is True


# ---------------------------------------------------------------------------
# Bloque 6 — contratos de respuesta y aritmetica del dinero
# ---------------------------------------------------------------------------


def test_el_id_de_la_venta_creada_es_un_entero_no_un_diccionario():
    """Contraste deliberado con `POST /notas`, cuyo `id` es un diccionario."""
    resultado = {"id": 501, "mensaje": "Venta exitosa registrada!"}

    assert isinstance(resultado["id"], int)


def test_una_venta_sin_estudiante_se_presenta_como_publico_general():
    fila = (1, None, None, "2026-01-01", "Contado", 10.0, "Pagado", "", None, None, None)

    assert venta_controller._formatear_venta(fila, {})["cliente"] == "Público General"


def test_el_cliente_se_arma_apellido_y_luego_nombre():
    fila = (1, "Paz", "Ana", "2026-01-01", "Contado", 10.0, "Pagado", "", 11, None, None)

    assert venta_controller._formatear_venta(fila, {})["cliente"] == "Ana Paz"


def test_los_importes_se_presentan_como_float_de_python():
    """La cifra es el contrato, y en este dominio la cifra es dinero.

    El dominio convierte con `float()` y no usa `Decimal` en ningun punto.
    """
    fila = (1, "Paz", "Ana", "2026-01-01", "Contado", 10.5, "Pagado", "", 11, None, None)

    total = venta_controller._formatear_venta(fila, {})["total"]
    assert isinstance(total, float)
    assert "Decimal" not in (RAIZ / CONTROLADOR).read_text(encoding="utf-8")


def test_el_saldo_pendiente_se_resta_en_python_sin_redondear(instrumentado):
    registro = instrumentado(fetches=[[(1, "2026-01-01", 10.10, "Pendiente", "", 3.03)], []])

    resultado = venta_controller.obtener_ventas_pendientes(11)

    assert registro.cursor is not None
    assert resultado[0]["total"] == 10.10 - 3.03


def test_la_descripcion_distingue_abono_de_cargo_de_inventario(instrumentado):
    instrumentado(fetches=[[(4, "2026-01-01", 10.0, "Pendiente", "", 0)], [(4, "Sudadera", 2, 5.0, 10.0)]])
    sin_abono = venta_controller.obtener_ventas_pendientes(11)

    assert sin_abono[0]["descripcion"] == "Cargo de Inventario #4: 2x Sudadera"


def test_la_descripcion_de_una_venta_abonada_dice_abono(instrumentado):
    instrumentado(fetches=[[(4, "2026-01-01", 10.0, "Pendiente", "", 3.0)], [(4, "Sudadera", 2, 5.0, 10.0)]])
    con_abono = venta_controller.obtener_ventas_pendientes(11)

    assert con_abono[0]["descripcion"] == "Abono a Cargo #4 (2x Sudadera)"


# ---------------------------------------------------------------------------
# Bloque 7 — hallazgos, fijados sin corregir
# ---------------------------------------------------------------------------


def test_anular_una_venta_busca_los_pagos_por_ILIKE_sin_delimitar(instrumentado):
    """Hallazgo doble sobre el vinculo por texto entre un pago y su cargo.

    `anular_venta` alcanza los pagos por `descripcion ILIKE '%Cargo #N%'`, y las
    dos descripciones que el propio dominio fabrica se comportan distinto:

    - `Abono a Cargo #40 (...)` **si** contiene `Cargo #4`, asi que anular la
      venta 4 alcanza los pagos de la venta 40. El numero no esta delimitado;
    - `Cargo de Inventario #4: ...` **no** contiene `Cargo #4`, asi que el
      patron no reconoce su propia otra forma y solo llega por `venta_id`.

    Se fija tal cual esta hoy; corregirlo es trabajo de otra capa.
    """
    registro = instrumentado(fetches=[(4, "Pendiente"), []])

    venta_controller.anular_venta(4, "Devolucion del cliente", admin_id=7)

    parametros = [params for _sql, params in registro.cursor.calls if params]
    patrones = [p for tupla in parametros for p in tupla if isinstance(p, str) and "Cargo #" in p]
    assert patrones == ["%Cargo #4%"]

    nucleo = patrones[0].strip("%")
    assert nucleo in "Abono a Cargo #40 (2x Sudadera)"
    assert nucleo not in "Cargo de Inventario #4: 2x Sudadera"


def test_eliminar_venta_es_codigo_muerto_que_borra_fisicamente():
    """Hallazgo: la unica sentencia `DELETE` del dominio no tiene consumidor.

    La ruta `DELETE /api/ventas/{id}` responde 405 y dice expresamente que las
    ventas no se eliminan fisicamente, pero la funcion sigue existiendo y hace
    `DELETE FROM ventas`. No se retira: la capa 6 sento el precedente de dejar
    el codigo muerto registrado en vez de borrarlo.
    """
    fuente_ruta = (RAIZ / RUTA).read_text(encoding="utf-8")

    assert hasattr(venta_controller, "eliminar_venta")
    assert "eliminar_venta" not in fuente_ruta
    assert "DELETE FROM ventas WHERE id = %s" in _literales_sql(REPOSITORIO)


def test_obtener_ventas_no_tiene_limite(instrumentado):
    """Hallazgo: la lectura sin paginar trae la tabla entera, sin LIMIT."""
    registro = instrumentado(fetches=[[], []])

    venta_controller.obtener_ventas()

    assert all("LIMIT" not in sql for sql in registro.cursor.sql)


def test_el_dominio_no_resuelve_el_estudiante_ni_comprueba_ownership(instrumentado):
    """Hallazgo: `estudiante_id` entra tal cual y no se valida que exista.

    El aislamiento entre colegios lo da el `search_path`, no una comprobacion
    del dominio. Es el mismo criterio que la capa 5 registro para pagos.
    """
    registro = instrumentado(fetches=[("Sudadera", 10, "activo"), (501,)])

    venta_controller.crear_venta(_venta(estudiante_id=999999))

    assert all("FROM estudiantes" not in sql for sql in registro.cursor.sql)


def test_el_total_de_la_venta_lo_fija_el_cliente_y_no_se_recalcula(instrumentado):
    """Hallazgo: `total` viaja en el payload y se inserta sin comparar subtotales."""
    registro = instrumentado(fetches=[("Sudadera", 10, "activo"), (501,)])

    venta_controller.crear_venta(
        _venta(total=1.0, detalles=[_detalle(subtotal=999999.0)])
    )

    insercion = next(
        params for sql, params in registro.cursor.calls if "INSERT INTO ventas (" in sql
    )
    assert 1.0 in insercion


def test_el_dominio_no_toma_ningun_lock_al_crear_pero_si_al_anular(instrumentado):
    """La venta se crea sin bloquear nada salvo el producto; anular si bloquea."""
    creacion = instrumentado(fetches=[("Sudadera", 10, "activo"), (501,)])
    venta_controller.crear_venta(_venta())
    bloqueos_al_crear = [sql for sql in creacion.cursor.sql if "FOR UPDATE" in sql]

    assert len(bloqueos_al_crear) == 1
    assert "FROM inventario" in bloqueos_al_crear[0]


# ---------------------------------------------------------------------------
# Bloque 8 — contrato HTTP real, medido por ASGI
#
# El resto de la suite llama a las funciones de ruta directamente, lo que NO
# observa el status code: lo infiere. 7.0 de `notas` dejo registrado que esa
# evidencia es mas debil de lo que las bitacoras sugieren. Aqui se conduce la
# aplicacion por su interfaz ASGI, que es el camino real de una peticion.
#
# No se usa TestClient porque httpx no esta instalado y esta subcapa no cambia
# dependencias. No se toca PostgreSQL: la capa de datos va con dobles.
# ---------------------------------------------------------------------------


def _peticion_asgi(aplicacion, metodo, ruta, cuerpo=None):
    """Ejecuta una peticion HTTP real contra la app y devuelve status y cuerpo."""
    import asyncio
    import json

    crudo = json.dumps(cuerpo).encode() if cuerpo is not None else b""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": metodo,
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(crudo)).encode()),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    salida = {"status": None, "body": b""}

    async def receive():
        return {"type": "http.request", "body": crudo, "more_body": False}

    async def send(mensaje):
        if mensaje["type"] == "http.response.start":
            salida["status"] = mensaje["status"]
        elif mensaje["type"] == "http.response.body":
            salida["body"] += mensaje.get("body", b"")

    asyncio.run(aplicacion(scope, receive, send))
    return salida["status"], json.loads(salida["body"].decode())


CUERPO_VENTA = {
    "estudiante_id": 11,
    "tipo_venta": "Credito",
    "total": 3000.0,
    "notas": "",
    "detalles": [
        {"inventario_id": 3, "cantidad": 2, "precio_unitario": 1500.0, "subtotal": 3000.0}
    ],
}


@pytest.fixture
def app_http(monkeypatch):
    """La aplicacion real con un admin autenticado y la capa de datos doblada."""
    from app.dependencies import get_current_user
    from app.main import app

    estado = SimpleNamespace(cursor=None)

    def instalar(fetches):
        cursor = CursorInstrumentado(fetches=fetches)
        estado.cursor = cursor
        monkeypatch.setattr(
            venta_controller,
            "get_connection",
            lambda: ConexionInstrumentada(cursor),
        )

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, instalar, estado
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_http_crear_venta_responde_200_con_el_id_plano(app_http):
    app, instalar, _estado = app_http
    instalar([("Sudadera", 10, "activo"), (501,)])

    estado, cuerpo = _peticion_asgi(app, "POST", "/api/ventas/", CUERPO_VENTA)

    assert estado == 200
    assert cuerpo == {"id": 501, "mensaje": "Venta exitosa registrada!"}


def test_http_una_validacion_fallida_si_responde_400(app_http):
    """Contraste con `POST /notas`, que responde 200 aunque no registre nada.

    Este dominio SI usa el mecanismo de error: la ruta traduce `ValueError` a
    400 y el cliente se entera de que no se guardo nada.
    """
    app, instalar, _estado = app_http
    instalar([("Sudadera", 10, "inactivo")])

    estado, cuerpo = _peticion_asgi(app, "POST", "/api/ventas/", CUERPO_VENTA)

    assert estado == 400
    assert cuerpo["detail"] == "El producto Sudadera está inactivo y no se puede vender."


def test_http_el_borrado_fisico_responde_405(app_http):
    app, _instalar, _estado = app_http

    estado, cuerpo = _peticion_asgi(app, "DELETE", "/api/ventas/7")

    assert estado == 405
    assert "no se eliminan físicamente" in cuerpo["detail"]


def test_http_un_motivo_de_anulacion_corto_responde_400(app_http):
    app, instalar, _estado = app_http
    instalar([])

    estado, cuerpo = _peticion_asgi(app, "POST", "/api/ventas/7/anular", {"motivo": "no"})

    assert estado == 400
    assert "al menos 5 caracteres" in cuerpo["detail"]


def test_http_un_payload_invalido_responde_422(app_http):
    """El contraste que delimita el hallazgo: FastAPI si valida lo que declara."""
    app, instalar, _estado = app_http
    instalar([])

    estado, _cuerpo = _peticion_asgi(
        app, "POST", "/api/ventas/", {"tipo_venta": "Credito"}
    )

    assert estado == 422
