# Primer núcleo de cargas dentro del presupuesto observado

2026-10-31. [Protocolo](CHARGE_REDUCED_PROTOCOLO.md),
[derivación](../evidence/charge_reduced_derivation01.json),
[dominio](../evidence/charge_reduced_domain01.json),
[reloj384 kHz](../evidence/charge_reduced_validation01.json),
[coste](../evidence/charge_reduced_native01.json) y
[QA](../evidence/charge_reduced_tests01.json).

## Alcance físico

Linealización local del circuito68 ya contrastado: mixer/C27, ladder,
recuperación, dos VCA y salida/J7. SVC-9 Fig.9-11 p.13, Fig.9-8 p.10,
Fig.9-17 p.19. Mismos dispositivos y cargas condicionales, sin reajuste.
Dos modelos separados: R61=200/L1 y200000/L0; VCA1/2=2 V y controles fijos
de mixer_chain_lab. R6=.5, puerto externo Ibus=(BUS-.5*U)/39250 A una vez.
U es una tensión de prueba; no incluye la familia H128, su realimentación
de BUS, VCO, contornos, saturación grande o parámetros variables.

Cada modelo parte de DC propio con U=0. G y M se exportan desde el
stamp nativo. El núcleo devuelve **perturbaciones** BUS/BASE/J7 y corriente
respecto a ese DC; no es la salida absoluta del circuito. State::ZERO
representa perturbación nula alrededor de capacitores ya cargados en DC,
no un reset físico a carga cero. La carga absoluta incluye el offset DC
y los rieles fijos; la reducción conserva sus incrementos.

## Reducción sin truncar capacitores

La incidencia A contiene18 ramas independientes:17 capacitores originales
y C10 explícito. Con x como incremento nodal, q=A*x son18 voltajes de
capacitor; las cargas incrementales son diag(C)*q. Completar con50
potenciales algebraicos permite x=T*[q,z]. La congruencia conserva
trabajo, corrientes y masa; M=A^t*diag(C)*A pasa por bits en estos exports.
No se eliminó ningún modo dinámico, capacitor pequeño o retorno.

El Schur de las50 filas sin masa da diag(C)*qdot=-K*q+B*U y reconstrucción
x=Xq*q+Xu*U. Xu conserva la respuesta instantánea del puerto. No anidar
Newton ni factorizar matrices en cada muestra: K/B y la transición
SDIRK2 L-stable se preparan fuera de audio para384 kHz. Entrada interpolada
linealmente entre extremos, gamma=1-1/sqrt(2), igual ley de integración
que la referencia no lineal. Datos derivados de G/M; ninguna reserva se
usó para ajustar coeficientes.

Las66 comparaciones de frecuencia (33 por escena,10..24000 Hz) pasan
contra solves complejos directos68 en todos los nodos y corriente BUS.
Máxima fracción de gate nodal .001063 (gate relativo1e-8 + absoluto1e-12).
Dieciséis pasos discretos pasan frente a solves BE68 de ambas etapas,
error nodal máximo2.56e-15 V; balance de carga y KCL algebraico pasan
1e-20 C y1e-12 A. Polos reales máximos -3.779/-3.453 s^-1; el modo lento
se conserva, sin llamarlo asentado tras4 ms.

## Reserva no lineal y reloj de producción

Ocho historias propias del circuito no lineal,0..4 ms, dos escenas,
amplitudes1e-5/1e-3 V y pasos500/250 ns. Entrada sinusoidal137 Hz más
.3 veces1103 Hz. Se calcula la entrada en cada etapa real del solver;
DC independiente del mapa reducido. No otro oráculo de dispositivos.

Todas pasan los gates predefinidos: peor error de68 nodos2.210 nV frente
a1 uV; corriente panel1.079 fA frente a2 nA. J7 pasa RMS .001, pico .003
y media1 uV, con fallback absoluto1 nV cerca de cero. Mayor RMS relativo
.0004747. Refinamiento no lineal500/250 ns pasa. Estos resultados admiten
las escenas ensayadas; la guarda |U|<=1.3 mV del kernel no certifica todas
las señales o historias posibles dentro de esa amplitud.

En384 kHz, cuatro contrastes contra la referencia fina conservan todas
las muestras de J7/BUS/BASE, y68 nodos en filas seleccionadas. Peor error
nodal retenido2.181 nV; BUS74.45 pV; mayor RMS relativo J7 .00047592.
El contraste de todos los nodos a este reloj es **disperso**, no una
medición de cada nodo en toda la rejilla original. Interpolación temporal
de la comparación declarada; no se cambia la trayectoria del circuito.

Rust/Python:1024 consultas nativas,18 estados y68 nodos, con gate1e-11 V
y1e-15 A. Los tres puertos publicados son idénticos por bits a la
reconstrucción nodal. Doce rechazos/reintentos conservan estado por bits,
incluyendo ceros con signo; cero heap. No se reejecutan tests heredados
ni se cuentan estas consultas como unit tests nuevos.

## Coste del bloque, no de una voz completa

Ryzen5 5600X/Windows11, plan Alto rendimiento verificado al cierre,
toolchain/rlib congelados, opt-level2 genérico, un hilo. El intervalo
incluye1024 pasos del núcleo18, reconstrucción BUS/BASE/J7/corriente y
FIR384→48 kHz heredado. El generador sinusoidal de prueba y la derivación
de matrices están fuera del intervalo. Ningún oscilador o contorno incluido.

| Escena | Bloques128 | Mediana | P99 | Máximo | Fracción máxima del presupuesto |
|---|---:|---:|---:|---:|---:|
| R61=200/L1 | 1200 | .16610 ms | .21712 ms | .25950 ms | 9.732 % |
| R61=200000/L0 | 1200 | .16625 ms | .20502 ms | .24880 ms | 9.330 % |

Presupuesto2.6667 ms/bloque. Primero incluido, cero incumplimientos de
deadline y del objetivo50% en2400 bloques, cero heap.128 entradas de
audio por bloque; el primer FIR entrega80 salidas por su latencia1 ms,
después128. Por escena:1228800 entradas384 kHz y153552 salidas48 kHz,
3.2 s de reloj procesado. Estado152 bytes, FIR6168 bytes, más arrays
temporales fijos del caller. El setup medido sólo crea estados/anillo;
no contiene la derivación offline de matrices. No es WCET o validación
del circuito no lineal a3.2 s. No comparar este tiempo con la voz completa
de44.6–47 s como si fueran el mismo trabajo.

## Recursos e incidencias

El export completo HIGH/LOW ocupó43,248,404 bytes y se retiró antes de
admitir evidencia, tras calcular métricas en toda su rejilla. El
[recibo de retiro](../evidence/charge_reduced_retirement01.json) conserva
SHA/tamaño y verifica todos los estados seleccionados contra ese export.
El pack compacto ocupa4,224,080 bytes: puertos completos y estados cada16
filas, más el peor caso y extremos. No reconstruye los bytes ausentes de
la rejilla completa. Se conservan digests y fuentes para volver a calcular;
ninguna de las8769 entradas privadas previas fue retirada.

El auxiliar de export falló E0277 al propagar StepError a Box<Error>.
[Fuente y replay](../evidence/charge_reduced_oracle01.json) retenidos;
la corrección adapta sólo ese error de consola. Ecuaciones y gates iguales.
Sin Cargo, rlib/cache, SPICE, WAV o promoción de voz anteriores. Temporales
vacíos. El rechazo nodal1 uV de la voz monofónica anterior sigue abierto.

## Siguiente decisión

Este bloque demuestra que conservar cargas/puertos y cumplir un presupuesto
pequeño son compatibles para la linealización local ensayada. Para una
voz musical falta extender la ley constitutiva fuera de esa linealización:
medir no linealidad y puntos de operación ante nivel/cutoff/contornos,
conservar memoria al cambiar representación y unir el VCO H128.
No interpolar matrices o multiplicar J7 por una envolvente sin contrastar
las corrientes y cargas devueltas. La admisión RT de la voz permanece falsa.
