"""La migracion base debe declarar las mismas migraciones que hay en migrations/.

El alta de un colegio nuevo no aplica las migraciones una por una: aplica el
archivo base. Si alguien anade una migracion y no regenera ese archivo, los
colegios nuevos nacen con la estructura vieja pero heredan el historial de la
plantilla: declaran tener algo que no tienen, y nada lo delata hasta que una
consulta usa lo que falta.

Esta prueba cierra ese hueco. Si falla, ejecuta:

    python scripts/generar_esquema_base.py --schema tenant_colegio_1

despues de haber aplicado la migracion nueva a ese schema.
"""
from pathlib import Path

from app.controllers.super_admin_controller import ESQUEMA_BASE_TENANT


RAIZ = Path(__file__).resolve().parents[1]
DIRECTORIO_MIGRACIONES = RAIZ / "migrations"

INICIO = "-- MIGRACIONES INCORPORADAS"
FIN = "-- FIN MIGRACIONES INCORPORADAS"


def declaradas_en_la_base():
    """Nombres que la cabecera del archivo base dice incorporar."""
    nombres = []
    dentro = False
    for linea in ESQUEMA_BASE_TENANT.read_text(encoding="utf-8").splitlines():
        if linea.startswith(FIN):
            break
        if dentro:
            nombres.append(linea.removeprefix("--").strip())
        elif linea.startswith(INICIO):
            dentro = True
    return sorted(nombres)


def migraciones_de_tenant():
    """Los .sql directos de migrations/. Se excluye public/ y base/ a proposito:
    las publicas no van a un tenant y la base no se incluye a si misma."""
    return sorted(ruta.name for ruta in DIRECTORIO_MIGRACIONES.glob("*.sql"))


def test_el_archivo_base_declara_que_migraciones_incorpora():
    declaradas = declaradas_en_la_base()

    assert declaradas, (
        "La cabecera del archivo base no declara ninguna migracion. "
        "Regeneralo con scripts/generar_esquema_base.py."
    )


def test_la_base_incorpora_todas_las_migraciones_de_tenant():
    declaradas = set(declaradas_en_la_base())
    en_disco = set(migraciones_de_tenant())

    faltan = sorted(en_disco - declaradas)
    assert not faltan, (
        f"El archivo base no incorpora {len(faltan)} migracion(es): {faltan}. "
        "Aplicalas al schema de referencia y regenera la base con "
        "scripts/generar_esquema_base.py."
    )


def test_la_base_no_declara_migraciones_que_ya_no_existen():
    declaradas = set(declaradas_en_la_base())
    en_disco = set(migraciones_de_tenant())

    sobran = sorted(declaradas - en_disco)
    assert not sobran, (
        f"El archivo base declara {len(sobran)} migracion(es) que no estan en "
        f"migrations/: {sobran}. żSe renombro o borro alguna?"
    )


def test_la_base_no_se_declara_a_si_misma_ni_incluye_las_publicas():
    declaradas = declaradas_en_la_base()

    assert ESQUEMA_BASE_TENANT.name not in declaradas
    publicas = {ruta.name for ruta in (DIRECTORIO_MIGRACIONES / "public").glob("*.sql")}
    assert not (set(declaradas) & publicas)


def test_el_archivo_base_sigue_siendo_aplicable():
    """Guardas minimas de contenido: sin esto la cabecera podria estar bien y el
    cuerpo vacio."""
    contenido = ESQUEMA_BASE_TENANT.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS" in contenido
    assert "ADD CONSTRAINT" in contenido
    assert "FOREIGN KEY" in contenido
    assert "SERIAL" in contenido
    # Nombres sin cualificar: el schema destino lo pone el search_path.
    assert "tenant_colegio_1." not in contenido
