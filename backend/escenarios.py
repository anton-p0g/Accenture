
"""
Consultas estadísticas de escenarios sintéticos 2020-2027.

Uso DuckDB en modo lectura y permito filtrar por categorías.
Las opiniones son simulaciones hipotéticas no validadas.
"""

import re
import unicodedata
from pathlib import Path
from typing import Literal

import duckdb
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/escenarios",
    tags=["Escenarios sintéticos"]
)

RAIZ = Path(__file__).resolve().parent.parent
RUTA_ESC = RAIZ / "data" / "escenarios_sinteticos.duckdb"


OPCIONES = {
    "P1": [
        ("Sí", "p1_si"),
        ("Depende", "p1_depende"),
        ("No", "p1_no")
    ],
    "P2": [
        ("Sí, prohibir", "p2_prohibir"),
        ("Limitar sin prohibir", "p2_limitar"),
        ("No prohibir", "p2_no_prohibir"),
        ("No sabe", "p2_ns")
    ],
    "P3": [
        ("Ahorro económico", "p3_ahorro"),
        ("Huella de carbono", "p3_ambiente"),
        ("Indiferente", "p3_indiferente")
    ],
    "P4": [
        ("Cero comisiones", "p4_comisiones"),
        ("Atención humana 24/7", "p4_humano"),
        ("App con IA", "p4_ia"),
        ("Ninguna", "p4_ninguna")
    ]
}


GRUPOS = {
    "sexo",
    "ccaa",
    "grupo_edad",
    "vivienda",
    "uso_ia_escenario",
    "quintil_renta",
    "urbanizacion",
    "ideologia_declarada_imputada"
}

FILTROS = GRUPOS


INDICADORES = {
    "internet_ultimos_3_meses",
    "internet_diario",
    "compras_internet_ultimos_3_meses",
    "tasa_paro_cuarto_trimestre",
    "uso_ia_generativa_ultimos_3_meses",
    "uso_banca_internet_ultimos_3_meses"
}


class SolicitudEscenario(BaseModel):
    pregunta_id: Literal["P1", "P2", "P3", "P4"]
    anio: int = Field(default=2026, ge=2020, le=2027)
    filtros: dict[str, str] = Field(default_factory=dict)
    edad_min: int | None = Field(default=None, ge=18, le=110)
    edad_max: int | None = Field(default=None, ge=18, le=110)
    agrupar_por: str | None = None


def conexion():
    # Abro exclusivamente en modo lectura.
    if not RUTA_ESC.is_file():
        raise FileNotFoundError(
            f"No existe {RUTA_ESC}. "
            "Ejecuta scripts/importar_escenarios.py"
        )

    return duckdb.connect(str(RUTA_ESC), read_only=True)


def normalizar(texto):
    # Ignoro tildes, mayúsculas y espacios adicionales.
    texto = unicodedata.normalize("NFKD", str(texto))

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    return re.sub(r"\s+", " ", texto.casefold()).strip()


def resolver_categorias(con, campo, valor):
    """
    Devuelvo una lista de categorías reales de DuckDB.

    Una expresión como 'alquiler' puede corresponder
    a varias categorías que debemos combinar.
    """

    # campo se valida antes contra FILTROS.
    filas = con.execute(
        f"""
        SELECT DISTINCT CAST("{campo}" AS VARCHAR)
        FROM opiniones_escenario
        WHERE "{campo}" IS NOT NULL
        """
    ).fetchall()

    categorias = sorted(
        str(fila[0]).strip()
        for fila in filas
        if fila[0] is not None
    )

    buscado = normalizar(valor)

    # Primero detecto un grupo semántico de vivienda.
    if campo == "vivienda":
        if buscado in {
            "alquiler",
            "alquilada",
            "alquilado",
            "de alquiler",
            "inquilino",
            "inquilina",
            "inquilinos",
            "inquilinas"
        }:
            coincidencias = [
                categoria
                for categoria in categorias
                if "alquiler" in normalizar(categoria)
                or "realquiler" in normalizar(categoria)
            ]

            if coincidencias:
                return coincidencias

        if buscado in {
            "propiedad",
            "propietario",
            "propietaria",
            "propietarios",
            "propietarias",
            "en propiedad"
        }:
            coincidencias = [
                categoria
                for categoria in categorias
                if "propiedad" in normalizar(categoria)
            ]

            if coincidencias:
                return coincidencias

    # Para el resto, busco coincidencia exacta,
    # pero ignorando tildes y mayúsculas.
    coincidencias = [
        categoria
        for categoria in categorias
        if normalizar(categoria) == buscado
    ]

    if coincidencias:
        return coincidencias

    raise ValueError(
        f"Categoría no reconocida para {campo}: {valor}. "
        f"Ejemplos: {categorias[:8]}"
    )


def consulta_escenario(p: SolicitudEscenario):

    # Valido los nombres de las columnas antes de construir SQL.
    if p.agrupar_por is not None and p.agrupar_por not in GRUPOS:
        raise ValueError(
            f"Agrupación no permitida: {p.agrupar_por}"
        )

    if len(p.filtros) > 5:
        raise ValueError("Máximo cinco filtros")

    if (
        p.edad_min is not None
        and p.edad_max is not None
        and p.edad_min > p.edad_max
    ):
        raise ValueError(
            "La edad mínima supera la máxima"
        )

    for campo, valor in p.filtros.items():
        if (
            campo not in FILTROS
            or not isinstance(valor, str)
            or not valor.strip()
            or len(valor) > 100
        ):
            raise ValueError(
                f"Filtro no permitido: {campo}={valor}"
            )

    opciones = OPCIONES[p.pregunta_id]

    with conexion() as con:

        condiciones = ['"anio" = ?']
        parametros = [p.anio]
        filtros_resueltos = {}

        # Aplico cada filtro con sus categorías reales.
        for campo, valor in p.filtros.items():

            categorias = resolver_categorias(
                con,
                campo,
                valor
            )

            filtros_resueltos[campo] = (
                categorias[0]
                if len(categorias) == 1
                else categorias
            )

            # Una categoría general puede equivaler
            # a varias categorías reales.
            marcadores = ", ".join(
                ["?"] * len(categorias)
            )

            condiciones.append(
                f'"{campo}" IN ({marcadores})'
            )

            parametros.extend(categorias)

        # Aplico los rangos de edad.
        if p.edad_min is not None:
            condiciones.append('"edad" >= ?')
            parametros.append(p.edad_min)

        if p.edad_max is not None:
            condiciones.append('"edad" <= ?')
            parametros.append(p.edad_max)

        # Si no agrupamos, calculo un total general.
        agrupacion = (
            f'CAST("{p.agrupar_por}" AS VARCHAR)'
            if p.agrupar_por
            else "'TOTAL'"
        )

        # Calculo la suma ponderada de cada opción.
        columnas = ",\n".join(
            f'SUM('
            f'CAST("peso_relativo_escenario" AS DOUBLE) * '
            f'CAST("{columna}" AS DOUBLE)'
            f') AS "{columna}"'
            for _, columna in opciones
        )

        sql = f"""
            SELECT
                {agrupacion} AS categoria,
                COUNT(*) AS registros,
                SUM(
                    CAST(
                        "peso_relativo_escenario" AS DOUBLE
                    )
                ) AS peso_grupo,
                SUM(
                    POWER(
                        CAST(
                            "peso_relativo_escenario" AS DOUBLE
                        ), 2
                    )
                ) AS pesos_cuadrado,
                {columnas}

            FROM opiniones_escenario

            WHERE {" AND ".join(condiciones)}

            GROUP BY 1
            ORDER BY peso_grupo DESC
        """

        datos = con.execute(
            sql,
            parametros
        ).fetchall()

    if not datos:
        raise ValueError(
            "No hay perfiles para esos filtros y año"
        )

    resultados = []

    for fila in datos:
        categoria, registros, peso, cuadrados, *numeradores = fila

        efectivo = (
            peso * peso / cuadrados
            if cuadrados and peso
            else 0
        )

        porcentajes = {
            etiqueta: (
                round(100 * numero / peso, 2)
                if peso and numero is not None
                else None
            )
            for (etiqueta, _), numero
            in zip(opciones, numeradores)
        }

        resultados.append({
            "categoria": categoria,
            "registros_sinteticos": registros,
            "peso_relativo_segmento": round(peso, 6),
            "tamano_efectivo_aproximado": round(
                efectivo, 1
            ),
            "porcentajes_modelados": porcentajes
        })

    advertencias = [
        "P1-P4 son opiniones hipotéticas, no encuestas reales.",
        "Los pesos normalizados no representan habitantes reales.",
        "2020-2024 son perfiles sintéticos retrospectivos.",
        "2026-2027 son escenarios futuros experimentales.",
        "Un tamaño efectivo alto no valida opiniones simuladas."
    ]

    if min(
        grupo["registros_sinteticos"]
        for grupo in resultados
    ) < 30:
        advertencias.append(
            "Algunos segmentos tienen menos de 30 perfiles."
        )

    return {
        "pregunta_id": p.pregunta_id,
        "anio": p.anio,
        "agrupar_por": p.agrupar_por,
        "edad_min": p.edad_min,
        "edad_max": p.edad_max,
        "filtros_solicitados": p.filtros,
        "filtros_aplicados": filtros_resueltos,
        "resultados": resultados,
        "fiabilidad": "EXPERIMENTAL_NO_VALIDADA",
        "procedencia": "SIMULACION_HIPOTETICA",
        "advertencias": advertencias
    }


def consultar_indicador(indicador, anio):
    # Mantengo la consulta a indicadores observados
    # y a proyecciones heurísticas.
    if indicador not in INDICADORES or not 2020 <= anio <= 2027:
        raise ValueError(
            "Indicador o año no autorizado"
        )

    with conexion() as con:

        if anio <= 2025:
            fila = con.execute(
                """
                SELECT anio, indicador, valor, unidad,
                       universo, periodo, tipo_dato,
                       fuente, url, nota
                FROM indicadores_observados
                WHERE indicador = ? AND anio = ?
                """,
                [indicador, anio]
            ).fetchone()

            if not fila:
                raise ValueError(
                    "No hay observación para ese indicador y año"
                )

            campos = [
                "anio", "indicador", "valor", "unidad",
                "universo", "periodo", "tipo_dato",
                "fuente", "url", "nota"
            ]

        else:
            fila = con.execute(
                """
                SELECT anio, indicador, valor_central,
                       escenario_bajo, escenario_alto,
                       unidad, tipo_dato, metodo,
                       "fuente_histórica", nota
                FROM indicadores_proyectados
                WHERE indicador = ? AND anio = ?
                """,
                [indicador, anio]
            ).fetchone()

            if not fila:
                raise ValueError(
                    "No hay proyección para ese indicador y año"
                )

            campos = [
                "anio", "indicador", "valor_central",
                "escenario_bajo", "escenario_alto",
                "unidad", "tipo_dato", "metodo",
                "fuente_historica", "nota"
            ]

        return dict(zip(campos, fila))


@router.get("/catalogo")
def catalogo():
    return {
        "preguntas": OPCIONES,
        "variables_agrupacion": sorted(GRUPOS),
        "fiabilidad": "opiniones experimentales"
    }


@router.post("/consultar")
def endpoint_consultar(solicitud: SolicitudEscenario):
    try:
        return consulta_escenario(solicitud)

    except FileNotFoundError as error:
        raise HTTPException(404, str(error))

    except ValueError as error:
        raise HTTPException(400, str(error))

    except duckdb.Error:
        raise HTTPException(
            500,
            "Error consultando DuckDB"
        )


@router.get("/indicadores/{anio}/{indicador}")
def endpoint_indicador(anio: int, indicador: str):
    try:
        return consultar_indicador(indicador, anio)

    except FileNotFoundError as error:
        raise HTTPException(404, str(error))

    except ValueError as error:
        raise HTTPException(400, str(error))

    except duckdb.Error:
        raise HTTPException(
            500,
            "Error consultando DuckDB"
        )
