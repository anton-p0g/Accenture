import duckdb
import pandas as pd

# Ajustar formato de salida en consola
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

db_path = r"C:\Users\ainho\Desktop\accenture\poblacion_sintetica.duckdb"
con = duckdb.connect(db_path)

print("="*60)
print("       AUDITORÍA DE LA BASE DE DATOS DUCKDB")
print("="*60)

# 1. Resumen de Comunidades Autónomas (CCAA) con Peso Poblacional Ponderado
# 1. Resumen de Comunidades Autónomas (CCAA) con Peso Poblacional Ponderado
print("\n--- 1. DISTRIBUCIÓN POR CCAA (Población Representada) ---")
df_ccaa = con.execute("""
    SELECT 
        ccaa,
        COUNT(*) as muestra_sintetica,
        ROUND(SUM(CAST(peso_poblacional AS DOUBLE)), 2) as poblacion_estimada,
        ROUND(AVG(CAST(peso_poblacional AS DOUBLE)), 2) as peso_medio,
        ROUND(
            SUM(CAST(peso_poblacional AS DOUBLE)) * 100.0 / 
            SUM(SUM(CAST(peso_poblacional AS DOUBLE))) OVER (), 2
        ) as pct_poblacion
    FROM poblacion
    GROUP BY ccaa
    ORDER BY poblacion_estimada DESC
""").df()
print(df_ccaa)

# 2. Distribución por Grupos de Edad y Sexo
print("\n--- 2. DISTRIBUCIÓN POR GRUPO DE EDAD Y SEXO ---")
df_edad_sexo = con.execute("""
    SELECT 
        grupo_edad,
        sexo,
        COUNT(*) as total_personas,
        ROUND(AVG(peso_poblacional), 2) as peso_medio
    FROM poblacion
    GROUP BY grupo_edad, sexo
    ORDER BY grupo_edad, sexo
""").df()
print(df_edad_sexo)

# 3. Distribución por Situación Laboral (Armonizada)
print("\n--- 3. SITUACIÓN LABORAL (ECV - INE) ---")
df_laboral = con.execute("""
    SELECT 
        situacion_laboral,
        COUNT(*) as muestra,
        ROUND(COUNT(*) * 100.0 / 25000, 2) as pct_muestra
    FROM poblacion
    GROUP BY situacion_laboral
    ORDER BY muestra DESC
""").df()
print(df_laboral)

# 4. Distribución de Nivel de Estudios
print("\n--- 4. NIVEL DE ESTUDIOS (Armonizado) ---")
df_estudios = con.execute("""
    SELECT 
        estudios,
        COUNT(*) as muestra,
        ROUND(COUNT(*) * 100.0 / 25000, 2) as pct_muestra
    FROM poblacion
    GROUP BY estudios
    ORDER BY muestra DESC
""").df()
print(df_estudios)

# 5. Renta y Vivienda (Quintiles)
print("\n--- 5. QUINTILES DE RENTA Y TENENCIA DE VIVIENDA ---")
df_renta_vivienda = con.execute("""
    SELECT 
        quintil_renta_hogar_ecv,
        vivienda,
        COUNT(*) as total
    FROM poblacion
    GROUP BY quintil_renta_hogar_ecv, vivienda
    ORDER BY quintil_renta_hogar_ecv, vivienda
""").df()
print(df_renta_vivienda.head(10))

# 6. Muestras del Prompt Narrativo (Ficha Social)
print("\n--- 6. EJEMPLO DE FICHA NARRATIVA (`ficha_social_v2`) ---")
ficha_muestra = con.execute("""
    SELECT id, ficha_social_v2 
    FROM poblacion 
    LIMIT 2
""").fetchall()

for row in ficha_muestra:
    print(f"\n[ID: {row[0]}]")
    print(row[1])

con.close()