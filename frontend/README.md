# Pulso — frontend de demostración

Prototipo independiente, sin dependencias, de un chat visual para explorar una sociedad española simulada. No usa el CSV del repositorio, modelos, servicios externos ni APIs. Las respuestas y las personas son ficticias, no estimaciones sociales válidas. Los temas reconocidos adaptan sus patrones ilustrativos; las preguntas restantes usan un patrón aleatorio reproducible.

Desde la raíz del repositorio:

```powershell
python -m http.server 5173 --bind 127.0.0.1 --directory frontend
```

Abre http://127.0.0.1:5173. También puedes abrir `frontend/index.html` directamente.

- Escribe una pregunta o elige una sugerencia. Enter envía; Mayús+Enter añade una línea.
- La esfera se reorganiza por sexo, edad o ambos. Cada punto representa una persona; el rojo brillante indica preocupación. El porcentaje se calcula dentro de cada grupo y los resultados se agregan a partir de las mismas personas dibujadas.
- Puedes cambiar entre 1.200, 2.400 y 4.800 personas, repetir la transición y exportar el resultado agregado a JSON.
- Las últimas ocho preguntas se guardan en localStorage. El diálogo «Demo · datos simulados» permite borrarlas.
- Diseño adaptable, controles con teclado y respeto de movimiento reducido. Movimiento continuo con interpolación según el tiempo entre fotogramas, deriva orgánica dentro de los grupos y transiciones de brillo. Canvas se pausa cuando la pestaña está oculta; los halos están precalculados para reducir el trabajo por fotograma. Cambiar la muestra conserva la posición de las personas existentes.

Integración futura: sustituir `applySimulation()` por una fuente validada y mantener el contrato de personas y grupos. La distribución de esta demo es ilustrativa. Para agregar la población real del repositorio hay que aplicar `peso_poblacional`, según el README principal. Las etiquetas actuales de demo deben conservarse hasta disponer de un modelo validado.
