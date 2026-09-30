# EMPHASIS nativo: retorno C10/R14/R73

## Fuente, dominio y estado

**SVC-9 Fig. 9-11, PDF p. 13** conecta el tap de recuperación R7/R3 al capacitor C10 y la base de Q30; **Fig. 9-17, PDF p. 19** muestra el cableado del potenciómetro EMPHASIS R14. **Tabla 7-8, PDF pp. 30–31** da `C10=10 µF`, `R14=50 kΩ`, `R73=1 kΩ` y `R76=330 Ω`. La [transcripción del retorno](REGENERACION_FILTRO.md) y el [modelo offline de 24 nodos](TRANSITORIO_FILTRO_ACOPLADO.md) documentan la polaridad. El valor de R61 continúa ambiguo entre 200 Ω y 200 kΩ; ambos se prueban. No hay acceso a una unidad física ni parámetros BJT medidos.

`step_with_emphasis` recibe la resistencia **eléctrica** `R14_7→6` en `0..50 kΩ`, no un ángulo de perilla. El `R73_L` desde BOTTOM al wiper se obtiene de `R30−R76` y exige `R30=330..1330 Ω`. El resistor serie desde el tap hasta C10/base es `R_top=R14_7→6+1000 Ω−R73_L`, siempre no negativo. El estado guarda la tensión `u10` del capacitor orientada desde el tap hacia la base Q30. El punto DC abre C10 y fija `u10=V_tap−V_Q30base`. Se puede ejecutar la ruta anterior con C10 desconectado mediante `step`, útil como laboratorio, sin alterar el estado físico de C10.

## Rama implícita de tres puertos

Con Euler implícito, `g10=C10/Δt` en S, `Y10=g10/(1+g10·R_top)` en S e `I10=Y10·(V_tap−V_Q30base−u10,prev)` en A, positivo del tap hacia Q30. El nuevo capacitor vale `u10=V_tap−V_Q30base−R_top·I10`; la prueba comprueba `I10=C10·(u10−u10,prev)/Δt`. Esta eliminación exacta de los nodos de serie admite `R_top=0 Ω`.

El [recuperador nativo](../crates/rf-d-circuit/src/recovery_vca_output.rs) añade `+I10` a KCL del tap y resuelve provisionalmente sus ocho nodos y toda la cadena de salida. Su puerto entrega tres corrientes salientes del ladder: `[I_C5, I_C1, −I10]` y un Jacobiano `3×3` respecto de `[V_ladderL, V_ladderR, V_Q30base]`. Tres términos derechos comparten una factorización del Jacobiano local `8×8`. El [ladder nativo](../crates/rf-d-circuit/src/ladder_recovery_output.rs) estampa esos tres puertos en nodos 11, 15 y 7; Newton acoplado resuelve el lazo y publica C10, ladder, recuperación y salida **atómicamente**. No hay heap en el camino de audio.

## Regresiones y límite

El [oráculo monolítico Python de 62 nodos](../tools/headphone_coupled_transient_reference.py) genera el [fixture BUS→J7](../evidence/ladder_j7_closed_loop_vectors.json) de forma independiente del solver Rust de puertos anidados. Hay cinco pasos por cada escenario de R61 con R14 en `0/25/50 kΩ`, más 192 muestras a 48 kHz y BUS senoidal de 100 Hz/0,1 V para R61=200 Ω; R14 cambia a los 64 y 128 pasos y SW18 conmuta entre 96 y 128. La prueba Rust contrasta los 24 nodos de filtro/recuperación, tensión de C10, J7 y salidas HI/LO. En la traza de 192, error máximo J7 `2,563×10⁻⁸ V`, error máximo de nodos en los ocho checkpoints `8,081×10⁻⁹ V` y razón señal/error **numérica** `115,0 dB`. Es una prueba de equivalencia entre modelos hipotéticos, no de fidelidad con audio vintage. El test del puerto `3×3` coteja diferencias simétricas, y la prueba sin heap añade 40 pasos con C10 cerrado.

El [perfil local congelado](../evidence/ladder_j7_native_profile_2026-09-30.json) registra `--release` en Windows/AMD Ryzen 5 5600X, 8192 muestras medidas tras calentamiento, 48 kHz, bloques de 64, BUS 100 Hz/0,1 V, `R14=25 kΩ`, `R61=200 Ω`: media **22 584,4 µs**, p99 **25 783,4 µs**, máximo **25 832,9 µs**, cero fallos y KCL máximo `4,083×10⁻¹² A`. El plazo es **1333,3 µs**. La medición abierta en C10 de otro lanzamiento tuvo media 24 205,4 µs; esa comparación entre lanzamientos no demuestra que cerrar C10 acelere el cálculo. Antes de usarlo en audio hacen falta una implementación de costo acotado dentro del plazo, mediciones A/B de sus optimizaciones y el resto de la voz (VCO, mezclador, controles).

```powershell
python -m unittest discover -s tests -p test_ladder_j7_closed_loop_vectors.py -q
cargo test --workspace
cargo run --release -p rf-d-circuit --example bench_ladder_recovery_output -- --emphasis
```
