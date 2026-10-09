from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.controllers.anios_lectivos_controller import (
    AnioLectivoActivoInexistenteError,
    AnioLectivoDestinoInvalidoError,
    AnioLectivoEnPreparacionError,
    AnioLectivoSiguienteExistenteError,
    CandidatosMatriculaInvalidosError,
    ConfiguracionAnioDuplicadaError,
    ConfiguracionAnioInconsistenteError,
    CursoMatriculaInvalidoError,
    ValoresEspecialesInconsistentesError,
    copiar_configuracion_anio_controller,
    crear_estudiante_en_preparacion_controller,
    crear_anio_lectivo_controller,
    guardar_decision_salida_controller,
    listar_candidatos_matricula_controller,
    listar_anios_lectivos_controller,
    promover_estudiantes_controller,
    resumen_anio_preparacion_controller,
    vista_previa_activacion_controller,
)
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas.anio_lectivo import (
    CopiarConfiguracionAnio,
    DecisionSalidaEstudiantes,
    PromocionEstudiantes,
)
from app.schemas.estudiante import EstudianteCreate
from app.services.anio_lectivo import AnioLectivoInexistenteError

# Admin y profesor: el admin ve todos los años y el profesor solo el activo.
# La regla vive en el servicio; aqui solo se exige sesion.
router = APIRouter(tags=["Años lectivos"], dependencies=[Depends(get_current_user)])


@router.get("/anios-lectivos")
def listar_anios_lectivos(current_user: dict = Depends(get_current_user)):
    """Años lectivos con su estado, el mas reciente primero."""
    return listar_anios_lectivos_controller(current_user)


@router.post(
    "/anios-lectivos",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_admin)],
)
def crear_anio_lectivo():
    """Crea N+1 en preparación; el cliente no elige el número del año."""
    try:
        return crear_anio_lectivo_controller()
    except (
        AnioLectivoActivoInexistenteError,
        AnioLectivoEnPreparacionError,
        AnioLectivoSiguienteExistenteError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.post(
    "/anios-lectivos/{anio_lectivo_id}/copiar-configuracion",
    dependencies=[Depends(get_current_active_admin)],
)
def copiar_configuracion_anio(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    opciones: CopiarConfiguracionAnio,
):
    """Copia al N+1 en preparación; todo se confirma o se revierte junto."""
    try:
        return copiar_configuracion_anio_controller(anio_lectivo_id, opciones)
    except AnioLectivoInexistenteError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
        ConfiguracionAnioDuplicadaError,
        ConfiguracionAnioInconsistenteError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


def _traducir_error_matricula(exc):
    if isinstance(exc, AnioLectivoInexistenteError):
        codigo = status.HTTP_404_NOT_FOUND
    else:
        codigo = status.HTTP_409_CONFLICT
    raise HTTPException(status_code=codigo, detail=str(exc)) from exc


@router.get(
    "/anios-lectivos/{anio_lectivo_id}/resumen",
    dependencies=[Depends(get_current_active_admin)],
)
def resumen_anio_preparacion(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
):
    """Resume la preparación financiera del siguiente año lectivo."""
    try:
        return resumen_anio_preparacion_controller(anio_lectivo_id)
    except (
        AnioLectivoInexistenteError,
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
    ) as exc:
        _traducir_error_matricula(exc)


@router.get(
    "/anios-lectivos/{anio_lectivo_id}/activacion/vista-previa",
    dependencies=[Depends(get_current_active_admin)],
)
def vista_previa_activacion(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
):
    """Muestra qué pasaría al activar el año en preparación, sin cambiar nada."""
    try:
        return vista_previa_activacion_controller(anio_lectivo_id)
    except (
        AnioLectivoInexistenteError,
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
    ) as exc:
        _traducir_error_matricula(exc)


@router.get(
    "/anios-lectivos/{anio_lectivo_id}/matriculas/candidatos",
    dependencies=[Depends(get_current_active_admin)],
)
def listar_candidatos_matricula(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    curso_origen_id: Annotated[int, Query(gt=0)],
):
    """Lista el curso activo para seleccionar quién pasa al siguiente año."""
    try:
        return listar_candidatos_matricula_controller(
            anio_lectivo_id, curso_origen_id
        )
    except (
        AnioLectivoInexistenteError,
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
        CursoMatriculaInvalidoError,
    ) as exc:
        _traducir_error_matricula(exc)


@router.post(
    "/anios-lectivos/{anio_lectivo_id}/matriculas/promocion",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_admin)],
)
def promover_estudiantes(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    datos: PromocionEstudiantes,
):
    """Matricula únicamente los estudiantes seleccionados por el admin."""
    try:
        return promover_estudiantes_controller(anio_lectivo_id, datos)
    except (
        AnioLectivoInexistenteError,
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
        CursoMatriculaInvalidoError,
        CandidatosMatriculaInvalidosError,
        ValoresEspecialesInconsistentesError,
    ) as exc:
        _traducir_error_matricula(exc)


@router.put(
    "/anios-lectivos/{anio_lectivo_id}/matriculas/salida",
    dependencies=[Depends(get_current_active_admin)],
)
def guardar_decision_salida(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    datos: DecisionSalidaEstudiantes,
):
    """Marca o desmarca quién no sigue en el año en preparación."""
    try:
        return guardar_decision_salida_controller(anio_lectivo_id, datos)
    except (
        AnioLectivoInexistenteError,
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
        CandidatosMatriculaInvalidosError,
    ) as exc:
        _traducir_error_matricula(exc)


@router.post(
    "/anios-lectivos/{anio_lectivo_id}/estudiantes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_admin)],
)
def crear_estudiante_en_preparacion(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    est: EstudianteCreate,
):
    """Crea un estudiante con matrícula solo en el año en preparación."""
    try:
        return crear_estudiante_en_preparacion_controller(anio_lectivo_id, est)
    except (
        AnioLectivoInexistenteError,
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
        CursoMatriculaInvalidoError,
    ) as exc:
        _traducir_error_matricula(exc)
