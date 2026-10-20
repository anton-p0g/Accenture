# Prototipo 1 · Preocupación por el cambio climático (19/10/2026)

Script: `trabajo/02_prototipo_clima.py` (módulos `armonizar.py`, `modelo.py`).
Entrena con CIS 3536 (dic 2025) → aplica a 25.000 personas sintéticas → valida con CIS 3577 (sep 2026, no visto).

## Resultados (% "mucho + bastante" preocupado/a)
| Comprobación | Error medio | Sin modelo* |
|---|---|---|
| Misma ola (dic 2025): población 72,4 % vs real 71,8 % | 0,6 pts | — |
| A) Directa a sep 2026: total | 8,4 pts | — |
| B) Re-anclada (solo total nacional conocido) · sexo | 1,8 pts | 7,0 |
| B) · edad | 3,0 pts | 3,7 |
| B) · CCAA (19) | 5,3 pts (74 % dentro del margen de la encuesta) | 4,8 |

*Sin modelo = dar a cada grupo el total nacional.

## Lecturas
1. La población + modelo reproduce bien la misma ola (0,6 pts) → el enlace población↔CIS funciona.
2. El mayor error es el **cambio real de opinión en el tiempo** (+9 pts entre dic 2025 y sep 2026, verano de incendios). Hay que anclar el nivel con el dato más reciente y ensanchar la incertidumbre cuando el dato es antiguo.
3. Las diferencias por **sexo y edad** se predicen bien. Por **CCAA** no mejora a la referencia: con ~100 entrevistas por comunidad la señal está dentro del ruido → necesitamos juntar varias olas por pregunta.

## Arreglos hechos sobre la base del equipo
- La columna `estudios` procesada infra-representa estudios básicos (20 % vs ~40 % en ECV/CIS) → uso `estudios_ecv`.
- Las 5.636 personas extranjeras no tienen ideología/religión → promedio sobre la distribución real del CIS de su mismo sexo, edad y estudios (antes el error era de 15 pts; ahora 0,6 pts en la misma ola).
