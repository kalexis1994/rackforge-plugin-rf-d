# Menor costo conservando ecuaciones, puertos y cargas

## Dos cambios en una familia pública explícita

[block_decay_voice](../crates/rf-d-circuit/src/block_decay_voice.rs) ensambla
el Jacobiano458×458 por sus cuatro cuadrantes229×229, con la misma expresión
por entrada, multiplicación/suma y +0 fuera de diagonal. [block_decay_engine](../crates/rf-d-circuit/src/block_decay_engine.rs)
mantiene el motor temporal, estados, eventos y API de decay anterior.
Se conservan fuentes nominales/controladas por bytes; lib.rs añade exports.

[block_decay_solver](../crates/rf-d-circuit/src/block_decay_solver.rs) verifica
conexiones sobre las entradas no nulas de CSR ya construido, con masks
OWNER/ALLOWED derivadas de los mismos interiores y puertos. Comprueba ambas
direcciones, incluidos puertos compartidos y ambos stages. Recalcular CSR
desde J real en cada preparación; no patrón de preset, threshold o cache
entre iteraciones. Finitud/capacidad/LU/Schur/refinamiento/pivote y gates
quedan intactos. No se elimina masa ni se omite una carga del circuito.

[Protocolo inicial](VOZ_COSTO_PIVOTE_PROTOCOLO.md),
[cuadrantes](VOZ_COSTO_BLOQUES_PROTOCOLO.md) y
[política CSR](VOZ_COSTO_SOPORTE_PROTOCOLO.md), fijados antes de cada medición.

## Perfil y candidatos rechazados por costo

Banco78:54 pares seleccionados a1 kΩ y24 nominales a100 kΩ, con old458 HIGH/LOW,
h y1834 f64 históricos completos por par. Nominales incluyen iteraciones y
trials históricos; en seleccionados se contrastan entre ejecuciones actuales.
No atribuir esos dos campos a un export que no los capturó.

[Perfil](../evidence/voice_pivot_bench01.json) conserva todos los bits. Tiempos
anidados: initialize56.07 % de step, parts36.01 %, joint_parts27.60 %;
solve37.60 % y prepare34.39 %. No sumar fracciones superpuestas. Instrumentación
de clocks/atomics sólo en copias del laboratorio, ausente del motor público.

Omitir pivotes exactamente nulos pasa números, pero falla costo: mediana
1.030818×baseline. Cuadrantes pasan en laboratorio (0.897892×), pero la primera
biblioteca pública sólo alcanza0.929573× y falla el gate0.90. Ambas versiones
y mediciones quedan conservadas; un resultado del laboratorio no admite
automáticamente el costo de la API portable. No se afloja el umbral.

## Verificación y utilidad públicas

[Biblioteca pública2](../evidence/voice_block_library02.json): compara **16.468.764
entradas f64 del stamp** (residuo, Jacobiano y candidatos) y todos los campos
de78 pares/contadores por bits. No es una auditoría independiente del grafo.
La política densa original y las masks coinciden en **209.764 posiciones**,
en ambas direcciones de cada arista posible. Seis fixtures ejercen rechazo
de matriz/RHS inválidos, soporte, singularidad y overflow, con mismo tipo
de error. Las ecuaciones y aritmética de eliminación siguen siendo originales.

Cinco rondas alternadas en mismo proceso/banco: ratio de medianas
**0.800968304**, reducción19.903 %;
peor ronda0.812226002. Pasan0.90/1.05 declarados. Es costo
de step en corpus finito y plataforma Rust GNU actual, sin deadline, comparación
de productos o promesa de ese porcentaje para todas las escenas.

## Cada avance, historia y carga en la API pública

[Campaña pareada pública](../evidence/voice_block_portable01.json),28.442→32.442 ms,
4 ms ya cubiertos por la referencia propia a1 kΩ. Desde cada checkpoint
postevento original, sin warmup, nueva raíz, controles o reloj distintos.
En cada Accepted comparar coarse/mid/end, estados e incrementos, residuos,
correcciones, iteraciones/trials, LTE/intentos/half, observables y checkpoint
lógico completo por bits. Rechazo de destino preserva ambos motores.

| h máximo µs | Accepted | Endpoints finos | Baseline kernel s | Candidato kernel s | Ratio |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 3879 | 7758 | 78.783104 | 65.408581 | 0.830236 |
| 1 | 4842 | 9684 | 90.318500 | 74.614073 | 0.826122 |

**8721 Accepted/17442 endpoints** públicos
coinciden,12 estados completos incluyendo entradas. Tiempos son sumas del
motor, excluyen dump/ledger/IO; el ratio agregado es0.828038593,
reducción17.196 %. Una campaña finita no mide plazo del
callback del host. El orden de esta campaña es baseline primero; el gate de
utilidad corresponde a las cinco rondas alternadas del banco, no a esta suma.

[Auditor de prefijo/cargas](../evidence/voice_block_portable_reference01.json):
todo STEP/OBS/GRID y458 valores en sus cortes coinciden por bytes con el
prefijo4 ms admitido de la campaña anterior. También coincide con el
[laboratorio pareado](../evidence/voice_block_paired_reference02.json), con
8721 Accepted adicionales comparados antes de publicar.
Integrales orientadas y checkpoints finales son idénticos. Nueve ΔQ se
recalculan con Decimal100 entre extremos reales y pasan1 pA·duración.

Se heredan8244 ecuaciones no lineales independientes correspondientes
a selecciones anteriores del prefijo; **cero nuevas** reejecutadas. La igualdad
no convierte todos los Accepted en solves independientes. Banco, predicado
estructural, comparación entre motores y grafo original son pruebas distintas.

## Fuentes y rechazos conservados

El [primer colector](../evidence/voice_pivot_layout_failure01.json) calculó
correctamente records de18368 bytes pero exigía18384; el fallo y replay se
conservan y se corrige sólo la longitud declarada. La [primera compilación
pareada](../evidence/voice_block_paired01.json) y replay rechazaron un comentario
interno Rust después de un item; [reparación de posición](../evidence/voice_block_paired_repair01.json)
sin cambios numéricos. Las [fuentes del candidato público1](../evidence/voice_block_library_rejected01.json)
se conservan con hashes comprobados, junto con su biblioteca y costo rechazado.

[QA](../evidence/voice_block_tests01.json) protege toda la línea anterior.
255 tests Rust y2 definiciones Python heredadas por identidad, sin reejecución;
checks nuevos de bancos, política, costo, Accepted/cargas y API portable se
cuentan por su alcance. Sin Cargo/cache/SPICE nuevos. Dos rlibs experimentales,
stack32 MiB; sin heap o uso máximo de stack nuevos medidos.

## Reproducir y siguiente

[Ejemplo público pareado](../crates/rf-d-circuit/examples/block_decay_verify.rs),
con la biblioteca actual y el checkpoint postevento de [decay control](DECAY_CONTROL_RESULTADOS.md):

```powershell
& $recipeRustc --edition=2021 --crate-name rf_d_circuit --crate-type rlib -C opt-level=2 -C debuginfo=0 crates/rf-d-circuit/src/lib.rs -o tmp/decay-usuario/librf_d_circuit-bloques.rlib
& $recipeRustc --edition=2021 -C opt-level=2 -C strip=symbols -C 'link-arg=-Wl,--stack,33554432' crates/rf-d-circuit/examples/block_decay_verify.rs --extern rf_d_circuit=tmp/decay-usuario/librf_d_circuit-bloques.rlib -o tmp/decay-usuario/bloques.exe
& ./tmp/decay-usuario/bloques.exe tmp/decay-usuario/recorrido/phase0-start.ckp tmp/decay-usuario/pareado-bloques
```

No nueva duración o WAV: los36 ms anteriores siguen siendo escucha de la
referencia anterior, no un render nuevo completo del motor optimizado.
Sólo4 ms por resolución se reejecutan/contrastan aquí. Siguiente: usar esta
familia para avanzar a un render más largo con controles y cargas reales,
conservando el contraste. No voz completa, fidelidad física o RT admitidos.
