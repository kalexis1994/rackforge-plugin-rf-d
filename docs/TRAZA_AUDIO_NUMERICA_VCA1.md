# Traza numérica sostenida del primer VCA a J7

El [oráculo Python](../tools/vca1_output_vectors.py) y la [ruta Rust](../crates/rf-d-circuit/src/vca1_output.rs) resuelven por métodos distintos el circuito condicionado de 25 incógnitas desde R2/C6/C15, los dos VCA, C4/Q1/Q12/Q17, C2, panel y placa 3. El [fixture de 192 muestras](../evidence/vca1_audio_trace.json) ejercita cuatro ciclos de `1 kHz` a `48 kHz` con `V_RECOVER_COLLECTOR=5 V+0,5 V·sin(2π·1000t)`. En la muestra 64 cambia `V_LOUDNESS` en `+0,03 V`, en la 128 `V_Q21_BASE` en `+0,02 V`, y SW18 se abre entre 80 y 159. La carga de auriculares es `32 Ω` por canal. Estas son señales de laboratorio impuestas, no capturas del instrumento.

La [prueba Rust](../crates/rf-d-circuit/tests/vca1_output.rs) compara en cada muestra los **23 voltajes internos** y la salida J7 con el [oráculo regenerable](../tests/test_vca1_audio_trace.py). En esta máquina, el máximo error interno fue `1,209×10⁻⁷ V`, el máximo error en J7 `2,334×10⁻⁹ V` y la relación RMS señal/error numérica en J7 `125,8 dB`. El gate exige respectivamente `<1 µV`, `<0,1 µV` y `>90 dB`, con KCL local `<10⁻¹⁰ A`. Esta relación mide **acuerdo entre implementaciones**; no es SNR de hardware, ruido analógico ni semejanza audible con un Model D.

La topología y los valores proceden de **SVC-9 Fig. 9-11, PDF p. 13; tabla 7-8, pp. 30–31; Fig. 9-8, p. 10; Fig. 9-17, p. 19**. Las ecuaciones, unidades, incertidumbre de componentes y supuestos BJT/diodos están en [VCA1→J7](VCA1_SALIDA_NATIVA.md). Esta traza comprueba una frecuencia y una pequeña región de controles; no caracteriza el barrido del filtro, la respuesta a lo largo del teclado, la calibración entre unidades ni el tiempo real. El [benchmark de plazo](VCA1_SALIDA_NATIVA.md) sigue fallando.

```powershell
python -m unittest discover -s tests -p test_vca1_audio_trace.py -q
cargo test -p rf-d-circuit --test vca1_output four_cycle -- --nocapture
```
