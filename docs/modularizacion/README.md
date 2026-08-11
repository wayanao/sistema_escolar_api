# Guía maestra de evolución segura del backend

Última revisión: 2026-08-11.

## Propósito

Este directorio conserva el contexto operativo necesario para mejorar el
backend por capas y continuar el trabajo en chats o modelos distintos sin leer
todo el historial del proyecto.

Aunque la carpeta se llama `modularizacion`, el programa no contiene únicamente
movimientos arquitectónicos. Incluye primero calidad, base de datos,
concurrencia y migraciones; la modularización por dominios comienza después.

Este documento define el orden. La bitácora activa define el trabajo concreto.
Un asistente no debe cambiar el orden ni ampliar el alcance sin aprobación del
usuario.

## Resultado buscado

Evolucionar el monolito FastAPI para soportar más colegios y datos con menor
riesgo, conservando:

- endpoints, métodos, status codes y payloads;
- permisos, roles, ownership y aislamiento entre tenants;
- cálculos, transacciones y efectos laterales actuales;
- compatibilidad con el frontend desplegado;
- PostgreSQL, `psycopg2` y el modelo de schemas tenant durante este programa.

No se autoriza una reescritura, microservicios, cambio de driver, ORM, rediseño
funcional ni una corrección oportunista ajena a la capa activa.

## Orden aprobado

| Orden | Capa | Resultado principal | Estado | Bitácora |
|---:|---|---|---|---|
| 0 | Línea base y calidad | Pruebas deterministas, compuerta global y CI | **Cerrada**; CI verificada en remoto | [00_LINEA_BASE_CALIDAD.md](./00_LINEA_BASE_CALIDAD.md) |
| 1 | Fundación de base de datos | Conexiones, transacciones, timeouts y pool definidos | **Cerrada**; calibración de `statement_timeout` pendiente y aceptada | [01_FUNDACION_BASE_DATOS.md](./01_FUNDACION_BASE_DATOS.md) |
| 2 | Concurrencia | DB síncrona fuera del event loop preservando `ContextVar` | En espera | Se crea al activarla |
| 3 | Migraciones y tenants | Todos los tenants versionados, runner bloqueado y alta reproducible | En espera | Se crea al activarla |
| 4 | Reportes financieros | Dominio modular, N+1 eliminado y consultas medidas | En espera | Se crea al activarla |
| 5 | Pagos y tipos de pago | Dominio financiero modularizado y protegido | En espera | Se crea al activarla |
| 6 | Asignaciones y estudiantes | Dominios grandes separados con contratos estables | En espera | Se crea al activarla |
| 7 | Resto de dominios | Migración individual con contratos y pruebas | En espera | Una bitácora por dominio al activarlo |

No se crea por anticipado un documento por cada dominio. Cuando una capa se
cierre y el usuario ordene continuar, se crea su sucesora desde
`PLANTILLA_CAPA.md`, se registra el commit base vigente y se actualiza esta
tabla.

Actualmente no hay una capa activa. Las capas 0 y 1 están cerradas. La capa 2
permanece en espera y no debe inferirse como activa: solo se creará su bitácora
cuando el usuario lo ordene explícitamente.

## Alcance de cada capa

### 0. Línea base y calidad

- Documentar contratos que deberán conservarse.
- Corregir exclusivamente las tres pruebas sensibles al reloj.
- Crear un comando global y reproducible de verificación.
- Agregar CI que ejecute la misma compuerta.

### 1. Fundación de base de datos

- Eliminar aperturas manuales progresivamente, sin migración masiva.
- Definir propiedad de `commit`, `rollback`, cursor y conexión.
- Establecer timeouts y manejo del pool con evidencia.
- Mantener `psycopg2`.

### 2. Concurrencia

- Sacar operaciones DB síncronas del event loop mediante un threadpool
  controlado.
- Preservar y probar correctamente el `ContextVar` del tenant.
- Medir concurrencia antes y después.

No basta con convertir dependencias a `def`: la propagación del tenant forma
parte del contrato de seguridad.

### 3. Migraciones y tenants

- Verificar y aplicar migraciones a todos los tenants reactivables.
- Agregar bloqueo para impedir ejecuciones simultáneas.
- Sustituir progresivamente la copia de un tenant plantilla por un alta basada
  en migraciones versionadas.
- Ensayar primero en una base de prueba o staging y preparar rollback.

### 4. Reportes financieros

- Primer dominio que se modulariza.
- Separar HTTP, reglas, servicios y persistencia.
- Eliminar el N+1 mediante consultas agrupadas equivalentes.
- Medir consultas críticas con `EXPLAIN ANALYZE` sobre datos no productivos.

### 5. Pagos y tipos de pago

- Segundo dominio por criticidad financiera.
- Proteger montos, saldos, comprobantes, idempotencia y transacciones.
- Mantener contratos del frontend y de la base de datos.

### 6. Asignaciones y estudiantes

- Migrar después de estabilizar las capas financieras.
- Trabajar cada dominio en subcapas y evitar una extracción conjunta masiva.
- Proteger permisos, relaciones académicas, archivos e historial.

### 7. Resto de dominios

- Priorizar uno a la vez cuando llegue esta etapa.
- Agregar `response_model`, errores de dominio y pruebas HTTP o de integración
  solo después de caracterizar y conservar la respuesta existente.
- No crear abstracciones compartidas sin dos consumidores reales.

## Paquete mínimo de contexto para un chat nuevo

Un chat nuevo debe leer completamente y en este orden:

1. `docs/modularizacion/README.md`;
2. la bitácora marcada como `Activa` en la tabla o, si no existe una, la
   bitácora cerrada más reciente que conserve verificaciones pendientes;
3. las instrucciones locales del repositorio, si existen;
4. únicamente los archivos fuente y pruebas relacionados con la subcapa activa.

Si no hay una capa marcada como `Activa`, el asistente puede completar o
registrar las verificaciones pendientes de la última capa cerrada, pero no debe
iniciar una capa nueva sin orden expresa del usuario.

No necesita leer todo `docs/`, `CAMBIOS_BACKEND.md` ni bitácoras cerradas, salvo
que el documento activo señale una sección concreta.

El usuario puede copiar siempre el mismo archivo
`PROMPT_CONTINUACION.md`. El prompt no contiene el nombre fijo de una capa: el
índice maestro le indica al asistente cuál está activa.

## Comprobaciones antes de modificar

El asistente debe:

1. confirmar la rama acordada;
2. confirmar que `git status` esté limpio;
3. comparar `HEAD` con el commit base registrado en la bitácora activa;
4. revisar que los commits posteriores al base estén explicados allí;
5. detenerse ante cambios ajenos, divergencias o un base ambiguo.

El commit base es el punto anterior a la capa activa. Se actualiza al activar
una capa nueva; no se reutiliza automáticamente el base inicial del programa.

## Regla de ejecución por turnos

- Ejecutar únicamente la primera subcapa pendiente de la bitácora activa.
- Agregar o conservar pruebas antes de una extracción importante.
- No iniciar la siguiente subcapa en el mismo turno.
- Actualizar la bitácora con archivos, comandos, resultados y decisiones.
- Registrar riesgos y la siguiente acción exacta.
- No hacer commit, push, deploy, acceso a producción ni migraciones reales.

Si aparece un defecto ajeno, se documenta. Solo se corrige si impide verificar
la subcapa y el usuario aprueba la ampliación.

## Verificación proporcional

Cada subcapa debe ejecutar:

1. pruebas específicas;
2. Ruff sobre el alcance modificado;
3. la compuerta global cuando ya exista o al cerrar la capa;
4. `git diff --check`;
5. revisión del alcance del diff.

La última subcapa de una capa debe incluir pruebas completas, lint,
dependencias, instrucciones de staging, rollback y verificación manual aplicable.

## Estado inicial registrado

- Repositorio: `sistema_escolar_api`.
- Rama al crear esta guía: `main` alineada con `origin/main`.
- Commit: `b8c7653445a50bc1e230a19e0ca8bb088c47cb69`.
- Árbol de trabajo al crear esta guía: limpio.
- Capa activa: 0, línea base y calidad.
- Código de producto modificado por esta guía: ninguno.

## Estado actual

- Repositorio: `sistema_escolar_api`.
- Rama acordada: `main`.
- Capa 0 **cerrada** el 2026-08-11, sin verificaciones pendientes.
- Compuerta global: 192 pruebas correctas, Ruff correcto y `pip check` correcto,
  tanto en local como en un checkout limpio de GitHub Actions.
- Último commit publicado y verificado en remoto:
  `b20dcbe43a64c25e2ece7a7a99782983e2626160`.
- Ejecución remota de GitHub Actions: el primer run, sobre `23bce41`, **falló**.
  `pytest` y `pip check` terminaron en exit 0, pero Ruff reportó 460 errores
  porque la instalación limpia resolvió `ruff>=0.5.0` a una versión mayor con
  otro conjunto de reglas por defecto. Se corrigió con el tope
  `ruff>=0.5.0,<0.16` y el run sobre `b20dcbe` terminó **correctamente**.
- Capa 1 **cerrada** el 2026-08-11. Commit base:
  `6754e4aad59c1e428ea97d31fe8e96fdbba7694d`; 17 commits, todos explicados en su
  bitácora.
- Resultado de la capa 1: las 50 aperturas de conexión sin cierre garantizado
  llegaron a **0**, incluidas 2 que fugaban en un camino normal; ninguna ruta
  abre conexiones; hay 4 timeouts donde antes no existía ninguno; la suite pasó
  de 192 a **334** pruebas.
- Los timeouts se aplican con `set_config(..., TRUE)` por transacción, no en el
  paquete de arranque: el endpoint `-pooler` de Neon es PgBouncer y rechaza la
  conexión entera si recibe parámetros que no sabe rastrear. Verificado contra la
  base real.
- **Verificación operativa pendiente y aceptada** de la capa 1: calibrar
  `DB_STATEMENT_TIMEOUT_MS` contra la duración real de las consultas pesadas. El
  usuario la aceptó para no bloquear el cierre; el valor puede ajustarse por
  entorno sin desplegar código. No debe marcarse como cumplida.
- Capa activa: ninguna.
- Siguiente capa: 2, concurrencia, en espera de autorización explícita.
- Código de producto modificado durante la capa 0: ninguno.
- Código de producto modificado durante la capa 1: el ciclo de vida de las
  conexiones en 20 archivos de `app/`, más los timeouts. Sin cambios en rutas,
  payloads, status codes, permisos, tenant, ownership ni SQL observable.

## Archivos de continuidad

- [01_FUNDACION_BASE_DATOS.md](./01_FUNDACION_BASE_DATOS.md): bitácora cerrada de
  la capa 1; conserva pendiente la calibración de `statement_timeout` y registra
  la lección de que un cambio en el pool no se verifica solo con pruebas
  herméticas.
- [00_LINEA_BASE_CALIDAD.md](./00_LINEA_BASE_CALIDAD.md): bitácora cerrada de
  la capa 0, sin verificaciones pendientes; conserva la compuerta, la CI y el
  inventario de contratos que la capa 1 debe preservar.
- [PROMPT_CONTINUACION.md](./PROMPT_CONTINUACION.md): texto para iniciar o
  continuar en otro chat.
- [PLANTILLA_CAPA.md](./PLANTILLA_CAPA.md): estructura de la siguiente bitácora.
