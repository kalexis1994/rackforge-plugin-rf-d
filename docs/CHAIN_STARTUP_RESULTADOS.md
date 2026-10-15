# Arranque propio y nota nominal de 0–100 ms

## Condición inicial y API

[Contrato previo](CHAIN_STARTUP_PROTOCOLO.md), motor por incidencias
seleccionado, mismas leyes CA3046/SVC-204D y cargas SVC-9 pp.9/19/13/10.
Se resuelve el DC conjunto de 118 nodos con KEY=0 y fuente periódica
congelada en t=0. Después se libera el tiempo desde esa memoria exacta.
No se proyecta el estado de 40 ms de una trayectoria reservada.

La API [nominal_chain_startup::cold_start](../crates/rf-d-circuit/src/nominal_chain_startup.rs)
recibe la receta de la cadena y construye su aproximación numérica sin
archivos ni una semilla aportada por el llamador. Usa DC parcial de audio
y heurísticas de volumen/filtro/timer publicadas, y vuelve a resolver el
DC conjunto con contornos y cargas reales. Las aproximaciones son ayudas
de Newton en voltios, no parámetros audibles o una secuencia física de
encendido. El DC parcial usa su frontera nominal impuesta sólo para
convergencia; no se publica como condición inicial final.

`numerical_guess` permite las dos variantes del banco; `initialize` admite
una aproximación explícita y presupuesto acotado. Ambas variantes convergen
en 16 iteraciones. Residuales nativos 3,290554e-17/2,775522e-17 A y
correcciones 1,782066e-13/1,264440e-10 V, dentro de 1 pA/2 nV. No se afirma
unicidad global de un circuito con latches por probar dos aproximaciones.

El [primer intento](../evidence/chain_startup_native01.json) falló antes
del DC conjunto: la ayuda de semilla intentaba resolver corriente impuesta
en el mezclador con sus cinco ramas OFF, que deja BUS flotante. Fuente y
replay sin cambios conservados. Se reemplaza ese adaptador por el DC
parcial de circuit66 con frontera impuesta declarada; el VCO sigue siendo
quien fija BUS en la solución conjunta. No se añade una conductancia o
fuente ficticia a las ecuaciones finales.

## Memorias y eventos

El [ledger inicial](../evidence/chain_startup_guards02.json) registra
24 capacitores lineales y doce cargas BE/BC de los seis dispositivos de
latch. Las tensiones salen de los terminales HIGH/LOW convergidos; no se
ponen todas las cargas a cero. C2 inicial 0,8602012381 V, C5 0,8605568568 V,
BUS −0,9417446218 V. J7 inicial resulta 0 V de las ecuaciones.

Primer ROOT.old idéntico por bits al DC publicado. KEY ON a 1 ms y OFF a
75 ms sin modificar ningún bit de estado entre el evento y los primeros
coarse/fine siguientes. Las memorias se confirman sólo tras aprobar el
paso. El estado de capacitor no se reconstruye desde otra trayectoria.

La API pasa 22 rechazos y 22 reintentos válidos exactos: no finitos,
canonicalidad HIGH/LOW, amplitud, optional, tiempo de preparación, presupuesto
y agotamiento de Newton, variante no admitida y tarjetas inválidas. Heap
cero en ese banco, incluidas llamadas completas a cold_start. El banco
previo de initialize aporta otros 18 rechazos/reintentos conservados.

## Trayectoria, control y auditoría

[Prototipo](../evidence/chain_startup_native02.json) y
[API autónoma](../evidence/chain_startup_selected01.json): ambos completan
dos perfiles 64/32 µs, de **0 a 100 ms**, con grilla de 125 µs y 801
observaciones por perfil. KEY=0 hasta 1 ms, 10 V hasta 75 ms y 0 V después.
La API conserva DC, GRID/ROOT, eventos y estado final idénticos al prototipo.

| Medición en la API | 64 µs | 32 µs |
| --- | ---: | ---: |
| Pasos aceptados | 8993 | 8996 |
| Pares auditables seleccionados | 18 | 18 |
| Replays exactos / rechazos atómicos | 6 / 5 | 6 / 5 |
| Heap durante integración | 0 | 0 |
| Menor paso full observado | 7,8125 ns | 7,8125 ns |
| Máximo residual nativo | 0,999193 pA | 0,999193 pA |
| Máxima corrección nativa | 1,970240 nV | 1,970240 nV |
| Procesamiento offline, s | 22,616008 | 22,337958 |

Los fine usan la mitad del paso full; no se relajan MIN_DT ni los gates.
Hay margen pequeño respecto de 2 nV. Los tiempos no incluyen replays ni
preparación DC y no acreditan deadline RT. No compararlos como ahorro frente
a la antigua rama de 60 ms, que tenía otra historia inicial.

Refinamiento propio: J7 RMS relativo 2,182993e-7, pico 1,877419e-6, media
3,556138e-11 V; pasan los límites previos. C2/C5, BUS y cargas también
pasan. A 10 ms, C2≈4,273670 V y C5≈5,196788 V; después de KEY OFF sigue
el decaimiento. La ventana de 100 ms no demuestra cola completamente asentada.
Pico J7 observado en la grilla 12,612974 mV, sin normalización o ajuste.

El [directo histórico](../evidence/chain_startup_control01.json) consume
el mismo DC propio y repite 32 µs: observaciones, raíces, eventos y estados
finales idénticos. Adaptadores copian tipos/estado, no ecuaciones; no se
usa ese tiempo como benchmark de admisión de costo.

[Auditoría original](../evidence/chain_startup_audit01.json): **8806 filas**,
238 de DC y 8568 de 36 pares Radau, con Amount y estrella VCO originales.
Dinámicas: máximos 0,696125 pA y 0,320298 nV frente a 20 pA/2 nV. Ambas
raíces DC pasan el mismo gate. Se comprueban explícitamente los empalmes
de memoria inicial/KEY. La API conserva esas etapas por bits: no se presenta
la auditoría como una segunda trayectoria independiente o como reejecutada
sobre una trayectoria nueva distinta de las etapas idénticas.

## Admisión y alcance pendiente

Se admite el arranque nominal de cadena y la campaña 0–100 ms con esa
fuente periódica y receta. El generador de fase ya está oscilando: esto
**no es arranque del VCO físico**, CV general, tres osciladores, encendido
de fuentes o parecido demostrado con hardware. El producto/plugin y RT
siguen pendientes. La salida es una trayectoria eléctrica J7, sin WAV nuevo.

[QA global](../evidence/chain_startup_tests01.json): 4239 fuentes anteriores
y 8769 inputs privados protegidos; 255 tests Rust heredados por identidad,
sin reejecutar. Se ejecutan cuatro ramas de prototipo/API y un control
histórico, con archivos de fuentes recuperables y fallo/replay preservados.
Un tmp/lab-current vacío; sin Cargo, rlib, cache o muestras nuevas. Recibos
por debajo de 8 MiB sin QA. Solver activo por incidencias conservado; su
commit de origen anterior queda resuelto. El inicializador nuevo se fija
por ruta/SHA y se comprueba en el commit real después de crearlo.

Siguiente: lectura offline de J7 a un reloj de audio, con tiempos/eventos
y error de lectura contrastados contra una referencia fina. Preparar un
buffer acotado, conservar nivel absoluto y estudiar la conversión temporal
antes de exportar audio. Evitar otra cadena de microoptimizaciones locales.
