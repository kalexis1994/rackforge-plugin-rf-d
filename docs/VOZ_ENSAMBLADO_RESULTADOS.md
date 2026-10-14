# Ensamblado directo de la voz: familia pública

## Transformación y alcance

La familia `assembly_decay_voice/engine` evita crear un Parts200 intermedio y copiarlo a Parts229. El constructor de parámetros, validaciones, VCO134, cadena68, sus dispositivos, orden de sumas/restas, masa, puertos y contorno son los mismos. BUS12 pertenece a ambos bloques en el mismo solve. La comprobación de finitud del bloque200 precede al contorno. No se fusionan ni omiten operaciones con coeficientes nulos; no cambian parámetros audibles ni discretización. Las familias anteriores permanecen intactas.

Modelo documental vintage CA3046, escena propia condicionada OSC1→BUS→escalera/VCA/J7, KEY0/S abierto/decay ON/R1 kΩ, más los pares nominales R100 kΩ del banco. Revisión y cargas heredadas de `OBJETIVO.md` y `DECAY_CONTROL_PROTOCOLO.md`. Esta comparación no identifica una unidad física ni cubre todas las escenas posibles del Model D.

## Banco de laboratorio y biblioteca pública

168 pares propios. 336 Parts completos (35548128 f64) y168 stamps (35471184 f64) coinciden por bits: **71019312 campos** en total. Además1834 f64 por solve, iteraciones/trials actuales y los counters históricos de24 pares nominales. Doce entradas inválidas de Parts y seis fixtures de solver completo conservan sus rechazos. Se preservan tanto HIGH como LOW, cargas/h, DC, tangentes y candidatos.

| Ejecución | Ratio de medianas | Peor ronda | Utilidad ≤0,95 / ≤1,05 |
| --- | --- | --- | --- |
| Laboratorio | 0.894587704883 | 0.945401173034 | admitida |
| Biblioteca pública | 0.895860582567 | 0.904102612158 | admitida |

La API pública reduce el tiempo del banco 10.413942 %. Cinco rondas alternadas por cada ejecución, mismos inputs/compiler/flags. Workspace de ambas versiones3378208 bytes, sin almacenamiento persistente añadido. El contenedor de200 nodos deja de aparecer en esta ruta; no se infiere de ello un pico de stack/RAM medido ni deadline. Los porcentajes corresponden a este banco y equipo.

Biblioteca `references-local/voice-assembly-public01/librf_d_circuit.rlib`, SHA256 `9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d`; compiler y comandos en [recibo público](../evidence/voice_assembly_public01.json). La primera preparación del laboratorio encontró dos restricciones de acceso a helpers privados. Cada rechazo y replay sin cambios queda conservado en lab01/lab02; reparaciones01/02 corrigen únicamente el binding de laboratorio y el selector de entradas. La copia local de `joint_vco_fine` difiere en dos rutas de importación/datos; su linearize físico no cambia. La familia pública llama al helper original privado de la crate. No se modifica la aritmética para reparar la compilación.

## Trayectoria pública pareada

Dos perfiles1/2 µs,4 ms cada uno:68,442→72,442 ms, desde sus checkpoints propios de la liberación extendida. 6464 Accepted completos y12928 endpoints coinciden por bits entre motores: coarse/mid/end, estados/incrementos, ratios, iteraciones/trials, LTE/intentos, observaciones, relojes y propuesta. Las doce rejillas con458 valores y los checkpoints finales coinciden por bytes. Los cuatro destinos inválidos se rechazan sin mutación (dos familias por perfil).

Todo STEP/OBS/GRID coincide también con el intervalo anterior admitido, no solo con el candidato. Nueve integrales orientadas pasan identidad de suma y ΔQ Decimal100 entre extremos propios. 2748 ecuaciones seleccionadas independientes se heredan de ese intervalo por identidad; ninguna se reejecuta aquí contra el grafo original. No atribuir ese solve a todos los endpoints.

Ratio agregado del kernel pareado 0.920475854723: reducción7.952415 %, excluyendo IO, serialización y ledger. No es un deadline. La campaña completa dura214.600655 s, incluyendo sus comprobaciones. No suma duración de circuito y no produce un nuevo WAV68 ms entero del candidato. La escucha anterior sigue disponible e identificada como anterior.

## Evidencia y siguiente bloque

- [Protocolo previo](VOZ_ENSAMBLADO_PROTOCOLO.md), [entradas reparadas](../evidence/voice_assembly_inputs03.json).
- [Laboratorio](../evidence/voice_assembly_lab03.json), [preparación pública](../evidence/voice_assembly_promotion01.json), [banco público](../evidence/voice_assembly_public01.json).
- [Recorrido](../evidence/voice_assembly_paired01.json), [intervalo anterior y carga](../evidence/voice_assembly_reference01.json), [QA](../evidence/voice_assembly_tests01.json).
- Fallos/replays [lab01](../evidence/voice_assembly_lab01.json)/[lab02](../evidence/voice_assembly_lab02.json), [reparación01](../evidence/voice_assembly_repair01.json)/[reparación02](../evidence/voice_assembly_repair02.json).

Datos y binarios privados ignorados, con presupuesto96 MiB y reserva1 GiB. Sin Cargo/cache ni SPICE nuevos; solo una biblioteca nueva medida y callers de laboratorio. 255 tests Rust y dos definiciones Python heredados sin reejecución; los fixtures y campañas de este bloque tienen conteo propio. Sin heap/deadline nuevos, fidelidad física o RT admitidos.

Siguiente: ampliar la duración real con esta familia desde estados propios, conservando el contraste de cargas, eventos y contorno. No prolongar el WAV anterior por repetición ni cambiar parámetros eléctricos para acelerar el cálculo.
