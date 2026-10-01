"""La fecha de hoy en Colombia, sin importar la zona del servidor.

Render corre en UTC, cinco horas por delante de Bogota. `date.today()` da la
fecha del servidor, asi que cada noche desde las 7 p. m. respondia con la de
mañana: el 2026-09-30 a las 22:50 de Bogota, produccion ya contaba vencida la
cuota de octubre y el backend local no. Ver "Hallazgos fuera de alcance" en
docs/funcionalidades/ANIO_LECTIVO.md.

Quien necesite "hoy" para una regla del colegio usa `hoy_en_colombia()`.
"""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


ZONA_HORARIA_COLOMBIA = ZoneInfo("America/Bogota")


def _ahora_utc() -> datetime:
    """El reloj, aparte para que las pruebas puedan fijarlo."""
    return datetime.now(timezone.utc)


def hoy_en_colombia() -> date:
    return _ahora_utc().astimezone(ZONA_HORARIA_COLOMBIA).date()
