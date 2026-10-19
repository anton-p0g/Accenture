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
