# Schur en sitio: banco confirmado y ciclo condicionado admitido

2026-10-13. Basecf79a8d. Voz229 CA3046 condicionada, sin hardware.
[Contrato del workspace](SCHUR_EN_SITIO_PROTOCOLO.md) y
[contrato temporal](SCHUR_EN_SITIO_TRAYECTORIA.md).

## Construcción y vida de las matrices

Dos interiores64 y exterior330 se llenan directamente en sus buffers
finales y se factorizan mediante &mut. Lu::factor_in_place, initialize
de Prepared y Sparse devuelven Result<()>; no retornan esos agregados
grandes. Workspace local seguro, de tamaño fijo; sin unsafe, heap nuevo
o dependencia de las directivas de inline del intento anterior.

Todo coeficiente de la matriz actual se repone antes de factorizar.
Permutaciones, soporte/escala y diez columnas de respuesta a puertos se
reconstruyen. No hay cache de factores entre Jacobianos distintos ni
publicación de estado ante rechazo. La misma factorización sí resuelve
los RHS de refinamiento de ese J. Mantener orden, tipos, pivotes1e-12,
capacidad4096, tres refinamientos y gate mixto1e-11.

Se mantienen458 correcciones,229 estados HIGH/LOW, ambos LM741 con sus
terminales y retorno a suelo, C4/C3/C5 y L2/L3, masa y resto de cargas.
No cambiar circuito, fuentes, predictor, contactos, Newton o tolerancias.
La API evita retornos grandes por diseño; no se atribuye un número de
copias eliminadas del binario sin otra inspección de compilación.

## Banco y confirmación única

Warmup separado, cinco rondas alternadas contra LU anterior sin refinar.
Ganancia marginal: la política fijada obliga una confirmación única con
el mismo ejecutable y packet, sin recompilar o modificar flags.

| Ronda | Banco | Confirmación |
|---|---:|---:|
| 1 | 1.010602× | 1.010955× |
| 2 | 1.013191× | 1.004208× |
| 3 | 1.008589× | 1.013324× |
| 4 | 1.002318× | 1.017167× |
| 5 | 1.008255× | 1.014678× |
| Mediana | **1.008589×** | **1.013324×** |

Las diez rondas superan1. Utilidad de banco admitida, moderada y específica
de esta plataforma/compilación; no prueba deadline ni una gran aceleración.
[Banco](../evidence/voice_schur_refined_inplacebench01.json) y
[confirmación](../evidence/voice_schur_refined_inplaceconfirm01.json).

84 raíces y toda la traza de396 J/b/correcciones coinciden por bytes
con el Schur estable previo.181368 filas Decimal100 se heredan por
esa identidad, sin reauditar.1680 memorias y2016 corrientes pasan sus
observaciones originales. [Trazas](../evidence/voice_schur_refined_inplacebank01.json).

## Reutilización, errores y driver reparado

26 regresiones: doce de estructura/capacidad/presupuesto, nueve de LU/RHS
y cinco de workspace. Probar cambio de matriz y recuperación después de
NaN, singularidad interior, acoplamiento extraño y exceso de capacidad.
Cada nuevo initialize exitoso reproduce una preparación fresca por bits.
La reutilización de esta prueba no implica cache persistente en el solver.

El primer driver materializa cuatro Jacobianos grandes en un literal y
agota su stack. Dos ejecuciones conservan la misma salida previa y clase
de overflow; fuentes y fallos guardados. Reparar sólo el scratch del
driver: un buffer secuencial, manteniendo32 MiB y el solver intacto.
[Rechazo](../evidence/voice_schur_refined_inplacestructure01.json),
[reparación](../evidence/voice_schur_inplace_driver_repair01.json) y
[26 regresiones/replay](../evidence/voice_schur_refined_inplacestructure02.json).

## Cuatro recorridos nuevos de la misma ventana

Se reejecuta8.438→11.442 ms desde cada historia/propuesta propia, ON/OFF
y máximos2/1 µs. No amplía duración simulada ni parte desde silencio.
Kernel público de banco, runner sin instrumentación y biblioteca congelada.

| Final decay | h máximo µs | Accepted | Wall del perfil s |
|---|---:|---:|---:|
| ON | 2 | 3020 | 111.5180 |
| ON | 1 | 3704 | 126.8733 |
| OFF | 2 | 2987 | 109.9030 |
| OFF | 1 | 3674 | 125.3957 |

Campaña474.890525 s. Estos walls incluyen el recorrido y sus replays/I/O;
no son un benchmark pareado con los tiempos históricos de LU.
[Nativo](../evidence/voice_schur_inplace_native01.json).

**38472 ecuaciones nuevas/168 candidatas seleccionadas** se reejecutan
con el grafo/FD/Q Decimal100; no se heredan por cercanía. Máximos de gates:
residual0.000735653 y corrección1.30671e-6.13385 accepted/26770 finos,
24 restores,368 avances repetidos,16 corrupciones y8 rollbacks pasan.
Balances, propuesta entrante, checkpoints, contacto exacto, LTE y resets
conservan sus gates. Unión con el tramo previo y ciclo entre resets pasan;
no acredita periodicidad asintótica, contorno desde silencio o placa2 completa.

48 comparaciones de229 coordenadas al mismo reloj contra LU: máximo
8.51708e-13 V y7.35903e-17 A, ratio4.25854e-7 del gate2 µV/2 nA.
Entre resoluciones, máximo0.0937776 del gate. Resets/periodo pasan10 ns.
[Auditoría temporal](../evidence/voice_schur_inplace_trajectory01.json).

La adaptación del auditor primero buscó reference02 cuando el recibo
congelado correcto era reference01; fallo/replay preservados antes de
reparar sólo la ruta. El auditor de publicación también conserva un
SyntaxError de cierre de lista y su replay antes de reparar. Ninguno de
esos intentos ejecutó ecuaciones o cambió datos/gates del circuito.

## Admisión y siguiente bloque

**La condensación dinámica queda admitida para este ciclo condicionado
de laboratorio**, con precisión, costo confirmado y recorrido propio.
Los negativos anteriores permanecen conservados. [QA](../evidence/voice_schur_inplace_tests01.json).
248 tests Rust heredados por identidad, no reejecutados. Sin biblioteca,
SPICE, audio o duración nuevos; sin identificación física ni admisión RT.

La ganancia moderada no alcanza duración musical utilizable. El siguiente
bloque debe localizar otra reducción estructural del sistema, conservando
puertos/cargas y contrastando con este recorrido. Mantener fronteras y
brechas de circuito explícitas antes de ampliar tiempo o empaquetar DSP.
