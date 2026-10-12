# Cambios C2/reset con memoria y restauración del circuito205

2026-10-12. Model D CA3046. [Contrato previo](VOZ_SEGUIDOR_CONTROL_PROTOCOLO.md),
[semillas/receta](../evidence/voice_loudness_control_inputs01.json),
[campaña nativa](../evidence/voice_loudness_control_native01.json),
[oráculo](../evidence/voice_loudness_control_reference02.json),
[QA](../evidence/voice_loudness_control_tests01.json).

## Continuidad y controles

Dos historias propias desde los finales C2=3,2 V/reset=0,7 V del
[seguidor cargado](VOZ_SEGUIDOR_RESULTADOS.md), con sus respectivos
pasos125/62,5 ns. Se extraen las410 coordenadas high/low del registro
nativo y se comparan por bytes con el recibo anterior antes de empaquetar.
Inicio absoluto5,252 ms; duración nueva10 µs. No nuevos DC, preparación
del seguidor o transferencia de memoria entre resoluciones.

Cinco tramos de2 µs aplican las fuentes ideales previamente declaradas.
Cada frontera conserva410 componentes por bits; el primer tramo mantiene
las fuentes iniciales y los otros cuatro las cambian. Los cinco nodos
algebraicos entrantes son guesses, no voltajes sujetos a continuidad física.
El solve simultáneo publica sólo la raíz aceptada con todas las cargas.

## Niveles y carga del terminal de reset

Perfil62,5 ns. J7 mantiene tip/ring32 Ω y R21 inferior2000 Ω, heredados.
Corriente y carga de reset positivas desde la fuente hacia la red cargada.

| Tramo | C2 V | Reset V | Volumen V | J7 mV final | Reset µA final | ∫I_reset pC |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3.2 | 0.7 | 2.05160043263 | 3.10129595058 | 0.01 | 0.02 |
| 1 | 6 | 0.7 | 4.84031260473 | 5.90584455505 | 0.00952736383 | 0.0190547275984 |
| 2 | 6 | 0.01 | 4.83748488623 | 5.86572280447 | -49.9320781 | -99.8641571437 |
| 3 | 0.846934576 | 0.01 | -0.290034076626 | 0.374133255906 | 0.01 | 0.02 |
| 4 | 3.2 | 0.7 | 2.05160043263 | 3.05467786431 | 0.01 | 0.02 |

El tramo2 entrega≈99,86 pC al terminal de reset en2 µs. Esta carga de la
red deberá incluirse al cerrar el biestable. La integral es intercambio
con una fuente ideal: no equivale al cambio de carga del capacitor C2,
que todavía no pertenece al estado dinámico205. El retorno a las fuentes
iniciales tampoco implica restaurar los voltajes capacitivos iniciales.
Los niveles J7 corresponden al final de cada tramo y no son amplitudes
por ciclo, envelope times ni un contorno de volumen identificado.

## Checkpoint y continuación por bits

Formato3320 bytes RFLCTL01: ticks absolutos, paso, cursor de tramo,
C2/reset y410 componentes. La receta fija de VCO/cadena se reconstruye
desde el helper protegido. Los parámetros ajenos a esta escena siguen
fuera del formato; no es un preset de host o checkpoint genérico.
Se valida esquema, reloj/calendario, fuentes, finitud y normalización.

Veinte checkpoints de inicio/mitad de tramo se escriben, leen, decodifican
y reempaquetan por bytes. Cada uno continúa hasta el final de su tramo,
comparando todos los pares con la historia original: candidatos,
incrementos, ratios, iteraciones/trials y checkpoint final.360 pasos
repetidos reproducen los240 pasos originales cubiertos por esos prefijos.
No se afirma replay desde cualquier checkpoint atravesando todo el calendario.
Ocho corrupciones se rechazan antes de avanzar: magic, NaN, fase inválida
sin soporte de reloj y fuente que no corresponde a su receta de tramo.

## Equaciones, corrientes y balances

Primer/último par por tramo/perfil:20 pares,40 candidatos,
**8200 ecuaciones independientes** del VCO Decimal100 y Python/FD
cadena/seguidor. Mayor ratio residual 0.00298399651943;
corrección 0.00123097731885, ambos gate1.
Veinte endpoints realmente emitidos por Rust:60 corrientes C2/reset/R59
contrastadas a1 nA y dos niveles por valor high+low.

C18=100 pF y C27=10 µF conservan ΔQ+∫I_dc=0 a1 pA·duración,
por cada tramo y recorrido completo. Se verifica composición de las
cuatro integrales entre tramos y total. La cuadratura3/4,1/4 usa etapas
nativas y no se describe como propagación/quadratura independiente de
cada paso. Las ecuaciones seleccionadas tienen el oráculo independiente.

Refinamiento a reloj común (semillas y cinco finales), gates2 µV/2 nA:

| Ticks absolutos | Error voltaje V | Error corriente A | Ratio al gate |
|---:|---:|---:|---:|
| 2753560576 | 3.359097298e-13 | 6.28839435038e-18 | 1.679548649e-07 |
| 2754609152 | 1.50277743467e-13 | 1.45078822123e-18 | 7.51388717335e-08 |
| 2755657728 | 4.59111216526e-11 | 4.0140489897e-18 | 2.29555608263e-05 |
| 2756706304 | 4.85566057838e-11 | 1.60507689552e-18 | 2.42783028919e-05 |
| 2757754880 | 5.04893565099e-10 | 4.62318474925e-18 | 0.000252446782549 |
| 2758803456 | 5.34857414946e-10 | 3.95156690302e-18 | 0.000267428707473 |

## Recursos y reparación del auditor

Compilación 0.717438 s; perfiles
2.79676/4.99075 s; oráculo
5.58213 s. Biblioteca/kernel205 sin cambios;248 tests Rust
heredados por identidad y no reejecutados. Memoria/IO/Vec de este llamador
son herramientas de laboratorio, sin medida de heap ni admisión RT.

El [auditor01](../evidence/voice_loudness_control_reference01.json)
confundía la última observación escalar ob con la lista obs al construir
el resumen: TypeError y repetición idéntica preservados junto con fuente.
Se corrigen sólo cinco accesos del resumen y el índice de recibo para
conservar el intento02. Ecuaciones, gates, inputs y campaña nativa son
los mismos; no se reintegró el circuito después de reparar el auditor.

## Próximo cierre

Integrar el estado C2 y su red de carga/descarga con la corriente del
seguidor ya admitida; preservar el puerto de reset para el biestable.
C2/reset todavía impuestos: no ADSR, conmutación causal completa,
controlador adaptativo205, audio nuevo, identificación vintage o RT.
Mantener la selección de rama del biestable como problema explícito,
sin resolverla mediante el calendario de fuentes de este banco.
