# VCO nominal de fase: núcleo rápido con puerto cargado

SVC-9 CA3046, nominal fijo, base `c6b6f91`.
[Protocolo](VCO_FASE_NOMINAL_PROTOCOLO.md),
[perfil](../evidence/vco_phase_profile01.json),
[contraste](../evidence/vco_phase_native05.json),
[QA](../evidence/vco_phase_tests01.json).

## Motor implementado

`vco_nominal_phase.rs` reemplaza el estado interno del generador por fase
compensada y reconstrucción periódica de DC/52 armónicos. Los coeficientes
proceden del ciclo eléctrico nativo de 30 ms ya admitido. Se recupera drive48
por KCL de la red resistiva; no se inventa una sierra o triángulo ideal.
El perfil conserva DC y limita armónicos a unos 21.36 kHz para este tono.

`vco_output_port.rs` elimina sierra/tap/cursor de la red resistiva y
entrega cuatro corrientes, 16 admitancias, tensiones reconstruidas y
potencia. BUS libre modifica la sierra a través de la impedancia de salida;
R6/R45 y sus retornos aparecen una sola vez. La reacción de los drivers
activos se aproxima mediante el perfil periódico: las memorias del VCO y
ambos 741 se sustituyen, sin afirmar conservación de sus cargas internas.

Frecuencia cargada **410.801335674 Hz**, derivada de cruces C1 descendentes
entre 8 y 40 ms; época de reset 0.211905625 µs y relación de fase obtenida
del ciclo aislado. Los 40–100 ms se reservan para medir. Fase de reset
sólo inicializada a partir de esa calibración; sin realinear las salidas.
La diferencia frente a la frecuencia aislada es 0.001750 cent.

## Resultados con límites previos

| Objeto | Resultado |
|---|---|
| Puerto original | 20 estrellas de tres nodos internos, contactos α=0/1, 80 columnas FD, corrientes y potencia pasan |
| Fase reservada | 25 cruces por resolución, error máximo 1.960e−6 ciclos, frecuencia 0.000168 cent |
| Sierra, armónicos 1–8 | Error vectorial AC 0.796337 %, DC 2.039307 mV |
| Triángulo, armónicos 1–8 | Error vectorial AC 0.084912 %, DC 0.469836 mV |
| Observaciones | 481 por resolución, 962 totales; hueco de fase máximo 0.002657 ciclos |
| Reacción local al BUS | 72 tangentes Radau, 24 estados a 1/8/32 µs, error máximo 0.001083 % |
| Residual lineal | ≤9.028e−11 tras refinamiento compensado, gate 1e−10 conservado |

La forma se compara mediante integración del interpolante sobre fase,
aplicada a ambos conjuntos de observaciones reservadas. Para sierra se
retira en ambos lados la contribución resistiva directa del BUS, conservando
la misma red y el mismo BUS observado; no se reajusta DC o amplitud.
Esto mide el componente periódico del generador. No equivale a una
cota continua ni acredita todos los armónicos altos. Error crudo de sierra:
RMS 0.136455 V, pico 1.633949 V alrededor del reset por truncado armónico.
Triángulo: RMS 5.677 mV, pico 80.973 mV. No presentar el error de armónicos
1–8 como ese error puntual ni como fidelidad completa de banda audible.
La tangente de BUS es local, con historia fija; no valida una nueva
trayectoria de gran señal o la realimentación de fase bajo otras cargas.

## Costo y dominio del callback

Tres millones de muestras medidas, un millón por rate: 48/96/192 kHz.
Tiempos 0.178360/0.178557/0.178197 s: aproximadamente **0.18 µs/muestra**
en este host, con **cero asignaciones heap** dentro del procesamiento.
Error de fase frente al reloj analítico ≤1.383e−12 ciclos. 200 cruces del
borde periódico con rates válidos, siete rechazos atómicos y retry idéntico
pasan. Se normaliza el ciclo también cuando el redondeo cae en 1 o apenas
por debajo de 0, conservando el incremento compensado.

No se ha medido deadline de la voz completa. El callback acepta rates
48–192 kHz y BUS ±2 V, α=.5, rieles y CV nominales. El benchmark admite el
costo de este núcleo, sin controles musicales generales, MIDI o hardware.

## Fallos y almacenamiento

Se conservan tres fallos con fuentes y replay: adaptador de compilación;
retorno R45 a masa omitido en el auditor con α=0; solve de tangente con
residual insuficiente. Reparaciones del arnés y hasta tres refinamientos
lineales recuperan los mismos gates. Las salidas eléctricas del replay
coinciden antes de las líneas de tiempo del benchmark.

[Recibos compactados](../evidence/vco_phase_failure_storage01.json):
5.544 MB restituidos exactamente desde 1.222 MB guardados, incluyendo
fuentes, fixtures y replays. La versión pasada anterior al ajuste del
borde de fase conserva sus fuentes ejecutadas. Un único `tmp/lab-current`
queda vacío; no hay WAV, nueva carpeta de muestras, biblioteca o cache.

## Estado de la voz

Este VCO es un **prototipo nominal de laboratorio**, sin exportación
ordinaria de plugin. La voz completa conserva su motor anterior y la nota
de 100 ms; no se atribuye a esa voz el tiempo de este núcleo.
Siguiente: conectar el puerto al BUS de la cadena real y contrastar J7,
C2/C5 y R59/R60, con memorias de contornos/filtro/VCA propias.
CV, rangos, modulación, otros selectores, arranque y hardware siguen abiertos.
