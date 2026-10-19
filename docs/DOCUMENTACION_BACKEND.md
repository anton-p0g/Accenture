# Memoria técnica del backend — Synthetic Spain AI
**GenAI Mavericks Challenge 2026** · Actualizado: 19/10/2026 · Rama: `feature/backend-fastapi`
> Prototipo experimental: los porcentajes P1–P4 son resultados modelados y NO encuestas ni pronósticos validados.

## 1. Objetivo y alcance
En esta fase del GenAI Mavericks Challenge de Accenture he desarrollado y probado el backend de un prototipo de consulta sobre población sintética española. El propósito es formular preguntas en lenguaje natural, seleccionar segmentos demográficos y devolver cálculos reproducibles realizados sobre DuckDB.

El resultado es un prototipo experimental. Las respuestas P1–P4 proceden de probabilidades definidas mediante hipótesis de simulación, no de entrevistas reales ni de un modelo predictivo validado. Esta distinción se indica expresamente al usuario.

## 2. Inicio del trabajo: GitHub y entorno local
Comencé trabajando con el repositorio colaborativo del equipo, clonado en mi ordenador Windows y abierto desde Visual Studio Code. Preparé mi desarrollo en la rama feature/backend-fastapi para separar mis cambios de la rama principal.

Configuré el entorno virtual .venv con Python 3.12 y las dependencias necesarias: FastAPI, Uvicorn, DuckDB, pandas, NumPy y el cliente de Ollama. Instalé y comprobé el modelo local qwen3:4b. La carpeta .venv debe permanecer fuera del control de versiones.

Comandos de arranque habituales: .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload; documentación API en http://127.0.0.1:8000/docs; frontend de pruebas en http://127.0.0.1:8000/chat.

Nota de trazabilidad: no dispongo aquí del historial real de commits; por ello describo las etapas realizadas, sin inventar fechas, hashes, ni órdenes exactos de ejecución.

## 3. Análisis de la base inicial
Revisé la base data/poblacion_sintetica.duckdb del equipo y su tabla poblacion: aproximadamente 25.000 perfiles sintéticos del año 2025, 58 columnas y edades entre 18 y 100 años.

Comprobé categorías y ponderaciones para saber qué filtros podían consultarse. La suma de pesos de la población base era aproximadamente 48.092.860, cifra que requiere revisar la calibración antes de describirla como población adulta española representativa.

Esta base original no se sustituyó por el módulo de escenarios: el trabajo de proyecciones se mantuvo en una base DuckDB independiente.

## 4. Primer backend de consulta
Organicé el servicio web con FastAPI. En backend/database.py implementé funciones de conexión y consulta read-only, metadatos, resumen general y distribuciones ponderadas, controlando las variables permitidas.

En backend/segmentos.py incorporé validación de solicitudes y cálculos ponderados por segmento, con normalización de etiquetas y filtros. En backend/agente.py integré Ollama para interpretar preguntas del conjunto inicial de 2025 y utilizar herramientas de consulta.

Conecté las rutas en backend/main.py y comprobé los endpoints básicos, especialmente /health, /metadata, /estadisticas/resumen, /estadisticas/distribucion, /estadisticas/segmento y /ask. Las estadísticas numéricas se calculan en la base de datos; el modelo lingüístico interpreta o presenta información.

## 5. Ampliación a escenarios 2020–2027
Incorporé el paquete de escenarios con un catálogo de cuatro preguntas sociales: P1, asistencia con IA para cuidar familiares mayores; P2, regulación de pisos turísticos; P3, campañas de ahorro energético; y P4, preferencias al cambiar de banco.

El archivo escenarios_perfiles_2020_2027.csv contiene 200.000 filas sintéticas: 25.000 perfiles simulados en cada año entre 2020 y 2027. No representan 200.000 personas diferentes encuestadas. Se generan mediante reglas e hipótesis a partir de la base de población.

Añadí datos observados separados de indicadores seleccionados del INE, contexto CIS y proyecciones macroeconómicas etiquetadas como experimentales. Los perfiles retrospectivos 2020–2024 son reconstrucciones artificiales, no observaciones históricas de preferencias.

Integré scripts/generar_escenarios.py y scripts/importar_escenarios.py para generar e importar los archivos. La base resultante es data/escenarios_sinteticos.duckdb y contiene, entre otras, las tablas opiniones_escenario, indicadores_observados e indicadores_proyectados.

En backend/escenarios.py expuse el catálogo, consultas ponderadas por escenarios y lectura de indicadores. En backend/chat_escenarios.py añadí un intérprete basado en Qwen3 para traducir la pregunta del usuario a un año, tema, filtros y rango de edad, y después consultar DuckDB.

## 6. Frontend de pruebas y conexión
Para ensayar el backend sin interferir con el desarrollo del frontend definitivo de otro miembro del equipo, preparé frontend_pruebas/index.html, una interfaz HTML/CSS/JavaScript sencilla que envía las preguntas mediante fetch a POST /escenarios/chat.

En backend/main.py habilité la ruta /chat para mostrar la interfaz de pruebas. Se mantuvo el frontend/ independiente del compañero, sin sobrescribir sus archivos.

El contrato de integración es una petición JSON como {"pregunta":"..."} a /escenarios/chat y una respuesta con texto, interpretación, evidencias y fiabilidad. El frontend definitivo deberá procesar las estructuras disponibles y tratar los errores.

## 7. Problemas encontrados y correcciones
Interpretación incorrecta de edades: inicialmente Qwen3 podía añadir una edad no solicitada. Corregí el sistema para extraer edades de forma determinista desde la propia pregunta y dejar edad_min/edad_max en null cuando el usuario no pide ninguna.

Filtros inventados: detecté un caso donde el modelo añadió uso_ia_escenario="No" aunque no aparecía en la pregunta. La validación de filtros limita la interpretación del LLM a condiciones expresadas por el usuario.

Categorías de vivienda: la palabra «alquiler» no coincidía con las etiquetas completas de la base. Añadí en escenarios.py un resolvedor que agrupa las categorías de alquiler a precio de mercado e inferior al de mercado; utilicé consultas parametrizadas.

Error HTTP 422 al probar Swagger: identifiqué una solicitud cuyo cuerpo JSON era inválido. Se solucionó al enviar un JSON válido; no implicaba un fallo del modelo ni de la consulta.

Categorías omitidas en la respuesta P3: comprobamos que, además del ahorro económico y medioambiental, existe la categoría «Indiferente». Se decidió generar las respuestas numéricas en Python incluyendo todas las opciones, en lugar de permitir que el LLM omita categorías.

## 8. Mejora final: desglose automático por sexo y edad
Incorporé una regla de consulta: si el usuario no especifica sexo, el backend devuelve resultados separados para Mujer y Hombre; si no especifica edad, devuelve seis rangos: 18–24, 25–34, 35–44, 45–54, 55–64 y 65 años o más. También conserva un resultado agregado del segmento consultado.

Cuando sí aparece un filtro de edad o sexo, el sistema respeta ese filtro y únicamente desglosa las dimensiones no especificadas. Los demás filtros, como Andalucía o uso de IA, se mantienen en cada subconsulta.

Son franjas demográficas operativas para el prototipo, no una clasificación única y universal del CIS. Los porcentajes de opciones se deben interpretar dentro de cada subgrupo y no sumarse entre tramos de edad.

He probado manualmente el nuevo comportamiento en el frontend según las pruebas realizadas durante el desarrollo; conviene añadir test automatizados para cubrir todas las combinaciones.

## 9. Pruebas funcionales realizadas
P1: aceptación hipotética de IA para ayudar a cuidar a un familiar mayor entre usuarios de IA de Andalucía en 2027. Se verificó la aplicación de comunidad autónoma y uso de IA, así como la ausencia de un filtro de edad no solicitado.

P2: postura respecto a prohibir pisos turísticos entre personas de alquiler de Andalucía en 2027. Tras corregir los filtros espurios, se obtuvo 40,34 % en la categoría «Sí, prohibir» para esa ejecución concreta.

P3: campaña de ahorro de energía para personas de 18 a 30 años en 2027. Una ejecución devolvió 44,9 % para ahorro económico y 39,2 % para huella de carbono; el resto correspondía a «Indiferente», cuya visualización había sido omitida inicialmente.

P4: motivos para cambiar de banco entre mayores de 65 años en 2027. Una ejecución arrojó 39,95 % para cero comisiones, 28,65 % para atención humana, 21,37 % para aplicación con IA y 10,03 % para ninguna opción.

Estos valores son resultados ilustrativos de ejecuciones del simulador, no porcentajes observados de la sociedad española. Pueden depender de las versiones locales de archivos y de los criterios de segmentación.

## 10. Estructura de archivos relevante
backend/main.py: aplicación, rutas y montaje de routers. backend/database.py: acceso a base inicial. backend/segmentos.py: consultas por segmento. backend/agente.py: agente de preguntas sobre datos iniciales. backend/escenarios.py: cálculos de escenarios e indicadores. backend/chat_escenarios.py: interpretación y respuesta conversacional.

data/poblacion_sintetica.duckdb: base original del equipo. data/escenarios/: catálogo, perfiles simulados, indicadores, proyecciones y metadatos. data/escenarios_sinteticos.duckdb: base derivada. scripts/generar_escenarios.py y scripts/importar_escenarios.py: reproducibilidad. frontend_pruebas/index.html: chat de prueba. frontend/: interfaz del compañero, no sustituida.

La organización real debe contrastarse con git status antes de preparar el commit. No todos los archivos generados tienen por qué subirse al repositorio.

## 11. Limitaciones y siguientes pasos
El agente tiene cobertura específica de cuatro temáticas y un conjunto delimitado de indicadores. No debe responder como si pudiera predecir cualquier opinión social o negocio. Los escenarios futuros y las probabilidades de preferencia son hipótesis no validadas.

Antes de la integración final conviene: comprobar dependencias y README; revisar el tamaño de los CSV y archivos DuckDB; evitar subir secretos y .venv; añadir tests automáticos de interpretación, sumas porcentuales y segmentos vacíos; y comprobar el contrato JSON con el frontend del compañero.

Como trabajo posterior: contrastar resultados con encuestas reales compatibles, revisar la calibración de pesos, definir intervalos demográficos oficiales por cada estudio y versionar las hipótesis utilizadas.

## 12. Publicación segura en GitHub
La subida todavía debe realizarse desde el ordenador donde está clonado el repositorio; este documento no implica que se haya hecho git push. Primero: git branch --show-current y git status. Después: revisar git diff y tamaños de data/, confirmar .gitignore y decidir qué datos derivados deben rastrearse.

Cuando esté verificado, seleccionar explícitamente los archivos, hacer git add, git commit -m "feat: backend de consultas y escenarios sinteticos", y git push -u origin feature/backend-fastapi. Por último, abrir una Pull Request hacia main y describir instalación, pruebas y límites del prototipo.

No recomiendo ejecutar git add . ni publicar archivos de gran tamaño sin inspeccionar antes el estado del repositorio y confirmar el acuerdo de datos con el equipo.

## Reproducción local
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```
Abrir `http://127.0.0.1:8000/chat` o `/docs`. Instalar previamente las dependencias y generar la base de escenarios cuando sea necesario.
