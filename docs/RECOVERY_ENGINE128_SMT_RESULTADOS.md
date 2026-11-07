# Política SMT y confirmación ASIO a 128 frames

2026-11-07. El paquete O2 con LTO coincidió byte a byte con el
paquete del banco previo. El motor RackForge `37e5f803` reprodujo
los mismos 2048 frames. El núcleo y el FIR conservaron el vínculo
por hash con las tres reservas eléctricas y con los 9288 frames
del banco de FIR. El driver recibió silencio.
[Protocolo](RECOVERY_ENGINE128_SMT_PROTOCOLO.md),
[reservas](../evidence/recovery_engine128_reserve08.json),
[FIR](../evidence/recovery_engine128_broadcast_fir08.json)

## Control con carga en el hermano SMT

Se inició carga en CPU 9 tras completar el callback 128, con
el render en CPU 8. Con afinidad fija, la mediana tras el
asentamiento fue 1.967 ms, con 1006 de 1008 bloques sobre margen.
Con selección adaptativa, el callback 132 ya corrió en CPU 2.
La mediana asentada bajó a 0.876 ms y quedaron 9 de 1008 bloques
sobre margen. Ambos bancos conservaron el reloj efectivo.

En la segunda confirmación adaptativa, una llamada de afinidad
tomó 1.8047 ms dentro del callback. La política que la mueve al
supervisor registró 70.1 µs como máximo fuera del callback en sus
confirmaciones y mantuvo la CPU solicitada en las observaciones
del render. Bajo la carga controlada de esa campaña, el primer
cambio llegó en el bloque 209. La mediana asentada pasó de
2.051 a 1.470 ms y la cola siguió perdiendo plazos.
El control silencioso de esa campaña tuvo cuatro intervalos
mayores que 1.5 períodos, con un máximo de 0.0245 ms dentro del
callback.
[Afinidad dentro del callback](../evidence/recovery_engine128_smt02.json),
[afinidad desde el supervisor](../evidence/recovery_engine128_smt03.json),
[documentación de afinidad](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadaffinitymask)

## Confirmaciones sin carga inducida

Cada fila corresponde a 4800 callbacks. Todos los pases
registraron pasos de 128 en el reloj de ASIO a 48 kHz. Las dos
últimas filas corresponden a la ruta virtual `Not Connected`.
Tiempos en ms.

| Política | Pase | Mediana | P99 | Máximo | Sobre 1.333 ms | Sobre 2.667 ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Cambio en el callback | Inicial | 0.8686 | 1.3373 | 1.5549 | 51 | 0 |
| Cambio en el callback | Replay | 0.9256 | 1.6325 | 3.7051 | 488 | 42 |
| Afinidad inicial mantenida | Inicial | 0.9211 | 3.4399 | 3.5109 | 860 | 124 |
| Afinidad inicial mantenida | Replay | 1.4398 | 3.5457 | 3.9623 | 3965 | 422 |
| Cambio desde el supervisor | Inicial | 0.9321 | 1.5543 | 3.5679 | 571 | 14 |
| Cambio desde el supervisor | Replay | 0.9492 | 3.4069 | 3.6671 | 769 | 57 |
| Afinidad mantenida, supervisor en núcleo excluido | Inicial | 0.9201 | 1.3926 | 1.5982 | 71 | 0 |
| Afinidad mantenida, supervisor en núcleo excluido | Replay | 0.9041 | 1.3452 | 1.5545 | 52 | 0 |
| Afinidad fija con condición previa | Inicial | 1.0120 | 1.3844 | 1.7523 | 84 | 0 |
| Afinidad fija con condición previa | Replay | 1.0224 | 1.1652 | 1.5097 | 7 | 0 |

La condición previa eligió CPU 8 en el control silencioso y
en los dos pases largos. La peor ventana inicial de la pareja
elegida tuvo el 97.62 % y 92.20 % de los ciclos ociosos del
máximo observado, respectivamente. Los pases largos cumplieron
el plazo del controlador y conservaron cero asignaciones de
render y fallos de slot. ASIO pasó de enumerar ocho salidas a
dos con nombre `Not Connected`. El reloj observado acredita
el período del driver en esa ruta virtual. La confirmación física
exige las salidas HD Audio originales. Las seis consultas
posteriores devolvieron `Not Connected`, por lo que la última
campaña se detuvo antes de abrir el stream. **El margen de
1.333 ms sigue sin confirmarse en dos pases físicos.** El VCO
y los contornos quedan pendientes.
[Pases en la ruta virtual](../evidence/recovery_engine128_smt04.json),
[consultas de las salidas](../evidence/recovery_engine128_smt05.json)

El primer capturador esperaba JSON y recibió tuplas en la
impresión de la topología de inicio. Se guardaron las filas del
fallo y del replay, y se corrigió sólo la lectura para el
siguiente banco. El perfil original de ASIO se restauró y se
retiraron el target, paquetes y cachés temporales.
[Fallo y replay](../evidence/recovery_engine128_smt01.json),
[auditoría](../evidence/recovery_engine128_smt_tests01.json)
