# Ladder nativo unido a recuperación, VCA y J7

## Alcance y fuentes

[`ladder_recovery_output.rs`](../crates/rf-d-circuit/src/ladder_recovery_output.rs) resuelve los 16 voltajes de la placa 4 y conecta los emisores superiores Q2/Q3 a C5/C1, Q5–Q8, ambos VCA, la conversión de salida, panel y J7. La topología se transcribió de **SVC-9 Fig. 9-11, PDF p. 13** (también SVC-204D p. 69); los valores de **tabla 7-8, PDF pp. 30–31**. Las conexiones de salida se documentan en [recuperación nativa](RECUPERACION_SALIDA_NATIVA.md) y [puerto C5/C1](PUERTO_NATIVO_HACIA_LADDER.md). La ley Ebers–Moll simple y sus límites constan en [punto DC del ladder](LADDER_EBERS_MOLL_DC.md). No hay parámetros medidos de una unidad física.

Los cinco resistores de columna son `R4=220 Ω` y `R16/R32/R41/R52=150 Ω`. `R54=470 Ω`. `R30=R76+R73_L` con `R76=330 Ω` y `R73_L` en `0..1000 Ω`; se valida `330..1330 Ω`. `R61` exige escoger **200 Ω** (esquema) o **200 kΩ** (lista); ninguno se promueve a valor físico. Q28 se reduce a una corriente de cola positiva y constante, obtenida del punto DC condicionado; cutoff dinámico queda fuera. Riel positivo `+10 V` ideal. Los diez BJT usan `I_S` en A, β directo/inverso adimensionales y temperatura en K compartidos por el escenario; la implementación puede ampliarse a parámetros por dispositivo al disponer de evidencia.

Las celdas `C16/C11/C7/C3=68 nF` unen los cuatro pares de colector/emisor; `C24=220 µF` va de BOTTOM a tierra y `C27=10 µF` de BASE_Q29 al BUS impuesto. Todos son ideales sin ESR, fuga o tolerancia incorporada. C5/C1 de `220 nF` se calculan en la recuperación; su corriente de entrada y matriz `2×2` se estampan en los nodos superiores del ladder. C10/EMPHASIS sigue **abierto**. El estado guarda seis tensiones de capacitor en V, 16 nodos actuales y anteriores y el estado completo de la salida. La inicialización DC abre los capacitores; recibe una semilla del cálculo offline, usada sólo para iniciar Newton.

## Ecuación y solver

El residuo usa corriente **saliente** de cada nodo en A. Cada BJT aporta base, colector y emisor de Ebers–Moll, con derivadas analíticas de ambas junturas. Euler implícito añade `I_C=(C/Δt)(V_nuevo−V_previo)`; `C27` conserva `V_BASE−V_BUS`. La corriente de cola se estampa como salida de TAIL. Para cada iteración externa se resuelve provisionalmente el resto de la cadena con **el mismo estado anterior** y se añade `I_C5/C1` y su Jacobiano local a los dos nodos superiores. El paso sólo publica el estado al converger `max |KCL| < 10⁻¹⁰ A`. Usa predictor lineal, pivoteo escalado, amortiguación acotada y reintento desde el estado anterior. Los presupuestos son 16 iteraciones y 16 intentos de amortiguación por solve; un fallo retorna error sin mutar el estado del llamador. No hay asignación en los pasos de audio.

## Contrastes

[`ladder_native_vectors.py`](../tools/ladder_native_vectors.py) genera 10 pasos por cada R61 con el oráculo Python **independiente** de 16 nodos y Jacobiano por diferencias finitas. El test Rust contrasta cada nodo a `<1 µV`, corriente de BUS a `<10 nA`, KCL y Jacobiano analítico contra diferencias centrales. Los tests adicionales cierran KCL del ladder **con el puerto C5/C1 y toda la salida cargada** para ambos R61, comprueban que la corriente del puerto coincide con la estampada, y comprueban que una entrada inválida preserva todo el estado. El test de asignaciones incluye 40 pasos acoplados sin heap. La comparación de una traza completa BUS→J7 con un oráculo independiente de todos los nodos sigue pendiente: esta conservación y los oráculos parciales no prueban equivalencia completa.

En Windows, AMD Ryzen 5 5600X, compilación `--release`, 48 kHz, bloques de 64, seno de BUS de 100 Hz y 0,1 V, R61=200 Ω, 8192 muestras medidas después de 8192 de calentamiento: media **24 205,4 µs/bloque**, p99 **28 068,5 µs**, máximo **28 623,3 µs**, cero fallos, KCL máximo `4,083×10⁻¹² A` y 2,00 solves de recuperación por muestra. El plazo de audio es **1333,3 µs/bloque**: la ruta excede la media ~18,2 veces. La prueba en [`bench_ladder_recovery_output.rs`](../crates/rf-d-circuit/examples/bench_ladder_recovery_output.rs) es un perfil local, no una calificación de tiempo real. Faltan un solver reducido o disperso y la comparación numérica/audio que exige RACE antes de adoptar una optimización.

```powershell
python -m unittest discover -s tests -p test_ladder_native_vectors.py -q
cargo test --workspace
cargo run --release -p rf-d-circuit --example bench_ladder_recovery_output
```
