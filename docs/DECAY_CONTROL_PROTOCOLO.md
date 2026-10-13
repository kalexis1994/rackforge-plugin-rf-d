# Control eléctrico de decay en la voz cargada

Base d620bd4, antes de medir. Conservar3499 fuentes/8117 privados y rlib
anterior. Sólo lib.rs y atributos añaden exports de una familia explícita;
la API nominal, ensambladores y motor anteriores permanecen por bytes.

## Función y procedencia

PANEL_R16 entre DECAY_OUT211 y TIMING_C2=205, placa2/panel; SVC-9 PDF9/19,
Fig9-7/9-17, BOM controles PDF21: potenciómetro total1 MΩ. Grafo original
`loudness_contour_graph.json`, campo decay_ohm. Punto anterior100 kΩ; nuevo
experimento1 kΩ interior. Unidad ohmio; dominio0<R≤1 MΩ, finito y conductancia
finita. Cero requiere tratamiento de contacto/topología propio y se rechaza.
Estos valores no definen posición de perilla, ley del pot o tolerancia física.

Nueva familia decay_voice/decay_engine: transformación mecánica explícita de
fuentes nominales. Ensamblar la resistencia directamente en el grafo30,
pasando R al stamp; no restar matrices completas ni multiplicar una envolvente.
Mismas229 incógnitas, cargas, puertos, Schur, Newton, Radau, LTE y controlador.
Default100 kΩ. set_decay_ohm cambia sólo el parámetro; conserva458 HIGH/LOW,
fuentes, reloj y propuesta. Rechazos inválidos son atómicos. No interpolación
automática de control o reset digital. Semiconductores siguen condicionados.

## Nominal y evento

Desde cada checkpoint propio28.442 ms RFREL001: comparar4 avances completos
del motor nominal antiguo y nuevo a100 kΩ, incluidos coarse/mid/end, observables,
decisiones y checkpoint lógico. Compilar un caller mínimo con la rlib congelada
anterior y comparar sus bytes con ambos motores de la nueva biblioteca.
Dos resoluciones1/2 µs, misma propuesta real de entrada. Esa comparación
finita no reemplaza toda la matriz histórica; fuentes nominales no modificadas.

Antes del recorrido largo, restaurar de nuevo su entrada original; cambiar
100 kΩ→1 kΩ al reloj28.442 ms. CodecRFDCY0013728 bytes añade R: antiguo payload
de458 f64 desde56 se coloca desde64. Conservar todos los valores originales,
no otra historia, warmup o raíz. Guardar copia original, checkpoint preevento
y postevento; sólo bytes56..64 (R) pueden variar en la transición nueva.
Comprobar 0,negativo,NaN,∞,mayor1 MΩ y conductancia infinita: rechazo sin
mutación; además restore inválido. Preservar fallos/replay antes de reparación.

## Trayectoria y gates

1 kΩ ON, KEY0 y contactoabierto,28.442→44.442 ms:16 ms nuevos. Cortes.8 ms,
20 targets/21 estados completos. Hasta3 probes de16 accepted desde inicio,
interior/reset o cruces observados; no acumular Accepted. Cuatro corrupciones
de codec y destino inválido por perfil. Seleccionar primer/final/resets/cruces.

Observador C2/dC2/dt/Iataque/Idecay/Ifollower/Q25c−Q15c/Q20c; corriente de
decay ahora(V211−V205)/1000. Derivada Radau y KCL inicial propios como antes.
Cada endpoint≤2e−6 V/s (20 pA/C2); componentes seleccionados Decimal100.
Auditor original reconstruye PANEL_R16 con1 kΩ en la red documental y FD,
sin llamar Rust ni ajustar resultados.458 ecuaciones/par, gates históricos
2e−10A restricción/2e−11A KCL y1 nA/1 µV corrección independiente.
Mismo gate2292 µV/2 nA, LTE, resets≤10 ns; cruces si existen≤100 ns.
Nueve balances de carga propios y acumulados;1 pA·duración. No afirmar
descarga completa, monotonicidad continua, asentamiento o fidelidad física.

## Audio y recursos

Unir sostenido+liberación+control sólo con458 valores completos por bits en
ambos seams, un único endpoint y reloj/fuentes propios.36.004 ms reales:
WAV nativo36 ms/1728 frames,48 kHz, sinc18 kHz/Blackman,0.01 V/FS. Cola4 µs
omitida; sin loop, normalización, DC removal o fades. Comparar1/2 µs≤2 µV
y7 LSB; cuadratura8/16≤.25 LSB/1 LSB, PCM y replay completos. CLI publica
sidecar con R/evento y rechaza outputs existentes o un seam incompatible.

Rlib nueva y callers rustc≤120 s cada uno; perfiles≤1900 s, guard1800 s,
campaña≤4000 s; auditor≤600 s. Nuevos privados≤128 MiB, reserva1 GiB;
stack32 MiB de laboratorio. Sin Cargo/cache nuevos, sin SPICE.255 tests Rust
anteriores heredados por fuentes, no reejecutados. Checks nominal/entrada/
control/replay/grafo/audio nuevos se cuentan aparte. Ninguna medición de RT,
heap o stack máximo nueva. Producir circuito, traza y señal antes de ampliar
certificados; próximo trabajo se decide con observaciones de este recorrido.
