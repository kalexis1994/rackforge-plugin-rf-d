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

Como segundo predictor, derivar la interpolación
cuadrática de Radau en el extremo del paso
anterior. En incrementos, la derivada por
ancho es 2,5 veces el segundo incremento menos
4,5 veces el primero. Proyectar sólo al mismo
KEY y a un ancho nuevo de hasta el doble.
El predictor afecta al contorno y al BUS.
Volver a la semilla anterior sin extrapolar
si el solve falla. Mantener los gates de
residuo y corrección, el calendario y la
partición 64/128. Ninguna etapa provisional
altera la historia aceptada.

El Jacobiano de los seis puertos de audio del
último paso aceptado puede dirigir una iteración
con el mismo KEY y ancho. Sólo se usa mientras
el residuo acoplado supera 1 pA. La búsqueda
prueba la disminución con la respuesta no lineal
actual. Si falla, la misma iteración se resuelve
con la derivada de audio actual. La aceptación
siempre vuelve a calcular esa derivada con las
108 leyes y comprueba la corrección de 2 nV.
El perfil separa las llamadas a la raíz y a
su derivada y suma ambas duraciones como audio.

## Reloj por comparación de un paso y dos medios

Ensayar un techo de 1.024 ticks. Para un paso de
más de ocho ticks, comparar el extremo acoplado
con dos medios pasos desde la misma historia.
Exigir una diferencia máxima de 0,05 del
límite nodal, de retorno y de fase. Publicar el
paso completo si pasa y permitir duplicarlo
por debajo de 0,05/16. Estos factores son del
control de paso local. La admisión sigue
requiriendo la trayectoria completa del solver.

Reducir al cambiar el orden de cualquier par
de colectores en cualquiera de las etapas
comprobadas. Los pasos de ocho ticks o menos
pueden registrar el evento y proponer crecer.
Contar los solves de comparación, los
rechazos y los pasos publicados. Conservar
los límites eléctricos y la partición 64/128.

Reutilizar el primer medio paso ya resuelto
cuando el candidato se rechaza y el ancho se
reduce a la mitad. La reutilización ocurre
dentro de la misma historia, KEY y tick de
inicio. El candidato sigue pasando el mismo
control al nuevo ancho. Registrar cada
reutilización por separado.

Probar también un techo de 4.096 ticks
con trece mapas diádicos, sin cruzar el
límite de una muestra ni cambiar el
control de error o de evento. Sólo llevar
al slot el reloj que haya pasado la
reserva nativa sin instrumentación.

En el primer ensayo con techo de una muestra,
el error nodal positivo excedió el límite
en el tramo de audio antes del cruce. Para
la siguiente prueba, conservar 0,05 hasta
1.024 ticks y dividir esa fracción por cada
duplicación adicional del ancho. Comprobar
el crecimiento con el límite del ancho
propuesto. Los límites de aceptación final
y el guard de colectores permanecen.

## Reutilización del segundo medio paso

Al rechazar un candidato, conservar los dos
medios pasos resueltos. El primero se somete
al mismo control al nuevo ancho. Su compañero
sólo puede sustituir el candidato siguiente
si se publica exactamente ese primer medio
paso y el siguiente ancho coincide. La caché
se limita a una muestra con KEY fijo. Si el
primer medio paso se subdivide, su compañero
pierde el origen y se descarta. Exigir la
misma trayectoria por bits y contar por
separado cada resolución evitada.

Para iniciar cada medio paso, reconstruir
las dos etapas de Radau del candidato amplio
a partir de su extremo y su derivada final.
Evaluar la interpolación cuadrática en 1/6
y 1/2 del intervalo para el primer medio paso
y en 2/3 y 1 para el segundo. Restar el estado
real de inicio de cada medio paso. Usar esta
estimación sólo como semilla del contorno y
el BUS. Si falla, volver al predictor normal
y contar ese trabajo. Confirmar ambos medios
pasos con los mismos residuos, correcciones
y control de cruce.

## Factor de audio con columnas compactas

Preparar fuera del callback el máximo
absoluto de cada columna del mapa de
realimentación P. En el solve, multiplicarlo
por la pendiente absoluta para seleccionar
las mismas columnas fuertes del umbral
5e−4. Armar sólo esas columnas para el
precondicionador. Calcular el residuo completo
como rhs − x − P·(pendiente·x). La prueba
conserva sus límites y las 108 leyes. Armar
la matriz completa sólo si hace falta la
ruta de LU completo. Comparar contra el
solver y medir las mismas ventanas con
el reloj adaptativo.

Resolver juntas las cinco columnas del
contorno y las seis derivadas del audio
para compartir la lectura de filas del LU.
En el audio, agrupar también el producto
por P y el refinamiento. Cada columna que
pasa su residuo deja de actualizarse. Si el
grupo agota las correcciones, usar el LU
completo. La sustitución conserva el orden
de las operaciones por columna. Contrastar
la trayectoria y las dos particiones.

Comparar un orden de eliminación que agrupe
las filas algebraicas de las dos etapas
antes de intercalar las dos filas de cada
nodo dinámico. La permutación se prepara
como tabla constante. Mantener todos los
coeficientes, los pivotes por escala y las
ecuaciones de puerto. Admitir la variante
sólo si pasan las mismas reservas y baja
el coste medido del contorno.

## Prefijo activo del factor de audio

Factorizar y sustituir sólo el prefijo
de columnas fuertes del precondicionador.
Sus filas ya tienen solución del LU.
Reconstruir por producto únicamente las
filas débiles. Conservar la selección de
columnas, el pivoteo y el residuo de las
108 leyes. Comparar el banco por bits y
medir el coste con el mismo calendario.

## Audio del ensayo aceptado por Newton

Conservar la respuesta de audio y del panel
del ensayo que ya pasó el residuo de las
108 leyes y redujo el residuo acoplado.
Consumirla en la siguiente iteración para
el mismo estado inicial, ancho, historial
y tensiones de etapa. Volver a armar el
contorno completo y aplicar los mismos
controles de dirección y convergencia.
La respuesta dura una iteración de una
sola resolución. Comparar las trazas por
bits, los contadores del reloj y las
evaluaciones de audio evitadas.

## Coste de la tangente de audio

Medir por separado las tangentes de seis
columnas dentro del tiempo total de audio.
Comparar la ventana positiva de los frames
74–82 con el mismo banco y calendario.
Conservar las 108 leyes en el residuo, los
umbrales de refinamiento y el respaldo de LU.

Comparar el producto del residuo de tangente
en grupos de cuatro filas. Con AVX, cada
fila usa cuatro carriles AVX y dos SSE.
Mantener la suma en el orden de las leyes
y separar multiplicación y suma. En otros
targets usar el producto escalar existente.

Formar el residuo directamente en los
registros del producto. Conservar el
`expm1` de las junturas convergidas con
la respuesta y derivar la pendiente a
partir de ese mismo valor.

## Coste de la respuesta no lineal

Separar el tiempo de las correcciones
de juntura del resto de la respuesta.
Contar las iteraciones y los retornos
al LU completo en la misma ventana
positiva de los frames 74–82. Mantener
las reservas, los puertos y el reloj.

Empaquetar la matriz de realimentación
en grupos de cuatro filas al preparar
cada banco con AVX. Aplicar el producto
al residuo no lineal y al refinamiento
de una sola columna. Cada carril sigue
el orden escalar y separa multiplicación
y suma. Conservar la matriz original
para el factor y las seis tangentes.
La copia vive fuera del callback y el
formato del banco conserva sus bytes.

Para la corrección de una columna con AVX,
armar sólo el cuadrado de columnas fuertes.
Reconstruir las filas débiles desde las
teselas y la solución fuerte. Preservar
el orden `(P * pendiente) * solución`,
la suma en orden de columna y el refinamiento
con el residuo de las 108 leyes. Para varias
columnas reutilizar el acoplamiento armado.
