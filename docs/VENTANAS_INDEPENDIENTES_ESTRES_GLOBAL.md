# Ventanas independientes de la traza larga

## Método y procedencia

El [estrés largo](ESTRES_LARGO_GLOBAL_66.md) conserva convergencia e historial en 752384 muestras. Se añaden **48 ventanas de cuatro pasos** resueltas por Python, con Jacobiano completo por diferencias finitas y eliminación independiente. Mantienen la red nominal de SVC-9 Fig. 9-11, 9-8 y 9-17, Ebers–Moll de ambas junturas, diodos y Euler implícito.

Para cada tasa y R61 se capturan dos muestras anteriores y dos desde cada cambio de 250 ms entre 0,25 y 1,75 s, más una ventana a 1,9 s. Hay ocho ventanas por escenario, seis escenarios y **192 pasos independientes**. Las fronteras son las registradas por Rust, en voltios, ohmios y segundos; no se recomputan con funciones trigonométricas Python que podrían mover un switch una muestra.

El historial inicial de cada ventana procede del estado nativo de la traza larga: 66 nodos, estado previo del predictor, 17 voltajes capacitivos, C10 y BUS anterior. Python usa ese mismo historial eléctrico al principio; después integra sus cuatro pasos consecutivos. El contraste cubre la trayectoria corta condicionada a ese historial. La integración completa de los dos segundos sigue perteneciendo a la ruta Rust y su auditoría KCL.

El oráculo de 62/66 nodos admite ahora `R14=None` para la apertura de laboratorio de C10: elimina la corriente de la rama y conserva exactamente el voltaje almacenado. Los demás capacitores siguen conectados. La API mantiene la validación de posiciones/capacitancias. Los 128 pasos anteriores de cutoff y 192 de la ruta de 62 nodos regeneran exactamente; no se modificaron sus criterios ni fixtures.

## Gates fijados y resultados

El generador `tools/circuit66_stress_probes.py` fija, antes de resolver, nodos/J7/voltajes capacitivos <1 µV, cola <1 nA y KCL Python <100 pA. Rust conserva KCL <10 pA; su regresión exige además C18 <0,1 µV, HI/LO <1 µV y conservación exacta de C10 desconectado. Son cotas de equivalencia numérica, sin comparación sonora vintage.

| Medida frente al oráculo | Máximo |
| --- | --- |
| Voltaje de los 66 nodos | 0,204625 µV |
| J7 | 0,397665 nV |
| C10/C18/C19/C15/C21 | 0,847020 nV |
| Corriente de cola | 0,000203759 pA |
| KCL del oráculo | 99,2700 pA |

El máximo interno aparece en TAIL (nodo 5), R61=200 Ω, 44,1 kHz, muestra 11026, tras el primer cambio de switches/cargas. Pasa el umbral de 1 µV. El gate se conserva.

Archivos:

- `evidence/circuit66_stress_probe_inputs.json`: captura nativa y fronteras exactas.
- `evidence/circuit66_stress_probe_vectors.json`: resultados Python, hash de entrada, cotas y máximos.
- `tests/test_circuit66_stress_probes.py`: regeneración exacta y conservación de C10 abierto.
- `crates/rf-d-circuit/tests/cutoff_ladder_output.rs`: 192 pasos Rust desde los historiales capturados, contra todos los nodos y salidas Python.

Son datos numéricos sintéticos del modelo provisional. Semiconductores, rails y fuentes de control mantienen sus incertidumbres. Falta refinamiento temporal, panel completo, parámetros de otras poblaciones, sesiones más largas, stack y deadlines del host. Estas ventanas amplían C5 para la escena declarada; C6/C7 permanecen abiertos.

## Reproducción

Con la captura congelada, CI sólo debe regenerar los vectores Python o ejecutar los tests; no necesita recalcular dos segundos de audio en cada test. Recapturar crea una nueva entrada con su hash y exige volver a contrastar el resultado.

```powershell
cargo build --release -p rf-d-circuit --example bench_ladder_recovery_output
./tools/run_circuit66_stress.ps1 -CaptureProbes -Output evidence/circuit66_stress_probe_inputs.json
python tools/circuit66_stress_probes.py
python -m unittest tests.test_circuit66_stress_probes tests.test_cutoff_j7_vectors tests.test_ladder_j7_closed_loop_vectors tests.test_headphone_coupled_transient_reference -v
cargo test -p rf-d-circuit --test cutoff_ladder_output -- --nocapture
```

Lección para RACE: las ventanas alrededor de eventos permiten contrastar un solver independiente con un historial eléctrico declarado sin depender de una integración independiente de toda la sesión. Registrar el origen de ese historial y la duración efectiva del contraste evita atribuir más evidencia de la obtenida.
