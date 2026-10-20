# Estudios CIS candidatos para Pulso (2025–2026)

Fuente: catálogo de cis.es (1ª página, 48 estudios más recientes) + búsquedas web.
Lista completa capturada en `catalogo_cis.csv`.
⚠️ Contenido de preguntas NO verificado salvo el 3528: hay que revisar el cuestionario de cada uno.

## Ya revisado
- **3528 Barómetro oct 2025** (n=4.029) → `cis3528/`. Opinión útil para los 6 temas:
  - P10R "principales problemas de España": vivienda 37,1 %, sanidad 13,4 %, medio ambiente 0,4 %
  - P11R "problema que más le afecta": vivienda 26,2 %, sanidad 22,3 %, soledad/problemas psicológicos 1,3 %
  - P8/P9 situación económica personal y de España (→ consumo)
  - El resto es política (voto, líderes, Franco, Gaza) → no sirve para los 6 temas.

## Candidatos por tema
| Tema | Estudio(s) | Por qué |
|---|---|---|
| Vivienda | Barómetros mensuales (3530, 3536, 3540, 3544, 3546, 3557, 3562, 3567, 3571, 3577) | Misma pregunta de "problemas" cada mes → serie temporal y validación con meses reservados |
| Soledad | 3535 Tendencias sociales (V), dic 2025; IV de nov 2024; 3547 Navidad | Tendencias IV incluía soledad (79,9 % prevé que aumente) |
| Tecnología / IA | 3535 Tendencias sociales (V); 3554 Temores en la sociedad actual; 3534 Miedos e incertidumbres; 3563 Desinformación | Probables preguntas sobre IA y tecnología (verificar) |
| Medio ambiente | Barómetros (pregunta "¿le preocupa el cambio climático?" repetida desde 2022 — verificar en 2025-26) | Serie temporal |
| Salud | 8825 Barómetro Sanitario 2025 (total oleadas, ~7.800 entrevistas); 3531; 3551 Sanitario 2026 | Muestra grande → mejor para desglose por CCAA |
| Consumo / banca | ICC mensual (3529, 3533, 3537, 3542, 3549, 3552, 3559, 3565, 3569, 3575); 3560 Inclusión financiera | Mensual → ideal para validar; 3560 sirve para la pregunta de banca (P4) |

## Prioridad de descarga (mínimo viable, 8 estudios)
1. 3528 Barómetro oct 2025 (ya usado por la población: mismos donantes)
2. 3536 Barómetro dic 2025 y 3577 Barómetro sep 2026 (validación temporal)
3. 3535 Tendencias sociales (V)
4. 3554 Temores en la sociedad actual
5. 8825 Barómetro Sanitario 2025 (total)
6. 3575 ICC julio 2026
7. 3560 Inclusión financiera

## Cómo descargar (manual: el CIS exige formulario y bloquea descargas automáticas)
Catálogo: https://www.cis.es/es/estudios/catalogo → buscar el número → "Microdatos" → rellenar formulario →
se descarga `MDxxxx.zip` (incluye `xxxx.sav`, `xxxx_num.csv`, `xxxx_etiq.csv`, cuestionario y libro de códigos).
Guardar cada zip en: `~/maverick_versionJJ/datos_cis/zips/`
