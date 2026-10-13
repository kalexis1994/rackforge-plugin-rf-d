# Cadena cargada condensada con puertos compartidos

2026-10-13. [Protocolo previo](SCHUR_CADENA_PROTOCOLO.md) y
[contrato temporal](SCHUR_CADENA_TRAYECTORIA.md). Una nueva partición lineal,
con red, dispositivos, controles, masas y controlador originales.

## Derivación y carga

SVC-9 Fig. 9-11 p. 13 (placa 4), Fig. 9-8 p. 10, Fig. 9-17 p. 19,
tablas7-8 pp. 30–31; SVC-204D §2.9/2.10 pp. 12–14. Se conservan
[derivación, conflictos e hipótesis](CONTORNO_CADENA_94_Y_ESTABILIDAD.md)
y el [ensamblaje conjunto](../crates/rf-d-circuit/src/joint_voice.rs).
No añade parámetros físicos ni extiende su identificación vintage.
Alimentaciones, cutoff, Q21 y otras fronteras permanecen condicionadas.

132 correcciones de cadena: nodos133..199 salvo165, ambas etapas Radau.
Retener BUS12 y base Q18/165 en el exterior, también241/394 de segunda
etapa, permite condensar cadena y contorno como bloques independientes.
R59=68 kΩ, salida del seguidor, carga del VCO, ladder, recuperación,
VCAs y salida conservan sus ramas y corrientes. Las guardas comprueban
acoplamientos en ambas direcciones; no se permite una conexión ajena.

| Partición | Interiores | Exterior | Estado físico |
| --- | ---: | ---: | ---: |
| Dos LM741 + contorno | 186 | 272 | 229 HIGH/LOW |
| Dos LM741 + contorno + cadena | 318 | 140 | 229 HIGH/LOW |

Resolver A132 con sus cuatro RHS de puerto, añadir −CA132⁻¹B al Schur
común y reconstruir las132 correcciones interiores después del solve
exterior. Se reconstruyen las458 correcciones antes de evaluar/publicar.
Conservar masas cruzadas, cargas de dispositivo e historia de cada etapa.
Tres refinamientos, soporte4096, τ=2 nV/2 pA y gate mixto1e-11 sin cambios.
Factores nuevos por J; reutilización sólo para RHS del mismo J. Sin unsafe,
heap nuevo, cache entre trials, fuente de loudness o fallback.
[Receta](../tools/prepare_schur_chain.py).

## Utilidad marginal confirmada

84 parejas congeladas ON/OFF, máximos2/1 µs y coarse/mid/end. Control
pareado: Schur con contorno admitido; LU completo verifica el packet y
candidatos independientemente. Warmup separado, cinco rondas alternadas.

Mediana inicial **1.0298753×**; confirmación única del
mismo ejecutable/packet **1.0264529×**. Una ronda
inicial queda por debajo de1: conservar toda la distribución. Ambas
medianas pasan la regla previa; la ganancia es moderada en esta plataforma.
[Banco](../evidence/voice_schur_refined_chainbench01.json) y
[confirmación](../evidence/voice_schur_refined_chainconfirm01.json).

## Banco independiente y regresiones

396 J/b/correcciones y contraste LU crudo/refinado; **181.368 filas lineales
únicas reejecutadas con Decimal100**. Peor residuo mixto
**8.04676062E-13 ≤ 1e-11**.
376 solves sin refinamiento adicional y20 con uno. Máximo contraste LU
crudo 0.00099066991 del gate2 nV/2 pA. La referencia
cruda conserva sus rechazos de residuo; la refinada pasa.
1.680 observaciones de memoria LM741 y2.016 corrientes de terminales/masa
pasan sus gates previos. [Banco/replay](../evidence/voice_schur_refined_chainbank01.json).

84 raíces nuevas/38.472 ecuaciones pasan el grafo/FD/Q Decimal100:
[raíces](../evidence/voice_schur_chain_roots01.json). Se reejecutan, sin
heredar por cercanía. 45 regresiones/replay:25 de estructura,9 LU/RHS,
11 de workspace. Incluyen dos etapas cargadas de cadena, puerto compartido
con contorno, masa cruzada, pivote/singularidad local, conexiones ajenas
y recuperación después de un rechazo. [Regresiones](../evidence/voice_schur_refined_chainstructure02.json).

El primer driver completa estructura y LU/RHS, pero agota stack al entrar
al workspace. Fallo y replay conservados antes de separar sus frames:
retornar del driver estructural no inlineado antes de ejecutar las pruebas
del workspace. Mismos32 MiB, casos, inputs, solver y gates. No se repara
el problema aumentando stack ni cambiando operaciones de producción.
[Rechazo](../evidence/voice_schur_refined_chainstructure01.json) y
[reparación](../evidence/voice_schur_chain_driver_repair01.json).

## Cuatro recorridos temporales propios

Misma ventana8.438→11.442 ms, desde cada historia/propuesta registrada.

| Final decay | h máximo µs | Accepted | Wall del perfil s |
| --- | ---: | ---: | ---: |
| ON | 2 | 3020 | 106.1379 |
| ON | 1 | 3704 | 120.8801 |
| OFF | 2 | 2987 | 104.8858 |
| OFF | 1 | 3674 | 118.3007 |

Campaña451.349188 s, con I/O y replays. Los walls no son un benchmark
pareado con campañas históricas. [Nativo](../evidence/voice_schur_chain_native01.json).
**38.472 ecuaciones temporales nuevas**, adicionales al banco de raíces;
13385 accepted/26770 finos,24 restores,368 avances
repetidos,16 corrupciones y8 rollbacks. Cargas, corrientes, balances,
propuestas, LTE, contactos y resets pasan los gates previos.

48 contrastes por control de las229 coordenadas al mismo reloj:

| Control | Máximo V | Máximo A | Ratio gate2 µV/2 nA |
| --- | ---: | ---: | ---: |
| LU original | 8.51699435e-13 | 5.05371330e-17 | 4.25849718e-07 |
| Schur con contorno | 3.18660552e-14 | 2.57940749e-17 | 1.59330276e-08 |

Refinamiento2/1 µs: máximo0.09377758 del gate.
Resets y periodo pasan10 ns; balances por1 pA×duración. Unión con el tramo
previo y ciclo entre resets admitidos. [Auditoría](../evidence/voice_schur_chain_trajectory01.json).

## Perfil del conjunto reducido

[Contrato del observador](SCHUR_CADENA_PERFIL_PROTOCOLO.md). Copia privada
instrumentada, fuera del benchmark y del kernel público; identidad1834
campos, iteraciones y trials de84 parejas frente al kernel intacto.
Tiempos anidados, con overhead del observador; no sumarlos ni atribuir
sus diferencias a copias/heap del binario sin prueba adicional.

| Fase | Total ms | Calls |
| --- | ---: | ---: |
| step | 865.2446 | 84 |
| linearize | 434.8525 | 460 |
| parts | 237.0814 | 856 |
| solve | 236.3446 | 396 |
| prepare | 217.7025 | 396 |
| support | 64.4494 | 396 |
| factor64 | 7.9590 | 792 |
| factor58 | 3.9211 | 396 |
| factor132 | 18.6581 | 396 |
| factor140 | 25.6084 | 396 |
| rhs64 | 21.7716 | 8752 |
| rhs58 | 2.6448 | 1208 |
| rhs132 | 20.6257 | 2000 |
| rhs140 | 5.0286 | 416 |
| correction | 13.8404 | 416 |
| residual | 2.5821 | 416 |

Linearize representa50.26% del step y
solve27.32%; prepare92.11% del solve.
El perfil inicial y su replay rechazan el supuesto parts=2×linearize:
64 trials retornan desde la primera etapa, sin ejecutar la segunda.
El observador corregido confirma460 linearize,856 parts,396 solves,
64 rechazos0 y0 rechazos1, conservando todos los bits. Es una reparación
de conteo, sin cambios eléctricos o del motor temporal.
[Reparación declarada](SCHUR_CADENA_PERFIL_REPARACION.md) y
[perfil corregido](../evidence/voice_schur_refined_chainprofile02.json).

## Admisión y siguiente bloque

**Cadena condensada admitida para esta ventana condicionada de laboratorio**.
[QA](../evidence/voice_schur_chain_tests01.json) conserva fuentes/privados
anteriores;248 tests Rust heredados por identidad, no reejecutados.
Sin biblioteca/SPICE, duración/audio nuevos, contorno desde silencio,
periodicidad asintótica, identificación física o DSP/RT admitidos.

El próximo bloque debe revisar el ensamblaje de Radau y la construcción
del Jacobiano en ubicación final, según el costo observado. Conservar
orden, filas, masas, puertos y rechazos tempranos; exigir identidad de
matriz/RHS y raíces antes de medir utilidad. No añadir otra condensación
por la sola reducción de dimensiones ni elegir una variante sin medición.
