# Contorno cargado condensado: resultados

2026-10-13. Una nueva partición del Jacobiano; red, dispositivos, constantes,
historia y controlador conservados. [Protocolo previo](SCHUR_CONTORNO_PROTOCOLO.md)
y [contrato temporal](SCHUR_CONTORNO_TRAYECTORIA.md).

## Circuito y frontera

Fuentes eléctricas heredadas: SVC-9 p. 9, Fig. 9-7 (contorno/gatillo),
p. 13, Fig. 9-11 (placa 4), p. 19, Fig. 9-17 (panel) y tablas 7-6/7-8,
pp. 26–27/30–31. [Derivación y conflictos](CONTORNO_VOLUMEN_CIRCUITO.md)
y [cierre de R59/Q18](CONTORNO_CADENA_94_Y_ESTABILIDAD.md).
No añade parámetros audibles. Alimentación de contorno impuesta a 9,3 V,
contorno de filtro y otras cargas de placa 2 pendientes; semiconductores
nominales de laboratorio, sin identificación de una unidad vintage.

Los 29 nodos 200..228 del contorno entran juntos en ambas etapas Radau:
58 correcciones internas. La frontera queda en 165/394, base Q18 de
placa 4 por etapa. La salida pin 7 de placa 2, nodo 203, permanece interna
y se reconstruye. R59=68 kΩ conserva su corriente hacia el VCA y la carga
que éste devuelve al seguidor; los terminales de la resistencia no se unen.
Cada preparación verifica acoplamientos en ambas direcciones y rechaza
los ajenos. C2/C7/C4 y las cargas Q25/Q15 conservan masas e historia.

| Solver | Correcciones interiores | Correcciones exteriores | Estado físico |
| --- | ---: | ---: | ---: |
| LU original | 0 | 458 | 229 HIGH/LOW |
| Schur en sitio admitido | 128 | 330 | 229 HIGH/LOW |
| Dos LM741 + contorno | 186 | 272 | 229 HIGH/LOW |

Eliminación sólo dentro de la resolución lineal: reconstrucción de las
458 correcciones antes de evaluar/publicar la raíz. Factores nuevos para
cada J; RHS adicionales del mismo J reutilizan esos factores. Mantiene
tres refinamientos, capacidad exacta 4096, τ=2 nV/2 pA y gate mixto1e-11.
Sin unsafe, heap nuevo, fuente impuesta de loudness o cambio del stamp.
[Receta reproducible](../tools/prepare_schur_contour.py).

## Costo frente al Schur admitido

84 parejas originales ON/OFF, 2/1 µs y coarse/mid/end. El control de
costo es el Schur en sitio; LU completo verifica por separado el packet
y la diferencia de candidatos. Warmup separado y cinco rondas alternadas.

Mediana inicial **1.0229034×**; confirmación única
con el mismo ejecutable/packet **1.0250972×**.
Las diez rondas superan 1. Ganancia moderada en esta plataforma/banco;
no acredita duración musical ni deadline. [Banco](../evidence/voice_schur_refined_contourbench01.json)
y [confirmación](../evidence/voice_schur_refined_contourconfirm01.json).

## Precisión y regresiones nuevas

396 resoluciones guardan J/b/corrección de contorno, LU crudo y LU refinado.
**181.368 filas lineales únicas reejecutadas con Decimal100**; no se heredan
por cercanía. Peor residuo mixto **8.29058719E-12 ≤ 1e-11**. 376 resoluciones
sin refinamiento adicional y 20 con uno. Contraste con LU crudo: máximo
0.00099066991 del gate 2 nV/2 pA. El LU crudo conserva
sus rechazos de residuo; sólo la referencia refinada pasa ese gate.
1.680 observaciones de memoria LM741 y 2.016 corrientes de terminales/masa
pasan. [Banco y replay idéntico](../evidence/voice_schur_refined_contourbank01.json).

84 raíces nuevas pasan **38.472 ecuaciones del grafo/FD/Q Decimal100**.
Se reejecutan, aunque las diferencias con el control sean pequeñas.
[Grafo](../evidence/voice_schur_contour_roots01.json).
35 regresiones/replay: 18 de estructura, 9 de LU/RHS y 8 de workspace.
Incluyen masa cruzada entre etapas del contorno cargado, pivote local,
singularidad, conexiones ajenas de entrada/retorno, entre bloques y
reinicialización tras rechazos locales. [Regresiones](../evidence/voice_schur_refined_contourstructure01.json).

## Cuatro recorridos temporales propios

Misma ventana 8.438→11.442 ms, desde cada historia/propuesta registrada.

| Final decay | h máximo µs | Accepted | Wall del perfil s |
| --- | ---: | ---: | ---: |
| ON | 2 | 3020 | 108.9173 |
| ON | 1 | 3704 | 124.8452 |
| OFF | 2 | 2987 | 107.0326 |
| OFF | 1 | 3674 | 122.6400 |

Campaña 464.504072 s, incluidos I/O y replays. Estos walls no son
una medición pareada con los tiempos históricos. [Nativo](../evidence/voice_schur_contour_native01.json).

**38.472 ecuaciones temporales nuevas**, adicionales
a las del banco de raíces. 13385 accepted/26770 finos,
24 restores, 368 avances repetidos,
16 corrupciones y 8 rollbacks pasan. Cargas, corrientes, balances, propuestas,
LTE, contactos exactos y resets conservan los gates previos.

48 contrastes por control de las 229 coordenadas al mismo reloj:

| Control | Máximo V | Máximo A | Ratio del gate 2 µV/2 nA |
| --- | ---: | ---: | ---: |
| LU original | 8.51704065e-13 | 7.63312079e-17 | 4.25852032e-07 |
| Schur en sitio | 8.02390608e-14 | 4.19076293e-17 | 4.01195304e-08 |

Refinamiento 2/1 µs: máximo 0.09377758 del gate. Resets y periodo pasan
10 ns; balances por 1 pA×duración. La unión con el tramo previo y el ciclo
entre resets pasan. [Auditoría temporal](../evidence/voice_schur_contour_trajectory01.json).

## Alcance y siguiente frontera

**Contorno condensado admitido para esta ventana condicionada de laboratorio**.
[QA](../evidence/voice_schur_contour_tests01.json) protege las fuentes y privados
anteriores. 248 tests Rust heredados por identidad, no reejecutados.
Sin biblioteca/SPICE, duración o audio nuevos, contorno desde silencio,
periodicidad asintótica, identificación física ni DSP/RT admitidos.

La [inspección de la siguiente frontera](../evidence/voice_schur_chain_frontier01.json)
recorre el soporte exacto de los 396 J nuevos: 132 correcciones de cadena
133..199 salvo165, ambas etapas, se conectan sólo por BUS12 y base165
(241/394 en segunda etapa). Sin acoplamientos ajenos en ese banco.
Mantener estos puertos exteriores permite conservar el contorno independiente
y dejar 140 correcciones exteriores. Es una inspección, con cero solves:
invertibilidad interior, precisión, utilidad y trayectoria aún no medidas.
El próximo bloque debe resolver esas cuatro condiciones antes de promover.
