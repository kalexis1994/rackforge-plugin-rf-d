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
