# Resumen de la noche (19-20 oct 2026)

## Qué hay nuevo
- **Banco ampliado**: 259 preguntas reales del CIS (antes 24). El LLM reescribió cada variable usando el enunciado real del libro de códigos; cada pregunta tiene su modelo entrenado con microdatos (error en la misma ola: 0,1–1 pp). Más preguntas del público salen en verde.
- **Etiquetas de escala legibles**: «Incómodo/a (1-3)», «Le suscita el máximo miedo o temor (7-10)», en vez de «Bajo (0-3)».
- **Vista por edad**: columnas al 100 %, % en cada franja, leyenda dentro del gráfico.
- **Lo que más se asocia**: cada respuesta explica qué actitudes / ideología / edad van con la opción ganadora.
- **Panel «¿Cómo lo sabemos?»** (clic en el semáforo): validación de cada modo con tabla y gráfico simulado vs real.
- **Filtro automático** si la pregunta nombra un grupo («los jóvenes», «las mujeres»…).
- **16 preguntas de demo precalculadas** (respuesta instantánea): `trabajo/05_precalcular_demo.py`.

## Números de la validación
| Modo | Error | Base |
|---|---|---|
| Verde · evidencia CIS | ±0,5 pp (misma ola) | 24 preguntas, ~25.000 entrevistas |
| Predicción en el tiempo (clima dic 25 → sep 26) | 1,8 pp por sexo, 3,0 por edad, 5,3 por CCAA | sin modelo: 7,0 / 3,7 / 4,8 |
| Rojo · simulación LLM (preguntas tratadas como nuevas) | ±15,7 pp por opción | repartir a partes iguales: 19,2 pp; solo demografía: 16,3 pp |

Lectura honesta: los datos reales del CIS son lo que hace fiable a pulso. El LLM aporta poco por sí solo
(las actitudes CIS lo mejoran algo: 16,3 → 15,4–15,7 pp) y no sabe los niveles de opinión en España;
por eso la estrategia es **cubrir con evidencia real todo lo posible** y marcar en rojo el resto.
Probé además: pedir al LLM el % directamente (16,5 pp) y «estirar» el reparto (no mejora).

## Para arrancar
`cd ~/maverick_versionJJ/trabajo && ../.venv/bin/python -m uvicorn servidor:app --port 8765` → http://127.0.0.1:8765

## Pendiente (hoy)
- Versión publicada + QR para el viernes (GitHub Pages o Netlify: elegir).
- Más estudios CIS de 2021-2024 activarían el selector de años y más preguntas en verde.
