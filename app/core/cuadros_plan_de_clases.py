"""Los cuadros del plan de clase que un colegio puede renombrar.

Ver `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`. Sin base de datos y sin
HTTP: el controlador llama a estas funciones y luego lee o escribe.

**Aqui viven las claves, no los nombres.** Los nombres y las ayudas
originales son textos de pantalla y viven en el frontend
(`src/utils/planeaciones/cuadros.js`); la tabla `plan_de_clases_cuadros` guarda
solo los que el colegio cambio. Asi, si la lectura falla, el profesor sigue
planeando con los originales.

Las claves son los campos del plan y de sus dos archivos. **Una clave nunca se
reutiliza ni cambia de significado**: los nombres guardados la usan.
`competencias` no esta: ya no se escribe en el formulario y solo aparece en
planes viejos, con su nombre fijo.
"""


CUADROS_DE_TEXTO = (
    "unidad",
    "estandar",
    "tema",
    "proposito",
    "clase",
    "dba",
    "actividad_casa",
)
CUADROS_DE_ARCHIVO = ("imagen1", "imagen2")

CLAVES = CUADROS_DE_TEXTO + CUADROS_DE_ARCHIVO
"""En el orden del formulario del profesor: asi se devuelven."""

LARGO_NOMBRE = 60
LARGO_AYUDA = 150

CLAVE_DESCONOCIDA = "Ese cuadro no existe en el plan de clase."
CLAVE_REPETIDA = "Un cuadro aparece dos veces."
NOMBRE_VACIO = "Cada cuadro necesita un nombre."
NOMBRE_LARGO = f"El nombre de un cuadro no puede pasar de {LARGO_NOMBRE} caracteres."
AYUDA_LARGA = f"El texto de ayuda no puede pasar de {LARGO_AYUDA} caracteres."
AYUDA_EN_ARCHIVO = "Los archivos no llevan texto de ayuda."


def motivo_para_rechazar(cuadros):
    """`None` si la lista se puede guardar; si no, el mensaje del primer error.

    `cuadros` son tuplas `(clave, nombre, ayuda)` ya recortadas. Que dos
    cuadros no se llamen igual no se revisa aqui: el backend solo ve los
    renombrados, y eso lo cuida la ventana del admin, que ve los nueve.
    """
    vistas = set()
    for clave, nombre, ayuda in cuadros:
        if clave not in CLAVES:
            return CLAVE_DESCONOCIDA
        if clave in vistas:
            return CLAVE_REPETIDA
        vistas.add(clave)
        if not nombre:
            return NOMBRE_VACIO
        if len(nombre) > LARGO_NOMBRE:
            return NOMBRE_LARGO
        if len(ayuda) > LARGO_AYUDA:
            return AYUDA_LARGA
        if ayuda and clave in CUADROS_DE_ARCHIVO:
            return AYUDA_EN_ARCHIVO
    return None


def en_orden_del_formulario(cuadros):
    """Los cuadros `(clave, nombre, ayuda)` en el orden de `CLAVES`, como dicts.

    Una clave que ya no este en `CLAVES` (una fila vieja de la tabla) se
    descarta: no hay cuadro donde mostrarla.
    """
    posicion = {clave: indice for indice, clave in enumerate(CLAVES)}
    conocidos = [cuadro for cuadro in cuadros if cuadro[0] in posicion]
    return [
        {"clave": clave, "nombre": nombre, "ayuda": ayuda}
        for clave, nombre, ayuda in sorted(conocidos, key=lambda c: posicion[c[0]])
    ]
