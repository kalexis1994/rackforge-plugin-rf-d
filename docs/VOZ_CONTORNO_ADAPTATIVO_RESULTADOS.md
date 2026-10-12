# Controlador229 y contacto sostenido

2026-10-12. [Protocolo](VOZ_CONTORNO_ADAPTATIVO_PROTOCOLO.md),
[inputs](../evidence/voice_contour_engine_inputs01.json),
[nativo](../evidence/voice_contour_engine_native01.json),
[auditor](../evidence/voice_contour_engine_reference01.json),
[QA](../evidence/voice_contour_engine_tests01.json).
Model D CA3046 condicionado, sin unidad física.

## Avance funcional

El controlador adaptativo existente para200 incógnitas ahora también
gobierna el sistema229: VCO1→BUS→ladder→ambos VCAs→J7, contorno de
volumen, Q25/Q15 cargados y gatillo. No se cambia ningún componente,
parámetro de dispositivo, capacitor, posición de panel o gate de Newton.
Las458 componentes entrantes del final229 propio se conservan por bits.

El motor calcula un coarse de2h y dos finos deh, comparando todas las
incógnitas a2 µV/2 nA. Publica los finos cuando LTE≤1 y las observaciones
terminan; duplica si LTE≤.25. Fallos reducen el paso con historia original.
Los cambios KEY/S modifican sólo las fuentes y no asignan estados ADSR.
Restore inmediato después de KEY propone el trial algebraico CR10 ya
usado por Newton para comprobar el dominio; no lo publica como estado.

Cuatro perfiles propios de102 µs desde5.332 hasta5.434 ms:
final decay ON/OFF × máximos h250/125 ns. Reposo2 µs, S cerrado/KEY10 V
durante50 µs y S abierto/KEY0 V durante50 µs. Ambos máximos parten de
la misma semilla fina para cada ON/OFF. No son dos pasos fijos ni dos
tolerancias; la ley de adaptación y los gates permanecen idénticos.

## Respuesta del contorno

Voltajes finales con límite h125 ns:

| Final decay | Tramo | C2 V | LOUDNESS V | Q25 colector V | C7 mV |
|---|---|---:|---:|---:|---:|
| ON | Reposo2 µs | 3.200636716 | 2.052234346 | 8.294104538 | 7.713905624 |
| ON | S sostenido50 µs | 3.203650020 | 2.055234387 | .01604061955 | 55.78782089 |
| ON | S abierto50 µs | 3.203537750 | 2.055122611 | 8.294091693 | 55.78402007 |
| OFF | Reposo2 µs | 3.194685915 | 2.046309747 | 8.294145011 | 7.713905624 |
| OFF | S sostenido50 µs | 3.197702161 | 2.049312711 | .01604347372 | 55.78782089 |
| OFF | S abierto50 µs | 3.189782830 | 2.041428260 | 8.294131703 | 55.78402007 |

C2 sube3.013304 mV ON/3.016246 mV OFF durante el contacto sostenido.
Durante la liberación baja.112270 mV ON/7.919332 mV OFF. Son observaciones
de cada escena y su historia propia, no tiempos de servicio del Minimoog
ni una identificación aislada de CR4. Q25 conmuta desde el circuito;
Q15 colector evoluciona a≈5.000862 V ON con S sostenido. Las fuentes
ideales del latch eliminadas en el bloque anterior siguen ausentes.

C4 orientado alcanza≈2.820568 V ON al sostener S y≈2.198855 V después
de soltarlo; ambas placas internas se conservan. SET_BASE llega≈−1.079909 V
durante la liberación bajo este modelo condicionado. El almacenamiento
intrínseco de los otros ocho BJT y diodos de placa2 sigue omitido.
C7 sólo llega≈55.79 mV: no se completó un Note On por KEY.
Esta voz entra precargada;102 µs no cubren un ataque desde silencio,
decay, sustain asentado ni release completo.

J7 al final es≈1.977147 mV ON/1.967251 mV OFF, con el VCO real continuando
su fase. Esa observación mezcla evolución del generador y del contorno;
no es una medición aislada de ganancia ni una nueva escucha.

## Control temporal, memoria y evidencia

3226 accepted,6452 pasos finos publicados y4474 accepted repetidos.
Cada replay reproduce coarse/finos, incrementos, estados, observaciones,
LTE, intentos, decisiones de paso y checkpoint por bits hasta el fin
del tramo.20 restores completos,16 corrupciones rechazadas y8 rollbacks
atómicos: destino inválido y presupuesto1 insuficiente al cerrar S.
Checkpoint3720 bytes incluye reloj absoluto, máximo/intentos/próximo
paso, tramo, versión, KEY/contactos y458 componentes; receta restante fija.

Se aceptan h entre30.517578125 ps y250 ns (125 ns en los perfiles limitados).
El paso pequeño resuelve la transición de este modelo condicionado;
no se interpreta como velocidad física medida del transistor. Máximo
LTE observado.9954477693≤1. La auditoría de todos los accepted verifica
clocks, halvings efectivos, límites del destino y próxima decisión.

144 candidatos/32976 ecuaciones independientes: coarse y ambos finos,
primer/último accepted de cada tramo, grafo/FD y Q Decimal100.
Máximo residual/gate=.00374367442; corrección/gate=1.450014619·10⁻⁵.
144 corrientes de contorno en48 endpoints, error≤4.659·10⁻²¹ A;
panel/BUS/C27/KCL se contrastan también, error≤7.859·10⁻²¹ A.
Balances por tramo/total C2/C18/C27/C7/C4 y terminales Q25/Q15:
error máximo6.985·10⁻²¹ C frente a1 pA×duración. Cuadratura de los
finos nativos, sin integración independiente de cada paso aceptado.

Las229 incógnitas se comparan en12 relojes por ON/OFF: semilla, fin de
reposo y cortes10/20/30/40/50 µs de cada tramo largo. Diferencia máxima
1.538720688·10⁻¹⁰ V (≈.154 nV), gate2 µV/2 nA. No es una cota durante
toda la conmutación ni una tolerancia de fidelidad física.

Campaña599.0525405 s, auditor27.8237959 s; salidas privadas10054782 bytes
bajo32 MiB. Los cuatro perfiles y el oráculo pasan al primer intento.
Biblioteca congelada y248 tests heredados por identidad, no reejecutados.
Sin compilación de biblioteca, nuevas cargas de placa2, SPICE o audio.
La velocidad media de laboratorio no acredita un deadline de tiempo real.

## Siguiente bloque

Extender el circuito cerrado a ventanas de milisegundos con contactos
propios y atravesar los resets del VCO. Mantener comparación al mismo
reloj y cargas completas antes de perseguir una nota de duración musical.
Contorno de filtro, otros VCO, parámetros físicos, host y RT siguen abiertos.
