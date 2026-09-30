# Corrección de voltaje en el paso temporal global

## Política y alcance

El [barrido de apagado](APAGADO_VCA_GLOBAL_66.md) demostró 20/96 sondas con error interno >1 µV aun cumpliendo KCL. El máximo era 1,318 mV en los emisores comunes del segundo VCA. Se extiende al paso temporal la política de [corrección DC](DC_GLOBAL_SEMILLA_COMPLETA.md): **KCL <10 pA y corrección Newton completa <10 nV**, con las 66 ecuaciones y los mismos historiales de capacitor durante todos los candidatos/reintentos.

La ley Ebers–Moll, diodos, topología, Euler, tasa, fronteras y parámetros documentales no cambian. El nuevo umbral es numérico, 100 veces menor que el gate interno de equivalencia de 1 µV. No añade smoothing, mute o recorte eléctrico. Después de cumplir KCL, la línea sólo acepta candidatos que mantengan ese gate y reduzcan el máximo de corrección. Antes, reduce KCL. Se rechaza un candidato con J no resoluble antes de publicar el estado. Se mantienen 16/16, el predictor y su reintento desde el último estado.

La feature `solver-kcl-only-transient` conserva la política histórica temporal para contrastes; DC mantiene su criterio de voltaje en ambas variantes. La feature no es un modo de calidad de producto ni una admisión de sus errores cerca de apagado. La corrección `J⁻¹r` es una estimación local; no prueba unicidad ni fidelidad física.

## Gates numéricos

La regresión usa las 96 raíces independientes históricas con el mismo historial entrante, no raíces suministradas por el nuevo solver. **Máximo interno 0,149686 nV**, sin relajar el gate de 1 µV. También pasan capacitores, C10 y J7. En los 128 pasos completos anteriores contra Python: máximo interno 10,71 nV, J7 0,05705 nV. Pasan la suite Rust completa, Jacobianos, R20 exacto, rechazo atómico, predictor y heap cero.

La [nueva captura de rampas](../evidence/circuit66_vca_release_voltage_survey.json) conserva 7104 pasos aceptados y cuatro saltos abruptos fallidos. El [diagnóstico independiente](../evidence/circuit66_vca_release_voltage_probe_vectors.json) pasa las 96 sondas de las rampas: KCL <10 pA y corrección estimada <10 nV. Su refinador parte del candidato capturado y ya no necesita moverlo; ese error interno cero es una auditoría de convergencia, **no integración independiente ni prueba de exactitud absoluta**. La cifra de equivalencia útil es la comparación de 0,149686 nV contra las raíces históricas refinadas.

El [estrés largo repetido](../evidence/circuit66_long_stress_voltage.json) acepta 752384 muestras a 44,1/48/96 kHz en ambos R61, sin fallos ni reintentos. Pasa 11756 auditorías de KCL y 188084 comprobaciones de C10 abierto. No se afirma oráculo independiente de todo ese recorrido.

## Costo y recursos

Cinco [pares alternados](../evidence/circuit66_transient_voltage_comparison.json), release/Ryzen 5 5600X/Rust 1.97.0: **2,32644→3,93914 ms por bloque de 64**, aumento **69,3205 %**. Cero fallos, 640/640 bloques candidatos fuera del deadline de 1,3333 ms, peor bloque 5,7755 ms. El contraste de 8192 muestras contra la partición también pasa sus gates (J7 21,4848 nV, interno 1,32184 µV bajo su gate específico de 2 µV). Las factorizaciones adicionales explican una parte del costo; esto no admite tiempo real.

Los [workers Win64 de 512 KiB](../evidence/circuit66_stack_voltage_512.json) pasan 32768 pasos/reintentos/rechazos atómicos, con **320–324 KiB comprometidos**, incluidas guardas de 24 KiB. No se mide el pico exacto ni el host. C7 sigue abierto; C6 no cambia.

Se conserva la ruta más precisa como referencia experimental. Próximo corte de costo: reutilizar la dirección Newton ya calculada para el candidato aceptado, comprobando que no cambie el resultado. Saltos Q21 a cero, semillas DC, R21 exacto y el contorno real siguen pendientes.

```powershell
cargo test --workspace
python -m unittest discover -s tests -p test_circuit66_vca_release_probes.py -v
cargo build --release -p rf-d-circuit --example bench_ladder_recovery_output --features solver-kcl-only-transient
# Preservar el ejecutable de referencia en target/ antes del build siguiente.
cargo build --release -p rf-d-circuit --example bench_ladder_recovery_output
./tools/compare_circuit66_variants.ps1 -Baseline target/release/rf_d_kcl_only_transient.exe -Output evidence/circuit66_transient_voltage_comparison.json -Runs 5
```

RACE: aceptar KCL y precisión de voltaje son gates distintos. El pequeño error de un jack no justifica ocultar errores grandes en un nodo interno, ni el aumento de costo de corregirlos.
