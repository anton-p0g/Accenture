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

## Mapa y gráficos de partículas

La portada y el chat comparten un único canvas con 4.644 partículas. En escritorio, el mapa permanece fijo a la derecha mientras la introducción se desvanece al bajar hacia el formulario de la izquierda. Durante la consulta se intensifica el latido; al recibir resultados, las mismas partículas se desplazan hasta formar bandas de puntos por respuesta. Las barras usan puntos intensos para el porcentaje consultado y puntos tenues para el resto; cada respuesta tiene una escala independiente de 0 a 100 %, sin normalizar preguntas multirrespuesta. Las filas de puntos y su movimiento sutil se inspiran en `../frontend/app.js`.

Las vistas General, Por sexo y Por edad están sincronizadas con el detalle textual. La pregunta activa selecciona edad o sexo cuando lo menciona y existen esos datos. Más de dos grupos se distribuyen en dos columnas. No se inventan gráficos para respuestas sin porcentajes. En móvil el mapa se coloca encima del formulario y permanece visible al desplazarse. Se respeta la preferencia de movimiento reducido. Cada envío genera una sola petición; cambiar de vista o recuperar el historial no realiza llamadas. No se han añadido dependencias ni servicios de pago.

Ajuste visual posterior: el mapa distribuye los puntos con desplazamientos deterministas irregulares y radios individuales; su deriva lenta mantiene la silueta. La cuadrícula de cada barra calcula cuántas filas necesita según el número de partículas y el ancho disponible, aproximando el mismo espaciado entre puntos en ambos ejes para evitar columnas aisladas. El radio se interpola al cambiar entre mapa y gráfico.

El movimiento entre formas usa rutas curvas individuales, pequeñas desviaciones y distintos tiempos de salida y llegada por partícula. Los recorridos parten de la posición actual al cambiar de vista, incluso si se interrumpe una transición. En el mapa hay deambulación suave con ritmos independientes; al llegar a los gráficos ese movimiento disminuye para mantener la lectura. La preferencia de movimiento reducido evita los recorridos y la deambulación.

La disposición final de los gráficos también representa una multitud: conserva la densidad de cada barra, pero reparte las partículas en bandas continuas, sin filas ni columnas alineadas. Las posiciones horizontales cubren la escala de forma uniforme y las verticales son individuales, con bordes suavemente irregulares, tamaños variados y una deambulación pequeña. Las semillas deterministas mantienen las posiciones al renderizar de nuevo el mismo resultado. Los porcentajes siguen definiendo el límite entre puntos intensos y tenues.

El pulso del mapa mantiene una fase acumulada continua, con un ciclo de aproximadamente 3,1 segundos durante la carga y entrada/salida de intensidad progresivas. Los círculos se dibujan en lotes reutilizables por color y opacidad; el halo suave se reserva para una de cada doce partículas. El reloj del pulso limita el avance tras una pausa para evitar saltos al recuperar la pestaña. Los cálculos de trayectorias se omiten una vez alcanzado el destino.

Durante la carga, un latido común refuerza el tamaño y el brillo de los puntos y los halos, con una expansión suave del mapa de hasta el 3 %. Se conserva el ciclo lento y la fase continua del renderizado por lotes para que el latido sea visible sin acelerarlo.
