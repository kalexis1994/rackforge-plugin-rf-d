# LU con extensión contigua: reducción de trabajo e identidad

2026-10-13. Voz229 CA3046 condicionada, matriz Radau458×458.
Base de costo y señal: [reuso de Newton](NEWTON_REUSO_RESULTADOS.md).
[Protocolo inicial](LU_SOPORTE_PROTOCOLO.md),
[segunda propuesta](LU_EXTENSION_PROTOCOLO.md) y
[confirmación previa](LU_EXTENSION_CONFIRMACION.md).

## Hipótesis comparadas

La lista indexada de coeficientes no nulos pasa84 pares por bits, pero
su mediana total es1.002914× y el rango
0.958849–1.095523×.
No se elige para el recorrido. Se conservan código y
[recibos](../evidence/voice_lu_support_bench_native01.json).

La propuesta elegida reconstruye la última columna no nula de cada
pivote después de su intercambio. Recorre col+1..end de forma contigua
y separa filas con split_at_mut/zip. El fill-in se observa en la matriz
actual, sin patrón fijo ni umbral para descartar coeficientes pequeños.
Mantiene escalas, selección de pivote, umbral1e-12, factor, RHS y
sustitución hacia atrás. Sin unsafe, heap nuevo o modificación física.
El reuso del trial sigue vigente; no se cambian Newton, h ni tolerancias.

## Benchmark pareado y confirmación

84 pares: coarse/mid/end de ON/OFF y h2/1 µs, incluyendo gatillo/reset.
Warmup separado y cinco rondas alternadas en cada proceso. Candidatos,
incrementos, ratios, iteraciones y trials coinciden por bits con el kernel
de reuso y datos originales. La primera medición tuvo variación del wall
de referencia; se repitió el mismo ejecutable/packet, sin cambiar código.

| Ronda | Primera medición | Confirmación |
|---|---:|---:|
| 1 | 1.074384× | 1.166507× |
| 2 | 0.990491× | 1.063692× |
| 3 | 1.239462× | 1.090330× |
| 4 | 1.081102× | 1.155175× |
| 5 | 1.203894× | 1.090756× |

Medianas de cocientes:1.081102× y
**1.090756×**. La confirmación mejora
en las cinco rondas. Misma cantidad de ensamblados/solves:460/396 por
ronda,384 iteraciones y376 trials. El ahorro está dentro del solve.
[Benchmark](../evidence/voice_lu_extent_bench_native01.json) y
[confirmación](../evidence/voice_lu_extent_confirmation01.json).
No se atribuye rendimiento universal o precisión de deadline a estos datos.

## Regresiones y conteo separado

[Diagnóstico](../evidence/voice_lu_extent_diagnostic01.json): ocho sistemas
8×8 contrastados por bits/rechazo, con diagonal, permutación de pivotes,
fill-in, coeficientes1e-200, fila cero, filas dependientes, cero con signo
e infinito. No es una prueba universal de aritmética IEEE o matrices finitas.

84 pares contrastados otra vez en una fase separada del timing:
1056568152→658065345 actualizaciones
de coeficientes durante la eliminación, reducción37.7167%.
Los contadores de actualizaciones no están en los kernels del benchmark
pareado ni del runner. La instrumentación de tiempos/calls sólo pertenece
al benchmark, y no cambia la matriz física.

## Cuatro recorridos completos

Mismos seeds propios y calendario de3.004 ms, mismos contactos y cargas.
40 archivos/20630344 bytes
coinciden con newton-reuse01: OBS, STEP/LTE/intentos, corrientes, ledgers,
raíces guardadas, checkpoints y rechazos inducidos.
26770 finos,24 restores de prefijos,368 avances repetidos,16 corrupciones
y8 rollbacks. Campos no guardados en cada endpoint no reciben cobertura
por esa comparación. Los84 pares sí contrastan todo HIGH/LOW de sus etapas.

| Final decay | h máximo µs | Wall actual s | Wall histórico s |
|---|---:|---:|---:|
| ON | 2 | 142.775772 | 163.644395 |
| ON | 1 | 160.566313 | 174.586811 |
| OFF | 2 | 139.335813 | 154.943690 |
| OFF | 1 | 163.664735 | 176.607265 |

Los tiempos históricos no son benchmark pareado. Campaña607.773525 s;
26265170 bytes privados nuevos bajo64 MiB/reserva1 GiB.
[Auditor](../evidence/voice_lu_extent_reference01.json) y
[QA](../evidence/voice_lu_extent_tests01.json).38472 ecuaciones independientes
heredadas por identidad de datos, no reejecutadas;248 tests Rust heredados.
Sin nueva biblioteca, SPICE, duración simulada o audio.

## Siguiente bloque

La reducción de trabajo tiene ganancia moderada con identidad de señal
en el banco. Para llegar a duración musical, abordar una reducción mayor:
condensar bloques del sistema dinámico conservando sus puertos y masa,
contra esta referencia. Mantener explícitos errores de redondeo, cargas
y dominio temporal. Contorno desde silencio, otras cargas de placa2,
contorno de filtro, identificación física y admisión RT siguen pendientes.
