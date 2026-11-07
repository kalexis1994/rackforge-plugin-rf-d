# Colas de latencia de RF-D en WASAPI

2026-11-07. El banco ejecutó el núcleo exponencial de recuperación y el
FIR original dentro de la devolución WASAPI de CPAL a 48 kHz. Solicitó
128 frames y registró los tamaños efectivos. La salida fue silenciosa.
El alcance es el núcleo nativo en el banco de devolución del host. La
medida excluye el motor de plugins, el VCO y los contornos.

La salida predeterminada PRO X 2 LIGHTSPEED rechazó la apertura y sus reintentos con
AUDCLNT_E_DEVICE_IN_USE. Se midió primero Steam Streaming Speakers y
después la salida física LS27AG55x por NVIDIA High Definition Audio.
Ambas registraron Pro Audio y la exención de throttling de RackForge.
El coste de activar esa política queda registrado por separado y
sumarlo a la primera devolución mantiene el plazo en cada banco.
[Protocolo](RECOVERY_HOST_PROTOCOLO.md).

| Banco principal | Llamadas | Frames efectivos | Mediana de procesamiento | Peor fracción del plazo | Incumplimientos | Intervalos >1.5 plazos |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Nativo sin reloj de audio | 4800 | 128 | 0.684 ms | 50.71 % | 0 | — |
| Steam WASAPI con DSP | 4800 | 480 × 3980, 960 × 819, 1056 × 1 | 2.886 ms | 45.04 % | 0 | 572 |
| Steam WASAPI silencioso | 4800 | 480 × 3870, 960 × 929, 1056 × 1 | 0.003 ms | 0.21 % | 0 | 673 |
| Monitor físico WASAPI con DSP | 4800 | 480 × 4799, 1056 × 1 | 3.786 ms | 40.97 % | 0 | 0 |

Las dos confirmaciones WASAPI con DSP pasan el objetivo de procesamiento
del 50 % por devolución. Los bancos cortos de 1200 también pasan y
registran cero intervalos largos. El mayor tramo DSP de 128 frames
costó 1.601 ms en Steam y 1.189 ms en el monitor. Esos tramos comparten
una devolución de más frames y su reloj de llegada corresponde a esa
devolución. El máximo absoluto de una devolución fue 8.144 ms en Steam
y 8.069 ms en el monitor.

## Separar procesamiento e intervalos

En los 572 intervalos largos de Steam con DSP, el procesamiento de la
devolución anterior había terminado dentro de su plazo. El mayor
intervalo fue 19.928 ms para una llegada de 480 frames. De ese intervalo,
5.513 ms corresponden al procesamiento anterior medido y 14.415 ms
quedan fuera de esa sección. El control Steam de igual longitud
reproduce los intervalos largos sin ejecutar DSP. Su máximo fue
19.970 ms. En ambos bancos, el tiempo total entre inicios y la duración
nominal de los frames difieren en menos de 1.1 ms. El conteo mide
irregularidad de llegada y no permite contar pérdidas del dispositivo.

La calibración separó una espera sintética y trabajo activo de unos
4 ms. Registraron medianas de 22 200 y 14 788 160 ciclos. El contador
incluye trabajo de usuario y kernel en el mismo hilo. Los ciclos se
comparan por tamaño efectivo y se conservan en sus unidades originales.
[Documentación de QueryThreadCycleTime](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime).

El nativo de 128 frames superó el margen de 1.333 ms una vez, con un
máximo de 1.352 ms. Ese bloque quedó por debajo del P99 de ciclos de
4799 bloques comparables y mostró procesadores distintos al inicio y
al final. El replay superó el margen tres veces y tuvo un máximo de
2.085 ms. En el mayor pico del replay también aumentaron los ciclos
respecto al P99 comparable. Los tres bancos nativos registrados
cumplieron el plazo de 2.667 ms. El pico de 4.800 ms de 12189ab sólo
tiene tiempo de pared y su causa sigue abierta.

## Alcance y evidencia

La campaña física verifica procesamiento con 480 frames efectivos en
4799 de 4800 devoluciones. La admisión de 128 frames en host y de la
voz completa sigue pendiente. El banco valida 1536 muestras J7 contra
el candidato previo y 464 frames del FIR por bits con particiones
distintas. Conserva las filas de tiempo, el arranque, los bancos
rechazados y sus replays. El enlace MSVC inicial falló por la ruta de
una biblioteca de importación. La corrección y los intentos de
apertura quedan registrados.

[Banco Steam y nativo](../evidence/recovery_host_native02.json),
[banco físico](../evidence/recovery_host_native03.json),
[control Steam largo](../evidence/recovery_host_native04.json) y
[auditoría](../evidence/recovery_host_tests01.json).
