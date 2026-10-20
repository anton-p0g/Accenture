# Inventario de microdatos CIS (19/10/2026)

8 estudios descargados → `datos_cis/microdatos/<n>/` (sav, csv, cuestionario, libro de códigos).
Detalle pregunta a pregunta: `inventario_preguntas.csv` (script: `trabajo/01_inventario_cis.py`).

## Tamaño y variables para enlazar con la población sintética
| Estudio | Tema | n | CCAA | Sexo | Edad | Estudios | Ideología | Religión | Sit. laboral | Municipio | Peso |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3528 Barómetro oct 2025 | general | 4.029 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3536 Barómetro dic 2025 | general | 4.017 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3577 Barómetro sep 2026 | general | 4.042 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3535 Tendencias sociales V | tecnología, soledad | 4.031 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3554 Temores | soledad, vivienda, salud | 5.015 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 8825 Barómetro Sanitario 2025 | salud, IA en salud | 7.197 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3560 Inclusión financiera | banca, consumo | 1.597 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3575 ICC jul 2026 | consumo, vivienda | 3.004 | ✓ | (otro nombre) | (otro nombre) | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |

Total: ~33.000 entrevistas reales.

## Preguntas clave por tema
- **Vivienda**: principales problemas de España / personales (PESPANNA, PPERSONAL) en 3528, 3536, 3577; temor a no poder pagar vivienda (3554 P2_11); intención de compra y precio esperado (3575 P17, P18); alquilaría su vivienda (3536 P8_1).
- **Soledad**: temor a la soledad (3554 P2_5); temor a quedarse solo/a sin apoyo emocional (3554 P16); soledad como tendencia futura (3535 IDEASPROS2_4).
- **Tecnología / IA**: opinión sobre la IA (3535 DESIN_9); robots y empleo (3535 SAT1, SAT2, IDEASPROS4_3); miedo al control por las nuevas tecnologías (3554 P13); **IA en sanidad: hablar con asistente IA, IA que lee radiografías, cirugía con robot, seguimiento con IA** (8825 P21–P25).
- **Medio ambiente**: **preocupación por el cambio climático, misma pregunta y escala en dic 2025 (3536 P1) y sep 2026 (3577 P13)** → validación temporal; incendios y pacto de Estado (3577 P8–P12); energías renovables (3535 DESIN_3).
- **Salud**: Barómetro Sanitario (82 preguntas), consumo de ansiolíticos (3554 P14), temor a perder la salud (3554 P2_13).
- **Consumo**: situación económica personal y de España (3528, 3536, 3577); confianza del consumidor (3575, 32 preguntas); banca digital (3560 P2).

## Implicaciones
- Todos los estudios comparten las variables de la población sintética → enlace directo, sin inventar nada.
- Hay preguntas repetidas en varias olas → podemos entrenar con una y validar con otra (dic 2025 → sep 2026).
- La P1 del equipo (IA para cuidar a un familiar) tiene un equivalente real cercano: 8825 P22 (IA en la atención sanitaria).
