
import logging
from pathlib import Path
from typing import Literal

import duckdb

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.database import (
    RUTA_BD,
    obtener_metadata,
    obtener_resumen,
    obtener_distribucion
)

from backend.agente import responder_pregunta
from backend.segmentos import router as router_segmentos
from backend.escenarios import router as router_escenarios
from backend.chat_escenarios import router as router_chat_escenarios


# Preparo las rutas de nuestro proyecto.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

RUTA_FRONTEND_PRUEBAS = (
    RAIZ_PROYECTO / "frontend_pruebas" / "index.html"
)


logger = logging.getLogger(__name__)


# Creo nuestra aplicación FastAPI.
app = FastAPI(
    title="Synthetic Spain AI",
    description=(
        "API para consultar la población sintética española "
        "y explorar escenarios de 2020 a 2027 mediante IA."
    ),
    version="0.7.0"
)


# Conservo todos los routers que ya funcionan.
app.include_router(router_segmentos)
app.include_router(router_escenarios)
app.include_router(router_chat_escenarios)


class PreguntaUsuario(BaseModel):
    pregunta: str = Field(
        min_length=5,
        max_length=600
    )


# Página principal.
@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a Synthetic Spain AI",
        "estado": "Backend funcionando",
        "version": "0.7.0",
        "chat": "/chat"
    }


# NUEVA RUTA: frontend provisional.
@app.get("/chat", include_in_schema=False)
def mostrar_chat():

    if not RUTA_FRONTEND_PRUEBAS.is_file():
        raise HTTPException(
            status_code=404,
            detail="No existe frontend_pruebas/index.html"
        )

    return FileResponse(
        RUTA_FRONTEND_PRUEBAS,
        media_type="text/html"
    )


@app.get("/health")
def comprobar_estado():
    return {
        "status": "ok",
        "api": "Synthetic Spain AI",
        "database": (
            "Archivo encontrado"
            if RUTA_BD.is_file()
            else "Archivo no encontrado"
        ),
        "llm": "Configurado con Ollama y Qwen3",
        "escenarios": "Rutas de escenarios registradas"
    }


@app.get("/metadata")
def consultar_metadata():
    try:
        return obtener_metadata()

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No se encuentra la base de datos"
        )

    except duckdb.Error:
        logger.exception("Error consultando metadata")
        raise HTTPException(
            status_code=500,
            detail="Error al consultar DuckDB"
        )


@app.get("/estadisticas/resumen")
def consultar_resumen():
    try:
        return obtener_resumen()

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No se encuentra la base de datos"
        )

    except duckdb.Error:
        logger.exception("Error calculando resumen")
        raise HTTPException(
            status_code=500,
            detail="Error calculando el resumen"
        )


@app.get("/estadisticas/distribucion")
def consultar_distribucion(
    variable: Literal[
        "sexo",
        "grupo_edad",
        "ccaa",
        "estudios",
        "situacion_laboral",
        "vivienda"
    ],
    anio: int | None = Query(
        default=None,
        ge=2000,
        le=2100
    )
):
    try:
        return obtener_distribucion(variable, anio)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No se encuentra la base de datos"
        )

    except duckdb.Error:
        logger.exception("Error calculando distribución")
        raise HTTPException(
            status_code=500,
            detail="Error calculando la distribución"
        )


@app.post("/ask")
def consultar_ia(datos: PreguntaUsuario):
    try:
        return responder_pregunta(datos.pregunta)

    except Exception:
        logger.exception("Error procesando pregunta")

        raise HTTPException(
            status_code=503,
            detail=(
                "No se ha podido procesar la pregunta. "
                "Comprueba Ollama y Qwen3."
            )
        )
