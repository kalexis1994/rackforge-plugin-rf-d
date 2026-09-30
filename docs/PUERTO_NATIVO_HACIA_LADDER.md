# Puerto C5/C1 del recuperador hacia el ladder

El [solver nativo Q5–Q8→J7](../crates/rf-d-circuit/src/recovery_vca_output.rs) expone ahora la carga que presentan **C5 y C1** a los dos emisores superiores del ladder. **SVC-9 Fig. 9-11, PDF p. 13**, y **tabla 7-8, pp. 30–31** conectan C5 `0,22 µF` del emisor izquierdo a Q8_BASE y C1 `0,22 µF` del derecho a Q6_BASE; la [transcripción](../evidence/filter_recovery_active_dc.json) identifica ambos terminales. El [circuito de recuperación](RECUPERACION_SALIDA_NATIVA.md) conserva las corrientes de base de Q8/Q6, el par Q7/Q5 y la carga posterior desde R2 hasta J7.

Para `u=[V_ladderL,V_ladderR]`, las corrientes `i=[I_C5,I_C1]` son positivas **desde el ladder hacia el recuperador**, en amperios. Con estado anterior fijo, `I_C5=(0,22×10⁻⁶ F/dt)·[V_ladderL−V_Q8base+V_C5,anterior]` donde `V_C5,anterior=V_Q8base,anterior−V_ladderL,anterior`; C1 tiene la ley análoga. La matriz `Y_ij=∂i_i/∂u_j`, en siemens, incluye la respuesta cruzada de Q5–Q8, R2, ambos VCA, C4/C2, panel y placa 3. Tras el paso acoplado se resuelven los dos términos derechos `J·(∂x/∂u_j)=e_base,j·C_j/dt` en una sola factorización del Jacobiano `8×8` cargado por la admisión exacta de R2. Entonces `Y_ij=(C_i/dt)·[δ_ij−∂V_base,i/∂u_j]`. No se aproxima la carga por un resistor fijo.

Cada llamada es **provisional**: parte del mismo estado previo de los capacitores C5/C1/C9/C6/C15/C4/C2 y de placa 3; el solver del ladder deberá confirmar sólo el `next_state` correspondiente a la solución conjunta. El resultado de recuperación retiene la corriente y admisión aceptadas de R2 para no repetir ese solve al calcular `Y`.

El [oráculo Python de 33 incógnitas](../tools/recovery_vca_output_vectors.py) congela ambas corrientes en los **16 pasos** del [fixture](../evidence/recovery_vca_output_vectors.json). La [prueba Rust](../crates/rf-d-circuit/tests/recovery_vca_output.rs) compara cada corriente con error `<1 nA` y las cuatro entradas de `Y` contra perturbaciones simétricas `±0,1 mV` en tres estados, con tolerancia `2×10⁻⁷ S+10⁻³·|Y_fd|`. La [prueba sin heap](../crates/rf-d-circuit/tests/no_alloc.rs) ejecuta 20 puertos adicionales. Las leyes son válidas para `dt>0`, fronteras finitas y el dominio de exponenciales/solver de [Q5–Q8](RECUPERACION_SALIDA_NATIVA.md). Los componentes y parámetros de semiconductor mantienen allí sus incertidumbres; no hay unidad Model D medida ni validación de fidelidad sonora. **C10/EMPHASIS permanece abierto** y el bloque nativo completo aún incumple el plazo de audio.

```powershell
python -m unittest discover -s tests -p test_recovery_vca_output_vectors.py -q
cargo test --workspace
```
