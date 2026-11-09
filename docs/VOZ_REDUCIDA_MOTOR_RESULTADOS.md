# Motor Rust y reloj de la voz cargada

El motor ahora renderiza la voz acoplada con
bloques de hasta 128 muestras. Conserva el H128,
los dos contornos, la memoria de carga y las
junturas de audio validadas, incluida la salida.
Los mapas del tramo de audio se preparan fuera
del render. En las pruebas no hubo asignaciones
durante el bloque y un rechazo de entrada
preservó el estado y la salida.
[Protocolo](VOZ_REDUCIDA_MOTOR_PROTOCOLO.md)

| Reserva | Pasos aceptados | Error nodal máximo | Error máximo en J7 | Tiempo nativo a 128 |
| --- | ---: | ---: | ---: | ---: |
| Negativa | 4.096 | 1,21 nV | 2,98 fV | 10,08 s |
| Positiva | 10.997 | 7,82 µV | 34,94 pV | 37,81 s |

Ambas reservas completaron 128 muestras contra
la rejilla fina. Dividir el render en dos bloques
de 64 reprodujo estados, corrientes, fase y
eventos por bits. En la positiva, la inversión
de volumen ocurrió en 319096–319104, sin inversión
adicional del filtro. El mayor error de R59 fue
2,81e−17 A y el de R60 fue 2,51e−14 A. J7 pasó
los límites de RMS, pico y media de ambas reservas.

El primer binario completó el bloque negativo,
pero el adaptador rechazó el formato del campo de
residual. El recibo preserva sus estados y salida.
La segunda corrida corrigió el formato y completó
la campaña. [Primer recibo](../evidence/rf_d_reduced_engine01.json),
[validación del motor y reloj](../evidence/rf_d_reduced_engine02.json)

## Slot nativo de RackForge

Se cargó el mismo motor como paquete nativo
temporal en el núcleo RackForge `7a14c68a`. Las
reservas usan presets de prueba con H128 fijo y
entregan J7 directamente en voltios. El slot y
mezclador devolvieron exactamente la salida
nativa convertida a f32 en ambos canales.

| Reserva | Pase 1 a 128 frames | Pase 2 a 128 frames |
| --- | ---: | ---: |
| Negativa | 10,576 s | 10,513 s |
| Positiva | 35,950 s | 36,349 s |

Cada pase registró un vencimiento de plazo y
cero fallos del slot. El máximo positivo quedó
a unas 27.262 veces el margen de 1,333 ms. Este
reloj hace 10.997 pasos en la reserva positiva.
Para sostener el margen, el promedio disponible
sería de unos 121 ns por paso, incluyendo el
resto del bloque. La prueba mide el motor y
mezclador fuera de ASIO. La salida física sigue
pendiente mientras el motor exceda el plazo.
[Dos pases por reserva](../evidence/rf_d_reduced_engine_rack01.json)

## Contornos cerrados en el render acoplado

El motor de la reserva nominal vuelve a resolver
los dos contornos en cada etapa. C2/C5, ambos
sustain y las ramas de reset del filtro son
incógnitas internas. KEY y el estado inicial son
los estímulos del banco. R59/R60 se cierran con
las reacciones del tramo de audio, y el orden
de colectores del estado resultante determina
los cruces de ambos biestables.

Se ordenaron las filas algebraicas antes de las
filas con carga en cada etapa. Se acotó el tramo
inicial nulo de la sustitución triangular. Para
el Jacobiano de audio se probó una serie corta
cuando la norma de su realimentación permite
acotar el error de la dirección, con retorno al
LU completo en los demás casos.

El banco de 128 muestras reprodujo 319096–319104
con 7,82 µV de error nodal máximo. Los errores de
R59/R60 quedaron en 2,81e−17 A y 2,51e−14 A.
J7 pasó sus límites y la partición 64/128 volvió
a ser idéntica por bits. Los dos pases positivos
en el slot de RackForge reprodujeron J7 nativo
en f32 y tardaron 37,524 s y 38,069 s. Los dos
negativos tardaron 10,668 s y 10,832 s.
La serie corta no produjo una mejora de tiempo
demostrable. Estos pases fueron offline. El
presupuesto aún impide abrir la campaña física.
[Banco acoplado](../evidence/rf_d_reduced_engine03.json),
[dos pases por reserva](../evidence/rf_d_reduced_engine_rack02.json)

## Precondicionador de audio y reloj ampliado

La primera compilación del precondicionador
conservó una llamada anterior y quedó registrada
como fallo de integración. Tras corregirla, el
precondicionador de 56 columnas y el residuo de
108 conservaron ambos contrastes, el cruce de
ocho ticks y la identidad por partición. En
nativo, el bloque negativo bajó de 11,05 s a
5,22 s y el positivo de 37,78 s a 21,81 s.
Se conservaron los mismos 4.096 y 10.997 pasos
aceptados.
[Compilación rechazada](../evidence/rf_d_reduced_engine04.json),
[precondicionador contrastado](../evidence/rf_d_reduced_engine05.json)

El techo de 1.024 ticks completó la reserva
negativa en 512 pasos y 0,686 s. En la positiva
coincidió el cruce y se mantuvieron los límites
de retornos y J7, con 40,95 µV de error en el
nodo de reset x16 a la muestra 78. El criterio
de curvatura tampoco pasó el límite nodal
positivo. En el slot se mantuvieron los techos
de 32 y 64 subpasos por muestra.
[Reloj ampliado](../evidence/rf_d_reduced_engine06.json),
[ensayo de curvatura](../evidence/rf_d_reduced_engine07.json)

| Reserva acoplada | RackForge offline, pase 1 | RackForge offline, pase 2 |
| --- | ---: | ---: |
| Negativa | 4,591 s | 4,817 s |
| Positiva | 19,382 s | 18,961 s |

Los cuatro bloques de 128 frames devolvieron
J7 idéntico al banco nativo en f32 y excedieron
el plazo. El render incluye ambos biestables y
sus cargas de contorno. El margen de 1,333 ms
sigue pendiente y estos pases no abrieron ASIO.
[Slot con precondicionador](../evidence/rf_d_reduced_engine_rack03.json)

## Perfil de la transición y semilla de audio

En los frames 74–82, el tramo de audio tomó
3,001 de 3,827 s del banco positivo instrumentado.
En esa ventana hubo 2.340 pasos aceptados y
2.014 de ocho ticks o menos. El lector inicial
exigió el mismo número de llamadas de armado y
audio. La traza conserva siete candidatos que
terminaron antes de entrar al tramo de audio.
El lector corregido recuperó el contraste con
el mismo estado y los mismos límites.
[Perfil original](../evidence/rf_d_reduced_engine08.json)

Al reutilizar las raíces de juntura como
semillas, la ventana bajó a 2,518 s y el audio
dentro de ella a 1,361 s. El bloque positivo
completo bajó de 18,656 s a 13,260 s en los
bancos instrumentados. Se conservaron el reloj,
el cruce, las corrientes R59/R60, J7 y la
identidad de la partición. El error nodal
máximo siguió en 7,82 µV. La semilla acompaña
el estado aceptado y el render registró cero
asignaciones.
[Reutilización contrastada](../evidence/rf_d_reduced_engine09.json)

La extrapolación desde la última etapa aceptada
redujo las iteraciones positivas de 33.236 a
22.348 con los mismos 10.997 pasos. En los
frames 74–82 redujo las direcciones calculadas
de 7.093 a 4.811 y el tiempo de 2,518 s a 1,591 s.
El banco sin instrumentar completó 128 frames
en 7,244 s en la reserva positiva y 2,393 s
en la negativa. Conservó los mismos ocho ticks
de cruce, el error nodal de 7,82 µV, los límites
de R59/R60 y J7 y la identidad 64/128. Ambos
bloques exceden el presupuesto físico.
[Perfil de la extrapolación](../evidence/rf_d_reduced_engine10.json),
[banco sin instrumentar](../evidence/rf_d_reduced_engine11.json)

## Jacobiano de audio reutilizado durante la búsqueda

Recalcular la derivada de audio al aceptar
cada paso conservó el calendario y los límites.
En los frames 74–82 se calcularon 2.359
derivadas de audio, frente a 4.811 en el banco
anterior. El tiempo de la ventana bajó a
1,282 s y el bloque positivo instrumentado a
6,063 s. Se conservaron los 10.997 pasos y el
cruce 319096–319104.

El banco nativo sin instrumentar tardó
6,697 s para 128 frames en la reserva positiva.
Los máximos fueron 7,82 µV por nodo,
2,82e−17 A en R59 y 2,52e−14 A en R60.
La salida J7 y la partición 64/128
pasaron sus gates. Se registraron cero
asignaciones durante el render.
[Perfil y derivadas](../evidence/rf_d_reduced_engine12.json),
[reserva sin instrumentar](../evidence/rf_d_reduced_engine13.json)

| Reserva | RackForge offline, pase 1 | RackForge offline, pase 2 |
| --- | ---: | ---: |
| Negativa | 2,248 s | 2,239 s |
| Positiva | 6,814 s | 6,848 s |

Cada bloque tuvo 128 frames y coincidió por
bits con el banco nativo convertido a f32.
El plazo de 1,333 ms sigue fuera del coste
del bloque. La campaña física sigue pendiente.
[Slot de RackForge](../evidence/rf_d_reduced_engine_rack04.json)

## Reloj adaptativo por refinamiento local

La comparación entre un paso y dos medios
redujo la reserva positiva de 10.997 a 712
pasos publicados. El trabajo total, incluidos
los medios pasos y los rechazos, fue de
2.165 solves. En los frames 74–82 se pasó
de 2.340 a 152 pasos publicados y de 2.014
a 34 pasos de ocho ticks o menos. El perfil
de la ventana bajó de 1,282 s a 0,388 s y el
bloque positivo de 128 frames tomó 1,901 s.

El cruce quedó en 319096–319104. El error
máximo fue de 15,05 µV por nodo, 3,23 fA
en R59 y 0,644 pA en R60. J7 y ambas
particiones volvieron a pasar sus límites.
La reserva negativa publicó 531 pasos y
también conservó la identidad de partición.
[Comparación instrumentada](../evidence/rf_d_reduced_engine14.json)

El primer ensayo de 4.096 ticks publicó
575 pasos en la positiva y conservó los
ocho ticks del cruce. El nodo 76 de audio
superó su límite a la muestra 25 por un
0,72 %. La repetición sin cambios reprodujo
la salida y quedó registrada. Se mantuvieron
los límites finales.
[Ensayo rechazado](../evidence/rf_d_reduced_engine15.json)

Con el control local más estricto para
anchos superiores a 1.024 ticks, la positiva
publicó 654 pasos y realizó 2.035 solves,
con 70 primeros medios pasos reutilizados.
La ventana 74–82 conservó 152 pasos, 34 de
ocho ticks. El cruce siguió en 319096–319104.
Los máximos fueron 15,68 µV por nodo,
3,52 fA en R59 y 0,663 pA en R60. J7 y la
partición 64/128 pasaron. El bloque sin
instrumentación tomó 1,726 s en nativo.
[Perfil del reloj adaptativo](../evidence/rf_d_reduced_engine16.json),
[banco sin instrumentación](../evidence/rf_d_reduced_engine17.json)

| Reserva | RackForge offline, pase 1 | RackForge offline, pase 2 |
| --- | ---: | ---: |
| Negativa | 0,777 s | 0,757 s |
| Positiva | 1,791 s | 1,756 s |

El slot de laboratorio usó el banco de trece
mapas y devolvió J7 idéntico por bits al banco
nativo convertido a f32 en los cuatro pases
de 128 frames. El margen físico de 1,333 ms
sigue fuera del coste actual del bloque.
[Slot con reloj adaptativo](../evidence/rf_d_reduced_engine_rack05.json)

## Auditoría del punto medio reconstruido

Se reconstruyó el punto medio de los 118
nodos, incluidos los dos puertos de retorno,
y se contrastó con el primer medio paso.
El ensayo exigió cuatro veces la discrepancia
normalizada dentro del límite local y 1 mV
de separación de los colectores de cada
biestable en la interpolación de Radau.
El segundo medio paso auditó cada atajo.

Los 25 casos elegibles de la reserva negativa
coincidieron con la comparación completa.
En la positiva hubo una discrepancia entre
183 casos elegibles. El banco eléctrico
terminó con el cruce de ocho ticks gracias
al control completo. La variante queda
rechazada y se retira del motor. El recibo
conserva los dos bloques y las fuentes del
ensayo.
[Auditoría del punto medio](../evidence/rf_d_reduced_engine18.json)

La reutilización del segundo medio paso
eliminó 68 resoluciones en la reserva positiva
y 21 en la negativa. Los totales pasaron de
2.035 a 1.967 y de 937 a 916. Las trazas
eléctricas completas y los eventos fueron
idénticos por bits respecto del banco anterior,
tanto en 128 frames como en dos bloques de 64.
[Banco con reutilización exacta](../evidence/rf_d_reduced_engine19.json)

## Semilla de los medios pasos

La interpolación del paso amplio inició los
medios pasos sin reintentos en las dos reservas.
Junto con la reutilización del segundo medio
paso, redujo las direcciones de Newton en los
frames 74–82 de 1.377 a 1.146. El tiempo
perfilado pasó de 379 ms a 277 ms. Se
conservaron los 654 pasos publicados, los
1.967 solves y el cruce 319096–319104.

El error máximo fue 15,68 µV por nodo, 3,52 fA
en R59 y 0,663 pA en R60. J7 y la partición
64/128 pasaron. El bloque positivo sin
instrumentación tardó 1,426 s. El banco
perfilado y el banco sin instrumentación
coincidieron por bits.
[Perfil de las semillas](../evidence/rf_d_reduced_engine20.json),
[banco nativo](../evidence/rf_d_reduced_engine21.json)

| Reserva | RackForge offline, pase 1 | RackForge offline, pase 2 |
| --- | ---: | ---: |
| Negativa | 0,766 s | 0,700 s |
| Positiva | 1,441 s | 1,438 s |

Los cuatro bloques de 128 frames devolvieron
J7 idéntico al banco nativo convertido a f32.
El presupuesto de 1,333 ms sigue por debajo
del coste medido. La campaña física permanece
pendiente.
[Slot con reutilización y semillas](../evidence/rf_d_reduced_engine_rack06.json)

## Coste por paso con el reloj adaptativo fijo

El factor de audio arma sólo las columnas
fuertes. Los máximos de las columnas se
preparan al cargar el banco y el residuo
sigue usando las 108 leyes. Las trazas de
128 y 64 frames y el reloj coincidieron por
bits con el banco anterior. En el perfil
positivo, el audio de los frames 74–82
bajó de 152,0 a 140,4 ms, con las mismas
1.899 evaluaciones. El bloque positivo
instrumentado tomó 1,325 s.
[Perfil de columnas compactas](../evidence/rf_d_reduced_engine22.json)

La sustitución agrupada conservó la
trayectoria completa por bits y el mismo
calendario. En los frames 74–82 del banco
positivo, el audio bajó de 140,4 a 113,9 ms
y la dirección del contorno de 82,1 a
63,2 ms. La ventana tomó 221,6 ms y el
bloque completo 1,066 s. La primera
compilación requirió declarar explícitamente
el ancho de cinco columnas del contorno.
[Compilación rechazada](../evidence/rf_d_reduced_engine23.json),
[perfil de sustituciones agrupadas](../evidence/rf_d_reduced_engine24.json)
