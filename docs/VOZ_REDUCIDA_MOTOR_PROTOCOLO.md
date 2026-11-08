# Motor de audio para la voz con contornos cargados

Trasladar el híbrido validado al motor Rust y
mantener sus dos contornos no lineales, los seis
puertos Radau y las junturas de audio retenidas.
Preparar el bloque lineal de audio al inicio de
cada escena. Los mapas de historia, tensión de
juntura, reacciones y reconstrucción se calculan
para cada uno de los ocho tamaños diádicos antes
de procesar audio. El estado dinámico conserva la
memoria de carga de audio y los contornos y la
fase H128. Usar los mismos retornos de 68 kΩ y
680 Ω y la misma excitación KEY de cada reserva.
[Modelo reducido](VOZ_REDUCIDA_CONTORNOS_PROTOCOLO.md)

Probar el reloj de 4096 ticks por muestra a
48 kHz. Empezar con techo de 32 subpasos en la
rama negativa y 64 en la positiva. Dividir un
paso grueso ante cambio de orden de colectores
en cualquiera de las etapas o movimiento superior
a VT/32. Permitir crecer bajo VT/128. La referencia
para la conmutación usa intervalos de hasta
ocho ticks. Los rechazos no confirman la historia.
[Reloj del solver de referencia](VCO_FAMILIA_BUS_VOZ_RELOJ_PROTOCOLO.md)

Contrastar 128 muestras continuas de las dos
reservas contra la rejilla fina archivada del
solver. Usar 20 µV + 2e−6·|V| por nodo y 2 nA
+ 2e−5·|I| por retorno. Exigir el mismo calendario,
error de fase máximo de 1e−7 ciclos, y para J7
RMS relativo de 0,1 %, pico relativo de 0,3 % y
error medio de 1 µV. Comprobar que partir 128 en
dos bloques de 64 conserva exactamente estados,
corrientes, fase y eventos. Comprobar rechazo
atómico y cero asignaciones en la entrada de audio.

Medir el bloque nativo completo por separado del
cotejo eléctrico. El margen objetivo es 1,333 ms
a 48 kHz y 128 frames efectivos. El banco nativo
sirve para decidir si el motor está en condiciones
de pasar a RackForge con el mismo modelo y reloj.
Un pase de software no sustituye la medición del
callback y la salida física.

## Paso por RackForge

Cargar un paquete nativo temporal con los mismos
bancos de coeficientes, las dos reservas como
presets y el mismo motor Rust. Medir dos pases
de 128 frames por reserva en un slot del motor
de RackForge, con el mezclador a nivel unidad
y paneo central. Contrastar sus dos canales con
J7 del banco nativo convertido a f32. Registrar
el tiempo de pared, telemetría, fallos y margen.
Medir fuera de ASIO mientras el render supera
el presupuesto. La sesión física requiere un
motor capaz de sostener el periodo.

## Dirección de audio y techo de reloj

El precondicionador usa hasta 56 columnas del
Jacobiano de audio. Cada columna se mide por
su mayor magnitud en el producto entre mapa y
pendiente. Tomar las que superan 5e−4. Comprobar
cada dirección contra las 108 filas y columnas,
con residuo de hasta 1e−14 + 2e−13 por la
magnitud del lado derecho. Si la proyección o
el refinamiento no cumplen, resolver el LU
completo. Se aplican los mismos límites
eléctricos y de partición al render.

El banco nativo admite un ensayo aparte con
techo de 1.024 ticks y once mapas diádicos.
Se conservan el guard de colectores, los ocho
ticks para el cruce y todos los límites. El
slot de RackForge conserva por ahora el banco
de ocho mapas. La opción experimental mide
cuánto coste se puede evitar lejos de un
cruce y si el reloj ampliado mantiene la
trayectoria bajo los mismos límites.

En una segunda variante del reloj ampliado,
comparar la primera etapa con la interpolación
lineal al tercio del paso. Medir la diferencia
en cada nodo con carga y en el sustain de volumen.
Subdividir por encima de 2 µV y crecer sólo por
debajo de 0,5 µV y del límite de movimiento.
Esta diferencia decide el reloj, y el contraste
contra la referencia decide la admisión.

## Perfil de cruce y semilla de audio

El perfil instrumentado separa el armado de
contornos, la respuesta de audio y la dirección
del solve acoplado. Sumar por ventanas de frames
0–73, 74–82 y 83–127. Incluir intentos rechazados
en el tiempo del paso. Excluir este binario del
banco de tiempo de RackForge.

La raíz de audio de un intento aceptado puede
servir de semilla para la siguiente evaluación
del mismo paso. Entre pasos, usar las 54
tensiones de juntura de la etapa final de la
historia aceptada para iniciar ambas etapas.
El anclaje de los mapas es común. Inicializar en
cero y volver a la semilla afín si falla la
convergencia. Las 108 leyes, el Jacobiano y los
límites permanecen. Publicar la semilla junto al
estado sólo después de aceptar el paso y el bloque.
