# Reuso exacto del trial de Newton: costo e identidad de señal

2026-10-12. [Protocolo previo](NEWTON_REUSO_PROTOCOLO.md). Voz229 CA3046
condicionada del [ciclo con contorno](VOZ_CONTORNO_CICLO_RESULTADOS.md),
sin instrumento físico. Esta optimización conserva el circuito y la duración.

## Cambio numérico

La búsqueda de línea ya construye el stamp y resuelve la corrección del
candidato que acepta. La siguiente iteración los recalculaba con idénticos
parámetros, historia, delta y h. El nuevo kernel conserva ambos resultados
dentro de ese mismo step; no reutiliza una matriz de otro estado ni
congela tangentes del dispositivo. Misma primera evaluación, predictor,
orden de operaciones, criterio de parada, 64 iteraciones y 24 halvings.
Un trial aceptado en la iteración64 sigue sin ampliar el budget.

Se conserva el kernel histórico. El caller y controlador sólo cambian su
binding al kernel con reuso. La caché tiene alcance local, arrays propios
y ninguna invalidación entre pasos. No cambia h, masa, fuentes o memoria.
Los errores inducidos del caller y sus rollbacks conservan sus bytes.

## Benchmark pareado

[84 pares congelados](../evidence/newton_reuse_inputs01.json), extraídos de
coarse/mid/end de cuatro perfiles, incluyendo gatillo y reset. Se comparan
por bits 1.834 componentes por par: HIGH/LOW de candidatos/incrementos y
ratios; también iteraciones y trials. Los candidatos coinciden con el
archivo original y con el kernel de referencia en warmup y las cinco rondas.
Mismo proceso/compilador GNU y opt2, stack32 MiB, orden alternado por ronda.
La instrumentación usa timers/contadores sólo en esta herramienta de laboratorio.

| Ronda | Referencia s | Reuso s | Aceleración pareada |
|---|---:|---:|---:|
| 1 | 2.425357 | 1.452883 | 1.669341× |
| 2 | 2.422057 | 1.496666 | 1.618302× |
| 3 | 2.410098 | 1.440428 | 1.673182× |
| 4 | 2.385259 | 1.420231 | 1.679487× |
| 5 | 2.403734 | 1.487048 | 1.616447× |

Mediana de cocientes por ronda: **1.669341×**.
384 iteraciones y 376 trials por recorrido
del banco; se ahorran 300 recomputaciones por ronda.
Ensamblados 760→460; solves
696→396. Los trials que no llegan a solve
explican la diferencia entre ambos contadores. El ensamblado ocupa una
mediana de 49.48% y el solve 37.87% del wall
de referencia instrumentada; el resto incluye bookkeeping, copias y harness.
No son porcentajes medidos del runner completo ni perfiles de deadline.

[Comandos y medición](../evidence/newton_reuse_bench_native01.json).
No se infiere rendimiento universal de estos 84 casos nominales.

## Trayectorias completas sin instrumentación

[Cuatro recorridos](../evidence/newton_reuse_native01.json), mismos seeds,
KEY/S, límites h2/1 µs y calendario de3.004 ms. Todos los archivos de cada
perfil coinciden byte a byte con la campaña anterior:
40 archivos / 20630344 bytes.
Incluyen STEP/LTE/intentos, OBS, ledgers, raíces seleccionadas, checkpoints
y rechazo de presupuesto. No se comparan ejecutables ni wall textual.

| Final decay | h máximo µs | Accepted | Wall actual s | Wall histórico s | Cociente histórico, no pareado |
|---|---:|---:|---:|---:|---:|
| ON | 2 | 3020 | 163.644395 | 274.582214 | 1.677920× |
| ON | 1 | 3704 | 174.586811 | 302.744977 | 1.734066× |
| OFF | 2 | 2987 | 154.943690 | 267.621150 | 1.727216× |
| OFF | 1 | 3674 | 176.607265 | 285.427160 | 1.616169× |

13385 accepted / 26770 finos; 24 restores
de prefijos y 368 avances repetidos por bits,
16 corrupciones / 8 rollbacks. Las 38.472 ecuaciones independientes del
banco anterior se heredan por identidad de datos: **no se reejecutaron**.
OBS cubre todos los endpoints publicados; HIGH/LOW229 completo se conserva
en los puntos y raíces almacenados, no en cada endpoint del recorrido.

[Auditor](../evidence/newton_reuse_reference01.json) y
[QA](../evidence/newton_reuse_tests01.json) protegen historia y nuevas mediciones.
Campaña 671.295742 s; 24978000 bytes privados nuevos,
bajo64 MiB y reserva1 GiB. 248 tests Rust heredados por identidad,
sin reejecutarlos, compilar biblioteca o ejecutar SPICE. Sin audio nuevo.

## Siguiente función a desbloquear

El reuso reduce costo con identidad de señal en este dominio. Ensamblado
y solve siguen dominando el benchmark. Siguiente: reducir el trabajo del
sistema lineal preservando masa y puertos, contrastando contra este kernel
exacto, para alcanzar un contorno de duración musical con costo viable.
No se acreditan aún deadlines RT, voz de producción, contorno desde
silencio, contorno de filtro ni identificación de dispositivos físicos.
