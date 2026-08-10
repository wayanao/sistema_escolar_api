# Prompt para continuar la evolución del backend

Este mismo prompt puede reutilizarse en cada chat. El plan maestro identifica
automáticamente la bitácora activa y la primera subcapa pendiente.

```text
Vamos a continuar el programa de evolución segura del backend.

Lee completamente y en este orden:
1. docs/modularizacion/README.md
2. el documento que ese índice marque como bitácora Activa
3. las instrucciones locales del repositorio, si existen

Después inspecciona únicamente la documentación, archivos fuente y pruebas
relacionados con la primera subcapa pendiente. No leas historiales globales ni
todo el repositorio salvo que la bitácora activa dirija a una sección concreta.

Antes de modificar:
1. Confirma la rama acordada.
2. Confirma que git status esté limpio.
3. Comprueba el commit base registrado en la bitácora activa.
4. Revisa que todo commit posterior al base esté explicado en la bitácora.
5. Si hay cambios anteriores, una rama incorrecta o divergencia no documentada,
   informa el problema y no mezcles ni sobrescribas cambios.

Trabaja exclusivamente en la capa activa e implementa únicamente su primera
subcapa pendiente. No inicies otra subcapa en el mismo turno. Conserva rutas,
payloads, status codes, permisos, tenant, ownership, SQL observable,
transacciones y comportamiento actual, salvo que la bitácora autorice de forma
explícita un cambio concreto.

No agregues funciones nuevas, no hagas rediseños, no corrijas asuntos ajenos,
no cambies tecnologías y no crees abstracciones compartidas sin dos usos reales.
Antes de una extracción importante, agrega o conserva pruebas de
caracterización.

Al terminar la subcapa:
- ejecuta las pruebas específicas y las verificaciones exigidas;
- ejecuta git diff --check;
- revisa que el diff pertenezca exclusivamente a la subcapa;
- actualiza la bitácora activa con archivos, comandos y resultados;
- registra decisiones, riesgos y la siguiente acción exacta;
- informa cuál es la siguiente subcapa, pero no la inicies.

Cuando sea la última subcapa de una capa, ejecuta también la compuerta global,
documenta staging, rollback y verificación manual, y actualiza el índice maestro.
No actives la capa siguiente sin mi orden.

No hagas commit, push, deploy, migraciones reales ni acceso a producción.
Yo revisaré los cambios y controlaré la publicación.
```

## Uso

1. Abrir un chat nuevo dentro de `sistema_escolar_api`.
2. Copiar el bloque anterior sin agregar el historial del chat viejo.
3. El asistente encontrará la capa activa desde el índice.
4. Verificar que su resumen mencione la misma capa, subcapa y commit base que la
   bitácora antes de permitir cambios.

Si dos asistentes indican capas diferentes, prevalece el estado guardado en
`README.md` y en la bitácora activa, no la memoria de la conversación.
