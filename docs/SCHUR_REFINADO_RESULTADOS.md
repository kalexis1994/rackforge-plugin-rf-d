# Schur refinado: gate lineal resuelto y costo pendiente

2026-10-13. Base869f4ec. Laboratorio229 CA3046 condicionado;
sin unidad física. [Protocolo](SCHUR_REFINADO_PROTOCOLO.md),
[soporte exacto](SCHUR_REFINADO_SOPORTE.md) y
[rechazo anterior](SCHUR_DINAMICO_RESULTADOS.md).

## Cambio numérico

La partición sigue siendo dos interiores64×64 (ambas etapas de cada741)
y un exterior330×330. Cada nuevo J se factoriza de nuevo; sus factores
L/U y permutaciones se conservan sólo para resolver RHS adicionales de
ese mismo J. No hay cache de factores entre trials de Newton distintos.
La respuesta a los puertos conserva masa y acoplamiento entre etapas.
Se reconstruyen458 correcciones antes de probar Newton y sus candidatas.
El estado aceptado229, HIGH/LOW, memorias y cargas externas no se reducen.

El residuo incluye −b, suma compensada y error de producto obtenido
mediante mul_add. Si el gate mixto1e-11 falla, se resuelve J·e=b−Jd
con los mismos factores y se suma e. Máximo tres refinamientos, con
rechazo de singularidad, no finitos, estancamiento o presupuesto agotado.
Sin fallback a LU completa, proyección de filas, descarte o cambio de GMIN.
No cambian dispositivos, contactos, fuentes, h ni gates de Newton.

## Sistema fallido y precisión independiente

El sistema RFSCHJ01 anterior conserva exactamente J/b y ambas
correcciones rechazadas. Una corrección de refinamiento baja el error
mixto de1.2834486e-10 a7.0571908e-17. Decimal100 con los operandos
binary64 exactos confirma el gate en458 filas. Dos ejecuciones reproducen
los mismos bytes y salida. [Replay](../evidence/voice_schur_refined_saved01.json).
Los recibos de rechazo anteriores permanecen intactos.

En el banco84, guardar J/b/correcciones de cada resolución como una lista
ordenada de coeficientes exactamente no nulos permite auditar todos los
operandos sin una exportación densa de cientos de MiB.
**396 sistemas/181368 filas lineales únicas** pasan Decimal100.
La segunda variante repite esta auditoría sobre trazas idénticas: no
duplica el conteo de cobertura única.

| Observación | Schur refinado | LU completa refinada |
|---|---:|---:|
| Solves sin refinamiento | 376 | 374 |
| Solves con un refinamiento | 20 | 22 |
| Solves con dos/tres | 0 | 0 |
| Máximo mixto Decimal100 | 8.29059e-12 | 9.52397e-12 |
| Gate | 1e-11 | 1e-11 |

La LU completa refinada es otro contraste explícito: reutiliza la función
LU original sobre cada RHS de residuo. Su corrección original sin refinar
también queda guardada y se compara a2 nV/2 pA. Diferencia máxima de Schur:
0.000990670 del gate.22 sistemas de esa referencia cruda siguen fallando
con el residuo que incluye error de producto; no se reinterpretan sus
rechazos anteriores como aprobados.
[Banco denso](../evidence/voice_schur_refined_bank01.json) y
[banco con soporte](../evidence/voice_schur_refined_bank02.json).

## Puertos, carga y raíces

336 candidatas de integrado:1680 observaciones de memoria y2016
corrientes de terminal/suelo pasan. Máximo de memoria6.77626e-12 del
gate y corriente4.33681e-19 A frente a20 pA. C4/C3/C5 y L2/L3 permanecen
en los estados completos; la evaluación DC de corrientes no es un solve
DC ni prueba balances integrados de una trayectoria nueva.

84 raíces reconstruidas pasan38472 ecuaciones nuevas del grafo/FD/Q
Decimal100 original. Máximo residual0.000735520 del gate y corrección
1.33894e-6. Los candidatos/incrementos difieren como máximo8.52929e-9
del gate2 µV/2 nA respecto de LU cruda. No heredar esta cobertura por
cercanía respecto de las raíces del bloque anterior.
[Grafo](../evidence/voice_schur_refined_roots01.json).

Doce regresiones finitas: nueve de estructura/pivotes/puertos cargados y
rechazos previos, más no finitos, capacidad y presupuesto. El presupuesto
cero usado para inducir rechazo sólo pertenece al test privado; la
variante pública mantiene tres. [Regresiones](../evidence/voice_schur_refined_structure01.json).

## Dos mediciones de costo, sin admisión temporal

Warmup separado y cinco rondas alternadas; diagnóstico, exportación,
replay y refinamiento de la referencia adicional fuera del timing.
El comparador del benchmark sigue siendo la LU anterior sin refinar.

| Ronda | Residuo denso | Soporte exacto |
|---|---:|---:|
| 1 | 0.908955× | 0.985599× |
| 2 | 0.908267× | 0.957106× |
| 3 | 0.966508× | 0.893128× |
| 4 | 0.779466× | 0.949607× |
| 5 | 0.889630× | 0.939316× |
| Mediana | **0.908267×** | **0.949607×** |

[Primera medición](../evidence/voice_schur_refined_bench01.json) y
[segunda](../evidence/voice_schur_refined_bench02.json). El índice exacto
evita recorridos repetidos de la matriz; sus operaciones conservan el
orden y los coeficientes.84 raíces y toda la traza de396 J/b/correcciones
coinciden por bytes entre variantes. Capacidad fija4096; máximo observado
2240. El exceso se rechaza antes de factorizar, sin truncar. El límite
es dominio del laboratorio, no una cota universal de otros circuitos.

El gate de estabilidad lineal quedó resuelto en este banco. **La utilidad
de costo no pasa; no se abre una nueva campaña temporal.** La voz aceptada
sigue usando la LU anterior. Sin audio, duración, biblioteca o SPICE nuevos,
sin identificación física ni admisión RT.248 tests Rust heredados por
identidad, no reejecutados. [QA](../evidence/voice_schur_refined_tests01.json).

## Siguiente bloque

Medir por separado preparación/factorización, sustituciones y residuo
para localizar el costo pendiente antes de otra variante. Preservar los
resultados de ambas; contrastar cualquier optimización con la traza
completa y sus gates. Sólo una variante que pase precisión y utilidad
abre el contrato de trayectoria, balances, eventos y restores.
