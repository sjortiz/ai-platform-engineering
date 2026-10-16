# AI Platform Engineering — El blocker eres tú

Charla para el [BarCamp RD](https://barcamp.org.do): cada vez que automatizamos un paso, el cuello de botella se mueve. Un recorrido de CI/CD a los agentes de IA, con la seguridad que trae cada paso y ejemplos para aplicar en tu empresa.

**Ver la presentación:** https://sjortiz.github.io/ai-platform-engineering/

## Cómo se navega

| Tecla | Acción |
|---|---|
| ← → | Paso anterior / siguiente |
| ↑ ↓ | Extras y preguntas de seguridad del paso (el botón de arriba indica cuál flecha) |
| Inicio / Fin | Portada / mapa completo |

También puedes hacer clic en cualquier punto del minimapa.

## Editar

El contenido vive en `src/detalle.py` y las fuentes de cada hito en `src/fuentes.py`. Para regenerar la página:

```bash
python3 build.py
```

La versión en inglés (`en/`) se genera en el mismo paso con la tabla `i18n/en.json`. Si cambias un texto, `build.py` lista los que no tienen traducción y esos quedan en español.
