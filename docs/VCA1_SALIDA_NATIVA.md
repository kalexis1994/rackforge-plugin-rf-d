# Primer VCA con C6/C15 hasta J7

El [bloque Rust](../crates/rf-d-circuit/src/vca1_output.rs) une la entrada del primer VCA a la [cadena ya verificada VCA2→J7](VCA2_SALIDA_NATIVA.md). El colector del recuperador del filtro, el volumen del primer VCA, la base de Q21, los rieles y las cargas externas son fronteras impuestas. El filtro, los contornos y los jacks de control todavía no forman parte del solver nativo.

## Grafo y ecuaciones

**SVC-9 Fig. 9-11, PDF p. 13** y **tabla 7-8, pp. 30–31** conectan R2 `82 kΩ` desde RECOVER_COLLECTOR a C6_LEFT, C6 `0,33 µF` de C6_LEFT a Q16_BASE, R34 `820 Ω` entre las bases, C15 `220 µF` y R36 `510 Ω` desde Q15_BASE a masa. El mismo esquema da Q16/Q15/Q18, R35 `1 kΩ`, R37 `6,8 kΩ`, R43 `270 kΩ`, R59 `68 kΩ`, R22 `120 Ω`, R19/R23 `100 Ω` y el cursor R14 de placa 4 `25 Ω`; R13 `120 Ω` conduce hacia el segundo cursor. **SVC-204D §2.9, PDF p. 12** describe la función de los dos multiplicadores. Las transcripciones están en [frontera de entrada](FRONTERA_ENTRADA_VCA1.md), [núcleo activo](NUCLEO_ACTIVO_VCA1_DC.md) y [cascada](VCA_CASCADA_DC.md).

Con Euler implícito y `dt` en segundos, `I_C6=(0,33×10⁻⁶ F/dt)·[(V_C6LEFT−V_Q16BASE)−V_C6,anterior]` e `I_C15=(220×10⁻⁶ F/dt)·[V_Q15BASE−V_C15,anterior]`, en amperios. El DC abre ambos capacitores. Las diez incógnitas locales son C6_LEFT, bases Q16/Q15, emisor común, colector/emisor de Q18, colectores Q16/Q15, base Q18 y cursor del primer balance. Las tres corrientes de carga de Q14_BASE, Q13_BASE y R13 llegan del [puerto de cuatro entradas](PUERTO_NATIVO_HACIA_VCA1.md). Su matriz `4×4` se incorpora a las tres KCL pertinentes; la cuarta corriente, de Q21_BASE/R51, carga a la fuente de control impuesta. Se resuelve un Newton `10×10` con Jacobiano local analítico y estado posterior provisional; sólo se confirma el estado de todos los capacitores cuando converge toda la cadena. Las cargas y parámetros de semiconductores mantienen las unidades y convenciones de los bloques previos.

## Regresión y plazo

El [oráculo Python](../tools/vca1_output_vectors.py) formula **25 ecuaciones** para C6_LEFT, los 22 nodos de la [cascada DC](CASCADA_HASTA_SALIDA_DC.md), C2_RIGHT y R21_WIPER. Diferencia numéricamente su Jacobiano y resuelve placa 3 por separado; no llama al código ni a la tangente Rust. El [fixture](../evidence/vca1_output_vectors.json) contiene DC y **12 pasos** a 48 kHz, con cambios de entrada, volumen, Q21 y SW18. La [regresión Rust](../crates/rf-d-circuit/tests/vca1_output.rs) compara los 23 voltajes internos, C6/C15/C4/C2, salidas HI/LO/J7 y los 12 nodos de placa 3 con tolerancia `<1 µV`, además de KCL `<10⁻¹⁰ A` y preservación completa del estado ante una entrada inválida. La [prueba de heap](../crates/rf-d-circuit/tests/no_alloc.rs) cubre inicialización y 100 pasos adicionales sin asignaciones.

La [corriente y admisión en R2](PUERTO_NATIVO_HACIA_FILTRO.md) quedan disponibles para el próximo cierre con el recuperador del filtro.

El [sondeo de 48 000 muestras](../crates/rf-d-circuit/examples/bench_vca1_output.rs) en Ryzen 5 5600X, compilación `--release`, bloques de 64 y señal impuesta de 100 Hz dio `mean 6019,0 µs`, `p99 6847,9 µs`, máximo `7596,6 µs` frente al plazo de `1333,3 µs`. Hubo **0 fallos**, **0 retornos al predictor**, media **2,00** evaluaciones del puerto posterior por muestra y KCL máximo `2,398×10⁻¹¹ A`. La ruta conjunta **no pasa** el gate de tiempo real; estos resultados no son rendimiento de un plugin ni de una voz completa. El costo de resolver reiteradamente la cadena posterior será el siguiente objeto de optimización y se contrastará contra esta referencia antes de reemplazarla.

## Incertidumbre y alcance

R2 y R34/R36 figuran con ±5 %, C6 con ±10 % y C15 con +50/−10 % en la tabla 7-8. `I_s=10⁻¹⁴ A`, `β_F=100`, `β_R=5`, `298,15 K`, los diodos y las cargas de prueba son **supuestos de laboratorio**; no se midió una placa Model D. El colector del recuperador se fija a `5 V` en DC y recibe una perturbación para probar el acoplamiento, sin atribuir ese valor al instrumento. La equivalencia Rust/Python verifica la implementación de este circuito condicionado; quedan parámetros reales, efectos parasitarios, variación entre unidades, filtro acoplado, osciladores, controles y contraste de audio externo antes de hablar de fidelidad sonora.

```powershell
python -m unittest discover -s tests -p test_vca1_output_vectors.py -q
cargo test --workspace
cargo run --release -p rf-d-circuit --example bench_vca1_output
```
