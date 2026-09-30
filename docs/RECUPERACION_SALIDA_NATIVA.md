# Recuperación Q5–Q8 acoplada al VCA y J7

El [solver Rust](../crates/rf-d-circuit/src/recovery_vca_output.rs) une el recuperador activo del filtro con el [puerto R2/C6 del primer VCA](PUERTO_NATIVO_HACIA_FILTRO.md), los dos multiplicadores, la conversión Q1/Q12/Q17 y C2/panel/placa 3/J7. Las tensiones de los dos emisores superiores del ladder siguen impuestas. **C10/EMPHASIS queda abierto**; no hay todavía un lazo de filtro completo ni señal BUS nativa.

## Circuito documentado

**SVC-9 Fig. 9-11, PDF p. 13**, y **tabla 7-8, pp. 30–31** sustentan el [grafo de Q5–Q8](../evidence/filter_recovery_active_dc.json). C5 y C1 `0,22 µF` acoplan los emisores superiores izquierdo y derecho a Q8_BASE y Q6_BASE. R31/R38 `47 kΩ` conectan las bases a masa; Q8/Q6 conducen a las bases Q7/Q5, con R24 `220 kΩ` y R20 `100 kΩ` hacia −10 V. Q7/Q5 comparten R26 `1 kΩ`. Q8/Q7 inyectan en RECOVER_COLLECTOR, alimentado desde +10 V por R6 `47 Ω`, R7 `180 Ω` y R3 `1 kΩ`; C9 `100 µF` desacopla el nodo R6/R7 a masa. El tap R7/R3 es el punto de EMPHASIS que posteriormente recibirá C10. La [referencia DC original](RECUPERACION_ACTIVA_FILTRO.md) fija el sentido de terminales y de las cuatro leyes Ebers–Moll.

El estado local contiene ocho tensiones y las tensiones anteriores de C5, C1 y C9. Con Euler implícito, `I_C5=(0,22×10⁻⁶ F/dt)·[(V_Q8base−V_ladderL)−V_C5,anterior]`, análogamente para C1, e `I_C9=(100×10⁻⁶ F/dt)·[V_R6R7−V_C9,anterior]`, todas en amperios. En DC los tres capacitores se abren; C10 también. El colector incorpora `I_R2=(V_col−V_C6LEFT)/82 kΩ`, positivo hacia el VCA, y su admisión local del [puerto aguas abajo](PUERTO_NATIVO_HACIA_FILTRO.md). El Newton de ocho nodos usa un Jacobiano analítico con las corrientes de base y colector de Q8/Q6/Q7/Q5. Cada prueba conserva el mismo estado previo de **todos** los capacitores hasta J7 y sólo confirma el candidato conjunto convergido.

El [puerto C5/C1 hacia el ladder](PUERTO_NATIVO_HACIA_LADDER.md) devuelve ahora las dos corrientes y la matriz de admisión `2×2` del circuito completo condicionado.

## Contraste numérico y costo

El [oráculo Python](../tools/recovery_vca_output_vectors.py) resuelve **33 incógnitas** del recuperador a R21_WIPER mediante diferencias finitas y llama al modelo no lineal independiente de placa 3. El [fixture](../evidence/recovery_vca_output_vectors.json) contiene DC y **16 pasos** a `48 kHz` con cambios de ambos emisores impuestos, primer y segundo control de volumen, y SW18. La [regresión Rust](../crates/rf-d-circuit/tests/recovery_vca_output.rs) compara los 31 nodos anteriores a C2, C5/C1/C9/C6/C15/C4/C2, R21_WIPER, HI/LO/J7 y los doce nodos de placa 3 con error `<1 µV`; exige KCL local `<10⁻¹⁰ A` y estado completo inalterado ante una frontera inválida. La [regeneración Python](../tests/test_recovery_vca_output_vectors.py) congela el oráculo. La [prueba sin heap](../crates/rf-d-circuit/tests/no_alloc.rs) añade DC y 100 pasos sin asignaciones.

La [sonda release](../crates/rf-d-circuit/examples/bench_recovery_vca_output.rs) procesó una pasada de calentamiento y `48 000` muestras medidas, señal impuesta de `100 Hz` en ambos emisores, auriculares `32 Ω+32 Ω`, bloques de `64`, Windows/AMD Ryzen 5 5600X y `rustc 1.97.0`. Obtuvo media `16 119,6 µs`, p99 `22 395,6 µs`, máximo `22 681,3 µs` por bloque frente al plazo de `1333,3 µs`; hubo `2,53` evaluaciones VCA por muestra, cero fallos y KCL máximo `9,998×10⁻¹¹ A`. **No pasa el gate de tiempo real**. Es una corrida, no una cota de peor caso. La anidación de los solves sigue siendo el principal problema numérico.

## Dominio e incertidumbre

Se admiten rieles finitos ordenados, emisores impuestos finitos, `dt>0`, parámetros BJT positivos y presupuesto Newton de hasta `16/16`; las exponenciales rechazan argumentos mayores que 45 unidades térmicas. `I_S=10⁻¹⁴ A`, `β_F=100`, `β_R=5`, `298,15 K` y parámetros de diodos/cargas posteriores son hipótesis de laboratorio. La lista de partes aporta los valores nominales de R/C, pero esta etapa no dispone de tolerancias o parámetros de cuatro TIS97 medidos. Se omiten fugas, ESR, capacitancias de juntura, dispersión, acoplamiento de C10 y realimentación hacia el ladder. La equivalencia Python/Rust comprueba la implementación condicionada; sin unidad física ni fuente comparable no demuestra fidelidad sonora.

```powershell
python -m unittest discover -s tests -p test_recovery_vca_output_vectors.py -q
cargo test --workspace
cargo run --release -p rf-d-circuit --example bench_recovery_vca_output
```
