# Primer puerto nativo: placa 3 de auriculares

El crate [`rf-d-circuit`](../crates/rf-d-circuit/src/lib.rs) ejecuta el circuito 11 de la placa 3 como un sistema de **12 nodos**. Su conectividad, componentes y rieles provienen de **SVC-9 Fig. 9-8, PDF p. 10** (también SVC-204D p. 66), con R56 y la carga externa de J7 según **SVC-9 Fig. 9-17, PDF p. 19**. La transcripción comprobable está en [`headphone_amp_active_board3.json`](../evidence/headphone_amp_active_board3.json). La frontera pin 7 está impuesta, en voltios: este puerto todavía no resuelve el bus, el filtro, los VCA ni el potenciómetro R21.

El motor usa `f64`, voltios, amperios, ohmios, faradios, segundos y kelvin. Los tres BJT usan Ebers–Moll simple con `I_S`, `β_F` y `β_R` proporcionados por el llamador; los dos diodos usan Shockley con `I_S` y factor de idealidad también impuestos. La tensión térmica es `k_B T/q_e`, con constantes SI exactas. Son parámetros de laboratorio **sin identificación de una población TIS-92/TIS-93 o 1N458A original**. No se modelan capacidades de transistor, ESR, fugas, dispersión, alimentación ni contacto de jack. La validez numérica del modelo se limita a exponentes directos `≤45` y parámetros positivos finitos. Ni el solver ni los vectores prueban fidelidad sonora vintage.

El [arranque DC nativo](../crates/rf-d-circuit/src/lib.rs) abre los tres capacitores, impone pin 7 a `0 V`, resuelve el punto de once nodos más J7 y carga C19/C15/C21 con las diferencias de tensión de sus terminales. Comparte la topología y las estampas de dispositivos con el paso temporal; la semilla de voltajes sólo sirve para Newton. Los tres escenarios del fixture reproducen el arranque del oráculo con error por nodo y capacitor `<10⁻⁸ V`. Esta operación corresponde a inicialización fuera del callback, no a una calibración vintage.

El paso integra C19 `2,5 µF`, C15 `220 pF` y C21 `400 µF` mediante Euler implícito. Conserva la tensión previa de cada capacitor, estampa `i=C/Δt·(v_nuevo−v_previo)` en KCL y resuelve BJT, diodos y carga J7 de forma simultánea con Jacobiano analítico. El estado de 12 tensiones y tres cargas sólo cambia si Newton converge. El callback puede seleccionar un presupuesto menor; el máximo admitido es **16 iteraciones y 16 pruebas de línea**, con residuo KCL `<10⁻¹⁰ A`. Los fallos retornan un código y dejan el estado intacto. El camino `step` usa arreglos de tamaño fijo y no hace asignaciones, I/O, bloqueos ni serialización. Aún falta medir plazo y comportamiento con una voz RackForge; tampoco existe una política aprobada de recuperación tras fallo dentro del callback.

La [herramienta de generación](../tools/headphone_board3_port_vectors.py) congela [`192 pasos`](../evidence/headphone_board3_port_vectors.json) del [oráculo Python](../tools/headphone_amp_active_transient_reference.py): 48 a 48 kHz con dos cargas de `32 Ω` y escalones bipolares, 96 a 9,6 kHz con J7 abierto y seno impuesto, y 48 a 4,8 kHz con cargas de `32 Ω` a `285 K`. Cada paso registra los 12 nodos, tres tensiones de capacitor y residuo. La [regresión Rust](../crates/rf-d-circuit/tests/board3_vectors.rs) exige error absoluto `<1 µV` en cada nodo y estado y KCL `<10⁻¹⁰ A`, además de comprobar que un paso fallido no muta el estado. Estas tolerancias se refieren sólo a la **equivalencia numérica** con el oráculo condicionado. El gate BUS→J7 de 62 nodos sigue [definido por separado](VECTORES_PORTABILIDAD_AURICULARES.md).

Para comprobar este bloque: `cargo test --workspace`. Para toda la investigación Python: `python -m unittest discover -s tests`.

## Coste local y asignaciones

La [prueba de asignaciones](../crates/rf-d-circuit/tests/no_alloc.rs) intercepta el asignador global de su proceso: el arranque DC más `1000` pasos bipolares de placa 3 con dos cargas de `32 Ω` generaron **cero asignaciones** de heap. No se extiende esta afirmación a un adaptador de host o a otros circuitos.

La [sonda reproducible](../crates/rf-d-circuit/examples/bench_board3.rs) ejecuta `cargo run --release -p rf-d-circuit --example bench_board3`. Una pasada de calentamiento y una medida de **48 000 muestras** por escena usan bloques de 64 muestras a 48 kHz, temperatura `300 K`, `I_S(BJT)=10⁻¹⁴ A`, `β_F=160`, `β_R=5`, diodos `n=1,5` con `I_S=1,4465886434575519·10⁻⁹ A`, y entrada senoidal de `100 Hz` que invierte polaridad a mitad de la escena. La generación de la entrada y la llamada a `step` quedan dentro del tiempo medido; el acumulado y la ordenación de duraciones quedan fuera. El presupuesto de audio teórico por bloque es `1333,3 µs`.

Una ejecución local en Windows, **AMD Ryzen 5 5600X**, `rustc 1.97.0`, build `--release`, produjo:

| Escena | Media/bloque | p99/bloque | Máximo/bloque | Iteraciones Newton media/máxima | Fallos |
| --- | ---: | ---: | ---: | ---: | ---: |
| J7 32 Ω + 32 Ω, 0,5 V pico | 288,3 µs | 382,9 µs | 574,6 µs | 2,49 / 3 | 0 |
| J7 abierto, 0,5 V pico | 244,2 µs | 317,3 µs | 667,4 µs | 1,99 / 3 | 0 |
| J7 32 Ω + 32 Ω, 1 V pico | 293,5 µs | 359,5 µs | 685,2 µs | 2,55 / 3 | 0 |

El mayor residuo KCL reportado fue `<10⁻¹⁰ A` en las tres escenas. Estos máximos son **observaciones de una corrida**, sensibles a planificación del sistema operativo y equipo. La placa 3 aislada consume una fracción importante del presupuesto, y habrá que medir de nuevo al acoplarla a los otros 50 nodos y al host, con la frecuencia interna y calidad de audio previstas. No se infiere un deadline garantizado ni la conveniencia de ejecutar el solver completo a cada muestra.
