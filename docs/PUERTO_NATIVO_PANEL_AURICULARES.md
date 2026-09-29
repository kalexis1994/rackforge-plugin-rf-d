# Frontera nativa C2_RIGHT→R77/R21→placa 3→J7

El [módulo Rust de panel](../crates/rf-d-circuit/src/panel.rs) añade **R77 `1000 Ω`** y las dos secciones de **R21 `5000 Ω`** al [puerto dinámico de placa 3](PUERTO_NATIVO_PLACA3_AURICULARES.md). R77 y R21 están en **SVC-9 Fig. 9-17, PDF p. 19** y la salida de placa 4 en **Fig. 9-11, p. 13**; la [transcripción](../evidence/output_panel_headphone_r21.json) conserva sus terminales. Las unidades del paso son voltios, amperios, ohmios y segundos. `C2_RIGHT` es una frontera de voltaje **impuesta**, no la respuesta de una etapa ya acoplada. `0<R21_inferior<5000 Ω` es una posición eléctrica; extremos ideales y ley angular de panel siguen sin modelar.

Con `R_s=R77+R21_superior`, el cursor `w` cumple simultáneamente `F(w)=(w−V_C2_RIGHT)/R_s+w/R21_inferior+I_C19(w)=0`. El paso de placa 3 se recalcula en cada prueba de Newton externo manteniendo fijo el estado capacitivo anterior. Su [derivada implícita](PUERTO_NATIVO_PLACA3_AURICULARES.md) da `F′(w)=1/R_s+1/R21_inferior+∂I_C19/∂w`. Una vez resuelto, `V_pin22=V_C2_RIGHT+(w−V_C2_RIGHT)R77/R_s` y `I_R77=(V_C2_RIGHT−w)/R_s`. El solver devuelve esa corriente para que la futura placa 4 cargue C2_RIGHT correctamente. C19 sigue como capacitor dinámico; no se reemplaza por una impedancia constante.

Para que C2_RIGHT forme parte de otro Newton, el puerto también devuelve `Y_R77=∂I_R77/∂V_C2_RIGHT=(1/R_s)[1−(1/R_s)/F′(w)]`, en siemens. La derivada se toma con el estado del paso anterior fijo y la placa 3 resuelta de nuevo para cada voltaje de prueba. La [regresión Rust](../crates/rf-d-circuit/tests/panel_vectors.rs) la compara con perturbación simétrica en doce puntos, incluidos cambios de signo y de carga. Es una tangente de la solución implícita, no una carga resistiva fija.

El presupuesto exterior e interior está limitado a `16/16` y el cierre del cursor exige residuo `<10⁻¹⁰ A`. Un error devuelve código sin mutar la placa ni el cursor. La [prueba con asignador instrumentado](../crates/rf-d-circuit/tests/no_alloc.rs) añade 100 pasos de esta frontera y registra **cero asignaciones de heap**. Esta frontera es un paso de arquitectura y un oráculo de integración, no una política admitida para el callback.

La [herramienta Python independiente](../tools/headphone_panel_port_vectors.py) resuelve la placa 3 con su referencia de doce nodos y el panel con Newton exterior de diferencia finita. Congela [96 pasos](../evidence/headphone_panel_port_vectors.json): tres escenas de 32 pasos con cargas `32 Ω+32 Ω` u abiertas, temperatura `300/285 K`, C2_RIGHT bipolar o senoidal y R21 inferior `2000 Ω`. Los parámetros TIS y de diodo son los mismos **supuestos de laboratorio** del puerto previo, no mediciones de una unidad vintage. La [prueba Python](../tests/test_headphone_panel_port_vectors.py) verifica regeneración exacta; la [prueba Rust](../crates/rf-d-circuit/tests/panel_vectors.rs) compara pin 22, cursor, J7 y los doce nodos con error absoluto `<1 µV`, y las corrientes R77/C19 con `<0,1 nA`. Ambas KCL deben ser `<10⁻¹⁰ A`.

El siguiente acoplamiento requiere resolver los **48 nodos anteriores** con `I_R77` dentro de su propia KCL y conservar la semántica de C10, C2 y BUS. El [gate de 62 nodos](VECTORES_PORTABILIDAD_AURICULARES.md) sigue abierto. Estos resultados verifican equivalencia con modelos condicionados; no verifican audio ni fidelidad del Model D.

## Coste del solve anidado

La [sonda local](../crates/rf-d-circuit/examples/bench_panel.rs) usa `cargo run --release -p rf-d-circuit --example bench_panel`: una pasada de calentamiento y otra medida con **48 000 muestras**, seno C2_RIGHT de `100 Hz` y `0,5 V` pico, R21 inferior `2000 Ω`, J7 con `32 Ω+32 Ω`, bloques de 64 a 48 kHz. La entrada senoidal se genera dentro del bloque medido. El presupuesto teórico es `1333,3 µs` por bloque. En Windows, AMD Ryzen 5 5600X y `rustc 1.97.0`, dos corridas locales consecutivas dieron:

| Variante | Media/bloque | p99/bloque | Máximo/bloque | Fallos |
| --- | ---: | ---: | ---: | ---: |
| Resolver nuevamente el mismo puerto aceptado | 900,9 µs | 1063,4 µs | 1400,6 µs | 0 |
| Reutilizar la solución aceptada | 599,6 µs | 714,9 µs | 1023,7 µs | 0 |

En los 96 pasos del fixture, la solución reutilizada de los doce nodos y la corriente C19 son **idénticas bit a bit** a una resolución adicional desde el mismo estado anterior; el contraste con el oráculo Python también pasa. La mejora elimina trabajo repetido, sin cambiar el esquema numérico. Los máximos de una sola corrida por variante son observaciones, no límites garantizados ni medición del plugin. El bloque anterior de 48 nodos, el host y posibles factores de sobremuestreo aún consumirán tiempo; se deberá volver a medir el sistema acoplado antes de aprobar un callback en vivo.
