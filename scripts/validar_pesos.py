import duckdb

db_path = r"C:\Users\ainho\Desktop\accenture\poblacion_sintetica.duckdb"

# Conexión a la base de datos
con = duckdb.connect(db_path)

# Muestra de verificación de rangos de peso
df_validacion = con.execute("""
    SELECT 
        ccaa, 
        COUNT(*) AS total_muestra, 
        ROUND(SUM(peso_poblacional), 2) AS suma_pesos,
        ROUND(AVG(peso_poblacional), 2) AS peso_promedio,
        ROUND(MIN(peso_poblacional), 2) AS peso_min,
        ROUND(MAX(peso_poblacional), 2) AS peso_max
    FROM poblacion 
    GROUP BY ccaa 
    ORDER BY total_muestra DESC
    LIMIT 5
""").df()

print("--- DIAGNÓSTICO RÁPIDO DE PESOS ---")
print(df_validacion)

con.close()