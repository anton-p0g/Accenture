# Pulso web

Frontend en React, TypeScript y Vite. La portada usa la paleta y tipografía de `pulso_presentacion_claro.html`.

La portada presenta un único formulario para escribir preguntas. Envía cada consulta a `POST /escenarios/chat`, que devuelve el total y, cuando hay datos, desgloses por sexo y edad. El año se puede incluir en el texto de la pregunta; si no se indica, se usa 2026. Solo aparecen vistas para las que hay resultados. Los porcentajes de cada subgrupo se calculan dentro de ese grupo; no se suman entre grupos.

Las seis consultas completadas más recientes se conservan en memoria junto con sus resultados. Las anteriores aparecen como cartas detrás de la pregunta seleccionada; al elegir una se recupera su resultado sin otra llamada a la API. Al recargar la página, el historial se borra para empezar una demo desde cero.

```bash
cd web
npm install
npm run dev
```

Inicia el backend desde la raíz del repositorio con `.venv/bin/python -m backend.run`. Vite lee `BACKEND_PORT` del `.env` de la raíz y envía allí las peticiones `/escenarios`. Si necesitas apuntar a otro servicio, inicia Vite así:

```bash
PULSO_API_TARGET=http://127.0.0.1:8001 npm run dev
```

Abre la URL exacta que muestra Vite, normalmente `http://127.0.0.1:5173`. Para comprobar la compilación: `npm run build`. En producción, el servidor debe servir `/escenarios` desde el mismo origen que la web.

## Escena central y gráficos de partículas

La portada muestra el mapa de España centrado y el chat debajo, sin textos de presentación ni columna lateral. Al preguntar, el mismo canvas pasa del mapa a los gráficos y aprovecha todo el ancho disponible. General, Por sexo y Por edad cambian la agrupación sin otra petición a la API. El logotipo permite volver al mapa; las seis consultas recientes siguen disponibles en el menú superior. Las cifras y fuentes detalladas se abren desde el enlace bajo el chat.

Las 4.644 partículas conservan su identidad durante la animación. Cada una sigue una ruta curva con ritmos y pequeños desvíos propios; al llegar, forman bandas densas e irregulares, con tamaños variados y una deambulación suave para dar aspecto de multitud. El mapa mantiene su proporción al cambiar de tamaño. Los gráficos calculan sus posiciones y tamaños a partir del espacio real del canvas: dos columnas para sexo y hasta tres para los grupos de edad en pantallas grandes. En móvil se apilan con espacio suficiente para las etiquetas.

Los puntos intensos representan el porcentaje de cada respuesta y los tenues, el resto del grupo. Cada opción tiene su propia escala de 0 a 100 %; las preguntas multirrespuesta no se normalizan. Las respuestas sin porcentajes muestran su texto o indicador disponible, sin inventar gráficos. Los colores y tamaños no representan poblaciones reales ni una encuesta validada.

Durante la carga hay un latido común lento, de aproximadamente 3,1 segundos por ciclo, que aumenta el tamaño y brillo de los puntos, los halos y la escala del mapa hasta un 3 %. La fase acumulada evita saltos al variar la intensidad. Los círculos se dibujan en lotes reutilizables por color y opacidad, y solo una de cada doce partículas tiene halo. La preferencia de movimiento reducido suprime los recorridos, la deambulación y el latido.

La espera visual mínima es de cinco segundos y se ejecuta a la vez que la petición, sin añadir cinco segundos después de recibirla. El formulario bloquea envíos duplicados; cambiar de grupo, abrir el detalle, volver al mapa o recuperar una consulta no hace llamadas. No se han añadido dependencias ni servicios de pago.

La interfaz utiliza barras horizontales. El selector temporal de orientación se ha retirado, pero `ParticleScene` conserva la opción `orientation="vertical"` y sus estilos para poder recuperarla. En horizontal, las pantallas amplias reservan columnas independientes para etiqueta, barra y porcentaje; las celdas estrechas colocan la etiqueta y el porcentaje encima con espacio suficiente. En vertical, cada respuesta ocupa una columna, con el porcentaje encima y la etiqueta debajo. Los grupos tienen títulos separados por una línea suave, y el gráfico crece verticalmente cuando hay demasiadas filas para la altura disponible.
