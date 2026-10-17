import pandas as pd
import numpy as np

# 1. RUTAS DE ARCHIVOS
ruta_origen = r"C:\Users\ainho\Desktop\accenture\poblacion_sintetica (1).csv"
ruta_destino = (
    r"C:\Users\ainho\Desktop\accenture\poblacion_sintetica_procesada.csv"
)

print("Cargando dataset original...")

# Lectura inicial intentando Latin-1 o Python Engine para evitar fallos
try:
    df = pd.read_csv(
        ruta_origen, encoding="latin-1", sep=None, engine="python"
    )
except Exception:
    df = pd.read_csv(
        ruta_origen, encoding="utf-8", sep=None, engine="python"
    )

# ==========================================
# 2. CORRECCIÓN DE MOJIBAKE / CARACTERES ESPECIALES
# ==========================================
print("Corrigiendo caracteres y texto desconfigurado (Mojibake)...")

reemplazos = {
    "aÃ±os": "años",
    "formaciÃ³n": "formación",
    "CatÃ³lico/a": "Católico/a",
    "Ã³": "ó",
    "Ã±": "ñ",
    "Ã¡": "á",
    "Ã©": "é",
    "Ã­": "í",
    "Ãº": "ú",
}

# Aplicar corrección ÚNICAMENTE a las columnas de texto (evita corruptos numéricos)
cols_texto = df.select_dtypes(include=["object", "string"]).columns
for col in cols_texto:
    df[col] = df[col].astype(str).replace(reemplazos, regex=True)

# Corregir nombres de columnas si vinieran con Mojibake
df.columns = df.columns.str.replace("Ã³", "ó").str.replace("Ã±", "ñ")

# ==========================================
# 3. LIMPIEZA Y AJUSTE DE RENTA E INGRESOS
# ==========================================
print("Ajustando la variable de Renta...")

if "ingresos_hogar_anuales_2024_ecv" in df.columns:
    renta_str = (
        df["ingresos_hogar_anuales_2024_ecv"]
        .astype(str)
        .str.replace(".", "", regex=False)  # Quitar puntos de miles
        .str.replace(",", ".", regex=False)  # Cambiar coma por punto decimal
    )
    renta = pd.to_numeric(renta_str, errors="coerce")

    # Reescalar si los valores vienen multiplicados por 10
    if renta.median() > 100000:
        renta = renta / 10.0

    # Imputar valores negativos o nulos con la mediana de los válidos
    renta_valida = renta[renta > 0]
    mediana_renta = (
        renta_valida.median() if not renta_valida.empty else 25000.0
    )

    renta = renta.apply(
        lambda x: mediana_renta if (pd.isna(x) or x <= 0) else x
    )
    df["ingresos_hogar_anuales_2024_ecv"] = renta

# ==========================================
# 4. LIMPIEZA Y CORRECCIÓN DEL PESO POBLACIONAL
# ==========================================
print("Ajustando la variable de Peso Poblacional...")

if "peso_poblacional" in df.columns:
    # 1. Limpieza de caracteres y conversión a float
    peso_str = (
        df["peso_poblacional"]
        .astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    peso_num = pd.to_numeric(peso_str, errors="coerce")

    # 2. Peso objetivo exacto para escalar 25.000 individuos a 47.3M de población
    total_registros = len(df)
    peso_objetivo = round(47300000.0 / total_registros, 2)  # Evalúa a ~1892.00

    # 3. Sustituir valores corruptos (< 500 o > 5000 o nulos) por el peso objetivo
    df["peso_poblacional"] = np.where(
        (peso_num < 500) | (peso_num > 5000) | (pd.isna(peso_num)),
        peso_objetivo,
        peso_num,
    )

    print("Estadísticas de peso poblacional corregido:")
    print(df["peso_poblacional"].describe())

# ==========================================
# 5. ARMONIZACIÓN DE MUNICIPIOS Y EDAD/AÑOS
# ==========================================
print("Procesando Municipios y Rangos de Edad...")


def map_municipio(val):
    if pd.isna(val) or str(val).lower() == "nan":
        return "No especificado"
    return str(val).strip().title()


if "municipio" in df.columns:
    df["municipio_procesado"] = df["municipio"].apply(map_municipio)
elif "municipio_ine" in df.columns:
    df["municipio_procesado"] = df["municipio_ine"].apply(map_municipio)


def map_rango_edad(val):
    try:
        edad = float(str(val).replace(",", "."))
        if edad < 18:
            return "Menor de 18"
        elif 18 <= edad <= 29:
            return "18-29 años"
        elif 30 <= edad <= 44:
            return "30-44 años"
        elif 45 <= edad <= 64:
            return "45-64 años"
        elif edad >= 65:
            return "65+ años"
    except (ValueError, TypeError):
        pass

    v = str(val).lower()
    if "18" in v and "29" in v:
        return "18-29 años"
    elif "30" in v and "44" in v:
        return "30-44 años"
    elif "45" in v and "64" in v:
        return "45-64 años"
    elif "65" in v or "mayores" in v:
        return "65+ años"
    return "No especificado"


if "edad" in df.columns:
    df["tramo_edad"] = df["edad"].apply(map_rango_edad)

# ==========================================
# 6. ARMONIZACIÓN DE CATEGORÍAS
# ==========================================


def map_estudios(val):
    v = str(val).lower()
    if "superior" in v or "postsecundaria" in v or "universi" in v:
        return "Universitarios"
    elif "secundaria" in v or "orientaci" in v or "fp" in v:
        return "Secundaria/FP"
    elif "primaria" in v or "eso" in v:
        return "Basicos (hasta ESO)"
    return "No estimado"


def map_vivienda(val):
    v = str(val).lower()
    if "propiedad" in v:
        return "Propiedad"
    elif "alquiler" in v:
        return "Alquiler"
    elif "cesion" in v or "padres" in v:
        return "Vive con padres/familia"
    return "No estimado"


def map_laboral(val):
    v = str(val).lower()
    if "trabajando" in v or "trabaja" in v:
        return "Trabaja"
    elif "parado" in v or "paro" in v:
        return "En paro"
    elif "estudiante" in v:
        return "Estudiante"
    elif "jubilado" in v:
        return "Jubilado/a"
    elif "hogar" in v or "inactividad" in v or "incapacitado" in v:
        return "Trabajo domestico/otros"
    return "No estimado"


def map_religion(val):
    v = str(val).lower()
    if "practicante" in v and "no" not in v:
        return "Catolico practicante"
    elif "cat" in v:
        return "Catolico no practicante"
    elif "ateo" in v or "agn" in v or "indiferente" in v:
        return "No creyente/agnostico"
    elif "otra" in v:
        return "Otra religion"
    return "No estimado"


print("Armonizando y recategorizando columnas...")

if "estudios_ecv" in df.columns:
    df["estudios"] = df["estudios_ecv"].apply(map_estudios)

if "vivienda_ecv" in df.columns:
    df["vivienda"] = df["vivienda_ecv"].apply(map_vivienda)

if "situacion_laboral_ecv" in df.columns:
    df["situacion_laboral"] = df["situacion_laboral_ecv"].apply(map_laboral)

if "religion_cis" in df.columns:
    df["religion"] = df["religion_cis"].apply(map_religion)

if "ideologia_1_10_cis" in df.columns:
    df["ideologia_1_10"] = (
        pd.to_numeric(df["ideologia_1_10_cis"], errors="coerce")
        .fillna(5)
        .astype(int)
    )

if "ficha_social_v2" in df.columns:
    df["ficha"] = df["ficha_social_v2"]

# ==========================================
# 7. ELIMINAR COLUMNAS NO REQUERIDAS
# ==========================================
print("Eliminando columnas no requeridas o vacías...")

columnas_a_eliminar = [
    "municipio",
    "calidad_atributos_sociales",
    "validacion_predictiva",
]
df = df.drop(
    columns=[col for col in columnas_a_eliminar if col in df.columns]
)

# ==========================================
# 8. GUARDAR DATASET LIMPIO EN UTF-8-SIG
# ==========================================
print("Guardando dataset procesado en UTF-8-SIG...")

df.to_csv(ruta_destino, index=False, encoding="utf-8-sig")

print("\n¡Dataset procesado generado con éxito!")