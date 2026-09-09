# Cambios Backend

Ultima revision documental: 2026-09-08.

## Proposito

Bitacora de cambios documentales y tecnicos observables del backend.

## 2026-09-08 - Observador unificado, fase 3: escribir y editar

`POST /observador` y `PUT /observador/{anotacion_id}`. Con esto **el backend de
la funcionalidad esta completo**. Sigue sin haber pantalla, asi que la bitacora
esta vacia y los profesores siguen usando la vieja: el fallo original sigue
vivo y lo cierra el frontend, no esto.

### El admin no crea, y esto corrigio una contradiccion del diseno

El documento decia dos cosas: su tabla de permisos daba a crear el mismo alcance
que a leer -lo que incluye al admin- y su tabla de API decia «profesor del
alumno». Se resolvio a favor de la segunda, con motivo:

**el `id` de un admin sale de la tabla `usuarios`, no de `profesor`.** Usarlo
como autor firmaria la anotacion con el profesor que por casualidad tenga ese
mismo numero. Se comprobo antes de decidir: en `tenant_colegio_1` la
administradora **maristella polo** tiene `usuarios.id = 1` y el profesor 1 es
**SINDY PAOLA VERGARA**. La anotacion habria quedado a nombre de Sindy Paola,
sin error, sin aviso y sin forma de notarlo despues.

Una bitacora que atribuye a alguien lo que no escribio no sirve para lo unico
que justifica su existencia. Lo impide `_profesor_que_escribe`, con prueba.

Se suma al invariante 3, que ya prohibia al admin **editar** lo de un profesor.
Ese sigue siendo una excepcion deliberada a la norma del proyecto -casi todos
los guards empiezan con `if rol == "admin": return`- y tiene su propia prueba,
que el documento pedia explicitamente.

### La autoria se comprueba en la sentencia que escribe

`UPDATE ... WHERE id = %s AND profesor_id = %s`. No hay un `SELECT` previo que
compruebe y luego un `UPDATE` que escriba: es la misma sentencia, sin ventana
entre las dos cosas, y el camino normal cuesta **una sola consulta**.

Cuando no actualiza nada se paga una segunda, **solo en el camino de error**,
para no decir «no es tuya» de algo que no existe ni «no existe» de algo que si.
De ahi que haya `403` y `404` distintos.

`editada_en` y `editada_por` se fijan en esa misma sentencia, no en el codigo
que la llama: el rastro no depende de que alguien se acuerde. Es el invariante 2.

### El texto se guarda ya corregido

Decidido con el usuario. `app/core/texto_observador.py` pone mayuscula en la
primera letra y despues de `.`, `?` y `!` -no despues de `,`, `;` ni `:`-,
colapsa espacios y anade el que falta tras el punto.

Vive en el servidor **ademas de** en el frontend: alli es comodidad, aqui es la
garantia. La profesora ve la correccion al salir del campo y puede rehacerla,
asi que lo que aprueba con los ojos es lo que queda escrito y lo que se imprime.

Dos detalles que costaron una vuelta:

- **`¿por que?` se quedaba en minuscula.** La primera letra no siempre es el
  primer caracter: en castellano la frase abre con `¿` o `¡`. Se corrigio
  buscando la primera letra, no el primer caracter, y lo mismo tras cada punto.
- **`mide 1.75 metros` no se toca.** El espacio tras el punto solo se anade si
  lo que sigue empieza frase de verdad, no si es un digito.

Defecto conocido y aceptado: `etc. y luego` -> `etc. Y luego`. Es raro en una
observacion, todos los sistemas que hacen esto lo tienen, y se ve en pantalla
antes de guardar.

### Probado de extremo a extremo contra la base real

Dentro de una transaccion deshecha al final, con un caso real de `tenant_2005`
-MARIA VICTORIA, de TRANSICION-A, preescolar-:

| Comprobacion | Resultado |
|---|---|
| La profesora crea una anotacion | OK |
| El admin NO puede crear | `403` |
| **La misma profesora anota otra vez en el mismo periodo** | OK, y quedan las dos |
| Leer de vuelta | 2 anotaciones, la mas nueva primero, `nivel='preescolar'` |
| El texto quedo corregido | `Se para mucho. Hace desorden` |
| Filtrar por un periodo vacio | 0 anotaciones y **el nivel sigue llegando** |
| La autora edita la suya | OK |
| El ADMIN edita lo de la profesora | `403` |
| Otro profesor edita lo ajeno | `403` |
| Editar una que no existe | `404` |
| El rastro | `editada_en` con fecha, `editada_por = 40` |

Tras el rollback, cero filas en los dos tenants.

La tercera fila es la que cierra el motivo de todo esto: **la tabla vieja no
podia hacerlo**. Su `UNIQUE (estudiante_id, asignacion_id, periodo)` y su
`UPSERT` hacian que el segundo guardado borrara el primero.

### Pruebas

`1252 pasan`. Veintinueve nuevas en `tests/test_observador_escritura.py`,
verificadas con mutaciones: meter el atajo de admin, quitar el rastro de
edicion, sacar la autoria del `WHERE`, convertir el `INSERT` en `UPSERT`, quitar
la correccion de mayusculas, quitar el rango del periodo, permitir la anotacion
vacia y confundir el `404` con el `403`. Todas cayeron.

Se borro `test_no_existe_ninguna_forma_de_borrar_una_anotacion` de
`test_observador_lectura.py`: afirmaba que el router era «solo lectura» y quedo
obsoleta al aparecer el `POST`. El invariante 1 -nadie borra- lo fija ahora
`test_no_existe_endpoint_de_borrado`, en el archivo de escritura, que ademas
comprueba que el repositorio no sabe borrar.

### Qué cambia para el cliente

Dos rutas nuevas. Ninguna existente cambia.

## 2026-09-08 - La materia del observador no se rellena, y el porque

Cambio de decision el mismo dia en que se creo la columna. Se registra entero
porque el recorrido vale mas que la conclusion, y porque deja una columna vacia
en la base que alguien podria confundir con un descuido.

**No lo es.** `observador_anotaciones.materia` existe, esta migrada en los dos
tenants y se queda **vacia a proposito**.

### Lo que la tumbo fue una medicion

Para etiquetar una anotacion con su materia hay que saber cual es. Se midio si
el servidor podia deducirla a partir del profesor y el alumno:

| Materias que da un profesor en un mismo curso | `tenant_2005` | `tenant_colegio_1` |
|---|---|---|
| Una sola, deducible | 9 casos, **27%** | 1 caso, **25%** |
| Varias, ambiguo | 24 casos, **73%** | 3 casos, **75%** |

LILIANA da **9** materias en PRIMERO-A. ANGELICA, **5** en JARDIN-B. No es un
caso de borde: es la norma. **El servidor no puede deducirla**, y no es cuestion
de programarlo mejor.

### Las dos salidas, y por que se descartaron las dos

- **Que la profesora elija** la materia al guardar: friccion en cada anotacion,
  para un dato secundario.
- **Deducirla de la asignacion desde la que entra** —su planilla de
  Matematicas—: sin friccion, pero **ata la pagina a una unica puerta de
  entrada**. El observador dejaria de poder abrirse desde un listado de alumnos,
  y esa puerta todavia no esta decidida.

Decision del usuario: **ninguna de las dos, por ahora**. La pantalla mostrara el
nivel del curso en el titulo -«Pepito · Primaria»- y las anotaciones iran solo
con profesora, fecha y periodo.

### Consecuencias, dichas claro

- **No queda registrado en que clase paso.** Se acepto a conciencia; el nombre
  de la profesora sigue diciendo quien observo.
- El `POST` de la fase 3 **no recibe `asignacion_id` ni `materia`**. Eso lo
  simplifica: le basta `require_estudiante_access`, el mismo guard de la
  lectura.
- La columna se conserva. Quitarla exigiria otra migracion y no gana nada;
  dejarla cuesta cero y queda lista si algun dia se decide usarla.
- `GET /observador/{estudiante_id}` **sigue devolviendo `materia`** en cada
  anotacion, con la cadena vacia. Es el valor real de la fila, no un adorno: la
  respuesta no miente sobre lo que hay guardado.
- Lo que **si** se aprovecha es el `nivel` anadido antes: ahora es lo unico que
  la pantalla pone tras el nombre del alumno, asi que aquel trabajo no se tira.

### Codigo

Ninguno. Nada que revertir: la escritura todavia no existe, asi que no habia una
sola linea que rellenara la columna. `1224 pasan`, sin cambios en pruebas.

## 2026-09-08 - La lectura del observador devuelve el nivel del curso

Añadido justo después de cerrar la fase 2, por una decisión de presentación: la
pantalla mostrará la materia **según el nivel** —preescolar la omite y dice el
nivel una vez en el título, primaria la lleva en cápsula, y un curso **sin
nivel** se comporta como primaria—. El detalle vive en el documento de frontend.

### La consulta arranca en `estudiantes`, y ese es todo el cambio

Antes arrancaba en `observador_anotaciones`. Ahora:

```sql
FROM estudiantes e
LEFT JOIN cursos c ON c.id = e.curso_id
LEFT JOIN observador_anotaciones a ON a.estudiante_id = e.id
                                  [AND a.periodo = %s]
LEFT JOIN profesor p ON p.id = a.profesor_id
WHERE e.id = %s
```

Tres trampas, las tres reales, las tres con prueba y mutación:

1. **Un alumno sin anotaciones.** Arrancando en las anotaciones devolvería cero
   filas y con ellas ningún nivel: la pantalla no podría ni escribir su título.
   No es un caso raro — **hoy es el caso de todos los alumnos**, porque la
   escritura no existe.
2. **`estudiantes.curso_id` es nulable**, comprobado en `information_schema`.
   Con unión interna a `cursos`, un alumno sin curso desaparecería de su propia
   bitácora: sin error y sin aviso.
3. **El filtro de periodo va en el `ON`, no en el `WHERE`.** En el `WHERE`
   descartaría también la fila del estudiante cuando ese periodo no tuviera
   anotaciones, y cambiar de periodo dejaría la pantalla sin nivel.

Las dos uniones nuevas **no cuestan idas y vueltas**: sigue siendo una sola
consulta, y hay prueba que cuenta las sentencias para que siga siéndolo.

### La respuesta cambia de forma, y el `404` es nuevo

De una lista a `{"nivel": ..., "anotaciones": [...]}`. El nivel va fuera porque
es del alumno, no de cada anotación, y sobre todo **porque tiene que llegar
aunque no haya ninguna**. No rompe a nadie: todavía no hay cliente.

Cero filas solo puede significar que el estudiante no existe, así que la ruta
responde `404`. Un alumno real sin anotaciones trae una fila de relleno con el
nivel y el resto en `NULL`, que la ruta descarta. La diferencia importa: en
pantalla, «no existe» y «todavía nadie le ha escrito» son mensajes distintos.

`leer_anotaciones` pasa a llamarse `leer_bitacora`: ya no devuelve solo
anotaciones.

### Medido contra la base real

Con casos reales de `tenant_2005`, ambos con la bitácora vacía:

| Caso | Tiempo | Resultado |
|---|---|---|
| Alumno de PARVULO (preescolar), todos los periodos | 1374 ms (abre conexión) | `nivel='preescolar'`, 0 anotaciones |
| El mismo, filtrando por periodo 3 | 618 ms | `nivel='preescolar'`, 0 anotaciones |
| Alumno de PRIMERO-A (primaria) | 607 ms | `nivel='primaria'`, 0 anotaciones |
| Estudiante inexistente, como admin | 529 ms | `404` |

La segunda fila es la que importa: **el nivel llega con el filtro de periodo
puesto y sin ninguna anotación**, que es justo lo que la trampa 3 rompía.

El camino del alumno **sin curso** no lo cubre ningún dato real —no hay ninguno
en ese tenant—, así que se protege fijando en una prueba que las uniones sean
`LEFT`. Es la regresión probable: alguien reordena la consulta y borra la
palabra.

### Pruebas

`1224 pasan`. Veintiuna en `tests/test_observador_lectura.py`, siete más que
antes. Verificadas con mutaciones: mover el filtro de periodo al `WHERE`, quitar
el `404`, dejar pasar la fila de relleno, perder el nivel y convertir cada
`LEFT JOIN` en interna. Todas cayeron.

## 2026-09-08 - Observador unificado, fase 2: la lectura

`GET /observador/{estudiante_id}` devuelve la bitácora completa de un alumno.
**Solo lectura**: no hay `POST` ni `PUT` todavía, y `DELETE` no existirá nunca.
La pantalla vieja no se toca y sigue siendo la única que los profesores usan.

### Una consulta y una conexión, que es el punto

La pantalla vieja hace **una petición HTTP por alumno**: con 12 tarda 16-20 s y
el frontend aborta a los 10 s. Aquí se abre **un** estudiante y su bitácora
entera sale de **una consulta**, con el guard corriendo sobre el mismo cursor
que después lee. El N+1 desaparece por diseño, no por optimización.

Hay dos pruebas que lo fijan por aserción y no por comentario: que se pide una
sola conexión al pool y que los guards no abren la suya. Si alguien vuelve a
partirlo en dos consultas, fallan.

### `require_estudiante_access` acepta `cursor=`

Replica lo que la optimización del 2026-09-03 hizo con `require_asignacion_access`
y `require_estudiante_in_asignacion`. Sin `cursor` conserva el comportamiento
histórico, así que los tres llamadores de `app/routes/notas.py` no cambian y sus
pruebas siguen pasando sin tocarlas.

Prestar el cursor **no relaja el permiso**: misma consulta, mismos parámetros,
mismo 403.

### La materia: una contradicción entre los dos documentos

El documento de frontend dibuja «Prof. Ana · Matemáticas · 20/mar». El de
backend había quitado la materia de la tabla. Nadie lo había cruzado. Decidido
con el usuario: la anotación **sí** dice de qué materia era.

`migrations/20260908_observador_anotaciones_materia.sql` añade la columna. Va
aparte porque la primera migración ya estaba aplicada y el runner bloquea un
archivo cuyo checksum cambie.

Es **texto copiado**, no una clave foránea a `materias(id)`: un vínculo
reintroduciría el defecto que esta tabla vino a corregir —quitar la materia del
horario se llevaría el dato— y además obligaría a una unión más en cada lectura.

Nadie la rellena todavía: eso es la fase 3, y **de dónde sale al guardar sigue
sin decidirse**. Queda como pregunta abierta que bloquea esa fase.

### Seis censos que había que actualizar a mano

El repositorio nuevo hizo fallar siete pruebas, y todas tenían razón:

- cinco enumeran el conjunto exacto de repositorios (`asistencia`, `dashboard`,
  `notas`, `planilla`, `ventas`), a propósito, para que ninguno se cuele sin
  reconocerse;
- una enumera los archivos que tocan la tabla `profesor` por SQL directo. El
  repositorio nuevo la une **solo** para el nombre que muestra la bitácora, en
  la misma consulta de lectura;
- `test_esquema_base` pide regenerar el archivo base tras la migración nueva.

Ninguna se relajó: todas se actualizaron declarando la pieza nueva.

### Pruebas

`1216 pasan` con la migración de `materia` aplicada. Catorce nuevas en
`tests/test_observador_lectura.py`, verificadas con mutaciones: quitar el
`except HTTPException`, dar al guard su propia conexión, filtrar el error de
PostgreSQL al cliente, quitar el desempate del orden y filtrar siempre por
periodo. Las cinco cayeron.

Una sexta mutación —aceptar la cadena vacía en el apellido— **no** cayó, y eso
destapó un hueco real: la prueba cubría el apellido nulo pero no el vacío. Se
amplió a los dos casos y entonces sí cae.

### Medido contra la base real, no estimado

Ejecutando la funcion de la ruta contra Neon con un caso real de `tenant_2005`
—profesor 40, estudiante 518—, con la bitacora todavia vacia:

| Llamada | Tiempo |
|---|---|
| Profesor del alumno, todos los periodos (primera, abre conexion) | 1147 ms |
| El mismo, filtrando por periodo | 593 ms |
| Admin, sin compartir curso | 445 ms |
| Rol no autorizado, `403` | 412 ms |

Los ~450-600 ms en caliente son el suelo de este proyecto: arranque de conexion
mas dos o tres idas y vueltas a ~180 ms cada una.

**La medicion NO incluye el sobrecoste de autenticacion**, porque llama a la
funcion de la ruta y no pasa por `get_current_user`. Una peticion HTTP real suma
las 6 idas y vueltas documentadas el 2026-09-03, o sea alrededor de 1,1 s mas.
Eso sigue siendo un defecto transversal, con su propio alcance, y esta
funcionalidad no lo toca.

Aun asi la comparacion decide: la pantalla vieja hace **12 peticiones** de ~2,8 s
para un curso y suma 16-20 s. Esta hace **una**. Lo que cambia no es el precio de
cada peticion sino cuantas hay, que era la conclusion de la medicion del
2026-09-03.

### El JOIN es interno a propósito

`profesor_id` es `NOT NULL` y su clave foránea no lleva `ON DELETE CASCADE` ni
`SET NULL`, así que PostgreSQL **impide** borrar un profesor con anotaciones. La
fila siempre existe. Dar de baja a un profesor en esta aplicación es cambiarle
el `estado`, no borrarlo, y eso no afecta a nada de aquí.

### Qué cambia para el cliente

Una ruta nueva. Ninguna existente cambia de comportamiento, código de estado ni
cuerpo.

## 2026-09-08 - Observador unificado, fase 1: la tabla existe y nadie la usa

Estructura y nada más. Se crea `observador_anotaciones` en los dos tenants
operativos. **No hay endpoint ni pantalla**: nada lee ni escribe esa tabla, y la
pantalla vieja del observador sigue siendo la única que los profesores usan. El
fallo «No pudimos recuperar la observación guardada» **sigue vivo**: lo cierra la
fase 2, no esta.

Diseño completo y decisiones en `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`.

### Qué se creó

`migrations/20260908_observador_anotaciones.sql`, aplicada con el runner:

| Tenant | Migración | Índice | Filas | `observaciones` (vieja) |
|---|---|---|---|---|
| `tenant_colegio_1` | OK | OK | 0 | 5, intacta |
| `tenant_2005` | OK | OK | 0 | 63, intacta |

La tabla vieja no se tocó y **no se toca**: se jubila cuando lo nuevo funcione,
y ni entonces se borra.

### El índice va en el script, no en la migración

El plan decía crearlo en la migración **y** en `scripts/apply_tenant_indexes.py`.
Se comprobó contra la base antes de hacerlo y habría creado un duplicado en cada
tenant: el script antepone el nombre del schema (`f"{schema}_{index_name}"`), así
que no habría reconocido el `idx_...` de la migración —`CREATE INDEX IF NOT
EXISTS` compara por **nombre**, no por definición— y habría creado otro idéntico
al lado.

No es hipotético. `tenant_2005` ya arrastra tres pares duplicados por esa causa:

```
asistencia_estudiante_id_fecha_idx      +  tenant_2005_idx_asistencia_estudiante_fecha
asistencia_asignacion_id_periodo_idx    +  tenant_2005_idx_asistencia_asignacion_periodo
estudiantes_curso_id_idx                +  tenant_2005_idx_estudiantes_curso_id
```

Decidido con el usuario: el índice lo crea **solo** `apply_tenant_indexes.py`, y
el archivo base lo hereda al regenerarse. La tabla nueva queda con exactamente
dos índices por tenant —su clave primaria y el suyo—, sin duplicados.

Queda anotado como **deuda, sin prisa**: el prefijo por schema de
`apply_tenant_indexes.py` es lo que produce esos duplicados, y los tres pares de
`tenant_2005` siguen ahí. Limpiarlos exige su propio alcance.

### Lo que se midió antes de tocar producción

Ensayo en los dos tenants: crear tabla e índice dentro de una transacción y
deshacerla. Confirmó que las claves foráneas resuelven contra `estudiantes` y
`profesor`, que no hay `CASCADE` ni `UNIQUE`, y que un `periodo = 99` rebota. Al
terminar, la tabla no existía en ningún schema.

No se usó una rama de Neon, que es lo que pide `docs/MIGRACIONES.md` paso 2. Para
una migración puramente aditiva el ensayo transaccional cubrió lo mismo. Si
alguna vez la migración altera datos, la rama deja de ser opcional.

### Pruebas

`1199 pasan`. Nueve nuevas en `tests/test_migracion_observador_anotaciones.py`,
verificadas con mutaciones —meter `CASCADE`, quitar un `NOT NULL`, aflojar el
`CHECK`, meter `UNIQUE`, meter `asignacion_id`, meter el índice en la
migración—: las seis cayeron, cada una en una sola prueba.

Una existente cambió: `test_ddl_fija_unicidad_estado_y_tres_referencias_externas`
contaba las referencias a `profesor(id)` en el archivo base y exigía 3. La tabla
nueva añade dos —el autor y quien editó—, así que son 5. Se actualizó declarando
las dos nuevas explícitamente, no solo subiendo el número, porque el valor de esa
prueba no es el número sino obligar a mirar cada referencia nueva y decidir a
propósito si arrastra borrados. Las dos nuevas **no** llevan `ON DELETE CASCADE`.
Renombrada a `test_ddl_fija_unicidad_estado_y_las_referencias_externas`, que no
envejece con la siguiente tabla.

### Tropiezo operativo, por si vuelve

`apply_migration.py` **se niega** sobre el endpoint agrupado de Neon
(`-pooler`), que es justo el que trae `.env`: allí su cerrojo de sesión no impide
dos ejecuciones simultáneas. Hay que apuntar `DATABASE_URL` al endpoint directo
—el mismo host sin `-pooler`— solo para ese comando. Está en
`docs/MIGRACIONES.md`, pero se olvida.

### Qué cambia para el cliente

**Nada.** Ni una ruta, ni un código de estado, ni un cuerpo de respuesta. La
tabla nace vacía y ningún camino de código la menciona.

## 2026-09-03 - Lectura de observaciones: una conexión en vez de tres, y caché de columnas

Trabajo previo al arreglo del observador del estudiante. **No lo cierra**, y el
apartado final explica por qué se registra igual.

Origen: el observador mostraba «No pudimos recuperar la observación guardada» en
el perfil de profesor. El mensaje viene del frontend, que aborta la petición a
los **10 segundos** (`useObservacionEstudiante.js`), así que no indicaba un
fallo del backend sino una respuesta que llegaba tarde.

### Lo que se midió, antes de tocar nada

Contra la base real (Neon, `us-east-1`) desde un backend local, y contra el
endpoint autenticado real con un token acuñado para el caso reportado
—`PARVULO`/`ARTÍSTICA`, asignación 131, 12 estudiantes, periodo 3—:

| Medición | Resultado |
|---|---|
| Abrir una conexión nueva (TLS + auth) | **1329 ms** |
| Una ida y vuelta cualquiera (`SELECT 1`) | **~180 ms** |
| `information_schema.columns` | **178 ms** |
| `GET /observaciones/...` una sola | **2,4 – 2,8 s** |
| Las 12 del curso **en paralelo** | **14,4 – 20,3 s**, todas con `http=200` |
| Las 12 **en una sola consulta** | **162 ms** |

Tres conclusiones, todas con evidencia:

1. **El endpoint no falla: llega tarde.** Las doce respuestas fueron `200`. El
   frontend se rinde a los 10 s y muestra el aviso.
2. **El coste no está en las consultas sino en su número.** Una lectura hacía
   **17 idas y vueltas** y solo **2** leían datos del dominio. Las otras 15 son
   validación de identidad y arranque de conexión. A ~180 ms cada una, el suelo
   eran ~3 s por estudiante.
3. **Ninguna consulta es lenta por sí misma.** `information_schema.columns`
   tarda lo mismo que `SELECT 1`. Lo que pesa es la distancia a la base, no el
   plan de ejecución.

El reparto de las 17 idas y vueltas, por si vuelve a hacer falta:

| Paso | Conexiones | Consultas |
|---|---|---|
| `ensure_tenant_allowed_for_app` | 1 | 3 |
| `_validar_usuario_en_bd` | 1 | 4 |
| `require_asignacion_access` | 1 | 3 |
| `require_estudiante_in_asignacion` | 1 | 3 |
| `get_cursor` + resolver + lectura | 1 | 4 |
| **Total** | **5** | **17** |

Cada apertura de conexión cuesta además dos consultas de arranque —`SET
search_path` y `set_config` de los timeouts— antes de la útil.

### Lo que cambió

- **`app/dependencies.py`**: `_columnas_tabla` cachea el resultado por
  `(schema del tenant, tabla)`. Se ejecutaba en **cada petición autenticada de
  toda la API**. La clave incluye el tenant porque dos colegios pueden ir con
  distinto nivel de migraciones; sin eso, el primero en pasar decidiría qué
  columnas cree tener el otro. Ahorra **una ida y vuelta (~180 ms) por
  petición**, no más: el comentario del módulo deja escrita la medición porque
  su primera versión afirmaba que esa vista era «de las lecturas más caras de
  PostgreSQL», que sonaba plausible y era **falso**. Se añade
  `limpiar_cache_columnas()` para migraciones en caliente; un despliegue
  reinicia el proceso y vacía el caché solo.
- **`app/core/permissions.py`**: `require_estudiante_in_asignacion` acepta
  `cursor=` opcional, replicando el que `require_asignacion_access` ya tenía.
  Sin él conserva el comportamiento histórico, así que los demás llamadores
  —`app/routes/boletines.py` y el `POST` de observaciones— no cambian.
- **`app/routes/observaciones.py`**: el `GET` corre los dos guards sobre el
  cursor que ya abre para leer. Pasa de **3 conexiones y 10 consultas a 1 y 6**.

### Qué cambia para el cliente

Nada observable. Mismos códigos de estado, mismo cuerpo, mismos mensajes. Lo
único que cambia es cuántas conexiones pide el proceso al pool.

Un matiz registrado: los guards ahora viven **dentro** del `try`, así que lo que
lancen y no sea `HTTPException` sale como 500 con su constante en vez de subir
crudo. Los guards reales solo lanzan `HTTPException` —y sigue saliendo con su
propio status, hay prueba—, así que en producción no cambia nada; un fallo de
base dentro de un guard ahora sale mejor formado, con `{"detail": ...}` y su
traza en el log.

Segundo matiz: si un guard deniega, el cursor **sí** se abre antes. No cuesta una
conexión de más, porque antes el propio guard abría la suya para consultar.

### Pruebas

`1190 pasan`. Tres se reescribieron a propósito y conviene saber por qué:

- `test_los_guards_se_evaluan_antes_de_abrir_el_cursor_en_la_lectura` fijaba el
  **orden textual** del código. Ese alambre hizo su trabajo: obligó a verificar
  qué protegía de verdad. No era el orden de las líneas sino dos garantías, y
  las dos se fijan ahora **por comportamiento**: que nada del dominio se lee sin
  permiso, y que **un 403 de un guard no se convierte en 500**. Comprobar el
  orden del texto ya no serviría: las tres llamadas viven en el mismo bloque.
- `test_obtener_observacion_no_consulta_si_el_guard_rechaza` usaba
  `PermissionError` como doble. Ningún guard lanza eso; los reales lanzan
  `HTTPException`. Se cambió al tipo real.
- Se añaden cuatro pruebas del caché, verificadas con una mutación —desactivando
  el caché a mano— para confirmar que fallan cuando deben y no pasan por vacías.

### Lo que NO se arregló, y es lo importante

**El aviso sigue saliendo.** Medido después del cambio: una lectura baja de
~3,1 s a ~2,8 s, un 10%. Con 12 alumnos en paralelo sigue en **16-20 s**.

La causa raíz no es el precio de cada petición sino **su cantidad**: el
observador hace **una petición HTTP por estudiante**. Es un N+1 sobre HTTP, y no
se corrige optimizando el 1.

Peor aún, el sistema quedó **justo encima de la raya de los 10 s**, y de qué lado
cae depende de la red en ese instante. Medido:

| En paralelo | Tiempo | ¿Pasa el límite de 10 s? |
|---|---|---|
| 1 | 2,8 s | sí |
| 2 | 8,1 – 9,7 s | sí, **por 0,3 s** |
| 3 | 11,2 – 14,7 s | no |
| 4 | 6,3 – 8,0 s | sí |
| 6 | 10,3 – 12,4 s | no |
| 12 | 16,2 – 20,1 s | no |

Que **4 en paralelo salga más rápido que 2** es el dato que más importa de esa
tabla: significa que manda la variación de la red, no la concurrencia. Un fallo
intermitente se da por cerrado y vuelve.

**No subir el timeout del frontend.** Cambiaría «sale un error» por «la página
tarda 20 segundos», que es peor: el profesor no sabe si está rota.

### Trabajo pendiente, no autorizado

- **Endpoint por asignación y periodo** que devuelva el curso entero:
  `GET /observaciones/{asignacion_id}/{periodo}`. Medido: **162 ms** la consulta.
  De 12 peticiones a 1, de ~20 s a ~2 s, y deja de crecer con el número de
  alumnos. No choca con la ruta actual: esa tiene tres segmentos, esta dos.
  Exige cambio de frontend a la vez —subir la carga a `ObservacionesPage`— y su
  propia orden. **Antes de diseñarlo hay que saber si el cambio previsto en
  observaciones altera qué dimensiones existen**; hoy son tres columnas fijas.
- **Sobrecoste de autenticación, que paga toda la API**: `ensure_tenant_allowed_for_app`
  y `_validar_usuario_en_bd` gastan **6 idas y vueltas y 2 conexiones por
  petición** solo en confirmar identidad. Es un defecto propio, ajeno a este
  dominio, y tocar autenticación exige su propio alcance.
- **`DB_POOL_MIN_CONNECTIONS` está en 1** y abrir una conexión cuesta 1329 ms,
  así que la primera ráfaga paga ese peaje en cascada. Subirlo es una línea, pero
  cambia el consumo de conexiones en Neon y merece decidirse aparte.

## 2026-08-27 - Endpoint de salud para monitoreo externo

- Se agregó `GET /health`, público y sin autenticación, porque un monitor
  externo no puede iniciar sesión. Es la única ruta abierta además de `login`.
- Responde `200` con `{"status": "ok", "database": "ok"}` cuando la API vive y
  PostgreSQL contesta, y `503` con `{"status": "degraded", "database": "error"}`
  cuando la base falla. Un monitor alerta ante cualquier código distinto de
  `200`, así que el aviso no necesita configuración adicional.
- El chequeo abre una conexión del pool, fija el tenant en `public` y ejecuta
  `SELECT 1`. No toca ningún schema de colegio ni cuenta filas.
- Cubre de una vez los dos fallos que dejan el sistema inservible aunque el
  proceso siga vivo: base inaccesible y pool agotado. `ThreadedConnectionPool`
  lanza `PoolError` en vez de esperar, así que `connection pool exhausted` —el
  incidente ya documentado en producción— llega al chequeo como excepción y
  activa la alerta.
- La respuesta no incluye versión, host ni detalle del error. El mensaje de
  `psycopg2` revela DSN y nombres internos, así que va solo al log del servidor
  con `logger.exception`.
- La ruta lleva límite explícito de `60/minute`. Es necesario porque el
  `default_limits=["100/minute"]` del limitador de `app/main.py` **no se está
  aplicando**: `slowapi` lo exige a través de `SlowAPIMiddleware`, que la app no
  monta, de modo que hoy solo quedan limitados los endpoints decorados. Ver el
  riesgo registrado más abajo.
- Archivos nuevos: `app/core/health.py` con el chequeo y `app/routes/health.py`
  con la ruta. El router se registra primero en `app/main.py` por ser
  infraestructura y no un dominio del colegio.
- No se agregaron columnas, tablas ni migraciones. No se modificó ningún
  endpoint existente.

Aviso operativo:

- **No usar `/health` como `Health Check Path` de Render.** Render reinicia el
  servicio cuando ese chequeo falla, así que un bache de la base provocaría
  reinicios en cadena y agravaría la caída. La ruta es para el monitor externo;
  el chequeo de la plataforma debe quedar vacío.

Riesgo detectado y no corregido:

- `default_limits=["100/minute"]` en `app/main.py` es inerte por falta de
  `SlowAPIMiddleware`. Hoy solo `POST /login` (`5/minute`) y `GET /health`
  (`60/minute`) están limitados de verdad; el resto de la API no tiene límite.
  No se corrigió aquí porque cambia el comportamiento observable de 139
  endpoints y excede el alcance de este cambio.

Verificación:

- 12 pruebas nuevas en `tests/test_health.py`, correctas. Cubren los dos status
  codes, el pool agotado, la ausencia de dependencias de autenticación, que el
  detalle del error no llegue al cuerpo pero sí al log, que la conexión vuelva
  al pool aunque la consulta falle y que el `ContextVar` del tenant quede
  restaurado.
- Compuerta global `python scripts/verify.py`: **1141 pruebas correctas**, Ruff
  correcto y `pip check` correcto, exit 0.
- `git diff --check` correcto.
- Sin PostgreSQL real: como el resto de la suite, la capa de datos va con
  dobles. La verificación contra la base queda para el despliegue.

## 2026-08-03 - Reporte académico parcial desde la planilla vigente

- Se agregó `GET /boletines/admin/reporte-parcial/{estudiante_id}/{periodo}`
  bajo la misma protección de administrador activo de los certificados.
- El endpoint consulta directamente `notas_detalle`; no usa ni prioriza
  `boletin_cabecera`, por lo que refleja cambios de la planilla incluso después
  de un envío anterior del boletín.
- Cada detalle conserva `descripcion`, nota, tipo de evaluación y valoración.
  La definitiva informativa se calcula únicamente con notas numéricas mayores
  que cero.
- No se modificó `/boletines/admin/generar`: el certificado y boletín oficial
  conservan su contrato anterior.
- No se agregaron tablas ni migraciones.

Verificación:

- 3 pruebas nuevas del controlador y la ruta correctas.
- Ruff correcto en controlador, ruta y pruebas.
- Suite completa fuera del sandbox: 189 pruebas correctas y 3 fallos
  preexistentes de Super Admin, cuyas fechas fijas de junio/julio de 2026 se
  evalúan como suspendidas frente a la fecha actual. No corresponden a
  boletines ni a este cambio.

## 2026-07-25 - Control de versión en el guardado del profesor

- `POST /plan-de-clases` acepta `version_esperada` en el multipart: `0` indica
  que el profesor abrió una fecha sin plan y un valor mayor que cero identifica
  la `version_revision` que cargó antes de editar.
- La versión se comprueba con bloqueo de fila dentro de la misma transacción
  del `UPSERT`. Si otra pestaña o dispositivo guardó primero, no se modifica el
  plan y se responde `409` con `version_actual`.
- La condición del `ON CONFLICT` también protege dos creaciones simultáneas
  para la misma asignación y fecha, incluso cuando ambas consultas iniciales
  todavía observaban la fecha vacía.
- Los clientes antiguos pueden omitir temporalmente `version_esperada` para
  mantener compatibilidad; el frontend del profesor ya lo envía siempre.
- Si el guardado es rechazado o falla después de subir imágenes nuevas, esos
  archivos se eliminan para no dejar evidencias huérfanas.
- El mensaje de éxito de planes ya revisados aclara que los cambios se
  guardaron conservando la revisión.
- No se agregaron columnas, tablas ni migraciones.

Verificación:

- Ruff correcto en rutas, controlador, servicio, repositorio, esquema y
  pruebas modificadas.
- 26 pruebas enfocadas de integridad y revisión correctas.

## 2026-07-24 - Ediciones de planes revisados no reabren la bandeja

- Cuando una planeación ya está en `revisado`, un nuevo guardado del profesor
  mantiene ese estado tenga o no observaciones administrativas.
- La misma regla se aplica si el profesor elimina una evidencia de imagen de
  esa planeación.
- La edición aumenta `version_revision`, conserva las fechas y responsables de
  seguimiento, pero no crea otra notificación administrativa ni devuelve el
  plan a la bandeja `pendiente`.
- Las correcciones en estado técnico `con_observaciones` mantienen el
  comportamiento existente.
- Solo los planes que administración todavía no ha revisado continúan en
  `pendiente` cuando el profesor los modifica.
- No se agregaron estados, tablas ni migraciones.

Verificación:

- Ruff correcto en el repositorio y las pruebas modificadas.
- 22 pruebas enfocadas de integridad y revisión correctas.

## 2026-07-24 - Paginación opcional del historial de planeaciones

- `GET /plan-de-clases/{asignacion_id}` acepta `limit` entre 1 y 50 y `offset`
  mayor o igual que cero cuando se consulta el historial.
- El límite y el desplazamiento se aplican en la base de datos después del
  orden descendente por fecha y creación.
- Omitir `limit` conserva la respuesta completa anterior para mantener
  compatibilidad con otros consumidores.
- La consulta exacta mediante `fecha` conserva su comportamiento y no aplica
  paginación.
- No se agregaron tablas ni migraciones.

Verificación:

- Ruff correcto en rutas, controlador, servicio, repositorio y prueba
  modificados.
- 20 pruebas enfocadas de integridad y revisión correctas.

## 2026-07-24 - Notificaciones administrativas resumidas por profesor

- `GET /notificaciones/planeadores` agrupa para administración todos los envíos
  pendientes de cada profesor directamente en la consulta.
- Cada elemento administrativo devuelve `profesor_id`, nombre, cantidad total
  de planeaciones pendientes y fecha del envío más reciente.
- `total_no_leidas` conserva el número total de planeaciones y
  `total_profesores` informa cuántos docentes tienen envíos pendientes.
- El perfil profesor conserva sin cambios sus notificaciones individuales de
  comentarios administrativos.
- No se agregaron tablas ni migraciones.

Verificación:

- 19 pruebas enfocadas de integridad, revisión y notificaciones correctas.

## 2026-07-23 - Revisión administrativa consolidada

- El listado administrativo agrupa los estados internos en dos decisiones
  visibles: `pendiente` incluye registros antiguos en `visto`, mientras
  `revisado` incluye también `con_observaciones`.
- Una planeación a la que administración solicitó ajustes conserva
  internamente `con_observaciones` cuando el profesor guarda la corrección.
- Esa corrección aumenta `version_revision` y conserva el historial, pero no
  crea otra notificación administrativa ni vuelve a la bandeja pendiente.
- El mismo criterio se aplica cuando el profesor elimina una evidencia como
  parte de la corrección.
- Los demás guardados continúan pasando a `pendiente` y generan la notificación
  administrativa habitual.
- No se agregaron estados, tablas ni migraciones.

Verificación:

- 19 pruebas enfocadas de integridad y revisión correctas.
- Suite completa: 179 de 182 pruebas correctas. Las 3 restantes siguen siendo
  los casos de Super Admin dependientes de la fecha fija `2026-07-01`.

## 2026-07-22 - Aprobación con comentario opcional

- `PATCH /admin/plan-de-clases/{plan_id}/revision` acepta `comentario` cuando
  la decisión es `revisado`.
- El comentario se normaliza, admite hasta 3000 caracteres y no se acepta para
  la apertura simple con estado `visto`.
- Cuando existe comentario, el historial y el estado `revisado` se guardan en
  una sola transacción protegida por la versión del plan.
- El profesor recibe el comentario mediante el flujo existente de
  notificaciones, sin agregar tablas ni aplicar otra migración.

Verificación:

- 16 pruebas enfocadas de integridad, revisión, comentarios y notificaciones
  correctas.
- Suite completa: 176 de 179 pruebas correctas. Las 3 restantes siguen siendo
  los casos de Super Admin dependientes de la fecha fija `2026-07-01`.

## 2026-07-22 - Notificaciones de planeadores por rol

Tercera subcapa del seguimiento administrativo. Agrega eventos persistentes
para administracion y reutiliza la lectura historica de observaciones para el
profesor.

- Cada guardado o nueva version del profesor crea un evento administrativo
  unico por `plan_id + plan_version`.
- Abrir, observar o revisar una version marca sus eventos administrativos
  pendientes como leidos dentro de la misma transaccion.
- El profesor recibe solamente observaciones propias cuyo
  `vista_por_profesor_at` sigue vacio; abrir el historial confirma la lectura.
- `GET /notificaciones/planeadores` entrega el contador total y hasta 20
  elementos recientes, adaptados al rol autenticado.
- `20260722_plan_de_clases_notificaciones.sql` crea la tabla de eventos sin
  poblar planes historicos y fue aplicada en los 4 schemas operativos.
- Los scripts de auditoria ahora abren una transaccion explicita de solo
  lectura y la revierten al finalizar, evitando que el modo de lectura quede
  adherido a conexiones reutilizadas por el proxy.

Verificacion:

- 14 pruebas enfocadas de integridad, revision y notificaciones correctas.
- Suite completa: 174 de 177 pruebas correctas. Las 3 restantes son los casos
  ya documentados de Super Admin dependientes de la fecha fija `2026-07-01`.
- `scripts/auditar_plan_de_clases_revision.py` confirma columnas, historial,
  tabla de eventos y estados validos en los 4 schemas.
- La simulacion posterior confirma la migracion como ya aplicada en todos los
  destinos.

## 2026-07-22 - Seguimiento versionado del plan de clases

Segunda subcapa del flujo de seguimiento administrativo. Prepara el contrato
que usaran las vistas y notificaciones, sin cambiar aun el frontend.

- Cada plan expone `estado_revision`, `version_revision`, fechas de seguimiento
  y contadores de observaciones.
- Los estados persistidos son `pendiente`, `visto`, `con_observaciones` y
  `revisado`.
- Administracion puede consultar un plan por id, marcar la version como vista
  o revisada y registrar observaciones historicas.
- Toda accion administrativa incluye la version leida. Si el profesor guardo
  cambios entretanto, se devuelve `409` y no se aplica una revision obsoleta.
- Un nuevo guardado o la eliminacion de una evidencia por el profesor aumenta
  la version y devuelve el plan a `pendiente`.
- El profesor propietario puede consultar las observaciones y confirmar su
  lectura; ese dato servira para las notificaciones de la siguiente capa.
- `20260722_plan_de_clases_revision.sql` agrega las columnas de seguimiento y
  la tabla `plan_de_clases_observaciones` sin borrar planes existentes.

Verificacion:

- 25 pruebas enfocadas de integridad, revision y permisos correctas.
- Suite completa: 171 de 174 pruebas correctas. Las 3 restantes son los casos
  ya documentados de Super Admin dependientes de la fecha fija `2026-07-01`.
- La migracion se aplico y registro correctamente en los 4 schemas operativos.
- `scripts/auditar_plan_de_clases_revision.py` confirmo en modo de solo lectura
  que la estructura y los datos inicializados no tienen inconsistencias.

## 2026-07-22 - Integridad atomica del plan de clases

Primera subcapa del nuevo flujo de seguimiento administrativo. No agrega aun
estados de revision, observaciones ni notificaciones.

- `guardar_plan_de_clases` reemplaza la secuencia `UPDATE` seguido de `INSERT`
  por un unico `INSERT ... ON CONFLICT DO UPDATE`.
- El contrato HTTP y el identificador retornado se conservan.
- Si no llegan imagenes nuevas, el upsert mantiene las evidencias existentes.
- `20260722_plan_de_clases_integridad.sql` valida datos incompletos y grupos
  duplicados antes de exigir `asignacion_id`, `fecha` y su unicidad.
- La migracion no borra ni fusiona registros; falla de forma transaccional si
  se requiere intervencion manual.
- `scripts/auditar_plan_de_clases_integridad.py` permite revisar todos los
  tenants y el schema plantilla mediante una conexion de solo lectura.

Orden de despliegue:

1. Auditoria de integridad.
2. Migracion por tenant.
3. Despliegue del nuevo repositorio.

Verificacion:

- 4 pruebas nuevas de upsert, conservacion de evidencias, seguridad de la
  migracion y auditoria de solo lectura.
- 18 pruebas enfocadas de integridad y permisos correctas.
- Suite completa: 164 de 167 pruebas correctas. Las 3 restantes pertenecen a
  `test_super_admin.py` y usan `2026-07-01` como fecha futura fija; al ejecutar
  la suite el 2026-07-22, el estado calculado es `suspendido`. Ese modulo no se
  modifico en esta subcapa para mantener el alcance aislado.
- La auditoria productiva de solo lectura finalizo sin inconsistencias en los
  4 schemas operativos.
- La migracion se aplico correctamente en los 4 schemas el 2026-07-22 y la
  verificacion posterior confirmo su registro e integridad.

## 2026-07-21 - Sesion ampliada a cuatro horas

- `ACCESS_TOKEN_EXPIRE_MINUTES` cambia de `120` a `240` minutos por defecto.
- El JWT y la cookie `token` conservan la misma expiracion absoluta de cuatro
  horas desde el inicio de sesion.
- `.env.example` y la documentacion operativa reflejan el nuevo valor.
- Una variable `ACCESS_TOKEN_EXPIRE_MINUTES` configurada en el proveedor de
  despliegue sigue teniendo prioridad sobre el valor predeterminado.

## 2026-07-16 - Distribucion parcial de subsidios en adelantos

- `PagoAdelantadoCreate` admite exactamente una de dos modalidades:
  `cantidad_meses` o `monto_distribuir`.
- Los meses futuros se consultan por saldo, de modo que un periodo con abono
  parcial permanece disponible para completar.
- Un monto se distribuye cronologicamente, cubriendo cuotas completas y
  aplicando el remanente al siguiente mes.
- El backend rechaza valores que excedan la capacidad disponible hasta
  diciembre y exige que los metodos sumen el total recibido.
- El recibo y la respuesta detallan el monto aplicado y saldo restante de cada
  periodo; la anulacion existente revierte todas las aplicaciones.
- No se requirio una nueva migracion: se reutiliza
  `20260716_pagos_aplicaciones_parciales.sql`, ya aplicada.

Verificacion:

- 39 pruebas enfocadas de pagos, subsidios, meses, anulaciones, paginacion y
  permisos.

## 2026-07-16 - Seleccion auditable de meses vencidos

Se amplio el pago pendiente mensual para identificar una o varias cuotas sin
reemplazar el contrato anterior de `POST /pagos`.

Archivos principales:

- `app/services/cartera.py`
- `app/services/cobros.py`
- `app/schemas/pago.py`
- `app/controllers/pagos_controller.py`
- `app/routes/pagos.py`
- `migrations/20260716_pagos_aplicaciones_parciales.sql`
- `tests/test_pagos_meses_vencidos.py`

Cambios:

- El calendario central expone los periodos vencidos con su fecha limite.
- Las opciones aplican pagos historicos sin periodo al saldo mas antiguo por
  FIFO y respetan aplicaciones explicitas o adelantos que ya maduraron.
- `POST /pagos` acepta `aplicaciones` opcionales y conserva el flujo anterior
  cuando no se envian.
- La validacion y la distribucion por metodos son transaccionales; un bloqueo
  asesor por estudiante y concepto evita cobros simultaneos sobre el mismo
  saldo.
- La descripcion de recibo incluye los meses y la anulacion desactiva sus
  aplicaciones como en el flujo de adelantos.

Migracion aplicada:

- `20260716_pagos_aplicaciones_parciales.sql` reemplaza el indice estricto por
  uno auditable por pago y periodo, sin modificar filas existentes.
- Se aplico y verifico en los 4 tenants operativos el 2026-07-16.

Verificacion:

- 34 pruebas enfocadas de pagos, meses, anulaciones, paginacion y permisos.
- Suite completa: 155 aprobadas; persisten 3 pruebas antiguas de Super Admin
  dependientes de la fecha fija `2026-07-01`.

## 2026-07-16 - Pagos de mensualidades adelantadas

Se agrego un flujo optativo para cubrir meses futuros sin modificar el contrato
de los pagos pendientes existentes.

Archivos modificados:

- `app/schemas/pago.py`
- `app/routes/pagos.py`
- `app/controllers/pagos_controller.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/reportes_controller.py`
- `app/services/cobros.py`
- `migrations/20260716_pagos_adelantados.sql`
- `tests/test_pagos_adelantados.py`
- `tests/test_anulaciones_financieras.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/CAMBIOS_BACKEND.md`
- `docs/MIGRACIONES.md`

Cambios:

- `POST /pagos` conserva su schema, validacion y comportamiento.
- Un endpoint de opciones devuelve solo conceptos mensuales asignados y sus
  proximos meses disponibles dentro del año actual.
- El endpoint de registro calcula el total con el valor vigente, exige que los
  metodos sumen exactamente ese total y crea un unico pago/recibo.
- Cada mes queda en `pagos_aplicaciones` con indice unico activo para impedir
  cobros adelantados duplicados.
- El ingreso aparece en caja desde la fecha del pago, pero cartera incorpora la
  aplicacion solo cuando llega el mes correspondiente.
- Los calculos individual y masivo de cartera comparten la misma separacion
  entre pagos normales y aplicaciones de adelantos.
- El estado de cuenta por curso reconoce solo aplicaciones cuyo mes ya llego y
  evita mostrar el mismo adelanto como `Otros Pagos`.
- Al anular, las aplicaciones quedan inactivas y esos meses vuelven a estar
  disponibles sin borrar la huella del pago.
- La operacion de registro es transaccional y un conflicto revierte tanto el
  pago como sus aplicaciones.

Migracion requerida:

- `migrations/20260716_pagos_adelantados.sql` debe ejecutarse por tenant con
  `apply_migration.py`; es aditiva y no modifica registros de pagos existentes.

Verificacion:

- 29 pruebas enfocadas de adelantos, anulaciones, reportes, paginacion y permisos.
- Ruff sobre schemas, rutas, controladores y servicios modificados.

## 2026-07-15 - Fecha limite obligatoria en Malla Curricular

Se formalizo el contrato de las filas del planeador anual y se corrigio el
guardado por lote.

Archivos modificados:

- `app/schemas/planeador_anual.py`
- `app/controllers/planeador_anual_controller.py`
- `tests/test_planeador_anual_validaciones.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- Los cuatro campos de contenido son opcionales entre si y se normalizan con
  `strip()`.
- Toda fila con al menos un contenido exige `fecha` como fecha limite.
- Una fecha sin contenido es invalida y una fila completamente vacia se
  acepta, normalizando `fecha` vacia a `null`.
- El guardado por lote conserva el indice como `slot`, actualiza las filas con
  contenido y elimina el registro de un `slot` que el profesor dejo vacio.
- La operacion se ejecuta en una transaccion con rollback y cierre garantizado
  de conexion.
- No cambia la estructura de la base de datos y no requiere migracion.

Verificacion:

- 19 pruebas enfocadas de Malla Curricular y permisos.
- Ruff sobre schema, controlador y pruebas.

## 2026-07-15 - Observaciones permiten dimensiones parciales

Se formalizo el contrato del observador para aceptar una o varias dimensiones.

Archivos modificados:

- `app/schemas/observacion.py`
- `app/routes/observaciones.py`
- `app/controllers/observacion_controller.py`
- `tests/test_observaciones_validaciones.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `conductual`, `cognitivo` y `lenguaje` tienen texto vacio como valor por
  defecto.
- El backend exige que al menos una dimension tenga contenido real.
- Los textos se normalizan con `strip()` antes de guardar.
- La ruta usa `ObservacionCreate` en lugar de recibir un diccionario sin tipo.
- El guardado usa rollback explicito y cierre garantizado de cursor/conexion.
- No cambia la estructura de la base de datos y no requiere migracion.

Verificacion:

- 18 pruebas enfocadas de observaciones y permisos.
- Ruff sobre schema, ruta, controlador y pruebas.

## 2026-07-15 - Actualizacion segura de asistencia por lote

Se reforzo el contrato que crea y modifica la asistencia del profesor.

Archivos modificados:

- `app/schemas/asistencia.py`
- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`
- `tests/test_asistencia_validaciones.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `estado` solo acepta `presente` o `ausente`.
- El lote no puede estar vacio, mezclar asignacion/fecha/periodo ni repetir
  estudiantes.
- La actualizacion elimina y reemplaza solamente los estudiantes enviados;
  conserva registros historicos de estudiantes que ya no estan activos.
- El reemplazo se ejecuta en una transaccion con rollback explicito ante error.
- Se mantienen el endpoint y la estructura de base de datos existentes; no se
  requiere migracion.

Verificacion:

- 21 pruebas enfocadas de asistencia y permisos.
- Ruff sobre schema, ruta, controlador y pruebas de asistencia.

## 2026-07-15 - Jornada incluida en las clases del profesor

Se amplio de forma compatible el contrato usado por el dashboard del profesor.

Archivos modificados:

- `app/routes/asignaciones.py`
- `tests/test_asignaciones_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `GET /mis-clases/{profesor_id}` incluye `jornada`, tomada directamente de
  `cursos.jornada`.
- No se cambian IDs academicos, permisos, horarios ni asignaciones existentes.
- Se actualizaron expectativas antiguas de pruebas para los rangos
  institucionales vigentes: mañana `06:30-12:30` y tarde `12:30-18:30`.

Verificacion:

- Pruebas enfocadas de asignaciones.
- Revision de sintaxis de la ruta y su prueba de contrato.

## 2026-07-15 - Limpieza operativa de tenant plantilla

Se limpio la informacion registrada por uso en `tenant_colegio_1`, conservando el schema, las tablas, el usuario admin y la configuracion base del tenant ejemplo.

Alcance:

- Se conservaron `usuarios`, `institucion_branding`, `plantilla_impresion`, `cursos`, `materias`, `tipos_de_pagos` y `tipos_pagos_cursos`.
- Se vaciaron datos operativos como estudiantes, profesores, asignaciones, asistencia, notas, pagos, ventas, inventario, boletines, planes de clase, planeadores, nomina, prestamos y egresos.
- No se ejecuto `DROP SCHEMA`, no se eliminaron tablas y no se tocaron otros tenants.
- Se genero un respaldo temporal antes de limpiar; se descarto posteriormente
  porque contenia exclusivamente datos artificiales de una prueba de carga.

Verificacion:

- `tenant_colegio_1.usuarios` conserva el admin `admin@sabiduria.com`.
- Las tablas operativas verificadas quedaron en 0 registros.
- `tenant_2005` conserva datos activos; verificacion posterior mostro estudiantes, profesores, asignaciones, pagos y asistencia con registros.
## 2026-07-15 - Reparacion segura de asignaciones academicas

Se corrigieron referencias `asignacion_academica_id` inconsistentes que podian hacer que un profesor abriera el ID academico de otro profesor, curso o materia.

Archivos modificados:

- `app/services/asignacion_academica.py`
- `app/routes/asignaciones.py`
- `migrations/20260715_reparar_asignacion_academica_invalida.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- La migracion no borra datos; solo actualiza `asignaciones.asignacion_academica_id` cuando apunta a una asignacion de otro profesor, curso o materia.
- El resolver central de asignacion academica valida que el ID apuntado pertenezca a la misma combinacion `profesor_id`, `curso_id` y `materia_id`; si no coincide, usa el ID original.
- `GET /mis-clases/{profesor_id}` queda protegido para no entregar IDs academicos que pertenezcan a otro docente.

Verificacion:

- Auditoria previa en tenants activos: solo `tenant_2005` tenia 8 asignaciones activas inconsistentes.
- Despues de aplicar la migracion, la auditoria queda en 0 inconsistencias en todos los tenants activos.
- `tenant_2005`: Matematicas Tercero de Edgar Villanueva Mercado queda con `292 -> 292` y `328 -> 292`.
- Se ejecuto `python -m py_compile app/services/asignacion_academica.py app/routes/asignaciones.py`.
## 2026-07-15 - Plan de clases permite textos largos

Se amplio el soporte de textos largos en plan de clases para que ninguna caja usada por el profesor bloquee el guardado por longitud.

Archivos modificados:

- `migrations/20260715_plan_de_clases_textos_largos.sql`
- `migrations/20260715_plan_de_clases_estandar_dba_text.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- La primera migracion convierte `plan_de_clases.unidad` y `plan_de_clases.tema` a `TEXT`.
- La migracion complementaria convierte `plan_de_clases.estandar` y `plan_de_clases.dba` a `TEXT`, que seguian limitadas a `VARCHAR(255)` en los tenants existentes.
- `actividad_casa` ya estaba soportada como texto largo.
- El contrato de API queda documentado como cajas opcionales con texto largo.

Verificacion:

- Revision estatica de migraciones y repositorio de plan de clases.
- Consulta a `information_schema.columns` confirmando `estandar` y `dba` como `text` en los tenants activos.

## 2026-07-15 - Plan de clases permite cajas de texto vacias

Se ajusto el contrato backend de plan de clases para que los docentes puedan guardar el plan aunque no usen todas las cajas de texto.

Archivos modificados:

- `app/routes/plan_de_clases.py`
- `app/schemas/plan_de_clases.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- `POST /plan-de-clases` mantiene obligatorios `asignacion_id`, `periodo` y `fecha`.
- Las cajas de texto del plan (`unidad`, `proposito`, `clase`, `estandar`, `dba`, `competencias`, `actividad_casa` y `tema`) tienen valor por defecto `""`.
- El schema de creacion y respuesta tolera textos vacios para no bloquear planes incompletos por decision pedagogica.

Verificacion:

- Se ejecuto `python -m py_compile app/routes/plan_de_clases.py app/schemas/plan_de_clases.py`.

## 2026-07-15 - Documentacion backend sincronizada con codigo actual

Se actualizo la documentacion operativa del backend para alinear el mapa de endpoints, base de datos, migraciones y plan de ejecucion con el codigo vigente.

Archivos modificados:

- `docs/README.md`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/SEGURIDAD.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/MULTITENANT.md`
- `docs/ARQUITECTURA_BACKEND.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- Se agregaron al mapa API los endpoints de valores personalizados por estudiante.
- Se documentaron filtros actuales de rendimiento en dashboard profesor.
- Se agrego `tipos_pagos_estudiantes` a la referencia de base de datos y migraciones.
- Se alineo el plan de ejecucion para usar lenguaje propio de backend en seguridad, roles, modulos y despliegue.
- Se actualizaron fechas de revision en documentos backend revisados.

Verificacion:

- Se contrasto `docs/API_ENDPOINTS.md` contra decorators reales en `app/routes/`.
- Se contrasto la documentacion de valores personalizados contra `app/routes/tipos_pagos.py`, `app/controllers/tipos_pagos_controller.py`, `app/services/cobros.py` y `migrations/20260713_tipos_pagos_estudiantes.sql`.

## 2026-07-13 - Valores personalizados de pago por estudiante

Se agrego soporte para que un estudiante tenga un valor distinto al valor del
curso en un concepto de cartera, sin modificar el curso ni el tipo de pago.

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/tipos_pagos_controller.py`
- `app/routes/tipos_pagos.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/reportes_controller.py`
- `migrations/20260713_tipos_pagos_estudiantes.sql`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Nueva tabla tenant `tipos_pagos_estudiantes`.
- Nueva regla central de valor: estudiante activo > curso > valor base.
- `GET /estudiantes/{estudiante_id}/deudas` respeta el valor personalizado.
- Cartera vencida y estado de cuenta por curso usan la misma regla.
- Se agregaron endpoints admin para listar, guardar y quitar valores
  personalizados por estudiante.
- El backend valida que el concepto este asignado al curso del estudiante antes
  de aceptar una excepcion individual.

## 2026-06-30 - Sesion de 2 horas

Se amplio la duracion por defecto de la sesion autenticada.

Archivos modificados:

- `app/config.py`
- `.env.example`
- `docs/SEGURIDAD.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- `ACCESS_TOKEN_EXPIRE_MINUTES` pasa de `30` a `120` minutos por defecto.
- El JWT y la cookie `token` usan el mismo valor, por lo que la sesion queda
  activa hasta 2 horas si no existe una variable de entorno externa que lo
  sobrescriba.

## 2026-06-24 - Orden configurable de materias en boletin

Se agrego soporte backend para ordenar materias del boletin por curso.

Archivos modificados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `app/schemas/asignacion.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/notas_controller.py`
- `migrations/20260624_asignaciones_orden_boletin.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Se agrego `asignaciones.orden_boletin` con default `100`.
- Se agregaron `GET` y `PUT /cursos/{curso_id}/orden-boletin` para consultar
  y guardar el orden de materias por curso.
- El guardado actualiza todos los horarios activos de la materia en el curso.
- Los boletines administrativos ordenan por `orden_boletin` y luego por nombre
  de materia como respaldo.
- Las consultas legacy de boletin de estudiante tambien respetan el nuevo
  orden.

## 2026-06-23 - Horarios multiples por asignacion academica

Se ajusto la regla de asignaciones academicas:

- Un curso y una materia solo pueden tener un profesor responsable activo.
- Ese mismo profesor puede tener varios horarios/dias para esa materia.
- Los horarios comparten `asignacion_academica_id`, para que notas,
  boletines, asistencia, observaciones y planeadores apunten a un solo historial.
- Se retiro el indice estricto por `profesor_id`, `curso_id`, `materia_id`.
- Se agrego indice unico por horario exacto y trigger para impedir otro profesor
  en la misma materia del mismo curso.
- Se resolvio de forma canonica cualquier `asignacion_id` de horario antes de
  consultar o guardar historial academico.

Archivos modificados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `app/services/asignacion_academica.py`
- `migrations/20260623_asignaciones_horarios_historial_unico.sql`

## 2026-06-23 - Asignaciones activas unicas

Se corrigieron asignaciones duplicadas activas por profesor, curso y materia, y
se agrego proteccion para evitar que vuelvan a generarse.

Archivos modificados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260623_asignaciones_unicas_activas.sql`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- La migracion conserva activa la asignacion con mas historial academico.
- Si las duplicadas no tienen historial, conserva la asignacion mas reciente.
- Las duplicadas restantes quedan `activo = FALSE`, preservando historial.
- Se crea un indice unico parcial para impedir mas de una asignacion activa con
  el mismo `profesor_id`, `curso_id` y `materia_id`.
- El API responde `409 Conflict` con un mensaje claro cuando se intenta crear o
  editar una asignacion duplicada.

Alcance:

- No borra notas, boletines, asistencias, observaciones ni planes.
- Corrige el caso donde el perfil profesor podia mostrar una asignacion vacia
  en lugar de la asignacion con notas.

## 2026-06-23 - Validaciones de duplicados academicos

Se blindaron los modulos administrativos de profesores, materias y cursos
contra duplicados.

Archivos modificados:

- `app/controllers/profesor_controller.py`
- `app/controllers/materia_controller.py`
- `app/controllers/curso_controller.py`
- `app/routes/profesores.py`
- `app/routes/materias.py`
- `app/routes/cursos.py`
- `migrations/20260623_admin_unicos_academicos.sql`
- `docs/API_ENDPOINTS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Profesores no permiten repetir `documento_identidad` ni `email`.
- Materias no permiten repetir `nombre`.
- Cursos no permiten repetir la combinacion `nombre + jornada`.
- El backend responde `409 Conflict` con un mensaje claro cuando detecta un
  duplicado.
- La base de datos agrega indices unicos por tenant para cubrir tambien casos
  concurrentes o llamadas directas al API.

Alcance:

- No bloquea profesores por nombre, porque pueden existir homonimos reales.
- No modifica correos de estudiantes ni usuarios.
- Requiere auditoria previa limpia y ejecucion de migracion tenant.

## 2026-06-23 - Nombres administrativos en mayuscula

Se normalizo el guardado de nombres administrativos para profesores, materias y
cursos.

Archivos modificados:

- `app/controllers/profesor_controller.py`
- `app/controllers/materia_controller.py`
- `app/controllers/curso_controller.py`
- `migrations/20260623_admin_nombres_mayuscula.sql`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Profesores se guardan con `nombre` y `apellido` en mayuscula.
- Materias se guardan con `nombre` en mayuscula.
- Cursos se guardan con `nombre` en mayuscula.
- La migracion convierte los registros existentes y limpia espacios duplicados.

Alcance:

- No modifica correos, documentos, jornadas ni estados.
- Requiere ejecutar la migracion tenant para actualizar datos ya guardados.

## 2026-06-23 - Codigo DANE en identidad institucional

Se agrego el campo institucional `codigo_dane` para que cada colegio pueda
guardarlo desde su configuracion de impresos.

Archivos modificados:

- `app/controllers/branding_controller.py`
- `app/schemas/branding.py`
- `migrations/20260623_institucion_branding_codigo_dane.sql`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- `GET /branding` devuelve `codigo_dane`.
- `PUT /branding` permite guardar `codigo_dane`.
- La migracion agrega `institucion_branding.codigo_dane` como `VARCHAR(20)`.

Alcance:

- Requiere ejecutar la migracion tenant antes o junto al despliegue backend.
- No cambia logos ni plantillas de impresion.

## 2026-06-23 - Endpoint dedicado para deudas de estudiante

Se agrego un endpoint especifico para consultar deudas academicas pendientes
de un estudiante sin depender del resumen amplio de detalle.

Archivos modificados:

- `app/controllers/estudiante_controller.py`
- `app/routes/estudiantes.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- Nuevo endpoint `GET /estudiantes/{estudiante_id}/deudas`.
- Reutiliza `calcular_deudas_estudiante` del servicio central de cobros.
- Devuelve `estudiante_id`, `curso_id`, `deudas` y `total_deuda`.
- Usa `get_cursor()` para cerrar cursor/conexion automaticamente.
- El endpoint existente `/estudiantes/{estudiante_id}/detalles` ahora carga notas,
  asistencia, observaciones, deudas e inventario por secciones independientes:
  si una seccion falla, registra el error y conserva las demas respuestas.

Alcance:

- No cambia cartera vencida ni el endpoint existente
  `/estudiantes/{estudiante_id}/detalles` a nivel de contrato de respuesta.
- No requiere migraciones.

## 2026-06-17 - Cumpleanos de estudiantes en dashboards

Se agregaron endpoints de dashboard para consultar solamente los estudiantes
activos que cumplen anos en la semana actual/proximos dias, usando la fecha
local de Colombia.

Archivos modificados:

- `app/controllers/dashboard_controller.py`
- `app/routes/dashboard.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Cambio:

- `GET /dashboard/cumpleanos/admin?dias=7` devuelve los cumpleaños de
  estudiantes activos para el perfil admin.
- `GET /dashboard/cumpleanos/profesor/{profesor_id}?dias=7` devuelve solo
  estudiantes activos de cursos asignados al profesor autenticado.
- `dias` es opcional, por defecto `7`, y se valida entre `0` y `31`.
- Las consultas filtran por mes y dia de `fecha_nacimiento` en base de datos
  usando `America/Bogota`, incluso si el rango cruza de diciembre a enero,
  evitando cargar listas completas de estudiantes en el frontend.
- Las conexiones y cursores se cierran en `finally`.

Alcance:

- No se crearon tablas ni migraciones.
- No cambia el contrato de `/estudiantes`, `/mis-clases` ni
  `/planilla-excel`.
- El cambio es aditivo y queda protegido por permisos existentes de admin y
  scope de profesor.

## 2026-06-13 - Documentacion backend de produccion, pool y endpoints

Se actualizo la carpeta `docs/` del backend para reflejar el estado operativo
actual despues del despliegue en produccion.

Archivos documentales modificados/agregados:

- `docs/README.md`
- `docs/API_ENDPOINTS.md`
- `docs/ARQUITECTURA_BACKEND.md`
- `docs/BASE_DATOS.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/ESCALABILIDAD.md`
- `docs/MIGRACIONES.md`
- `docs/MULTITENANT.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/SEGURIDAD.md`

Cambio:

- Se agrego indice general de documentacion backend.
- Se documento respuesta operativa ante
  `psycopg2.pool.PoolError: connection pool exhausted`.
- Se dejo como regla que todo `get_connection()` debe cerrar cursor/conexion en
  `finally`, y que codigo nuevo deberia preferir `get_cursor()`.
- Se agrego checklist de Render/Neon, pool, cookies moviles/cross-site y
  post-deploy.
- Se corrigio `API_ENDPOINTS.md`: ventas queda bajo `/api/ventas` y super admin
  queda bajo `/super-admin`.
- Se actualizo la lista de migraciones tenant/public observadas.

Alcance:

- Solo documentacion.
- No se modifico codigo backend en esta actualizacion documental.

Contexto:

- En produccion se observo un error de pool agotado que bloqueo login.
- El login ya habia sido revisado para cerrar conexiones en
  `app/controllers/auth_controller.py`; esta sesion dejo esa regla reflejada en
  los documentos operativos.

## 2026-06-10 - Bloqueo backend de eliminaciones no auditables

Se cerro el acceso backend a endpoints `DELETE` que no deben eliminar registros
operativos o contables.

Archivos modificados:

- `app/routes/tipos_pagos.py`
- `app/controllers/tipos_pagos_controller.py`
- `app/routes/inventario.py`
- `app/controllers/inventario_controller.py`
- `tests/test_catalogos_pagination.py`
- `tests/test_inventario_pagination.py`

Cambio:

- `DELETE /tipos-pagos/{id}` responde `405 Method Not Allowed`.
- `DELETE /inventario/{item_id}` responde `405 Method Not Allowed`.
- Los controladores asociados ya no ejecutan SQL de borrado ni desactivacion por
  metodo `DELETE`.
- Para tipos de pago se debe usar la configuracion `activo/inactivo`.
- Para inventario se debe usar `PATCH /inventario/{item_id}/estado`.
- Egresos y prestamos ya estaban bloqueados con `405`; se mantienen igual.

Motivo:

- Alinear backend con la politica de no eliminar registros que afectan auditoria,
  historial financiero, cobros, ventas o trazabilidad operativa.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m pytest tests\test_egresos_fechas.py tests\test_prestamos_validaciones.py tests\test_inventario_pagination.py tests\test_catalogos_pagination.py -q
.\venv\Scripts\python.exe -m pytest -q
```

Resultado:

- Pruebas especificas OK.
- Suite completa OK.

## Cambio documentado

Fecha: 2026-05-25

Cambio:

- Se actualiza carpeta `docs/` para documentar el estado real actual del backend.

Archivos documentales actualizados:

- `docs/ARQUITECTURA_BACKEND.md`
- `docs/MULTITENANT.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/BASE_DATOS.md`
- `docs/API_ENDPOINTS.md`
- `docs/SEGURIDAD.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Alcance:

- estructura de `app/`;
- rutas y controladores;
- servicios y repositorios;
- autenticacion JWT;
- roles y permisos;
- multi-tenant por schema PostgreSQL;
- uso de `search_path`;
- conexion a base de datos;
- endpoints existentes;
- migraciones y scripts existentes;
- riesgos pendientes;
- variables `.env`;
- estado de preparacion para produccion.

Restricciones aplicadas:

- No se modifico logica del backend.
- No se propusieron cambios nuevos en estos documentos.
- Se documento solo lo observado en el codigo actual.

## 2026-05-25 - Seguridad multi-tenant consolidada

Se consolida en este archivo la bitacora detallada que estaba en README_SEGURIDAD_MULTITENANT.md.

Motivo:

- Evitar documentacion duplicada en la raiz del backend.
- Dejar docs/CAMBIOS_BACKEND.md como bitacora oficial de cambios.
- Conservar pruebas, comandos, decisiones y pendientes de la auditoria multi-tenant.

Resultado:

- README_SEGURIDAD_MULTITENANT.md fue eliminado de la raiz.
- docs/HISTORIAL_SEGURIDAD_MULTITENANT.md fue eliminado porque quedaba duplicado.
- La bitacora historica queda integrada abajo en este mismo archivo.

### Bitacora historica integrada

# Seguimiento de seguridad multi-tenant

Fecha: 2026-05-19

Este documento resume los cambios realizados para endurecer la seguridad
multi-tenant del backend antes de produccion, y deja una lista clara de
pendientes para continuar mas adelante.

## Cambios realizados hoy

### 1. Nomina protegida solo para admin

Archivo:
- `app/routes/nomina.py`

Cambio:
- El router de nomina ahora usa `get_current_active_admin`.
- Antes cualquier request podia acceder a endpoints de nomina si conocia la URL.

Impacto:
- Sin token responde `401`.
- Profesor responde `403`.
- Admin puede operar normalmente.

### 2. Eliminado fallback a tenant por defecto

Archivos:
- `app/globals.py`
- `app/db/tenant.py`
- `app/dependencies.py`
- `app/main.py`

Cambio:
- El `ContextVar` de tenant ya no inicia en `tenant_colegio_1`.
- Si una request no tiene tenant valido, falla en vez de apuntar a un colegio real.
- El JWT debe traer `tenant` valido.

Impacto:
- Evita que requests mal formadas o sin tenant caigan accidentalmente sobre datos reales.

### 3. `public` ya no es tenant valido para usuarios

Archivo:
- `app/db/tenant.py`

Cambio:
- `TENANT_SCHEMA_PATTERN` ya no acepta `public`.
- Se agrego `INTERNAL_SCHEMA_PATTERN` para permitir `public` solo en operaciones internas, como login.

Impacto:
- Un JWT de usuario con `tenant = public` ya no debe ser aceptado.
- El login sigue pudiendo consultar `public.colegios`.

### 4. Usuarios administrativos solo para admin

Archivos:
- `app/routes/usuario.py`
- `app/controllers/usuario_controller.py`

Cambio:
- `/usuarios` ahora requiere `get_current_active_admin`.
- Al crear o actualizar usuarios, la password se guarda con `get_password_hash`.

Impacto:
- Profesor no puede crear, editar, listar ni eliminar usuarios internos.
- Nuevas passwords ya no se guardan en texto plano.

### 5. Inventario solo para admin

Archivo:
- `app/routes/inventario.py`

Cambio:
- Todo el modulo de inventario ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede consultar ni modificar inventario desde API.

### 6. Tipos de pagos solo para admin

Archivo:
- `app/routes/tipos_pagos.py`

Cambio:
- Todo el modulo de tipos de pagos ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede cambiar conceptos, valores, mora ni asignaciones por curso.

### 7. Reportes solo para admin

Archivo:
- `app/routes/reportes.py`

Cambio:
- Todo el modulo de reportes ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede acceder a reportes financieros o resumenes globales.

### 8. Asignaciones separadas por permisos

Archivos:
- `app/routes/asignaciones.py`
- `src/pages/DashboardProfesor.jsx` en frontend

Cambio:
- Crear, editar, eliminar y listar todas las asignaciones ahora es admin-only.
- Profesor puede consultar solo sus propias clases.
- Se agrego validacion de ownership por `profesor_id`.
- El dashboard del profesor ya no consume `/asignaciones/lista`; usa `/mis-clases/{profesor_id}`.
- `/mis-clases/{profesor_id}` ahora devuelve tambien `dia`, `hora_inicio` y `hora_fin`.

Impacto:
- Profesor ya no puede consultar la lista global de asignaciones.
- Profesor conserva su horario y sus clases.

### 9. Dashboard de profesor con ownership

Archivo:
- `app/routes/dashboard.py`

Cambio:
- Endpoints por `profesor_id` validan que el profesor solo consulte su propio ID.
- Endpoints por `asignacion_id` validan que la asignacion pertenezca al profesor.
- Admin puede consultar todo.

Impacto:
- Evita que un profesor cambie IDs para ver datos academicos de otro profesor.

### 10. Plan de clases con ownership

Archivo:
- `app/routes/plan_de_clases.py`

Cambio:
- `POST /plan-de-clases` valida que la asignacion pertenezca al profesor.
- `GET /plan-de-clases/{asignacion_id}` valida ownership.
- Admin mantiene acceso global por `/admin/plan-de-clases`.

Impacto:
- Profesor no puede crear ni consultar planeadores de una asignacion ajena.

### 11. Planilla y notas con ownership por asignacion

Archivos:
- `app/routes/planilla.py`
- `app/routes/notas.py`

Cambio:
- `POST /planilla/nota` valida ownership de `data.asignacion_id`.
- `GET /planilla-excel/{asignacion_id}/{periodo}` valida ownership.
- `DELETE /planilla/tipo` valida ownership.
- `POST /notas` valida ownership de `nota.asignacion_id`.
- `GET /planilla/{asignacion_id}` valida ownership.
- `POST /boletin/guardar` validaba ownership de cada `materia.asignacion_id`;
  esta ruta legacy fue retirada el 2026-05-30 y el flujo actual usa
  `/boletines/guardar`.

Impacto:
- Profesor no puede registrar, borrar o consultar planillas/notas de asignaciones ajenas.

### 12. Revalidacion de usuario/rol contra DB

Archivo:
- `app/dependencies.py`

Cambio:
- `get_current_user` ya no confia solamente en el JWT.
- Despues de validar firma, tenant y rol del token, consulta la base del tenant.
- Si el rol es `profesor`, confirma que exista en la tabla `profesor`.
- Si el rol no es `profesor`, confirma que exista en `usuarios` y que el rol actual en DB coincida con el rol del token.
- Si en alguna tabla existen columnas `estado` o `activo`, tambien las respeta.

Impacto:
- Si un usuario se elimina o cambia de rol, un token viejo deja de servir.
- Si mas adelante se agregan columnas `estado` o `activo` a `usuarios`/`profesor`, la validacion queda lista para bloquear cuentas inactivas.

### 13. Boletines con permisos separados

Archivo:
- `app/routes/boletines.py`

Cambio:
- `POST /boletines/guardar` valida que la asignacion pertenezca al profesor o que el usuario sea admin.
- `POST /boletines/guardar` tambien valida que el estudiante pertenezca al curso de esa asignacion.
- `GET /boletines/referencia/{asignacion_id}/{periodo}` valida ownership por asignacion.
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` ahora requiere `get_current_active_admin`.

Impacto:
- Profesor no puede guardar ni consultar boletines de asignaciones ajenas.
- Profesor no puede guardar boletin cruzando un estudiante que no pertenece a la asignacion.
- La generacion global de boletines queda limitada a admin.

### 14. Asistencia con ownership por asignacion

Archivos:
- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`

Cambio:
- `POST /asistencia` valida que cada asignacion enviada pertenezca al profesor o que el usuario sea admin.
- `POST /asistencia` valida que cada estudiante pertenezca al curso de su asignacion.
- `GET /asistencia/historial/{asignacion_id}/{periodo}` valida ownership por asignacion.
- Se removieron `print` con datos de asistencia recibida para no exponer informacion en logs.

Impacto:
- Profesor no puede registrar ni consultar asistencia de asignaciones ajenas.
- Profesor no puede registrar asistencia cruzando estudiantes fuera del curso de la asignacion.

### 15. Estudiantes, pagos, cuentas y cartera solo para admin

Archivos:
- `app/routes/estudiantes.py`
- `app/routes/pagos.py`
- `app/routes/cuentas.py`
- `app/routes/cartera.py`

Cambio:
- Estos routers ahora usan `get_current_active_admin`.
- Se confirmo que el flujo del profesor para observaciones usa `/planilla/{asignacion_id}`, no `/estudiantes`.

Impacto:
- Profesor no puede listar ni modificar estudiantes desde endpoints administrativos.
- Profesor no puede consultar ni registrar pagos.
- Profesor no puede consultar estados de cuenta ni cartera vencida.
- Las pantallas admin existentes siguen siendo las consumidoras naturales de estos endpoints.

### 16. Cursos, materias y profesores solo para admin

Archivos:
- `app/routes/cursos.py`
- `app/routes/materias.py`
- `app/routes/profesores.py`

Cambio:
- Estos routers ahora usan `get_current_active_admin`.
- Se revisaron usos en frontend y aparecen ligados a pantallas administrativas como crear cursos, crear materias, crear profesores, asignar clases, planeadores admin y boletin admin.
- Los flujos del profesor continúan usando rutas ya acotadas como `/mis-clases/{profesor_id}`, `/planilla/{asignacion_id}` y rutas por asignacion con ownership.

Impacto:
- Profesor no puede crear, editar ni listar catalogos academicos globales desde API.
- La estructura academica queda bajo control del admin.

### 17. `/uploads` protegido por autenticacion y tenant

Archivos:
- `app/main.py`
- `app/dependencies.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/controllers/branding_controller.py`

Cambio:
- Se elimino el `app.mount("/uploads", StaticFiles(...))` publico.
- Se agrego `GET /uploads/{file_path:path}` como endpoint autenticado.
- `get_current_user` ahora tambien puede leer el token desde cookie `token`, necesario para que etiquetas `<img>` puedan cargar logos/imagenes.
- El endpoint valida que la ruta real quede dentro de la carpeta `uploads`.
- El endpoint valida tenant:
  - `uploads/branding/{tenant}/...` solo se sirve a usuarios autenticados de ese tenant.
  - `uploads/{tenant}/plan_de_clases/...` solo se sirve al admin del tenant o al profesor propietario de la asignacion asociada a esa imagen.
- Las imagenes de plan de clases ahora se guardan con UUID, no con el nombre original del archivo.
- Las imagenes de plan de clases validan extension, content-type y tamano maximo.
- Los nuevos logos ya no permiten SVG; solo PNG, JPG/JPEG y WEBP.
- El borrado de logos valida que el archivo real este dentro de `uploads`.

Impacto:
- Un usuario sin token ya no puede abrir archivos de `/uploads`.
- Un usuario de otro tenant no puede abrir archivos de otro colegio por URL.
- Un profesor no puede abrir imagenes de planeadores ajenos si adivina la URL.
- Se reduce riesgo de path traversal y de XSS por SVG en nuevos logos.

Nota:
- En produccion, si frontend y backend viven en dominios/subdominios distintos, revisar configuracion de cookie `token` para que las imagenes autenticadas se carguen correctamente desde `<img>`.

### 18. Script legacy de admin eliminado

Archivos:
- `insert_admin.sql`

Cambio:
- Se elimino `insert_admin.sql` de la raiz del backend.
- Tambien se elimino la copia legacy que habia quedado como referencia.

Impacto:
- Elimina el riesgo de ejecutar por accidente un script que crea un admin con password en texto plano.
- Actualizacion 2026-06-02: el flujo recomendado para crear tenants y admin
  inicial es `/super-admin` -> `Crear colegio`. `crear_cliente.py` paso a
  `scripts/legacy/crear_cliente.py`.

### 19. Prueba base de permiso por estudiante

Archivos:
- `app/core/permissions.py`
- `tests/test_permissions.py`
- `tests/test_notas_permissions.py`

Cambio:
- Se agregaron pruebas unitarias para `require_estudiante_access`.
- Las pruebas validan:
  - admin pasa sin consultar DB;
  - profesor duenio del estudiante pasa;
  - profesor no duenio recibe `403`;
  - rol no autorizado recibe `403`.
- Se agregaron pruebas de cableado para confirmar que las rutas antiguas de
  `notas.py` llaman el permiso antes de devolver datos:
  - `GET /notas/{estudiante_id}`;
  - `GET /boletin/{estudiante_id}`;
  - `GET /boletin/detallado/{estudiante_id}`.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py`
- Resultado: 8 pruebas pasaron.

Pendiente manual:
- Probar funcionalmente en la app con usuarios reales:
  - profesor duenio del estudiante;
  - profesor no duenio;
  - admin;
  - request sin token.

Prueba manual realizada:
- Se intento consultar un estudiante no autorizado desde URL directa y el backend respondio `{"detail":"No autorizado"}`.

### 20. Pruebas base de auth, tenant y uploads

Archivos:
- `tests/test_auth_tenant.py`
- `tests/test_uploads_permissions.py`

Cambio:
- Se agregaron pruebas unitarias para `get_current_user`:
  - sin token responde `401`;
  - token invalido responde `401`;
  - token con `tenant=public` responde `401`;
  - token valido fija el tenant y revalida usuario contra DB;
  - usuario eliminado o rol cambiado invalida el token.
- Se agregaron pruebas unitarias para la validacion de `/uploads`:
  - branding del mismo tenant se permite;
  - branding de otro tenant se bloquea;
  - path traversal se bloquea;
  - admin del tenant puede abrir imagen de plan de clases;
  - profesor duenio puede abrir imagen de su plan de clases;
  - profesor no duenio recibe `403`.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 19 pruebas pasaron.

Nota:
- Aparecieron advertencias de dependencias/Pydantic, pero no errores de pruebas.

### 21. Runner de migraciones con historial

Archivos:
- `apply_migration.py`
- `migrations/README.md`
- `tests/test_apply_migration.py`

Cambio:
- Se mejoro `apply_migration.py` para registrar historial en `public.schema_migrations`.
- Se agrega checksum SHA-256 por migracion.
- Si una migracion ya fue aplicada en un tenant con el mismo checksum, se omite.
- Si existe el mismo nombre de migracion con checksum diferente, se bloquea.
- Se agrego modo `--dry-run` para simular antes de aplicar cambios.
- Se reemplazo el `SET search_path` construido manualmente por `psycopg2.sql.Identifier`.

Uso recomendado:
- `python apply_migration.py migrations/<archivo>.sql --dry-run`
- `python apply_migration.py migrations/<archivo>.sql`

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 24 pruebas pasaron.

Pendiente:
- Probar el runner contra una copia de la base real antes de usarlo en produccion.
- Decidir mas adelante si se migra completamente a Alembic.

### 22. Script de indices por tenant actualizado

Archivos:
- `scripts/apply_tenant_indexes.py`
- `tests/test_apply_tenant_indexes.py`

Cambio:
- Se completo la lista de indices recomendados para consultas frecuentes.
- Se agrego modo `--dry-run` para simular sin crear indices.
- El script ahora valida que la tabla exista antes de crear el indice.
- El script ahora valida que las columnas existan antes de crear el indice.
- Si una tabla o columna falta en un tenant, se omite sin romper todo el proceso.

Indices incluidos:
- `estudiantes(curso_id)`
- `asignaciones(profesor_id)`
- `asignaciones(curso_id)`
- `notas_detalle(estudiante_id, asignacion_id, periodo)`
- `boletin_cabecera(estudiante_id, asignacion_id, periodo)`
- `asistencia(asignacion_id, periodo)`
- `asistencia(estudiante_id, fecha)`
- `pagos(estudiante_id)`
- `ventas(estudiante_id, estado)`
- `plan_de_clases(asignacion_id, fecha)`

Uso recomendado:
- Simular: `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py --dry-run`
- Aplicar: `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py`

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 28 pruebas pasaron.
- Se ejecuto `--dry-run` y encontro 2 tenants activos: `tenant_3333` y `tenant_colegio_1`.
- No se crearon indices durante la simulacion.
- Se ejecuto el script real y los indices quedaron verificados en `tenant_3333` y `tenant_colegio_1`.

Pendiente:
- Despues de aplicar, revisar consultas pesadas con `EXPLAIN ANALYZE`.

### 23. Paginacion compatible en estudiantes

Archivos:
- `app/routes/estudiantes.py`
- `app/controllers/estudiante_controller.py`
- `tests/test_estudiantes_pagination.py`

Cambio:
- `GET /estudiantes` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /estudiantes?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agrego `busqueda` opcional:
  - `GET /estudiantes?limit=50&offset=0&busqueda=ana`
- El limite maximo permitido por request es `200`.

Motivo:
- Evita romper las pantallas actuales que consumen `/estudiantes` como lista.
- Permite migrar el frontend a paginacion pantalla por pantalla.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_estudiantes_pagination.py tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`
- Resultado: 30 pruebas pasaron.

Pruebas manuales recomendadas:
- `GET /estudiantes`
- `GET /estudiantes?limit=20&offset=0`
- `GET /estudiantes?limit=20&offset=0&busqueda=<texto>`

### 24. Paginacion compatible en ventas

Archivos:
- `app/routes/ventas.py`
- `app/controllers/venta_controller.py`
- `tests/test_ventas_pagination.py`

Cambio:
- `GET /api/ventas/` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /api/ventas/?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `busqueda`;
  - `estudiante_id`;
  - `estado`.
- El limite maximo permitido por request es `200`.
- En modo paginado, el backend solo carga los detalles de las ventas de esa pagina, no todos los detalles historicos.

Motivo:
- Evita cargar todas las ventas y todos sus detalles cuando el historial crezca.
- Mantiene intacta la pantalla actual mientras se migra el frontend con calma.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py tests\test_apply_tenant_indexes.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_uploads_permissions.py`

Pruebas manuales recomendadas:
- `GET /api/ventas/`
- `GET /api/ventas/?limit=20&offset=0`
- `GET /api/ventas/?limit=20&offset=0&estado=Pendiente`
- `GET /api/ventas/?limit=20&offset=0&busqueda=<texto>`

### 25. Paginacion compatible en pagos por estudiante

Archivos:
- `app/routes/pagos.py`
- `app/controllers/pagos_controller.py`
- `tests/test_pagos_pagination.py`

Cambio:
- `GET /pagos/{estudiante_id}` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /pagos/{estudiante_id}?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.

Motivo:
- El historial de pagos puede crecer mucho por estudiante.
- Permite migrar la pantalla de pagos a paginacion sin romper el flujo actual de facturacion/recibos.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /pagos/<estudiante_id>`
- `GET /pagos/<estudiante_id>?limit=20&offset=0`
- `GET /pagos/<estudiante_id>?limit=20&offset=20`

### 26. Paginacion compatible en inventario

Archivos:
- `app/routes/inventario.py`
- `app/controllers/inventario_controller.py`
- `tests/test_inventario_pagination.py`

Cambio:
- `GET /inventario` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /inventario?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `busqueda`;
  - `solo_con_stock`.
- El limite maximo permitido por request es `200`.

Motivo:
- Inventario se usa en administracion y en punto de venta.
- Al crecer el catalogo, permite cargar productos por paginas sin romper las pantallas actuales.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /inventario`
- `GET /inventario?limit=20&offset=0`
- `GET /inventario?limit=20&offset=0&busqueda=<texto>`
- `GET /inventario?limit=20&offset=0&solo_con_stock=true`

### 27. Paginacion compatible en reportes de ingresos

Archivos:
- `app/routes/reportes.py`
- `app/controllers/reportes_controller.py`
- `scripts/apply_tenant_indexes.py`
- `tests/test_reportes_pagination.py`
- `tests/test_apply_tenant_indexes.py`

Cambio:
- `GET /reportes/ingresos-mes/{mes}` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /reportes/ingresos-rango?inicio=<fecha>&fin=<fecha>` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- Ambos endpoints aceptan ahora `limit` y `offset`.
- Con paginacion devuelven:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.
- Se agregaron al script de indices:
  - `pagos(fecha)`;
  - `pagos(fecha_pago)`.

Motivo:
- Los reportes financieros por mes/rango pueden crecer mucho y devolver demasiados pagos.
- La pantalla actual de reportes sigue funcionando sin cambios.
- Los indices por fecha preparan mejor la base para consultas historicas grandes.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_reportes_pagination.py tests\test_apply_tenant_indexes.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /reportes/ingresos-mes/2026-05`
- `GET /reportes/ingresos-mes/2026-05?limit=20&offset=0`
- `GET /reportes/ingresos-rango?inicio=2026-05-01&fin=2026-05-31`
- `GET /reportes/ingresos-rango?inicio=2026-05-01&fin=2026-05-31&limit=20&offset=0`

Pendiente operativo:
- Se ejecuto `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py --dry-run` y encontro los indices nuevos pendientes de verificacion en `tenant_3333` y `tenant_colegio_1`.
- Si la simulacion se ve bien, ejecutar `.\venv\Scripts\python.exe scripts\apply_tenant_indexes.py` para verificar/crear los indices nuevos.

### 28. Paginacion compatible en asignaciones administrativas

Archivos:
- `app/routes/asignaciones.py`
- `app/controllers/asignacion_controller.py`
- `tests/test_asignaciones_pagination.py`

Cambio:
- `GET /asignaciones/lista` conserva el comportamiento anterior si no se envian parametros: devuelve una lista simple.
- `GET /asignaciones/lista?limit=50&offset=0` devuelve respuesta paginada:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- Se agregaron filtros opcionales:
  - `profesor_id`;
  - `curso_id`;
  - `materia_id`;
  - `busqueda`.
- El limite maximo permitido por request es `200`.

Motivo:
- La grilla de asignacion de clases necesita seguir cargando todas las asignaciones como hoy para validar cruces visuales y materias duplicadas.
- La paginacion queda disponible para futuras vistas administrativas o busquedas mas livianas.
- Es un listado sensible porque cruza profesor, curso, materia y horario.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_asignaciones_pagination.py tests\test_reportes_pagination.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /asignaciones/lista`
- `GET /asignaciones/lista?limit=20&offset=0`
- `GET /asignaciones/lista?limit=20&offset=0&profesor_id=<id>`
- `GET /asignaciones/lista?limit=20&offset=0&curso_id=<id>`
- `GET /asignaciones/lista?limit=20&offset=0&busqueda=<texto>`

### 29. Paginacion compatible en catalogos administrativos

Archivos:
- `app/routes/profesores.py`
- `app/controllers/profesor_controller.py`
- `app/routes/cursos.py`
- `app/controllers/curso_controller.py`
- `app/routes/materias.py`
- `app/controllers/materia_controller.py`
- `app/routes/usuario.py`
- `app/controllers/usuario_controller.py`
- `tests/test_catalogos_pagination.py`

Cambio:
- `GET /profesores`, `GET /cursos`, `GET /materias` y `GET /usuarios` conservan el comportamiento anterior si no se envian parametros: devuelven listas simples.
- Todos aceptan ahora `limit` y `offset`.
- `profesores`, `cursos`, `materias` y `usuarios` aceptan `busqueda`.
- `usuarios` acepta ademas filtro `rol`.
- Con paginacion devuelven:
  - `total`;
  - `limit`;
  - `offset`;
  - `items`.
- El limite maximo permitido por request es `200`.

Motivo:
- Son catalogos normalmente pequenos, pero dejarlos con paginacion opcional completa el patron del backend.
- Permite crear futuras pantallas administrativas con busqueda/paginacion sin cambiar contratos existentes.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_catalogos_pagination.py tests\test_asignaciones_pagination.py tests\test_reportes_pagination.py tests\test_inventario_pagination.py tests\test_pagos_pagination.py tests\test_ventas_pagination.py tests\test_estudiantes_pagination.py`

Pruebas manuales recomendadas:
- `GET /profesores`
- `GET /profesores?limit=20&offset=0&busqueda=<texto>`
- `GET /cursos`
- `GET /cursos?limit=20&offset=0&busqueda=<texto>`
- `GET /materias`
- `GET /materias?limit=20&offset=0&busqueda=<texto>`
- `GET /usuarios`
- `GET /usuarios?limit=20&offset=0&busqueda=<texto>&rol=admin`

### 30. Permisos repetidos centralizados

Archivos:
- `app/core/permissions.py`
- `app/routes/notas.py`
- `app/routes/planilla.py`
- `app/routes/asistencia.py`
- `app/routes/boletines.py`
- `app/routes/dashboard.py`
- `app/routes/asignaciones.py`
- `app/routes/plan_de_clases.py`
- `tests/test_permissions.py`

Cambio:
- Se consolido `app/core/permissions.py` como modulo unico para permisos reutilizables.
- Se agregaron funciones centrales:
  - `require_profesor_scope`;
  - `require_asignacion_access`;
  - `require_estudiante_access`;
  - `require_estudiante_in_asignacion`;
  - `require_plan_de_clases_access`.
- Se reemplazaron validaciones locales repetidas en rutas criticas:
  - notas;
  - planilla;
  - asistencia;
  - boletines;
  - dashboard;
  - asignaciones;
  - plan de clases.

Motivo:
- Evita que cada ruta tenga su propia version de permisos.
- Reduce riesgo de que una ruta quede mas permisiva que otra por error.
- Hace mas facil auditar y endurecer reglas multi-tenant/profesor/admin en un solo lugar.

Decision tecnica:
- Se mantuvo el modulo en `app/core/permissions.py`.
- No se creo `app/security/permissions.py` porque ya existe `app/security.py`; crear una carpeta con el mismo nombre podria causar conflictos de importacion en Python.

Verificacion:
- `.\venv\Scripts\python.exe -m pytest tests\test_permissions.py tests\test_notas_permissions.py tests\test_auth_tenant.py tests\test_asignaciones_pagination.py`
- Resultado: 25 pruebas pasaron.

Pruebas manuales recomendadas:
- Profesor debe poder ver sus propias clases en `/mis-clases/<profesor_id>`.
- Profesor no debe poder ver clases de otro profesor cambiando el ID.
- Profesor debe poder abrir planilla/notas/asistencia de sus asignaciones.
- Profesor debe recibir `403` al intentar una asignacion ajena.
- Admin debe conservar acceso administrativo normal.

## Verificaciones realizadas

- Validacion de sintaxis con `ast.parse` en los archivos Python modificados.
- Build de frontend con `pnpm run build` despues de corregir el horario del profesor.
- El build de frontend termino correctamente.
- Validacion de sintaxis de `app/dependencies.py` despues de agregar revalidacion contra DB.
- Validacion de sintaxis de `app/routes/boletines.py` despues de agregar permisos por asignacion/admin.
- Validacion de sintaxis de `app/routes/asistencia.py` y `app/controllers/asistencia_controller.py`.
- Validacion de sintaxis de `app/routes/estudiantes.py`, `app/routes/pagos.py`, `app/routes/cuentas.py` y `app/routes/cartera.py`.
- Validacion de sintaxis de `app/routes/cursos.py`, `app/routes/materias.py` y `app/routes/profesores.py`.
- Validacion de sintaxis de `app/main.py`, `app/dependencies.py`, `app/controllers/plan_de_clases_controller.py` y `app/controllers/branding_controller.py`.

## Pendientes importantes

### 1. Revisar scripts antiguos

Archivo:
- `insert_admin.sql`

Estado:
- Hecho. El script fue eliminado por completo.

Riesgo residual:
- Ninguno desde el repositorio, mientras no se recree un script similar con password en texto plano.

### 2. Provisionamiento de tenants

Archivo:
- `scripts/legacy/crear_cliente.py`

Estado:
- Actualmente el alta de tenant se hace por terminal.
- Este flujo hashea la password del admin inicial.

Pendiente:
- Mas adelante crear panel o comando superadmin mas robusto.
- Asegurar migraciones completas para cada tenant nuevo.

## Recomendacion de siguiente sesion

Orden sugerido:

1. Revisar scripts antiguos y provisionamiento de tenants.
2. Probar en entorno real que logos e imagenes de planeadores cargan correctamente con el nuevo `/uploads` autenticado.

## Hoja de ruta de auditoria para produccion

Esta seccion resume el paso a paso recomendado despues de la auditoria general
del sistema. El objetivo es seguir endureciendo seguridad, escalabilidad y
mantenibilidad sin romper funcionalidades existentes.

### 1. Seguridad inmediata: cerrar endpoints por `estudiante_id`

Archivo principal:
- `app/routes/notas.py`

Endpoints a cerrar:
- `GET /notas/{estudiante_id}`
- `GET /boletin/{estudiante_id}`
- `GET /boletin/detallado/{estudiante_id}`

Riesgo:
- Aunque el usuario este autenticado, hoy un profesor podria cambiar el
  `estudiante_id` en la URL e intentar consultar notas o boletines de un
  estudiante que no pertenece a sus asignaciones dentro del mismo tenant.

Accion recomendada:
- Crear una validacion de acceso por estudiante.
- Admin: puede consultar estudiantes dentro de su tenant.
- Profesor: solo puede consultar estudiantes cuyo curso tenga una asignacion
  perteneciente a ese profesor.
- Si no cumple, responder `403`.

Pruebas necesarias:
- Profesor duenio del estudiante recibe `200`.
- Profesor no duenio recibe `403`.
- Admin recibe `200` dentro de su tenant.
- Sin token recibe `401`.
- Token de otro tenant no debe ver datos fuera de su schema.

### 2. Scripts peligrosos

Archivo:
- `insert_admin.sql`

Riesgo:
- Crea un usuario admin con password plano (`admin123`).

Accion recomendada:
- Hecho: fue eliminado por completo porque no era necesario para el funcionamiento del sistema.
- Actualizacion 2026-06-02: el flujo oficial ahora es `/super-admin` ->
  `Crear colegio`. `crear_cliente.py` paso a `scripts/legacy/crear_cliente.py`.

### 3. Pruebas base de seguridad

Objetivo:
- Montar pruebas automatizadas minimas antes de produccion.

Casos obligatorios:
- Login correcto por tenant.
- Login falla con colegio inactivo o inexistente.
- Token viejo falla si el usuario se elimina o cambia de rol.
- Profesor no puede consultar asignaciones ajenas.
- Profesor no puede consultar estudiantes ajenos.
- Admin puede operar dentro de su tenant.
- `/uploads` exige autenticacion.
- `/uploads` bloquea archivos de otro tenant.
- Passwords nuevas siempre quedan hasheadas.

Estado:
- Iniciado. Ya existen pruebas para:
  - regla de acceso por estudiante;
  - rutas antiguas de notas;
  - auth/JWT/tenant;
  - validacion de uploads protegidos.
- Falta ampliar pruebas a flujos completos con DB de prueba e integracion de endpoints reales.

### 4. Migraciones

Estado actual:
- Existen scripts sueltos y una carpeta `migrations`.
- Alembic aun no esta inicializado como fuente formal de verdad.
- `apply_migration.py` ya tiene historial por tenant con checksum y `--dry-run`.

Accion recomendada:
- Usar `apply_migration.py` como runner temporal seguro.
- Ejecutar siempre primero con `--dry-run`.
- Inicializar Alembic mas adelante, o consolidar este runner propio como flujo oficial.
- Distinguir entre:
  - cambios globales en `public`;
  - cambios repetidos en schemas `tenant_*`;
  - indices y constraints por tenant.

Riesgo si no se hace:
- Un tenant nuevo puede quedar con tablas o columnas distintas.
- Un cambio aplicado manualmente puede no llegar a todos los colegios.

### 5. Indices y revision con `EXPLAIN ANALYZE`

Accion recomendada:
- Usar `scripts/apply_tenant_indexes.py` para aplicar indices por tenant.
- Ejecutar primero `--dry-run`.
- Revisar reportes con `EXPLAIN ANALYZE`.

Prioridad de indices:
- `estudiantes(curso_id)`
- `asignaciones(profesor_id)`
- `asignaciones(curso_id)`
- `notas_detalle(estudiante_id, asignacion_id, periodo)`
- `boletin_cabecera(estudiante_id, asignacion_id, periodo)`
- `asistencia(asignacion_id, periodo)`
- `asistencia(estudiante_id, fecha)`
- `pagos(estudiante_id)`
- `ventas(estudiante_id, estado)`
- `plan_de_clases(asignacion_id, fecha)`

Estado:
- Script actualizado con modo seguro `--dry-run`.
- Pruebas unitarias agregadas.
- Simulacion ejecutada correctamente.
- Indices reales aplicados/verificados en los tenants activos.
- Falta medir consultas pesadas con `EXPLAIN ANALYZE`.

### 6. Paginacion

Problema:
- Varios endpoints devuelven listas completas. Esto funciona con pocos datos,
  pero puede afectar memoria, tiempos de respuesta y experiencia de usuario.

Empezar por:
- `GET /estudiantes` (iniciado con paginacion compatible)
- ventas
- pagos por estudiante
- reportes de ingresos por rango
- inventario
- asignaciones/listados administrativos

Accion recomendada:
- Agregar `limit` y `offset` con limites maximos razonables.
- Mantener compatibilidad con el frontend actual mientras se migra pantalla por pantalla.

Estado:
- `GET /estudiantes` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /api/ventas/` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /pagos/{estudiante_id}` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /inventario` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /reportes/ingresos-mes/{mes}` y `GET /reportes/ingresos-rango` ya soportan paginacion opcional sin romper el contrato anterior.
- `GET /asignaciones/lista` ya soporta paginacion opcional sin romper el contrato anterior.
- `GET /profesores`, `GET /cursos`, `GET /materias` y `GET /usuarios` ya soportan paginacion opcional sin romper el contrato anterior.
- La fase de paginacion compatible queda cubierta en los listados administrativos principales.

### 7. Refactor de permisos

Problema:
- Las validaciones de permisos estan repetidas en varios routers.

Accion escalable recomendada:
- Crear un archivo central, por ejemplo:
  - `app/security/permissions.py`

Funciones sugeridas:
- `require_admin(current_user)`
- `require_asignacion_access(asignacion_id, current_user)`
- `require_estudiante_access(estudiante_id, current_user)`
- `require_estudiante_in_asignacion(estudiante_id, asignacion_id)`

Estrategia segura:
- No mover todo de una vez.
- Primero crear funciones centrales.
- Migrar una ruta critica.
- Probar.
- Continuar modulo por modulo.

Estado:
- Iniciado y aplicado en rutas criticas de profesor/asignacion/estudiante/plan de clases.
- Falta una segunda pasada mas adelante para revisar otros permisos especiales y simplificar imports/casos no cubiertos por estas funciones.

### 8. Refactor de modulos grandes

Archivos backend que conviene dividir:
- `app/controllers/estudiante_controller.py`
- `app/controllers/reportes_controller.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/asignacion_controller.py`
- `app/controllers/tipos_pagos_controller.py`

Archivos frontend que conviene dividir:
- `src/components/cartera/AdministrarTiposPago.jsx`
- `src/pages/EstudiantesAdmin.jsx`
- `src/components/AsignarClaseGrid.jsx`
- `src/pages/CarteraVencidaAdmin.jsx`
- `src/pages/PagosAdmin.jsx`

Objetivo:
- Separar UI, llamadas API, helpers de formato, validaciones y componentes hijos.
- Reducir riesgo de romper una pantalla completa por cambios pequenos.

### 9. Endurecer sesion

Estado actual:
- El frontend guarda token en cookie creada por JavaScript y conserva datos en
  `localStorage`.

Riesgo:
- Si algun dia aparece XSS, el token podria quedar expuesto.

Accion recomendada para produccion:
- Mover el token a cookie `HttpOnly`, `Secure`, `SameSite`.
- El backend debe emitir y limpiar la cookie.
- El frontend no deberia necesitar leer el token directamente.

### 10. Provisionamiento de tenants

Archivo legacy:
- `scripts/legacy/crear_cliente.py`

Estado:
- Antes el tenant se creaba desde terminal.
- El flujo actual crea colegios desde `/super-admin`.

Accion recomendada:
- Mantener el script solo como referencia historica.
- Validar que cada tenant nuevo reciba todas las tablas, datos iniciales,
  plantillas, branding vacio, indices y migraciones.
- A mediano plazo crear flujo superadmin o comando CLI mas robusto.

Checklist minimo de tenant nuevo:
- Registro en `public.colegios`.
- Schema creado con nombre valido.
- Tablas completas.
- Indices aplicados.
- Plantillas predefinidas copiadas.
- Branding inicial creado.
- Admin inicial con password hasheada.
- Login probado.
- Build/frontend apuntando al backend correcto.

## Lectura general de estado

El sistema ya avanzo bastante en seguridad multi-tenant: se elimino el fallback
a tenant real, se protegio gran parte de los modulos administrativos, se
revalida usuario contra DB, y `/uploads` ya no es publico.

Aun asi, no se considera listo para produccion masiva hasta cerrar tres frentes:

1. Ownership por `estudiante_id` en rutas antiguas de `notas.py`.
2. Pruebas automatizadas de acceso cruzado, autenticacion, tenants y uploads.
3. Migraciones confiables para que todos los tenants tengan el mismo schema.

La base ya es seria, pero falta la parte menos visible y mas importante:
pruebas, permisos centralizados, migraciones, paginacion e indices.

importante: cuando se modifique cada paso pedir probar lo que se acctualizo



## 2026-05-26 - Cierre incremental de ownership en rutas de profesor

Se continuo la fase critica de seguridad backend enfocada en rutas con IDs directos manipulables desde el navegador.

### Observaciones protegidas por asignacion y estudiante

Archivo modificado:

- `app/routes/observaciones.py`

Cambio:

- `POST /observaciones` ahora valida `asignacion_id` con `require_asignacion_access`.
- `POST /observaciones` ahora valida que `estudiante_id` pertenezca a la asignacion con `require_estudiante_in_asignacion`.
- `GET /observaciones/{estudiante_id}/{asignacion_id}/{periodo}` aplica las mismas validaciones antes de consultar.

Riesgo cerrado:

- Un profesor autenticado podia intentar cambiar manualmente `estudiante_id` o `asignacion_id` para leer o guardar observaciones de una asignacion ajena.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m py_compile app\routes\observaciones.py
.\venv\Scripts\python.exe -m pytest tests\test_permissions.py
```

Resultado:

- `tests/test_permissions.py`: 14 pruebas pasaron.

Pruebas manuales recomendadas:

- Profesor duenio debe poder guardar y consultar observaciones de su asignacion.
- Profesor no duenio debe recibir `403` al cambiar `asignacion_id` por una asignacion ajena.
- Profesor debe recibir `403` si intenta cruzar un estudiante que no pertenece a la asignacion.
- Admin debe conservar acceso normal dentro del tenant.
- Request sin token debe responder `401`.

### Planeador anual protegido por asignacion

Archivo modificado:

- `app/routes/planeador_anual.py`

Cambio:

- `GET /planeador-anual/{asignacion_id}/{periodo}` ahora valida `asignacion_id` con `require_asignacion_access`.
- `PUT /planeador-anual/{asignacion_id}/{periodo}` aplica la misma validacion antes de actualizar.

Riesgo cerrado:

- Un profesor autenticado podia intentar cambiar manualmente `asignacion_id` para consultar o actualizar el planeador anual de otro profesor.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m py_compile app\routes\planeador_anual.py
.\venv\Scripts\python.exe -m pytest tests\test_permissions.py
```

Resultado:

- `tests/test_permissions.py`: 14 pruebas pasaron.

Pruebas manuales recomendadas:

- Profesor duenio debe poder consultar y actualizar su planeador anual.
- Profesor no duenio debe recibir `403` al usar una `asignacion_id` ajena.
- Admin debe conservar acceso normal dentro del tenant.
- Request sin token debe responder `401`.

Nota de entorno:

- Durante las ejecuciones de PowerShell aparecieron mensajes locales de `fnm`/perfil de PowerShell por permisos en `AppData`; no afectaron las pruebas de backend.

## 2026-05-26 - Verificacion de rutas criticas ya protegidas

Se continuo la fase critica de seguridad backend y se verificaron modulos sensibles sin requerir cambios de codigo adicionales.

### Plan de clases

Archivos revisados:

- `app/routes/plan_de_clases.py`
- `app/controllers/plan_de_clases_controller.py`
- `app/core/permissions.py`

Estado:

- `POST /plan-de-clases` ya valida `require_asignacion_access`.
- `GET /plan-de-clases/{asignacion_id}` ya valida `require_asignacion_access`.
- `DELETE /plan-de-clases/{plan_id}/imagen` ya valida `require_plan_de_clases_access`.
- Rutas admin de plan de clases ya usan `get_current_active_admin`.

Resultado:

- No se modifico codigo.
- Se valido sintaxis con `py_compile`.
- `tests/test_permissions.py` paso, pero `tests/test_uploads_permissions.py` no pudo completarse por permisos locales de pytest creando temporales en Windows.

### Asistencia

Archivos revisados:

- `app/routes/asistencia.py`
- `app/controllers/asistencia_controller.py`
- `app/schemas/asistencia.py`

Estado:

- `POST /asistencia` ya valida cada item con `require_asignacion_access` y `require_estudiante_in_asignacion`.
- `GET /asistencia/historial/{asignacion_id}/{periodo}` ya valida `require_asignacion_access`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py`: 14 pruebas pasaron.

### Boletines

Archivos revisados:

- `app/routes/boletines.py`
- `app/controllers/boletin_controller.py`
- `app/schemas/boletin.py`

Estado:

- `POST /boletines/guardar` ya valida `require_asignacion_access` y `require_estudiante_in_asignacion`.
- `GET /boletines/referencia/{asignacion_id}/{periodo}` ya valida `require_asignacion_access`.
- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` ya exige `get_current_active_admin`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py tests/test_notas_permissions.py`: 18 pruebas pasaron.

### Dashboard

Archivos revisados:

- `app/routes/dashboard.py`
- `app/controllers/dashboard_controller.py`

Estado:

- Endpoints por `profesor_id` ya usan `require_profesor_scope`.
- Endpoints por `asignacion_id` ya usan `require_asignacion_access`.

Resultado:

- No se modifico codigo.
- `py_compile` correcto.
- `tests/test_permissions.py`: 14 pruebas pasaron.

### Rutas admin-only

Archivos revisados:

- `app/routes/estudiantes.py`
- `app/routes/pagos.py`
- `app/routes/cursos.py`
- `app/routes/profesores.py`
- `app/routes/materias.py`
- `app/routes/usuario.py`
- `app/routes/reportes.py`
- `app/routes/inventario.py`
- `app/routes/tipos_pagos.py`
- `app/routes/cartera.py`
- `app/routes/nomina.py`

Estado:

- Todos los routers revisados usan `get_current_active_admin` a nivel de router.

Resultado:

- No se modifico codigo.
- `py_compile` correcto para todos los archivos revisados.

Conclusion:

- La fase de revision de ownership/admin-only queda avanzada.
- Los cambios reales de codigo hechos hoy fueron en `observaciones.py` y `planeador_anual.py`.
- Los demas modulos listados quedaron verificados como ya protegidos.

## 2026-05-26 - Configuracion base para produccion

Se avanzo en la preparacion de variables y comportamiento de sesion/CORS para despliegue.

Archivos modificados:

- `app/config.py`
- `app/main.py`
- `app/routes/auth.py`
- `.env.example`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`
- `docs/CAMBIOS_BACKEND.md`

Cambios:

- Se agrego `ALLOW_DEV_CORS_ORIGINS` a configuracion.
- CORS ahora incluye `localhost` y `127.0.0.1` solo si `ALLOW_DEV_CORS_ORIGINS=true`.
- `.env.example` ahora documenta `ALLOW_DEV_CORS_ORIGINS`.
- `.env.example` ahora documenta `SESSION_COOKIE_SECURE`.
- `.env.example` ahora documenta `SESSION_COOKIE_SAMESITE`.
- `POST /logout` borra la cookie `token` usando `httponly`, `secure` y `samesite` segun configuracion.

Valores recomendados para produccion:

- `ENVIRONMENT=production`
- `FRONTEND_URL=https://<dominio-frontend-real>`
- `ALLOW_DEV_CORS_ORIGINS=false`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=lax` o el valor requerido segun dominio/subdominio real.
- `SECRET_KEY` largo, aleatorio y privado.

Verificacion:

```powershell
.\venv\Scripts\python.exe -m py_compile app\config.py app\main.py app\routes\auth.py
.\venv\Scripts\python.exe -m pytest tests\test_auth_tenant.py
```

Resultado:

- `tests/test_auth_tenant.py`: 5 pruebas pasaron.

Pruebas manuales recomendadas:

- Iniciar sesion como admin y profesor.
- Revisar en DevTools que la cookie `token` sea HttpOnly.
- En entorno HTTPS/productivo, confirmar que `SESSION_COOKIE_SECURE=true` marca cookie Secure.
- Ejecutar logout y confirmar que la cookie `token` desaparece.
- Con `ALLOW_DEV_CORS_ORIGINS=false`, confirmar que solo el dominio `FRONTEND_URL` puede consumir la API.

## 2026-05-26 - Migraciones e indices verificados en tenants activos

Se aplicaron las migraciones SQL pendientes usando el runner oficial `apply_migration.py`.

Tenants activos verificados:

- `tenant_colegio_1` - Colegio Demo
- `tenant_3333` - milagro

Migraciones aplicadas en ambos tenants:

- `20260429_pagos_tipo_pago_largo.sql`
- `20260429_plan_de_clases_reportes.sql`
- `20260509_branding_plantillas_impresion.sql`
- `20260517_tipos_pagos_avanzado.sql`

Comandos ejecutados:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260429_pagos_tipo_pago_largo.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260429_plan_de_clases_reportes.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260509_branding_plantillas_impresion.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260517_tipos_pagos_avanzado.sql
```

Resultado:

- Las 4 migraciones respondieron `OK` en los 2 tenants activos.
- `public.schema_migrations` quedo con historial para las 4 migraciones por cada tenant activo.
- La verificacion posterior mostro `MIGRACIONES_TODAS_OK: True`.

Indices:

- Se verificaron los indices principales por tenant.
- La verificacion posterior mostro `INDICES_TODOS_OK: True`.

Estado del bloque de base de datos:

```text
Base de datos
[x] migraciones aplicadas en todos los tenants activos
[x] indices aplicados
[x] revisar public.schema_migrations
[ ] backup antes de salir
```

Pendiente:

- Hacer backup antes de cualquier salida real a produccion.
- Probar flujo principal de admin/profesor despues de migraciones.

## 2026-05-26 - Inicio centralizacion de cobros en tipos de pago

Se inicio la transicion para que la logica financiera dependa de `tipos_de_pagos`
y `tipos_pagos_cursos`, dejando los valores financieros de `cursos` como fallback
legacy temporal para matricula/mensualidad.

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/pagos_controller.py`
- `app/controllers/estudiante_controller.py`

Cambio:

- Se creo `app/services/cobros.py` como servicio central para:
  - cargar tipos de pago;
  - leer asignaciones por curso desde `tipos_pagos_cursos`;
  - aplicar fallback legacy de `cursos.matricula`, `cursos.mensualidad` y `cursos.meses`;
  - calcular deudas por estudiante usando `app/services/cartera.py`;
  - obtener saldo pendiente por concepto.
- `pagos_controller.py` ya no calcula saldos con una copia local de la logica de matricula/mensualidad.
- `pagos_controller.py` valida el monto del pago contra `obtener_saldo_concepto` del servicio central.
- `estudiante_controller.py` usa `calcular_deudas_estudiante` para poblar `deudas` y `total_deuda`.

Objetivo:

- Evitar logica financiera duplicada en pagos, estudiante, cartera y reportes.
- Preparar el sistema para que antes de produccion los cobros se administren desde Tipos de Pago.
- Mantener compatibilidad mientras se retiran gradualmente los campos financieros del formulario de curso.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\pagos_controller.py', r'app\controllers\estudiante_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Nota:

- `py_compile` no pudo usarse porque Windows nego permisos al escribir `__pycache__`.
- La validacion con `ast.parse` no escribe bytecode y paso correctamente.

Pruebas manuales recomendadas antes de continuar:

- Abrir detalle de un estudiante con deuda y confirmar que `deudas` y `total_deuda` se ven igual o correctamente.
- Registrar un pago parcial de un concepto configurado en Tipos de Pago.
- Intentar registrar un pago mayor al saldo pendiente: debe bloquear.
- Registrar pago de matricula/mensualidad legacy y confirmar que respeta descuento del estudiante.
- Confirmar que conceptos opcionales no generen deuda automatica.

Pendiente:

- Migrar `cartera_mora_controller.py` al servicio central sin perder eficiencia en listados grandes.
- Migrar reportes financieros al mismo servicio.
- Ajustar frontend de Crear Curso para dejar matricula/mensualidad/meses como legacy o retirarlos del flujo principal.

### Cartera vencida conectada al servicio central

Archivos modificados:

- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`

Cambio:

- Se agrego `calcular_deudas_desde_contexto` en `app/services/cobros.py`.
- Esta funcion permite calcular deudas usando datos ya precargados para evitar consultas repetidas por estudiante.
- `cartera_mora_controller.py` ahora usa esa funcion para calcular deuda academica, mora y cuotas vencidas.
- Se conserva la carga agrupada de estudiantes, pagos, ventas y asignaciones para mantener eficiencia en listados grandes.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\cartera_mora_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Abrir cartera vencida general.
- Confirmar que los estudiantes con deuda aparecen con total correcto.
- Filtrar cartera vencida por curso si la pantalla lo permite.
- Confirmar que deuda academica, deuda inventario, mora y total se ven coherentes.
- Confirmar que conceptos opcionales no aparecen como deuda automatica.
- Confirmar que un concepto asignado desde Tipos de Pago a un curso aparece en los estudiantes de ese curso.

Pendiente actualizado:

- Migrar reportes financieros al servicio central.
- Revisar `estado_cuenta_controller.py`, que todavia calcula deuda usando directamente `cursos.matricula`, `cursos.mensualidad` y `cursos.meses`.
- Ajustar frontend de Crear Curso para dejar los campos financieros como legacy/fallback.

### Reporte de estado de cuenta por curso conectado al servicio central

Archivo modificado:

- `app/controllers/reportes_controller.py`

Cambio:

- `reporte_estado_cuenta_curso_controller` ahora usa:
  - `obtener_tipos_pago`;
  - `obtener_asignaciones_cobro_por_curso`;
  - `calcular_deudas_desde_contexto`.
- Se elimino de ese reporte la logica repetida que detectaba manualmente conceptos legacy y calculaba deuda por matricula/mensualidad.
- Se conserva compatibilidad con pagos por `concepto_id`, `tipo_pago` y el formato actual de respuesta.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\services\cobros.py', r'app\controllers\reportes_controller.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Abrir el reporte de estado de cuenta por curso.
- Confirmar que cada estudiante conserva `pagado`, `total`, `deuda` y `deudas_detalle`.
- Confirmar que conceptos asignados desde Tipos de Pago aparecen en el curso correcto.
- Confirmar que matricula/mensualidad legacy siguen funcionando como fallback.
- Registrar un pago y volver a abrir el reporte para verificar que baja la deuda.

Pendiente actualizado:

- Revisar `estado_cuenta_controller.py`, que todavia contiene consultas directas antiguas.
- Ajustar frontend de Crear Curso para que cobros queden en Tipos de Pago y los campos financieros del curso dejen de ser el flujo principal.

### Estado de cuenta conectado al servicio central

Archivo modificado:

- `app/controllers/estado_cuenta_controller.py`

Cambio:

- `estado_cuenta_curso_controller` ya no calcula deuda con la formula fija:
  `cursos.matricula + cursos.mensualidad * cursos.meses`.
- `estado_cuenta_estudiante_controller` tambien usa el servicio central.
- Ambos controladores llaman `calcular_deudas_estudiante`.
- Se conserva el formato de respuesta:
  - `id`;
  - `nombre`;
  - `apellido`;
  - `pagado`;
  - `total`;
  - `deuda`;
  - `tipos_pagos`.

Motivo:

- Hacer que estado de cuenta respete conceptos configurados desde Tipos de Pago.
- Mantener los campos financieros de curso solo como fallback legacy.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'app\controllers\estado_cuenta_controller.py', r'app\services\cobros.py']]; print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.
- No queda la formula directa de `cursos.matricula`, `cursos.mensualidad` y `cursos.meses` en `estado_cuenta_controller.py`.

Pruebas manuales recomendadas:

- Abrir estado de cuenta por curso.
- Abrir estado de cuenta de un estudiante.
- Confirmar que los conceptos de Tipos de Pago afectan deuda/total.
- Confirmar que un pago registrado reduce la deuda.
- Confirmar que matricula/mensualidad legacy siguen funcionando como fallback mientras se ajusta Crear Curso.

### Ajuste de fallback para conceptos asignados con valor 0

Archivo modificado:

- `app/services/cobros.py`

Cambio:

- Si un tipo de pago esta asignado a un curso en `tipos_pagos_cursos` con valor `0`, ya no se toma ese `0` como deuda final automaticamente.
- Nueva regla:
  - si el valor asignado al curso es mayor que `0`, se usa ese valor;
  - si el valor asignado es `0`, se usa el valor global de `tipos_de_pagos`;
  - si tambien es `0` y el concepto es matricula/mensualidad legacy, se usa el valor del curso como fallback.

Motivo:

- Evitar que una asignacion en cero bloquee pagos de matricula o mensualidad.
- Mantener Tipos de Pago como fuente principal sin romper colegios que todavia usan valores financieros en Crear Curso.

Verificacion:

```powershell
.\venv\Scripts\python.exe -c "import ast, pathlib; ast.parse(pathlib.Path(r'app\services\cobros.py').read_text(encoding='utf-8')); print('Sintaxis OK')"
```

Resultado:

- Sintaxis OK.

Pruebas manuales recomendadas:

- Revisar un curso con `matricula` configurada en Crear Curso.
- En Tipos de Pago, confirmar que el concepto Matricula exista y este activo.
- Si Matricula esta asignada al curso con valor `0`, intentar registrar el pago.
- Debe tomar el valor global del tipo de pago o, si es `0`, el valor de matricula del curso.

## 2026-05-26 - Curso queda solo academico y Tipos de Pago queda como fuente unica de deuda

Se cerro la transicion financiera para que los cobros academicos dependan de
`tipos_de_pagos` y `tipos_pagos_cursos`, no de columnas financieras en `cursos`.

Archivos modificados:

- `app/schemas/curso.py`
- `app/controllers/curso_controller.py`
- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/reportes_controller.py`
- `scripts/legacy/crear_cliente.py`
- `migrations/20260526_cursos_solo_academicos.sql`

Cambios:

- `CursoCreate` ya no exige:
  - `matricula`;
  - `mensualidad`;
  - `meses`.
- `crear_curso_controller` solo inserta:
  - `nombre`;
  - `jornada`.
- `actualizar_curso_controller` solo actualiza:
  - `nombre`;
  - `jornada`.
- Los listados de cursos ya no retornan campos financieros.
- `app/services/cobros.py` ya no usa fallback legacy contra `cursos.matricula`, `cursos.mensualidad` ni `cursos.meses`.
- `cartera_mora_controller.py` y `reportes_controller.py` ya no seleccionan ni pasan esos campos al servicio de cobros.
- `scripts/legacy/crear_cliente.py` se habia actualizado para que el SQL base de `cursos` no incluyera columnas financieras.

Migracion aplicada:

- `migrations/20260526_cursos_solo_academicos.sql`

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260526_cursos_solo_academicos.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.
- Verificacion posterior:
  - `tenant_colegio_1`: cursos sin columnas financieras.
  - `tenant_3333`: cursos sin columnas financieras.

Estado nuevo:

```text
Tipos de Pago = fuente unica de deuda academica
Curso = entidad academica
```

Pruebas manuales recomendadas:

- Crear curso nuevo.
- Editar curso existente.
- Crear/asignar un tipo de pago al curso.
- Ver cartera vencida.
- Ver detalle del estudiante.
- Registrar pago de un concepto asignado.
- Confirmar que si un tipo de pago no esta asignado al curso, no genera deuda.

## 2026-05-26 - Nomina expone sueldo del profesor

Se ajusto la consulta de empleados de nomina para devolver el sueldo asignado al
profesor.

Archivo modificado:

- `app/controllers/nomina_controller.py`

Cambio:

- `obtener_estado_cuenta_profesores()` ahora selecciona `COALESCE(p.sueldo, 0) AS sueldo`.
- La respuesta de `/api/nomina/empleados` incluye:
  - `sueldo`;
  - `saldo_prestamos`.

Motivo:

- Permitir que el frontend precargue el campo `Salario Base` en el modal de pago
  de nomina con el sueldo real configurado en el profesor.

Verificacion:

- Sintaxis de `app/controllers/nomina_controller.py`: OK.

Pruebas manuales recomendadas:

- Crear o editar un profesor con sueldo.
- Consultar nomina desde Admin.
- Abrir `Realizar Pago`.
- Confirmar que el salario base coincide con el sueldo del profesor.

## 2026-05-26 - Mensaje claro para tipos de pago duplicados

Se ajusto la creacion/edicion de tipos de pago para devolver una causa clara
cuando el nombre ya existe.

Archivos modificados:

- `app/controllers/tipos_pagos_controller.py`
- `app/routes/tipos_pagos.py`

Cambio:

- Se agrego `TipoPagoDuplicadoError`.
- Antes de crear un tipo de pago se valida si ya existe otro con el mismo nombre,
  ignorando mayusculas/minusculas y espacios al inicio/final.
- Antes de editar un tipo de pago se valida que el nuevo nombre no exista en otro
  registro.
- La API responde `409 Conflict` con un mensaje legible cuando hay duplicado.

Motivo:

- Evitar que el frontend muestre un error generico de servidor cuando el problema
  real es que el concepto ya existe.

Verificacion:

- Sintaxis de `app/controllers/tipos_pagos_controller.py` y `app/routes/tipos_pagos.py`: OK.

Pruebas manuales recomendadas:

- Crear un tipo de pago con un nombre existente.
- Confirmar que responde una alerta de concepto duplicado.
- Editar un tipo de pago y ponerle el nombre de otro existente.
- Confirmar que tambien se bloquea con mensaje claro.

## 2026-05-26 - Normalizacion de nombres academicos en backend

Se agrego normalizacion en backend para guardar nombres con iniciales en
mayuscula en entidades academicas y profesores.

Archivos modificados:

- `app/controllers/profesor_controller.py`
- `app/controllers/curso_controller.py`
- `app/controllers/materia_controller.py`

Cambio:

- Al crear o editar profesor:
  - `nombre` se guarda en formato titulo;
  - `apellido` se guarda en formato titulo;
  - `email` se guarda en minusculas.
- Al crear o editar curso:
  - `nombre` se guarda en formato titulo.
- Al crear o editar materia:
  - `nombre` se guarda en formato titulo.

Motivo:

- Mantener datos consistentes aunque se envie informacion directa por API.
- Evitar listados, boletines, reportes e impresos con nombres en minusculas o
  mayusculas mezcladas.

Verificacion:

- Sintaxis de controladores de profesor, curso y materia: OK.

Pruebas manuales recomendadas:

- Crear profesor con nombre/apellido en minusculas.
- Crear curso con nombre en minusculas.
- Crear materia con nombre en minusculas.
- Confirmar que se listan con iniciales en mayuscula.

## 2026-05-27 - Anulacion auditada de pagos

Se implemento anulacion de pagos sin eliminacion fisica, empezando desde el
historial de pagos del estudiante.

Archivos modificados:

- `migrations/20260527_pagos_anulacion.sql`
- `app/schemas/pago.py`
- `app/controllers/pagos_controller.py`
- `app/routes/pagos.py`
- `app/services/cobros.py`
- `app/controllers/cartera_mora_controller.py`
- `app/controllers/estado_cuenta_controller.py`
- `app/controllers/reportes_controller.py`
- `scripts/legacy/crear_cliente.py`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agregaron columnas a `pagos`:
  - `estado`;
  - `motivo_anulacion`;
  - `fecha_anulacion`;
  - `anulado_por`.
- Se agrego endpoint admin:
  - `POST /pagos/{pago_id}/anular`
- La anulacion exige motivo.
- Los pagos anulados quedan visibles en historial y reportes.
- Cartera, estado de cuenta y calculo de deudas ignoran pagos con `estado = 'Anulado'`.
- Reportes de ingresos mensuales/rango incluyen la huella del pago anulado, pero
  lo devuelven con `monto_valido = 0`.
- Totales generales e ingresos mensuales suman solo pagos validos.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_pagos_anulacion.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Registrar un pago academico.
- Anularlo desde historial de pagos del estudiante con motivo.
- Confirmar que aparece marcado como `Anulado`.
- Confirmar que la deuda vuelve a subir.
- Abrir Reportes > Ingresos Mensuales.
- Confirmar que el pago anulado aparece como huella, pero no suma al total valido.

### Anulacion segura de pagos de inventario

Se amplio la anulacion para cubrir pagos asociados a ventas de inventario.

Archivos modificados:

- `migrations/20260527_pagos_venta_id.sql`
- `app/controllers/pagos_controller.py`
- `scripts/legacy/crear_cliente.py`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agrego `pagos.venta_id`.
- Al registrar un pago de inventario, se guarda el `venta_id`.
- Al anular un pago con `venta_id`, se resta el monto anulado de `ventas.pagado`.
- Si despues de la anulacion la venta vuelve a tener saldo pendiente, `ventas.estado`
  queda en `Pendiente`.
- Para pagos antiguos sin `venta_id`, el backend intenta inferirlo desde la
  descripcion con formato `Cargo #ID`.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_pagos_venta_id.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Crear una venta de inventario a credito.
- Registrar un abono desde pagos del estudiante.
- Confirmar que la venta aumenta `pagado`.
- Anular ese pago desde historial.
- Confirmar que el pago queda anulado.
- Confirmar que la venta vuelve a `Pendiente` y el saldo vuelve a aparecer.

## 2026-05-27 - Anulacion de ventas de inventario

Se agrego anulacion transaccional de ventas de inventario.

Archivos modificados:

- `migrations/20260527_ventas_anulacion.sql`
- `app/controllers/venta_controller.py`
- `app/routes/ventas.py`
- `docs/API_ENDPOINTS.md`
- `docs/MIGRACIONES.md`
- `docs/BASE_DATOS.md`

Cambio:

- Se agregaron columnas a `ventas`:
  - `motivo_anulacion`;
  - `fecha_anulacion`;
  - `anulado_por`.
- Se agrego endpoint admin:
  - `POST /api/ventas/{venta_id}/anular`
- Al anular una venta:
  - la venta queda con `estado = 'Anulada'`;
  - se devuelve el stock de cada item al inventario;
  - se anulan pagos asociados por `venta_id`;
  - se intenta cubrir pagos antiguos asociados por descripcion `Cargo #ID`;
  - `ventas.pagado` vuelve a `0`.

Motivo:

- Evitar eliminacion fisica de ventas.
- Mantener trazabilidad financiera y de inventario.
- Evitar que cartera siga cobrando cargos anulados.

Migracion aplicada:

```powershell
.\venv\Scripts\python.exe apply_migration.py migrations\20260527_ventas_anulacion.sql
```

Resultado:

- `tenant_colegio_1`: OK.
- `tenant_3333`: OK.
- La migracion quedo registrada en `public.schema_migrations`.

Pruebas manuales recomendadas:

- Crear una venta/cargo de inventario.
- Confirmar que baja el stock.
- Anular la venta desde el listado de cargos recientes.
- Confirmar que la venta queda `Anulada`.
- Confirmar que el stock vuelve.
- Si tenia pagos asociados, confirmar que quedan anulados y no suman en reportes.

## 2026-05-27 - Ingresos Hoy usa fecha local Colombia

Se ajusto el calculo de `ingresos_hoy` del reporte general para comparar contra
la fecha local de Colombia.

Archivo modificado:

- `app/controllers/reportes_controller.py`

Cambio:

- Antes usaba `CURRENT_DATE` de PostgreSQL.
- Ahora usa `(NOW() AT TIME ZONE 'America/Bogota')::date`.
- Se mantiene la regla de no sumar pagos con `estado = 'Anulado'`.

Motivo:

- Evitar que Neon/PostgreSQL calcule "hoy" con una zona horaria distinta a la
  fecha local con la que se registran los pagos.

Pruebas manuales recomendadas:

- Registrar un pago con fecha de hoy.
- Abrir Admin > Reportes y Estadisticas.
- Confirmar que `Ingresos Hoy` suma el pago.
- Anular ese pago y confirmar que `Ingresos Hoy` deja de sumarlo.

## 2026-05-27 - Bloqueo de eliminacion fisica de ventas

Se bloqueo el endpoint legacy de eliminacion fisica de ventas.

Archivo modificado:

- `app/routes/ventas.py`

Cambio:

- `DELETE /api/ventas/{venta_id}` ya no elimina la venta.
- Ahora responde `405` con mensaje indicando usar:
  - `POST /api/ventas/{venta_id}/anular`

Motivo:

- Evitar perdida de trazabilidad financiera e inventario.
- Forzar el flujo seguro de anulacion con motivo, devolucion de stock y anulacion
  de pagos asociados.

Pruebas manuales recomendadas:

- Intentar llamar `DELETE /api/ventas/{venta_id}`.
- Confirmar que responde bloqueado.
- Anular una venta desde el frontend y confirmar que usa el endpoint de anulacion.

## 2026-05-27 - Pruebas de anulaciones financieras

Se agregaron pruebas unitarias para blindar los flujos de anulacion financiera.

Archivo agregado:

- `tests/test_anulaciones_financieras.py`

Casos cubiertos:

- Anular pago academico sin tocar ventas.
- Anular pago de inventario descontando el abono de la venta asociada.
- Anular venta con devolucion de stock.
- Anular venta dejando pagos asociados en estado `Anulado`.
- Reporte general excluyendo pagos anulados de ingresos y de ingresos de hoy.
- Formato de ingresos marcando `monto_valido = 0` cuando el pago esta anulado.

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q tests\test_anulaciones_financieras.py -p no:cacheprovider
```

Resultado:

- 5 pruebas pasaron correctamente.

Motivo:

- Evitar regresiones en anulaciones de pagos academicos, pagos de inventario,
  ventas, reportes y devolucion de stock antes de produccion.

## 2026-05-28 - Soporte Cloudflare R2 para uploads

Se agrego una capa de almacenamiento para que logos e imagenes del plan diario puedan guardarse en Cloudflare R2 sin romper las URLs actuales.

Archivos modificados/agregados:

- `app/services/storage.py`
- `app/config.py`
- `app/main.py`
- `app/controllers/branding_controller.py`
- `app/controllers/plan_de_clases_controller.py`
- `.env.example`
- `requirements.txt`
- `docs/PRODUCCION_BACKEND.md`
- `docs/SEGURIDAD.md`

Cambio:

- `STORAGE_PROVIDER=local` mantiene `uploads/` local.
- `STORAGE_PROVIDER=r2` usa Cloudflare R2 compatible con S3.
- `/uploads/...` sigue siendo el endpoint de lectura protegido.
- Se agrego dependencia `boto3`.

Comandos ejecutados:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\config.py app\services\storage.py app\controllers\plan_de_clases_controller.py app\controllers\branding_controller.py app\main.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_uploads_permissions.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- Pruebas de permisos de uploads: 6 pasaron.

Pendiente para activar R2 real:

- Crear bucket en Cloudflare R2.
- Crear Access Key/Secret con permiso sobre el bucket.
- Configurar variables R2 en produccion.
- Reiniciar backend.
- Probar subida/visualizacion/eliminacion de logo y plan diario.

## 2026-05-28 - Carga demo para pruebas SQL de rendimiento

Se agrego script para cargar datos demo de rendimiento en un tenant.

Archivo agregado:

- `scripts/seed_tenant_performance.py`

Comando ejecutado:

```powershell
.\venv\Scripts\python.exe scripts\seed_tenant_performance.py --tenant tenant_colegio_1 --reset
```

Datos cargados en `tenant_colegio_1`:

- 20 cursos `PERF_DEMO`.
- 30 profesores `PERF_DEMO`.
- 12 materias `PERF_DEMO`.
- 80 asignaciones.
- 500 estudiantes.
- 10.000 pagos.
- 20.000 notas detalle.
- 3.000 asistencias.
- 50 productos de inventario.
- 1.000 ventas.
- 1.000 ventas detalle.

Comando para limpiar estos datos:

```powershell
.\venv\Scripts\python.exe scripts\seed_tenant_performance.py --tenant tenant_colegio_1 --clean
```

Primeros resultados de `EXPLAIN ANALYZE`:

- `reporte_general_ingresos_hoy`: usa `Seq Scan` sobre `pagos`, ~5 ms con 10.000 pagos.
- `reporte_ingresos_mes`: usa `Seq Scan` por `TO_CHAR(COALESCE(...))`, ~3.7 ms con 10.000 pagos.
- `reporte_ingresos_rango`: usa `Seq Scan`, ~0.94 ms con 10.000 pagos.
- `ventas_paginado`: usa `Seq Scan` + sort sobre `ventas`, ~0.32 ms con 1.000 ventas.
- `cartera_estudiantes`: usa `Seq Scan` en estudiantes activos y nested loop con cursos, ~1 ms con 500 estudiantes.

Lectura tecnica:

- Con datos demo actuales el sistema responde rapido.
- El primer riesgo de crecimiento esta en reportes de pagos por fecha porque usan funciones sobre fecha (`DATE`, `TO_CHAR`, `COALESCE`) que no aprovechan bien indices simples.
- Siguiente paso recomendado: optimizar reportes de pagos con rangos de fecha e indices de expresion o columna normalizada para fecha efectiva.

## 2026-05-28 - Dashboard profesor: filtros seguros por curso

Se ajustaron endpoints del dashboard profesor para soportar ranking de inasistencias por curso y filtro de notas por curso.

Archivos modificados:

- `app/controllers/dashboard_controller.py`
- `app/routes/dashboard.py`
- `app/routes/asignaciones.py`

Cambio:

- `/dashboard/inasistencias/{profesor_id}` ahora devuelve ranking por curso.
- `/dashboard/notas-bajas/{profesor_id}` acepta `curso_id` opcional.
- `/dashboard/notas-altas/{profesor_id}` acepta `curso_id` opcional.
- `/mis-clases/{profesor_id}` incluye `curso_id` para que el frontend pueda filtrar por cursos asignados.

Seguridad:

- Se mantiene `require_profesor_scope` para evitar consultar datos de otro profesor.
- Si llega `curso_id`, el backend valida que ese curso pertenezca a una asignacion del profesor.
- Si el profesor intenta cambiar el `curso_id` manualmente por uno no asignado, debe responder `403`.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\dashboard_controller.py app\routes\dashboard.py app\routes\asignaciones.py
```

Pruebas manuales recomendadas:

- Entrar como profesor y abrir el dashboard.
- Probar notas bajas/altas seleccionando un curso y luego `Todas las materias` o una materia especifica.
- Probar manualmente un `curso_id` no asignado en `/dashboard/notas-bajas/{profesor_id}?curso_id=ID` y confirmar `403`.
- Confirmar que `/dashboard/inasistencias/{profesor_id}` lista ranking por curso.

Correccion del dashboard profesor:

- El filtro final de notas bajas/altas exige `curso_id`.
- Opcionalmente acepta `asignacion_id` para filtrar una materia especifica dentro de ese curso.
- Si no se envia `asignacion_id`, calcula `Todas las materias` que ese profesor dicta en el curso seleccionado.
- El backend valida que el curso pertenezca al profesor.
- Si se envia asignacion, valida que la asignacion pertenezca al profesor y al curso seleccionado.

## 2026-05-28 - Tests de uploads aislados de R2

Se ajustaron las pruebas de permisos de uploads para que no dependan del `.env`
real ni del bucket Cloudflare R2 configurado en desarrollo/produccion.

Archivo modificado:

- `tests/test_uploads_permissions.py`

Cambio:

- Cada prueba que crea archivos temporales locales fuerza
  `using_remote_storage()` a `False` mediante `monkeypatch`.
- Esto permite probar permisos de branding, plan de clases, tenant y path
  traversal usando archivos temporales locales.
- La aplicacion real puede seguir usando `STORAGE_PROVIDER=r2` sin que estas
  pruebas intenten consultar el bucket.

Motivo:

- Con `STORAGE_PROVIDER=r2`, el backend busca archivos en R2.
- Estas pruebas no suben objetos al bucket; crean archivos temporales locales.
- Sin aislar el storage, las pruebas fallaban con `404` aunque la logica de
  permisos pudiera estar correcta.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q tests\test_uploads_permissions.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- 6 pruebas pasaron correctamente.
- Se elimino la carpeta temporal `.pytest_tmp` despues de la verificacion.

## 2026-05-30 - Retiro de endpoint legacy de boletin

Se retiro la ruta legacy `POST /boletin/guardar` del router de notas.

Archivos modificados:

- `app/routes/notas.py`
- `app/controllers/notas_controller.py`
- `app/schemas/nota.py`
- `docs/API_ENDPOINTS.md`
- `docs/CAMBIOS_BACKEND.md`

Motivo:

- El frontend actual y el build generado usan `POST /boletines/guardar`.
- La ruta nueva valida `require_asignacion_access` y
  `require_estudiante_in_asignacion`.
- La ruta legacy no aparecia usada por el frontend actual y quedaba como
  superficie innecesaria antes de produccion.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q tests\test_auth_tenant.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- 34 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-05-30 - Estados SaaS iniciales por tenant

Se agrego soporte backend para controlar el estado operativo inicial de cada
tenant desde `public.colegios.estado`.

Estados reconocidos:

- `activo`
- `en_mora`
- `suspendido`
- `cancelado`

Archivos modificados/agregados:

- `app/core/tenant_status.py`
- `app/controllers/auth_controller.py`
- `app/dependencies.py`
- `app/routes/auth.py`
- `app/routes/tenant.py`
- `app/main.py`
- `apply_migration.py`
- `scripts/check_tenant_schemas.py`
- `scripts/apply_tenant_indexes.py`
- scripts historicos de migracion puntual en `scripts/`
- `tests/test_auth_tenant.py`
- `tests/test_apply_migration.py`
- `docs/API_ENDPOINTS.md`
- `docs/MULTITENANT.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/SEGURIDAD.md`

Cambio:

- `POST /login` permite tenants `activo` y `en_mora`.
- `POST /login` rechaza tenants `suspendido` y `cancelado`.
- `get_current_user` revalida el estado del tenant en cada peticion
  autenticada.
- Estados vacios o desconocidos se normalizan como `suspendido` para bloquear
  por defecto.
- Se agrego `GET /tenant/status` para que el frontend pueda mostrar avisos
  cuando el tenant este `en_mora`.
- La respuesta de login incluye `tenant_estado` como dato informativo.
- Los scripts operativos de migraciones, comparacion de schemas e indices ahora
  incluyen tenants `activo` y `en_mora`.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\core\tenant_status.py app\controllers\auth_controller.py app\dependencies.py app\routes\auth.py app\routes\tenant.py app\main.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 44 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-05-30 - Rol super admin inicial

Se agrego el primer control de plataforma para administrar tenants desde la app.

Archivos modificados/agregados:

- `app/core/super_admin.py`
- `app/controllers/super_admin_controller.py`
- `app/routes/super_admin.py`
- `app/controllers/auth_controller.py`
- `app/main.py`
- `migrations/public/20260530_super_admins.sql`
- `scripts/create_super_admin.py`
- `tests/test_super_admin.py`
- `docs/API_ENDPOINTS.md`
- `docs/ROLES_PERMISOS_BACKEND.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- `super_admin` inicia sesion por el mismo `POST /login` usando codigo
  `super_admin`.
- `super_admin` usa `tenant = public` en el JWT, pero solo lo acepta
  `get_current_super_admin`.
- `get_current_user` sigue rechazando `public` para usuarios de colegios.
- Se agregaron endpoints `GET /super-admin/tenants` y
  `PATCH /super-admin/tenants/{tenant_id}/estado`.
- Se agrego script para crear/actualizar el primer super admin con password
  hasheada.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\core\super_admin.py app\controllers\super_admin_controller.py app\routes\super_admin.py app\controllers\auth_controller.py app\main.py scripts\create_super_admin.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 50 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-06-01 - Mensaje claro para tenants suspendidos/cancelados

Se separo el error de login por credenciales del error por estado SaaS del
colegio.

Archivos modificados:

- `app/core/tenant_status.py`
- `app/controllers/auth_controller.py`
- `app/routes/auth.py`
- `tests/test_auth_tenant.py`
- `docs/SEGURIDAD.md`

Cambio:

- Si el colegio no existe o las credenciales no validan, `POST /login` sigue
  respondiendo `401`.
- Si el colegio existe pero esta `suspendido` o `cancelado`, `POST /login`
  responde `403` con `detail.code = tenant_blocked`, `estado` y mensaje
  especifico.
- Esto evita mostrar "credenciales incorrectas" cuando en realidad el servicio
  esta bloqueado por estado del tenant.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\core\tenant_status.py app\controllers\auth_controller.py app\routes\auth.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 52 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

## 2026-06-01 - Auditoria de cambios de estado de tenant

Se agrego trazabilidad para cambios de estado SaaS realizados por super admin.

Archivos modificados/agregados:

- `app/controllers/super_admin_controller.py`
- `app/routes/super_admin.py`
- `migrations/public/20260601_tenant_estado_auditoria.sql`
- `tests/test_super_admin.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`

Cambio:

- Al cambiar estado de tenant se registra auditoria en
  `public.tenant_estado_auditoria`.
- La auditoria guarda estado anterior, estado nuevo, motivo, super admin y
  fecha.
- Se agrego `GET /super-admin/tenants/{tenant_id}/estado-auditoria` para
  consultar los ultimos 50 cambios.
- Si el estado solicitado es igual al actual, no se crea registro de auditoria.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\super_admin_controller.py app\routes\super_admin.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 8 pruebas de super admin pasaron correctamente.

## 2026-06-01 - Creacion de colegios desde super admin

Se agrego el flujo backend para crear nuevos colegios desde el panel de
plataforma.

Archivos modificados/agregados:

- `app/controllers/super_admin_controller.py`
- `app/routes/super_admin.py`
- `migrations/public/20260601_tenant_suscripciones.sql`
- `tests/test_super_admin.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/MIGRACIONES.md`
- `docs/PRODUCCION_BACKEND.md`
- `docs/CHECKLIST_PRODUCCION_BACKEND.md`
- `docs/PLAN_EJECUCION_BACKEND.md`

Cambio:

- Se agrego `POST /super-admin/tenants`.
- El endpoint crea `public.colegios`, schema `tenant_<codigo>`, tablas desde
  `DEFAULT_TENANT_SCHEMA`, branding inicial, plantillas iniciales y admin
  inicial con password hasheada.
- Se agrego `public.tenant_suscripciones` para guardar fecha de inicio,
  proximo pago y dias de gracia.
- El listado de tenants ahora devuelve datos basicos de suscripcion.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\super_admin_controller.py app\routes\super_admin.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py tests\test_permissions.py tests\test_notas_permissions.py tests\test_uploads_permissions.py tests\test_anulaciones_financieras.py -p no:cacheprovider --basetemp=.pytest_tmp
```

Resultado:

- Sintaxis OK.
- 58 pruebas pasaron correctamente.
- Solo quedaron warnings conocidos de `slowapi` y configuracion legacy de
  Pydantic.

Actualizacion posterior:

- `app/core/tenant_status.py` calcula el estado efectivo usando
  `public.tenant_suscripciones`.
- Si vencio `fecha_proximo_pago` pero esta dentro de `dias_gracia`, el estado
  efectivo es `en_mora`.
- Si vencieron tambien los dias de gracia, el estado efectivo es `suspendido`.
- Esto se usa en login y en revalidacion de sesiones existentes.

## 2026-06-01 - Cierre fase SaaS super admin

Se cerraron endurecimientos previos a produccion para la operacion SaaS.

Archivos modificados/agregados:

- `app/controllers/auth_controller.py`
- `app/controllers/super_admin_controller.py`
- `app/routes/auth.py`
- `app/routes/super_admin.py`
- `app/core/tenant_status.py`
- `app/security.py`
- `apply_migration.py`
- `migrations/public/20260601_tenant_eventos_auditoria.sql`
- `migrations/20260601_usuarios_password_obligatorio.sql`
- `tests/test_super_admin.py`
- `tests/test_auth_tenant.py`
- `tests/test_apply_migration.py`

Cambio:

- El listado de tenants devuelve `estado` efectivo por fecha de pago y
  `estado_manual` como estado administrativo guardado.
- Se quito la creacion automatica de tablas publicas desde consultas normales.
  Las tablas publicas deben existir por migracion antes del deploy.
- `apply_migration.py` detecta archivos dentro de `migrations/public/` y los
  aplica contra `public`, incluso si no hay tenants registrados.
- Al crear colegio se exige password temporal fuerte para el admin inicial.
- El admin inicial se crea con `debe_cambiar_password = TRUE`.
- Se agrego `POST /auth/cambiar-password` para que el admin cambie la password
  temporal y apague `debe_cambiar_password`.
- Crear colegio registra evento en `public.tenant_eventos_auditoria`.
- `crear_cliente.py` y `setup_saas.py` se movieron a `scripts/legacy/` para
  evitar usarlos por error; el flujo oficial queda en el panel super admin.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\auth_controller.py app\controllers\super_admin_controller.py app\routes\auth.py app\routes\super_admin.py app\core\tenant_status.py app\security.py apply_migration.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_super_admin.py tests\test_auth_tenant.py tests\test_apply_migration.py --basetemp=.pytest_tmp
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260530_super_admins.sql
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260601_tenant_estado_auditoria.sql
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260601_tenant_suscripciones.sql
.\venv\Scripts\python.exe apply_migration.py migrations\public\20260601_tenant_eventos_auditoria.sql
.\venv\Scripts\python.exe apply_migration.py migrations\20260601_usuarios_password_obligatorio.sql
```

Resultado:

- Sintaxis OK.
- 33 pruebas enfocadas pasaron correctamente.
- Migraciones publicas SaaS registradas/aplicadas en local.
- `debe_cambiar_password` aplicado en `tenant_colegio_1` y `tenant_3333`.
- `listar_tenants_controller()` devolvio los colegios locales con `estado` y
  `estado_manual`.

## 2026-06-02 - Asignaciones activas y asignador unico

Se reestructuro el flujo de asignacion de clases para proteger historial
academico y dejar un solo asignador administrativo.

Archivos modificados/agregados:

- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260602_asignaciones_activo.sql`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/BASE_DATOS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- `asignaciones` ahora usa `activo = TRUE/FALSE`.
- `DELETE /asignaciones/{asignacion_id}` desactiva la asignacion y conserva
  planes de clase, asistencia, notas, boletines y observaciones.
- Los listados actuales, horarios, clases del profesor y validaciones de cruce
  solo consideran asignaciones activas.
- Se agrego `GET /profesores/{profesor_id}/disponibilidad?dia=<dia>` para
  calcular rangos libres del profesor.
- El backend valida que las horas queden dentro de `06:30-12:30` o
  `12:30-18:30`.
- Si una asignacion ya tiene historial academico, no se permite cambiar
  profesor, curso o materia; se debe desactivar y crear una nueva.

Frontend relacionado:

- `src/components/AsignarClase.jsx` queda como unico asignador tipo formulario.
- `src/components/AsignarClaseGrid.jsx` se retiro porque ya no forma parte del
  flujo oficial.
- El admin selecciona primero curso, luego profesor/materia/dia/horas, ve
  disponibilidad del profesor y abajo el horario activo del curso.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -m py_compile app\controllers\asignacion_controller.py app\routes\asignaciones.py
.\venv\Scripts\python.exe -B -m pytest -q tests\test_asignaciones_activo.py tests\test_asignaciones_pagination.py --basetemp=.pytest_tmp
python apply_migration.py migrations\20260602_asignaciones_activo.sql --dry-run
python apply_migration.py migrations\20260602_asignaciones_activo.sql
```

Resultado:

- Sintaxis backend OK.
- 5 pruebas enfocadas de asignaciones pasaron correctamente.
- Build frontend `pnpm run build` OK.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.

## 2026-06-04 - Reportes con egresos y balance

Se amplio el modulo de reportes para mostrar egresos y balance financiero.

Archivos modificados/agregados:

- `app/controllers/reportes_controller.py`
- `app/routes/reportes.py`
- `tests/test_reportes_pagination.py`
- `tests/test_anulaciones_financieras.py`
- `docs/API_ENDPOINTS.md`

Cambio:

- `GET /reportes/general` ahora incluye:
  - `total_egresos`;
  - `egresos_hoy`;
  - `balance_general`;
  - `balance_hoy`;
  - `egresos_mensuales`.
- Se agrego `GET /reportes/egresos-rango?inicio=YYYY-MM-DD&fin=YYYY-MM-DD`.
- El endpoint de egresos por rango conserva compatibilidad con respuesta lista
  simple si no se envia `limit`, y respuesta paginada si se envia `limit`.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest tests\test_reportes_pagination.py tests\test_anulaciones_financieras.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_reportes
```

Resultado:

- Ruff OK.
- 12 pruebas enfocadas de reportes/anulaciones pasaron correctamente.
- 127 pruebas completas pasaron correctamente.

## 2026-06-04 - Prestamos sin eliminacion y filtro por profesor

Se ajusto el modulo de prestamos para conservar trazabilidad financiera y
evitar borrado fisico.

Archivos modificados/agregados:

- `app/controllers/prestamo_controller.py`
- `app/routes/prestamos.py`
- `tests/test_prestamos_validaciones.py`
- `docs/API_ENDPOINTS.md`

Cambio:

- `GET /api/prestamos/` permite filtrar por `profesor_id`.
- `POST /api/prestamos/` valida profesor, monto mayor que 0 y estado inicial
  `Pendiente`.
- La fecha faltante se completa con el dia actual y las notas se normalizan con
  `strip()`.
- `PUT /api/prestamos/{prestamo_id}/estado` solo permite saldar con estado
  `Pagado`.
- `DELETE /api/prestamos/{prestamo_id}` queda bloqueado con `405`; los
  prestamos no se eliminan fisicamente.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest tests\test_prestamos_validaciones.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_prestamos
```

Resultado:

- Ruff OK.
- 9 pruebas enfocadas de prestamos pasaron correctamente.
- 125 pruebas completas pasaron correctamente.

## 2026-06-04 - Estados operativos de estudiantes y profesores

Se implemento manejo por estado para estudiantes y profesores, manteniendo
historial y evitando borrado fisico antes de produccion.

Archivos modificados/agregados:

- `app/schemas/estudiante.py`
- `app/controllers/estudiante_controller.py`
- `app/routes/estudiantes.py`
- `app/schemas/profesor.py`
- `app/controllers/profesor_controller.py`
- `app/routes/profesores.py`
- `app/controllers/auth_controller.py`
- `app/controllers/asignacion_controller.py`
- `app/controllers/planilla_excel_controller.py`
- `app/controllers/boletin_controller.py`
- `app/controllers/notas_controller.py`
- `migrations/20260604_profesor_estado.sql`
- `tests/test_estudiantes_pagination.py`
- `tests/test_catalogos_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Estudiantes soportan estados `activo`, `retirado`, `egresado`, `inactivo`.
- Profesores soportan estados `activo`, `inactivo`.
- `GET /estudiantes` y `GET /profesores` filtran `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agregaron `PATCH /estudiantes/{estudiante_id}/estado` y
  `PATCH /profesores/{profesor_id}/estado`.
- Estudiantes que no estan `activo` quedan fuera de planillas, asistencia y
  boletines del flujo operativo del profesor, sin perder historial.
- Profesores `inactivo` no pueden iniciar sesion ni ser asignados/actualizados
  en asignaciones activas.
- El login ya no devuelve `access_token` ni `token_type` en JSON; la sesion
  queda por cookie `HttpOnly`.
- La migracion `20260604_profesor_estado.sql` agrega `profesor.estado`,
  normaliza profesores existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_profesor_estado.sql
```

Resultado:

- Ruff OK.
- 96 pruebas pasaron correctamente.
- Migracion aplicada en `tenant_colegio_1`, `tenant_3333` y `tenant_4444`.
- Frontend relacionado probado con `pnpm run build` y `pnpm run lint`.

## 2026-06-04 - Estado operativo de cursos

Se implemento manejo por estado para cursos, manteniendo historial academico y
evitando borrado fisico.

Archivos modificados/agregados:

- `app/schemas/curso.py`
- `app/controllers/curso_controller.py`
- `app/routes/cursos.py`
- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260604_cursos_estado.sql`
- `tests/test_catalogos_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Cursos soportan estados `activo` e `inactivo`.
- `GET /cursos` filtra `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agrego `PATCH /cursos/{curso_id}/estado`.
- Cursos `inactivo` no pueden usarse en nuevas asignaciones ni en ediciones de
  asignaciones activas.
- Las vistas operativas de asignaciones, horarios y clases del profesor filtran
  cursos activos para no seguir usando cursos cerrados.
- La migracion `20260604_cursos_estado.sql` agrega `cursos.estado`, normaliza
  cursos existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_cursos_estado.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_cursos_estado.sql
```

Resultado:

- Ruff OK.
- 99 pruebas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.
- Un dry-run posterior mostro la migracion como omitida por ya aplicada.

## 2026-06-04 - Estado operativo de materias

Se implemento manejo por estado para materias, manteniendo historial academico
y evitando borrado fisico.

Archivos modificados/agregados:

- `app/schemas/materia.py`
- `app/controllers/materia_controller.py`
- `app/routes/materias.py`
- `app/controllers/asignacion_controller.py`
- `app/routes/asignaciones.py`
- `migrations/20260604_materias_estado.sql`
- `tests/test_catalogos_pagination.py`
- `tests/test_asignaciones_activo.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Materias soportan estados `activo` e `inactivo`.
- `GET /materias` filtra `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agrego `PATCH /materias/{materia_id}/estado`.
- Materias `inactivo` no pueden usarse en nuevas asignaciones ni en ediciones
  de asignaciones activas.
- Las vistas operativas de asignaciones, horarios y clases del profesor filtran
  materias activas para no seguir usando materias cerradas.
- La migracion `20260604_materias_estado.sql` agrega `materias.estado`,
  normaliza materias existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_materias
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_materias_estado.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_materias_estado.sql
```

Resultado:

- Ruff OK.
- 102 pruebas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.
- Un dry-run posterior mostro la migracion como omitida por ya aplicada.

## 2026-06-04 - Estado operativo de productos de inventario

Se implemento manejo por estado para productos de inventario, manteniendo
historial de ventas y evitando borrado fisico.

Archivos modificados/agregados:

- `app/schemas/inventario.py`
- `app/controllers/inventario_controller.py`
- `app/routes/inventario.py`
- `app/controllers/venta_controller.py`
- `app/routes/ventas.py`
- `migrations/20260604_inventario_estado.sql`
- `tests/test_inventario_pagination.py`
- `tests/test_anulaciones_financieras.py`
- `docs/API_ENDPOINTS.md`
- `docs/PRODUCCION_BACKEND.md`

Cambio:

- Productos de inventario soportan estados `activo` e `inactivo`.
- `GET /inventario` filtra `activo` por defecto.
- `estado=todos` permite consulta administrativa/historica.
- Se agrego `PATCH /inventario/{item_id}/estado`.
- `DELETE /inventario/{item_id}` ahora desactiva el producto y conserva
  historial de ventas.
- Productos `inactivo` no aparecen para nuevas ventas y el backend rechaza
  intentos de venderlos por API.
- La migracion `20260604_inventario_estado.sql` agrega `inventario.estado`,
  normaliza productos existentes a `activo` y crea indice por estado.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_inventario
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_inventario_estado.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_inventario_estado.sql
```

Resultado:

- Ruff OK.
- 105 pruebas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.
- Un dry-run posterior mostro la migracion como omitida por ya aplicada.

## 2026-06-04 - Egresos filtrados por fecha y sin eliminacion fisica

Se ajusto el modulo de egresos para consultar por fechas y conservar
trazabilidad contable.

Archivos modificados/agregados:

- `app/controllers/egreso_controller.py`
- `app/controllers/nomina_controller.py`
- `app/routes/egresos.py`
- `migrations/20260604_egresos_origen.sql`
- `tests/test_egresos_fechas.py`
- `docs/API_ENDPOINTS.md`

Cambio:

- `GET /api/egresos/` devuelve por defecto solo los egresos del dia actual.
- Se agregaron filtros `fecha_desde` y `fecha_hasta`.
- Si se envia solo `fecha_desde`, se consulta ese dia.
- Si se envia rango, se valida que `fecha_desde <= fecha_hasta`.
- `POST /api/egresos/` valida concepto obligatorio, categoria obligatoria y
  monto mayor que 0 antes de insertar en base de datos.
- Los datos de texto del egreso se normalizan con `strip()` y la fecha faltante
  se completa con el dia actual.
- Se agrego `egresos.origen` para diferenciar egresos `manual` de egresos
  automaticos.
- Los egresos creados desde este modulo quedan con `origen = manual`.
- Los egresos creados por nomina quedan con `origen = nomina`.
- Se agrego `PUT /api/egresos/{egreso_id}` para editar solo egresos manuales.
- Si se intenta editar un egreso automatico, el backend responde `403`.
- `DELETE /api/egresos/{egreso_id}` queda bloqueado con `405`; los egresos no
  se eliminan fisicamente.

Verificacion ejecutada:

```powershell
$env:RUFF_CACHE_DIR = "$env:TEMP\ruff-cache-sistema-escolar"; .\venv\Scripts\python.exe -m ruff check app tests scripts apply_migration.py
.\venv\Scripts\python.exe -m pytest tests\test_egresos_fechas.py
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_egresos_origen.sql --dry-run
.\venv\Scripts\python.exe apply_migration.py migrations\20260604_egresos_origen.sql
.\venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_egresos_edit
```

Resultado:

- Ruff OK.
- 11 pruebas enfocadas de egresos pasaron correctamente.
- 116 pruebas completas pasaron correctamente.
- Dry-run de migracion OK en `tenant_colegio_1`, `tenant_3333` y
  `tenant_4444`.
- Migracion aplicada en los tres tenants locales.

## 2026-06-04 - Certificados usan notas de planilla como respaldo

Se ajusto la generacion administrativa de boletines/certificados para que las
notas se reflejen aunque todavia no exista una cabecera de boletin guardada.

Archivos modificados:

- `app/controllers/boletin_controller.py`

Cambio:

- `GET /boletines/admin/generar/{estudiante_id}/{periodo}` mantiene primero la
  definitiva guardada en `boletin_cabecera`.
- Si esa definitiva no existe, calcula un promedio desde `notas_detalle` para
  el mismo estudiante, asignacion y periodo.
- Si la definitiva guardada es `0`, se trata como ausencia de definitiva y se
  permite usar el promedio real de planilla, porque las notas numericas validas
  del sistema van de 1 a 5.
- El promedio de respaldo solo considera `notas_detalle.nota > 0`.
- Las notas `0` guardadas en detalles de boletin no se devuelven como notas
  numericas validas por periodo.
- Se excluyen valoraciones de desarrollo del promedio numerico.

Motivo:

- Certificados y boletines administrativos deben poder mostrar notas ya
  registradas en planilla, incluso antes de que el profesor guarde el resumen
  final del boletin.

Verificacion ejecutada:

```powershell
.\venv\Scripts\python.exe -B -c "import ast, pathlib; ast.parse(pathlib.Path('app/controllers/boletin_controller.py').read_text(encoding='utf-8'))"
```

Resultado:

- Sintaxis OK.






