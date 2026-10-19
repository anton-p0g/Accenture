"""Generador reproducible de ESCENARIOS SINTÉTICOS (no encuesta ni predicción validada).
Ejecutar desde raíz del repo: python scripts/generar_escenarios.py
Necesita data/poblacion_sinteticaV2.csv (o --origen) y Python estándar.
"""
import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

SEMILLA = 20261018
VERSION = 'demo_escenarios_1.0'
ANOS = range(2020, 2028)

# Observaciones oficiales, NO respuestas a las cuatro preguntas.
# INE TIC 2025 tabla de evolución 2020–2025, universo 16–74 años.
TIC_INTERNET = {2020:93.2, 2021:93.9, 2022:94.5, 2023:95.4, 2024:95.8, 2025:96.3}
TIC_DIARIO = {2020:83.1, 2021:85.8, 2022:87.1, 2023:90.0, 2024:91.5, 2025:92.5}
TIC_COMPRAS = {2020:53.8, 2021:55.2, 2022:55.3, 2023:55.9, 2024:56.7, 2025:59.6}
# Tasas de paro EPA 4T (NO tasas medias anuales), población activa.
EPA_PARO_4T = {2020:16.13, 2021:13.44, 2022:12.99, 2023:11.80, 2024:10.61, 2025:9.93}
URL_TIC = 'https://www.ine.es/dyngs/Prensa/TICH2025.htm'
URL_EPA = 'https://www.ine.es/prensa/epa_tabla.htm'
URL_CIS = 'https://www.cis.es/documents/d/cis/es3471sdMT_a'

PREGUNTAS = {
    'P1': {'texto':'¿Aceptarías que una IA ayudara a cuidar a un familiar mayor, como apoyo humano?', 'opciones':['Sí','Depende','No'], 'ambito':'actitud_ia_cuidados', 'procedencia':'SIMULACION_HIPOTETICA'},
    'P2': {'texto':'¿Prohibirías los pisos turísticos en el centro de tu ciudad?', 'opciones':['Sí, prohibir','Limitar sin prohibir','No prohibir','No sabe'], 'ambito':'regulacion_vivienda_turismo', 'procedencia':'SIMULACION_HIPOTETICA'},
    'P3': {'texto':'¿Qué mensaje te convence más para ahorrar energía en casa: 200 euros/año o menor huella de carbono?', 'opciones':['Ahorro económico','Huella de carbono','Indiferente'], 'ambito':'preferencia_mensaje', 'procedencia':'SIMULACION_HIPOTETICA'},
    'P4': {'texto':'¿Qué te haría cambiar de banco: cero comisiones, atención humana 24/7 o app de IA?', 'opciones':['Cero comisiones','Atención humana 24/7','App con IA','Ninguna'], 'ambito':'preferencia_producto', 'procedencia':'SIMULACION_HIPOTETICA'},
}

COLUMNAS = [
 'id_escenario','id_plantilla_2025','anio','edad','grupo_edad','sexo','ccaa','estudios','vivienda','situacion_laboral',
 'quintil_renta','uso_ia_escenario','ideologia_declarada_imputada','urbanizacion','peso_relativo_escenario',
 'necesita_apoyo_cuidados_hipotetico','tension_vivienda_hipotetica','sensibilidad_precio_hipotetica','preocupacion_ambiental_hipotetica',
 'p1_si','p1_depende','p1_no', 'p2_prohibir','p2_limitar','p2_no_prohibir','p2_ns',
 'p3_ahorro','p3_ambiente','p3_indiferente', 'p4_comisiones','p4_humano','p4_ia','p4_ninguna',
 'respuesta_p1','respuesta_p2','respuesta_p3','respuesta_p4','tipo_registro','metodo','version_modelo'
]


def booleano(texto):
    return str(texto).strip().lower() in {'si','sí','true','1'}

def no_est(texto):
    return not texto or texto.strip().lower() in {'no estimado','n.s.','n.c.','nan'}

def edad_grupo(edad):
    for lo, hi, grupo in [(18,24,'18-24'),(25,34,'25-34'),(35,44,'35-44'),(45,54,'45-54'),(55,64,'55-64'),(65,74,'65-74'),(75,84,'75-84'),(85,99,'85-99'),(100,200,'100+')]:
        if lo <= edad <= hi: return grupo
    return '18+'

def seed_from(s):
    digest = hashlib.sha256(f'{SEMILLA}:{s}'.encode('utf-8')).digest()
    return int.from_bytes(digest[:8],'big')

def softmax(xs):
    maximum=max(xs)
    values=[math.exp(v-maximum) for v in xs]
    total=sum(values)
    return [v/total for v in values]

def categorica(probs, labels, rand):
    u=rand.random()
    acum=0.0
    for p, label in zip(probs,labels):
        acum+=p
        if u <= acum: return label
    return labels[-1]

def indice_sintetico(plantilla, ano):
    """Nunca debe describirse como una opinión observada ni propensión validada."""
    edad=int(plantilla['edad'])
    renta=plantilla.get('quintil_renta_hogar_ecv','') or ''
    vivienda=plantilla.get('vivienda_ecv','') or ''
    urbanizacion=plantilla.get('urbanizacion_ecv','') or ''
    usa_ia=plantilla.get('usa_ia','')
    base_ia = booleano(usa_ia)
    # Multiplicadores de ADOPCION HIPOTETICA de IA, sin serie individual observada.
    escala={2020:.06,2021:.10,2022:.18,2023:.38,2024:.63,2025:1.0,2026:1.10,2027:1.20}[ano]
    ur = random.Random(seed_from('ia:'+plantilla['id']+':'+str(ano)))
    if ano == 2025: ia = base_ia if not no_est(usa_ia) else False
    elif ano < 2025: ia = base_ia and (ur.random()<escala)
    else: ia = base_ia or ((not base_ia) and edad <=74 and ur.random()<0.15*(ano-2025))
    # Indicadores contextuales sólo hipotéticos, NO medidos por persona.
    rp={'Q1':1.0,'Q2':.78,'Q3':.56,'Q4':.31,'Q5':.12}.get(renta,.55)
    alquila='alquiler' in vivienda.lower()
    ciudad='muy poblada' in urbanizacion.lower()
    semilla_aleatoria=random.Random(seed_from('latentes:'+plantilla['id']))
    cuidado = (edad>=45 and semilla_aleatoria.random()<.25) or (semilla_aleatoria.random()<.08)
    tension = min(1.0, .20 + .28*alquila+.18*rp+(.06 if ciudad else 0))
    precio = min(1.0, .18 + .67*rp)
    ambiente = .25 + .5*semilla_aleatoria.random()
    drift = (ano-2025)
    # Ningún coeficiente está calibrado con respuestas reales a P1-P4.
    p1=softmax([.0 + .48*ia + .16*cuidado + .08*drift,
                .30 + .14*cuidado,
                -.35 + .15*(edad>=70) - .25*ia])
    p2=softmax([-.05 + .75*tension + .17*ciudad + .035*drift,
                .40 + .15*ciudad,
                -.20 - .18*tension,
                -1.25])
    p3=softmax([.35 + .95*precio,
                .15 + 1.0*ambiente,
                -.25])
    p4=softmax([.45+ .60*precio,
                .27 + .18*(edad>=60),
                -.10 + .72*ia + .06*drift,
                -.60])
    rand=random.Random(seed_from('respuestas:'+plantilla['id']+':'+str(ano)))
    respuestas=[categorica(p,PREGUNTAS[f'P{i}']['opciones'],rand) for i,p in enumerate([p1,p2,p3,p4],start=1)]
    return [ia,cuidado,tension,precio,ambiente,p1,p2,p3,p4,respuestas]


def crear_historicos(carpeta):
    path=carpeta/'indicadores_oficiales_2020_2025.csv'
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(['anio','indicador','valor','unidad','universo','periodo','tipo_dato','fuente','url','nota'])
        for ano in range(2020,2026):
            for indicador, serie in [('internet_ultimos_3_meses',TIC_INTERNET),('internet_diario',TIC_DIARIO),('compras_internet_ultimos_3_meses',TIC_COMPRAS)]:
                w.writerow([ano,indicador,serie[ano],'porcentaje','personas de 16 a 74 años','encuesta TIC anual','OBSERVADO_INE','INE Encuesta TIC',URL_TIC,'Datos agregados, no opiniones individuales'])
            w.writerow([ano,'tasa_paro_cuarto_trimestre',EPA_PARO_4T[ano],'porcentaje','poblacion activa','cuarto trimestre','OBSERVADO_INE','INE EPA 4T',URL_EPA,'No es tasa media anual; no confundir universos'])
        w.writerow([2025,'uso_ia_generativa_ultimos_3_meses',37.9,'porcentaje','personas de 16 a 74 años','encuesta TIC 2025','OBSERVADO_INE','INE Encuesta TIC',URL_TIC,'Dato único 2025; NO extrapolar a toda la población adulta'])
        w.writerow([2025,'uso_banca_internet_ultimos_3_meses',74.7,'porcentaje','personas de 16 a 74 años','encuesta TIC 2025','OBSERVADO_INE','INE Encuesta TIC',URL_TIC,'Indicador de uso bancario, no preferencia de cambio de banco'])
    path2=carpeta/'contexto_cis_2024.csv'
    with path2.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(['anio','estudio','pregunta_original','respuesta','porcentaje','universo','tipo_dato','url','advertencia'])
        rows=[('Sí',76.3),('No',13.6),('Depende',1.3),('No sabe/duda',7.0),('No contesta',1.9)]
        for resp,pct in rows:
            w.writerow([2024,'CIS 3471 Turismo y gastronomía (II)','¿Es partidario/a de que se controle la expansión de los pisos turísticos en España?',resp,pct,'muestra CIS 3471 nacionalidad española 18+','OBSERVADO_CIS',URL_CIS,'CONTROLAR la expansión NO es PROHIBIR pisos turísticos; distintas preguntas. Redondeos pueden superar 100'])
    return path,path2


def crear_proyecciones(carpeta):
    path=carpeta/'proyecciones_macro_2026_2027_EXPERIMENTALES.csv'
    series={'internet_ultimos_3_meses':TIC_INTERNET,'internet_diario':TIC_DIARIO,'compras_internet_ultimos_3_meses':TIC_COMPRAS,'tasa_paro_cuarto_trimestre':EPA_PARO_4T}
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(['anio','indicador','valor_central','escenario_bajo','escenario_alto','unidad','tipo_dato','metodo','fuente_histórica','nota'])
        for ind, y in series.items():
            # Media anual de incrementos de 2023 a 2025, sin entrenamiento posterior.
            slope=(y[2025]-y[2023])/2
            slope=max(-2.0,min(slope,3.0))
            for ano in [2026,2027]:
                diff=ano-2025
                central=max(0,min(100,y[2025]+slope*diff))
                # Banda DE ESCENARIOS HEURISTICA. No es intervalo estadístico de confianza.
                incertidumbre=(1.5 if ind != 'tasa_paro_cuarto_trimestre' else 2.0)*diff
                lo=max(0,central-incertidumbre)
                hi=min(100,central+incertidumbre)
                w.writerow([ano,ind,round(central,2),round(lo,2),round(hi,2),'porcentaje','PROYECCION_HEURISTICA_NO_VALIDADA','pendiente 2023-2025 extrapolada con tope ±2/3 puntos por año',URL_EPA if ind=='tasa_paro_cuarto_trimestre' else URL_TIC,'No es previsión oficial. Intervalo heurístico, no banda de confianza'])
    return path


def crear_escenarios(origen, destino):
    with origen.open(encoding='utf-8-sig',newline='') as f:
        fuentes=list(csv.DictReader(f))
    if not fuentes or not {'id','edad','ccaa','sexo','peso_poblacional','usa_ia'}.issubset(fuentes[0]):
        raise ValueError('CSV de origen no corresponde al esquema V2 esperado')
    baselines=[]
    for s in fuentes:
        try: peso=float(s['peso_poblacional'])
        except (TypeError,ValueError): continue
        if peso <=0: continue
        baselines.append(s)
    if not baselines: raise ValueError('Sin perfiles válidos')
    salida=destino/'escenarios_perfiles_2020_2027.csv'
    with salida.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(COLUMNAS)
        for ano in ANOS:
            # Total de los pesos relativas de la sección transversal=1 por año.
            norm=sum(float(s['peso_poblacional'])*(1+.0025*(ano-2025)*(int(s['edad'])-45)/20) for s in baselines)
            for s in baselines:
                eid=f'ESC{ano}-{s["id"].split("-")[-1]}'
                edad=int(s['edad'])
                ideologia=s.get('ideologia_1_10_cis','')
                vivienda=s.get('vivienda_ecv') or 'No estimado'
                quintil=s.get('quintil_renta_hogar_ecv') or 'No estimado'
                laboral=s.get('situacion_laboral_ecv') or 'No estimado'
                urbano=s.get('urbanizacion_ecv') or 'No estimado'
                ia,cuidado,tension,precio,ambiente,p1,p2,p3,p4,respuestas=indice_sintetico(s,ano)
                peso=float(s['peso_poblacional'])*(1+.0025*(ano-2025)*(edad-45)/20)/norm
                proba=p1+p2+p3+p4
                writer.writerow([
                    eid,s['id'],ano,edad,edad_grupo(edad),s['sexo'],s['ccaa'],s['estudios'],vivienda,
                    laboral,quintil,'Si' if ia else 'No',ideologia,urbano,f'{peso:.12f}',
                    'Si' if cuidado else 'No',f'{tension:.4f}',f'{precio:.4f}',f'{ambiente:.4f}',
                    *[f'{v:.6f}' for v in proba],*respuestas,
                    'HIPOTESIS_SINTETICA_2020_2027','escenario_reconstruido' if ano < 2025 else ('base_sintetica_2025' if ano==2025 else 'escenario_futuro'),VERSION
                ])
    return len(baselines),salida


def crear_resumen(destino, n):
    path=destino/'metadata_dataset.json'
    data={
      'version':VERSION,'semilla':SEMILLA,'anios':list(ANOS),'filas_por_anio':n,'filas_totales':n*len(list(ANOS)),
      'peso_relativo_anual':'suma = 1; NO representa 48 millones de adultos','dataset_base':'25.000 perfiles sintéticos de 2025; no contiene serie real microdatos 2020-2024',
      '2020_2024':'reconstrucciones hipotéticas desde plantilla 2025; NO observaciones históricas',
      '2025':'perfiles 2025 de fuente sintética + respuestas calculadas por supuestos',
      '2026_2027':'escenarios hipotéticos + proyecciones macro heurísticas; NO predicciones validadas',
      'opiniones':'P1-P4 SIMULADAS; no hay calibración directa con encuestas sobre esas preguntas',
      'equivalencia_cis':'La pregunta CIS sobre CONTROLAR pisos turísticos no es la pregunta P2 sobre PROHIBIR; NO calibrada P2',
      'prohibido':'presentar respuestas simuladas como preferencias observadas o como probabilidad de éxito verificable',
      'preguntas':PREGUNTAS,
      'fuentes':{'INE_TIC':URL_TIC,'INE_EPA':URL_EPA,'CIS_3471':URL_CIS}
    }
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (destino/'catalogo_preguntas.json').write_text(json.dumps(PREGUNTAS,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--origen',type=Path,default=Path('data/poblacion_sinteticaV2.csv'))
    parser.add_argument('--destino',type=Path,default=Path('data/escenarios'))
    a=parser.parse_args()
    a.destino.mkdir(parents=True,exist_ok=True)
    crear_historicos(a.destino)
    crear_proyecciones(a.destino)
    n,p=crear_escenarios(a.origen,a.destino)
    crear_resumen(a.destino,n)
    print(f'OK: {n} perfiles/año; {n*8} registros 2020-2027. Guardado en {a.destino}')
    print('ATENCION: respuestas P1–P4 y perfiles de años !=2025 son HIPOTESIS, no datos observados.')

if __name__=='__main__':main()
