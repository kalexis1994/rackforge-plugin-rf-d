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
