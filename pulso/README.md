# pulso · motor con datos reales del CIS + nuevo frontend

Esta carpeta conecta la población sintética del equipo (`data/poblacion_sintetica_procesada.csv`, 25.000 personas)
con **respuestas reales del CIS** y añade un **frontend nuevo** (`pulso/frontend/`). No sustituye nada de `web/` ni `frontend/`.

## Cómo predice
- **La pregunta ya la hizo el CIS** (banco de ~300 preguntas reales): modelo entrenado con los microdatos de esa encuesta
  y aplicado a las 25.000 personas → semáforo **verde** (error medido ±0,5–2 pp).
- **Pregunta nueva, campaña o test A/B**: pulso elige ~100 personas sintéticas de perfiles distintos y un LLM local
  (llama3.1:8b), usando su contexto y sus actitudes medidas en el CIS, predice qué respondería cada una; luego se extiende
  a las 25.000 → semáforo **ámbar/rojo** (error medido ±15 pp; un LLM sin datos: ±16 pp y con estereotipos).

## Arrancar
```bash
pip install -r pulso/requirements.txt
ollama pull llama3.1:8b && ollama pull bge-m3
cd pulso/trabajo && python -m uvicorn servidor:app --port 8765   # → http://127.0.0.1:8765
```
Las preguntas de `resultados/cache_consultas/` responden al instante. Las nuevas necesitan Ollama.

## Qué hay
| Carpeta | Contenido |
|---|---|
| `trabajo/` | Motor: `armonizar.py` (CIS ↔ población), `modelo.py`, `banco_preguntas.py`, `simulador.py` (LLM), `motor.py`, `servidor.py` (API + web) y scripts 01–07 |
| `frontend/` | Web nueva (inicio con mapa de puntos, 5 vistas, campañas y A/B, «LLM sin datos vs pulso», validación) |
| `resultados/perfiles/` | Actitudes CIS de cada persona sintética (24 preguntas) y sus modelos |
| `resultados/banco_ampliado/` | Banco de 297 preguntas CIS reescritas con su enunciado real y su modelo por pregunta |
| `resultados/calibracion_simulador/` | Validación del LLM con preguntas reales tratadas como nuevas |
| `resultados/cache_consultas/`, `cache_comparar/` | Consultas ya calculadas (demo) |
| `docs/` | Resumen técnico y capturas |

## Microdatos del CIS (no incluidos)
El CIS entrega los ficheros tras un formulario, así que no se redistribuyen aquí. Para reentrenar: descargar el «Fichero datos»
de los estudios 3528, 3535, 3536, 3554, 3560, 3569, 3575, 3577 y 8825 en cis.es y descomprimirlos en
`pulso/datos_cis/microdatos/<número>/`. Lista y motivos en `datos_cis/ESTUDIOS_CANDIDATOS.md`.

## Arreglos sobre la base del equipo
- La columna `estudios` procesada infra-representa estudios básicos (20 % vs ~40 % en ECV/CIS): el motor usa `estudios_ecv`.
- Los 5.636 extranjeros no tienen ideología/religión: el motor promedia sobre la distribución real del CIS de su perfil.
