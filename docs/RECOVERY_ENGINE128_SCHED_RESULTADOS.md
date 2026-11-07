# Planificación, SMT y margen de RF-D

2026-11-07. Se conservó el paquete Wasm byte a byte, con el
mismo núcleo y FIR de la campaña anterior. El motor RackForge
`37e5f803` devolvió los mismos 2048 frames de referencia. Los
hashes vinculan el paquete con las tres reservas eléctricas y
la comprobación de 9288 frames del FIR. Las mediciones ASIO
verificaron el reloj de muestras. El driver recibió silencio.
[Protocolo](RECOVERY_ENGINE128_SCHED_PROTOCOLO.md),
[reservas](../evidence/recovery_engine128_reserve07.json),
[FIR](../evidence/recovery_engine128_broadcast_fir07.json)

## Precisión de los relojes

Windows rechazó Windows Performance Recorder con `0xc5585011`.
El reloj de CPU por hilo devolvió incrementos de 0 o 15.625 ms
en la calibración. Marcó cero en 120 de los 128 tramos ocupados
de 0.9 ms del banco aceptado. El contador de ciclos distinguió
esos tramos de las esperas. Se usaron ciclos y pared como
lecturas separadas, sin estimar el tiempo efectivo en CPU por
callback ni inferir cambios de contexto individuales.
[Documentación de QueryThreadCycleTime](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime),
[calibración](../evidence/recovery_engine128_schedule03.json)

El capturador inicial descartaba las filas si la afinidad no
se verificaba. El banco siguiente conservó las filas y repitió
la misma captura. Ambos pases mostraron múltiples CPUs al fijar
la afinidad antes de activar Pro Audio. Aplicarla después
permitió verificar la CPU en cada bloque.
[Primer intento](../evidence/recovery_engine128_schedule01.json),
[replay con filas](../evidence/recovery_engine128_schedule02.json)

## Control del hermano SMT

Windows identificó las CPUs lógicas 4 y 5 como hermanos del
mismo núcleo físico y la 6 como parte de otro núcleo. Fuera de
ASIO, el render con Pro Audio quedó en CPU 4. Un hilo de carga
temporal ejecutó el mismo bucle en CPU 5 o CPU 6. El banco usó
un temporizador al período de 128 frames y alternó el orden
de las cargas. Los tiempos de la tabla están en ms.

| Carga | Medianas de 1200 bloques | Bloques sobre 1.333 ms |
| --- | --- | --- |
| Sin carga introducida | 0.953 / 0.962 | 3 / 5 |
| Hermano SMT | 1.636 / 1.643 | 1178 / 1198 |
| Otro núcleo físico | 0.957 / 0.945 | 18 / 5 |

En los mismos ordinales de entrada, la mediana de la razón de
ciclos fue 1.711 con carga en el hermano y 1.004 con carga en
otro núcleo, respecto al control. El experimento reproduce un
aumento de ciclos dentro del render con el mismo DSP. Demuestra
que compartir el núcleo puede generar picos de esta magnitud.
El banco ASIO usó la política TIME_CRITICAL y las lecturas
disponibles no identifican qué ejecutaba cada hermano durante
sus picos naturales.
[Control SMT](../evidence/recovery_engine128_schedule03.json)

## ASIO a 128 frames efectivos

El control silencioso pasó. Cada fila con DSP corresponde a
4800 callbacks a 48 kHz, con cero plazos perdidos, avisos,
fallos de slot y asignaciones durante el render.

| Postura | Pase | Mediana ms | P99 ms | Máximo ms | Bloques sobre margen |
| --- | --- | ---: | ---: | ---: | ---: |
| Libre | Inicial | 0.8289 | 1.3494 | 1.5737 | 80 |
| CPU 4 | Inicial | 0.8214 | 1.2103 | 1.3751 | 11 |
| CPU 4 | Replay | 0.8142 | 1.1663 | 1.3318 | 0 |
| Libre | Replay | 0.8171 | 1.2350 | 1.4344 | 8 |

El P99 del tiempo de pared fuera del render quedó entre 3.6
y 4.1 µs en los pases con DSP. El peor callback libre duró
1.5737 ms, con 1.5695 ms dentro del render. Su hilo consumió
5.800 millones de ciclos, de los cuales 5.789 millones
ocurrieron dentro del render. La afinidad fija superó el
criterio en un pase y lo falló en el otro.
[ASIO libre y fijo](../evidence/recovery_engine128_schedule03.json)

## Selección y confirmación independiente

La CPU 8 ganó la selección de cinco núcleos con un máximo de
1.1867 ms en 1200 callbacks. Los dos pases largos nuevos usaron
esa CPU. O2 mantuvo el mismo núcleo, LTO y FIR. En WASI, su
reserva volvió a coincidir bit a bit, con la misma fragmentación
de 9288 frames del FIR. Los cuatro pases tuvieron 128 frames
efectivos, cero plazos perdidos, avisos, fallos de slot y
asignaciones durante el render.

| Invitado en CPU 8 | Pase de 4800 | Mediana ms | P99 ms | Máximo ms | Bloques sobre margen |
| --- | --- | ---: | ---: | ---: | ---: |
| O3 | Inicial | 0.8226 | 1.2587 | 1.4798 | 12 |
| O3 | Replay | 0.8154 | 0.9502 | 1.2917 | 0 |
| O2 | Inicial | 0.8565 | 0.9194 | 1.3672 | 3 |
| O2 | Replay | 0.8536 | 0.8975 | 1.3064 | 0 |

**El margen de 1.333 ms queda sin confirmar.** O2 en CPU 8
quedó a 33.9 µs del límite en el peor bloque del primer pase.
El replay cumplió el criterio, con la preparación incluida.
La posición fija se probó sólo en el proceso de laboratorio.
El VCO y los contornos quedan fuera. Se restauró el perfil de
ASIO y se retiraron el target temporal, paquetes y cachés.
[Selección y O3](../evidence/recovery_engine128_schedule04.json),
[O2](../evidence/recovery_engine128_schedule05.json),
[reservas O2](../evidence/recovery_engine128_reserve08.json),
[FIR O2](../evidence/recovery_engine128_broadcast_fir08.json),
[auditoría](../evidence/recovery_engine128_schedule_tests01.json)
