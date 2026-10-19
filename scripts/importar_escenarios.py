"""Importa CSV del paquete a una BD NUEVA sin tocar data/poblacion_sintetica.duckdb.
Ejecutar desde raíz del repositorio: python scripts/importar_escenarios.py
"""
from pathlib import Path
import duckdb

RAIZ=Path(__file__).resolve().parent.parent
RUTA_DATOS=RAIZ/'data'/'escenarios'
RUTA_BD=RAIZ/'data'/'escenarios_sinteticos.duckdb'

ARCHIVOS={
    'opiniones_escenario':RUTA_DATOS/'escenarios_perfiles_2020_2027.csv',
    'indicadores_observados':RUTA_DATOS/'indicadores_oficiales_2020_2025.csv',
    'indicadores_proyectados':RUTA_DATOS/'proyecciones_macro_2026_2027_EXPERIMENTALES.csv',
    'contexto_cis':RUTA_DATOS/'contexto_cis_2024.csv',
}

def main():
    for nombre, ruta in ARCHIVOS.items():
        if not ruta.is_file():
            raise FileNotFoundError(f'Falta {nombre}: {ruta}')
    RUTA_BD.parent.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(str(RUTA_BD))
    try:
        for tabla, ruta in ARCHIVOS.items():
            # DuckDB lee los tipos desde el archivo CSV; no ejecutamos SQL de usuarios.
            con.execute(f'CREATE OR REPLACE TABLE "{tabla}" AS SELECT * FROM read_csv_auto(?, header=true, sample_size=-1)', [str(ruta)])
            n=con.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]
            print(f'{tabla}: {n:,} registros')
        # Comprobación: cada año debe tener 25.000 perfiles.
        print('Perfiles por año:',con.execute('SELECT anio,COUNT(*) FROM opiniones_escenario GROUP BY anio ORDER BY anio').fetchall())
        print('BD generada:',RUTA_BD)
    finally: con.close()

if __name__=='__main__':main()
