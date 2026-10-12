# Seguidor cargado: C2/reset → VCA en la voz nativa

2026-10-12. Model D CA3046. [Protocolo previo](VOZ_SEGUIDOR_PROTOCOLO.md),
[inputs](../evidence/voice_loudness_inputs02.json),
[nativo](../evidence/voice_loudness_native02.json),
[ecuaciones independientes](../evidence/voice_loudness_reference01.json),
[corrientes observadas](../evidence/voice_loudness_observations01.json),
[QA](../evidence/voice_loudness_tests01.json).

## Conexión realizada

La fuente de volumen de2 V se sustituye por Q3/Q2/CR6 y R59 cargados
por Q18 dentro del mismo Newton de205 incógnitas/dos etapas Radau.
Los cinco nodos nuevos son algebraicos; C2 y base Q15/reset siguen
impuestos. Las leyes del VCO, ladder, VCAs y auriculares se heredan de
la biblioteca congelada; sólo cambia esta frontera y su incidencia.

Cada uno de los doce perfiles conserva por bytes las400 coordenadas
high/low entrantes del checkpoint abierto de62,5 ns a5,25 ms. La
preparación resuelve sólo los cinco nodos del seguidor con la carga
Q18 entrante, y no reescribe ninguna carga del circuito anterior.
Se integra una continuación de2 µs a pasos fijos125/62,5 ns. Los estados
no se interpretan como una nota en régimen ni tiempos attack/decay.

## Observaciones al final de2 µs

Perfil62,5 ns, J7 tip/ring32 Ω, R21 inferior2000 Ω. Corrientes positivas
hacia el circuito desde C2/reset; R59 positiva desde seguidor a Q18.

| C2 V | Reset V | Volumen resuelto V | J7 mV | C2 µA | Reset µA | R59 µA |
|---:|---:|---:|---:|---:|---:|---:|
| 0.846934576 | 0.01 | -0.290034076626 | 0.377018885298 | 0.040162342 | 0.01 | -2.08221757e-09 |
| 0.846934576 | 0.7 | -0.290034076626 | 0.377018885298 | 0.040162342 | 0.01 | -2.08221757e-09 |
| 3.2 | 0.01 | 2.05160043263 | 3.11229983935 | 0.0500717472 | 0.01 | 2.28269788 |
| 3.2 | 0.7 | 2.05160043263 | 3.11229983935 | 0.0500717472 | 0.01 | 2.28269788 |
| 6 | 0.01 | 4.83748490508 | 5.98241233188 | 0.0657011086 | -49.9320805 | 8.55723832 |
| 6 | 0.7 | 4.84031261663 | 5.9824409657 | 0.0622253502 | 0.00952736373 | 8.59408477 |

El reset0,01 V a C2=6 V recibe≈49,93 µA mediante CR6; imponer una base
sin registrar esta corriente ocultaría la carga que deberá recibir el
biestable completo. La corriente de C2 permanece mucho menor, lo que
ilustra por qué no se puede confundir una curva de control de salida
con las corrientes de sus terminales. Los niveles bajos/altos de C2 son
escenarios documentados de laboratorio, no umbrales físicos identificados.

## Contraste y alcance

288 pasos nuevos; doce repeticiones del primer solve reproducen por bits
estados, incrementos, ratios, iteraciones y trials. Primer/último par
por perfil:24 pares,48 candidatos,9840 ecuaciones independientes.
VCO Decimal100; cadena/seguidor Python y Jacobiano FD central1 µV,
cargas Radau explícitas. Mayor ratio residual independiente
0.0012802529762; corrección
3.08633651672e-05, gates1.

Los seis refinamientos al mismo reloj de2 µs pasan sobre las205
incógnitas high+low:2 µV/2 nA, mayor ratio
6.15869171534e-05.
El auditor nodal evalúa48 vectores de puertos en sus candidatos;
un segundo auditor compara las24 observaciones de endpoints realmente
emitidas por Rust:72 valores de corriente, gate1 nA, además de niveles
J7/volumen exactos. No se cuenta ese segundo auditor como otras raíces.

Compilación del llamador 0.623232 s, ejecución
4.02038 s, auditor de ecuaciones 6.89652 s.
Son medidas de laboratorio offline, sin medición de heap/deadline.
248 tests Rust heredados por identidad; no se reejecutaron ni se compiló
la biblioteca. Sin nuevo audio/SPICE, fidelidad vintage ni admisión RT.

## Fallo de compilación preservado

El [intento01](../evidence/voice_loudness_native01.json) y su repetición
idéntica encontraron dos helpers privados: joint_vco_fine y
solve_linear_sparse. Se conserva fuente completa, compiler y stderr.
La [reparación declarada](../tools/repair_joint_loudness.py) proyecta
las200 incógnitas existentes hacia joint_voice::parts público y copia
exactamente two_sum/eliminación desde fuentes protegidas. Mantiene
leyes, preparación, Newton, incidencia, presupuestos y gates. El
intento02 pasó; no se amplió la visibilidad de la biblioteca.

## Próximo bloque

Continuar controles C2/reset desde estos estados con carga entrante y
restores completos del conjunto205; después conectar el estado C2 y
el biestable causal. Conserva abierta la ambigüedad documentada del
[contorno completo](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) y las hipótesis
rápidas del [biestable](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md).
El contorno de filtro y VCO2/3 también quedan pendientes. Esta conexión
admite el seguidor cargado en una ventana corta, no un ADSR emulado.
