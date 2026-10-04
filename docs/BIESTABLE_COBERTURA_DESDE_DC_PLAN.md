# Etapa siguiente: cobertura contigua y anclajes desde DC

Este plan usa el [inventario exacto](BIESTABLE_COBERTURA_METRICAS_RESULTADOS.md).
No declara cerrado el gate de 1 mV ni congela todavía un experimento futuro.
Cada etapa requiere su propio protocolo fijado antes de medir y datos/tests
fijados antes de validar. No cambiar gates o parámetros para facilitar el cierre.

## 1. DC y consistencia al conmutar KEY

- Identificar los estados completos nominales del DC KEY=0 y sus cargas,
  con el grafo, revisión, parámetros sintéticos y precisión ya declarados.
- Obtener un recinto del error algebraico del DC; residual pequeño o dos
  solves iguales no sustituyen una prueba del error respecto al modelo ideal.
- Separar el salto KEY 0→10 V de un intervalo continuo. Especificar qué
  cargas son continuas, qué incógnitas algebraicas pueden saltar y cuáles
  constraints deben satisfacerse después del evento.
- Acotar la consistencia del estado de entrada y su conversión a la norma
  de error, sin asumir anclaje cero por usar un DC fresco.

## 2. Primer tramo continuo desde el evento

- Elegir un prefijo contiguo del reloj publicado, con extremos, todos sus
  soportes y política de reconstrucción declarados; conservar el inventario
  completo de 6.486 intervalos para mostrar lo que permanece descubierto.
- Resolver explícitamente el arranque del interpolante: los primeros pasos
  no tienen cuatro historiales publicados anteriores. No extrapolar el
  soporte de la muestra 31 hacia DC ni inventar historias.
- Cubrir residual continuo, descriptor ideal variable y mapa de salida en
  cada celda del prefijo. Elegir partición y norma antes de medir.
- Propagar un anclaje demostrado con kernels de extremo y pico, incluyendo
  forzamiento tardío. No sustituir un pico interior por el error final.

## 3. Resto no lineal y cierre condicionado

- Derivar el resto en un tubo de error explícito alrededor de la trayectoria
  reconstruida, con dominio de exponenciales y transiciones de juntura.
- Convertir el resto de ecuaciones a contribución nodal mediante el mismo
  descriptor y kernels; una reserva de 0,5 mV no es ese cálculo.
- Probar autoconsistencia del tubo, o conservar el fracaso. La cobertura
  del tangente no cierra por sí sola el error del DAE no lineal.
- Mantener separados el error numérico del modelo sintético y la incertidumbre
  física vintage, que no queda identificada sin una unidad de referencia.

## 4. Extensión hacia ataque, reset y cola

- Extender sólo por regiones contiguas, conservando extremos e identidades
  de los mismos interpolantes. Un extremo con el mismo reloj pero otro
  historial requiere una prueba adicional de cambio de trayectoria.
- Usar una norma común cuando convenga o pagar conversiones certificadas
  en interfaces reales. Los 36 puentes disponibles no propagan los huecos.
- En reset, conservar el crecimiento interno congelado y fijar una norma
  no contractiva para acotar dinámica acoplada, forzamiento y duración.
  No buscar una P favorable por selección posterior de celdas o parámetros.
- Comprobar todos los máximos nodales y los dos niveles de refinamiento.
  Una comparación N2/N4 o una cota local pequeña no prueba toda la trayectoria.

## Salidas exigidas

Un mapa de cobertura contigua con huecos explícitos; anclajes por identidad
y cota; costes de cambio de norma/trayectoria; resto no lineal propagado;
máximo nodal por región y global; rechazos y todos los intentos preservados.
No promover a cálculo nativo/audio hasta cerrar sus gates propios, incluida
la medición de deadline con la voz completa cuando esté implementada.
