# Base profesional para escalar el Sistema Escolar API

Ultima revision documental: 2026-09-03.

Este proyecto es una API web escolar multi-tenant construida con FastAPI y PostgreSQL. La prioridad de esta base es crecer sin romper las funcionalidades actuales: estudiantes, pagos, notas, asistencia, boletines, inventario, reportes, nomina y administracion por colegio.

## Objetivos de arquitectura

- Mantener PostgreSQL como base principal.
- Aislar datos por colegio usando schemas tenant.
- Evitar conexiones nuevas por cada consulta bajo alta concurrencia.
- Separar responsabilidades para que nuevas funcionalidades no terminen en controladores gigantes.
- Versionar cambios de base de datos con migraciones.
- Proteger rutas por autenticacion y, progresivamente, por roles.

## Estructura recomendada

La estructura actual sigue funcionando. La evolucion recomendada es esta:

```text
app/
  core/           configuracion transversal: logging, seguridad, settings
  db/             pool, sesiones, tenant context y helpers de transaccion
  routes/         endpoints HTTP
  controllers/    capa actual; migrar gradualmente a services/repositories
  services/       reglas de negocio
  repositories/   consultas SQL por modulo
  schemas/        modelos Pydantic de entrada y salida
docs/             documentacion operativa y decisiones tecnicas
migrations/       migraciones de base de datos
```

No es necesario reescribir todo de una vez. Cada modulo nuevo o modificado deberia acercarse a esta estructura.

## Cambios aplicados en esta base

### Pool de conexiones

`app/database.py` sigue exponiendo `get_connection()` para no romper controladores existentes, pero ahora delega en `app/db/session.py`.

Beneficios:

- Reduce el costo de abrir conexiones repetidamente.
- Permite controlar el maximo de conexiones con variables de entorno.
- Deja listo un helper `get_cursor()` para nuevos modulos.

Variables sugeridas:

```env
DB_POOL_MIN_CONNECTIONS=1
DB_POOL_MAX_CONNECTIONS=10
```

Para produccion, ajusta `DB_POOL_MAX_CONNECTIONS` segun el limite real de PostgreSQL y la cantidad de workers.

Regla importante:

- El pool evita abrir conexiones nuevas por cada consulta, pero no corrige una
  fuga de conexiones.
- Todo uso manual de `get_connection()` debe cerrar cursor y conexion en
  `finally`.
- Codigo nuevo deberia usar `get_cursor()` salvo que necesite control manual de
  transaccion.
- Si Render muestra `connection pool exhausted`, revisar primero rutas
  recientes o muy concurridas que usen `get_connection()`.

#### Coste real de una conexion, medido el 2026-09-03

Los valores sugeridos arriba se escribieron sin medir. Contra la base real
—Neon, `us-east-1`, desde un backend local— el coste es este:

| Operacion | Tiempo |
|---|---|
| Abrir una conexion nueva (TLS + auth) | **1329 ms** |
| Una ida y vuelta cualquiera (`SELECT 1`) | **~180 ms** |
| Arranque de cada conexion (`SET search_path` + `set_config`) | **~390 ms** |

Tres consecuencias practicas:

- **`DB_POOL_MIN_CONNECTIONS=1` hace que la primera rafaga pague 1329 ms por
  cada conexion que el pool tenga que crear.** Con varias peticiones simultaneas
  tras un arranque en frio, ese peaje se acumula. Subirlo pre-calienta el pool,
  pero cambia el consumo de conexiones contra Neon y conviene decidirlo mirando
  el limite real del plan.
- **Cada `get_connection()` cuesta dos consultas antes de la util.** Una ruta que
  pida tres conexiones para atender una peticion gasta seis idas y vueltas
  —mas de un segundo— solo en preparar sesiones. Prestar el cursor entre capas,
  como hacen `require_asignacion_access` y `require_estudiante_in_asignacion` con
  su parametro `cursor=`, evita ese gasto.
- **Ninguna consulta es lenta por si misma; lo que pesa es la distancia.**
  `information_schema.columns` tarda lo mismo que `SELECT 1`. Al optimizar,
  contar **idas y vueltas** predice el tiempo mucho mejor que juzgar que consulta
  parece cara.

La regla que se deriva: **el numero de idas y vueltas por peticion es la metrica
que importa**, no la complejidad del SQL. Un caso trabajado de punta a punta,
con el reparto exacto de las 17 idas y vueltas que costaba leer una observacion,
esta en `modularizacion/07_OBSERVACIONES.md`, entrada del 2026-09-03.

Aviso sobre entornos: correr el backend en local **no** acerca la base. El
frontend apunta a `localhost:8000`, pero `DATABASE_URL` sigue siendo Neon en otro
continente. «Es local» no significa «es rapido», y medir contra `/health` no
sirve para estimar un endpoint autenticado: hay que medir el endpoint real.

### Tenant mas seguro

El schema del tenant ahora pasa por validacion en `app/db/tenant.py` antes de aplicar `search_path`.

Esto reduce el riesgo de usar valores malformados del JWT. A futuro, el siguiente paso es validar el tenant contra `public.colegios` y cachear esa validacion por pocos minutos.

### Logging

Se agrego `app/core/logging.py` para usar logging estandar en lugar de `print`.

Variable sugerida:

```env
LOG_LEVEL=INFO
```

### Shutdown limpio

FastAPI ahora cierra el pool de base de datos al apagar la aplicacion.

### Rutas de boletines protegidas

`/boletines/*` ahora usa `Depends(get_current_user)`, igual que el resto de modulos privados.

## Patron recomendado para nuevos controladores

Para codigo nuevo, evita abrir y cerrar conexiones manualmente.

```python
from app.database import get_cursor


def crear_recurso(data):
    with get_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO tabla (campo)
            VALUES (%s)
            RETURNING id
            """,
            (data.campo,),
        )
        return cursor.fetchone()[0]
```

Para consultas:

```python
from app.database import get_cursor


def listar_recursos():
    with get_cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM tabla ORDER BY nombre")
        return cursor.fetchall()
```

## Migraciones

Migrar no significa cambiar PostgreSQL. Significa versionar cambios de tablas, columnas, indices y relaciones.

Ejemplos de migraciones:

```sql
ALTER TABLE estudiantes ADD COLUMN acudiente_email VARCHAR(255);
CREATE INDEX idx_pagos_estudiante_id ON pagos(estudiante_id);
```

La recomendacion es usar Alembic. Flujo esperado:

```bash
alembic init migrations
alembic revision -m "agregar indices principales"
alembic upgrade head
```

Como tu app usa schemas por colegio, las migraciones deben considerar:

- cambios en `public`, por ejemplo `colegios`;
- cambios repetidos en cada schema tenant;
- una tabla de control para saber que tenants fueron migrados.

## Indices prioritarios

Revisar y agregar primero:

```sql
CREATE INDEX IF NOT EXISTS idx_estudiantes_curso_id ON estudiantes(curso_id);
CREATE INDEX IF NOT EXISTS idx_pagos_estudiante_id ON pagos(estudiante_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_estudiante_fecha ON asistencia(estudiante_id, fecha);
CREATE INDEX IF NOT EXISTS idx_notas_detalle_estudiante_asignacion ON notas_detalle(estudiante_id, asignacion_id);
CREATE INDEX IF NOT EXISTS idx_boletin_cabecera_lookup ON boletin_cabecera(estudiante_id, asignacion_id, periodo);
CREATE INDEX IF NOT EXISTS idx_asignaciones_curso_id ON asignaciones(curso_id);
CREATE INDEX IF NOT EXISTS idx_asignaciones_profesor_id ON asignaciones(profesor_id);
```

Antes de aplicarlos en produccion, deben pasar por migracion y probarse en una copia de datos.

## Reglas para seguir escalando

- Cada listado grande debe tener paginacion.
- Cada endpoint debe tener `response_model`.
- Los errores internos no deben devolverse con `str(e)` al usuario.
- Las reglas de negocio deben ir a `services`, no a rutas.
- Las consultas SQL deben ir migrando a `repositories`.
- Cada conexion abierta manualmente debe cerrarse aunque la request falle.
- Cada modulo critico debe tener pruebas: login, pagos, boletines, notas, cartera y asistencia.
- Cada cambio de base de datos debe ser una migracion, no un SQL suelto aplicado manualmente.

## Proxima fase recomendada

1. Revisar que los tenants operativos (`activo` y `en_mora`) tengan la misma estructura.
2. Agregar indices principales por tenant.
3. Crear migraciones Alembic reales.
4. Refactorizar primero `estudiante_controller.py`, `pagos_controller.py` y `boletin_controller.py`.
5. Agregar permisos por rol: admin, profesor y otros roles futuros.
6. Agregar tests de integracion sobre PostgreSQL de prueba.

## Flujo simple para tus colegios

Aunque hoy tengas colegios demo, la configuracion correcta es:

- `public.colegios` guarda el registro de cada colegio.
- Cada colegio tiene su schema `tenant_*`.
- Todos los schemas tenant deben tener las mismas tablas.
- Ningun script de mantenimiento debe borrar tablas ni datos sin una orden explicita.

Para revisar sin modificar nada:

```bash
python scripts/check_tenant_schemas.py
```

Para aplicar indices recomendados sin borrar tablas:

```bash
python scripts/apply_tenant_indexes.py
```

Ese segundo script solo usa `CREATE INDEX IF NOT EXISTS`. Si una tabla no existe en un tenant demo, la omite y lo reporta.

## Crear nuevos colegios

El flujo oficial para crear colegios es el panel `/super-admin`, boton
`Crear colegio`. El backend usa `POST /super-admin/tenants` para crear un
schema nuevo copiando la estructura desde el schema configurado en:

```env
DEFAULT_TENANT_SCHEMA=tenant_colegio_1
```

Eso significa que `tenant_colegio_1` funciona como plantilla inicial mientras no tengamos Alembic completo. Por eso, antes de crear colegios reales, conviene tener ese tenant con todas las tablas actuales.

El flujo no elimina tablas existentes. Si el codigo del colegio ya existe, la transaccion se revierte.
