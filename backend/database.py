
from pathlib import Path
import duckdb


# Localizo la raíz del proyecto y el archivo DuckDB.
RUTA_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_BD = RUTA_PROYECTO / "data" / "poblacion_sintetica.duckdb"


# Defino qué variables permito consultar desde la API.
# Así evito introducir directamente nombres arbitrarios en SQL.
VARIABLES_PERMITIDAS = {
    "sexo",
    "grupo_edad",
    "ccaa",
    "estudios",
    "situacion_laboral",
    "vivienda"
}


def obtener_conexion():
    # Compruebo que existe la base de datos.
    if not RUTA_BD.is_file():
        raise FileNotFoundError(
            f"No se encuentra la base de datos: {RUTA_BD}"
        )

    # Abro la base en modo de solo lectura.
    return duckdb.connect(str(RUTA_BD), read_only=True)


def obtener_metadata():
    conexion = obtener_conexion()

    try:
        # Consulto los nombres y tipos de las columnas.
        resultado_columnas = conexion.execute(
            "PRAGMA table_info('poblacion')"
        ).fetchall()

        columnas = [
            {"nombre": fila[1], "tipo": fila[2]}
            for fila in resultado_columnas
        ]

        # Obtengo el tamaño y la población representada.
        resultado = conexion.execute("""
            SELECT
                COUNT(*),
                SUM(TRY_CAST(peso_poblacional AS DOUBLE))
            FROM poblacion
        """).fetchone()

        return {
            "tabla": "poblacion",
            "total_perfiles": resultado[0],
            "poblacion_ponderada": (
                round(resultado[1], 2)
                if resultado[1] is not None else None
            ),
            "total_columnas": len(columnas),
            "columnas": columnas
        }

    finally:
        conexion.close()


def obtener_resumen():
    # Analizo cuántos registros tenemos por año,
    # qué edades aparecen y si hay pesos inválidos.
    conexion = obtener_conexion()

    try:
        filas = conexion.execute("""
            SELECT
                TRY_CAST(anio AS INTEGER) AS anio,
                COUNT(*) AS perfiles,

                SUM(
                    CASE
                        WHEN TRY_CAST(
                            peso_poblacional AS DOUBLE
                        ) > 0
                        THEN TRY_CAST(
                            peso_poblacional AS DOUBLE
                        )
                        ELSE 0
                    END
                ) AS poblacion_ponderada,

                MIN(TRY_CAST(edad AS INTEGER)) AS edad_minima,
                MAX(TRY_CAST(edad AS INTEGER)) AS edad_maxima,

                SUM(
                    CASE
                        WHEN TRY_CAST(edad AS INTEGER) IS NULL
                             OR TRY_CAST(edad AS INTEGER) < 18
                        THEN 1
                        ELSE 0
                    END
                ) AS edades_invalidas,

                SUM(
                    CASE
                        WHEN TRY_CAST(
                            peso_poblacional AS DOUBLE
                        ) IS NULL
                             OR TRY_CAST(
                                 peso_poblacional AS DOUBLE
                             ) <= 0
                        THEN 1
                        ELSE 0
                    END
                ) AS pesos_invalidos

            FROM poblacion
            GROUP BY 1
            ORDER BY 1
        """).fetchall()

        resultados = []

        for fila in filas:
            resultados.append({
                "anio": fila[0],
                "perfiles": fila[1],
                "poblacion_ponderada": round(fila[2], 2),
                "edad_minima": fila[3],
                "edad_maxima": fila[4],
                "edades_invalidas": fila[5],
                "pesos_invalidos": fila[6]
            })

        return {
            "total_anios": len(resultados),
            "resumen_por_anio": resultados
        }

    finally:
        conexion.close()


def obtener_distribucion(variable: str, anio: int | None = None):
    # Compruebo que la variable está autorizada.
    if variable not in VARIABLES_PERMITIDAS:
        raise ValueError(
            f"Variable no permitida: {variable}"
        )

    conexion = obtener_conexion()

    try:
        # Compruebo que la columna existe realmente.
        columnas = {
            fila[1]
            for fila in conexion.execute(
                "PRAGMA table_info('poblacion')"
            ).fetchall()
        }

        if variable not in columnas:
            raise ValueError(
                f"La columna '{variable}' no existe en la BD"
            )

        # Solo incorporo al SQL una columna previamente validada.
        columna = f'"{variable}"'

        # El año se pasa como parámetro, nunca concatenado.
        condicion = ""
        parametros = []

        if anio is not None:
            condicion = (
                "WHERE TRY_CAST(anio AS INTEGER) = ?"
            )
            parametros.append(anio)

        consulta = f"""
            WITH distribucion AS (
                SELECT
                    COALESCE(
                        NULLIF(
                            TRIM(CAST({columna} AS VARCHAR)),
                            ''
                        ),
                        'Sin dato'
                    ) AS categoria,

                    COUNT(*) AS perfiles,

                    SUM(
                        CASE
                            WHEN TRY_CAST(
                                peso_poblacional AS DOUBLE
                            ) > 0
                            THEN TRY_CAST(
                                peso_poblacional AS DOUBLE
                            )
                            ELSE 0
                        END
                    ) AS poblacion

                FROM poblacion
                {condicion}
                GROUP BY 1
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

            FROM distribucion
            ORDER BY poblacion DESC
        """

        filas = conexion.execute(
            consulta, parametros
        ).fetchall()

        if not filas:
            raise ValueError(
                "No existen registros para los filtros indicados"
            )

        resultados = []

        for fila in filas:
            resultados.append({
                "categoria": fila[0],
                "perfiles": fila[1],
                "poblacion_ponderada": round(fila[2], 2),
                "porcentaje": (
                    round(fila[3], 2)
                    if fila[3] is not None else None
                )
            })

        return {
            "variable": variable,
            "anio": anio,
            "distribucion": resultados,
            "nota": (
                "Porcentajes calculados usando pesos "
                "de la población sintética. "
                "'Sin dato' se incluye en el denominador."
            )
        }

    finally:
        conexion.close()
