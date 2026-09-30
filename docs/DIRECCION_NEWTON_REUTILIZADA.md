# Reutilización de la dirección Newton aceptada

## Transformación y condiciones

El [criterio de voltaje temporal](CRITERIO_VOLTAJE_TRANSITORIO_GLOBAL.md) calcula la dirección del candidato durante la búsqueda para comprobar su Jacobiano y, cuando KCL ya pasa, el descenso de corrección. Al aceptar ese candidato, la iteración siguiente volvía a factorizar **el mismo J y el mismo residual**.

Se conserva su dirección ordenada junto al residual/J ya cacheados. En la iteración siguiente se reutiliza antes de permutar a orden documental. Es local a **una llamada** de `solve`, con parámetros, fronteras, tasa e historiales de capacitores inmutables. No se guarda en `State`, no cruza muestras ni reintentos, no reutiliza candidatos rechazados y comienza vacía en cada llamada. La feature `solver-uncached-direction` mantiene el cálculo anterior para contrastes.

La transformación no altera semiconductores, topología, Euler, los gates KCL <10 pA/corrección <10 nV, presupuesto 16/16 ni publicación atómica. El caso histórico `solver-kcl-only-transient` no produce dirección de candidato y conserva su ruta sin ese caché. Son arrays fijos, sin heap, IO ni sincronización.

## Equivalencia y recursos

Dos builds release del mismo código, uno con `solver-uncached-direction` y otro por defecto. Se repiten las 28 escenas de [apagado VCA](APAGADO_VCA_GLOBAL_66.md), con 7104 pasos aceptados, cuatro fallos abruptos y 96 capturas completas.

[Comparación exacta](../evidence/circuit66_direction_trace_comparison.json): **23224 valores f64 idénticos en bits IEEE-754**, incluidos ceros con signo, y 308 escalares iguales. Sólo se excluyen metadatos de compilación/entorno. Incluye fronteras, residuales máximos, iteraciones, fallos, nodos actuales/anteriores y los 18 historiales de capacitores de las sondas. No se normalizan ni redondean datos para compararlos.

Pasan las seis regresiones globales tanto en el candidato como en `solver-uncached-direction`: 14 puntos DC, 96 raíces de apagado, 192 sondas de estrés, las dos rutas de 128 pasos contra Python y 128 pasos R20 exacto, junto a rechazo atómico/Jacobianos. El máximo de apagado se mantiene en 0,149686 nV. También pasa heap cero. El estrés largo de la política estricta sigue como evidencia del bloque anterior; esta comparación de caché no afirma una nueva integración independiente de 752384 muestras.

Cinco [pares de costo alternados](../evidence/circuit66_direction_cache_comparison.json), sin builds durante las mediciones: **3,84444→2,95328 ms por bloque**, reducción **23,1805 %**. Cero fallos de convergencia, 640/640 bloques fuera de 1,3333 ms, peor bloque candidato 3,7917 ms. La comparación completa de 8192 muestras contra la partición pasa sus gates. Esta mejora conserva la precisión más estricta; no se compara causalmente con las cifras de otros cortes o corridas.

El [banco Win64 de 512 KiB](../evidence/circuit66_stack_cached_voltage_512.json) pasa 32768 pasos con DC dentro/fuera, reintentos y rechazos atómicos. Observa 324 KiB comprometidos (300 normales +24 guardas), con 188 KiB sin commit. No establece pico exacto ni margen de host. C7 y C6 siguen abiertos.

## Reproducción

```powershell
cargo test -p rf-d-circuit --test cutoff_ladder_output
cargo test -p rf-d-circuit --test no_alloc
cargo test -p rf-d-circuit --features solver-uncached-direction --test cutoff_ladder_output
cargo build --release -p rf-d-circuit --example bench_ladder_recovery_output --features solver-uncached-direction
Copy-Item -LiteralPath target/release/examples/bench_ladder_recovery_output.exe -Destination target/release/rf_d_uncached_voltage.exe
cargo build --release -p rf-d-circuit --example bench_ladder_recovery_output
./tools/compare_circuit66_variants.ps1 -Baseline target/release/rf_d_uncached_voltage.exe -Output evidence/circuit66_direction_cache_comparison.json -Runs 5
python tools/compare_circuit66_direction_traces.py --left evidence/circuit66_vca_release_uncached_survey.json --right evidence/circuit66_vca_release_cached_survey.json --output evidence/circuit66_direction_trace_comparison.json
```

Las dos capturas de rampas se produjeron mediante `circuit66_admission --vca-release` en cada build; sus metadatos conservan hashes de ejecutable y fuentes. Sus cuatro fallos históricos permanecen como limitación, aunque la comparación entre variantes pase.

RACE: reutilizar resultados exige demostrar identidad de estado, frontera y orden de cálculo. Un caché local de Newton puede eliminar una factorización sin introducir un estado DSP nuevo.
