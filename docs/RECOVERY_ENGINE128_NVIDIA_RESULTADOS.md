# Confirmación física a 128 frames en NVIDIA

2026-11-07. El control silencioso y los dos pases físicos
de 4800 callbacks pasaron en la CPU lógica 9, con espera
por evento, ASIO4ALL y la salida `High Definition Audio 1/2`.
Las aperturas confirmaron 48 kHz, avance de reloj de 128
muestras y alternancia de búfer. Cada apertura exigió
cuatro ventanas de 250 ms con 85 % de inactividad global
y 95 % de ciclos ociosos relativos en el par SMT 8/9.
[Protocolo](RECOVERY_ENGINE128_NVIDIA_PROTOCOLO.md),
[confirmación física](../evidence/recovery_engine128_smt18.json)

| Banco | Callbacks | Mediana (ms) | P99 (ms) | Máximo (ms) | Primero con preparación (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Control silencioso | 1200 | 0,0036 | 0,0072 | 0,0369 | 0,0764 |
| Confirmación 1 | 4800 | 0,8195 | 1,0295 | 1,3171 | 0,9020 |
| Confirmación 2 | 4800 | 0,8206 | 0,9514 | 1,2395 | 0,8858 |

Los dos pases tuvieron cero bloques sobre 1,333333… ms,
plazos perdidos, intervalos de más de 1,5 períodos, avisos,
errores, asignaciones de render y fallos de slot. La
holgura mínima frente al margen fue 16,2 µs. La admisión
corresponde al banco de laboratorio con esta afinidad y
preselección. El VCO y los contornos quedan fuera de la
ruta medida.

## Controles de aislamiento

La espera por evento eliminó el despertar del supervisor
cada 5 ms. Con selección automática de CPU quedaron cinco
y un bloques sobre margen. Con CPU 8 fija, la condición
previa global de 90 % no se sostuvo cuatro ventanas con
el mínimo exigido en el par. El control y ambos pases
se rechazaron antes de crear los búferes.
[Espera por evento](../evidence/recovery_engine128_smt13.json),
[preselección a 90 %](../evidence/recovery_engine128_smt14.json)

Al volver al 85 % global con CPU 8 fija y 95 % en el par,
cada campaña tuvo un pase válido y otro sobre margen.
Los máximos fueron 1,3360 y 1,2190 ms en la primera, y
1,4296 y 1,2814 ms en el replay. Un pase DSP previo pasó
por sí solo, seguido de picos de 1,3579 y 3,4217 ms en
las confirmaciones. El último perdió dos plazos.
[CPU 8](../evidence/recovery_engine128_smt15.json),
[replay](../evidence/recovery_engine128_smt16.json),
[pase previo](../evidence/recovery_engine128_smt17.json)

El contraste sin ASIO, fijado a CPU 8, también presentó
picos sobre 1,333 ms. En la campaña de CPU 9, el bloque
3844 del replay histórico bajó de 3,8926 ms dentro del
render a 0,8351 ms al repetir ese ordinal sin ASIO.
Los picos no se repitieron de forma sistemática en los
mismos ordinales del mismo paquete. La comparación mide
tiempo de pared en el render e incluye interrupciones
del hilo. Los contadores por CPU consultados fuera del
stream orientaron la elección de CPU 9. La causa de una
interrupción individual quedó sin atribuir.
[Repetición por ordinal](../evidence/recovery_engine128_smt18.json),
[diagnóstico previo de WPR](../evidence/recovery_engine128_schedule03.json)

## Integridad

Los paquetes O3 coincidieron por hash con sus referencias
y los 2048 frames de prueba se conservaron bit a bit. La
auditoría vinculó el núcleo a las tres reservas eléctricas
y al FIR exacto de 9288 frames. Conservó los dos rechazos
de compilación del capturador y sus replays. Al terminar,
ASIO4ALL volvió a 44,1 kHz y al valor de búfer original.
Las dos consultas finales volvieron a enumerar el par
NVIDIA. Se retiraron binarios y cachés del área temporal.
[Reservas](../evidence/recovery_engine128_reserve07.json),
[FIR](../evidence/recovery_engine128_broadcast_fir07.json),
[salida final](../evidence/recovery_engine128_endpoint07.json),
[auditoría](../evidence/recovery_engine128_nvidia_tests01.json)
