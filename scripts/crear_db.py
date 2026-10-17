import duckdb

# 1. Rutas
csv_procesado = r"C:\Users\ainho\Desktop\accenture\poblacion_sintetica_procesada.csv"
db_path = r"C:\Users\ainho\Desktop\accenture\poblacion_sintetica.duckdb"

# Reemplazar barras invertidas en una variable separada
csv_clean = csv_procesado.replace("\\", "/")

print("Creando base de datos DuckDB...")

# 2. Conectar y volcar la tabla
con = duckdb.connect(db_path)

# Crear la consulta SQL usando la variable limpia
query = f"""
    CREATE OR REPLACE TABLE poblacion AS 
    SELECT * FROM read_csv_auto('{csv_clean}', encoding='utf-8')
"""

con.execute(query)

# Comprobar filas cargadas
total = con.execute("SELECT COUNT(*) FROM poblacion").fetchone()[0]

print(f"\n¡Base de datos DuckDB creada con éxito!")
print(f"Archivo generado: {db_path}")
print(f"Total de individuos en la tabla 'poblacion': {total}")

con.close()