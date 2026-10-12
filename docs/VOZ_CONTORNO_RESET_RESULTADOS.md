# Contorno229: milisegundos y reset con carga

2026-10-12, CA3046 condicionado, sin hardware.
[Protocolo](VOZ_CONTORNO_RESET_PROTOCOLO.md),
[inputs](../evidence/voice_contour_reset_inputs01.json),
[nativo](../evidence/voice_contour_reset_native01.json),
[auditor](../evidence/voice_contour_reset_reference01.json),
[QA](../evidence/voice_contour_reset_tests01.json).

## Ventana funcional

Cuatro perfiles de3.004 ms nuevos, desde5.434 hasta8.438 ms absolutos:
reposo4 µs, KEY10/S sostenido1.5 ms, KEY0/S abierto1.5 ms. ON/OFF y
límites h2/1 µs parten de la misma historia fina por escena.458 componentes
heredadas por bits, sin precargas nuevas, fases ADSR o voltajes de latch
impuestos. Red, dispositivos, panel y tolerancias permanecen iguales.
Sólo se amplía el máximo permitido del controlador; LTE decide el paso.

El VCO1 real, BUS, ladder, ambos VCAs, J7 y contorno de volumen permanecen
en el mismo solve229. No se impone un audio de entrada para atravesar
el reset. El contorno de filtro y las cargas intrínsecas de otros ocho
BJT/diodos de placa2 siguen pendientes. Las hipótesis de dispositivo
no identifican un Minimoog físico ni heredan la admisión Gummel–Poon.

Finales con límite h1 µs:

| Final decay | Tramo | C2 V | LOUDNESS V | Q25 colector V | C7 V |
|---|---|---:|---:|---:|---:|
| ON | Reposo4 µs | 3.203528325 | 2.055113227 | 8.294092013 | .0557837160 |
| ON | S sostenido1.5 ms | 3.293292354 | 2.144483679 | .0241213110 | 1.327072656 |
| ON | Liberación1.5 ms | 3.289647577 | 2.140854826 | 8.293459191 | 1.143480167 |
| OFF | Reposo4 µs | 3.189149962 | 2.040798181 | 8.294132020 | .0557837160 |
| OFF | S sostenido1.5 ms | 3.279125889 | 2.130379133 | .0241213043 | 1.327072656 |
| OFF | Liberación1.5 ms | 3.046107395 | 1.898389686 | 8.293507003 | 1.143480167 |

C2 sube≈89.764 mV ON/89.976 mV OFF al sostener S. Al soltarlo baja
≈3.645 mV ON/233.018 mV OFF. Son respuestas de cada escena e historia,
sin asignar tiempos ADSR ni atribuir la diferencia sólo a un componente.
El RC de teclado también evoluciona: C7 supera1 V y permanece cargado
durante la liberación. RESET_DRIVER llega≈9.29987 V al sostener y
≈.03940/.04613 V después de abrir. Q25/Q15 responden a ambos caminos
de gatillo; abrir S no asigna un estado lógico ni descarga C7 de golpe.

J7 termina≈.220765 mV ON/.288495 mV OFF. Su valor instantáneo incluye
la fase del VCO; no mide por sí solo la ganancia del VCA. C2 continúa
precargado y la ventana no cubre ataque desde silencio, sustain asentado
o release completo. No hay audio nuevo ni nota completa admitida.

## Reset y precisión temporal

Cada perfil cruza exactamente un reset creciente de rampa43 a−2 V,
convención de observación heredada. Los cuatro eventos corresponden
al mismo reset bajo dos escenas/dos límites; no son cuatro ciclos consecutivos.
Tiempo interpolado≈7.303002624 ms. ON tiene bracket
[3828876576,3828876832] ticks; OFF [3828876544,3828876800].
Anchura.48828125 ns. Cada pareja de límites coincide en su bracket y
pasa el gate10 ns de diferencia interpolada. La interpolación guardada
es descriptiva; no acredita precisión física superior al bracket.

Se guardan las etapas coarse y finas que cruzan, su predecesor completo
y los endpoints de rampa. Restore desde ese predecesor reproduce hasta16
accepted posteriores por bits. No se acredita un periodo o periodicidad
asintótica a partir de un solo cruce por perfil.

12576 accepted y25152 finos publicados. Se aceptan h entre15.2587890625 ps
y2/1 µs, conservando coarse2h/dos finosh, gates2 µV/2 nA y20 intentos.
Todas las229 coordenadas se comparan en12 relojes por ON/OFF: máximo
.140395796 µV, dentro de2 µV/2 nA. Son cortes finitos, no una cota
para toda la trayectoria continua ni un criterio de fidelidad vintage.

## Auditoría y memoria

156 candidatos/35724 ecuaciones independientes,156 valores de corriente
en52 endpoints. Primer/último accepted de cada tramo y todos los que
cruzan reset; si un tramo tiene un único accepted, se cuenta una vez.
Residual/gate máximo.00432215142; corrección/gate3.496942293·10⁻⁶.
Corrientes del contorno: error≤1.735·10⁻¹⁸ A; panel/BUS/C27/KCL,
≤1.356·10⁻²⁰ A. Se contrastan también las decisiones LTE y clocks.

Balances por tramo/total de C2/C18/C27/C7/C4 y cargas Q25/Q15:
error máximo1.366·10⁻¹⁸ C, gate1 pA×duración. Sólo las etapas finas
publicadas alimentan la cuadratura nativa; no hay integración independiente
de todos los pasos. Las fronteras conservan458 componentes por bits.

24 restores y326 accepted repetidos, con candidatos, incrementos,
observaciones, LTE, intentos y checkpoint exactos. Cobertura de prefijos
de hasta16 accepted, no replay completo de los tramos nuevos de1.5 ms.
Los replays completos del banco anterior permanecen archivados.
16 corrupciones y8 rollbacks inducidos pasan. Codec3720 bytes/magic
RFMCTR01 separa esta receta; reloj absoluto u64 alcanza8.438 ms sin truncar
al superar2³² ticks. Un rechazo guardaría checkpoint/destino para replay.

Cuatro perfiles y oráculo pasan al primer intento. Campaña1195.2307122 s,
auditor31.1914704 s;20842915 bytes privados bajo64 MiB. Biblioteca congelada,
248 tests heredados por identidad, no reejecutados. Sin nuevas cargas,
compilación de biblioteca, SPICE, identificación física o deadline RT.

## Próximo bloque

Completar un ciclo entre dos resets con el contorno cargado y extender
la observación de carga/liberación. Mantener separados ciclo del VCO,
contorno desde silencio y duración musical; optimizar sólo con comparación
contra esta referencia y un presupuesto de error declarado.
