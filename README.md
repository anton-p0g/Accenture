# Accenture

## Synthetic population database

`data/poblacion_sintetica.csv` is the seed dataset for the synthetic Spanish society model.

- 25,000 synthetic records for 2025.
- 59 columns covering demographics, household circumstances, health, internet and AI use, ideology, and religion.
- Record IDs are unique within this file.

This file contains synthetic records, not official survey microdata or observed individual respondents. Model outputs require calibration and validation against suitable real-world statistics before they are used as predictions.

The separate `data/escenarios_sinteticos.duckdb` contains simulated scenarios for 2020–2027. Opinions P1–P4 are hypothetical and are not observed survey responses.

## Arranque local del backend con uv

Desde la raíz del repositorio:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp -n .env.example .env
```

En `.env`, cambia `OLLAMA_MODEL` por el nombre exacto de un modelo instalado en Ollama (por ejemplo, `gemma4:26b`) y `BACKEND_PORT` si el puerto 8000 está ocupado. Comprueba el modelo con `ollama list`. El archivo `.env` es local y está ignorado por Git; `.env.example` documenta los valores iniciales.

Con Ollama en marcha, inicia la API:

```bash
.venv/bin/python -m backend.run
```

Con `BACKEND_PORT=8001`, la documentación interactiva está en `http://127.0.0.1:8001/docs` y el chat de pruebas en `http://127.0.0.1:8001/chat`.

## Iniciar la web app

La primera vez, prepara `.venv` y `.env` con los pasos anteriores e instala Node.js y npm. Asegúrate de que Ollama está en marcha y de que el modelo indicado en `.env` aparece en `ollama list`.

Abre dos terminales desde la raíz del repositorio:

```bash
# Terminal 1: API
.venv/bin/python -m backend.run
```

```bash
# Terminal 2: web
cd web
npm install
npm run dev
```

Abre en el navegador la URL que muestra Vite, normalmente `http://127.0.0.1:5173`. La web usa automáticamente el `BACKEND_PORT` definido en el `.env` de la raíz. Para empezar la demo sin preguntas anteriores, recarga la página.

## pulso: motor con datos reales del CIS y nuevo frontend

En `pulso/` está el motor que conecta la población sintética con respuestas reales del CIS (banco de ~300 preguntas,
validación del LLM) y un frontend nuevo. Instrucciones en [pulso/README.md](pulso/README.md).
