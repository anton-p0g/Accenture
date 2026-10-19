
import json
import re

from ollama import chat
from pydantic import ValidationError

from backend.database import obtener_distribucion
from backend.segmentos import SolicitudSegmento, calcular_segmento


# Indico el modelo local que utilizo mediante Ollama.
MODELO = "qwen3:4b"


# Defino las variables que el agente puede analizar.
VARIABLES = [
    "sexo",
    "grupo_edad",
    "ccaa",
    "estudios",
    "situacion_laboral",
    "vivienda"
]


# Defino las herramientas disponibles para el LLM.
HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_distribucion",
            "description": (
                "Calcula la distribución ponderada de una "
                "variable para toda la población sintética. "
                "Úsala cuando NO necesites filtrar por sexo, "
                "comunidad autónoma ni otros atributos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "variable": {
                        "type": "string",
                        "enum": VARIABLES,
                        "description": (
                            "Variable cuya distribución quiero conocer"
                        )
                    },
                    "anio": {
                        "type": "integer",
                        "enum": [2025],
                        "description": "Año disponible: 2025"
                    }
                },
                "required": ["variable"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_segmento",
            "description": (
                "Calcula una distribución ponderada para un "
                "segmento concreto de población. "
                "Permite combinar filtros como sexo y comunidad "
                "autónoma, y también filtrar por edades. "
                "Los porcentajes se calculan dentro del segmento."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "agrupar_por": {
                        "type": "string",
                        "enum": VARIABLES,
                        "description": (
                            "Variable que quiero estudiar dentro "
                            "del segmento seleccionado"
                        )
                    },
                    "filtros": {
                        "type": "object",
                        "description": (
                            "Filtros exactos por variables. "
                            "Ejemplo: "
                            "{'sexo': 'Mujer', 'ccaa': 'Andalucía'}"
                        ),
                        "additionalProperties": {
                            "type": "string"
                        }
                    },
                    "anio": {
                        "type": "integer",
                        "enum": [2025]
                    },
                    "edad_min": {
                        "type": "integer",
                        "description": "Edad mínima incluida"
                    },
                    "edad_max": {
                        "type": "integer",
                        "description": "Edad máxima incluida"
                    }
                },
                "required": ["agrupar_por"]
            }
        }
    }
]


# Especifico cómo quiero que razone operativamente el agente.
INSTRUCCIONES = """
Eres un analista especializado en la población sintética
española de 2025.

Tu función es responder preguntas utilizando resultados
estadísticos obtenidos de herramientas.

REGLAS:

1. Responde siempre en español de España.

2. Nunca inventes porcentajes, cantidades ni estadísticas.

3. Si el usuario solicita datos disponibles, utiliza
   una herramienta antes de responder.

4. Utiliza consultar_distribucion cuando la pregunta
   sea sobre toda la población.

5. Utiliza consultar_segmento cuando necesites
   filtrar por sexo, comunidad autónoma, estudios,
   situación laboral, vivienda o edad.

6. Puedes indicar categorías con o sin tildes.
   El backend resolverá las denominaciones reales.

7. Para rangos de edad exactos, utiliza edad_min
   y edad_max en consultar_segmento.

8. Si necesitas comparar dos grupos distintos,
   puedes solicitar varias consultas.

9. No confundas porcentajes de toda España con
   porcentajes dentro de un segmento filtrado.

10. Todas las cifras proceden de una población
    sintética, no de observaciones individuales reales.

11. No afirmes que la población es estadísticamente
    representativa de España: la calibración externa
    todavía no está verificada.

12. No inventes predicciones electorales, precios
    futuros ni relaciones causales.

13. Si falta información, reconoce la limitación
    y explica qué datos serían necesarios.

14. Redacta respuestas claras y fundamentadas.
    Menciona los porcentajes y categorías relevantes.

15. No expongas razonamientos internos. Devuelve
    únicamente la respuesta final destinada al usuario.
"""


def limpiar_respuesta(texto: str) -> str:
    # Elimino posibles etiquetas internas del modelo.
    texto = re.sub(
        r"<think>.*?</think>",
        "",
        texto,
        flags=re.DOTALL
    )

    if "</think>" in texto:
        texto = texto.split("</think>")[-1]

    return texto.strip()


def ejecutar_herramienta(nombre: str, argumentos: dict):
    # Solo ejecuto herramientas previamente autorizadas.

    if nombre == "consultar_distribucion":
        variable = argumentos.get("variable", "")
        anio = argumentos.get("anio", 2025)

        if isinstance(anio, bool) or anio != 2025:
            raise ValueError("Solo existen datos del año 2025")

        return obtener_distribucion(
            variable=variable,
            anio=anio
        )

    if nombre == "consultar_segmento":
        # Valido todos los parámetros antes de utilizarlos.
        solicitud = SolicitudSegmento(**argumentos)

        if solicitud.anio != 2025:
            raise ValueError("Solo existen datos del año 2025")

        return calcular_segmento(solicitud)

    raise ValueError(
        f"Herramienta no autorizada: {nombre}"
    )


def calcular_fiabilidad(evidencias: list) -> dict:
    # Esta primera escala mide el respaldo de la consulta.
    # NO representa una probabilidad real de acierto.

    if not evidencias:
        return {
            "nivel": "no_evaluable",
            "motivo": "No existen consultas válidas que respalden la respuesta."
        }

    # Compruebo si algún segmento contiene pocos perfiles.
    perfiles_segmentos = [
        evidencia["total_perfiles"]
        for evidencia in evidencias
        if "total_perfiles" in evidencia
    ]

    if perfiles_segmentos and min(perfiles_segmentos) < 30:
        return {
            "nivel": "exploratoria",
            "motivo": (
                "Algún segmento contiene menos de 30 perfiles "
                "sintéticos. Los resultados pueden ser inestables "
                "y la representatividad externa no está validada."
            )
        }

    return {
        "nivel": "no_calibrada",
        "motivo": (
            "Los porcentajes han sido calculados directamente "
            "sobre la base sintética, pero todavía no se ha "
            "validado su representatividad frente a datos "
            "oficiales de la población adulta española."
        )
    }


def responder_pregunta(pregunta: str) -> dict:
    # Inicio la conversación con instrucciones y pregunta.
    mensajes = [
        {
            "role": "system",
            "content": INSTRUCCIONES
        },
        {
            "role": "user",
            "content": pregunta
        }
    ]

    evidencias = []
    registro_herramientas = []

    # Permito hasta tres rondas de herramientas.
    # Esto permite comparar varios segmentos sin
    # dejar al agente ejecutando consultas indefinidamente.
    for ronda in range(3):

        respuesta = chat(
            model=MODELO,
            messages=mensajes,
            tools=HERRAMIENTAS,
            think=False,
            options={
                "temperature": 0,
                "num_ctx": 8192
            }
        )

        mensajes.append(respuesta.message)

        llamadas = respuesta.message.tool_calls or []

        # Si Qwen3 ya no solicita herramientas,
        # puedo devolver su respuesta final.
        if not llamadas:

            if not evidencias:
                return {
                    "pregunta": pregunta,
                    "respuesta": (
                        "No he podido obtener datos estadísticos "
                        "que permitan fundamentar la respuesta. "
                        "Puede que la pregunta requiera información "
                        "que aún no existe en la base."
                    ),
                    "evidencias": [],
                    "registro_herramientas": registro_herramientas,
                    "fiabilidad": calcular_fiabilidad([])
                }

            texto = limpiar_respuesta(
                respuesta.message.content or ""
            )

            return {
                "pregunta": pregunta,
                "respuesta": texto,
                "evidencias": evidencias,
                "registro_herramientas": registro_herramientas,
                "fiabilidad": calcular_fiabilidad(evidencias)
            }

        # Proceso cada llamada solicitada por Qwen3.
        for llamada in llamadas:

            nombre = llamada.function.name
            argumentos = llamada.function.arguments or {}

            try:
                if isinstance(argumentos, str):
                    argumentos = json.loads(argumentos)

                if not isinstance(argumentos, dict):
                    raise ValueError(
                        "Los argumentos deben ser un objeto JSON"
                    )

                # Ejecuto la función Python correspondiente.
                resultado = ejecutar_herramienta(
                    nombre,
                    argumentos
                )

                evidencias.append(resultado)

                registro_herramientas.append({
                    "herramienta": nombre,
                    "argumentos": argumentos,
                    "estado": "correcto"
                })

            except (
                ValueError,
                TypeError,
                ValidationError,
                json.JSONDecodeError
            ) as error:

                resultado = {
                    "error": str(error)
                }

                registro_herramientas.append({
                    "herramienta": nombre,
                    "argumentos": argumentos,
                    "estado": "error",
                    "detalle": str(error)
                })

            # Devuelvo el resultado de Python al modelo.
            mensajes.append({
                "role": "tool",
                "tool_name": nombre,
                "content": json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            })

    # Si el agente ha agotado las rondas,
    # no permito nuevas llamadas a herramientas.
    if not evidencias:
        return {
            "pregunta": pregunta,
            "respuesta": (
                "No he conseguido completar una consulta "
                "estadística válida para esta pregunta."
            ),
            "evidencias": [],
            "registro_herramientas": registro_herramientas,
            "fiabilidad": calcular_fiabilidad([])
        }

    mensajes.append({
        "role": "system",
        "content": (
            "Las consultas han terminado. Redacta ahora "
            "la respuesta final utilizando únicamente "
            "las evidencias recibidas. No inventes cifras."
        )
    })

    respuesta_final = chat(
        model=MODELO,
        messages=mensajes,
        think=False,
        options={
            "temperature": 0,
            "num_ctx": 8192
        }
    )

    return {
        "pregunta": pregunta,
        "respuesta": limpiar_respuesta(
            respuesta_final.message.content or ""
        ),
        "evidencias": evidencias,
        "registro_herramientas": registro_herramientas,
        "fiabilidad": calcular_fiabilidad(evidencias)
    }
