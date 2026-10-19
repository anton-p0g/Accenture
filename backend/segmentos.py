
import re
import unicodedata

import duckdb
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database import obtener_conexion, VARIABLES_PERMITIDAS


# Creo las rutas para analizar segmentos de población.
router = APIRouter(
    prefix="/estadisticas",
    tags=["Estadísticas avanzadas"]
)


# Defino la estructura de cada consulta.
class SolicitudSegmento(BaseModel):
    agrupar_por: str
    filtros: dict[str, str] = Field(default_factory=dict)
    anio: int = Field(default=2025, ge=2000, le=2100)
    edad_min: int | None = Field(default=None, ge=18, le=110)
    edad_max: int | None = Field(default=None, ge=18, le=110)


def normalizar_texto(texto: str) -> str:
    # Convierto el texto a una forma comparable.
    texto = unicodedata.normalize("NFKD", texto)

    # Elimino las marcas de acentuación.
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    # Ignoro mayúsculas y espacios repetidos.
    texto = texto.casefold()
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def resolver_categoria(conexion, campo: str, valor: str) -> str:
    # El campo ya ha sido validado contra la lista autorizada.
    # Consulto las categorías existentes en nuestra base.
    filas = conexion.execute(
        f"""
        SELECT DISTINCT CAST("{campo}" AS VARCHAR)
        FROM poblacion
        WHERE "{campo}" IS NOT NULL
        """
    ).fetchall()

    # Comparo la categoría introducida con las existentes.
    valor_normalizado = normalizar_texto(valor)

    categorias = []

    for fila in filas:
        categoria_real = fila[0].strip()
        categorias.append(categoria_real)

        if normalizar_texto(categoria_real) == valor_normalizado:
            return categoria_real

    # Si no existe, aviso en vez de devolver un falso 0 %.
    raise ValueError(
        f"No he encontrado '{valor}' en la variable '{campo}'. "
        f"Algunas categorías disponibles son: "
        f"{', '.join(sorted(categorias)[:12])}"
    )


def calcular_segmento(solicitud: SolicitudSegmento):
    # Compruebo que las variables estén autorizadas.
    if solicitud.agrupar_por not in VARIABLES_PERMITIDAS:
        raise ValueError(
            "Variable de agrupación no permitida"
        )

    if len(solicitud.filtros) > 5:
        raise ValueError(
            "Se permiten como máximo cinco filtros"
        )

    for campo, valor in solicitud.filtros.items():
        if campo not in VARIABLES_PERMITIDAS:
            raise ValueError(
                f"Filtro no permitido: {campo}"
            )

        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(
                f"Valor de filtro inválido: {campo}"
            )

        if len(valor) > 100:
            raise ValueError(
                f"El valor del filtro '{campo}' es demasiado largo"
            )

    if (
        solicitud.edad_min is not None
        and solicitud.edad_max is not None
        and solicitud.edad_min > solicitud.edad_max
    ):
        raise ValueError(
            "La edad mínima no puede superar la máxima"
        )

    conexion = obtener_conexion()

    try:
        # Compruebo qué columnas existen realmente.
        columnas = {
            fila[1]
            for fila in conexion.execute(
                "PRAGMA table_info('poblacion')"
            ).fetchall()
        }

        necesarias = {
            solicitud.agrupar_por,
            "anio",
            "edad",
            "peso_poblacional",
            *solicitud.filtros.keys()
        }

        if not necesarias.issubset(columnas):
            raise ValueError(
                "Alguna variable no existe en la base de datos"
            )

        # Preparo las condiciones de filtrado.
        condiciones = [
            "TRY_CAST(anio AS INTEGER) = ?",
            "TRY_CAST(peso_poblacional AS DOUBLE) > 0"
        ]

        parametros = [solicitud.anio]
        filtros_resueltos = {}

        # Resuelvo cada valor contra las categorías reales.
        for campo, valor in solicitud.filtros.items():
            valor_real = resolver_categoria(
                conexion,
                campo,
                valor
            )

            filtros_resueltos[campo] = valor_real

            # Utilizo parámetros para evitar inyección SQL.
            condiciones.append(
                f'TRIM(CAST("{campo}" AS VARCHAR)) = ?'
            )
            parametros.append(valor_real)

        # Añado los filtros de edad cuando existen.
        if solicitud.edad_min is not None:
            condiciones.append(
                "TRY_CAST(edad AS INTEGER) >= ?"
            )
            parametros.append(solicitud.edad_min)

        if solicitud.edad_max is not None:
            condiciones.append(
                "TRY_CAST(edad AS INTEGER) <= ?"
            )
            parametros.append(solicitud.edad_max)

        where_sql = " AND ".join(condiciones)

        # El nombre de columna está previamente validado.
        columna = f'"{solicitud.agrupar_por}"'

        # DuckDB realiza todos los cálculos ponderados.
        consulta = f"""
            WITH datos_filtrados AS (
                SELECT
                    COALESCE(
                        NULLIF(
                            TRIM(CAST({columna} AS VARCHAR)),
                            ''
                        ),
                        'Sin dato'
                    ) AS categoria,

                    TRY_CAST(
                        peso_poblacional AS DOUBLE
                    ) AS peso

                FROM poblacion
                WHERE {where_sql}
            ),
            agrupados AS (
                SELECT
                    categoria,
                    COUNT(*) AS perfiles,
                    SUM(peso) AS poblacion
                FROM datos_filtrados
                GROUP BY categoria
            )
            SELECT
                categoria,
                perfiles,
                poblacion,
                CASE
                    WHEN SUM(poblacion) OVER () > 0
                    THEN 100.0 * poblacion /
                         SUM(poblacion) OVER ()
                    ELSE NULL
                END AS porcentaje
            FROM agrupados
            ORDER BY poblacion DESC
        """

        filas = conexion.execute(
            consulta,
            parametros
        ).fetchall()

        # No confundo ausencia de datos con un porcentaje cero.
        if not filas:
            raise ValueError(
                "No existen perfiles para los filtros indicados "
                "en el año seleccionado"
            )

        distribucion = []

        for fila in filas:
            distribucion.append({
                "categoria": fila[0],
                "perfiles": fila[1],
                "poblacion_ponderada": round(fila[2], 2),
                "porcentaje": (
                    round(fila[3], 2)
                    if fila[3] is not None else None
                )
            })

        total_perfiles = sum(
            fila["perfiles"]
            for fila in distribucion
        )

        total_ponderado = sum(
            fila["poblacion_ponderada"]
            for fila in distribucion
        )

        # Preparo advertencias sobre la interpretación.
        advertencias = [
            "Los datos proceden de una población sintética.",
            "La representatividad externa aún no está validada."
        ]

        if total_perfiles < 30:
            advertencias.append(
                "El segmento contiene menos de 30 perfiles "
                "sintéticos; los resultados pueden ser inestables."
            )

        return {
            "anio": solicitud.anio,
            "agrupar_por": solicitud.agrupar_por,
            "filtros": solicitud.filtros,
            "filtros_resueltos": filtros_resueltos,
            "edad_min": solicitud.edad_min,
            "edad_max": solicitud.edad_max,
            "total_perfiles": total_perfiles,
            "poblacion_ponderada": round(
                total_ponderado, 2
            ),
            "distribucion": distribucion,
            "advertencias": advertencias
        }

    finally:
        conexion.close()


@router.post("/segmento")
def consultar_segmento(solicitud: SolicitudSegmento):
    try:
        return calcular_segmento(solicitud)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Base de datos no encontrada"
        )

    except duckdb.Error:
        raise HTTPException(
            status_code=500,
            detail="Error consultando DuckDB"
        )
