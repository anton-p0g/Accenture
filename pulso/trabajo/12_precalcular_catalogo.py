"""Amplía el catálogo de la versión publicada: calcula y guarda en caché más preguntas, campañas y test A/B.

Se suma a las de 05_precalcular_demo.py. Las que ya están en caché no se recalculan, así que se puede
interrumpir y relanzar. Al final, compara con un LLM sin datos las que salen en verde.

Uso: cd trabajo && ../.venv/bin/python 12_precalcular_catalogo.py
"""
import time

from motor import Motor

PREGUNTAS = [
    # --- pensadas para el CIS (verde si el motor encuentra la misma pregunta)
    "¿Te importaría alquilar tu vivienda a alguien de otro origen, raza o religión?",
    "¿Crees que dentro de diez años habrá muchos más robots en las empresas?",
    "¿Crees que las energías renovables van a desarrollarse mucho en los próximos diez años?",
    "¿Crees que los vehículos eléctricos van a desarrollarse mucho en los próximos diez años?",
    "¿Cuánta habilidad tienes para hacer gestiones bancarias por internet?",
    "¿Has pagado con el móvil en el último año?",
    "¿Te sentirías cómodo si una inteligencia artificial interpretara tus radiografías?",
    "¿Te incomodaría que te operara un robot?",
    "¿Te preocupa que las empresas privadas usen datos clínicos para desarrollar inteligencia artificial?",
    "¿Hay que informar al paciente cuando se usa inteligencia artificial en su atención médica?",
    "¿Conoces herramientas de inteligencia artificial aplicadas a la salud?",
    "¿Cómo está tu salud en general?",
    "¿Tienes algún problema de salud crónico?",
    "¿Las listas de espera de la sanidad pública han mejorado o empeorado en el último año?",
    "¿Irías a la sanidad pública o a la privada para ver a un especialista?",
    "¿Tienes un seguro médico privado?",
    "¿Has ido a un profesional de salud mental en el último año?",
    "¿Cuánta confianza te dan los médicos de atención primaria?",
    "¿Estás satisfecho con las urgencias de los hospitales públicos?",
    "¿Te da miedo perder a un familiar cercano?",
    "¿Te da miedo que tu trabajo o tu pensión no te permitan vivir con dignidad?",
    "¿Crees que en diez años habrá más interés por la salud y el cuidado personal?",
    "¿Te cuesta llegar a final de mes?",
    "¿Cómo ha evolucionado tu capacidad de ahorro en el último año?",
    "¿Crees que la inflación subirá el próximo año?",
    "¿Crees que los tipos de interés subirán el próximo año?",
    "¿Cómo crees que estará la economía de tu hogar en los próximos seis meses?",
    "¿Usas habitualmente la banca online o la app de tu banco?",
    "¿Has tenido un fondo de inversión o acciones en los últimos cinco años?",
    "¿Crees que será más fácil encontrar empleo en los próximos seis meses?",
    "¿Crees que tu familia podría verse afectada por un incendio en el futuro?",
    "¿Quién debería encargarse de la lucha contra los incendios: el Gobierno central o las comunidades autónomas?",
    "¿Te da miedo el deterioro del medio ambiente?",
    "¿Crees que en diez años habrá más deterioro del medio ambiente?",
    "¿Crees que habrá muchos cambios económicos y sociales en los próximos diez años?",
    "¿Debe el Estado intervenir en la economía?",
    "¿Crees que en diez años la protección social del Estado será mayor o menor que ahora?",
    "¿Crees que en diez años habrá más consumo de drogas en España?",
    "¿Te da miedo contraer una enfermedad como la COVID?",
    # --- nuevas (ámbar o rojo): el CIS no las ha hecho
    "¿Vivirías en un piso compartido para pagar menos alquiler?",
    "¿Te mudarías a un pueblo si pudieras teletrabajar?",
    "¿Debería limitarse por ley el precio del alquiler?",
    "¿Crees que podrás comprar una vivienda antes de los 40 años?",
    ("¿Vivirías más lejos del trabajo a cambio de una casa más grande?", ["Sí", "Tal vez", "No"]),
    "¿Con qué frecuencia hablas con tus vecinos?",
    "¿Te sientes solo los fines de semana?",
    "¿Usarías una app para conocer gente nueva de tu barrio?",
    "¿Debería haber un plan nacional contra la soledad no deseada?",
    "¿En el último año has sentido que no tenías a quién pedir ayuda?",
    "¿Confiarías en un coche autónomo sin conductor?",
    "¿Debería prohibirse el móvil en los colegios?",
    ("¿Te preocupa que la inteligencia artificial te quite el trabajo?", ["Mucho", "Bastante", "Poco", "Nada"]),
    "¿Te fías más de una noticia escrita por una persona o por una inteligencia artificial?",
    "¿Pagarías una suscripción mensual a una inteligencia artificial?",
    "¿Pagarías más por productos de proximidad?",
    "¿Estás a favor de las zonas de bajas emisiones en las ciudades?",
    ("¿Viajarías menos en avión para cuidar el clima?", ["Sí", "Tal vez", "No"]),
    "¿Comerías menos carne para cuidar el planeta?",
    "¿Crees que los veranos en España serán cada vez más calurosos?",
    "¿Usarías una app para pedir cita médica en vez de llamar por teléfono?",
    "¿Deberían las farmacias poder recetar algunos medicamentos?",
    "¿Haces ejercicio al menos tres veces por semana?",
    "¿Debería la sanidad pública cubrir el dentista?",
    "¿Compras más por internet que en tiendas físicas?",
    "¿Pagarías más por una marca sostenible?",
    ("¿Has reducido tus gastos de ocio por la subida de precios?", ["Sí", "No"]),
    "¿Prefieres pagar en efectivo o con tarjeta?",
    "¿Comprarías ropa de segunda mano?",
    ("¿Estarías a favor de una semana laboral de cuatro días?", ["A favor", "En contra", "No lo sé"]),
    "¿Crees que los jóvenes vivirán peor que sus padres?",
    "¿Te gustaría trabajar desde casa todos los días?",
    "¿Cambiarías de compañía de la luz para ahorrar 10 € al mes?",
    # --- banca
    ("¿Cambiarías de banco por una cuenta remunerada al 3 %?", ["Sí", "Tal vez", "No"]),
    ("¿Te fías de los bancos españoles?", ["Mucho", "Algo", "Nada"]),
    "¿Usarías un banco 100 % digital como banco principal?",
    "¿Dejarías que una inteligencia artificial te recomiende en qué invertir?",
    ("¿Te preocupa el cierre de oficinas bancarias en tu zona?", ["Mucho", "Bastante", "Poco", "Nada"]),
    "¿Comprarías criptomonedas?",
    "¿Pagarías con el euro digital si el Banco Central Europeo lo lanzara?",
    "¿Prefieres una hipoteca a tipo fijo o a tipo variable?",
    # --- energía
    "¿Instalarías placas solares en tu casa si tuvieras ayudas?",
    ("¿Sabes qué tarifa de luz tienes contratada?", ["Sí", "Más o menos", "No"]),
    ("¿Estás a favor de alargar la vida de las centrales nucleares?", ["Sí", "No", "No lo sé"]),
    "¿Cambiarías la caldera de gas por una bomba de calor?",
    ("¿Te preocupa que se repita un gran apagón como el de abril de 2025?", ["Mucho", "Bastante", "Poco", "Nada"]),
    "¿Pondrías un punto de recarga para coche eléctrico en tu casa?",
    "¿Pagarías más en la factura por energía 100 % renovable?",
    # --- retail
    ("¿Dónde haces la compra principal: supermercado, hipermercado o tienda de barrio?", ["Supermercado", "Hipermercado", "Tienda de barrio"]),
    "¿Compras más marca blanca que hace un año?",
    "¿Usas las cajas de autocobro del supermercado?",
    ("¿Te influyen los influencers cuando compras algo?", ["Sí, a menudo", "A veces", "Nunca"]),
    ("¿Compras en plataformas como Shein o Temu?", ["Sí, a menudo", "A veces", "Nunca"]),
    "¿Harías la compra del supermercado por internet?",
    ("¿Usas tarjetas o apps de fidelización de tiendas?", ["Sí", "No"]),
    "¿Esperas al Black Friday para hacer compras grandes?",
    # --- elecciones (sin partidos ni intención de voto)
    ("¿Qué tema pesará más en tu voto: vivienda, economía, sanidad o inmigración?", ["La vivienda", "La economía", "La sanidad", "La inmigración"]),
    "¿Crees que el próximo Gobierno mejorará el acceso a la vivienda?",
    ("¿Te fías de las encuestas electorales?", ["Mucho", "Algo", "Nada"]),
    "¿Crees que la desinformación en redes sociales influirá en las próximas elecciones?",
    "¿Prefieres un Gobierno de un solo partido o de coalición?",
    ("¿Votarías por internet si se pudiera?", ["Sí", "Tal vez", "No"]),
    # --- elecciones con partidos: datos reales del CIS 3577 (13_banco_manual.py)
    "Si mañana hubiera elecciones generales, ¿a qué partido votarías?",
    "¿Quién preferirías como presidente del Gobierno?",
    "Del 0 al 10, ¿qué probabilidad hay de que vayas a votar en las próximas elecciones generales?",
    "¿Cuál es el problema que más te afecta a ti personalmente?",
    # --- sustituyen consultas antiguas con opciones mal propuestas por el LLM
    "¿Cómo valorarías tu situación económica personal actual?",
    "¿En el último año no has podido tomar un medicamento recetado por su coste?",
    # --- las dos preguntas de la presentación (la primera con opciones cerradas)
    ("¿Dejarías que una inteligencia artificial acompañara a un familiar mayor que vive solo?", ["Sí", "Tal vez", "No"]),
]
# (texto que se muestra en el chat, tipo, mensajes), igual que en 05_precalcular_demo.py
CAMPANAS = [
    ("Campaña: Abono único de transporte por 20 € al mes en toda España", "campana",
     ["Abono único de transporte por 20 € al mes en toda España"]),
    ("Campaña: Tu médico de cabecera, también por videollamada", "campana",
     ["Tu médico de cabecera, también por videollamada"]),
    ("Campaña: Alquila tu segunda vivienda con garantía pública de cobro", "campana",
     ["Alquila tu segunda vivienda con garantía pública de cobro"]),
    ("Campaña: Una inteligencia artificial te ayuda a hacer la declaración de la renta", "campana",
     ["Una inteligencia artificial te ayuda a hacer la declaración de la renta"]),
    ("Campaña: Apaga la luz una hora: el planeta te lo agradece", "campana",
     ["Apaga la luz una hora: el planeta te lo agradece"]),
    ("«Ahorra en tu factura de la luz con placas solares» vs «Produce tu propia energía limpia»", "ab",
     ["Ahorra en tu factura de la luz con placas solares", "Produce tu propia energía limpia"]),
    ("«Hipoteca a tipo fijo: duerme tranquilo» vs «Hipoteca a tipo variable: paga menos hoy»", "ab",
     ["Hipoteca a tipo fijo: duerme tranquilo", "Hipoteca a tipo variable: paga menos hoy"]),
    ("«Vacúnate de la gripe para protegerte» vs «Vacúnate de la gripe para proteger a tus mayores»", "ab",
     ["Vacúnate de la gripe para protegerte", "Vacúnate de la gripe para proteger a tus mayores"]),
    ("«Banco 100 % digital sin comisiones» vs «Banco con oficina cerca de casa»", "ab",
     ["Banco 100 % digital sin comisiones", "Banco con oficina cerca de casa"]),
    ("«Conoce a tus vecinos: comida popular este sábado» vs «¿Necesitas ayuda? Tus vecinos están aquí»", "ab",
     ["Conoce a tus vecinos: comida popular este sábado", "¿Necesitas ayuda? Tus vecinos están aquí"]),
    ("«Cuenta sin comisiones y sin condiciones» vs «Cuenta que te devuelve el 5 % de tus compras»", "ab",
     ["Cuenta sin comisiones y sin condiciones", "Cuenta que te devuelve el 5 % de tus compras"]),
    ("«Tarifa de luz con precio fijo 12 meses» vs «Tarifa de luz que sigue el precio del mercado»", "ab",
     ["Tarifa de luz con precio fijo 12 meses", "Tarifa de luz que sigue el precio del mercado"]),
    ("«Envío gratis en 24 horas» vs «Devoluciones gratis durante 60 días»", "ab",
     ["Envío gratis en 24 horas", "Devoluciones gratis durante 60 días"]),
    ("Campaña: Compra en tu barrio: el comercio local da vida a tu calle", "campana",
     ["Compra en tu barrio: el comercio local da vida a tu calle"]),
    ("«Vota por tu futuro» vs «Si no votas, otros deciden por ti»", "ab",
     ["Vota por tu futuro", "Si no votas, otros deciden por ti"]),
]


# --- tercera tanda (noche del 20/10): verdes sin opciones (si se fijan opciones, no se usa el CIS) y nuevas con opciones cerradas
PREGUNTAS += ['¿Te da miedo tener una infección de transmisión sexual?',
    '¿Te da miedo perder la vista?',
    '¿Te da miedo perder la vida?',
    '¿Te da miedo una crisis económica?',
    '¿Cuánto tiempo dedican los médicos de atención primaria a cada paciente?',
    '¿Cómo valoras la atención en la consulta de tu médico de familia?',
    '¿Has tenido que esperar más de una hora en la sala de espera del médico?',
    '¿Alguna vez has necesitado ver a tu médico de familia de la sanidad pública y no lo has conseguido?',
    '¿Cuánto tardaron en atenderte la última vez que pediste cita con tu médico de familia?',
    '¿Tienes acceso a tu historia clínica por internet?',
    '¿Cómo es la coordinación entre los distintos servicios médicos de la sanidad pública?',
    '¿La sanidad de tu comunidad autónoma es mejor o peor que la del resto de España?',
    '¿Te preocupa que la sanidad pública use datos clínicos para desarrollar inteligencia artificial?',
    '¿Debería el paciente poder negarse a que sus datos clínicos se usen para desarrollar inteligencia artificial?',
    '¿Hace falta legislar de forma específica la inteligencia artificial en la salud?',
    '¿Irías a la sanidad pública o a la privada si te tuvieran que ingresar en un hospital?',
    '¿Irías a la sanidad pública o a la privada para ver al médico de cabecera?',
    '¿Estás satisfecho con la atención primaria en los centros de salud?',
    '¿Cuánta confianza te dan los profesionales de enfermería?',
    '¿Cuántas veces has sacado dinero en efectivo en el último año?',
    '¿Cómo prefieres hacer las transferencias: en la oficina, por internet o con el móvil?',
    '¿Vas habitualmente a tu oficina bancaria?',
    '¿Has tenido un préstamo personal en los últimos cinco años?',
    '¿Has tenido un plan de pensiones en los últimos cinco años?',
    '¿Has tenido un seguro de vida en los últimos cinco años?',
    '¿Crees que el próximo año tendrás más o menos posibilidades de comprar muebles o electrodomésticos?',
    '¿Cómo ha ido la economía de España en los últimos seis meses?',
    '¿Cómo crees que estará la economía de tu comunidad autónoma en los próximos seis meses?',
    '¿Cómo ves la posibilidad de encontrar o mejorar empleo en España en los próximos seis meses?',
    '¿Te han afectado a ti o a tu familia los incendios de este verano?',
    '¿Crees que en diez años habrá más muertes por cáncer?',
    '¿Crees que en diez años habrá más interés por las cosas materiales?',
    '¿Crees que la ingeniería genética va a desarrollarse mucho en los próximos diez años?',
    '¿Crees que la biotecnología, como los alimentos transgénicos, va a desarrollarse mucho en los próximos diez años?',
    '¿Crees que los videojuegos y las tecnologías del ocio van a desarrollarse mucho en los próximos diez años?',
    '¿Crees que los robots domésticos van a desarrollarse mucho en los próximos diez años?',
    '¿Hay que favorecer la igualdad y la solidaridad, o que cada uno llegue tan lejos como pueda?',
    '¿Crees que Estados Unidos tendrá más influencia en el mundo dentro de diez años?',
    '¿Cuánto interés tienes por la política?', ('¿Cuánto de tu sueldo se va en pagar la vivienda?', ['Menos de un tercio', 'Entre un tercio y la mitad', 'Más de la mitad', 'No pago vivienda']),
    ('¿A qué edad pueden independizarse hoy los jóvenes en España?', ['Antes de los 25', 'Entre 25 y 30', 'Entre 30 y 35', 'Después de los 35']),
    ('¿Qué medida bajaría más el precio del alquiler?', ['Construir vivienda pública', 'Limitar los precios', 'Bajar impuestos a los propietarios', 'Limitar los pisos turísticos']),
    ('¿Prefieres vivir de alquiler o comprar una vivienda?', ['Alquilar', 'Comprar', 'Me da igual']),
    ('¿Aceptarías un piso más pequeño a cambio de vivir en el centro de la ciudad?', ['Sí', 'Tal vez', 'No']),
    ('¿Debería prohibirse que extranjeros no residentes compren vivienda en España?', ['Sí', 'No', 'No lo sé']),
    ('¿Volverías a vivir con tus padres para ahorrar?', ['Sí', 'Tal vez', 'No']),
    ('¿Cuántas veces a la semana quedas con amigos?', ['Ninguna', 'Una', 'Dos o tres', 'Más de tres']),
    ('¿Te sientes más solo ahora que hace cinco años?', ['Más solo', 'Igual', 'Menos solo']),
    ('¿Tienes a alguien a quien llamar si te pasa algo de madrugada?', ['Sí, a varias personas', 'Sí, a una persona', 'No']),
    ('¿Las redes sociales te hacen sentir más acompañado o más solo?', ['Más acompañado', 'Igual', 'Más solo']),
    ('¿Te apuntarías a una actividad de tu barrio para conocer gente?', ['Sí', 'Tal vez', 'No']),
    ('¿Hablarías con un chatbot cuando te sientes solo?', ['Sí', 'Tal vez', 'No']),
    ('¿Ayudarías a un vecino mayor que vive solo con la compra o los recados?', ['Sí', 'Tal vez', 'No']),
    ('¿Cuántas horas al día pasas con el móvil?', ['Menos de 2', 'Entre 2 y 4', 'Entre 4 y 6', 'Más de 6']),
    ('¿A qué edad debería tener un niño su primer móvil?', ['Antes de los 12', 'Entre 12 y 14', 'Entre 14 y 16', 'Después de los 16']),
    ('¿La inteligencia artificial hará tu trabajo más fácil o más difícil?', ['Más fácil', 'Igual', 'Más difícil', 'No trabajo']),
    ('¿Debería etiquetarse todo el contenido creado con inteligencia artificial?', ['Sí', 'No', 'No lo sé']),
    ('¿Confiarías en un diagnóstico médico hecho solo por una inteligencia artificial?', ['Sí', 'Tal vez', 'No']),
    ('¿Dejarías que los niños usen inteligencia artificial para hacer los deberes?', ['Sí', 'Con límites', 'No']),
    ('¿Te preocupa la privacidad de tus datos en internet?', ['Mucho', 'Bastante', 'Poco', 'Nada']),
    ('¿Desconectas del trabajo fuera de tu horario laboral?', ['Siempre', 'A veces', 'Nunca']),
    ('¿Has sufrido un fraude o una estafa por internet?', ['Sí', 'No', 'No estoy seguro']),
    ('¿Deberían prohibirse las redes sociales a los menores de 16 años?', ['Sí', 'No', 'No lo sé']),
    ('¿Cambiarás tu coche de gasolina o diésel por uno eléctrico en los próximos cinco años?', ['Sí', 'Tal vez', 'No', 'No tengo coche']),
    ('¿Apoyarías un impuesto a los vuelos cortos que tienen alternativa en tren?', ['Sí', 'No', 'No lo sé']),
    ('¿Has notado más olas de calor donde vives?', ['Mucho', 'Algo', 'Nada']),
    ('¿Te preocupa la sequía y la falta de agua?', ['Mucho', 'Bastante', 'Poco', 'Nada']),
    ('¿Quién debe hacer más contra el cambio climático?', ['El Gobierno', 'Las empresas', 'Los ciudadanos', 'La Unión Europea']),
    ('¿Pagarías más impuestos para proteger los bosques de los incendios?', ['Sí', 'Tal vez', 'No']),
    ('¿Cuántas horas duermes normalmente?', ['Menos de 6', 'Entre 6 y 7', 'Entre 7 y 8', 'Más de 8']),
    ('¿Has sentido ansiedad o estrés en el último mes?', ['Mucho', 'Algo', 'Nada']),
    ('¿Pagarías un seguro médico privado para evitar las listas de espera?', ['Sí', 'Ya lo tengo', 'No']),
    ('¿Debería la sanidad pública cubrir el psicólogo sin listas de espera?', ['Sí', 'No', 'No lo sé']),
    ('¿Te vacunarás de la gripe este invierno?', ['Sí', 'Tal vez', 'No']),
    ('¿Cuidas tu alimentación?', ['Mucho', 'Bastante', 'Poco', 'Nada']),
    ('¿Usas una app o un reloj inteligente para controlar tu salud?', ['Sí, a diario', 'A veces', 'No']),
    ('¿Te preocupa más tu salud física o tu salud mental?', ['La física', 'La mental', 'Las dos por igual']),
    ('¿Compras de segunda mano en apps como Wallapop o Vinted?', ['A menudo', 'A veces', 'Nunca']),
    ('¿Cuántas plataformas de series o música pagas?', ['Ninguna', 'Una', 'Dos o tres', 'Más de tres']),
    ('¿Cuántas veces comes fuera de casa a la semana?', ['Ninguna', 'Una', 'Dos o tres', 'Más de tres']),
    ('¿Viajarás al extranjero este año?', ['Sí', 'Tal vez', 'No']),
    ('¿Si compraras un coche, sería nuevo o de segunda mano?', ['Nuevo', 'De segunda mano', 'No compraría coche']),
    ('¿Pagas a plazos compras pequeñas?', ['A menudo', 'A veces', 'Nunca']),
    ('¿Te fías de los asesores financieros de tu banco?', ['Mucho', 'Algo', 'Nada']),
    ('¿Invertirías parte de tus ahorros en bolsa?', ['Sí', 'Tal vez', 'No']),
    ('¿Has cambiado de compañía de luz o gas en los últimos dos años?', ['Sí', 'No', 'No lo sé']),
    ('¿Pones la lavadora en las horas más baratas para ahorrar luz?', ['Ya lo hago', 'Lo haría', 'No']),
    ('¿Prefieres comprar en grandes cadenas o en el comercio de tu barrio?', ['Grandes cadenas', 'Comercio de barrio', 'Me da igual']),
    ('¿Devuelves a menudo lo que compras por internet?', ['A menudo', 'A veces', 'Nunca']),
    ('¿Estás satisfecho con tu trabajo?', ['Mucho', 'Bastante', 'Poco', 'No trabajo']),
    ('¿Te jubilarías antes aunque cobraras menos pensión?', ['Sí', 'Tal vez', 'No']),
    ('¿Crees que cobrarás una pensión cuando te jubiles?', ['Sí, completa', 'Sí, pero más baja', 'No']),
    ('¿Te irías a otro país por un trabajo mejor pagado?', ['Sí', 'Tal vez', 'No']),
    ('¿Es buena la inmigración para la economía española?', ['Sí', 'No', 'Depende']),
    ('¿Confías en la justicia española?', ['Mucho', 'Bastante', 'Poco', 'Nada']),
    ('¿Debería ser obligatorio votar?', ['Sí', 'No', 'No lo sé']),
    ('¿Hay hoy más igualdad entre hombres y mujeres que hace diez años?', ['Más', 'Igual', 'Menos']),
    ('¿Has hecho voluntariado en el último año?', ['Sí', 'No']),
    ('¿Preferirías trabajar cuatro días a la semana cobrando un poco menos?', ['Sí', 'Tal vez', 'No']),
    ('¿Crees que tus hijos vivirán mejor que tú?', ['Mejor', 'Igual', 'Peor']),
    ('¿Te mudarías a otra comunidad autónoma por una vivienda más barata?', ['Sí', 'Tal vez', 'No']),
    ('¿Te preocupa que tus padres o abuelos estén solos?', ['Mucho', 'Bastante', 'Poco', 'Nada']),
    ('¿Usarías un robot en casa para las tareas del hogar?', ['Sí', 'Tal vez', 'No'])]
CAMPANAS += [('«Tu pensión, en tus manos: empieza a ahorrar hoy» vs «Jubílate tranquilo con un plan a tu medida»', 'ab', ['Tu pensión, en tus manos: empieza a ahorrar hoy', 'Jubílate tranquilo con un plan a tu medida']),
    ('«Come sano: más fruta, menos azúcar» vs «Cuida tu corazón: menos azúcar»', 'ab', ['Come sano: más fruta, menos azúcar', 'Cuida tu corazón: menos azúcar']),
    ('Campaña: Desconecta para conectar: un día a la semana sin pantallas', 'campana', ['Desconecta para conectar: un día a la semana sin pantallas']),
    ('Campaña: Ayuda de 500 € para jóvenes que se independicen', 'campana', ['Ayuda de 500 € para jóvenes que se independicen']),
    ('«Recicla: tu barrio más limpio» vs «Recicla: multas de hasta 600 € si no lo haces»', 'ab', ['Recicla: tu barrio más limpio', 'Recicla: multas de hasta 600 € si no lo haces']),
    ('«Teletrabajo dos días por semana» vs «Jornada intensiva todo el año»', 'ab', ['Teletrabajo dos días por semana', 'Jornada intensiva todo el año']),
    ('Campaña: Bono cultural de 400 € para mayores de 65 años', 'campana', ['Bono cultural de 400 € para mayores de 65 años']),
    ('«Seguro de salud con videoconsulta 24 horas» vs «Seguro de salud sin copagos»', 'ab', ['Seguro de salud con videoconsulta 24 horas', 'Seguro de salud sin copagos'])]


def informe(t, etiqueta, r, texto):
    lider = max(range(len(r["opciones"])), key=lambda j: r["agregados"]["total"][j])
    print(f"{time.time() - t:5.0f}s  {etiqueta:10s} {r['agregados']['total'][lider]:5.1f}% «{r['opciones'][lider]}»  · {texto}", flush=True)


def main():
    m = Motor()
    verdes = []
    for q in PREGUNTAS:
        q, opciones = q if isinstance(q, tuple) else (q, None)  # (pregunta, opciones fijadas)
        t = time.time()
        try:
            r = m.responder(q, opciones)
        except Exception as e:  # una pregunta que falla no para el resto
            print(f"ERROR {q}: {e}", flush=True)
            continue
        informe(t, r["modo"], r, q)
        if r["modo"] == "evidencia":
            verdes.append(q)
    for texto, tipo, mensajes in CAMPANAS:
        t = time.time()
        try:
            informe(t, tipo, m.responder(texto, tipo=tipo, mensajes=mensajes), texto)
        except Exception as e:
            print(f"ERROR {texto}: {e}", flush=True)
    for q in verdes:  # panel «LLM sin datos vs pulso»
        try:
            c = m.comparar(q)
            print(f"comparar  pulso ±{c['error_pulso']} · LLM sin datos ±{c['error_llm_solo']}  · {q}", flush=True)
        except Exception as e:
            print(f"ERROR comparar {q}: {e}", flush=True)
    print("FIN", flush=True)


if __name__ == "__main__":
    main()
