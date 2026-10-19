
"""
Chat de escenarios de España entre 2020 y 2027.

Qwen3 interpreta la pregunta.
DuckDB calcula los resultados de la población sintética.

Cuando no se indica edad o sexo, genero desgloses
automáticos por las dimensiones no especificadas.

Las opiniones son escenarios hipotéticos no validados.
"""

import json
import logging
import re
import unicodedata
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from ollama import chat
from pydantic import BaseModel, Field, StringConstraints, ValidationError

from backend.config import OLLAMA_MODEL
from backend.escenarios import (
    SolicitudEscenario,
    consulta_escenario,
    consultar_indicador,
    INDICADORES,
    GRUPOS
)


router = APIRouter(
    prefix="/escenarios",
    tags=["Chat de escenarios"]
)

logger = logging.getLogger(__name__)

MODELO = OLLAMA_MODEL


# Defino los rangos de edad que quiero utilizar.
# Son franjas sociológicas habituales y configurables.
TRAMOS_EDAD = [
    ("18-24 años", 18, 24),
    ("25-34 años", 25, 34),
    ("35-44 años", 35, 44),
    ("45-54 años", 45, 54),
    ("55-64 años", 55, 64),
    ("65 años o más", 65, 110)
]


# --------------------------------------------------
# MODELOS
# --------------------------------------------------

class PreguntaChat(BaseModel):
    pregunta: str = Field(min_length=8, max_length=900)


class ClasificacionPregunta(BaseModel):
    tipo: Literal["escenario", "indicador", "no_disponible"] = "no_disponible"
    pregunta_id: Literal["P1", "P2", "P3", "P4"] | None = None
    filtros: dict[
        str, Annotated[str, StringConstraints(max_length=100)]
    ] = Field(default_factory=dict)
    indicador: Literal[
        "internet_ultimos_3_meses",
        "internet_diario",
        "compras_internet_ultimos_3_meses",
        "tasa_paro_cuarto_trimestre",
        "uso_ia_generativa_ultimos_3_meses",
        "uso_banca_internet_ultimos_3_meses"
    ] | None = None


class InterpretacionPregunta(ClasificacionPregunta):
    anio: int = 2026
    edad_min: int | None = None
    edad_max: int | None = None
    agrupar_por: str | None = None


# --------------------------------------------------
# INSTRUCCIONES DE QWEN3
# --------------------------------------------------

INSTRUCCIONES = """
Interpreta preguntas sobre la sociedad sintética española.

Devuelve únicamente JSON conforme al esquema proporcionado.
No inventes porcentajes ni respondas todavía.

Escenarios disponibles:
P1: IA para ayudar a cuidar a familiares mayores.
P2: Prohibición o limitación de pisos turísticos.
P3: Campañas de ahorro energético y medioambiente.
P4: Motivos para cambiar de banco.

Indicadores disponibles: uso de internet, compras por internet,
tasa de paro del cuarto trimestre, uso de IA generativa y banca por internet.

Años: 2020-2027. Por defecto, 2026.

Filtros permitidos:
sexo, ccaa, grupo_edad, vivienda,
uso_ia_escenario, quintil_renta,
urbanizacion, ideologia_declarada_imputada.

No añadas filtros ni edades que el usuario no haya pedido.

Si una pregunta menciona cuidar a personas mayores,
eso NO significa que quienes responden sean mayores.

Una pregunta sobre inteligencia artificial NO implica
que las personas consultadas utilicen IA.

Si no hay información suficiente, usa tipo=no_disponible.
"""


# --------------------------------------------------
# NORMALIZACIÓN Y DETECCIÓN
# --------------------------------------------------

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))

    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    return re.sub(r"\s+", " ", texto.casefold()).strip()


def detectar_edad(pregunta):
    texto = normalizar(pregunta)

    # Entre 18 y 30 años.
    patron = re.search(
        r"entre\s+(?:los?\s+)?(\d{1,3})"
        r"\s+y\s+(?:los?\s+)?(\d{1,3})",
        texto
    )

    if patron:
        return int(patron.group(1)), int(patron.group(2))

    # De 18 a 30 años.
    patron = re.search(
        r"\bde\s+(\d{1,3})\s+a\s+(\d{1,3})\s+anos?",
        texto
    )

    if patron:
        return int(patron.group(1)), int(patron.group(2))

    # Mayores de 60 años.
    patron = re.search(
        r"mayores?\s+de\s+(?:los?\s+)?(\d{1,3})",
        texto
    )

    if patron:
        return int(patron.group(1)) + 1, None

    # Personas de 60 años o más.
    patron = re.search(
        r"(\d{1,3})\s+anos?\s+o\s+mas",
        texto
    )

    if patron:
        return int(patron.group(1)), None

    # Menores de 30 años.
    patron = re.search(
        r"menores?\s+de\s+(?:los?\s+)?(\d{1,3})",
        texto
    )

    if patron:
        return None, int(patron.group(1)) - 1

    return None, None


def detectar_filtros_explicitos(pregunta):
    texto = normalizar(pregunta)
    filtros = {}

    # Sexo.
    if re.search(r"\bmujeres?\b", texto):
        filtros["sexo"] = "Mujer"

    elif re.search(r"\bhombres?\b", texto):
        filtros["sexo"] = "Hombre"

    # Comunidades que ya hemos utilizado en pruebas.
    if re.search(
        r"\bandalucia\b|\bandaluz(?:a|as|es)?\b",
        texto
    ):
        filtros["ccaa"] = "Andalucia"

    # Vivienda.
    if re.search(
        r"\balquiler\b|\binquilin\w*\b",
        texto
    ):
        filtros["vivienda"] = "alquiler"

    elif re.search(
        r"\bpropietari\w*\b|\ben propiedad\b",
        texto
    ):
        filtros["vivienda"] = "propiedad"

    # Uso de IA.
    patron_no = (
        r"\bno\s+(?:usan|utilizan|emplean)\s+"
        r"(?:la\s+)?(?:ia|inteligencia artificial)\b"
    )

    patron_si = (
        r"\b(?:usan|utilizan|emplean)\s+"
        r"(?:la\s+)?(?:ia|inteligencia artificial)\b"
    )

    if re.search(patron_no, texto):
        filtros["uso_ia_escenario"] = "No"

    elif re.search(patron_si, texto):
        filtros["uso_ia_escenario"] = "Si"

    return filtros


def detectar_tema(pregunta):
    texto = normalizar(pregunta)

    if (
        re.search(r"\bia\b|inteligencia artificial", texto)
        and re.search(r"cuid\w*|familiar mayor", texto)
    ):
        return "P1"

    if (
        re.search(r"\bpisos?\b", texto)
        and re.search(r"turistic\w*|vacacional\w*", texto)
    ):
        return "P2"

    if (
        re.search(r"energia|carbono", texto)
        and re.search(r"ahorr\w*|campan\w*|convenc\w*", texto)
    ):
        return "P3"

    if (
        re.search(r"banco\w*|bancari\w*", texto)
        and re.search(
            r"cambi\w*|comision\w*|atencion", texto
        )
    ):
        return "P4"

    return None


def detectar_indicador(pregunta):
    texto = normalizar(pregunta)

    if re.search(r"\bparo\b|desempleo", texto) and re.search(
        r"cuarto trimestre|ultimo trimestre|\b4t\b", texto
    ):
        return "tasa_paro_cuarto_trimestre"

    if re.search(r"compras? (?:por |en )?internet", texto):
        return "compras_internet_ultimos_3_meses"

    if re.search(r"\bia generativa\b|inteligencia artificial generativa", texto):
        return "uso_ia_generativa_ultimos_3_meses"

    if re.search(r"banca (?:por )?internet|banca online", texto):
        return "uso_banca_internet_ultimos_3_meses"

    if "internet" in texto:
        if re.search(r"diario|cada dia|a diario", texto):
            return "internet_diario"
        if re.search(r"ultimos? (?:los )?3 meses|ultimos? tres meses", texto):
            return "internet_ultimos_3_meses"

    return None


# --------------------------------------------------
# INTERPRETACIÓN DE LA PREGUNTA
# --------------------------------------------------

def interpretar(pregunta):

    respuesta = chat(
        model=MODELO,
        messages=[
            {"role": "system", "content": INSTRUCCIONES},
            {"role": "user", "content": pregunta}
        ],
        format=ClasificacionPregunta.model_json_schema(),
        think=False,
        options={
            "temperature": 0,
            "num_ctx": 8192,
            "num_predict": 512
        }
    )

    datos = InterpretacionPregunta.model_validate_json(
        respuesta.message.content
    )

    # Solo aplico un año mencionado en la pregunta.
    anios = re.findall(r"\b20\d{2}\b", pregunta)
    datos.anio = int(anios[0]) if anios else 2026

    # No acepto edades inventadas por Qwen3.
    datos.edad_min, datos.edad_max = detectar_edad(pregunta)

    # Conservo filtros del modelo solamente cuando
    # encuentro referencias a esa variable en el texto.
    texto = normalizar(pregunta)

    referencias = {
        "sexo": r"\bmujer\w*\b|\bhombre\w*\b",
        "ccaa": (
            r"andaluc\w*|madrid|catalun\w*|galicia"
            r"|valencia|aragon|asturias|canarias"
            r"|baleares|murcia|navarra|cantabria"
            r"|extremadura|castilla|euskadi"
            r"|pais vasco|rioja|ceuta|melilla"
        ),
        "vivienda": (
            r"alquiler|inquilin\w*|propietari\w*"
            r"|en propiedad"
        ),
        "quintil_renta": r"renta|ingresos|quintil",
        "urbanizacion": r"rural|urbano|urbanizacion",
        "ideologia_declarada_imputada": (
            r"ideologia|ideologic\w*"
        )
    }

    filtros = {}

    for campo, valor in datos.filtros.items():
        if campo in referencias and re.search(
            referencias[campo], texto
        ):
            filtros[campo] = valor

    # Completo y corrijo con condiciones explícitas.
    filtros.update(
        detectar_filtros_explicitos(pregunta)
    )

    datos.filtros = filtros

    # Las agrupaciones las gestionará Python.
    datos.agrupar_por = None

    tema = detectar_tema(pregunta)

    if tema:
        datos.tipo = "escenario"
        datos.pregunta_id = tema
        datos.indicador = None
    else:
        indicador = detectar_indicador(pregunta)
        if indicador:
            datos.tipo = "indicador"
            datos.pregunta_id = None
            datos.indicador = indicador

    return datos


# --------------------------------------------------
# CÁLCULOS POR SEGMENTOS
# --------------------------------------------------

def consultar_segmento(
    pregunta_id,
    anio,
    filtros,
    edad_min=None,
    edad_max=None
):
    solicitud = SolicitudEscenario(
        pregunta_id=pregunta_id,
        anio=anio,
        filtros=filtros,
        edad_min=edad_min,
        edad_max=edad_max,
        agrupar_por=None
    )

    return consulta_escenario(solicitud)


def resultado_simplificado(evidencia):
    # Extraigo las opciones del resultado TOTAL.
    resultado = evidencia["resultados"][0]

    return {
        "registros_sinteticos": resultado[
            "registros_sinteticos"
        ],
        "tamano_efectivo_aproximado": resultado[
            "tamano_efectivo_aproximado"
        ],
        "porcentajes": resultado["porcentajes_modelados"]
    }


def generar_desgloses(datos):

    # Primero calculo la población solicitada.
    total = consultar_segmento(
        datos.pregunta_id,
        datos.anio,
        datos.filtros,
        datos.edad_min,
        datos.edad_max
    )

    desgloses = {
        "total": resultado_simplificado(total),
        "por_sexo": {},
        "por_edad": {}
    }

    evidencias = [total]

    # Si el usuario NO indica sexo, consulto ambos.
    if "sexo" not in datos.filtros:

        for sexo in ["Mujer", "Hombre"]:

            filtros = dict(datos.filtros)
            filtros["sexo"] = sexo

            try:
                resultado = consultar_segmento(
                    datos.pregunta_id,
                    datos.anio,
                    filtros,
                    datos.edad_min,
                    datos.edad_max
                )

                desgloses["por_sexo"][sexo] = (
                    resultado_simplificado(resultado)
                )

                evidencias.append(resultado)

            except ValueError:
                desgloses["por_sexo"][sexo] = {
                    "error": "Sin perfiles para este grupo"
                }

    # Si el usuario NO indica edades, calculo
    # todos los tramos que hemos definido.
    if datos.edad_min is None and datos.edad_max is None:

        for etiqueta, minimo, maximo in TRAMOS_EDAD:

            try:
                resultado = consultar_segmento(
                    datos.pregunta_id,
                    datos.anio,
                    datos.filtros,
                    minimo,
                    maximo
                )

                desgloses["por_edad"][etiqueta] = (
                    resultado_simplificado(resultado)
                )

                evidencias.append(resultado)

            except ValueError:
                desgloses["por_edad"][etiqueta] = {
                    "error": "Sin perfiles para este tramo"
                }

    return desgloses, evidencias


# --------------------------------------------------
# FORMATO DE RESPUESTA
# --------------------------------------------------

def formatear_porcentajes(porcentajes):
    return ", ".join(
        f"{opcion}: {valor:.2f}%"
        for opcion, valor in porcentajes.items()
        if valor is not None
    )


def construir_respuesta(datos, desgloses):

    lineas = []

    lineas.append(
        f"Resultados del escenario sintético de {datos.anio}."
    )

    lineas.append(
        "\nRESULTADO GENERAL DEL SEGMENTO CONSULTADO:"
    )

    lineas.append(
        formatear_porcentajes(
            desgloses["total"]["porcentajes"]
        )
    )

    # Incluyo ambos sexos si no se especificó uno.
    if desgloses["por_sexo"]:

        lineas.append("\nRESULTADOS POR SEXO:")

        for sexo, resultado in desgloses[
            "por_sexo"
        ].items():

            if "porcentajes" in resultado:
                lineas.append(
                    f"{sexo}: "
                    + formatear_porcentajes(
                        resultado["porcentajes"]
                    )
                )

    # Incluyo los grupos de edad si no se especificaron.
    if desgloses["por_edad"]:

        lineas.append("\nRESULTADOS POR EDAD:")

        for tramo, resultado in desgloses[
            "por_edad"
        ].items():

            if "porcentajes" in resultado:
                lineas.append(
                    f"{tramo}: "
                    + formatear_porcentajes(
                        resultado["porcentajes"]
                    )
                )

    lineas.append(
        "\nIMPORTANTE: Estos porcentajes proceden "
        "de opiniones sintéticas generadas mediante "
        "hipótesis. No son encuestas reales ni "
        "predicciones empíricamente validadas."
    )

    return "\n".join(lineas)


# --------------------------------------------------
# ENDPOINT PRINCIPAL
# --------------------------------------------------

@router.post("/chat")
def preguntar(solicitud: PreguntaChat):

    interpretacion = None

    try:

        # Qwen3 identifica el escenario y los filtros.
        interpretacion = interpretar(
            solicitud.pregunta
        )

        if not 2020 <= interpretacion.anio <= 2027:
            raise ValueError(
                "El año solicitado está fuera del periodo."
            )

        if (
            interpretacion.edad_min is not None
            and interpretacion.edad_max is not None
            and interpretacion.edad_min
                > interpretacion.edad_max
        ):
            raise ValueError(
                "El rango de edades no es válido."
            )

        # Mantengo las consultas de indicadores.
        if interpretacion.tipo == "indicador":

            if interpretacion.indicador not in INDICADORES:
                raise ValueError(
                    "El indicador no está disponible."
                )

            evidencia = consultar_indicador(
                interpretacion.indicador,
                interpretacion.anio
            )

            return {
                "pregunta": solicitud.pregunta,
                "respuesta": (
                    "He recuperado el indicador solicitado. "
                    "Consulta su valor y fuente en evidencias."
                ),
                "consulta_interpretada": (
                    interpretacion.model_dump()
                ),
                "evidencias": [evidencia],
                "fiabilidad": evidencia.get(
                    "tipo_dato", "NO_EVALUABLE"
                )
            }

        # Compruebo que el escenario exista.
        if (
            interpretacion.tipo != "escenario"
            or interpretacion.pregunta_id
                not in {"P1", "P2", "P3", "P4"}
        ):
            return {
                "pregunta": solicitud.pregunta,
                "respuesta": (
                    "No hay información suficiente "
                    "para responder esta pregunta."
                ),
                "evidencias": [],
                "fiabilidad": "NO_EVALUABLE"
            }

        # Ejecuto las estadísticas por segmentos.
        desgloses, evidencias = generar_desgloses(
            interpretacion
        )

        # Construyo la respuesta con todas las opciones.
        # Python conserva las cifras sin omitir categorías.
        respuesta = construir_respuesta(
            interpretacion,
            desgloses
        )

        return {
            "pregunta": solicitud.pregunta,
            "respuesta": respuesta,
            "consulta_interpretada": (
                interpretacion.model_dump()
            ),
            "desgloses": desgloses,
            "evidencias": evidencias,
            "fiabilidad": "EXPERIMENTAL_NO_VALIDADA",
            "procedencia": "SIMULACION_HIPOTETICA"
        }

    except (ValueError, ValidationError) as error:

        return {
            "pregunta": solicitud.pregunta,
            "respuesta": (
                f"No he podido realizar la consulta: {error}"
            ),
            "consulta_interpretada": (
                interpretacion.model_dump()
                if interpretacion is not None else None
            ),
            "evidencias": [],
            "fiabilidad": "NO_EVALUABLE"
        }

    except Exception:

        logger.exception(
            "Error procesando el chat de escenarios"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "No se ha podido ejecutar la consulta. "
                "Comprueba Ollama y DuckDB."
            )
        )
